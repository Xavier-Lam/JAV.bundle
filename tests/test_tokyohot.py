# coding=utf-8
"""Tests for TokyoHot agent"""

import datetime
import unittest
from base_test import QueryAgentTest, MetadataAgentTest
from agents.tokyohot import TokyoHot


class TestTokyoHotQuery(QueryAgentTest):
    """Test TokyoHot query functionality"""

    agent_class = TokyoHot

    test_cases = [
        ("n0820", {
            'id': "TokyoHot.21044",
            'name': u'Wカン悠希めい/武井麻希',
            'score_min': 100
        }),
    ]


class TestTokyoHotMetadata(MetadataAgentTest):
    """Test TokyoHot metadata retrieval"""

    agent_class = TokyoHot

    test_cases = [
        ("21044", {
            'title': u'東熱 n0820 Wカン悠希めい/武井麻希',
            'studio': u'東熱',
            'movie_id': 'n0820',
            'agent_id': '21044',
            'roles': [u'悠希めい', u'武井麻希'],
            'genres': True,
            'collections': [u'東熱'],
            'summary': True,
            'duration': True,
            'originally_available_at': datetime.datetime(2013, 2, 1),
        }),
    ]


if __name__ == '__main__':
    unittest.main()
