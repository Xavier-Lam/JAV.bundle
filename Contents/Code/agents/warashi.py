# coding=utf-8

from urllib import quote

from bs4 import BeautifulSoup

from .base import AvatarAgent
from .types import Resource

BASE_URL = "https://warashi-asian-pornstars.fr"


class WarashiPornstars(AvatarAgent):
    name = "WarashiPornstars"
    weight = -200

    def __init__(self, *args, **kwargs):
        super(WarashiPornstars, self).__init__(*args, **kwargs)
        self.cache = {}

    def get_avatar(self, name, lang):
        if name not in self.cache:
            soup = self.fetch(name)
            ele = soup.find("div", "bloc-resultats")
            if ele:
                actress = ele.find("div", "resultat-pornostar")
                if actress:
                    href = actress.find("a")["href"]
                    detail_url = BASE_URL + quote(href.encode("utf-8"), safe="/:")
                    fallback = Resource(BASE_URL + actress.find("img")["src"])
                    fallback.score = 20
                    try:
                        detail_soup = self.fetch_url(detail_url)
                        img = detail_soup.find(
                            "img", src=lambda s: s and "/profil-0/large/" in s)
                        if not img:
                            raise ValueError("No image found on detail page")
                        self.cache[name] = Resource(BASE_URL + img["src"])
                    except Exception as e:
                        self.logger.warning(
                            "Failed to fetch detail page for actress %s: %s",
                            name, e)
                        self.cache[name] = fallback

        return self.cache.get(name)

    def fetch(self, name):
        url = BASE_URL + "/ja/s-12/%E6%A4%9C%E7%B4%A2"
        resp = self.session.post(url, dict(
            recherche_critere="f",
            recherche_valeur=name,
            x=0,
            y=0
        ))
        resp.raise_for_status()
        html = resp.content.decode("utf-8")
        return BeautifulSoup(html, "html.parser")

    def fetch_url(self, url):
        resp = self.session.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.content.decode("utf-8"), "html.parser")
