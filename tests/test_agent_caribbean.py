# coding=utf-8

from base import AgentTestCase

import datetime
import unittest

from agents.caribbean import Caribbean, STUDIO_NAME


class TestCaribbeanAgent(AgentTestCase):
    def get_agent_instance(self):
        return Caribbean(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            "Caribbean 042215-858",
            "042215-858.mp4",
            "Caribbean 042215-858",
            ["042215-858"]
        )
        self.assertNegativeGuessedKeywords(
            "042215_858",
            "042215-858.mp4",
            "042215_858",
        )

    def test_search_042215_858(self):
        video_code = "042215-858"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(video_code, results[0].id)
        self.assertEqual(
            u"カリビアンコム 042215-858 THE 未公開 〜机の下のおしゃぶり中毒女〜", results[0].title)
        self.assertEqual(100, results[0].score)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_042215_858(self):
        video_code = "042215-858"
        metadata = self.agent.get_metadata(video_code, video_code, "ja")
        self.assertTitleEquals(
            u"カリビアンコム 042215-858 THE 未公開 〜机の下のおしゃぶり中毒女〜", metadata)
        self.assertJapaneseTitleEquals(
            u"カリビアンコム 042215-858 THE 未公開 〜机の下のおしゃぶり中毒女〜", metadata)
        self.assertReleaseDateIs(datetime.datetime(2015, 4, 22), metadata)
        self.assertStudioIs(STUDIO_NAME, metadata)
        self.assertSeriesIs(u"THE 未公開", metadata)
        self.assertDurationExists(metadata)
        self.assertActressesInclude(
            [u"尾嶋みゆき", u"松岡すず", u"江波りゅう", u"石原あみ"], metadata)
        self.assertPostersInclude(
            ["https://www.caribbeancom.com/moviepages/042215-858/images/jacket.jpg"], metadata)
        self.assertArtInclude(
            ["https://www.caribbeancom.com/moviepages/042215-858/images/l_l.jpg"], metadata)
        self.assertTrailersInclude(
            ["https://smovie.caribbeancom.com/sample/movies/042215-858/sample_m.mp4"], metadata)
        self.assertTitleSortEquals(u"カリビアンコム 150422-858", metadata)
        self.assertGenresInclude([u"オリジナル動画", u"口内発射"], metadata)
        self.assertSummaryExists(metadata)
        self.assertRatingExists(metadata)

    def test_metadata_031015_824(self):
        video_code = "031015-824"
        metadata = self.agent.get_metadata(video_code, video_code, "ja")
        self.assertTitleEquals(u"カリビアンコム 031015-824 鬼イキトランス12", metadata)
        self.assertPostersInclude(
            ["https://www.caribbeancompr.com/moviepages/072215_284/images/main_s.jpg"], metadata)


if __name__ == "__main__":
    unittest.main()
