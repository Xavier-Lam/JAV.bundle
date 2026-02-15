# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import QueryAgent, StudioAgent


class Caribbean(StudioAgent, QueryAgent):
    def get_name(self):
        return "Caribbean"

    def guess_keywords(self, name):
        if "カリビ" in name or "carib" in name.lower():
            match = re.search(r"(\d{6})[-_](\d{3})", name)
            if match:
                return [match.group(1) + "-" + match.group(2)]
        return []

    def is_studio(self, name):
        return name.lower() in ["カリビ", "carib", "caribbean"]

    def query(self, keyword):
        data = self.crawl(keyword)
        originally_available_at = self.get_originally_available_at(data)
        thumbs = self.get_thumbs(keyword)
        return [self.make_result(
            keyword,
            self.get_original_title(keyword, data),
            year=originally_available_at and originally_available_at.year,
            thumb=thumbs and thumbs[0]
        )]

    def get_metadata(self, metadata_id):
        movie_id = self.get_agent_id(metadata_id)
        data = self.crawl(movie_id)

        title = self.get_original_title(movie_id, data)
        if not title:
            raise Exception(
                "Got an unexpected response for {0}".format(metadata_id))

        available_at = self.get_originally_available_at(data)
        if not available_at:
            available_at = datetime.datetime.strptime(movie_id[:6], "%m%d%y")

        return {
            "movie_id": movie_id,
            "agent_id": movie_id,
            "title": title,
            "title_sort": self.get_title_sort(movie_id),
            "originally_available_at": available_at,
            "roles": self.get_roles(data),
            "studio": self.get_studio(),
            "duration": self.get_duration(data),
            "genres": self.get_genres(data),
            "rating": self.get_rating(data),
            "collections": self.get_collections(data),
            "summary": self.get_summary(data),
            "posters": self.get_posters(movie_id),
            "art": self.get_thumbs(movie_id)
        }

    def get_original_title(self, movie_id, data):
        title = data.find("h1", {"itemprop": "name"}).text.strip()
        return "{0} {1} {2} {3}".format(
            self.get_studio(),
            movie_id,
            title,
            " ".join([role["name"] for role in self.get_roles(data)])
        )

    def get_title_sort(self, movie_id):
        match = re.match(r"(\d{2})(\d{2})(\d{2})-(\d+)$", movie_id)
        return "{0} {1}".format(
            self.get_studio(),
            "{0}{1}{2}-{3}".format(match.group(3), match.group(1),
                                   match.group(2), match.group(4))
        )

    def get_studio(self):
        return "カリビアンコム"

    def get_collections(self, data):
        rv = [self.get_studio()]
        ele = self.find_ele(data, "シリーズ")
        if ele:
            rv.append(ele.find("a").text.strip())
        return rv

    def get_originally_available_at(self, data):
        ele = self.find_ele(data, "配信日")
        if ele:
            dt_str = ele.text.strip()
            return datetime.datetime.strptime(dt_str, "%Y/%m/%d")

    def get_duration(self, data):
        ele = data.find("span", {"itemprop": "duration"})
        if ele:
            dt = datetime.datetime.strptime(ele.text.strip(), "%H:%M:%S")
            diff = dt - datetime.datetime(1900, 1, 1)
            return int(diff.total_seconds())*1000

    def get_roles(self, data):
        ele = self.find_ele(data, "出演")
        if ele:
            return [
                {"name": item.find(
                    "span", {"itemprop": "name"}).text.strip("()")}
                for item in ele.findAll("a", {"itemprop": "actor"})
            ]
        return []

    def get_genres(self, data):
        ele = self.find_ele(data, "タグ")
        if ele:
            return [
                item.text.strip()
                for item in ele.findAll("a", "spec-item")
            ]

    def get_rating(self, data):
        ele = self.find_ele(data, "ユーザー評価")
        if ele:
            return float(len(ele.text.strip())*2)

    def get_summary(self, data):
        ele = data.find("p", {"itemprop": "description"})
        if ele:
            return ele.text.strip()

    def base_url(self):
        return "https://www.caribbeancom.com"

    def get_thumbs(self, movie_id):
        return [
            "{0}/moviepages/{1}/images/l_l.jpg".format(
                self.base_url(),
                movie_id)
        ]

    def get_posters(self, movie_id):
        urls = self.get_thumbs(movie_id) + [
            "{0}/moviepages/{1}/images/jacket.jpg".format(
                self.base_url(),
                movie_id)
        ]
        return [url for url in urls if requests.head(url).status_code != 404]

    def crawl(self, movie_id):
        url = "{0}/moviepages/{1}/index.html".format(
            self.base_url(),
            movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("euc-jp", errors="ignore")
        return BeautifulSoup(html, "html.parser")

    def find_ele(self, data, title):
        for li in data.findAll("li", "movie-spec"):
            if li.find("span", "spec-title").text.strip() == title:
                return li.find("span", "spec-content")
