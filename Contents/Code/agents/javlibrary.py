# coding=utf-8

import datetime
from difflib import SequenceMatcher
import re

from bs4 import BeautifulSoup
import requests

from .base import ID_PATTERN, LibraryAgent


class JAVLibrary(LibraryAgent):
    def get_name(self):
        return "JAVLibrary"

    def guess_keywords(self, name):
        match = re.search(ID_PATTERN, name)
        if match:
            return [match.group(1).upper()]
        return []

    def query(self, keyword):
        keyword = keyword.upper()
        results = []
        url = "https://www.javlibrary.com/ja/vl_searchbyid.php"
        params = {
            "keyword": keyword
        }
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        if soup.find("div", "videos"):
            if soup.find("div", "video"):
                for video in soup.find_all("div", "video"):
                    agent_id = video.find("a")["href"][5:]
                    video_id = video.find("div", "id").text.strip().upper()
                    score = int(SequenceMatcher(
                        None, keyword, video_id).ratio()*100)
                    results.append(self.make_result(
                        agent_id,
                        video.find("a")["title"],
                        score=score
                    ))
        else:
            try:
                agent_id = soup.find("h3", "post-title").find("a")["href"][7:]
            except AttributeError:
                Log("an exception occurred: " + url)
                return
            results.append(self.make_result(
                agent_id,
                soup.find("div", {"id": "video_title"}).find("a").text.strip()
            ))
        return results

    def get_metadata(self, metadata_id):
        agent_id = self.get_agent_id(metadata_id)
        data = self.crawl(agent_id)

        title = self.get_original_title(data)
        if not title:
            raise Exception(
                "Got an unexpected response for {0}".format(metadata_id))

        return {
            "movie_id": re.split(r"\s", title)[0],
            "agent_id": agent_id,
            "title": title,
            "originally_available_at": self.get_originally_available_at(data),
            "roles": self.get_roles(data),
            "directors": self.get_directors(data),
            "studio": self.get_studio(data),
            "duration": self.get_duration(data),
            "genres": self.get_genres(data),
            "rating": self.get_rating(data),
            "posters": self.get_posters(data),
            "art": self.get_thumbs(data)
        }

    def get_studio(self, data):
        ele = self.find_ele(data, "メーカー:")
        if ele:
            return ele.find("a").text.strip()

    def get_original_title(self, data):
        return data.find("div", {"id": "video_title"}).find("a").text.strip()

    def get_originally_available_at(self, data):
        ele = self.find_ele(data, "発売日:")
        if ele:
            dt_str = ele.text.strip()
            match = re.search("\d+[-]\d+[-]\d+", dt_str)
            try:
                if match:
                    return datetime.datetime.strptime(match.group(0), "%Y-%m-%d")
            except ValueError:
                pass

    def get_roles(self, data):
        ele = self.find_ele(data, "出演者:")
        if ele:
            return [
                {"name": list(filter(None, item.text.strip().split(" ")))[0]}
                for item in ele.findAll("a")
            ]
        return []

    def get_duration(self, data):
        ele = self.find_ele(data, "収録時間:")
        if ele:
            match = re.search("\d+", ele.find("span", "text").text)
            if match:
                return int(match.group(0))*60*1000

    def get_directors(self, data):
        ele = self.find_ele(data, "監督:")
        if ele and ele.find("a"):
            return [{"name": ele.find("a").text.strip()}]
        return []

    def get_genres(self, data):
        ele = self.find_ele(data, "ジャンル:")
        if ele:
            return [ele.text.strip() for ele in ele.findAll("a")]
        return []

    def get_rating(self, data):
        ele = self.find_ele(data, "平均評価:")
        if ele:
            try:
                return float(ele.find("span", "score").text.strip("()"))
            except ValueError:
                pass

    def get_posters(self, data):
        javlibrary_thumb = data.find("img", {"id": "video_jacket_img"})
        if javlibrary_thumb and javlibrary_thumb["src"]:
            src = javlibrary_thumb["src"]
            if not src.startswith("http"):
                src = "https:" + src
            return [src.replace("pl.", "ps.")]

    def get_thumbs(self, data):
        javlibrary_thumb = data.find("img", {"id": "video_jacket_img"})
        if javlibrary_thumb and javlibrary_thumb["src"]:
            src = javlibrary_thumb["src"]
            if not src.startswith("http"):
                src = "https:" + src
            return [src]

    def crawl(self, agent_id):
        url = "https://www.javlibrary.com/ja/"
        resp = self.session.get(url, params={
            "v": agent_id
        })
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

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
        if not self.s_requests:
            self.s_requests = requests.session()
            if Prefs["userAgent"]:
                self.s_requests.headers["User-Agent"] = Prefs["userAgent"]
        return self.s_requests
