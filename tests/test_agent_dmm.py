# coding=utf-8

from base import AgentTestCase

import datetime
import unittest

from agents.dmm import DMM


class TestDMMAgent(AgentTestCase):
    def get_agent_instance(self):
        return DMM(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            u"JBD-226", u"jbd226", u"JBD-226", [u"JBD-226"])
        self.assertGuessedKeywords(
            u"AKA-007", u"aka007", u"AKA-007", [u"AKA-007"])
        self.assertNegativeGuessedKeywords(
            u"random text", u"random text", u"random text")
        self.assertNegativeGuessedKeywords(u"12345", u"12345", u"12345")

    def test_search_JBD_226(self):
        video_code = "JBD-226"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(u"mono_dvd_jbd226", results[0].id)
        self.assertEqual(video_code, results[0].video_code)
        self.assertEqual(u"JBD-226 拷問無残4 篠田ゆう", results[0].title)
        self.assertEqual(100, results[0].score)

    def test_search_MVG_109(self):
        video_code = "MVG-109"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(u"mono_dvd_mvg109", results[0].id)
        self.assertEqual(video_code, results[0].video_code)
        self.assertEqual(
            u"MVG-109 3連休の無人の学校で緊縛調教されマゾ堕ちしていく巨乳女教師 あやせ舞菜", results[0].title)
        self.assertEqual(100, results[0].score)

    def test_search_PRTD_033(self):
        video_code = "PRTD-033"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(u"mono_dvd_prtd033", results[0].id)
        self.assertEqual(video_code, results[0].video_code)
        self.assertEqual(
            u"PRTD-033 男よりも才能・美貌溢れる最強W女雀士 アナル中出し凌●輪● 沙月恵奈 花狩まい", results[0].title)
        self.assertEqual(100, results[0].score)

    def test_search_CXD_017(self):
        video_code = "CXD-017"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(u"mono_dvd_24cxd017", results[0].id)
        self.assertEqual(video_code, results[0].video_code)
        self.assertEqual(
            u"CXD-017 誘惑、女教師。葉山さゆり", results[0].title)
        self.assertEqual(100, results[0].score)

    def test_search_IBW_431(self):
        video_code = "IBW-431"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual(u"mono_dvd_504ibw431z", results[0].id)
        self.assertEqual(video_code, results[0].video_code)
        self.assertEqual(
            u"IBW-431 親には内緒の妹近親相姦旅行 かれん1○才", results[0].title)
        self.assertEqual(100, results[0].score)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_JBD_226(self):
        video_code = "JBD-226"
        agent_id = "mono_dvd_jbd226"
        metadata = self.agent.get_metadata(agent_id, video_code, "ja")
        self.assertTitleEquals(u"JBD-226 拷問無残4 篠田ゆう", metadata)
        self.assertJapaneseTitleEquals(u"JBD-226 拷問無残4 篠田ゆう", metadata)
        self.assertReleaseDateIs(datetime.datetime(2018, 6, 7), metadata)
        self.assertStudioIs(u"アタッカーズ", metadata)
        self.assertSeriesIs(u"拷問無残", metadata)
        self.assertDurationExists(metadata)
        self.assertActressesInclude([u"篠田ゆう"], metadata)
        self.assertDirectorsInclude([u"朝霧浄"], metadata)
        self.assertGenresInclude([u"巨乳", u"SM", u"単体作品", u"縛り・緊縛"], metadata)
        self.assertLabelsInclude([u"蛇縛"], metadata)
        self.assertPostersInclude(
            [u"https://pics.dmm.co.jp/mono/movie/adult/jbd226/jbd226ps.jpg"], metadata)
        self.assertArtInclude(
            [u"https://pics.dmm.co.jp/mono/movie/adult/jbd226/jbd226pl.jpg"], metadata)
        self.assertTrailersInclude(
            [u"https://cc3001.dmm.co.jp/pv/N3d6RBwgN031ODtblqFcun1SGLPz63C4smMnjjuUtNtwhFPIG7vbCwofa66db/jbd00226_dmb_w.mp4"], metadata)
        self.assertSummaryExists(metadata)
        self.assertRatingExists(metadata)

    def test_metadata_XVSR_316(self):
        video_code = "XVSR-316"
        agent_id = "mono_dvd_xvsr316"
        metadata = self.agent.get_metadata(agent_id, video_code, "ja")
        self.assertTitleEquals(
            u"XVSR-316 大槻ひびきとイチャLOVE中出しデート", metadata)
        self.assertPostersInclude(
            [u"https://pics.dmm.co.jp/mono/movie/adult/xvsr316so/xvsr316sops.jpg"], metadata)
        self.assertArtInclude(
            [u"https://pics.dmm.co.jp/mono/movie/adult/xvsr316so/xvsr316sopl.jpg"], metadata)

    def test_metadata_PRTD_033(self):
        video_code = "PRTD-033"
        agent_id = "rental_ppr_4prtd033"
        metadata = self.agent.get_metadata(agent_id, video_code, "ja")
        self.assertTitleEquals(
            u"PRTD-033 男よりも才能・美貌溢れる最強W女雀士 アナル中出し凌●輪● 沙月恵奈 花狩まい", metadata)
        self.assertReleaseDateIs(datetime.datetime(2024, 4, 24), metadata)
        self.assertStudioIs(u"プレミアム", metadata)
        self.assertSeriesIs(None, metadata)
        self.assertLabelsInclude([u"強く気高い美女たち"], metadata)
        self.assertGenresInclude([u"辱め", u"淫乱・ハード系"], metadata)
        self.assertPostersInclude(
            [u"https://pics.dmm.co.jp/mono/movie/4prtd033/4prtd033ps.jpg"], metadata)
        self.assertArtInclude(
            [u"https://pics.dmm.co.jp/mono/movie/4prtd033/4prtd033pl.jpg"], metadata)
        self.assertTrailersInclude(
            [u"https://cc3001.dmm.co.jp/pv/MRM9EBUxHTteFUziyhWulHG2L08v0wcSpadyXJ-Pzo7_rneWjVAjQsW35SHXhs/prtd00033mhb.mp4"], metadata)

    # ---------------------------------------------------------------------------
    # Utils test cases
    # ---------------------------------------------------------------------------

    def test_normalize_cid(self):
        self.assertEqual(u"jbd226", self.agent.normalize_cid(u"7jbd226"))
        self.assertEqual(u"jbd226", self.agent.normalize_cid(u"jbd226"))
        self.assertEqual(u"fsdss872", self.agent.normalize_cid(u"1fsdss872r"))
        self.assertEqual(u"fsdss872", self.agent.normalize_cid(u"1fsdss872"))
        self.assertEqual(u"gma065", self.agent.normalize_cid(u"gma065bod"))
        self.assertEqual(u"dcxd017", self.agent.normalize_cid(u"h_1711dcxd017"))


if __name__ == "__main__":
    unittest.main()
