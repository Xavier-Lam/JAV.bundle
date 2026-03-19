# coding=utf-8

from collections import defaultdict
import copy
import datetime
import json
import re

from bs4 import BeautifulSoup

from .base import MetadataAgent, SearchAgent
from .types import Metadata, Person, Resource, SearchItem
from .utils import get_code_group, guess_video_code


BASE_URL = "https://www.dmm.co.jp"
SEARCH_URL = BASE_URL + \
    "/search/=/searchstr={keyword}/limit=30/sort=rankprofile"

# Extracts the URL pattern (e.g. "mono/dvd") and CID from a DMM detail href.
DETAIL_RE = re.compile(r"/([a-z]+/[a-z]+)/-/detail/=/cid=([^/&?]+)")


class DMM(SearchAgent, MetadataAgent):
    """Agent that scrapes metadata from dmm.co.jp."""

    name = "DMM"
    weight = 800

    def create_session(self):
        """Return a new session with the DMM age-check cookie pre-set."""
        s = super(DMM, self).create_session()
        s.cookies.set("age_check_done", "1", domain=".dmm.co.jp")
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
        target = keyword.replace(u"-", u"").lower()
        url = SEARCH_URL.format(keyword=keyword)
        resp = self.session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(
            resp.content.decode("utf-8", "ignore"), "html.parser")

        found = defaultdict(list)
        item = SearchItem()
        for link in soup.find_all(
                "a", href=lambda h: h and "/detail/=/cid=" in h):
            href = link.get("href", "")
            m = DETAIL_RE.search(href)
            if not m:
                continue
            pattern, cid = m.group(1), m.group(2)
            if target not in cid.lower():
                continue
            if target != self.normalize_cid(cid).lower():
                continue

            if not item.title:
                item.title = self.clean_title_element(link)
            if not item.thumb:
                img = link.find("img")
                item.thumb = img.get("src", "") if img else ""
            found[pattern].append(cid)

        if not found:
            return []

        if "mono/dvd" in found:
            # prioritize mono/dvd
            if target in found["mono/dvd"]:
                key = "mono/dvd/{0}".format(target)
            else:
                key = "mono/dvd/{0}".format(found["mono/dvd"][0])
        elif "rental/ppr" in found:
            key = "rental/ppr/{0}".format(found["rental/ppr"][0])
        else:
            pattern = list(found.keys())[0]
            key = "{0}/{1}".format(pattern, found[pattern][0])

        item.id = key.replace("/", "_")
        item.title = (keyword + " " + item.title) if item.title else keyword
        item.video_code = keyword
        item.score = 100
        return [item]

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, agent_id, video_code, lang):
        pattern, cid = agent_id.replace("_", "/", 2).rsplit("/", 1)
        html = self.fetch(pattern, cid)
        soup = BeautifulSoup(html, "html.parser")

        metadata = Metadata()
        metadata.code_group = get_code_group(video_code)

        # Title - try h1#title (mono/dvd, digital), then h1.item (rental/ppr),
        # then og:title meta tag as a last resort.
        el = soup.select_one("h1#title") or soup.select_one("h1.item")
        if el:
            title_text = self.clean_title_element(el)
            metadata.title = u"{0} {1}".format(video_code, title_text)
        else:
            og = soup.find("meta", property="og:title")
            if og:
                title_text = (og.get("content") or u"").strip()
                if title_text:
                    metadata.title = u"{0} {1}".format(video_code, title_text)
        metadata.japanese_title = metadata.title
        metadata.title_sort = metadata.title

        # Release date
        for label in (u"発売日", u"配信開始日", u"貸出開始日"):
            value = self.find_table_value(soup, label)
            if value:
                m = re.search(r"(\d{4})/(\d{2})/(\d{2})", value)
                if m:
                    try:
                        metadata.release_date = datetime.datetime(
                            int(m.group(1)), int(m.group(2)), int(m.group(3)),
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
        for sel in ("p.mg-b20", "div.mg-b20 p"):
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    metadata.summary = text
                    break

        # Rating
        el = soup.select_one("p.dcd-review__average")
        if el:
            text = el.get_text(strip=True)
            m = re.search(r"(\d+\.?\d*)", text)
            if m:
                metadata.rating = float(m.group(1)) * 2  # 5-star -> 10-point

        # Genres
        links = self.find_table_links(soup, u"ジャンル")
        if links:
            genres = [
                a.get_text(strip=True) for a in links
                if a.get_text(strip=True) and a.get_text(strip=True) != u"サンプル動画"
            ]
            if genres:
                metadata.genres = set(genres)

        # Actresses
        links = self.find_table_links(soup, u"出演者")
        if links:
            metadata.actresses = [
                Person(re.sub(ur"\uff08[^\uff09]*\uff09", u"", a.get_text(strip=True)).strip())
                for a in links if a.get_text(strip=True)
            ]

        # Directors
        links = self.find_table_links(soup, u"監督")
        if links:
            metadata.directors = [
                Person(a.get_text(strip=True))
                for a in links if a.get_text(strip=True)
            ]

        # Series
        raw = self.find_table_value(soup, u"シリーズ")
        value = raw.strip("-") if raw else ""
        if value:
            metadata.series = value

        # Labels
        label_value = self.find_table_value(soup, u"レーベル")
        if label_value:
            metadata.labels = set([label_value])

        # Poster & Art – scrape from the page image, fall back to pattern.
        img = soup.find("img", src=lambda s: s and "pics.dmm.co.jp" in s)
        if img:
            src = img.get("src", "")
            art_url = re.sub(
                r"(?<=/)([^/]+)(?:ps|pt)\.jpg$", r"\1pl.jpg", src)
            art_url = Resource(art_url)
            art_url.score = 55
            poster_url = re.sub(
                r"(?<=/)([^/]+)(?:pl|pt)\.jpg$", r"\1ps.jpg", src)
            poster_url = Resource(poster_url)
            poster_url.score = 55
            metadata.posters = [poster_url]
            metadata.art = [art_url]
        else:
            metadata.posters = [Resource(self.image_url(cid, "ps", pattern))]
            metadata.art = [Resource(self.image_url(cid, "pl", pattern))]

        # Trailer
        trailer_url = self.resolve_trailer(soup)
        if trailer_url and self.validate_resource(trailer_url, "video/"):
            trailer = Resource(trailer_url)
            trailer.thumb = self.image_url(cid, "pl", pattern)
            trailer.score = 30  # 403 errors are common
            metadata.trailers = [trailer]

        return metadata

    def fetch(self, pattern, cid):
        """Fetch the detail page HTML for the given pattern and CID.

        Args:
            pattern (str): URL pattern, e.g. ``"mono/dvd"`` or ``"rental/ppr"``.
            cid (str): DMM content-ID.

        Returns:
            str: The HTML content of the detail page.

        Raises:
            Exception: If the page is not found or has no server-rendered content.
        """
        url = "{0}/{1}/-/detail/=/cid={2}/".format(BASE_URL, pattern, cid)
        resp = self.session.get(url)
        resp.raise_for_status()
        html = resp.content.decode("utf-8", "ignore")
        if "self.__next_f" in html and "<h1" not in html:
            raise Exception(
                "No server-rendered content for cid={0}".format(cid))
        return html

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def image_url(self, cid, variant, pattern):
        """Build a DMM CDN image URL for *cid* and image *variant*.

        Args:
            cid: DMM content-ID.
            variant: Image size suffix, e.g. ``"pl"``, ``"ps"``, ``"pt"``.
            pattern: URL pattern, e.g. ``"mono/dvd"`` or ``"digital/videoa"``.

        Returns:
            str: The absolute image URL.
        """
        if "digital" in pattern:
            base = "https://pics.dmm.co.jp/digital/video"
        else:
            base = "https://pics.dmm.co.jp/mono/movie"
        return "{0}/{1}/{1}{2}.jpg".format(base, cid, variant)

    # ------------------------------------------------------------------
    # Title helpers
    # ------------------------------------------------------------------

    def clean_title_element(self, el):
        """Return the text of *el* with DMM format-badge spans removed.

        DMM injects ``<span class="ic">`` elements inside title tags to
        indicate the release format (e.g. "DVD", "HD", "Blu-ray").  This
        method strips those before returning the plain text.

        Args:
            el: A BeautifulSoup tag.

        Returns:
            str: Cleaned plain-text string.
        """
        el = copy.copy(el)
        for img in el.find_all("img"):
            img.decompose()
        for badge in el.find_all("span", class_="ic"):
            badge.decompose()
        # Rental/PPR pages inject exclusivity badges like 【独占】 in a
        # <span class="red"> inside the h1.  Strip those too.
        for badge in el.find_all("span", class_="red"):
            badge.decompose()

        # DMM search page structure places the title inside a <p> element
        el = el.find("p") or el
        text = el.get_text(separator=u" ", strip=True)
        # Strip 【...】 bracket badges (e.g. 【ベストヒット】, 【アウトレット】).
        text = re.sub(u"\u3010[^\u3011]*\u3011", u"", text)
        # Strip （BOD）
        text = text.replace(u"（BOD）", u"")
        return re.sub(r" +", u" ", text).strip()

    def find_table_value(self, soup, label):
        """Return the text content of the value ``<td>`` whose preceding
        sibling ``<td>`` contains *label*.

        Handles both the normal two-column table layout used by mono/dvd
        pages and the rental/ppr layout where many detail fields appear as
        sibling ``<td>`` elements inside a single ``<tr>``.

        Args:
            soup: Parsed BeautifulSoup document.
            label (unicode): Japanese label text to look for.

        Returns:
            str or None: Stripped text, or ``None``.
        """
        # Iterate every <td> in every table row.  When a cell's text
        # matches *label* (ignoring a trailing full-width colon), return the
        # text of the immediately following sibling <td>.
        for td in soup.select("table td"):
            text = td.get_text(strip=True).rstrip(u"\uff1a")
            if text == label:
                # Try the next sibling <td>
                sibling = td.find_next_sibling("td")
                if sibling:
                    return sibling.get_text(strip=True)
        return None

    def find_table_links(self, soup, label):
        """Return the ``<a>`` elements inside the value cell of a row
        whose label cell contains *label*.

        Args:
            soup: Parsed BeautifulSoup document.
            label (unicode): Japanese label text.

        Returns:
            list: List of ``<a>`` :class:`bs4.element.Tag` objects.
        """
        for td in soup.select("table td"):
            text = td.get_text(strip=True).rstrip(u"\uff1a")
            if text == label:
                sibling = td.find_next_sibling("td")
                if sibling:
                    return sibling.find_all("a")
        return []

    def resolve_trailer(self, soup):
        """Resolve the sample-video MP4 URL from the detail page.

        DMM detail pages expose a ``data-video-url`` attribute that
        points to an AJAX endpoint.  The endpoint returns an ``<iframe>``
        whose source is a litevideo player page.  The player page contains
        a JSON ``args`` object with the actual video ``src`` URL.

        Args:
            soup: The parsed detail page.

        Returns:
            str or None: The absolute MP4 URL, or ``None``.
        """
        el = soup.find(True, attrs={"data-video-url": True})
        if el:
            ajax_path = el.get("data-video-url", "")
            if not ajax_path:
                return None
            ajax_url = BASE_URL + ajax_path
        else:
            # Rental/PPR pages embed the AJAX URL in an onclick handler:
            # onclick="sampleplay('https://...ajax-sample/...');return false;"
            el = soup.find(True, onclick=re.compile(r"sampleplay\("))
            if not el:
                return None
            m = re.search(r"sampleplay\('([^']+)'", el.get("onclick", ""))
            if not m:
                return None
            ajax_url = m.group(1)
        try:
            resp = self.session.get(ajax_url)
            resp.raise_for_status()
        except Exception:
            return None

        ajax_html = resp.content.decode("utf-8", errors="ignore")
        iframe_soup = BeautifulSoup(ajax_html, "html.parser")
        iframe = iframe_soup.find("iframe")
        if not iframe:
            return None

        player_url = iframe.get("src", "")
        if not player_url:
            return None
        if not player_url.startswith("http"):
            player_url = "https:" + player_url

        try:
            resp = self.session.get(player_url)
            resp.raise_for_status()
        except Exception:
            return None

        player_html = resp.content.decode("utf-8", errors="ignore")
        return self.extract_video_url(player_html)

    def extract_video_url(self, player_html):
        """Extract the MP4 video URL from a DMM litevideo player page.

        The player page contains a JavaScript ``args`` object with a
        ``src`` field pointing to the sample video and optionally a
        ``bitrates`` array with multiple quality options.

        Args:
            player_html (str): The raw HTML of the player page.

        Returns:
            str or None: The absolute video URL, or ``None``.
        """
        m = re.search(r"const\s+args\s*=\s*(\{.+?\});\s*$", player_html,
                      re.MULTILINE | re.DOTALL)
        if not m:
            return None
        try:
            args = json.loads(m.group(1))
        except (ValueError, TypeError):
            return None

        src = args.get("src", "")
        if src:
            if not src.startswith("http"):
                src = "https:" + src
            return src

        bitrates = args.get("bitrates", [])
        if bitrates:
            src = bitrates[0].get("src", "")
            if src and not src.startswith("http"):
                src = "https:" + src
            return src if src else None

        return None

    def normalize_cid(self, cid):
        """Strip leading-digit prefix from a DMM content-ID.

        DMM uses numeric prefixes such as ``7`` to distinguish special
        editions (e.g. *Best Hits*).  ``7jbd226`` and ``jbd226`` refer
        to the same underlying title.

        Args:
            cid (str): Raw content-ID (e.g. ``"7jbd226"``).

        Returns:
            str: Normalised CID (e.g. ``"jbd226"``).
        """
        m = re.match(r"^(?:[a-zA-Z]+_)?\d*([a-zA-Z].*\d+)[a-zA-Z]*$", cid)
        if m:
            return m.group(1)
        return cid
