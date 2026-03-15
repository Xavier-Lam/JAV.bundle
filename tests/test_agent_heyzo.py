# coding=utf-8

from base import AgentTestCase

import datetime
import unittest

from agents.heyzo import Heyzo, STUDIO_NAME


class TestHeyzoAgent(AgentTestCase):
    def get_agent_instance(self):
        return Heyzo(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            u"Heyzo 0647",
            u"042215-858.mp4",
            u"Heyzo 0647 他人妻味～挑発するシルキィ豊満ボディ～ - 尾嶋みゆき",
            [u"0647"]
        )
        self.assertNegativeGuessedKeywords(
            u"042215_858",
            u"042215-858.mp4",
            u"042215_858",
        )

    def test_search_0647(self):
        video_code = "0647"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(video_code, results[0].id)
        self.assertEqual(
            u"Heyzo 0647 他人妻味～挑発するシルキィ豊満ボディ～ - 尾嶋みゆき", results[0].title)
        self.assertEqual(100, results[0].score)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_0647(self):
        video_code = "0647"
        metadata = self.agent.get_metadata(video_code, video_code, "ja")
        self.assertTitleEquals(
            u"Heyzo 0647 他人妻味～挑発するシルキィ豊満ボディ～ - 尾嶋みゆき", metadata)
        self.assertJapaneseTitleEquals(
            u"Heyzo 0647 他人妻味～挑発するシルキィ豊満ボディ～ - 尾嶋みゆき", metadata)
        self.assertReleaseDateIs(datetime.datetime(2014, 7, 27), metadata)
        self.assertStudioIs(STUDIO_NAME, metadata)
        self.assertSeriesIs(u"他人妻味(ひとつまみ)", metadata)
        self.assertActressesInclude([u"尾嶋みゆき"], metadata)
        self.assertPostersInclude(
            [u"https://www.heyzo.com/contents/3000/0647/images/thumbnail.jpg"], metadata)
        self.assertArtInclude(
            [u"https://www.heyzo.com/contents/3000/0647/images/player_thumbnail.jpg"], metadata)
        self.assertTrailersInclude(
            [u"https://hls.heyzo.com/sample/3000/0647/mb.m3u8"], metadata)
        self.assertTitleSortEquals(u"Heyzo 0647", metadata)
        self.assertGenresInclude([u"69", u"中出し"], metadata)
        self.assertSummaryExists(metadata)
        self.assertRatingExists(metadata)


if __name__ == "__main__":
    unittest.main()
