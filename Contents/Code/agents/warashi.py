# coding=utf-8

from bs4 import BeautifulSoup

from .base import AvatarAgent


class WarashiPornstars(AvatarAgent):
    name = "WarashiPornstars"
    weight = -300

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
                    self.cache[name] = "http://warashi-asian-pornstars.fr" + \
                        actress.find("img")["src"]

        return self.cache.get(name)

    def fetch(self, name):
        url = "http://warashi-asian-pornstars.fr/ja/s-12/%E6%A4%9C%E7%B4%A2"
        resp = self.session.post(url, dict(
            recherche_critere="f",
            recherche_valeur=name,
            x=0,
            y=0
        ))
        resp.raise_for_status()
        html = resp.content.decode()
        return BeautifulSoup(html, "html.parser")
