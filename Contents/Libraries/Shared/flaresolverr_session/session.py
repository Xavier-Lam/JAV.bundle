# -*- coding: utf-8 -*-

import threading
import time
import warnings

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import requests
from requests.structures import CaseInsensitiveDict

from flaresolverr_session.rpc import RPC
from flaresolverr_session.exceptions import (
    FlareSolverrChallengeError,
    FlareSolverrUnsupportedMethodError,
)


class Session(requests.Session):
    """A ``requests.Session`` subclass that routes requests through
    FlareSolverr.

    The response objects are instances of
    :class:`flaresolverr_session.Response`, which carry additional
    FlareSolverr-specific attributes.

    Parameters:
        flaresolverr_url (str or None): The FlareSolverr API endpoint
            (e.g. ``"http://localhost:8191/v1"``).  Ignored when *rpc*
            is provided.
        session_id (str or None): An optional FlareSolverr session id.
            When *None* a new session is automatically created.
        proxy (str, dict or None): A proxy specification.
            When a *str*, it is interpreted as a URL.
            When a *dict*, it has a ``"url"`` key.
        timeout (int or None): ``maxTimeout`` in **milliseconds**
            passed to FlareSolverr.  Defaults to *60000* (60 s).
        rpc (RPC or None): An optional pre-configured
            :class:`~flaresolverr_session.rpc.RPC` instance.  When provided,
            *flaresolverr_url* is ignored.
        max_retries (int): Number of times to retry the request when a
            :class:`~flaresolverr_session.exceptions.FlareSolverrChallengeError`
            is raised (e.g. FlareSolverr challenge timeout).

    .. note::

        Only ``GET`` and ``x-www-form-urlencoded`` ``POST`` requests
        are supported by FlareSolverr.  Calling unsupported methods or
        passing ``json`` data will raise
        :class:`FlareSolverrUnsupportedMethodError`.
    """

    DEFAULT_TIMEOUT = 60000

    _SUPPORTED_METHODS = ("GET", "POST")

    def __init__(
        self,
        flaresolverr_url=None,
        session_id=None,
        proxy=None,
        timeout=None,
        rpc=None,
        max_retries=0,
    ):
        super(Session, self).__init__()

        if rpc is not None and flaresolverr_url is not None:
            warnings.warn(
                "Both 'rpc' and 'flaresolverr_url' are provided. "
                "The 'rpc' instance will be used and 'flaresolverr_url' "
                "will be ignored.",
                stacklevel=2,
            )

        if not rpc:
            rpc = RPC(flaresolverr_url)
        self._rpc = rpc

        self._timeout = timeout or self.DEFAULT_TIMEOUT
        if proxy and not isinstance(proxy, dict):
            proxy = {"url": proxy}
        self._proxy = proxy
        self._session_id = session_id
        self._session_created = False
        self._max_retries = max_retries
        self._lock = threading.Lock()

    @property
    def session_id(self):
        """The FlareSolverr session identifier."""
        if not self._session_created:
            self._create_session()
        return self._session_id

    def request(self, method, url, **kwargs):
        """Send a request through FlareSolverr.

        Parameters:
            method (str): HTTP method (``"GET"`` or ``"POST"``).
            url (str): Target URL.
            **kwargs: Keyword arguments.  Recognised keys include
                ``params`` (URL query parameters), ``data`` (for POST),
                ``cookies``, ``timeout`` (FlareSolverr ``maxTimeout``
                in ms).  Standard ``requests`` parameters such as
                ``headers`` are accepted but ignored -- the headless
                browser manages its own headers and navigation.

        Returns:
            Response: A response built from the FlareSolverr solution,
            with extra ``flaresolverr_*`` attributes.

        Raises:
            FlareSolverrUnsupportedMethodError: If *method* is not
                ``GET`` or ``POST``, or if ``json`` data is passed.
            FlareSolverrResponseError: If FlareSolverr returns a
                non-ok status for a reason not related to a challenge.
            FlareSolverrChallengeError: If a challenge, CAPTCHA, or
                timeout was encountered.
        """
        method = method.upper()
        if method not in self._SUPPORTED_METHODS:
            raise FlareSolverrUnsupportedMethodError(
                "FlareSolverr only supports GET and POST requests. "
                "Method '%s' is not supported." % method
            )

        if kwargs.get("json") is not None:
            raise FlareSolverrUnsupportedMethodError(
                "FlareSolverr only supports x-www-form-urlencoded "
                "POST requests. JSON POST is not supported."
            )

        request_kwargs = self._build_request_kwargs(method, url, **kwargs)
        send = getattr(self._rpc.request, method.lower())
        attempts = 0
        while True:
            try:
                with self._lock:
                    resp_data = send(**request_kwargs)
                    return Response(resp_data)
            except FlareSolverrChallengeError:
                if attempts >= self._max_retries:
                    raise
                attempts += 1
                time.sleep(1)

    def close(self):
        """Destroy the FlareSolverr session and close the inherited
        ``requests.Session``."""
        try:
            if self._session_created:
                self._destroy_session()
        finally:
            super(Session, self).close()

    def _build_request_kwargs(self, method, url, **kwargs):
        params = kwargs.get("params")
        if params:
            if isinstance(params, dict):
                encoded_params = urlencode(params)
                if "?" in url:
                    url = url + "&" + encoded_params
                else:
                    url = url + "?" + encoded_params

        request_kwargs = {
            "url": url,
            "session_id": self.session_id,
            "max_timeout": kwargs.get("timeout", self._timeout),
        }

        # POST data
        if method == "POST":
            request_kwargs["data"] = kwargs.get("data")

        # Optional cookies
        request_kwargs["cookies"] = kwargs.get("cookies")

        return request_kwargs

    def _create_session(self):
        """Create a FlareSolverr browser session via RPC."""
        data = self._rpc.session.create(session_id=self._session_id, proxy=self._proxy)
        self._session_id = data.get("session", self._session_id)
        self._session_created = True

    def _destroy_session(self):
        """Destroy the FlareSolverr browser session via RPC."""
        if not self._session_id:
            return
        try:
            self._rpc.session.destroy(self._session_id)
        except Exception:
            return  # Best-effort cleanup
        self._session_created = False


