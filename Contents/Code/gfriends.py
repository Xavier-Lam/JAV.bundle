# coding=utf-8

import requests
from urllib import quote


class GFriend(dict):
    def __init__(self):
        github_template = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/{}/{}/{}'
        request_url = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/Filetree.json'

        Log("Loading gfriends file tree has started.")

        response = requests.get(request_url)
        if response.status_code != 200:
            Log('request gfriend map failed {}'.format(response.status_code))
            return {}

        Log("Finish loading gfriends file tree")

        map_json = response.json()
        map_json.pop('Filetree.json', None)
        map_json.pop('README.md', None)

        # plex doesnt support fucking recursive call
        first_lvls = map_json.keys()
        for first in first_lvls:
            second_lvls = map_json[first].keys()
            for second in second_lvls:
                for k, v in map_json[first][second].items():
                    self[k[:-4]] = github_template.format(
                        quote(first.encode("utf-8")),
                        quote(second.encode("utf-8")),
                        quote(v.encode("utf-8"))
                    )


gfriends = GFriend()
