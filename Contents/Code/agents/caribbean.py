# coding=utf-8

import datetime
import json
import re

from bs4 import BeautifulSoup
from requests import HTTPError

from .base import SearchAgent, StudioAgent
from .types import Metadata, Person, Resource, SearchItem


BASE_URL = "https://www.caribbeancom.com"
STUDIO_NAME = u"カリビアンコム"

# Pattern to extract a Caribbean movie ID from a filename or directory name.
# The movie ID format is MMDDYY-NNN (e.g. "070116-197").
MOVIE_ID_PATTERN = re.compile(r"(\d{6})-(\d{3})")

# Keywords that hint the media belongs to Caribbean.
SEARCH_KEYWORDS = (u"カリビ", u"carib")


class Caribbean(SearchAgent, StudioAgent):
    """Agent that scrapes metadata from caribbeancom.com."""

    name = "Caribbean"
    weight = 500

    @property
    def enabled(self):
        return True

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def guess_keywords(self, name, filename, directory):
        text = u" ".join([name or "", filename or "", directory or ""]).lower()
        if not [kw in text for kw in SEARCH_KEYWORDS if kw in text]:
            return []
        movie_id = self.guess_movie_id(text)
        if not movie_id:
            return []
        return [movie_id]

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

        el = soup.select_one('h1[itemprop="name"]')
        title = el.text.strip() if el else video_code

        item = SearchItem()
        item.id = video_code
        item.video_code = video_code
        item.title = u"{0} {1} {2}".format(STUDIO_NAME, video_code, title)
        item.year = self.parse_year_from_movie_id(video_code)
        item.score = 100
        item.thumb = "{0}/moviepages/{1}/images/jacket.jpg".format(
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
        cast_spec = self.find_spec(soup, u"出演")
        if cast_spec:
            for a in cast_spec.select('a[itemprop="actor"]'):
                name_el = a.select_one('span[itemprop="name"]')
                if name_el:
                    actresses.append(Person(name_el.text.strip(u"()")))
        metadata.actresses = actresses

        # Title
        title_el = soup.select_one('h1[itemprop="name"]')
        title_text = title_el.text.strip() if title_el else video_code
        metadata.title = u"{0} {1} {2}".format(
            STUDIO_NAME, video_code, title_text
        ).strip()
        metadata.japanese_title = metadata.title

        # Title sort
        match = re.match(r"(\d{2})(\d{2})(\d{2})-(\d+)$", video_code)
        metadata.title_sort = u"{0} {1}".format(
            STUDIO_NAME,
            "{0}{1}{2}-{3}".format(
                match.group(3), match.group(1),
                match.group(2), match.group(4)
            )
        )

        # Studio & release date
        metadata.studio = STUDIO_NAME
        metadata.release_date = self.parse_date_from_movie_id(video_code)

        # Duration
        duration_el = soup.select_one('span[itemprop="duration"]')
        if duration_el:
            try:
                dt = datetime.datetime.strptime(
                    duration_el.text.strip(), "%H:%M:%S")
                diff = dt - datetime.datetime(1900, 1, 1)
                metadata.duration = int(diff.total_seconds()) * 1000
            except ValueError:
                pass

        # Summary
        desc_el = soup.select_one('p[itemprop="description"]')
        if desc_el:
            metadata.summary = desc_el.text.strip()

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

        # Series
        series_spec = self.find_spec(soup, u"シリーズ")
        if series_spec:
            link = series_spec.select_one("a")
            if link:
                metadata.series = link.text.strip()

        # Posters
        poster_urls = [
            "{0}/moviepages/{1}/images/jacket.jpg".format(
                BASE_URL, video_code),
            "{0}/moviepages/{1}/images/l_l.jpg".format(BASE_URL, video_code),
        ]
        premium_id = self.find_premium_movie_id(soup)
        if premium_id:
            poster_urls.insert(
                0,
                "https://www.caribbeancompr.com/moviepages/{0}/images/main_s.jpg".format(premium_id))
        metadata.posters = []
        for i, url in enumerate(poster_urls):
            poster = Resource(url)
            poster.score = 100 - i
            metadata.posters.append(poster)

        # Art
        metadata.art = [
            Resource("{0}/moviepages/{1}/images/l_l.jpg".format(BASE_URL, video_code))]

        # Trailer
        movie_json = self.parse_movie_json(html)
        if movie_json:
            sample_url = movie_json.get("sample_m_flash_url",
                                        movie_json.get("sample_flash_url"))
            if sample_url:
                trailer = Resource(sample_url)
                trailer.thumb = "{0}/moviepages/{1}/images/l_l.jpg".format(
                    BASE_URL, video_code)
                metadata.trailers = [trailer]

        return metadata

    def fetch(self, video_code, lang):
        url = "{0}/moviepages/{1}/index.html".format(BASE_URL, video_code)
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.content.decode("euc-jp", errors="ignore")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def find_premium_movie_id(self, soup):
        u"""Extract a caribbeancompr.com movie ID from the \u300c\u5358\u54c1\u52d5\u753b\u300d section.

        Some caribbeancom.com pages contain a \u300c\u5358\u54c1\u52d5\u753b\u300d (single-movie purchase)
        section that links to the matching page on caribbeancompr.com.
        The premium movie ID uses underscores (e.g. ``072215_284``) rather
        than hyphens.  Only links inside that specific section are
        considered to avoid picking up unrelated promo links.

        Args:
            soup: Parsed BeautifulSoup document.

        Returns:
            str or None: The premium movie ID string, or ``None``.
        """
        for heading in soup.find_all(["h2", "h3", "h4"]):
            if u"単品動画" not in heading.get_text():
                continue
            # The heading is often wrapped in a div.heading inside a
            # section container.  Walk up to find a container that
            # actually holds the premium links.
            container = heading.parent
            if container.parent:
                container = container.parent
            for a in container.select("a[href]"):
                href = a.get("href", "")
                m = re.search(
                    r"caribbeancompr\.com/moviepages/(\d{6}_\d+)/", href)
                if m:
                    return m.group(1)
        return None

    def guess_movie_id(self, text):
        """Try to extract a Caribbean movie ID from *text*.

        Args:
            text (str): Filename, directory name, or media name.

        Returns:
            str or None: Movie ID (e.g. ``"070116-197"``), or ``None``.
        """
        match = MOVIE_ID_PATTERN.search(text)
        if match:
            return "{0}-{1}".format(match.group(1), match.group(2))
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

        The movie ID format is ``MMDDYY-NNN``.

        Args:
            movie_id (str): E.g. ``"070116-197"``.

        Returns:
            datetime.datetime or None: The parsed date, or ``None``.
        """
        match = re.match(r"(\d{6})-\d+$", movie_id)
        if match:
            try:
                return datetime.datetime.strptime(match.group(1), "%m%d%y")
            except ValueError:
                return None
        return None

    def parse_year_from_movie_id(self, movie_id):
        """Extract the release year from the movie ID.

        Args:
            movie_id (str): E.g. ``"070116-197"``.

        Returns:
            int or None: The year as integer, or ``None``.
        """
        dt = self.parse_date_from_movie_id(movie_id)
        return dt.year if dt else None
