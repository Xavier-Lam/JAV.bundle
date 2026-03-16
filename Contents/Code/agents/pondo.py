# coding=utf-8

import datetime
import re

from .base import SearchAgent, StudioAgent
from .types import Metadata, Person, Resource, SearchItem


BASE_URL = "https://www.1pondo.tv"
API_URL = BASE_URL + "/dyn/phpauto/movie_details/movie_id/{0}.json"
STUDIO_NAME = u"一本道"

# Pattern to extract a 1Pondo movie ID from a filename or directory name.
# The movie ID format is MMDDYY_NNN (e.g. "090111_166").
MOVIE_ID_PATTERN = re.compile(r"(\d{6})_(\d{3})")

# Keywords that hint the media belongs to 1Pondo.
SEARCH_KEYWORDS = (u"一本道", u"1pon")


class Pondo(SearchAgent, StudioAgent):
    """Agent that scrapes metadata from 1pondo.tv via its JSON API."""

    name = "1Pondo"
    weight = 500

    @property
    def enabled(self):
        return True

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def guess_keywords(self, name, filename, directory):
        text = u" ".join([name or "", filename or "", directory or ""]).lower()
        if not [kw for kw in SEARCH_KEYWORDS if kw in text]:
            return []
        video_code = self.guess_video_code(text)
        if not video_code:
            return []
        return [video_code]

    def search(self, keywords, lang):
        video_code = keywords[0]
        data = self.fetch_json(video_code)
        if data is None:
            return []

        title = data.get("Title", video_code)
        release_date = self.parse_release(data)

        item = SearchItem()
        item.id = video_code
        item.video_code = video_code
        item.title = u"{0} {1} {2}".format(STUDIO_NAME, video_code, title)
        item.year = release_date.year if release_date else None
        item.score = 100
        item.thumb = data.get("MovieThumb")
        return [item]

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, agent_id, video_code, lang):
        data = self.fetch_json(video_code)
        if data is None:
            raise Exception("Failed to fetch data for {0}".format(video_code))

        metadata = Metadata()

        # Actresses
        actresses_ja = data.get("ActressesJa", [])
        metadata.actresses = [
            Person(name) for name in actresses_ja] if actresses_ja else []

        # Title
        title_text = data.get("Title", "")
        role_names = u" ".join(metadata.actresses)
        metadata.title = u"{0} {1} {2} {3}".format(
            STUDIO_NAME, video_code, title_text, role_names
        ).strip()
        metadata.japanese_title = metadata.title

        # Title sort
        match = re.match(r"(\d{2})(\d{2})(\d{2})[-_](\d+)$", video_code)
        if match:
            metadata.title_sort = u"{0} {1}{2}{3}-{4}".format(
                STUDIO_NAME,
                match.group(3), match.group(1),
                match.group(2), match.group(4),
            )
        else:
            metadata.title_sort = metadata.title

        # Studio
        metadata.studio = STUDIO_NAME

        # Release date
        metadata.release_date = self.parse_release(data)

        # Duration
        duration = data.get("Duration")
        if duration is not None:
            metadata.duration = int(duration) * 1000

        # Summary
        desc = data.get("Desc")
        if desc:
            metadata.summary = desc.strip()

        # Rating
        rating = data.get("AvgRating")
        if rating is not None:
            metadata.rating = float(rating) * 2

        # Genres
        ucname = data.get("UCNAME")
        if ucname:
            metadata.genres = set(ucname)

        # Series
        series = data.get("Series")
        if series:
            metadata.series = series

        # Posters
        poster_url = data.get("MovieThumb")
        if poster_url:
            metadata.posters = [Resource(poster_url)]
        else:
            metadata.posters = [Resource(
                "{0}/assets/sample/{1}/str.jpg".format(BASE_URL, video_code)
            )]

        # Art
        metadata.art = [Resource(
            "{0}/assets/sample/{1}/str.jpg".format(BASE_URL, video_code)
        )]

        # Trailer
        sample_files = data.get("SampleFiles")
        if sample_files:
            best = sample_files[-1]
            url = best.get("URL")
            if url:
                trailer = Resource(url.replace("smovie.1pondo.tv", "sample-1pondo.eroxjapanz.com"))
                trailer.thumb = "{0}/assets/sample/{1}/str.jpg".format(
                    BASE_URL, video_code
                )
                metadata.trailers = [trailer]

        return metadata

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def guess_video_code(self, text):
        """Try to extract a 1Pondo movie ID from *text*.

        Args:
            text (str): Filename, directory name, or media name.

        Returns:
            str or None: Movie ID (e.g. ``"090111_166"``), or ``None``.
        """
        match = MOVIE_ID_PATTERN.search(text)
        if match:
            return "{0}_{1}".format(match.group(1), match.group(2))
        return None

    def fetch_json(self, video_code):
        """Fetch the movie details JSON from the 1Pondo API.

        Args:
            video_code (str): E.g. ``"090111_166"``.

        Returns:
            dict or None: The parsed JSON, or ``None`` on error.
        """
        url = API_URL.format(video_code)
        resp = self.session.get(url)
        if resp.status_code != 200:
            return None
        try:
            return resp.json()
        except (ValueError, TypeError):
            return None

    def parse_release(self, data):
        """Parse the Release field into a datetime.

        Args:
            data (dict): JSON data dict.

        Returns:
            datetime.datetime or None: The release date, or ``None``.
        """
        release = data.get("Release")
        if release:
            try:
                return datetime.datetime.strptime(release, "%Y-%m-%d")
            except ValueError:
                return None
        return None
