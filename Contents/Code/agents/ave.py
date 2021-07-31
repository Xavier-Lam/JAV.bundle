# coding=utf-8

import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class AVE(Base):
    name = "AVEntertainments"

    def get_results(self, media, lang):
        rv = []
        movie_id = self.get_local_id(media)
        if movie_id:
            if movie_id.lower().startswith("red-"):
                movie_id = movie_id.lower().replace("red-", "red")
            rv.extend(self.get_results_by_keyword(movie_id, lang))
        else:
            vol_ids = self.get_volumn_id(media)
            if vol_ids:
                for vol_id in vol_ids:
                    rv.extend(self.get_results_by_keyword(vol_id, lang))
        rv.extend(self.get_results_by_keyword(media.name, lang))
        return rv

    def get_results_by_keyword(self, keyword, lang):
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
            rv.append({
                "id": self.name + "." + match.group(1),
                "name": title_ele.text.strip(),
                "lang": lang,
                "score": 100,
                "thumb": product.find("div", "single-slider-product__image").find("img")["src"]
            })
        return rv

    def is_match(self, media):
        return bool(self.get_local_id(media) or self.get_volumn_id(media))

    def get_id(self, media, data=None, lang=None):
        if data:
            return self.find_ele(data, "商品番号").text.strip()
        return self.get_local_id(media)

    def get_local_id(self, media):
        pattern = r"(?:^|\s|\[|\(|\.|\\|\/)([a-z\d]+[-][a-z\d]+)(?:$|\s|\]|\)|\.)"
        if hasattr(media, "name"):
            match = re.search(pattern, media.name, re.I)
            if match:
                return match.group(1)
        filename = media.items[0].parts[0].file.lower()
        match = re.search(pattern, filename)
        if match:
            return match.group(1)

    def get_volumn_id(self, media):
        filename = media.items[0].parts[0].file.lower()
        pattern = r"vol\s*\.?\s*(\d+)"
        match = re.search(pattern, filename)
        rv = []
        if match:
            vol = int(match.group(1))
            rv.append("Vol." + str(vol))
            if vol < 100:
                rv.append("Vol.0" + str(vol))
        return rv

    def get_title_sort(self, media, data, lang):
        return self.get_title(media, data, lang)

    def get_studio(self, media, data, lang):
        return self.find_ele(data, "スタジオ").text.strip()

    def crawl(self, media, lang):
        url = "https://www.aventertainments.com/product_lists.aspx"
        resp = requests.get(url, params={
            "product_id": media.metadata_id.split(".")[1],
            "languageID": 2,
            "dept_id": "29"
        })
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def get_original_title(self, media, data, lang):
        return "[{0}] {1}".format(
            self.get_id(media, data, lang),
            data.find("div", "section-title").find("h3").text.strip()
        )

    def get_originally_available_at(self, media, data, lang):
        ele = self.find_ele(data, "発売日")
        if ele:
            dt_str = ele.text.strip()
            match = re.search("\d+/\d+/\d+", dt_str)
            try:
                if match:
                    return datetime.datetime.strptime(match.group(0), "%m/%d/%Y")
            except ValueError:
                pass

    def get_roles(self, media, data, lang):
        ele = self.find_ele(data, "主演女優")
        if ele:
            return [
                item.text.strip()
                for item in ele.findAll("a")
            ]
        return []

    def get_duration(self, media, data, lang):
        ele = self.find_ele(data, "収録時間")
        if ele:
            match = re.search("\d+", ele.text)
            if match:
                return int(match.group(0))*60*1000

    def get_collections(self, media, data, lang):
        rv = []
        studio = self.get_studio(media, data, lang)
        if studio:
            rv.append(studio)
        series = self.find_ele(data, "シリーズ")
        if series:
            rv.append(series.text.strip())        
        return rv

    def get_genres(self, media, data, lang):
        ele = self.find_ele(data, "カテゴリ")
        if ele:
            return [ele.text.strip() for ele in ele.findAll("a")]
        return []

    def get_summary(self, media, data, lang):
        ele = data.find("div", "product-description")
        if ele:
            return ele.text.strip()
        
    def get_posters(self, media, data, lang):
        thumbs = self.get_thumbs(media, data, lang)
        return [
            thumb.replace("bigcover", "jacket_images")
            for thumb in thumbs
        ]

    def get_thumbs(self, media, data, lang):
        ele = data.find("div", {"id": "PlayerCover"})
        if ele:
            return [
                ele.find("img")["src"]
            ]
        return []

    def find_ele(self, data, title):
        single_infos = data.findAll("div", "single-info")
        for single_info in single_infos:
            if single_info.find("span", "title").text.strip() == title:
                return single_info.find("span", "title").findNext("span")
