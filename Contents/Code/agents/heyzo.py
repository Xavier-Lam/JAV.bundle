# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import SearchAgent, StudioAgent
from .types import Metadata, Person, Resource, SearchItem


BASE_URL = "https://www.heyzo.com"
STUDIO_NAME = u"Heyzo"

# Pattern to extract a Heyzo movie ID from a filename or directory name.
# The movie ID is a 4-digit number (e.g. "0647").
MOVIE_ID_PATTERN = re.compile(r"(\d{4})")

# Keywords that hint the media belongs to Heyzo.
SEARCH_KEYWORDS = (u"heyzo",)


class Heyzo(SearchAgent, StudioAgent):
    """Agent that scrapes metadata from heyzo.com."""

    name = "Heyzo"
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
        url = "{0}/moviepages/{1}/index.html".format(BASE_URL, video_code)
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        h1 = soup.select_one("#movie h1")
        title = re.sub(r'\s+', ' ', h1.text).strip() if h1 else video_code
        release_date = self.parse_release_date(soup)

        item = SearchItem()
        item.id = video_code
        item.video_code = video_code
        item.title = u"{0} {1} {2}".format(STUDIO_NAME, video_code, title)
        item.year = release_date.year if release_date else None
        item.score = 100
        item.thumb = "{0}/contents/3000/{1}/images/thumbnail.jpg".format(
            BASE_URL, video_code
        )
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
        tr = soup.select_one("tr.table-actor")
        if tr:
            tds = tr.select("td")
            if len(tds) >= 2:
                spans = tds[1].select("span")
                if spans:
                    actresses = [
                        Person(s.text.strip())
                        for s in spans if s.text.strip()
                    ]
                else:
                    links = tds[1].select("a")
                    if links:
                        actresses = [
                            Person(a.text.strip())
                            for a in links if a.text.strip()
                        ]
        metadata.actresses = actresses

        # Title
        h1 = soup.select_one("#movie h1")
        if h1:
            title_text = re.sub(r'\s+', ' ', h1.text).strip()
            metadata.title = u"{0} {1} {2}".format(
                STUDIO_NAME, video_code, title_text
            ).strip()
            metadata.japanese_title = metadata.title
        metadata.title_sort = u"{0} {1}".format(STUDIO_NAME, video_code)

        # Studio
        metadata.studio = STUDIO_NAME

        # Release date
        metadata.release_date = self.parse_release_date(soup)

        # Duration
        bonus = soup.select_one("tr.table-bonus-dl-big td:first-child")
        if bonus:
            text = bonus.text.strip()
            match = re.match(r"(\d{2}):(\d{2}):(\d{2})", text)
            if match:
                h, m, s = (
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                )
                metadata.duration = (h * 3600 + m * 60 + s) * 1000

        # Summary
        el = soup.select_one("p.memo")
        if el:
            metadata.summary = el.text.strip()

        # Rating
        el = soup.select_one('span[itemprop="ratingValue"]')
        if el:
            try:
                metadata.rating = float(el.text.strip()) * 2
            except (ValueError, TypeError):
                pass

        # Genres
        tags = soup.select("tr.table-tag-keyword-big ul.tag-keyword-list a")
        if tags:
            metadata.genres = set(t.text.strip()
                                  for t in tags if t.text.strip())

        # Series
        tr = soup.select_one("tr.table-series")
        if tr:
            tds = tr.select("td")
            if len(tds) >= 2:
                link = tds[1].select_one("a")
                if link:
                    text = link.text.strip("-")
                    if text:
                        metadata.series = text

        # Posters
        metadata.posters = [Resource(
            "{0}/contents/3000/{1}/images/thumbnail.jpg".format(
                BASE_URL, video_code
            )
        )]

        # Art
        metadata.art = [Resource(
            "{0}/contents/3000/{1}/images/player_thumbnail.jpg".format(
                BASE_URL, video_code
            )
        )]

        # Trailer
        trailer_url = "https://hls.heyzo.com/sample/3000/{0}/mb.m3u8".format(
            video_code
        )
        trailer = Resource(trailer_url)
        trailer.thumb = "{0}/contents/3000/{1}/images/player_thumbnail.jpg".format(
            BASE_URL, video_code
        )
        metadata.trailers = [trailer]

        return metadata

    def fetch(self, video_code, lang):
        url = "{0}/moviepages/{1}/index.html".format(BASE_URL, video_code)
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.content.decode("utf-8")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def guess_video_code(self, text):
        """Try to extract a Heyzo movie ID from *text*.

        Only matches if the text contains 'heyzo' and a 4-digit number.

        Args:
            text (str): Filename, directory name, or media name.

        Returns:
            str or None: Movie ID (e.g. ``"0647"``), or ``None``.
        """
        text_lower = text.lower()
        if "heyzo" not in text_lower:
            return None
        # Find a 4-digit number separated by whitespace or delimiters
        match = re.search(r"\s+(\d{4})(?:\s+|$)", text_lower)
        if match:
            return match.group(1)

    def parse_release_date(self, soup):
        """Extract the release date from the movie info table.

        Args:
            soup: Parsed BeautifulSoup document.

        Returns:
            datetime.datetime or None: The release date, or ``None``.
        """
        tr = soup.select_one("tr.table-release-day")
        if tr:
            tds = tr.select("td")
            if len(tds) >= 2:
                dt_str = tds[1].text.strip()
                try:
                    return datetime.datetime.strptime(dt_str, "%Y-%m-%d")
                except ValueError:
                    pass
        return None
