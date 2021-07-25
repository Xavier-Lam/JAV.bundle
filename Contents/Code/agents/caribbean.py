# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class Caribbean(Base):
    def match(self, filename):
        filename = filename.lower()
        if "カリビアンコム" in filename or "carib" in filename:
            match = re.search(r"(\d{6})[-_](\d{3})", filename)
            if match:
                return match.group(1) + "-" + match.group(2)

    def crawl_page(self, movie_id):
        url = "https://www.caribbeancom.com/moviepages/{0}/index.html".format(movie_id)
        resp = requests.get(url)
        html = resp.content.decode("euc-jp", errors="ignore")
        return BeautifulSoup(html, "html.parser")

    def get_title(self, movie_id, html):
        title = html.find("h1", {"itemprop": "name"}).text.strip()
        return "{0} {1} {2} {3}".format(
            self.get_studio(movie_id, html),
            movie_id,
            title,
            " ".join(self.get_roles(movie_id, html))
        )

    def get_title_sort(self, movie_id, html):
        return "{0} {1}".format(
            self.get_studio(movie_id, html),
            movie_id
        )

    def get_originally_available_at(self, movie_id, html):
        for li in html.findAll("li", "movie-spec"):
            if li.find("span", "spec-title").text.strip() == "配信日":
                dt_str = li.find("span", "spec-content").text.strip()
                return datetime.datetime.strptime(dt_str, "%Y/%m/%d")

    def get_roles(self, movie_id, html):
        for li in html.findAll("li", "movie-spec"):
            if li.find("span", "spec-title").text.strip() == "出演":
                return [
                    item.find("span", {"itemprop": "name"}).text.strip()
                    for item in li.findAll("a", {"itemprop": "actor"})
                ]
        return []

    def get_posters(self, movie_id, html):
        return [
            "https://www.caribbeancom.com/moviepages/{0}/images/l_l.jpg".format(movie_id)
        ]

    def get_studio(self, movie_id, html):
        return "カリビアンコム"
