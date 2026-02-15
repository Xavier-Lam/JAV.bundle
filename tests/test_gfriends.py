# coding=utf-8
"""Tests for GFriend avatar agent"""

import unittest
from base_test import AvatarAgentTest
from agents.gfriends import GFriend


class TestGFriendAvatar(AvatarAgentTest):
    """Test GFriend avatar functionality"""

    agent_class = GFriend

    def setUp(self):
        """Set up test fixtures and initialize GFriend agent"""
        super(TestGFriendAvatar, self).setUp()
        # GFriend agent needs to be initialized to load actress data from
        # GitHub
        if not self.agent.initialized:
            self.agent.initialize()

    test_cases = [
        (u"かなで自由", {
            'photo': 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/Content/v-Attackers/%E3%81%8B%E3%81%AA%E3%81%A7%E8%87%AA%E7%94%B1.jpg'
        }),
    ]


if __name__ == '__main__':
    unittest.main()
