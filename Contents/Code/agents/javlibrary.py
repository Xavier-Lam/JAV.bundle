# coding=utf-8

import datetime
from difflib import SequenceMatcher
import re

from bs4 import BeautifulSoup
import flaresolverr_session
import requests

from .base import MetadataAgent, SearchAgent
from .types import Metadata, Person, Resource, SearchItem
from .utils import get_code_group, guess_video_code


BASE_URL = "https://www.javlibrary.com"


class JAVLibrary(SearchAgent, MetadataAgent):
    """Agent that scrapes metadata from javlibrary.com."""

    name = "JAVLibrary"
    weight = 900

    @property
    def session(self):
        # prefer FlareSolverr session if configured
        return self.flaresolverr_session or super(JAVLibrary, self).session

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def guess_keywords(self, name, filename, directory):
        text = u" ".join([name or "", filename or "", directory or ""])
        code = guess_video_code(text)
        if code:
            return [code.upper()]
        return []

    def search(self, keywords, lang):
        video_code = keywords[0]
        url = "{0}/ja/vl_searchbyid.php".format(BASE_URL)
        resp = self.session.get(url, params={"keyword": video_code})
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        found = []
        videos_div = soup.select_one("div.videos")
        if videos_div:
            # Multiple results page
            for video in videos_div.select("div.video"):
                link = video.select_one("a")
                if not link:
                    continue
                href = link.get("href", "")
                agent_id = self.extract_agent_id_from_href(href)
                if not agent_id:
                    continue
                video_id_el = video.select_one("div.id")
                video_id = video_id_el.text.strip().upper() if video_id_el else ""
                title = link.get("title", "")
                score = int(
                    SequenceMatcher(
                        None,
                        video_code,
                        video_id).ratio() *
                    100)
                img = video.select_one("img")
                thumb = img.get("src", "") if img else ""
                if thumb and not thumb.startswith("http"):
                    thumb = "https:" + thumb

                item = SearchItem()
                item.id = agent_id
                item.video_code = video_id
                item.title = title
                item.score = score
                item.thumb = thumb
                found.append(item)
        else:
            # Single result (redirected to detail page)
            title_div = soup.select_one("div#video_title")
            if title_div:
                link = title_div.select_one("a")
                if link:
                    href = link.get("href", "")
                    agent_id = self.extract_agent_id_from_href(href)
                    title = link.text.strip()
                    video_id = title.split()[0].upper(
                    ) if title else video_code

                    item = SearchItem()
                    item.id = agent_id
                    item.video_code = video_id
                    item.title = title
                    item.score = 100
                    found.append(item)
        return found

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, agent_id, video_code, lang):
        html = self.fetch(agent_id, lang)
        soup = BeautifulSoup(html, "html.parser")

        metadata = Metadata()
        metadata.code_group = get_code_group(video_code)

        # Title
        title_div = soup.select_one("div#video_title")
        title_text = None
        if title_div:
            a = title_div.select_one("a")
            if a:
                title_text = a.text.strip()
        metadata.title = title_text
        metadata.japanese_title = title_text
        metadata.title_sort = title_text

        # Release date
        div = soup.select_one("div#video_date")
        if div:
            td = div.select_one("td.text")
            if td:
                match = re.search(r"\d{4}-\d{2}-\d{2}", td.text.strip())
                if match:
                    try:
                        metadata.release_date = datetime.datetime.strptime(
                            match.group(0), "%Y-%m-%d"
                        )
                    except ValueError:
                        pass

        # Studio
        div = soup.select_one("div#video_maker")
        if div:
            a = div.select_one("td.text a")
            if a:
                metadata.studio = a.text.strip()

        # Duration
        div = soup.select_one("div#video_length")
        if div:
            span = div.select_one("span.text")
            if span:
                match = re.search(r"\d+", span.text)
                if match:
                    metadata.duration = int(match.group(0)) * 60 * 1000

        # Rating
        div = soup.select_one("div#video_review")
        if div:
            score_span = div.select_one("span.score")
            if score_span:
                try:
                    metadata.rating = float(score_span.text.strip("() "))
                except ValueError:
                    pass

        # Genres
        div = soup.select_one("div#video_genres")
        if div:
            metadata.genres = set(
                a.text.strip()
                for a in div.select("span.genre a")
                if a.text.strip()
            )

        # Actresses
        div = soup.select_one("div#video_cast")
        if div:
            metadata.actresses = [
                Person(a.text.strip())
                for a in div.select("span.star a")
                if a.text.strip()
            ]

        # Directors
        div = soup.select_one("div#video_director")
        if div:
            metadata.directors = [
                Person(a.text.strip())
                for a in div.select("td.text a")
                if a.text.strip()
            ]

        # Labels
        div = soup.select_one("div#video_label")
        if div:
            a = div.select_one("td.text a")
            if a:
                label_text = a.text.strip()
                if label_text:
                    metadata.labels = set([label_text])

        img = soup.select_one("img#video_jacket_img")
        if img:
            src = img.get("src", "")
            if src and not src.startswith("http"):
                src = "https:" + src
            if src:
                poster_url = src.replace("pl.jpg", "ps.jpg")
                metadata.posters = [Resource(poster_url)]
                metadata.art = [Resource(src)]

        return metadata

    def fetch(self, agent_id, lang):
        url = "{0}/ja/".format(BASE_URL)
        # legacy agent_id has .html suffix
        if agent_id.endswith(".html"):
            agent_id = agent_id[:-5]
        resp = self.session.get(url, params={"v": "jav" + agent_id})
        resp.raise_for_status()
        return resp.content.decode("utf-8")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def extract_agent_id_from_href(self, href):
        """Extract the JAVLibrary agent ID from a link href.

        The href format is ``./javXXXXXXX.html`` or ``/ja/javXXXXXXX.html``.
        The agent ID is the part after ``jav`` without the ``.html``
        extension.

        Args:
            href (str): The href attribute value.

        Returns:
            str or None: Agent ID (e.g. ``"li7ah34"``), or ``None``.
        """
        match = re.search(r"jav([a-z0-9]+)(?:\.html)?$", href)
        if match:
            return match.group(1)
        return None
