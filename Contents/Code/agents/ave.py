# coding=utf-8

import datetime
from difflib import SequenceMatcher
import re

from bs4 import BeautifulSoup
import requests

from .base import ID_PATTERN, LibraryAgent


class AVE(LibraryAgent):
    def get_name(self):
        return "AVEntertainments"

    def guess_keywords(self, name):
        name = name.lower()

        match = re.search(ID_PATTERN, name)
        if match:
            movie_id = match.group(1)
            # fix match for red hot
            if movie_id.startswith("red-"):
                movie_id = movie_id.replace("red-", "red")
            return [movie_id]

        # Search for 'Vol.' like names
        pattern = r"vol\s*\.?\s*(\d+)"
        match = re.search(pattern, name)
        if match:
            rv = []
            vol = int(match.group(1))
            rv.append("Vol." + str(vol))
            if vol < 100:
                rv.append("Vol.0" + str(vol))
            return rv

        return []

    def query(self, keyword):
        url = "https://www.aventertainments.com/search_Products.aspx"
        params = {
            "languageId": "2",
            "dept_id": "29",
            "keyword": keyword,
            "searchby": "keyword"
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        wrap = soup.find("div", "shop-product-wrap")
        products = wrap.findAll("div", "grid-view-product")
        rv = []
        for product in products:
            title_ele = product.find("p", "product-title").find("a")
            url = title_ele["href"]
            match = re.search("product_id=(\d+)", url)
            title = title_ele.text.strip()

            if re.search(ID_PATTERN, keyword):
                score = 100
            else:
                # A blur search
                score = int(SequenceMatcher(None, keyword, title).ratio()*100)

            rv.append(self.make_result(
                match.group(1),
                title,
                thumb=product.find(
                    "div", "single-slider-product__image").find("img")["src"],
                score=score
            ))
        return rv

    def get_metadata(self, metadata_id):
        agent_id = self.get_agent_id(metadata_id)
        data = self.crawl(agent_id)

        title = self.get_original_title(data)
        if not title:
            raise Exception(
                "Got an unexpected response for {0}".format(metadata_id))

        return {
            "movie_id": self.get_id(data),
            "agent_id": agent_id,
            "title": title,
            "originally_available_at": self.get_originally_available_at(data),
            "roles": self.get_roles(data),
            "studio": self.get_studio(data),
            "duration": self.get_duration(data),
            "genres": self.get_genres(data),
            "collections": self.get_collections(data),
            "summary": self.get_summary(data),
            "posters": self.get_posters(data),
            "art": self.get_thumbs(data)
        }

    def get_id(self, data):
        return self.find_ele(data, "商品番号").text.strip()

    def get_studio(self, data):
        return self.find_ele(data, "スタジオ").text.strip()

    def get_original_title(self, data):
        return "[{0}] {1}".format(
            self.get_id(data),
            data.find("div", "section-title").find("h3").text.strip()
        )

    def get_originally_available_at(self, data):
        ele = self.find_ele(data, "発売日")
        if ele:
            dt_str = ele.text.strip()
            match = re.search("\d+/\d+/\d+", dt_str)
            try:
                if match:
                    return datetime.datetime.strptime(match.group(0), "%m/%d/%Y")
            except ValueError:
                pass

    def get_roles(self, data):
        ele = self.find_ele(data, "主演女優")
        if ele:
            return [
                {"name": item.text.strip()}
                for item in ele.findAll("a")
            ]
        return []

    def get_duration(self, data):
        ele = self.find_ele(data, "収録時間")
        if ele:
            match = re.search("\d+", ele.text)
            if match:
                return int(match.group(0))*60*1000

    def get_collections(self, data):
        rv = []
        studio = self.get_studio(data)
        if studio:
            rv.append(studio)
        series = self.find_ele(data, "シリーズ")
        if series:
            rv.append(series.text.strip())
        return rv

    def get_genres(self, data):
        ele = self.find_ele(data, "カテゴリ")
        if ele:
            return [ele.text.strip() for ele in ele.findAll("a")]
        return []

    def get_summary(self, data):
        ele = data.find("div", "product-description")
        if ele:
            return ele.text.strip()

    def get_posters(self, data):
        thumbs = self.get_thumbs(data)
        return [
            thumb.replace("bigcover", "jacket_images")
            for thumb in thumbs
        ]

    def get_thumbs(self, data):
        ele = data.find("div", {"id": "PlayerCover"})
        if ele:
            return [
                ele.find("img")["src"]
            ]
        return []

    def crawl(self, agent_id):
        url = "https://www.aventertainments.com/product_lists.aspx"
        resp = requests.get(url, params={
            "product_id": agent_id,
            "languageID": 2,
            "dept_id": "29"
        })
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def find_ele(self, data, title):
        single_infos = data.findAll("div", "single-info")
        for single_info in single_infos:
            if single_info.find("span", "title").text.strip() == title:
                return single_info.find("span", "title").findNext("span")
