# coding=utf-8

from bs4 import BeautifulSoup
import requests
import re

from .base import QueryAgent, StudioAgent

class FC2(QueryAgent, StudioAgent):
    """
    http://adult.contents.fc2.com/
    """

    def guess_keywords(self, name):
        if self.is_studio(name):
            results = re.findall(r'\d+', name)

            # filter bogus numbers from FC2 and mp4
            results = [r for r in results if r not in ['2', '4']]

            # filter out small numbers
            results = [r for r in results if int(r) > 1000]

            return results
        else:
            return []


    def query(self, keyword):
        metadata = self.crawl(keyword)
        return [self.make_result(keyword, metadata["title"])]

    def get_name(self):
        return "FC2"

    def is_studio(self, name):
        return "fc" in name.lower()

    def get_studio(self):
        return "FC2"

    def get_tag_url(self, movie_id):
        return "https://adult.contents.fc2.com/api/v4/article/%d/tag?" % int(movie_id)

    def get_tag_data(self, movie_id):
        url = self.get_tag_url(movie_id)
        resp = requests.get(url)
        return resp.json()

    def is_match(self, metadata_id):
        movie_id = self.get_agent_id(metadata_id)
        if movie_id.isdigit():
            data = self.get_tag_data(movie_id)
            return data["code"] == 200
        return False

    def get_collections(self, movie_id):
        return [self.get_studio()]

    def get_genres(self, movie_id):
        data = self.get_tag_data(movie_id)
        if data["code"] == 200:
            genres = [tag["tag"] for tag in data["tags"]]
            return genres
        else:
            return []

    def get_metadata(self, metadata_id):
        movie_id = self.get_agent_id(metadata_id)
        return self.crawl(movie_id)

    def get_posters(self, movie_id):
        url = "https://adult.contents.fc2.com/api/v2/videos/%d/sample?" % int(movie_id)
        resp = requests.get(url)
        data = resp.json()
        if data["code"] == 200:
            return [data["poster_image_path"]]

    def crawl(self, movie_id):
        Log("FC2 >>> crawl %s", movie_id)
        url = 'https://adult.contents.fc2.com/article/%s/' % int(movie_id)
        resp = requests.get(url)
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h3").text.strip()
        return {
            "movie_id": movie_id,
            "title": title,
            "genres": self.get_genres(movie_id),
            "studio": self.get_studio(),
            "posters": self.get_posters(movie_id),
            "roles": [], # FC2 doesn't track actresses
            "collections": self.get_collections(movie_id),
            "agent_id": movie_id,
        }
