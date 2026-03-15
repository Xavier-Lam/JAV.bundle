# coding=utf-8

from base import AgentTestCase

import datetime
import unittest

from agents.caribpr import CaribbeanPr, STUDIO_NAME


class TestCaribbeanPrAgent(AgentTestCase):
    def get_agent_instance(self):
        return CaribbeanPr(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            u"カリビアンコムプレミアム 072215_284",
            u"072215_284.mp4",
            u"072215_284",
            [u"072215_284"],
        )
        # Negative — MMDDYY-NNN (Caribbean, not CaribbeanPr)
        self.assertNegativeGuessedKeywords(
            u"Caribbean 042215-858",
            u"042215-858.mp4",
            u"Caribbean 042215-858",
        )
        # Negative — different studio
        self.assertNegativeGuessedKeywords(
            u"JBD-226",
            u"JBD-226.mp4",
            u"JBD-226",
        )
        # Negative — 1PON studio with similar ID format but no CaribbeanPr keyword
        self.assertNegativeGuessedKeywords(
            u"hhd800.com@072122_001-1PON.mp4",
            u"hhd800.com@072122_001-1PON.mp4",
            u"一本道 072122_001 男を一瞬でその気にさせる罪な女",
        )

    def test_search_072215_284(self):
        video_code = u"072215_284"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(video_code, results[0].id)
        self.assertEqual(u"カリビアンコムプレミアム 072215_284 鬼イキトランス 12",
                         results[0].title)
        self.assertEqual(100, results[0].score)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_072215_284(self):
        video_code = u"072215_284"
        metadata = self.agent.get_metadata(video_code, video_code, "ja")
        self.assertTitleEquals(
            u"カリビアンコムプレミアム 072215_284 鬼イキトランス 12 江波りゅう", metadata)
        self.assertJapaneseTitleEquals(
            u"カリビアンコムプレミアム 072215_284 鬼イキトランス 12 江波りゅう", metadata)
        self.assertReleaseDateIs(datetime.datetime(2015, 7, 22), metadata)
        self.assertStudioIs(u"カリビアンコム", metadata)
        self.assertDurationExists(metadata)
        self.assertActressesInclude([u"江波りゅう"], metadata)
        self.assertPostersInclude(
            [u"https://www.caribbeancompr.com/moviepages/072215_284/images/main_s.jpg"], metadata)
        self.assertArtInclude(
            [u"https://www.caribbeancompr.com/moviepages/072215_284/images/l_l.jpg"], metadata)
        self.assertTrailersInclude(
            [u"https://smovie.caribbeancompr.com/sample/movies/072215_284/480p.mp4"], metadata)
        self.assertTitleSortEquals(u"カリビアンコムプレミアム 150722-284", metadata)
        self.assertGenresInclude([u"AV女優", u"美乳", u"中出し", u"潮吹き"], metadata)
        self.assertSummaryExists(metadata)


if __name__ == "__main__":
    unittest.main()
