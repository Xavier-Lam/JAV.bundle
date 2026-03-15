# coding=utf-8
"""Unit tests for :class:`TokyoHot` agent.

Test cases are defined as data in the module-level constants.  Adding a
new test case requires only appending to the relevant list -- no test code
changes are needed.
"""

from base import AgentTestCase

import datetime
import unittest

from agents.tokyohot import DEFAULT_STUDIO, TokyoHot


class TestTokyoHotAgent(AgentTestCase):
    def get_agent_instance(self):
        return TokyoHot(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            u"Tokyo-Hot n0820",
            u"n0820.mp4",
            u"Tokyo-Hot n0820",
            [u"n0820"]
        )
        self.assertNegativeGuessedKeywords(
            u"n0820",
            u"n0820.mp4",
            u"Tokyo n0820",
        )

    def test_search_n0820(self):
        video_code = "n0820"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual("21044", results[0].id)
        self.assertEqual(u"東熱 n0820 Wカン悠希めい/武井麻希", results[0].title)
        self.assertEqual(100, results[0].score)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_n0820(self):
        video_code = "n0820"
        agent_id = "21044"
        metadata = self.agent.get_metadata(agent_id, video_code, "ja")
        self.assertTitleEquals(u"東熱 n0820 Wカン悠希めい/武井麻希", metadata)
        self.assertJapaneseTitleEquals(u"東熱 n0820 Wカン悠希めい/武井麻希", metadata)
        self.assertReleaseDateIs(datetime.datetime(2013, 2, 1), metadata)
        self.assertStudioIs(DEFAULT_STUDIO, metadata)
        self.assertDurationExists(metadata)
        self.assertActressesInclude([u"悠希めい", u"武井麻希"], metadata)
        self.assertPostersInclude(
            [u"https://my.cdn.tokyo-hot.com/media/21044/package/_v.jpg"], metadata)
        self.assertArtInclude(
            [u"https://my.cdn.tokyo-hot.com/media/21044/jacket/n0820.jpg"], metadata)
        self.assertTrailersInclude(
            [u"https://my.cdn.tokyo-hot.com/media/samples/21044.mp4"], metadata)
        self.assertEqual(
            u"https://my.cdn.tokyo-hot.com/media/21044/list_image/n0820%201280x720/820x462_default.jpg", metadata.trailers[0].thumb)
        self.assertTitleSortEquals(u"Tokyo-Hot n0820", metadata)
        self.assertGenresInclude([u"輪姦中出し", u"中出し"], metadata)
        self.assertSummaryExists(metadata)


if __name__ == "__main__":
    unittest.main()
