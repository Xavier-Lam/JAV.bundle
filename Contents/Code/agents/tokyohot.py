# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import QueryAgent, StudioAgent


class TokyoHot(StudioAgent, QueryAgent):
    def get_name(self):
        return "TokyoHot"

    def guess_keywords(self, name):
        name = name.lower()
        if "tokyo" in name and "hot" in name:
            match = re.search(r"(?:k|n)\d{4}", name)
            if match:
                return [match.group(0)]
        return []

    def is_studio(self, name):
        return "tokyo" in name and "hot" in name

    def query(self, keyword):
        url = "https://my.tokyo-hot.com/product/"
        params = {
            "q": keyword
        }
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        wrap = soup.find("ul", "list")
        products = wrap.findAll("a")
        rv = []
        for product in products:
            title_ele = product.find("div", "title")
            url = product["href"]
            match = re.match("/product/(\d+)/", url)
            rv.append(self.make_result(
                match.group(1),
                title_ele.text.strip(),
                thumb=product.find("img")["src"]
            ))
        return rv

    def get_metadata(self, metadata_id):
        agent_id = self.get_agent_id(metadata_id)
        data = self.crawl(agent_id)
        movie_id = self.get_movie_id(data)

        title = self.get_original_title(movie_id, data)
        if not title:
            raise Exception(
                "Got an unexpected response for {0}".format(metadata_id))

        return {
            "movie_id": movie_id,
            "agent_id": agent_id,
            "title": title,
            "originally_available_at": self.get_originally_available_at(data),
            "roles": self.get_roles(data),
            "studio": self.get_studio(data),
            "duration": self.get_duration(data),
            "genres": self.get_genres(data),
            "collections": self.get_collections(data),
            "summary": self.get_summary(data),
            "posters": self.get_posters(agent_id),
            "art": self.get_thumbs(agent_id, movie_id)
        }

    def get_movie_id(self, data):
        ele = self.find_ele(data, "作品番号")
        return ele.text.strip()

    def get_original_title(self, movie_id, data):
        return "{0} {1} {2}".format(
            self.get_studio(data),
            movie_id,
            data.find("div", {"id": "main"}).find("h2").text.strip()
        )

    def get_studio(self, data):
        studios = self.find_ele(data, "レーベル")
        if studios:
            eles = studios.findAll("a")
            if eles:
                return eles[0].text.strip()
        return "Tokyo-Hot"

    def get_originally_available_at(self, data):
        ele = self.find_ele(data, "配信開始日")
        if ele:
            dt_str = ele.text.strip()
            match = re.search("\d+/\d+/\d+", dt_str)
            try:
                if match:
                    return datetime.datetime.strptime(match.group(0), "%Y/%m/%d")
            except ValueError:
                pass

    def get_roles(self, data):
        ele = self.find_ele(data, "出演者")
        if ele:
            return [
                {"name": item.text.strip()}
                for item in ele.findAll("a")
            ]
        return []

    def get_duration(self, data):
        ele = self.find_ele(data, "収録時間")
        if ele:
            dt = datetime.datetime.strptime(ele.text.strip(), "%H:%M:%S")
            diff = dt - datetime.datetime(1900, 1, 1)
            return int(diff.total_seconds())*1000

    def get_collections(self, data):
        # studios = self.find_ele(data, "レーベル")
        # if studios:
        #     return [studio.text.strip() for studio in studios.findAll("a")]
        return [self.get_studio(data)]

    def get_genres(self, data):
        rv = []
        ele = self.find_ele(data, "タグ")
        if ele:
            rv.extend([ele.text.strip() for ele in ele.findAll("a")])
        ele = self.find_ele(data, "シリーズ")
        if ele:
            rv.extend([ele.text.strip() for ele in ele.findAll("a")])
        return rv

    def get_summary(self, data):
        ele = data.find("div", {"id": "main"}).find("div", "sentence")
        if ele:
            return ele.text.strip()

    def get_posters(self, agent_id):
        return [
            "https://my.cdn.tokyo-hot.com/media/{0}/package/_v.jpg".format(
                agent_id
            )
        ]

    def get_thumbs(self, agent_id, movie_id):
        return [
            "https://my.cdn.tokyo-hot.com/media/{0}/jacket/{1}.jpg".format(
                agent_id,
                movie_id
            )
        ]

    @property
    def session(self):
        if not hasattr(self, "_session"):
            session = requests.session()
            session.get("https://my.tokyo-hot.com/index?lang=ja")
            setattr(self, "_session", session)
        return getattr(self, "_session")

    def crawl(self, movie_id):
        url = "https://my.tokyo-hot.com/product/{0}/"
        resp = self.session.get(url.format(movie_id))
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def find_ele(self, data, title):
        single_infos = data.find("div", {"id": "main"})\
                           .find("dl", "info")\
                           .findAll("dt")
        for single_info in single_infos:
            if single_info.text.strip() == title:
                return single_info.findNext("dd")
