# coding=utf-8

from bs4 import BeautifulSoup
import requests
import re

from .base import ID_PATTERN, QueryAgent, StudioAgent

class JavDB(QueryAgent, StudioAgent):
    """
    https://javdb.com/
    """

    def get_name(self):
        return "JavDB"


    def guess_keywords(self, name):
        match = re.search(ID_PATTERN, name)
        if match:
            return [match.group(1).upper()]
        else:
            return []

    def query(self, keyword):
        url = 'https://javdb.com//search?q=%s&f=all' % keyword
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        ele = soup.find("div", class_="movie-list")
        ele.findAll("div", class_="video-title")
        results = ele.findAll("div", class_="item")

        answers = list()
        score = 100
        for result in results:
            title = result.find("div", class_="video-title").text.strip()
            code = result.find("a")["href"].split("/")[-1]
            answer = self.make_result(code, title, score=score)
            score = score - 1
            answers.append(answer)
        return answers

    def get_studio(self, data):
        return data[u"\u7247\u5546"] # 片商

    def get_title(self, data):
        return data["title"]

    def get_genres(self, data):
        k = u"\u985e\u5225" # 類別
        if k in data:
            genres = data[k].split(",")
            genres = [g.strip() for g in genres]
            return genres
        else:
            return []

    def is_match(self, metadata_id):
        movie_id = self.get_agent_id(metadata_id)
        url = 'https://javdb.com/v/%s' % movie_id
        resp = requests.head(url)
        return resp.ok

    def get_posters(self, data):
        # The thumbs endpoint returns the covers image if there are no thumbs
        thumb = data["cover"].replace("covers", "thumbs")
        return [thumb]

    def get_collections(self, data):
        k = u'\u7cfb\u5217' # 系列
        if k in data:
            return [data[k]]
        else:
            return []

    def get_roles(self, data):
        return data["roles"]

    def get_metadata(self, metadata_id):
        movie_id = self.get_agent_id(metadata_id)
        data = self.crawl(movie_id)
        result = {
            "movie_id": self.get_movie_id(metadata_id),
            "title": self.get_title(data),
            "genres": self.get_genres(data),
            "studio": self.get_studio(data),
            "posters": self.get_posters(data),
            "roles": self.get_roles(data),
            "collections": self.get_collections(data),
            "agent_id": movie_id,
        }
        return result

    def crawl(self, movie_id):
        url = 'https://javdb.com/v/%s' % movie_id
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        divs = soup.findAll("div", class_="panel-block")

        data = dict()
        data["title"] = soup.find("h2", class_="title is-4").text

        roles = list()
        links = soup.findAll("a")
        for link in links:
            href = link.get("href")
            class_ = link.get("class")
            if href and "/actors/" in href and not class_:
                roles.append({"name":link.text})
        data["roles"] = roles

        img = soup.find("img", class_="video-cover")
        data["cover"] = img.get("src")

        for div in divs:
            text = div.text
            if ":" in text:
                parts = text.split(":")
                k = parts[0].strip()
                v = parts[1].strip()
                data[k] = v
        return data
