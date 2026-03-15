# coding=utf-8

from datetime import datetime


class Person(unicode):
    photo = None  # type: str
    japanese_name = None  # type: str


class Resource(unicode):
    thumb = None  # type: str
    score = 50  # type: int


class Metadata(object):
    """
    Metadata of a JAV

    Attributes:
        code_group (str): The code group of the video, e.g. "ABC" for "ABC-123"
        title (str): The title of the movie
        japanese_title (str): The Japanese title of the movie
        release_date (datetime.date): The release date of the movie
        studio (str): The studio that produced the movie
        series (str): The series the movie belongs to
        duration (int): The duration of the movie in seconds
        actresses (set[Person]): The cast of the movie
        directors (set[Person]): The directors of the movie
        posters (list[Resource]): The posters of the movie
        art (list[Resource]): The background art
        themes (list[Resource]): The theme images of the movie
        trailers (list[Resource]): The trailers of the movie
        title_sort (str): The title used for sorting
        genres (set[str]): The genres of the movie
        labels (set[str]): The labels of the movie
        summary (str): Plot summary
        rating (float): Critic rating
    """

    code_group = None  # type: str

    title = None  # type: str
    japanese_title = None  # type: str
    release_date = None  # type: datetime.date
    studio = None  # type: str
    series = None  # type: str
    duration = None  # type: int

    actresses = None  # type: set[Person]
    directors = None  # type: set[Person]

    posters = None  # type: list[Resource]
    art = None  # type: list[Resource]
    themes = None  # type: list[Resource]
    trailers = None  # type: list[Resource]

    title_sort = None  # type: str
    genres = None  # type: set[str]
    labels = None  # type: set[str]
    summary = None  # type: str
    rating = None  # type: float

    def __repr__(self):
        return (u"Metadata(title=%s, release_date=%s, studio=%s, series=%s, actresses=%s)" % (
            self.title,
            self.release_date and self.release_date.strftime('%Y-%m-%d'),
            self.studio,
            self.series,
            self.actresses
        )).encode('utf-8')


class SearchItem(object):
    """
    Search result of a JAV search query.

    Attributes:
        id (str): The video id of the agent
        video_code (str): The code of the JAV
        title (str): The title of the search result
        year (str): The release year of the search result
        score (int): Match confidence score (0–100)
        thumb (str): The thumbnail image
    """

    id = None  # type: str
    video_code = None  # type: str
    title = None  # type: str
    year = None  # type: str
    score = None  # type: int
    thumb = None  # type: str

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return "SearchItem(id=%s, video_code=%s, title=%s, score=%s)" % (
            self.id, self.video_code, self.title, self.score)