class FlareSolverr(object):
    """
    Attributes:
        status (str): ``"ok"`` on success.
        message (str): Message from FlareSolverr (e.g.
            challenge status).
        user_agent (str): User-Agent used by the headless
            browser.
        start (int): Start timestamp (ms).
        end (int): End timestamp (ms).
        version (str): FlareSolverr server version.
    """

    def __init__(
        self, status="", message="", user_agent="", start=0, end=0, version=""
    ):
        self.status = status
        self.message = message
        self.user_agent = user_agent
        self.start = start
        self.end = end
        self.version = version

    def __repr__(self):
        return "FlareSolverr(status=%r, message=%r, version=%r)" % (
            self.status,
            self.message,
            self.version,
        )


class Response(requests.Response):
    """
    Attributes:
        flaresolverr (FlareSolverr): FlareSolverr metadata
            associated with this response.
    """

    def __init__(self, flaresolverr_data):
        """Initialize from FlareSolverr JSON response."""
        super(Response, self).__init__()

        solution = flaresolverr_data.get("solution", {})

        self.status_code = solution.get("status", 200)
        self.url = solution.get("url", "")
        self.headers = CaseInsensitiveDict(solution.get("headers", {}))

        content = solution.get("response", "")
        if isinstance(content, bytes):
            self._content = content
        else:
            self._content = content.encode("utf-8")
        self.encoding = "utf-8"

        # Cookies
        for cookie in solution.get("cookies", []):
            self.cookies.set(
                cookie.get("name", ""),
                cookie.get("value", ""),
                domain=cookie.get("domain", ""),
                path=cookie.get("path", "/"),
            )

        self.flaresolverr = FlareSolverr(
            status=flaresolverr_data.get("status", ""),
            message=flaresolverr_data.get("message", ""),
            user_agent=solution.get("userAgent", ""),
            start=flaresolverr_data.get("startTimestamp", 0),
            end=flaresolverr_data.get("endTimestamp", 0),
            version=flaresolverr_data.get("version", ""),
        )
