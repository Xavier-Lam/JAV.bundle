# coding=utf-8

import datetime
import re

import requests

from .base import QueryAgent, StudioAgent


class Pondo(StudioAgent, QueryAgent):
    def get_name(self):
        return "1Pondo"

    def guess_keywords(self, name):
        if "一本道" in name or "1pon" in name.lower():
            match = re.search(r"(\d{6})[-_](\d{3})", name)
            if match:
                return [match.group(1) + "_" + match.group(2)]
        return []

    def is_studio(self, name):
        return name.lower() in ["一本道", "1pondo"]

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
            "title_sort": self.get_title_sort(movie_id, data),
            "originally_available_at": self.get_originally_available_at(data),
            "roles": self.get_roles(data),
            "studio": self.get_studio(),
            "duration": self.get_duration(data),
            "genres": self.get_genres(data),
            "rating": self.get_rating(data),
            "collections": self.get_collections(data),
            "summary": self.get_summary(data),
            "posters": self.get_posters(movie_id, data),
            "art": self.get_thumbs(movie_id)
        }

    def get_original_title(self, movie_id, data):
        title = data["Title"]
        return "{0} {1} {2} {3}".format(
            self.get_studio(),
            movie_id,
            title,
            " ".join([role["name"] for role in self.get_roles(data)])
        )

    def get_title_sort(self, movie_id, data):
        match = re.match(r"(\d{2})(\d{2})(\d{2})_(\d+)$", movie_id)
        return "{0} {1}".format(
            self.get_studio(),
            "{0}{1}{2}-{3}".format(match.group(3), match.group(1),
                                   match.group(2), match.group(4))
        )

    def get_studio(self):
        return "一本道"

    def get_collections(self, data):
        rv = [self.get_studio()]
        if data["Series"]:
            rv.append(data["Series"])
        return rv

    def get_originally_available_at(self, data):
        return datetime.datetime.strptime(data["Release"], "%Y-%m-%d")

    def get_duration(self, data):
        return data["Duration"]*1000

    def get_roles(self, data):
        return [{"name": role} for role in data["ActressesJa"]]

    def get_genres(self, data):
        return data["UCNAME"]

    def get_rating(self, data):
        return float(data["AvgRating"]*2)

    def get_summary(self, data):
        return data["Desc"]

    def get_thumbs(self, movie_id):
        return [
            "https://www.1pondo.tv/assets/sample/{0}/str.jpg".format(movie_id)
        ]

    def get_posters(self, movie_id, data):
        poster = data.get("MovieThumb")
        return [poster] if poster else self.get_thumbs(movie_id)

    def crawl(self, movie_id):
        url = "https://www.1pondo.tv/dyn/phpauto/movie_details/movie_id/{0}.json".format(
            movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
