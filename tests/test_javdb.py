# coding=utf-8
"""Tests for JavDB agent (CloudFlare protected)"""

import unittest
try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock

from base_test import QueryAgentTest, MetadataAgentTest
from agents.javdb import JavDB


class TestJavDBQuery(QueryAgentTest):
    """Test JavDB query functionality"""

    agent_class = JavDB

    # TODO: Fill in test cases with real keywords and expected properties
    test_cases = [
        # Example format:
        # ("ABP-123", {
        #     'name': 'Expected Title Substring',
        #     'score_min': 90
        # }),
    ]

    def setUp(self):
        """Set up test fixtures with mocked HTTP responses"""
        super(TestJavDBQuery, self).setUp()

        # Mock the session property to avoid CloudFlare
        mock_session = MagicMock()
        mock_response = MagicMock()

        # Load mock HTML for query. Prefer per-keyword file: javdb_query_<keyword>.html
        mock_html = None
        if self.test_cases:
            keyword = self.test_cases[0][0]
            mock_html = self.load_mock_html('javdb_query_{0}.html'.format(keyword))
        # Fallback to generic filename for compatibility
        if not mock_html:
            mock_html = self.load_mock_html('javdb_query.html')
        if mock_html:
            mock_response.content = mock_html.encode('utf-8')
            mock_response.raise_for_status = MagicMock()
            mock_session.get.return_value = mock_response

        # Use property mock
        type(self.agent).session = property(lambda self: mock_session)


class TestJavDBMetadata(MetadataAgentTest):
    """Test JavDB metadata retrieval"""

    agent_class = JavDB

    # TODO: Fill in test cases with real agent IDs and expected properties
    test_cases = [
        # Example format:
        # ("abcd123", {
        #     'title': 'Expected Title',
        #     'studio': 'Studio Name',
        #     'genres': ['Genre1', 'Genre2'],
        # }),
    ]

    def setUp(self):
        """Set up test fixtures with mocked HTTP responses"""
        super(TestJavDBMetadata, self).setUp()

        # Mock the session property to avoid CloudFlare
        mock_session = MagicMock()
        mock_response = MagicMock()

        # Load mock HTML for metadata. Prefer per-id file: javdb_metadata_<id>.html
        mock_html = None
        if self.test_cases:
            agent_id = self.test_cases[0][0]
            mock_html = self.load_mock_html('javdb_metadata_{0}.html'.format(agent_id))
        # Fallback to generic filename for compatibility
        if not mock_html:
            mock_html = self.load_mock_html('javdb_metadata.html')
        if mock_html:
            mock_response.content = mock_html.encode('utf-8')
            mock_response.raise_for_status = MagicMock()
            mock_response.ok = True
            mock_session.get.return_value = mock_response
            mock_session.head.return_value = mock_response

        # Use property mock
        type(self.agent).session = property(lambda self: mock_session)


if __name__ == '__main__':
    unittest.main()
