# coding=utf-8


class _Prefs(object):

    def __init__(self):
        self._prefs = {}

    def __getitem__(self, key):
        return self._prefs[key]


Prefs = _Prefs()
