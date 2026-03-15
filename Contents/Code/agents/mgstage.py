# coding=utf-8

import datetime
from difflib import SequenceMatcher
import json
import re

from bs4 import BeautifulSoup

from .base import MetadataAgent, SearchAgent
from .types import Metadata, Person, Resource, SearchItem
from .utils import get_code_group, guess_video_code


BASE_URL = "https://www.mgstage.com"
SEARCH_URL = BASE_URL + "/search/cSearch.php"
DETAIL_URL = BASE_URL + "/product/product_detail/{product_id}/"
SAMPLE_RESPONS_URL = BASE_URL + "/sampleplayer/sampleRespons.php"


class MGStage(SearchAgent, MetadataAgent):
    """Agent that scrapes metadata from mgstage.com."""

    name = "MGStage"
    weight = 500

    def create_session(self):
        """Return a new session with the MGStage age-check cookie pre-set."""
        s = super(MGStage, self).create_session()
        s.cookies.set("adc", "1", domain=".mgstage.com")
        return s

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
        keyword = keywords[0]
        resp = self.session.get(
            SEARCH_URL,
            params={"search_word": keyword, "type": "top"},
        )
        resp.raise_for_status()
        html = resp.content.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        found = []
        for li in soup.select("li.product_list_item"):
            link = li.select_one('a[href*="product_detail"]')
            if not link:
                continue

            href = link.get("href", "")
            m = re.search(r"product_detail/([^/]+)/", href)
            if not m:
                continue
            product_id = m.group(1).upper()

            # Title
            title_el = li.select_one("a.title")
            title = title_el.get_text(strip=True) if title_el else product_id

            # Thumbnail
            img = li.select_one("img")
            thumb = img.get("src", "") if img else ""

            # Normalize by stripping leading digits (e.g. "1234ABCD" -> "ABCD")
            video_code = product_id.lstrip("1234567890")
            score = int(
                SequenceMatcher(None, keyword.upper(), video_code).ratio() * 100
            )

            item = SearchItem()
            item.id = product_id
            item.video_code = video_code
            item.title = u"{0} {1}".format(video_code, title)
            item.score = score
            item.thumb = thumb
            found.append(item)

        return found

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, agent_id, video_code, lang):
        html = self.fetch(agent_id, lang)
        soup = BeautifulSoup(html, "html.parser")

        # Extract sample UUID from the first button_sample link.
        sample_uuid = None
        btn = soup.select_one("a.button_sample")
        if btn:
            href = btn.get("href", "")
            m = re.search(r"/sampleplayer/sampleplayer\.html/([^/?]+)", href)
            if m:
                sample_uuid = m.group(1)

        # Attempt to resolve sample trailer URL.
        trailer_url = self.resolve_trailer(
            self.session, sample_uuid,
            DETAIL_URL.format(product_id=agent_id),
        )

        metadata = Metadata()
        metadata.code_group = get_code_group(video_code)

        # Title
        el = soup.select_one("h1.tag")
        if not el:
            el = soup.select_one(".common_detail_cover h1")
        if el:
            title_text = el.get_text(strip=True)
            metadata.title = u"{0} {1}".format(video_code, title_text)
        metadata.japanese_title = metadata.title
        metadata.title_sort = metadata.title

        # Release date
        for label in (u"配信開始日", u"商品発売日"):
            value = self.find_table_value(soup, label)
            if value:
                m = re.search(r"(\d{4})/(\d{2})/(\d{2})", value)
                if m:
                    try:
                        metadata.release_date = datetime.datetime(
                            int(m.group(1)),
                            int(m.group(2)),
                            int(m.group(3)),
                        )
                        break
                    except ValueError:
                        continue

        # Studio
        metadata.studio = self.find_table_value(soup, u"メーカー") or None

        # Duration
        value = self.find_table_value(soup, u"収録時間")
        if value:
            m = re.search(r"(\d+)", value)
            if m:
                metadata.duration = int(m.group(1)) * 60 * 1000

        # Summary
        for sel in (".introduction p.txt", "#introduction p.txt"):
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    metadata.summary = text
                    break

        # Rating
        td = soup.select_one("td.review")
        if td:
            text = td.get_text(strip=True)
            m = re.search(r"(\d+\.?\d*)", text)
            if m:
                metadata.rating = float(m.group(1)) * 2  # 5-star -> 10-point

        # Genres
        links = self.find_table_links(soup, u"ジャンル")
        if links:
            genres = [
                a.get_text(strip=True) for a in links
                if a.get_text(strip=True)
            ]
            if genres:
                metadata.genres = set(genres)

        # Actresses
        links = self.find_table_links(soup, u"出演")
        if links:
            metadata.actresses = [
                Person(a.get_text(strip=True))
                for a in links if a.get_text(strip=True)
            ]

        # Series
        value = self.find_table_value(soup, u"シリーズ")
        if value:
            metadata.series = value

        # Art (large background image - pb_e_*.jpg)
        art_url = None
        el = soup.select_one("#EnlargeImage")
        if not el:
            el = soup.select_one("a.link_magnify")
        if el:
            art_url = el.get("href", "") or None

        # Poster (small cover image - pf_o1_*.jpg)
        poster_url = None
        img = soup.select_one(".detail_photo img.enlarge_image")
        if not img:
            img = soup.select_one(
                '.detail_photo img[src*="image.mgstage.com"]'
            )
        if img:
            poster_url = img.get("src", "") or None
        if not poster_url and art_url:
            poster_url = art_url

        if poster_url:
            metadata.posters = [Resource(poster_url)]
        if art_url:
            metadata.art = [Resource(art_url)]

        # Trailer
        if trailer_url:
            trailer = Resource(trailer_url)
            if poster_url:
                trailer.thumb = poster_url
            trailer.score = 100  # prefer studio-provided trailer
            metadata.trailers = [trailer]

        return metadata

    def fetch(self, product_id, lang):
        url = DETAIL_URL.format(product_id=product_id)
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.content.decode("utf-8", errors="ignore")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def find_table_value(self, soup, label):
        """Return the text of the ``<td>`` paired with a ``<th>``
        containing *label*.

        MGStage detail pages use ``<th>``/``<td>`` pairs rather than
        two ``<td>`` columns.

        Args:
            soup: Parsed BeautifulSoup document.
            label (unicode): Japanese label text to look for.

        Returns:
            str or None: Stripped text, or ``None``.
        """
        for th in soup.find_all("th"):
            if label in th.get_text(strip=True):
                td = th.find_next_sibling("td")
                if td:
                    return td.get_text(strip=True)
        return None

    def find_table_links(self, soup, label):
        """Return the ``<a>`` elements inside the ``<td>`` paired with
        a ``<th>`` containing *label*.

        Args:
            soup: Parsed BeautifulSoup document.
            label (unicode): Japanese label text.

        Returns:
            list: List of ``<a>`` :class:`bs4.element.Tag` objects.
        """
        for th in soup.find_all("th"):
            if label in th.get_text(strip=True):
                td = th.find_next_sibling("td")
                if td:
                    return td.find_all("a")
        return []

    def resolve_trailer(self, session, sample_uuid, referer):
        """Attempt to fetch the sample-video MP4 URL via sampleRespons.php.

        Args:
            session: Authenticated :class:`requests.Session`.
            sample_uuid (str or None): UUID extracted from a button_sample href.
            referer (str): The detail page URL (used as Referer header).

        Returns:
            str or None: MP4 URL, or ``None``.
        """
        if not sample_uuid:
            return None
        try:
            resp = session.get(
                SAMPLE_RESPONS_URL,
                params={"pid": sample_uuid},
                headers={"Referer": referer},
            )
            resp.raise_for_status()
        except Exception:
            return None
        try:
            data = json.loads(resp.content.decode("utf-8", errors="ignore"))
        except (ValueError, KeyError):
            return None
        url = data.get("url", "")
        if not url:
            return None
        # The API returns a Smooth Streaming URL (.ism/request?...).  Convert
        # it to the equivalent .mp4 file on the same CDN path.
        url = re.sub(r"\.ism.*$", ".mp4", url)
        return url or None
