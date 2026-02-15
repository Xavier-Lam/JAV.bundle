# coding=utf-8
"""Tests for Heyzo agent"""

import datetime
import unittest
from base_test import QueryAgentTest, MetadataAgentTest
from agents.heyzo import Heyzo


class TestHeyzoQuery(QueryAgentTest):
    """Test Heyzo query functionality"""

    agent_class = Heyzo

    test_cases = [
        ("0647", {
            'name': u'Heyzo 0647 他人妻味～挑発するシルキィ豊満ボディ～ - 尾嶋みゆき',
            'year': 2014,
            'score_min': 100
        }),
    ]


class TestHeyzoMetadata(MetadataAgentTest):
    """Test Heyzo metadata retrieval"""

    agent_class = Heyzo

    test_cases = [
        ("0647", {
            'title': u'Heyzo 0647 他人妻味～挑発するシルキィ豊満ボディ～ - 尾嶋みゆき',
            'studio': 'Heyzo',
            'movie_id': '0647',
            'agent_id': '0647',
            'genres': [u'69', u'中出し'],
            'roles': [u'尾嶋みゆき'],
            'collections': ['Heyzo'],
            'summary': True,
            'rating': True,
            'originally_available_at': datetime.datetime(2014, 7, 27),
        }),
    ]


if __name__ == '__main__':
    unittest.main()
