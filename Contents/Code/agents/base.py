# coding=utf-8

import os


class Base(object):
    def __init__(self, lang=None):
        self.lang = lang

    def update(self, metadata, media):
        data = self.crawl(media)
        metadata.title = self.get_title(media, data)
        metadata.title_sort = self.get_title_sort(media, data)
        metadata.original_title = self.get_original_title(media, data)

        metadata.originally_available_at = self.get_originally_available_at(media, data)
        metadata.year = metadata.originally_available_at and metadata.originally_available_at.year
        metadata.duration = self.get_duration(media, data)

        metadata.tagline = self.get_tagline(media, data)
        metadata.summary = self.get_summary(media, data)
        metadata.trivia = self.get_trivia(media, data)
        metadata.quotes = self.get_quotes(media, data)

        metadata.studio = self.get_studio(media, data)

        metadata.rating = self.get_rating(media, data)

        metadata.countries.clear()
        countries = self.get_countries(media, data)
        for country in countries:
            metadata.countries.new().name = country

        directors = self.get_directors(media, data)
        metadata.directors.clear()
        for director in directors:
            metadata.directors.new().name = director

        producers = self.get_producers(media, data)
        metadata.producers.clear()
        for producer in producers:
            metadata.producers.new().name = producer

        roles = self.get_roles(media, data)
        metadata.roles.clear()
        for actress_name in roles:
            role = metadata.roles.new()
            role.name = actress_name

        posters = self.get_posters(media, data)
        for poster in posters:
            metadata.posters[poster] = Proxy.Preview(HTTP.Request(poster).content)

        thumbs = self.get_thumbs(media, data)
        for key in metadata.art.keys():
            del metadata.art[key]
        for thumb in thumbs:
            metadata.art[thumb] = Proxy.Preview(HTTP.Request(thumb).content)

        genres = self.get_genres(media, data)
        for genre in genres:
            metadata.genres.add(genre)

        collections = self.get_collections(media, data)
        for collection in collections:
            metadata.collections.add(collection)

    def is_match(self, media):
        meta_id = getattr(media, "metadata_id", "")
        return bool(meta_id.startswith(self.name + ".")
                    or self.get_id(media))

    def get_id(self, media, data=None):
        return self.get_id_by_name(getattr(media, "name", ""))\
               or self.get_id_by_name(media.items[0].parts[0].file)

    def get_id_by_name(self, name):
        pass

    def get_results(self, media):
        return []

    def crawl(self, media):
        pass

    def get_title(self, media, data):
        return self.get_original_title(media, data)

    def get_title_sort(self, media, data):
        return self.get_original_title(media, data)

    def get_original_title(self, media, data):
        pass

    def get_originally_available_at(self, media, data):
        pass

    def get_tagline(self, media, data):
        pass

    def get_summary(self, media, data):
        pass

    def get_trivia(self, media, data):
        pass

    def get_quotes(self, media, data):
        pass

    def get_studio(self, media, data):
        pass

    def get_rating(self, media, data):
        pass

    def get_duration(self, media, data):
        pass

    def get_countries(self, media, data):
        return []

    def get_directors(self, media, data):
        return []

    def get_producers(self, media, data):
        return []

    def get_roles(self, media, data):
        return []

    def get_posters(self, media, data):
        return []

    def get_thumbs(self, media, data):
        return self.get_posters(media, data)

    def get_genres(self, media, data):
        return []

    def get_collections(self, media, data):
        return []

    def get_filename(self, media):
        filename = media.items[0].parts[0].file
        return os.path.basename(filename)

    def get_dirname(self, media):
        filename = media.items[0].parts[0].file
        return os.path.dirname(filename)
