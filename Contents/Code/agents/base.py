# coding=utf-8

from urllib import quote

from cached_property import cached_property
import requests


class GFriend(dict):
    def __init__(self):
        github_template = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/{}/{}/{}'
        request_url = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/Filetree.json'

        Log("start loading gfriend file tree")

        response = requests.get(request_url)
        if response.status_code != 200:
            Log('request gfriend map failed {}'.format(response.status_code))
            return {}

        Log("gfriend file tree loaded success")

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


class DummyClass(object):
    pass


class Collection(list):
    def clear(self):
        pass

    def add(self, item):
        self.append(item)

    def new(self):
        return DummyClass()


class DummyMetaData(object):
    directors = Collection()
    roles = Collection()
    posters = {}
    genres = Collection()
    art = {}


class Base(object):
    def match(self, filename):
        pass

    def get_results(self, movie_id):
        metadata = DummyMetaData()
        self.get_info(movie_id, metadata)
        return [MetadataSearchResult(
            id=movie_id,
            name=metadata.title,
            year=metadata.year,
            score=100
        )]

    def get_info(self, movie_id, metadata):
        global gfriends

        html = self.crawl_page(movie_id)
        metadata.title = self.get_title(movie_id, html)
        metadata.title_sort = self.get_title_sort(movie_id, html)
        metadata.studio = self.get_studio(movie_id, html)
        metadata.originally_available_at = self.get_originally_available_at(movie_id, html)
        if metadata.originally_available_at:
            metadata.year = metadata.originally_available_at.year
        else:
            metadata.year = None
        metadata.rating = self.get_rating(movie_id, html)
        metadata.duration = self.get_duration(movie_id, html)
        directors = self.get_directors(movie_id, html)
        metadata.directors.clear()
        for director in directors:
            metadata.directors.new().name = director

        roles = self.get_roles(movie_id, html)
        metadata.roles.clear()
        for actress_name in roles:
            role = metadata.roles.new()
            role.name = actress_name
            role.photo = gfriends.get(actress_name.upper(), "")

        posters = self.get_posters(movie_id, html)
        for poster in posters:
            metadata.posters[poster] = Proxy.Preview(HTTP.Request(poster).content)

        thumbs = self.get_thumbs(movie_id, html)
        for key in metadata.art.keys():
            del metadata.art[key]
        for thumb in thumbs:
            metadata.art[thumb] = Proxy.Preview(HTTP.Request(thumb).content)

        genres = self.get_genres(movie_id, html)
        for genre in genres:
            metadata.genres.add(genre)

    def crawl_page(self, movie_id):
        pass

    def get_title(self, movie_id, html):
        pass

    def get_title_sort(self, movie_id, html):
        pass

    def get_studio(self, movie_id, html):
        pass

    def get_originally_available_at(self, movie_id, html):
        pass

    def get_rating(self, movie_id, html):
        pass

    def get_duration(self, movie_id, html):
        pass

    def get_directors(self, movie_id, html):
        return []

    def get_roles(self, movie_id, html):
        return []

    def get_posters(self, movie_id, html):
        return []

    def get_thumbs(self, movie_id, html):
        return self.get_posters(movie_id, html)

    def get_genres(self, movie_id, html):
        return []
