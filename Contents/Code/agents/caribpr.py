# coding=utf-8

import re

from caribbean import Caribbean


class CaribbeanPr(Caribbean):
    def get_name(self):
        return "Caribbean Premium"

    def guess_keywords(self, name):
        if "caribpr" in name.lower():
            match = re.search(r"(\d{6})[-_](\d{3})", name)
            if match:
                return [match.group(1) + "_" + match.group(2)]
        return []

    def get_original_title(self, movie_id, data):
        title = data.find("h1").text.strip()
        return "{0} {1} {2} {3}".format(
            self.get_studio(),
            movie_id,
            title,
            " ".join([role["name"] for role in self.get_roles(data)])
        )

    def get_title_sort(self, movie_id):
        match = re.match(r"(\d{2})(\d{2})(\d{2})_(\d+)$", movie_id)
        return "{0} {1}".format(
            self.get_studio(),
            "{0}{1}{2}-{3}".format(match.group(3), match.group(1),
                                   match.group(2), match.group(4))
        )

    def get_roles(self, data):
        ele = self.find_ele(data, "出演")
        if ele:
            items = ele.findAll("a", {"class": "spec-item"})
            roles = [
                {"name": item.text.strip()}
                for item in items
            ]
            return roles
        return []

    def is_studio(self, name):
        return name.lower() in ["caribpr"]

    def base_url(self):
        return "https://www.caribbeancompr.com"
