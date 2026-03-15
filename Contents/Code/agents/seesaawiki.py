# coding=utf-8

import re
import urllib

import requests
from bs4 import BeautifulSoup

from .base import PartialMetadataAgent
from .types import Person


BASE_URL = "https://seesaawiki.jp/w/sougouwiki"
SEARCH_URL = BASE_URL + "/search"

# Maximum number of search-result pages to visit when looking for actresses.
MAX_PAGES_TO_VISIT = 5


class SeesaaWiki(PartialMetadataAgent):
    name = "SeeSaaWiki"

    def __init__(self, *args, **kwargs):
        self.cache = {}
        super(SeesaaWiki, self).__init__(*args, **kwargs)

    @property
    def weight(self):
        return -100

    # ------------------------------------------------------------------
    # PartialMetadataAgent interface
    # ------------------------------------------------------------------

    def partial_update(self, video_code, metadata, lang):
        actresses = list(metadata.actresses or [])

        # If no actresses are present yet, try to discover them from the wiki.
        if not actresses:
            discovered = self.discover_actresses(video_code)
            if discovered:
                actresses = map(Person, discovered)
                self.logger.debug("Discovered actresses for %s: %s",
                                  video_code, u", ".join(str(a) for a in actresses))

        # Correct each actress name via page-name lookup.
        corrected = []
        for actress in actresses:
            new_name = self.get_actress_name(actress)
            if new_name and new_name != actress:
                self.logger.debug("Corrected actress name: %s -> %s",
                                  actress, new_name)
                p = Person(new_name)
                p.photo = actress.photo
                corrected.append(p)
            else:
                corrected.append(actress)

        metadata.actresses = corrected

    # ------------------------------------------------------------------
    # Actress discovery (by unique ID)
    # ------------------------------------------------------------------

    def discover_actresses(self, video_code):
        """Search seesaawiki for *video_code* and return a list of Person.

        Strategy:
        1. Full-text search for the video code.
        2. Visit result pages and look for a series/label **table** whose
           row matches the code — extract names from the ACTRESS column.
        3. If no table match, fall back to result pages that look like
           actress filmography pages (date + code pattern for that entry).
        """
        if not video_code:
            return []

        search_results = self.search_wiki(video_code)
        if not search_results:
            return []

        # Phase 1: visit pages and collect soups (limit network calls)
        pages = []  # (title, url, soup)
        for title, url in search_results[:MAX_PAGES_TO_VISIT]:
            if not url:
                continue
            try:
                soup = self.fetch_page(url)
            except Exception:
                continue
            pages.append((title, url, soup))

        # Phase 2: try the structured table approach
        for title, url, soup in pages:
            names = self.find_actresses_in_table(soup, video_code)
            if names:
                return names

        # Phase 3: fall back to actress-page detection
        names = []
        for title, url, soup in pages:
            if self.has_filmography_entry(soup, video_code):
                name = self.extract_page_name(soup) or title
                names.append(name)
        return names

    # ------------------------------------------------------------------
    # Actress name correction (by name search)
    # ------------------------------------------------------------------

    def get_actress_name(self, name):
        """Return the canonical actress name from seesaawiki.

        Results are memoised in ``self._cache`` so that repeated calls for
        the same input name do not trigger additional network requests.

        1. Return the cached result if available.
        2. Search by page name.
        3. Visit the matched page.
        4. Follow any redirect (pages containing ``リダイレクト``).
        5. Cache and return the target page's title.
        """
        if not name:
            return name

        if name in self.cache:
            return self.cache[name]

        try:
            results = self.search_wiki(name, search_target="page_name")
        except Exception:
            return name
        if not results:
            self.cache[name] = name
            return name

        title, url = results[0]
        if not url:
            self.cache[name] = name
            return name

        try:
            canonical = self.resolve_page_name(url)
        except Exception:
            return name
        result = canonical or name
        self.cache[name] = result
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def fetch_page(self, url):
        """GET *url* and return a ``BeautifulSoup`` parsed with EUC-JP."""
        resp = requests.get(url)
        resp.encoding = "euc-jp"
        return BeautifulSoup(resp.text, "html.parser")

    def search_wiki(self, keywords, search_target="all"):
        """Search seesaawiki and return ``[(title, url), ...]``."""
        try:
            encoded_kw = keywords.encode("euc-jp")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return []

        params = urllib.urlencode({
            "search_type": "2",
            "search_target": search_target,
            "keywords": encoded_kw,
            "x": "0",
            "y": "0",
        })
        soup = self.fetch_page(SEARCH_URL + "?" + params)

        result_box = soup.find("div", class_="result-box")
        if not result_box:
            return []

        results = []
        for body in result_box.find_all("div", class_="body"):
            h3 = body.find("h3", class_="keyword")
            if not h3:
                continue
            a = h3.find("a")
            if a:
                results.append((a.get_text(), a.get("href", "")))
        return results

    def resolve_page_name(self, url, depth=0):
        """Visit *url*, follow one redirect if present, return the page name."""
        if depth > 3:
            return None

        soup = self.fetch_page(url)
        user_area = soup.find("div", class_="user-area")

        if user_area:
            text = user_area.get_text()
            # Japanese text for "redirect": リダイレクト
            if u"\u30ea\u30c0\u30a4\u30ec\u30af\u30c8" in text:
                for link in user_area.find_all("a"):
                    href = link.get("href", "")
                    if "/d/" in href:
                        return self.resolve_page_name(href, depth + 1)

        return self.extract_page_name(soup)

    @staticmethod
    def extract_page_name(soup):
        """Return the wiki page name from the ``<div class="title">`` or ``<title>``."""
        title_div = soup.find("div", class_="title")
        if title_div:
            text = title_div.get_text().strip()
            if text:
                return text

        title_tag = soup.find("title")
        if title_tag:
            # Format: "ページ名 - 素人系総合 wiki"
            raw = title_tag.get_text()
            if " - " in raw:
                return raw.split(" - ", 1)[0].strip()
            return raw.strip()

        return None

    @staticmethod
    def find_actresses_in_table(soup, video_code):
        """Find actress names from a ``<table>`` whose row contains *video_code*.

        Series / label pages use a structured table with columns like
        NO, PHOTO, TITLE, ACTRESS, RELEASE, NOTE.  We look for the
        ACTRESS header and extract names from the matching row.
        """
        user_area = soup.find("div", class_="user-area")
        if not user_area:
            return []

        vc_upper = video_code.upper()

        for table in user_area.find_all("table"):
            thead = table.find("thead")
            if not thead:
                continue
            headers = [th.get_text().strip().upper()
                       for th in thead.find_all("th")]
            try:
                actress_idx = headers.index("ACTRESS")
            except ValueError:
                continue

            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue
                # The first cell typically holds the unique ID text / link.
                first_cell_text = cells[0].get_text().strip().upper()
                if vc_upper not in first_cell_text:
                    continue
                if actress_idx >= len(cells):
                    continue
                actress_cell = cells[actress_idx]
                names = [
                    a.get_text().strip()
                    for a in actress_cell.find_all("a")
                    if a.get_text().strip()
                ]
                if not names:
                    raw = actress_cell.get_text().strip()
                    if raw:
                        names = [raw]
                return names

        return []

    @staticmethod
    def has_filmography_entry(soup, video_code):
        """Return ``True`` if the page has a filmography line for *video_code*.

        Actress pages list entries as ``YYYY/MM/DD VIDEO-CODE`` on their own
        line.  This distinguishes genuine filmography mentions from passing
        references like range text ``SSIS-001〞SSIS-200``.
        """
        user_area = soup.find("div", class_="user-area")
        if not user_area:
            return False
        text = user_area.get_text()
        pattern = r"\d{4}/\d{2}/\d{2}\s+" + re.escape(video_code) + r"\b"
        return bool(re.search(pattern, text, re.IGNORECASE))
