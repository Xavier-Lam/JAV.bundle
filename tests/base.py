# coding=utf-8

import __builtin__

import json
import os
import sys

import unittest

import framework


BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENTS_PATH = os.path.join(BUNDLE_ROOT, "Contents")
CODE_PATH = os.path.join(CONTENTS_PATH, "Code")
LIBS_PATH = os.path.join(CONTENTS_PATH, "Libraries", "Shared")


# Libraries/Shared should take precedence over pip-installed packages
sys.path.insert(0, LIBS_PATH)
sys.path.insert(0, CODE_PATH)
sys.path.insert(0, CONTENTS_PATH)  # for tests to import from Contents/Code


from agents.base import AccessRestrictedError


for t in [
    "Agent",
    "Locale",
    "Log",
    "MessageContainer",
    "Prefs",
    "Proxy",
    "Resource",
    "MetadataSearchResult",
    "TrailerObject",
]:
    setattr(__builtin__, t, getattr(framework, t))


RESOURCES_PATH = os.path.join(CONTENTS_PATH, "Resources")


def _load_resource(filename):
    path = os.path.join(RESOURCES_PATH, filename)
    with open(path, 'r') as f:
        return f.read()


framework.Resource.Load = staticmethod(_load_resource)


class BaseTestCase(unittest.TestCase):
    _default_prefs = None

    @classmethod
    def setUpClass(cls):
        cls._default_prefs = load_prefs()

    def setUp(self):
        Prefs._prefs = dict(self._default_prefs)

    def update_prefs(self, **kwargs):
        Prefs._prefs.update(kwargs)


class AgentTestCase(BaseTestCase):

    agent = None  # type: BaseAgent

    def run(self, result=None):
        skip_access_restricted = os.environ.get("SKIP_ACCESS_RESTRICTED_TESTS", "0") == "1"
        if result is not None:
            original_add_error = result.addError

            def patched_add_error(test, err):
                exc_type, exc_value, tb = err
                if isinstance(exc_value, AccessRestrictedError) and skip_access_restricted:
                    result.addSkip(test, str(exc_value))
                else:
                    original_add_error(test, err)

            result.addError = patched_add_error
        super(AgentTestCase, self).run(result)

    def setUp(self):
        super(AgentTestCase, self).setUp()
        self.update_prefs(
            flaresolverr_url=os.environ.get(
                "FLARESOLVERR_URL", "http://localhost:8191/v1"
            ),
            proxy=os.environ.get(
                "HTTPS_PROXY", os.environ.get("HTTP_PROXY", "")
            ),
        )
        self.agent = self.get_agent_instance()

    def get_agent_instance(self):
        raise NotImplementedError

    # ===================================================================
    # Helper assertion methods for testing agent
    # ===================================================================

    def assertGuessedKeywords(self, name, filename, directory, expected):
        keywords = self.agent.guess_keywords(name, filename, directory)
        self.assertEqual(expected, keywords)

    def assertNegativeGuessedKeywords(self, name, filename, directory):
        keywords = self.agent.guess_keywords(name, filename, directory)
        self.assertEqual([], keywords)

    def assertShouldContributeTo(self, metadata, attribute, new_value):
        self.assertTrue(self.agent.should_contribute_to(
            metadata, attribute, new_value))

    def assertShouldNotContributeTo(self, metadata, attribute, new_value):
        self.assertFalse(self.agent.should_contribute_to(
            metadata, attribute, new_value))

    def assertContributionValue(self, new_value, attribute, current_value):
        self.assertEqual(new_value, self.agent.get_contribution_value(
            attribute, current_value))

    # ===================================================================
    # Helper assertion methods for testing metadata objects
    # ===================================================================

    def assertTitleEquals(self, expected, metadata, msg=None):
        actual = metadata.title
        self.assertEqual(expected, actual, msg)

    def assertJapaneseTitleEquals(self, expected, metadata, msg=None):
        actual = metadata.japanese_title
        self.assertEqual(expected, actual, msg)

    def assertReleaseDateIs(self, expected, metadata, msg=None):
        actual = metadata.release_date
        self.assertEqual(expected, actual, msg)

    def assertStudioIs(self, expected, metadata, msg=None):
        actual = metadata.studio
        self.assertEqual(expected, actual, msg)

    def assertSeriesIs(self, expected, metadata, msg=None):
        actual = metadata.series
        self.assertEqual(expected, actual, msg)

    def assertDurationExists(self, metadata, msg=None):
        actual = metadata.duration
        self.assertIsNotNone(actual, msg)

    def assertActressesInclude(self, expected, metadata, msg=None):
        for name in expected:
            self.assertIn(name, metadata.actresses, msg)

    def assertDirectorsInclude(self, expected, metadata, msg=None):
        for name in expected:
            self.assertIn(name, metadata.directors, msg)

    def assertPostersInclude(self, expected, metadata):
        for i, poster in enumerate(expected):
            if metadata.posters[i] != poster:
                self.fail("Poster %d does not match: expected %r, got %r" % (
                    i, poster, metadata.posters[i]
                ))

    def assertArtInclude(self, expected, metadata):
        for i, art in enumerate(expected):
            if metadata.art[i] != art:
                self.fail("Art %d does not match: expected %r, got %r" % (
                    i, art, metadata.art[i]
                ))

    def assertThemesInclude(self, expected, metadata):
        for i, theme in enumerate(expected):
            if metadata.themes[i] != theme:
                self.fail("Theme %d does not match: expected %r, got %r" % (
                    i, theme, metadata.themes[i]
                ))

    def assertTrailersInclude(self, expected, metadata):
        for i, trailer in enumerate(expected):
            if metadata.trailers[i] != trailer:
                self.fail("Trailer %d does not match: expected %r, got %r" % (
                    i, trailer, metadata.trailers[i]
                ))

    def assertTitleSortEquals(self, expected, metadata, msg=None):
        actual = metadata.title_sort
        self.assertEqual(expected, actual, msg)

    def assertGenresInclude(self, expected, metadata, msg=None):
        actual = set(metadata.genres)
        for genre in expected:
            self.assertIn(genre, actual, msg)

    def assertLabelsInclude(self, expected, metadata, msg=None):
        actual = set(metadata.labels)
        for label in expected:
            self.assertIn(label, actual, msg)

    def assertSummaryExists(self, metadata, msg=None):
        actual = metadata.summary
        self.assertIsNotNone(actual, msg)

    def assertRatingExists(self, metadata, msg=None):
        actual = metadata.rating
        self.assertIsNotNone(actual, msg)

    def assertResourceExists(self, url, mime_type=None):
        import requests

        resp = requests.head(url)
        try:
            resp.raise_for_status()
        except Exception as e:
            self.fail("Resource %r is not accessible: %s" % (url, e))
        if mime_type:
            actual_mime_type = resp.headers.get("Content-Type", "")
            if not actual_mime_type.startswith(mime_type):
                self.fail("Resource %r has unexpected MIME type: expected %r, got %r" % (
                    url, mime_type, actual_mime_type
                ))


def load_prefs():
    prefs_path = os.path.join(BUNDLE_ROOT, "Contents", "DefaultPrefs.json")
    with open(prefs_path) as f:
        data = json.load(f)
    return {item["id"]: item["default"] for item in data}
