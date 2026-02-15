# coding=utf-8
"""Tests for Pondo agent"""

import datetime
import unittest
from base_test import QueryAgentTest, MetadataAgentTest
from agents.pondo import Pondo


class TestPondoQuery(QueryAgentTest):
    """Test Pondo query functionality"""

    agent_class = Pondo

    test_cases = [
        ("090111_166", {
            'name': 'エロ過ぎる潮吹きアイドル',
            'year': 2011,
            'score_min': 100
        }),
    ]


class TestPondoMetadata(MetadataAgentTest):
    """Test Pondo metadata retrieval"""

    agent_class = Pondo

    test_cases = [
        ("090111_166", {
            'title': '一本道 090111_166 エロ過ぎる潮吹きアイドル',
            'studio': '一本道',
            'movie_id': '090111_166',
            'agent_id': '090111_166',
            'genres': [u'ロリ', u'巨乳'],
            'roles': [u'羽月希'],
            'collections': [u'一本道'],
            'summary': True,
            'rating': True,
            'duration': True,
            'originally_available_at': datetime.datetime(2011, 9, 1),
        }),
    ]


if __name__ == '__main__':
    unittest.main()
