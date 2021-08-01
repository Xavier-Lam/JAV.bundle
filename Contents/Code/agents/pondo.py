# coding=utf-8

import datetime
import os
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class Pondo(Base):
    name = "1Pondo"

    def get_results(self, media):
        movie_id = self.get_id(media)
        data = self.crawl(media)
        originally_available_at = self.get_originally_available_at(media, data)
        return [{
            "id": movie_id,
            "name": self.get_title(media, data),
            "year": originally_available_at and originally_available_at.year,
            "lang": self.lang,
            "score": 100,
            "thumb": self.get_thumbs(media, None)[0]
        }]

    def get_id_by_name(self, name):
        if "一本道" in name or "1pon" in name.lower():
            match = re.search(r"(\d{6})[-_](\d{3})", name)
            if match:
                return match.group(1) + "_" + match.group(2)

    def get_title_sort(self, media, data):
        movie_id = self.get_id(media)
        match = re.match(r"(\d{2})(\d{2})(\d{2})_(\d+)$", movie_id)
        return "{0} {1}".format(
            self.get_studio(media, data),
            "{0}{1}{2}-{3}".format(match.group(3), match.group(1),
                                   match.group(2), match.group(4))
        )

    def get_studio(self, media, data):
        return "一本道"

    def crawl(self, media):
        movie_id = self.get_id(media)
        url = "https://www.1pondo.tv/dyn/phpauto/movie_details/movie_id/{0}.json".format(movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_original_title(self, media, data):
        title = data["Title"]
        return "{0} {1} {2} {3}".format(
            self.get_studio(media, data),
            self.get_id(media),
            title,
            " ".join(self.get_roles(media, data))
        )

    def get_originally_available_at(self, media, data):
        return datetime.datetime.strptime(data["Release"], "%Y-%m-%d")

    def get_duration(self, media, data):
        return data["Duration"]*1000

    def get_roles(self, media, data):
        return data["ActressesJa"]

    def get_genres(self, media, data):
        return data["UCNAME"]

    def get_rating(self, media, data):
        return float(data["AvgRating"]*2)

    def get_summary(self, media, data):
        return data["Desc"]

    def get_thumbs(self, media, data):
        movie_id = self.get_id(media)
        return [
            "https://www.1pondo.tv/assets/sample/{0}/str.jpg".format(movie_id)
        ]
        
    def get_posters(self, media, data):
        poster = data.get("MovieThumb")
        return [poster] if poster else self.get_thumbs(self, media, data)

    def get_collections(self, media, data):
        rv = [self.get_studio(media, data)]
        if data["Series"]:
            rv.append(data["Series"])
        return rv
