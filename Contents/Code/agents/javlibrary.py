# coding=utf-8

import cloudscraper
import datetime
import re

from bs4 import BeautifulSoup
import requests

from .base import Base


class JAVLibrary(Base):
    name = "JAVLibrary"

    def get_results(self, media):
        rv = []
        movie_id = self.get_id(media)
        if movie_id:
            rv.extend(self.get_results_by_keyword(movie_id))
        return rv

    def get_results_by_keyword(self, keyword):
        results = []
        url = "https://www.javlibrary.com/ja/vl_searchbyid.php"
        params = {
            "keyword": keyword
        }
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        score = 100
        if soup.find("div", "videos"):
            if soup.find("div", "video"):
                for video in soup.find_all("div", "video"):
                    movie_id = video.find("a")["href"][5:]
                    results.append({
                        "id": self.name + "." + movie_id,
                        "name": video.find("a")["title"],
                        "year": None,
                        "score": score,
                        "lang": self.lang
                    })
                    score = score - 1
        else:
            try:
                movie_id = soup.find("h3", "post-title").find("a")["href"][7:]
            except AttributeError:
                Log("an exception occurred: " + url)
                return
            results.append({
                "id": self.name + "." + movie_id,
                "name": soup.find("div", {"id": "video_title"}).find("a").text.strip(),
                "year": None,
                "score": score,
                "lang": self.lang
            })
        return results

    def is_match(self, media):
        meta_id = getattr(media, "metadata_id", "")
        if meta_id:
            return meta_id.startswith(self.name + ".")
        else:
            return super(JAVLibrary, self).is_match(media)

    def get_id_by_name(self, name):
        name = name.lower()
        pattern = r"(?:^|\s|\[|\(|\.|\\|\/)([a-z\d]+[-][a-z\d]+)(?:$|\s|\]|\)|\.)"
        match = re.search(pattern, name)
        if match:
            return match.group(1)

    def get_title_sort(self, media, data):
        return self.get_title(media, data)

    def crawl(self, media):
        url = "https://www.javlibrary.com/ja/"
        resp = self.session.get(url, params={
            "v": media.metadata_id.split(".")[1]
        })
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def get_studio(self, media, data):
        ele = self.find_ele(data, "メーカー:")
        if ele:
            return ele.find("a").text.strip()

    def get_original_title(self, media, data):
        return data.find("div", {"id": "video_title"}).find("a").text.strip()

    def get_originally_available_at(self, media, data):
        ele = self.find_ele(data, "発売日:")
        if ele:
            dt_str = ele.text.strip()
            match = re.search("\d+[-]\d+[-]\d+", dt_str)
            try:
                if match:
                    return datetime.datetime.strptime(match.group(0), "%Y-%m-%d")
            except ValueError:
                pass

    def get_roles(self, media, data):
        ele = self.find_ele(data, "出演者:")
        if ele:
            return [
                list(filter(None, item.text.strip().split(" ")))[0]
                for item in ele.findAll("a")
            ]
        return []

    def get_duration(self, media, data):
        ele = self.find_ele(data, "収録時間:")
        if ele:
            match = re.search("\d+", ele.find("span", "text").text)
            if match:
                return int(match.group(0))*60*1000

    def get_directors(self, media, data):
        ele = self.find_ele(data, "監督:")
        if ele and ele.find("a"):
            return [ele.find("a").text.strip()]
        return []

    def get_genres(self, media, data):
        ele = self.find_ele(data, "ジャンル:")
        if ele:
            return [ele.text.strip() for ele in ele.findAll("a")]
        return []

    def get_rating(self, media, data):
        ele = self.find_ele(data, "平均評価:")
        if ele:
            try:
                return float(ele.find("span", "score").text.strip("()"))
            except ValueError:
                pass
        
    def get_posters(self, media, data):
        javlibrary_thumb = data.find("img", {"id": "video_jacket_img"})
        if javlibrary_thumb and javlibrary_thumb["src"]:
            return ["https:" + javlibrary_thumb["src"].replace("pl.", "ps.")]

    def get_thumbs(self, media, data):
        javlibrary_thumb = data.find("img", {"id": "video_jacket_img"})
        if javlibrary_thumb and javlibrary_thumb["src"]:
            return ["https:" + javlibrary_thumb["src"]]

    def find_ele(self, data, title):
        ele = data.find("table", {"id": "video_jacket_info"})
        single_infos = ele.findAll("tr")
        for single_info in single_infos:
            if single_info.find("td", "header").text.strip() == title:
                return single_info.find("td", "header").findNext("td")

    s_requests = None
    s_cloudscraper = None

    @property
    def session(self):
        rv = None
        if Prefs["enableJavLibraryCloudScraper"]:
            if not self.s_cloudscraper:
                self.s_cloudscraper = cloudscraper.create_scraper(delay=5)
            rv = self.s_cloudscraper
        else:
            if not self.s_requests:
                self.s_requests = requests.session()
            rv = self.s_requests
        if Prefs["userAgent"]:
            rv.headers["User-Agent"] = Prefs["userAgent"]
        return rv
