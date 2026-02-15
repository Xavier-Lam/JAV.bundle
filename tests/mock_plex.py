# coding=utf-8
"""Mock Plex classes for testing"""

import json


def Log(msg, *args):
    """Mock Plex Log function"""
    # In real Plex, Log() is a simple function that logs messages
    # For testing, we just print to stdout
    if args:
        print("[LOG] {0}".format(msg % args))
    else:
        print("[LOG] {0}".format(msg))


class HTTP(object):
    """Mock Plex HTTP class"""
    @staticmethod
    def Request(url, **kwargs):
        import requests
        return requests.get(url, **kwargs).text


class Prefs(dict):
    """Mock Plex Prefs class"""

    def __init__(self):
        super(Prefs, self).__init__()
        self["proxy"] = None
        self["userAgent"] = None
        self["javdbCFClearance"] = None
        self["javlibraryCFClearance"] = None


class JSON(object):
    """Mock Plex JSON class"""
    @staticmethod
    def ObjectFromString(s):
        return json.loads(s)

    @staticmethod
    def StringFromObject(obj):
        return json.dumps(obj)


class Locale(object):
    """Mock Plex Locale class"""
    class Language(object):
        NoLanguage = 'xx'
        English = 'en'
        Japanese = 'ja'


class Agent(object):
    """Mock Plex Agent class"""
    class Movies(object):
        pass


class Media(object):
    """Mock Plex Media object"""

    def __init__(self, name="", year=None, filename=""):
        self.name = name
        self.year = year
        self.filename = filename
        self.primary_metadata = None
        self.primary_agent = None


class MetadataSearchResult(object):
    """Mock Plex MetadataSearchResult"""

    def __init__(self, id, name, year=None, score=100, lang='xx', thumb=None):
        self.id = id
        self.name = name
        self.year = year
        self.score = score
        self.lang = lang
        self.thumb = thumb

    def __repr__(self):
        return "<MetadataSearchResult id={0}, name={1}, year={2}, score={3}>".format(
            self.id, self.name, self.year, self.score)


class VideoClipObject(object):
    """Mock Plex VideoClipObject"""

    def __init__(self):
        self.title = None
        self.year = None
        self.originally_available_at = None
        self.rating = None
        self.content_rating = None
        self.studio = None
        self.tagline = None
        self.summary = None
        self.duration = None
        self.genres = []
        self.roles = []
        self.directors = []
        self.writers = []
        self.collections = []
        self.posters = {}
        self.art = {}


def inject_mocks():
    """Inject mock classes into globals"""
    import sys

    # Get the calling module's globals
    frame = sys._getframe(1)
    calling_globals = frame.f_globals

    calling_globals['Log'] = Log
    calling_globals['HTTP'] = HTTP
    calling_globals['Prefs'] = Prefs()
    calling_globals['JSON'] = JSON
    calling_globals['Locale'] = Locale
    calling_globals['Agent'] = Agent
    calling_globals['Media'] = Media
    calling_globals['MetadataSearchResult'] = MetadataSearchResult
    calling_globals['VideoClipObject'] = VideoClipObject
