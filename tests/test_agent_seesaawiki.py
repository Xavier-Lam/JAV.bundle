# coding=utf-8

from base import BaseTestCase

import unittest

import mock

from agents.seesaawiki import SeesaaWiki


# ---------------------------------------------------------------------------
# Test data — add new entries here to extend coverage
# ---------------------------------------------------------------------------

# (video_code, [expected_actress_name, ...])
# Each tuple asserts that searching the wiki for *video_code* discovers the
# listed actresses.
VIDEO_CODE_TEST_CASES = [
    ("JBD-226", [u"篠田ゆう"]),
    ("DRPT-009", [u"綾川ふみ"]),
    ("MEYD-514", [u"篠田ゆう", u"黒川すみれ"]),
]

# (input_name, expected_canonical_name)
# Each tuple asserts that looking up *input_name* on the wiki yields
# *expected_canonical_name* (following redirects where necessary).
ACTRESS_NAME_TEST_CASES = [
    (u"白石みお", u"かなで自由"),
    (u"篠田ゆう", u"篠田ゆう"),
]


# ---------------------------------------------------------------------------
# get_actresses tests (by unique ID)
# ---------------------------------------------------------------------------

class TestGetActresses(BaseTestCase):
    """Verify :meth:`SeesaaWiki.get_actresses` discovers correct actresses."""

    def setUp(self):
        super(TestGetActresses, self).setUp()
        self.update_prefs(seesaawiki_enabled=True)
        self.agent = SeesaaWiki(Prefs)


def _make_get_actresses_test(video_code, expected_names):
    """Factory that creates a test method for *video_code*."""

    def test_method(self):
        actresses = self.agent.discover_actresses(video_code)
        for expected in expected_names:
            self.assertIn(
                expected,
                actresses,
                u"Expected actress '{}' not found in {} for {}".format(
                    expected, actresses, video_code,
                ),
            )

    return test_method


for _vc, _names in VIDEO_CODE_TEST_CASES:
    _test_name = "test_get_actresses_{}".format(_vc.replace("-", "_"))
    setattr(TestGetActresses, _test_name, _make_get_actresses_test(_vc, _names))


# ---------------------------------------------------------------------------
# get_actress_name tests (name correction / redirect following)
# ---------------------------------------------------------------------------

class TestGetActressName(BaseTestCase):
    """Verify :meth:`SeesaaWiki.get_actress_name` returns canonical names."""

    def setUp(self):
        super(TestGetActressName, self).setUp()
        self.update_prefs(seesaawiki_enabled=True)
        self.agent = SeesaaWiki(Prefs)


def _make_get_actress_name_test(input_name, expected_name):
    """Factory that creates a test method for *input_name*."""

    def test_method(self):
        result = self.agent.get_actress_name(input_name)
        self.assertEqual(
            result,
            expected_name,
            u"Expected '{}' but got '{}' for input '{}'".format(
                expected_name, result, input_name,
            ),
        )

    return test_method


for i, (_inp, _exp) in enumerate(ACTRESS_NAME_TEST_CASES):
    _test_name = "test_name_{}".format(i)
    setattr(TestGetActressName, _test_name,
            _make_get_actress_name_test(_inp, _exp))


# ---------------------------------------------------------------------------
# Cache tests
# ---------------------------------------------------------------------------

class TestActressNameCache(BaseTestCase):
    """Verify that :meth:`SeesaaWiki.get_actress_name` uses its internal cache."""

    def setUp(self):
        super(TestActressNameCache, self).setUp()
        self.update_prefs(seesaawiki_enabled=True)
        self.agent = SeesaaWiki(Prefs)

    def test_second_call_uses_cache(self):
        self.agent.cache = {}
        with mock.patch.object(
            self.agent, "search_wiki",
            return_value=[(u"篠田ゆう",
                           "https://seesaawiki.jp/w/sougouwiki/d/%bc%c4%c5%c4%a4%e6%a4%a6")]
        ) as mock_search, mock.patch.object(
            self.agent, "resolve_page_name",
            return_value=u"篠田ゆう"
        ) as mock_resolve:
            first = self.agent.get_actress_name(u"篠田ゆう")
            second = self.agent.get_actress_name(u"篠田ゆう")

        self.assertEqual(first, second)
        mock_search.assert_called_once()
        mock_resolve.assert_called_once()

    def test_cache_stores_canonical_name(self):
        self.agent.cache = {}
        input_name = u"白石みお"  # 白石みお
        canonical = u"かなで自由"  # かなで自由
        with mock.patch.object(
            self.agent, "search_wiki",
            return_value=[
                (canonical, "https://seesaawiki.jp/w/sougouwiki/d/dummy")]
        ), mock.patch.object(
            self.agent, "resolve_page_name",
            return_value=canonical
        ):
            self.agent.get_actress_name(input_name)

        self.assertIn(input_name, self.agent.cache)
        self.assertEqual(self.agent.cache[input_name], canonical)

    def test_cache_is_keyed_per_name(self):
        self.agent.cache = {}
        cases = [
            (u"篠田ゆう", u"篠田ゆう"),
            (u"白石みお", u"かなで自由"),
        ]

        for inp, canonical in cases:
            with mock.patch.object(
                self.agent, "search_wiki",
                return_value=[
                    (canonical, "https://seesaawiki.jp/w/sougouwiki/d/dummy")]
            ), mock.patch.object(
                self.agent, "resolve_page_name",
                return_value=canonical
            ):
                self.agent.get_actress_name(inp)

        for inp, canonical in cases:
            self.assertIn(inp, self.agent.cache)
            self.assertEqual(self.agent.cache[inp], canonical)

    def test_cache_miss_on_unknown_name_stores_original(self):
        self.agent.cache = {}
        unknown = u"UNKNOWN_XYZ_99999"
        with mock.patch.object(self.agent, "search_wiki", return_value=[]) as mock_search:
            self.agent.get_actress_name(unknown)
            self.agent.get_actress_name(unknown)

        mock_search.assert_called_once()
        self.assertEqual(self.agent.cache[unknown], unknown)

    def test_pre_populated_cache_is_respected(self):
        self.agent.cache = {u"白石みお": u"かなで自由"}
        with mock.patch.object(self.agent, "search_wiki") as mock_search:
            result = self.agent.get_actress_name(u"白石みお")

        mock_search.assert_not_called()
        self.assertEqual(result, u"かなで自由")


if __name__ == "__main__":
    unittest.main()
