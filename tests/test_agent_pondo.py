# coding=utf-8

from base import AgentTestCase

import datetime
import unittest

from agents.pondo import Pondo, STUDIO_NAME


# ---------------------------------------------------------------------------
# Test-case data
# ---------------------------------------------------------------------------

METADATA_TEST_CASES = [
    ("090111_166", {
        "title": u"一本道 090111_166 エロ過ぎる潮吹きアイドル",
        "studio": STUDIO_NAME,
        "originally_available_at": datetime.datetime(2011, 9, 1),
        "year": 2011,
        "duration": 2987000,
        "roles": [u"羽月希"],
        "genres": [u"AV女優", u"ロリ", u"美尻",
                   u"巨乳", u"美乳", u"潮吹き"],
        "tags": [],
        "rating": True,
        "summary": True,
        "posters": ["090111_166/images/thum_b.jpg"],
        "art": ["090111_166/str.jpg"],
        "trailer": True,
    }),
]

# ---------------------------------------------------------------------------
# should_search test cases
# (expected_bool, media_kwargs)
# ---------------------------------------------------------------------------

SHOULD_SEARCH_TEST_CASES = [
    # Positive -- 1Pondo keyword + MMDDYY_NNN movie-ID pattern
    (True, "1pon 090111_166"),
    (True, {"name": u"一本道 090111_166"}),
    # Negative -- no MMDDYY_NNN pattern in text
    (False, "072215-284"),
    (False, "JBD-226"),
]

# ---------------------------------------------------------------------------
# should_update test cases
# (expected_bool, metadata_id_string_or_PlexMetadata)
# ---------------------------------------------------------------------------

SHOULD_UPDATE_TEST_CASES = [
    # Positive -- agent_id present, no studio set
    (True, "090111_166,1Pondo.090111_166"),
    # Negative -- no agent_id in metadata
    (False, "090111_166"),
]

# ---------------------------------------------------------------------------
# search test cases
# (media_kwargs, expected_video_code)
# ---------------------------------------------------------------------------

SEARCH_TEST_CASES = [
    ("1pon 090111_166", "090111_166", u"一本道 090111_166 エロ過ぎる潮吹きアイドル"),
]


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestPondoAgent(AgentTestCase):
    def get_agent_instance(self):
        return Pondo(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            u"090111_166",
            u"090111_166.mp4",
            u"一本道 090111_166 エロ過ぎる潮吹きアイドル",
            [u"090111_166"]
        )
        self.assertNegativeGuessedKeywords(
            u"090111_166",
            u"090111_166.mp4",
            u"Caribpr 090111_166",
        )

    def test_search_090111_166(self):
        video_code = "090111_166"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(video_code, results[0].id)
        self.assertEqual(u"一本道 090111_166 エロ過ぎる潮吹きアイドル", results[0].title)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_090111_166(self):
        video_code = "090111_166"
        metadata = self.agent.get_metadata(video_code, video_code, "ja")
        self.assertTitleEquals(u"一本道 090111_166 エロ過ぎる潮吹きアイドル 羽月希", metadata)
        self.assertJapaneseTitleEquals(
            u"一本道 090111_166 エロ過ぎる潮吹きアイドル 羽月希", metadata)
        self.assertReleaseDateIs(datetime.datetime(2011, 9, 1), metadata)
        self.assertStudioIs(STUDIO_NAME, metadata)
        self.assertDurationExists(metadata)
        self.assertActressesInclude([u"羽月希"], metadata)
        self.assertPostersInclude(
            [u"https://www.1pondo.tv/moviepages/090111_166/images/thum_b.jpg"], metadata)
        self.assertArtInclude(
            [u"https://www.1pondo.tv/assets/sample/090111_166/str.jpg"], metadata)
        self.assertTrailersInclude(
            [u"https://smovie.1pondo.tv/sample/movies/090111_166/480p.mp4"], metadata)
        self.assertGenresInclude([u"AV女優", u"ロリ", u"美尻",
                                  u"巨乳", u"美乳", u"潮吹き"], metadata)


if __name__ == "__main__":
    unittest.main()
