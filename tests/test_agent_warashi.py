# coding=utf-8

from base import BaseTestCase

import unittest

import requests
from bs4 import BeautifulSoup

from agents import WarashiPornstars


class TestWarashiGetAvatar(BaseTestCase):

    def setUp(self):
        super(TestWarashiGetAvatar, self).setUp()
        self.agent = WarashiPornstars(Prefs)

    # [(actress_name, expected_photo_url), ...]
    test_cases = [
        (
            u"三上悠亜",
            u"https://warashi-asian-pornstars.fr/WAPdB-img/pornostars-f/y/u/2922/yua-mikami/profil-0/large/wapdb-yua-mikami-pornostar-asiatique.warashi-asian-pornstars.fr.jpg",
        ),
    ]

    def test_get_avatar(self):
        for name, expected_url in self.test_cases:
            result = self.agent.get_avatar(name, "ja")
            self.assertEqual(
                result,
                expected_url,
                "Unexpected URL for actress {0!r}".format(name),
            )
            resp = self.agent.session.head(result)
            self.assertEqual(
                resp.status_code,
                200,
                "URL {0!r} is not accessible for actress {1!r}".format(
                    result, name),
            )
            self.assertTrue(
                resp.headers.get("Content-Type", "").startswith("image/"),
                "URL {0!r} does not point to an image for actress {1!r}".format(
                    result, name),
            )
            self.assertEqual(result.score, 50,
                             "Unexpected score for actress {0!r}".format(name))

    def test_get_avatar_not_found_returns_none(self):
        result = self.agent.get_avatar(u"ZZZNOBODYXXX99999", "ja")
        self.assertIsNone(result)

    def test_get_avatar_stores_in_cache(self):
        name = u"三上悠亜"
        result = self.agent.get_avatar(name, "ja")
        self.assertIn(name, self.agent.cache)
        self.assertEqual(self.agent.cache[name], result)

    def test_get_avatar_returns_cached_result(self):
        name = u"三上悠亜"
        result1 = self.agent.get_avatar(name, "ja")
        # Poison the cache to confirm the second call reads from it
        self.agent.cache[name] = "https://warashi-asian-pornstars.fr/cached"
        result2 = self.agent.get_avatar(name, "ja")
        self.assertEqual(result2, "https://warashi-asian-pornstars.fr/cached")

    # Fallback URL from the search-results thumbnail for 三上悠亜
    fallback_url = (
        u"https://warashi-asian-pornstars.fr"
        u"/WAPdB-img/pornostars-f/y/u/2922/yua-mikami/preview/mini"
        u"/wapdb-yua-mikami-pornostar-asiatique.warashi-asian-pornstars.fr.jpg"
    )

    def test_get_avatar_falls_back_when_detail_request_fails(self):
        name = u"三上悠亜"
        original_fetch_url = self.agent.fetch_url

        def failing_fetch_url(url):
            raise requests.exceptions.ConnectionError("simulated failure")

        self.agent.fetch_url = failing_fetch_url
        result = self.agent.get_avatar(name, "ja")
        self.agent.fetch_url = original_fetch_url

        self.assertEqual(result, self.fallback_url)
        self.assertEqual(result.score, 20,
                         "Unexpected score for fallback URL for actress {0!r}".format(name))

    def test_get_avatar_falls_back_when_detail_has_no_image(self):
        name = u"三上悠亜"
        original_fetch_url = self.agent.fetch_url

        def no_img_fetch_url(url):
            return BeautifulSoup(u"<html><body></body></html>", "html.parser")

        self.agent.fetch_url = no_img_fetch_url
        result = self.agent.get_avatar(name, "ja")
        self.agent.fetch_url = original_fetch_url

        self.assertEqual(result, self.fallback_url)
        self.assertEqual(result.score, 20,
                         "Unexpected score for fallback URL for actress {0!r}".format(name))


if __name__ == "__main__":
    unittest.main()
