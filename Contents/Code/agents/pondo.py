# coding=utf-8

import datetime
import os
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class Pondo(Base):
    name = "1Pondo"

    def get_results(self, media, lang):
        movie_id = self.get_id(media)
        data = self.crawl(media, lang)
        originally_available_at = self.get_originally_available_at(media, data, lang)
        return [{
            "id": movie_id,
            "name": self.get_title(media, data, lang),
            "year": originally_available_at and originally_available_at.year,
            "lang": lang,
            "score": 100,
            "thumb": self.get_thumbs(media, None, lang)[0]
        }]

    def get_id(self, media):
        filename = media.items[0].parts[0].file.lower()
        if "一本道" in filename or "1pon" in filename:
            name = self.get_filename(media)
            dirname = self.get_dirname(media)
            match = re.search(r"(\d{6})[-_](\d{3})",
                              os.path.join(dirname, name))
            if match:
                return match.group(1) + "_" + match.group(2)

    def get_title_sort(self, media, data, lang):
        movie_id = self.get_id(media)
        match = re.match(r"(\d{2})(\d{2})(\d{2})_(\d+)$", movie_id)
        return "{0} {1}".format(
            self.get_studio(media, data, lang),
            "{0}{1}{2}-{3}".format(match.group(3), match.group(1),
                                   match.group(2), match.group(4))
        )

    def get_studio(self, media, data, lang):
        return "一本道"

    def crawl(self, media, lang):
        movie_id = self.get_id(media)
        url = "https://www.1pondo.tv/dyn/phpauto/movie_details/movie_id/{0}.json".format(movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_original_title(self, media, data, lang):
        title = data["Title"]
        return "{0} {1} {2} {3}".format(
            self.get_studio(media, data, lang),
            self.get_id(media),
            title,
            " ".join(self.get_roles(media, data, lang))
        )

    def get_originally_available_at(self, media, data, lang):
        return datetime.datetime.strptime(data["Release"], "%Y-%m-%d")

    def get_duration(self, media, data, lang):
        return data["Duration"]*1000

    def get_roles(self, media, data, lang):
        return data["ActressesJa"]

    def get_genres(self, media, data, lang):
        return data["UCNAME"]

    def get_rating(self, media, data, lang):
        return float(data["AvgRating"]*2)

    def get_summary(self, media, data, lang):
        return data["Desc"]

    def get_thumbs(self, media, data, lang):
        movie_id = self.get_id(media)
        return [
            "https://www.1pondo.tv/assets/sample/{0}/str.jpg".format(movie_id)
        ]
        
    def get_posters(self, media, data, lang):
        poster = data.get("MovieThumb")
        return [poster] if poster else self.get_thumbs(self, media, data, lang)

    def get_collections(self, media, data, lang):
        rv = [self.get_studio(media, data, lang)]
        if data["Series"]:
            rv.append(data["Series"])
        return rv
