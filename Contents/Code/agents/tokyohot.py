# coding=utf-8

import datetime
import re
import urllib

from bs4 import BeautifulSoup

from .base import SearchAgent, StudioAgent
from .types import Metadata, Person, Resource, SearchItem


BASE_URL = "https://my.tokyo-hot.com"
CDN_URL = "https://my.cdn.tokyo-hot.com"
DEFAULT_STUDIO = u"東熱"

# Pattern to extract a TokyoHot movie ID from a filename or directory name.
# The movie ID format is a letter followed by digits (e.g. "n0820", "k1234").
MOVIE_ID_PATTERN = re.compile(r"(?:k|n)\d{4}", re.IGNORECASE)

# Keywords that hint the media belongs to TokyoHot.
SEARCH_KEYWORDS = (u"tokyo hot", u"東熱", u"tokyo-hot")


class TokyoHot(SearchAgent, StudioAgent):
    """Agent that scrapes metadata from my.tokyo-hot.com."""

    name = "TokyoHot"
    weight = 500

    @property
    def enabled(self):
        return True

    def create_session(self):
        """Return a new session with the TokyoHot language cookie set.

        Visiting the homepage sets the ``lang=ja`` preference cookie that
        is required for Japanese-language responses.
        """
        s = super(TokyoHot, self).create_session()
        s.get("{0}/index?lang=ja".format(BASE_URL))
        return s

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def guess_keywords(self, name, filename, directory):
        text = u" ".join([name or "", filename or "", directory or ""]).lower()
        if not [kw for kw in SEARCH_KEYWORDS if kw in text]:
            return []
        match = re.search(MOVIE_ID_PATTERN, text)
        if not match:
            return []
        return [match.group(0)]

    def search(self, keywords, lang):
        video_code = keywords[0]
        url = "{0}/product/".format(BASE_URL)
        params = {"q": video_code}
        resp = self.session.get(url, params=params)
        self.raise_for_status(resp)
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        wrap = soup.select_one("ul.list")
        if not wrap:
            return []

        found = []
        for product in wrap.select("a"):
            title_el = product.select_one("div.title")
            href = product.get("href", "")
            match = re.match(r"/product/(\d+)/", href)
            if not match:
                continue
            agent_id = match.group(1)
            title = title_el.text.strip() if title_el else video_code
            title = u"{0} {1} {2}".format(DEFAULT_STUDIO, video_code, title)
            img = product.select_one("img")
            thumb = img["src"] if img and img.get("src") else None

            item = SearchItem()
            item.id = agent_id
            item.video_code = video_code
            item.title = title
            item.score = 100
            item.thumb = thumb
            found.append(item)

        return found

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, agent_id, video_code, lang):
        html = self.fetch(agent_id, lang)
        soup = BeautifulSoup(html, "html.parser")

        metadata = Metadata()

        # Actresses
        dd = self.find_info(soup, u"出演者")
        if dd:
            metadata.actresses = [
                Person(a.text.strip())
                for a in dd.select("a") if a.text.strip()
            ]

        # Title
        main = soup.select_one("div#main")
        studio = DEFAULT_STUDIO
        dd_label = self.find_info(soup, u"レーベル")
        if dd_label:
            link = dd_label.select_one("a")
            if link:
                studio = link.text.strip()
        metadata.studio = studio

        if main:
            h2 = main.select_one("h2")
            if h2:
                title_text = h2.text.strip()
                if video_code:
                    metadata.title = u"{0} {1} {2}".format(
                        studio, video_code, title_text
                    )
                else:
                    metadata.title = u"{0} {1}".format(studio, title_text)
        metadata.japanese_title = metadata.title
        if video_code:
            metadata.title_sort = u"Tokyo-Hot {0}".format(video_code)
        else:
            metadata.title_sort = metadata.title

        # Release date
        dd = self.find_info(soup, u"配信開始日")
        if dd:
            dt_str = dd.text.strip()
            match = re.search(r"\d+/\d+/\d+", dt_str)
            if match:
                try:
                    metadata.release_date = datetime.datetime.strptime(
                        match.group(0), "%Y/%m/%d"
                    )
                except ValueError:
                    pass

        # Duration
        dd = self.find_info(soup, u"収録時間")
        if dd:
            text = dd.text.strip()
            try:
                dt = datetime.datetime.strptime(text, "%H:%M:%S")
                diff = dt - datetime.datetime(1900, 1, 1)
                metadata.duration = int(diff.total_seconds()) * 1000
            except ValueError:
                pass

        # Summary
        if main:
            el = main.select_one("div.sentence")
            if el:
                metadata.summary = el.text.strip()

        # Genres
        genres = []
        dd = self.find_info(soup, u"タグ")
        if dd:
            genres.extend(a.text.strip()
                          for a in dd.select("a") if a.text.strip())
        dd = self.find_info(soup, u"プレイ内容")
        if dd:
            genres.extend(a.text.strip()
                          for a in dd.select("a") if a.text.strip())
        if genres:
            metadata.genres = set(genres)

        # # Series
        # dd = self.find_info(soup, u"シリーズ")
        # if dd:
        #     for a in dd.select("a"):
        #         text = a.text.strip()
        #         if text:
        #             metadata.series = text
        #             break

        # Posters
        metadata.posters = [Resource(
            "{0}/media/{1}/package/_v.jpg".format(CDN_URL, agent_id)
        )]

        # Art
        if video_code:
            metadata.art = [Resource(
                "{0}/media/{1}/jacket/{2}.jpg".format(
                    CDN_URL, agent_id, video_code
                )
            )]

        # Trailer
        trailer_file = "https://my.cdn.tokyo-hot.com/media/samples/{0}.mp4".format(
            agent_id
        )
        thumb = self.get_video_poster(soup)
        if thumb:
            thumb = urllib.quote(thumb, safe=":/")
        else:
            if video_code:
                thumb = "{0}/media/{1}/jacket/{2}.jpg".format(
                    CDN_URL, agent_id, video_code,
                )
        trailer = Resource(trailer_file)
        if thumb:
            trailer.thumb = thumb
        metadata.trailers = [trailer]

        return metadata

    def fetch(self, agent_id, lang):
        url = "{0}/product/{1}/".format(BASE_URL, agent_id)
        resp = self.session.get(url)
        self.raise_for_status(resp)
        return resp.content.decode("utf-8")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def guess_movie_id(self, text):
        """Try to extract a TokyoHot movie ID from *text*.

        Args:
            text (str): Filename, directory name, or media name.

        Returns:
            str or None: Movie ID keyword (e.g. ``"n0820"``), or ``None``.
        """
        text_lower = text.lower()
        if "tokyo" not in text_lower or "hot" not in text_lower:
            return None
        match = MOVIE_ID_PATTERN.search(text_lower)
        if match:
            return match.group(0)
        return None

    def find_info(self, soup, title):
        """Find a ``dd`` element in the info ``dl`` whose ``dt`` matches *title*.

        Args:
            soup: Parsed BeautifulSoup document.
            title (unicode): The Japanese label text to match.

        Returns:
            The ``dd`` element, or ``None``.
        """
        main = soup.select_one("div#main")
        if not main:
            return None
        info = main.select_one("dl.info")
        if not info:
            return None
        for dt in info.select("dt"):
            if dt.text.strip() == title:
                dd = dt.find_next_sibling("dd")
                return dd
        return None

    def get_video_poster(self, soup):
        """Extract the ``poster`` attribute from the ``<video>`` element.

        Args:
            soup: Parsed BeautifulSoup document.

        Returns:
            str or None: The poster URL string, or ``None``.
        """
        video = soup.select_one("video[poster]")
        if video:
            return video.get("poster")
        return None
