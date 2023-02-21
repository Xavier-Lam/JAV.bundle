# coding=utf-8

import requests

from bs4 import BeautifulSoup

from .base import AvatarAgent


class WarashiPornstars(AvatarAgent, dict):
    initialized = False

    def get_name(self):
        return "WarashiPornstars"

    def get_roledata(self, name):
        soup = self.crawl(name)
        ele = soup.find("div", "bloc-resultats")
        if ele:
            actress = ele.find("div", "resultat-pornostar")
            if actress:
                url = "http://warashi-asian-pornstars.fr" + \
                    actress.find("img")["src"]
                return {
                    "photo": url
                }
        return {}

    def crawl(self, name):
        url = "http://warashi-asian-pornstars.fr/ja/s-12/%E6%A4%9C%E7%B4%A2"
        resp = requests.post(url, dict(
            recherche_critere="f",
            recherche_valeur=name,
            x=0,
            y=0
        ))
        resp.raise_for_status()
        html = resp.content.decode()
        return BeautifulSoup(html, "html.parser")
