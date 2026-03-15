# coding=utf-8
"""Unit tests for the :class:`GFriends` avatar agent."""

from base import BaseTestCase

import unittest

import mock
import requests

from agents.gfriends import (
    GFriends,
    FILETREE_URL,
)


class TestGFriendsGetAvatar(BaseTestCase):

    def setUp(self):
        super(TestGFriendsGetAvatar, self).setUp()
        self.agent = GFriends(Prefs)

    # [(actress_name, expected_photo_url), ...]
    test_cases = [
        (
            u"かなで自由",
            u"https://raw.githubusercontent.com/xinxin8816/gfriends/master/Content/v-Attackers/%E3%81%8B%E3%81%AA%E3%81%A7%E8%87%AA%E7%94%B1.jpg",
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
            resp = requests.head(result)
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

    @mock.patch("agents.gfriends.requests.get")
    def test_initialize_failure_leaves_uninitialised(self, mock_get):
        mock_get.return_value = self.make_mock_response(status_code=500)

        self.agent.initialize()

        self.assertFalse(self.agent.initialized)
        self.assertEqual(self.agent.resource, {})

    @mock.patch("agents.gfriends.requests.get")
    def test_initialize_called_only_once(self, mock_get):
        mock_get.return_value = self.make_mock_response(
            json_data={"Content": {}})

        self.agent.initialize()
        self.agent.initialize()

        self.assertEqual(mock_get.call_count, 1)

    def make_mock_response(self, status_code=200, json_data=None):
        resp = mock.MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        return resp


if __name__ == "__main__":
    unittest.main()
