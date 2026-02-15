# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import QueryAgent, StudioAgent


class Heyzo(StudioAgent, QueryAgent):
    def get_name(self):
        return "Heyzo"

    def guess_keywords(self, name):
        if "heyzo" in name.lower():
            match = re.search(r"\s+(\d{4})(?:\s+|$)", name)
            if match:
                return [match.group(1)]
        return []

    def is_studio(self, name):
        return name.lower() == "heyzo"

    def query(self, keyword):
        data = self.crawl(keyword)
        originally_available_at = self.get_originally_available_at(data)
        return [self.make_result(
            keyword,
            self.get_original_title(keyword, data),
            year=originally_available_at and originally_available_at.year,
            thumb=self.get_thumbs(keyword)[0]
        )]

    def get_metadata(self, metadata_id):
        movie_id = self.get_agent_id(metadata_id)
        data = self.crawl(movie_id)

        title = self.get_original_title(movie_id, data)
        if not title:
            raise Exception(
                "Got an unexpected response for {0}".format(metadata_id))

        return {
            "movie_id": movie_id,
            "agent_id": movie_id,
            "title": title,
            "title_sort": self.get_title_sort(movie_id),
            "originally_available_at": self.get_originally_available_at(data),
            "roles": self.get_roles(data),
            "studio": self.get_studio(),
            "genres": self.get_genres(data),
            "rating": self.get_rating(data),
            "collections": self.get_collections(data),
            "summary": self.get_summary(data),
            "posters": self.get_posters(movie_id),
            "art": self.get_thumbs(movie_id)
        }

    def get_original_title(self, movie_id, data):
        title_text = data.find("div", {"id": "movie"}).find("h1").text
        title_cleaned = re.sub(r'\s+', ' ', title_text).strip()
        return u"{0} {1} {2}".format(
            self.get_studio(),
            movie_id,
            title_cleaned
        )

    def get_title_sort(self, movie_id):
        return "{0} {1}".format(
            self.get_studio(),
            movie_id
        )

    def get_studio(self):
        return "Heyzo"

    def get_originally_available_at(self, data):
        ele = self.find_ele(data, "table-release-day")
        if ele:
            dt_str = ele.text.strip()
            try:
                return datetime.datetime.strptime(dt_str, "%Y-%m-%d")
            except ValueError:
                pass

    def get_roles(self, data):
        ele = self.find_ele(data, "table-actor")
        if ele:
            return [
                {"name": item.text.strip()}
                for item in ele.findAll("span")
            ]
        return []

    def get_collections(self, data):
        rv = [self.get_studio()]
        ele = self.find_ele(data, "table-series")
        if ele and ele.find("a"):
            rv.append(ele.find("a").text.strip())
        return rv

    def get_genres(self, data):
        ele = data.find("ul", "tag-keyword-list")
        if ele:
            return [
                item.text.strip()
                for item in ele.findAll("a")
            ]
        else:
            return []

    def get_rating(self, data):
        ele = self.find_ele(data, "table-estimate")
        if ele:
            return float(ele.find("span", {"itemprop": "ratingValue"}).text.strip())*2

    def get_summary(self, data):
        ele = data.find("tr", "table-memo")
        if ele:
            return ele.find("p", "memo").text.strip()

    def get_posters(self, movie_id):
        return [
            "https://www.heyzo.com/contents/3000/{0}/images/thumbnail.jpg".format(
                movie_id)
        ]

    def get_thumbs(self, movie_id):
        return [
            "https://www.heyzo.com/contents/3000/{0}/images/player_thumbnail.jpg".format(
                movie_id)
        ]

    def crawl(self, movie_id):
        url = "https://www.heyzo.com/moviepages/{0}/index.html".format(
            movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def find_ele(self, data, cls):
        return data.find("tr", cls).findAll("td")[1]
