# coding=utf-8

from base import AgentTestCase

import datetime
import unittest

from agents.mgstage import MGStage


class TestMGStageAgent(AgentTestCase):
    def get_agent_instance(self):
        return MGStage(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            u"AKA-007",
            u"AKA-007.mp4",
            u"AKA-007 ボンデージトランスパーティー ～ドMご奉仕ペット3匹の大乱交～",
            [u"AKA-007"]
        )
        self.assertNegativeGuessedKeywords(
            u"Caribbean 042215-858",
            u"042215-858.mp4",
            u"Caribbean 042215-858"
        )

    def test_search_AKA_007(self):
        video_code = u"AKA-007"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(video_code, results[0].id)
        self.assertEqual(
            u"AKA-007 ボンデージトランスパーティー ～ドMご奉仕ペット3匹の大乱交～", results[0].title)
        self.assertEqual(100, results[0].score)

    def test_search_MILK_216(self):
        video_code = u"MILK-216"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual("337MILK-216", results[0].id)
        self.assertEqual(
            u"MILK-216 出張マッサージ師の鼠径部きわきわ施術で下着に染みができるほどのつゆだくマ○コに豹変 旦那とは違う凄テクと絶倫チ○ポで壮絶に寝取られた話。岬さくら", results[0].title)
        self.assertEqual(100, results[0].score)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_AKA_007(self):
        video_code = u"AKA-007"
        metadata = self.agent.get_metadata(video_code, video_code, "ja")
        self.assertTitleEquals(
            u"AKA-007 ボンデージトランスパーティー ～ドMご奉仕ペット3匹の大乱交～", metadata)
        self.assertJapaneseTitleEquals(
            u"AKA-007 ボンデージトランスパーティー ～ドMご奉仕ペット3匹の大乱交～", metadata)
        self.assertReleaseDateIs(datetime.datetime(2015, 6, 6), metadata)
        self.assertStudioIs(u"プレステージ", metadata)
        self.assertSeriesIs(None, metadata)
        self.assertDurationExists(metadata)
        self.assertPostersInclude(
            [u"https://image.mgstage.com/images/prestige/aka/007/pf_o1_aka-007.jpg"], metadata)
        self.assertArtInclude(
            [u"https://image.mgstage.com/images/prestige/aka/007/pb_e_aka-007.jpg"], metadata)
        self.assertTrailersInclude(
            [u"https://sample.mgstage.com/sample/prestige/aka/007/AKA-007.mp4"], metadata)
        self.assertTitleSortEquals(
            u"AKA-007 ボンデージトランスパーティー ～ドMご奉仕ペット3匹の大乱交～", metadata)
        self.assertGenresInclude([u"巨乳", u"ボンテージ", u"人妻"], metadata)
        self.assertSummaryExists(metadata)
        self.assertRatingExists(metadata)


if __name__ == "__main__":
    unittest.main()
