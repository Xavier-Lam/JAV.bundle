# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class Caribbean(Base):
    name = "Caribbean"

    def get_results(self, media):
        movie_id = self.get_id(media)
        data = self.crawl(media)
        originally_available_at = self.get_originally_available_at(media, data)
        thumbs = self.get_thumbs(media, None)
        return [{
            "id": movie_id,
            "name": self.get_title(media, data),
            "year": originally_available_at and originally_available_at.year,
            "lang": self.lang,
            "score": 100,
            "thumb": thumbs and thumbs[0]
        }]

    def get_id_by_name(self, name):
        if "カリビ" in name or "carib" in name.lower():
            match = re.search(r"(\d{6})[-_](\d{3})", name)
            if match:
                return match.group(1) + "-" + match.group(2)

    def get_title_sort(self, media, data):
        movie_id = self.get_id(media)
        match = re.match(r"(\d{2})(\d{2})(\d{2})-(\d+)$", movie_id)
        return "{0} {1}".format(
            self.get_studio(media, data),
            "{0}{1}{2}-{3}".format(match.group(3), match.group(1),
                                   match.group(2), match.group(4))
        )

    def get_studio(self, media, data):
        return "カリビアンコム"

    def get_collections(self, media, data):
        return [self.get_studio(media, data)]

    def crawl(self, media):
        movie_id = self.get_id(media)
        url = "https://www.caribbeancom.com/moviepages/{0}/index.html".format(movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("euc-jp", errors="ignore")
        return BeautifulSoup(html, "html.parser")

    def get_original_title(self, media, data):
        title = data.find("h1", {"itemprop": "name"}).text.strip()
        return "{0} {1} {2} {3}".format(
            self.get_studio(media, data),
            self.get_id(media),
            title,
            " ".join(self.get_roles(media, data))
        )

    def get_originally_available_at(self, media, data):
        ele = self.find_ele(data, "配信日")
        if ele:
            dt_str = ele.text.strip()
            return datetime.datetime.strptime(dt_str, "%Y/%m/%d")

    def get_duration(self, media, data):
        ele = data.find("span", {"itemprop": "duration"})
        if ele:
            dt = datetime.datetime.strptime(ele.text.strip(), "%H:%M:%S")
            diff = dt - datetime.datetime(1900, 1, 1)
            return int(diff.total_seconds())*1000

    def get_roles(self, media, data):
        ele = self.find_ele(data, "出演")
        if ele:
            return [
                item.find("span", {"itemprop": "name"}).text.strip("()")
                for item in ele.findAll("a", {"itemprop": "actor"})
            ]
        return []

    def get_genres(self, media, data):
        ele = self.find_ele(data, "タグ")
        if ele:
            return [
                item.text.strip()
                for item in ele.findAll("a", "spec-item")
            ]

    def get_rating(self, media, data):
        ele = self.find_ele(data, "ユーザー評価")
        if ele:
            return float(len(ele.text.strip())*2)

    def get_summary(self, media, data):
        ele = data.find("p", {"itemprop": "description"})
        if ele:
            return ele.text.strip()

    def get_thumbs(self, media, data):
        movie_id = self.get_id(media)
        return [
            "https://www.caribbeancom.com/moviepages/{0}/images/l_l.jpg".format(movie_id)
        ]
        
    def get_posters(self, media, data):
        movie_id = self.get_id(media)
        urls = self.get_thumbs(media, data) + [
            "https://www.caribbeancom.com/moviepages/{0}/images/jacket.jpg".format(movie_id)
        ]
        return [url for url in urls if requests.head(url).status_code != 404]

    def find_ele(self, data, title):
        for li in data.findAll("li", "movie-spec"):
            if li.find("span", "spec-title").text.strip() == title:
                return li.find("span", "spec-content")

    def get_collections(self, media, data):
        rv = super(Caribbean, self).get_collections(media, data)
        ele = self.find_ele(data, "シリーズ")
        if ele:
            rv.append(ele.find("a").text.strip())
        return rv
