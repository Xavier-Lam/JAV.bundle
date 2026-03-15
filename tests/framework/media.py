# coding=utf-8


class MediaStream(object):
    type = None  # type: int
    index = None  # type: int
    id = None  # type: int
    codec = None  # type: str
    language = None  # type: str
    languageCode = None  # type: str

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MediaPart(object):
    file = None  # type: str
    hash = None  # type: str
    size = None  # type: int
    _streams = None  # type: list[MediaStream]
    _thumbs = None  # type: dict
    _art = None  # type: dict
    _subtitles = None  # type: dict
    openSubtitlesHash = None  # type: str

    @property
    def streams(self):
        if self._streams is None:
            self._streams = []
        return self._streams

    @property
    def thumbs(self):
        if self._thumbs is None:
            self._thumbs = {}
        return self._thumbs

    @property
    def art(self):
        if self._art is None:
            self._art = {}
        return self._art

    @property
    def subtitles(self):
        if self._subtitles is None:
            self._subtitles = {}
        return self._subtitles


class MediaItem(object):
    _parts = None  # type: list[MediaPart]

    @property
    def parts(self):
        if self._parts is None:
            self._parts = []
        return self._parts


class MediaTree(object):
    _items = None  # type: list[MediaItem]
    _settings = None  # type: dict
    _children = None  # type: list[MediaTree]

    @property
    def items(self):
        if self._items is None:
            self._items = []
        return self._items

    @property
    def settings(self):
        if self._settings is None:
            self._settings = {}
        return self._settings

    @property
    def children(self):
        if self._children is None:
            self._children = []
        return self._children


class Media(object):

    class Movie(object):
        name = None  # type: str
        year = None  # type: str
        openSubtitlesHash = None  # type: str
        duration = None  # type: str
        id = None  # type: str
        _items = None  # type: list[MediaItem]

        @property
        def items(self):
            if self._items is None:
                self._items = []
            return self._items

    class TV_Show(object):
        pass

    class Artist(object):
        pass

    class Album(object):
        pass

    class Photo(object):
        pass
