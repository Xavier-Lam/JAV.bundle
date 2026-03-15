# coding=utf-8
"""Tests that plugin code compiles and runs under the Plex RestrictedPython sandbox.

The Plex Framework compiles all plugin source files through RestrictedPython
before execution.  This module verifies that every ``.py`` file under
``Contents/Code`` compiles cleanly under the **Elevated** policy, and that the
compiled ``__init__.py`` can be executed in a sandbox-like environment with
a successful call to ``Start()``.
"""

from base import CODE_PATH, load_prefs

import binascii
import os
import sys
import types
import unittest

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins


# ---------------------------------------------------------------------------
# Sandbox helpers (mirrors Framework/code/sandbox.py)
# ---------------------------------------------------------------------------

class PrintHandler:
    def write(self, text):
        if sys.platform != "win32":
            sys.stdout.write(text)


class FrameworkException(Exception):
    pass


def _apply(f, *args, **kwargs):
    return apply(f, args, kwargs)


def _inplacevar(op, arg1, arg2):
    if op == '+=':
        return arg1 + arg2
    raise FrameworkException("Operator '%s' is not supported" % op)


def make_sandbox_environment(custom_import):
    """Build the globals dict that Plex passes to ``exec(code) in env``.

    Mirrors ``Sandbox.__init__`` in the Framework, configured for the
    **Elevated** policy (adds *hasattr*, *getattr*, *setattr*, *dir*,
    *super*, *type*).
    """
    standard_builtins = dict(safe_builtins)
    standard_builtins['__import__'] = custom_import

    env = dict(
        # RestrictedPython guard functions
        _print_=PrintHandler,
        _getattr_=getattr,
        _write_=lambda x: x,
        _getiter_=lambda x: x.__iter__(),
        _getitem_=lambda x, y: x.__getitem__(y),
        _apply_=_apply,
        _inplacevar_=_inplacevar,

        # Sandbox builtins
        __builtins__=standard_builtins,
        __name__='__code__',

        # Additional types exposed by the sandbox
        object=object,
        set=set,
        str=str,
        unicode=unicode,
        min=min,
        max=max,
        xrange=xrange,
        list=list,
        dict=dict,
        staticmethod=staticmethod,
        classmethod=classmethod,
        property=property,
        sorted=sorted,
        reversed=reversed,
        reduce=reduce,
        filter=filter,
        map=map,
        enumerate=enumerate,
        FrameworkException=FrameworkException,
        hexlify=binascii.hexlify,
        unhexlify=binascii.unhexlify,

        # Elevated policy additions
        hasattr=hasattr,
        getattr=getattr,
        setattr=setattr,
        dir=dir,
        super=super,
        type=type,
    )

    # Inject plex builtins that are usually published by the framework API.
    import __builtin__
    for name in [
        "Agent", "Locale", "Log", "MessageContainer", "Prefs", "Proxy",
        "SearchResult", "TrailerObject",
    ]:
        obj = __builtin__.__dict__.get(name)
        if obj is not None:
            env[name] = obj

    # initialize Prefs
    env['Prefs']._prefs = load_prefs()

    return env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def collect_code_files():
    """Return ``[(relative_path, absolute_path), ...]`` for all ``.py``
    files under *Contents/Code*."""
    result = []
    for dirpath, dirnames, filenames in os.walk(CODE_PATH):
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                abspath = os.path.join(dirpath, fn)
                relpath = os.path.relpath(abspath, CODE_PATH)
                result.append((relpath, abspath))
    return result


def compile_source(source, filename, elevated=True):
    """Compile *source* through RestrictedPython.

    Returns the code object on success.  Raises ``SyntaxError`` on
    failure (the message contains the restriction violation).
    """
    return compile_restricted(source, filename, 'exec', elevated=elevated)


# ---------------------------------------------------------------------------
# Custom __import__ for the sandbox
# ---------------------------------------------------------------------------

