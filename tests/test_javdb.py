# coding=utf-8
"""Tests for JavDB agent"""

import unittest
from base_test import QueryAgentTest, MetadataAgentTest
from agents.javdb import JavDB


class TestJavDBQuery(QueryAgentTest):
    """Test JavDB query functionality"""

    agent_class = JavDB

    test_cases = [
        ("JBD-226", {
            'name': u'JBD-226',
            'score_min': 95
        }),
    ]


class TestJavDBMetadata(MetadataAgentTest):
    """Test JavDB metadata retrieval"""

    agent_class = JavDB

    test_cases = [
        ("QNmy7", {
            'title': u'JBD-226',
            'studio': u'Attackers',
            'movie_id': 'JBD-226',
            'agent_id': 'QNmy7',
            'genres': [u'SM', u'\u5de8\u4e73'],  # 巨乳
            'roles': [u'\u7be0\u7530\u3086\u3046'],  # 篠田ゆう
            'collections': [u'\u62f7\u554f\u7121\u6b8b'],  # 拷問無残
        }),
    ]


if __name__ == '__main__':
    unittest.main()
