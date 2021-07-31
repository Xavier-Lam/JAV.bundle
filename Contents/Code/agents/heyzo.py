# coding=utf-8

import datetime
import os
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class Heyzo(Base):
    name = "Heyzo"

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
        if "heyzo" in filename:
            name = self.get_filename(media)
            dirname = self.get_dirname(media)
            match = re.search(r"\s+(\d{4})(?:\s+|$)", os.path.join(dirname, name))
            if match:
                return match.group(1)

    def get_title_sort(self, media, data, lang):
        return "{0} {1}".format(
            self.get_studio(media, data, lang),
            self.get_id(media)
        )

    def get_studio(self, media, data, lang):
        return "Heyzo"

    def crawl(self, media, lang):
        movie_id = self.get_id(media)
        url = "https://www.heyzo.com/moviepages/{0}/index.html".format(movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def get_original_title(self, media, data, lang):
        return "{0} {1} {2}".format(
            self.get_studio(media, data, lang),
            self.get_id(media),
            data.find("div", {"id": "movie"}).find("h1").text.strip()
        )

    def get_originally_available_at(self, media, data, lang):
        ele = self.find_ele(data, "table-release-day")
        if ele:
            dt_str = ele.text.strip()
            try:
                return datetime.datetime.strptime(dt_str, "%Y-%m-%d")
            except ValueError:
                pass

    def get_roles(self, media, data, lang):
        ele = self.find_ele(data, "table-actor")
        if ele:
            return [
                item.text.strip()
                for item in ele.findAll("span")
            ]
        return []

    def get_collections(self, media, data, lang):
        rv = [self.get_studio(media, data, lang)]
        ele = self.find_ele(data, "table-series")
        if ele and ele.find("a"):
            rv.append(ele.find("a").text.strip())
        return rv

    def get_genres(self, media, data, lang):
        ele = data.find("ul", "tag-keyword-list")
        return [
            item.text.strip()
            for item in ele.findAll("a")
        ]

    def get_rating(self, media, data, lang):
        ele = self.find_ele(data, "table-estimate")
        if ele:
            return float(ele.find("span", {"itemprop": "ratingValue"}).text.strip())*2

    def get_summary(self, media, data, lang):
        ele = data.find("tr", "table-memo")
        if ele:
            return ele.find("p", "memo").text.strip()
        
    def get_posters(self, media, data, lang):
        movie_id = self.get_id(media)
        return [
            "https://www.heyzo.com/contents/3000/{0}/images/thumbnail.jpg".format(movie_id)
        ]

    def get_thumbs(self, media, data, lang):
        movie_id = self.get_id(media)
        return [
            "https://www.heyzo.com/contents/3000/{0}/images/player_thumbnail.jpg".format(movie_id)
        ]

    def find_ele(self, data, cls):
        return data.find("tr", cls).findAll("td")[1]
