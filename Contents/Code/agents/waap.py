# coding=utf-8

from .base import StudioAgent


class Waap(StudioAgent):
    """
    http://www.waap.co.jp/
    """

    def get_metadata(self, movie_id):
        pass

    def is_match(self, movie_id):
        for prefix in self.allowed_prefixes:
            if movie_id.startswith(prefix + "-"):
                return True
        return False
