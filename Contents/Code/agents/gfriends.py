# coding=utf-8

import requests
from urllib import quote
from urlparse import urlparse

from .base import AvatarAgent


class GFriend(AvatarAgent, dict):
    initialized = False

    def get_name(self):
        return "Gfriends"

    def get_roledata(self, name):
        if not self.initialized:
            self.initialize()
        return {
            "photo": self.get(name.upper(), "")
        }

    def initialize(self):
        github_template = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/{}/{}/{}'
        request_url = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/Filetree.json'

        Log("Loading gfriends file tree has started.")

        response = requests.get(request_url)
        if response.status_code != 200:
            Log('request gfriend map failed {}'.format(response.status_code))

        Log("Finish loading gfriends file tree")

        map_json = response.json()

        # plex doesn't support fucking recursive call
        data = map_json["Content"]
        second_lvls = data.keys()
        for second in second_lvls:
            for k, v in data[second].items():
                self[k[:-4]] = github_template.format(
                    quote("Content".encode("utf-8")),
                    quote(second.encode("utf-8")),
                    quote(urlparse(v).path.encode("utf-8"))
                )

        self.initialized = True
