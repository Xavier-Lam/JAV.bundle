# coding=utf-8

from threading import Lock
from urllib import quote
from urlparse import urlparse

from .base import AvatarAgent
from .types import Resource


GITHUB_TEMPLATE = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/{}/{}/{}'
FILETREE_URL = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/Filetree.json'


class GFriends(AvatarAgent):
    name = "Gfriends"
    weight = -300

    def __init__(self, *args, **kwargs):
        super(GFriends, self).__init__(*args, **kwargs)
        self.initialized = False
        self.resource = {}
        self.lock = Lock()

    def get_avatar(self, actress, lang):
        if not self.initialized:
            self.initialize()
        url = self.resource.get(actress)
        if url is not None:
            url = Resource(url)
        return url

    def initialize(self):
        with self.lock:
            if self.initialized:
                return

            self.logger.info("loading gfriends file tree has started.")

            response = self.session.get(FILETREE_URL)
            if response.status_code != 200:
                self.logger.info("request gfriend map failed %s",
                                 response.status_code)
                return

            self.logger.info("finish loading gfriends file tree")

            map_json = response.json()

            data = map_json["Content"]
            second_lvls = data.keys()
            for second in second_lvls:
                for k, v in data[second].items():
                    self.resource[k[:-4]] = GITHUB_TEMPLATE.format(
                        quote("Content".encode("utf-8")),
                        quote(second.encode("utf-8")),
                        quote(urlparse(v).path.encode("utf-8"))
                    )

            self.initialized = True
