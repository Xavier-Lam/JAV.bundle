# coding=utf-8


class Agent(object):

    class Movies(object):
        pass

    class TV_Shows(object):
        pass

    class Artists(object):
        pass

    class Albums(object):
        pass

    class Photos(object):
        pass


class MetadataSearchResult(object):

    def __init__(self, id, name=None, year=None, score=0, lang=None, thumb=None):
        self.id = id
        self.name = name
        self.year = year
        self.score = score
        self.lang = lang
        self.thumb = thumb


class SearchResult(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
