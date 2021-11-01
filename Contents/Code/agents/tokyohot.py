# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class TokyoHot(Base):
    name = "TokyoHot"

    @property
    def session(self):
        if not hasattr(self, "_session"):
            session = requests.session()
            session.get("https://my.tokyo-hot.com/index?lang=ja")
            setattr(self, "_session", session)
        return getattr(self, "_session")

    def get_results(self, media):
        rv = []
        movie_id = self.get_id(media, None)
        if movie_id:
            rv.extend(self.get_results_by_keyword(movie_id))
        else:
            rv.extend(self.get_results_by_keyword(media.name))
        return rv

    def get_results_by_keyword(self, keyword):
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
            rv.append({
                "id": self.name + "." + match.group(1),
                "name": title_ele.text.strip(),
                "lang": self.lang,
                "score": 100,
                "thumb": product.find("img")["src"]
            })
        return rv

    def get_id_by_name(self, name):
        name = name.lower()
        if "tokyo" in name and "hot" in name:
            match = re.search(r"(?:k|n)\d{4}", name)
            if match:
                return match.group(0)

    def get_title_sort(self, media, data):
        return self.get_title(media, data)

    def get_studio(self, media, data):
        studios = self.find_ele(data, "レーベル")
        if studios:
            eles = studios.findAll("a")
            if eles:
                return eles[0].text.strip()
        return "Tokyo-Hot"

    def crawl(self, media):
        url = "https://my.tokyo-hot.com/product/{0}/"
        resp = self.session.get(url.format(media.metadata_id.split(".")[1]))
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def get_original_title(self, media, data):
        return "{0} {1} {2}".format(
            self.get_studio(media, data),
            self.get_id(media, data),
            data.find("div", {"id": "main"}).find("h2").text.strip()
        )

    def get_originally_available_at(self, media, data):
        ele = self.find_ele(data, "配信開始日")
        if ele:
            dt_str = ele.text.strip()
            match = re.search("\d+/\d+/\d+", dt_str)
            try:
                if match:
                    return datetime.datetime.strptime(match.group(0), "%Y/%m/%d")
            except ValueError:
                pass

    def get_roles(self, media, data):
        ele = self.find_ele(data, "出演者")
        if ele:
            return [
                item.text.strip()
                for item in ele.findAll("a")
            ]
        return []

    def get_duration(self, media, data):
        ele = self.find_ele(data, "収録時間")
        if ele:
            dt = datetime.datetime.strptime(ele.text.strip(), "%H:%M:%S")
            diff = dt - datetime.datetime(1900, 1, 1)
            return int(diff.total_seconds())*1000

    def get_collections(self, media, data):
        studios = self.find_ele(data, "レーベル")
        if studios:
            return [studio.text.strip() for studio in studios.findAll("a")] 
        return [self.get_studio(media, data)]

    def get_genres(self, media, data):
        rv = []
        ele = self.find_ele(data, "タグ")
        if ele:
            rv.extend([ele.text.strip() for ele in ele.findAll("a")])
        ele = self.find_ele(data, "シリーズ")
        if ele:
            rv.extend([ele.text.strip() for ele in ele.findAll("a")])
        return rv

    def get_summary(self, media, data):
        ele = data.find("div", {"id": "main"}).find("div", "sentence")
        if ele:
            return ele.text.strip()
        
    def get_posters(self, media, data):
        return [
            "https://my.cdn.tokyo-hot.com/media/{0}/package/_v.jpg".format(
                media.metadata_id.split(".")[1]
            )
        ]

    def get_thumbs(self, media, data):
        return [
            "https://my.cdn.tokyo-hot.com/media/{0}/jacket/{1}.jpg".format(
                media.metadata_id.split(".")[1],
                self.get_id(media)
            )
        ]

    def find_ele(self, data, title):
        single_infos = data.find("div", {"id": "main"})\
                           .find("dl", "info")\
                           .findAll("dt")
        for single_info in single_infos:
            if single_info.text.strip() == title:
                return single_info.findNext("dd")
