# coding=utf-8
"""Tests for JAVLibrary agent (CloudFlare protected)"""

import datetime
import unittest
try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock
import os

from base_test import QueryAgentTest, MetadataAgentTest
from agents.javlibrary import JAVLibrary


class TestJAVLibraryQueryMixin(object):
    """Test JAVLibrary query functionality"""

    agent_class = JAVLibrary

    test_cases = [
        ("JBD-226", {
            "id": "JAVLibrary.li7ah34",
            'name': u'JBD-226 拷問無残4 篠田ゆう',
            'score_min': 95
        }),
    ]


class TestJAVLibraryQuery(TestJAVLibraryQueryMixin, QueryAgentTest):
    _original_session = None

    def setUp(self):
        """Set up test fixtures with mocked HTTP responses"""
        super(TestJAVLibraryQuery, self).setUp()

        # Mock the session property to avoid CloudFlare
        # The query makes a GET to vl_searchbyid.php?keyword=XXX
        # If there's one exact match, javlibrary redirects to the detail page
        # For our mock, we return the detail page HTML directly
        def mock_get(url, **kwargs):
            mock_response = MagicMock()
            keyword = kwargs.get('params', {}).get('keyword', '')
            test_cases = dict(self.test_cases)
            test_case = test_cases[keyword]
            agent_id = test_case['id'].replace('JAVLibrary.', '')
            mock_html = self.load_mock_html(
                'javlibrary_metadata_{0}.html'.format(agent_id))
            mock_response.content = mock_html.encode(
                'utf-8')
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_session = MagicMock()
        mock_session.get = mock_get

        # Use property mock
        self._original_session = type(self.agent).session
        type(self.agent).session = property(lambda self: mock_session)

    def tearDown(self):
        type(self.agent).session = self._original_session
        super(TestJAVLibraryQuery, self).tearDown()


class TestJAVLibraryQueryFlareSolverr(TestJAVLibraryQueryMixin, QueryAgentTest):
    def setUp(self):
        super(TestJAVLibraryQueryFlareSolverr, self).setUp()
        Prefs["flaresolverrUrl"] = os.environ.get('FLARESOLVERR_URL')

    def tearDown(self):
        Prefs["flaresolverrUrl"] = None
        super(TestJAVLibraryQueryFlareSolverr, self).tearDown()


class TestJAVLibraryMetadataMixin(object):
    """Test JAVLibrary metadata retrieval"""

    agent_class = JAVLibrary

    test_cases = [
        ("li7ah34", {
            'title': u'JBD-226 拷問無残4 篠田ゆう',
            'studio': u'アタッカーズ',
            'movie_id': 'JBD-226',
            'agent_id': 'li7ah34',
            'genres': [u'SM', u'巨乳'],
            'roles': [u'篠田ゆう'],
            'rating': True,
            'duration': True,
            'originally_available_at': datetime.datetime(2018, 6, 7),
        }),
    ]


class TestJAVLibraryMetadata(TestJAVLibraryMetadataMixin, MetadataAgentTest):
    _original_session = None

    def setUp(self):
        """Set up test fixtures with mocked HTTP responses"""
        super(TestJAVLibraryMetadata, self).setUp()

        # Mock the session property to avoid CloudFlare
        # The metadata crawl makes a GET with params v=jav{agent_id}
        def mock_get(url, **kwargs):
            mock_response = MagicMock()
            # Extract agent_id from params
            params = kwargs.get('params', {})
            agent_id = params['v'][3:]

            # Load mock HTML for this specific agent_id
            mock_html = None
            if agent_id:
                mock_html = self.load_mock_html(
                    'javlibrary_metadata_{0}.html'.format(agent_id))

            mock_response.content = mock_html.encode('utf-8')
            mock_response.raise_for_status = MagicMock()
            mock_response.ok = True
            return mock_response

        mock_session = MagicMock()
        mock_session.get = mock_get

        # Use property mock
        self._original_session = type(self.agent).session
        type(self.agent).session = property(lambda self: mock_session)

    def tearDown(self):
        type(self.agent).session = self._original_session
        super(TestJAVLibraryMetadata, self).tearDown()


class TestJAVLibraryMetadataFlareResolverr(TestJAVLibraryMetadataMixin, MetadataAgentTest):
    def setUp(self):
        super(TestJAVLibraryMetadataFlareResolverr, self).setUp()
        Prefs["flaresolverrUrl"] = os.environ.get('FLARESOLVERR_URL')

    def tearDown(self):
        Prefs["flaresolverrUrl"] = None
        super(TestJAVLibraryMetadataFlareResolverr, self).tearDown()


if __name__ == '__main__':
    unittest.main()