class SandboxImporter(object):
    """A minimal re-implementation of the Framework's sandbox ``__import__``.

    Plugin code files (those living under *Contents/Code*) are compiled
    through ``compile_restricted`` and executed inside a
    ``RestrictedModule``.  Everything else is delegated to the standard
    ``__import__``.
    """

    def __init__(self, code_path, environment, elevated=True):
        self.code_path = code_path
        self.environment = environment
        self.elevated = elevated
        self.modules = {}

    def _find_code_file(self, name, search_dir):
        """Return the absolute path of the code file for *name* under
        *search_dir*, or ``None`` if not found.

        Handles both flat (``utils``) and dotted (``agents.base``) names.
        Only searches under *search_dir*; callers should pass either
        ``self.code_path`` (absolute imports) or the caller's package
        directory (relative imports).
        """
        parts = name.split('.')
        dirpath = search_dir
        for part in parts[:-1]:
            candidate = os.path.join(dirpath, part)
            if os.path.isdir(candidate):
                dirpath = candidate
            else:
                return None

        final = parts[-1]
        for filepath in (
            os.path.join(dirpath, final + '.py'),
            os.path.join(dirpath, final, '__init__.py'),
        ):
            if os.path.isfile(filepath):
                return filepath

        return None

    def _caller_dir(self, globs, locs):
        """Return the package directory of the importing module, or None."""
        for ns in (locs, globs):
            if ns:
                p = ns.get('__path__')
                if p and isinstance(p, basestring):
                    return p
        return None

    def __call__(self, name, globs=None, locs=None, fromlist=None, level=-1):
        if globs is None:
            globs = {}
        if locs is None:
            locs = {}
        if fromlist is None:
            fromlist = []

        is_relative = level > 0
        caller_dir = self._caller_dir(globs, locs)

        if is_relative and caller_dir:
            # Resolve relative imports against the caller's package directory.
            # Compute the fully-qualified name so 'utils' inside 'agents/'
            # becomes 'agents.utils' and does not collide with the top-level
            # 'utils' module.
            try:
                rel = os.path.relpath(caller_dir, self.code_path)
                if rel and rel != '.':
                    package = rel.replace(os.sep, '.')
                    full_name = package + '.' + name
                else:
                    full_name = name
            except ValueError:
                full_name = name  # different drive letters on Windows
            filepath = self._find_code_file(name, caller_dir)
        else:
            # Absolute import: only search top-level code_path.
            full_name = name
            filepath = self._find_code_file(name, self.code_path)

        if filepath is not None:
            return self.load_restricted_module(full_name, filepath)

        # Fall back to the real import for stdlib / third-party packages.
        return __import__(name, globs, locs, fromlist, level)

    def load_restricted_module(self, name, filepath):
        if name in self.modules:
            return self.modules[name]

        # Prevent infinite recursion while loading.
        mod = types.ModuleType(str(name))
        self.modules[name] = mod
        # Register in sys.modules so dotted imports can locate the parent.
        sys.modules[name] = mod

        source = open(filepath, 'r').read()
        code = compile_source(source, filepath, self.elevated)

        mod.__dict__.update(self.environment)
        mod.__dict__['__name__'] = name
        mod.__path__ = os.path.dirname(filepath)
        exec(code) in mod.__dict__
        return mod


# ===================================================================
# Test cases
# ===================================================================

class TestSandboxCompilation(unittest.TestCase):
    """Every ``.py`` file under Contents/Code must compile under
    RestrictedPython with the Elevated policy."""

    def test_all_code_files_compile(self):
        failures = []
        for relpath, abspath in collect_code_files():
            source = open(abspath, 'r').read()
            try:
                compile_source(source, relpath, elevated=True)
            except SyntaxError as exc:
                failures.append((relpath, str(exc)))

        if failures:
            msg_lines = ["The following files failed restricted compilation:"]
            for path, err in failures:
                msg_lines.append("  %s: %s" % (path, err))
            self.fail("\n".join(msg_lines))


class TestSandboxExecution(unittest.TestCase):
    """The compiled __init__.py must execute and its ``Start`` function
    must be callable inside the sandbox environment."""

    def setUp(self):
        # Snapshot both the key set and the actual module objects so that
        # tearDown can fully restore sys.modules (not just remove new keys).
        # This matters because the sandbox replaces existing entries, which
        # makes the original module objects unreferenced; Python 2 then clears
        # their __dict__ on GC, corrupting globals of still-live functions.
        self._pre_test_modules = dict(sys.modules)

    def tearDown(self):
        # Remove any modules the sandbox injected into sys.modules, and
        # restore any modules whose entries were replaced by the sandbox,
        # to avoid polluting the test session for other test files.
        for key in list(sys.modules.keys()):
            if key not in self._pre_test_modules:
                del sys.modules[key]
            elif sys.modules[key] is not self._pre_test_modules[key]:
                sys.modules[key] = self._pre_test_modules[key]

    def test_start_function_executes(self):
        importer = SandboxImporter(CODE_PATH, {}, elevated=True)
        env = make_sandbox_environment(importer)
        # Let the importer share the same environment.
        importer.environment = env

        init_path = os.path.join(CODE_PATH, "__init__.py")
        source = open(init_path, 'r').read()
        code = compile_source(source, "__init__.py", elevated=True)

        # Execute the module.
        exec(code) in env

        # Start must be defined and callable.
        start_fn = env.get("Start")
        self.assertIsNotNone(
            start_fn, "Start function not found in sandbox environment")
        self.assertTrue(callable(start_fn), "Start is not callable")

        # Actually call Start() — it should succeed without error.
        start_fn()


if __name__ == '__main__':
    unittest.main()
