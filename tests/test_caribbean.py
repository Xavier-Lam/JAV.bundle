# coding=utf-8
"""Tests for Caribbean agent"""

import datetime
import unittest
from base_test import QueryAgentTest, MetadataAgentTest
from agents.caribbean import Caribbean


class TestCaribbeanQuery(QueryAgentTest):
    """Test Caribbean query functionality"""

    agent_class = Caribbean

    test_cases = [
        ("052114-001", {
            'name': u'カリビアンコム 052114-001 淫蜜 江波りゅう',
            'score_min': 100
        }),
    ]


class TestCaribbeanMetadata(MetadataAgentTest):
    """Test Caribbean metadata retrieval"""

    agent_class = Caribbean

    test_cases = [
        ("052114-001", {
            'studio': u'カリビアンコム',
            'movie_id': '052114-001',
            'agent_id': '052114-001',
            'title': u'カリビアンコム 052114-001 淫蜜 江波りゅう',
            'genres': True,
            'roles': [u'江波りゅう'],
            'collections': [u'カリビアンコム'],
            'summary': True,
            'rating': True,
            'duration': True,
            'originally_available_at': datetime.datetime(2014, 5, 21),
        }),
    ]


if __name__ == '__main__':
    unittest.main()
