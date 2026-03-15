# coding=utf-8

from base import BaseTestCase

import json
import re

import mock
import unittest

from Code import Start, ValidatePrefs


class TestValidatePrefs(BaseTestCase):

    def test_valid_http_url(self):
        self.update_prefs(
            flaresolverr_url="http://localhost:8191/v1",
            proxy=""
        )
        result = ValidatePrefs()
        self.assertIsNone(result)

    def test_valid_https_url(self):
        self.update_prefs(
            flaresolverr_url="https://solverr.example.com/v1",
            proxy=""
        )
        result = ValidatePrefs()
        self.assertIsNone(result)

    def test_invalid_no_scheme(self):
        self.update_prefs(
            flaresolverr_url="localhost:8191/v1",
            proxy=""
        )
        result = ValidatePrefs()
        self.assertIsInstance(result, MessageContainer)
        self.assertEqual(result.message, "Flaresolverr URL is not a valid URL.")

    def test_invalid_plain_text(self):
        self.update_prefs(
            flaresolverr_url="not-a-url",
            proxy=""
        )
        result = ValidatePrefs()
        self.assertIsInstance(result, MessageContainer)
        self.assertEqual(result.message, "Flaresolverr URL is not a valid URL.")

    def test_empty_url_is_valid(self):
        self.update_prefs(
            flaresolverr_url="",
            proxy=""
        )
        result = ValidatePrefs()
        self.assertIsNone(result)

    def test_whitespace_only_is_valid(self):
        self.update_prefs(
            flaresolverr_url="   ",
            proxy=""
        )
        result = ValidatePrefs()
        self.assertIsNone(result)


class TestPrefsLogging(BaseTestCase):

    def test_start_logs_all_prefs(self):
        with mock.patch.object(Log, "Info") as mock_info:
            Start()
        mock_info.assert_called_once()
        data = mock_info.call_args[0][1]
        for item in data:
            key, value = item
            self.assertEqual(value, Prefs[key],
                             "Logged value for %s does not match actual preference" % key)
        self.assertEqual(len(data), len(Prefs._prefs),
                         "Logged preferences count does not match expected count")

    def test_validate_prefs_logs_all_prefs(self):
        with mock.patch.object(Log, "Info") as mock_info:
            ValidatePrefs()
        mock_info.assert_called_once()
        data = mock_info.call_args[0][1]
        for item in data:
            key, value = item
            self.assertEqual(value, Prefs[key],
                             "Logged value for %s does not match actual preference" % key)
        self.assertEqual(len(data), len(Prefs._prefs),
                         "Logged preferences count does not match expected count")

        # update the config
        self.update_prefs(flaresolverr_url="http://testserver:1234/v1")
        with mock.patch.object(Log, "Info") as mock_info:
            ValidatePrefs()
        mock_info.assert_called_once()
        data = mock_info.call_args[0][1]
        for item in data:
            key, value = item
            if key == "flaresolverr_url":
                self.assertEqual(value, "http://testserver:1234/v1",
                                 "Logged value for %s does not match updated preference" % key)
                break
        else:
            self.fail("flaresolverr_url not found in logged preferences")
        self.assertEqual(len(data), len(Prefs._prefs),
                         "Logged preferences count does not match expected count")


if __name__ == "__main__":
    unittest.main()
