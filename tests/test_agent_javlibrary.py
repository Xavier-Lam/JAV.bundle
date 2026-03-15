# coding=utf-8

from base import AgentTestCase, BaseTestCase

import datetime
import unittest

import flaresolverr_session
import requests

from agents import JAVLibrary


class TestJAVLibraryAgent(AgentTestCase):

    def get_agent_instance(self):
        return JAVLibrary(Prefs)

    # ---------------------------------------------------------------------------
    # Search test cases
    # ---------------------------------------------------------------------------

    def test_guess_search_keywords(self):
        self.assertGuessedKeywords(
            u"JBD-226", u"jbd226", u"JBD-226", [u"JBD-226"])
        self.assertGuessedKeywords(
            u"AKA-007", u"aka007", u"AKA-007", [u"AKA-007"])
        self.assertNegativeGuessedKeywords(
            "Caribbean 042215-858",
            "042215-858.mp4",
            "Caribbean 042215-858"
        )

    def test_search_JBD_226(self):
        video_code = "JBD-226"
        results = self.agent.search([video_code], "ja")
        self.assertEqual(1, len(results))
        self.assertEqual("li7ah34", results[0].id)
        self.assertEqual(video_code, results[0].video_code)
        self.assertEqual(u"JBD-226 拷問無残4 篠田ゆう", results[0].title)
        self.assertEqual(100, results[0].score)

    # ---------------------------------------------------------------------------
    # Metadata test cases
    # ---------------------------------------------------------------------------

    def test_metadata_JBD_226(self):
        video_code = "JBD-226"
        agent_id = "li7ah34"
        metadata = self.agent.get_metadata(agent_id, video_code, "ja")
        self.assertTitleEquals(u"JBD-226 拷問無残4 篠田ゆう", metadata)
        self.assertJapaneseTitleEquals(u"JBD-226 拷問無残4 篠田ゆう", metadata)
        self.assertReleaseDateIs(datetime.datetime(2018, 6, 7), metadata)
        self.assertStudioIs(u"アタッカーズ", metadata)
        self.assertDurationExists(metadata)
        self.assertActressesInclude([u"篠田ゆう"], metadata)
        self.assertDirectorsInclude([u"朝霧浄"], metadata)
        self.assertGenresInclude([u"巨乳", u"SM"], metadata)
        self.assertLabelsInclude([u"蛇縛"], metadata)
        self.assertPostersInclude(
            [u"https://pics.dmm.co.jp/mono/movie/adult/jbd226/jbd226ps.jpg"], metadata)
        self.assertArtInclude(
            [u"https://pics.dmm.co.jp/mono/movie/adult/jbd226/jbd226pl.jpg"], metadata)
        self.assertRatingExists(metadata)


class TestJAVLibrarySessionManagement(BaseTestCase):

    def setUp(self):
        super(TestJAVLibrarySessionManagement, self).setUp()
        self.agent = JAVLibrary(Prefs)

    def test_plain_session_without_flaresolverr(self):
        s = self.agent.session
        self.assertIsInstance(s, requests.Session)
        self.assertNotIsInstance(s, flaresolverr_session.Session)

    def test_flaresolverr_session_when_configured(self):
        self.update_prefs(flaresolverr_url="http://localhost:8191/v1")
        s = self.agent.session
        self.assertIsInstance(s, flaresolverr_session.Session)


if __name__ == "__main__":
    unittest.main()
