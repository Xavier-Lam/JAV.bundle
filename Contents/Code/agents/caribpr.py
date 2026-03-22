# coding=utf-8

import datetime
import json
import re

from bs4 import BeautifulSoup
from requests import HTTPError

from .base import SearchAgent, StudioAgent
from .types import Metadata, Person, Resource, SearchItem


BASE_URL = "https://www.caribbeancompr.com"
STUDIO_NAME = u"カリビアンコムプレミアム"

# Pattern to extract a CaribbeanPr movie ID from a filename or directory name.
# The movie ID format is MMDDYY_NNN (e.g. "072215_284").
MOVIE_ID_PATTERN = re.compile(r"(\d{6})[_](\d{3})")

# Keywords that hint the media belongs to CaribbeanPr.
SEARCH_KEYWORDS = (u"カリビ", u"carib")


class CaribbeanPr(SearchAgent, StudioAgent):
    """Agent that scrapes metadata from caribbeancompr.com."""

    name = "Caribbean Premium"
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
        try:
            html = self.fetch(video_code, lang)
        except HTTPError as e:
            if e.response.status_code == 404:
                self.logger.info(u"video code {0} not found".format(video_code))
                return []
            raise
        soup = BeautifulSoup(html, "html.parser")

        section = soup.select_one("div.movie-info div.section.is-wide")
        title = video_code
        if section:
            h1 = section.select_one("h1")
            if h1:
                title = h1.text.strip()

        item = SearchItem()
        item.id = video_code
        item.video_code = video_code
        item.title = u"{0} {1} {2}".format(STUDIO_NAME, video_code, title)
        item.year = self.parse_year_from_movie_id(video_code)
        item.score = 100
        item.thumb = "{0}/moviepages/{1}/images/main_s.jpg".format(
            BASE_URL, video_code)
        return [item]

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, agent_id, video_code, lang):
        html = self.fetch(video_code, lang)
        soup = BeautifulSoup(html, "html.parser")

        metadata = Metadata()

        # Actresses
        actresses = []
        spec = self.find_spec(soup, u"出演")
        if spec:
            actors = spec.select("a.spec-item")
            if not actors:
                actors = spec.select("a")
            for a in actors:
                name_text = a.text.strip()
                if name_text:
                    actresses.append(Person(name_text))
        metadata.actresses = actresses

        # Title
        section = soup.select_one("div.movie-info div.section.is-wide")
        title_text = video_code
        if section:
            h1 = section.select_one("h1")
            if h1:
                title_text = h1.text.strip()
        role_names = u" ".join(actresses)
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
        studio_spec = self.find_spec(soup, u"スタジオ")
        if studio_spec:
            link = studio_spec.select_one("a")
            if link:
                metadata.studio = link.text.strip()
        if not metadata.studio:
            metadata.studio = STUDIO_NAME

        # Release date
        metadata.release_date = self.parse_date_from_movie_id(video_code)

        # Duration
        duration_spec = self.find_spec(soup, u"再生時間")
        if duration_spec:
            try:
                dt = datetime.datetime.strptime(
                    duration_spec.text.strip(), "%H:%M:%S"
                )
                diff = dt - datetime.datetime(1900, 1, 1)
                metadata.duration = int(diff.total_seconds()) * 1000
            except ValueError:
                pass

        # Summary
        if section:
            p = section.select_one("p")
            if p:
                metadata.summary = p.text.strip()

        # Rating
        rating_spec = self.find_spec(soup, u"ユーザー評価")
        if rating_spec:
            count = len(rating_spec.text.strip())
            if count > 0:
                metadata.rating = float(count * 2)

        # Genres
        tags_spec = self.find_spec(soup, u"タグ")
        if tags_spec:
            metadata.genres = set(
                a.text.strip() for a in tags_spec.select("a.spec-item")
            )

        # Posters
        poster_urls = [
            "{0}/moviepages/{1}/images/main_s.jpg".format(
                BASE_URL, video_code),
            "{0}/moviepages/{1}/images/l_l.jpg".format(BASE_URL, video_code),
        ]
        metadata.posters = []
        for i, url in enumerate(poster_urls):
            poster = Resource(url)
            poster.score = 100 - i
            metadata.posters.append(poster)

        # Art
        metadata.art = [Resource(
            "{0}/moviepages/{1}/images/l_l.jpg".format(BASE_URL, video_code)
        )]

        # Trailer
        movie_json = self.parse_movie_json(html)
        if movie_json:
            sample_url = movie_json.get("sample_flash_url")
            if sample_url:
                trailer = Resource(sample_url)
                trailer.thumb = "{0}/moviepages/{1}/images/l_l.jpg".format(
                    BASE_URL, video_code
                )
                metadata.trailers = [trailer]

        return metadata

    def fetch(self, video_code, lang):
        url = "{0}/moviepages/{1}/index.html".format(BASE_URL, video_code)
        resp = self.session.get(url)
        self.raise_for_status(resp)
        return resp.content.decode("euc-jp", errors="ignore")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def guess_video_code(self, text):
        """Try to extract a CaribbeanPr movie ID from *text*.

        Args:
            text (str): Filename, directory name, or media name.

        Returns:
            str or None: Movie ID (e.g. ``"072215_284"``), or ``None``.
        """
        match = MOVIE_ID_PATTERN.search(text)
        if match:
            return "{0}_{1}".format(match.group(1), match.group(2))
        return None

    def find_spec(self, soup, title):
        """Find a ``li.movie-spec`` whose ``span.spec-title`` matches *title*.

        Args:
            soup: Parsed BeautifulSoup document.
            title (unicode): The Japanese label text to match.

        Returns:
            The ``span.spec-content`` element, or ``None``.
        """
        for li in soup.select("li.movie-spec"):
            title_el = li.select_one("span.spec-title")
            if title_el and title_el.text.strip() == title:
                return li.select_one("span.spec-content")
        return None

    def parse_movie_json(self, html):
        """Extract the ``var Movie = {...}`` JSON object from the page source.

        Args:
            html (str): The raw HTML string.

        Returns:
            dict or None: The parsed dict, or ``None``.
        """
        match = re.search(r"var\s+Movie\s*=\s*(\{[^}]+\})", html)
        if match:
            try:
                return json.loads(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    def parse_date_from_movie_id(self, movie_id):
        """Parse a release date from the movie ID.

        The movie ID format is ``MMDDYY_NNN``.

        Args:
            movie_id (str): E.g. ``"072215_284"``.

        Returns:
            datetime.datetime or None: The parsed date, or ``None``.
        """
        match = re.match(r"(\d{6})[-_]\d+$", movie_id)
        if match:
            try:
                return datetime.datetime.strptime(match.group(1), "%m%d%y")
            except ValueError:
                return None
        return None

    def parse_year_from_movie_id(self, movie_id):
        """Extract the release year from the movie ID.

        Args:
            movie_id (str): E.g. ``"072215_284"``.

        Returns:
            int or None: The year as integer, or ``None``.
        """
        dt = self.parse_date_from_movie_id(movie_id)
        return dt.year if dt else None
