# coding=utf-8

from .containers import Map, ObjectContainer, Set
from .proxies import Proxy


class Person(object):
    name = None  # type: str
    role = None  # type: str
    photo = None  # type: str


class Review(object):
    author = None  # type: str
    source = None  # type: str
    image = None  # type: str
    link = None  # type: str
    text = None  # type: str


class Chapter(object):
    title = None  # type: str
    start_time_offset = None  # type: int
    end_time_offset = None  # type: int


class Movie(object):
    id = None  # type: str
    title = None  # type: str
    year = None  # type: int
    originally_available_at = None  # type: datetime.date
    studio = None  # type: str
    tagline = None  # type: str
    summary = None  # type: str
    trivia = None  # type: str
    quotes = None  # type: str
    content_rating = None  # type: str
    content_rating_age = None  # type: int
    duration = None  # type: int
    rating = None  # type: float
    audience_rating = None  # type: float
    rating_image = None  # type: str
    audience_rating_image = None  # type: str
    original_title = None  # type: str
    title_sort = None  # type: str
    _genres = None  # type: set[str]
    _tags = None  # type: set[str]
    _collections = None  # type: set[str]
    _similar = None  # type: set[str]
    _writers = None  # type: set[Person]|Set
    _directors = None  # type: set[Person]|Set
    _producers = None  # type: set[Person]|Set
    _roles = None  # type: set[Person]|Set
    _countries = None  # type: set[str]
    _reviews = None  # type: set[Review]|Set
    _posters = None  # type: dict[str, Proxy.Media]|Map
    _art = None  # type: dict[str, Proxy.Media]|Map
    _banners = None  # type: dict[str, Proxy.Media]|Map
    _themes = None  # type: dict[str, Proxy.Media]|Map
    _extras = None  # type: ObjectContainer

    @property
    def genres(self):
        if self._genres is None:
            self._genres = set()
        return self._genres

    @property
    def tags(self):
        if self._tags is None:
            self._tags = set()
        return self._tags
    
    @property
    def collections(self):
        if self._collections is None:
            self._collections = set()
        return self._collections

    @property
    def similar(self):
        if self._similar is None:
            self._similar = set()
        return self._similar
    
    @property
    def writers(self):
        if self._writers is None:
            self._writers = Set(Person)
        return self._writers

    @property
    def directors(self):
        if self._directors is None:
            self._directors = Set(Person)
        return self._directors

    @property
    def producers(self):
        if self._producers is None:
            self._producers = Set(Person)
        return self._producers

    @property
    def roles(self):
        if self._roles is None:
            self._roles = Set(Person)
        return self._roles
    
    @property
    def countries(self):
        if self._countries is None:
            self._countries = set()
        return self._countries

    @property
    def reviews(self):
        if self._reviews is None:
            self._reviews = Set(Review)
        return self._reviews

    @property
    def posters(self):
        if self._posters is None:
            self._posters = Map()
        return self._posters

    @property
    def art(self):
        if self._art is None:
            self._art = Map()
        return self._art

    @property
    def banners(self):
        if self._banners is None:
            self._banners = Map()
        return self._banners

    @property
    def themes(self):
        if self._themes is None:
            self._themes = Map()
        return self._themes

    @property
    def extras(self):
        if self._extras is None:
            self._extras = ObjectContainer()
        return self._extras


class TrailerObject(object):
    url = None  # type: str
    file = None  # type: str
    title = None  # type: str
    index = None  # type: int
    thumb = None  # type: str


class DeletedSceneObject(TrailerObject):
    pass


class BehindTheScenesObject(TrailerObject):
    pass


class InterviewObject(TrailerObject):
    pass


class SceneOrSampleObject(TrailerObject):
    pass


class FeaturetteObject(TrailerObject):
    pass


class ShortObject(TrailerObject):
    pass


class OtherObject(TrailerObject):
    pass


class MusicVideoObject(TrailerObject):
    pass


class LiveMusicVideoObject(TrailerObject):
    pass


class LyricMusicVideoObject(TrailerObject):
    pass


class ConcertVideoObject(TrailerObject):
    pass
