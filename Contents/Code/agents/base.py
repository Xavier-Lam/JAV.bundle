# coding=utf-8

import os


class Base(object):
    def update(self, metadata, media, lang):
        data = self.crawl(media, lang)
        metadata.title = self.get_title(media, data, lang)
        metadata.title_sort = self.get_title_sort(media, data, lang)
        metadata.original_title = self.get_original_title(media, data, lang)

        metadata.originally_available_at = self.get_originally_available_at(media, data, lang)
        metadata.year = metadata.originally_available_at and metadata.originally_available_at.year
        metadata.duration = self.get_duration(media, data, lang)

        metadata.tagline = self.get_tagline(media, data, lang)
        metadata.summary = self.get_summary(media, data, lang)
        metadata.trivia = self.get_trivia(media, data, lang)
        metadata.quotes = self.get_quotes(media, data, lang)

        metadata.studio = self.get_studio(media, data, lang)

        metadata.rating = self.get_rating(media, data, lang)

        metadata.countries.clear()
        countries = self.get_countries(media, data, lang)
        for country in countries:
            metadata.countries.new().name = country

        directors = self.get_directors(media, data, lang)
        metadata.directors.clear()
        for director in directors:
            metadata.directors.new().name = director

        producers = self.get_producers(media, data, lang)
        metadata.producers.clear()
        for producer in producers:
            metadata.producers.new().name = producer

        roles = self.get_roles(media, data, lang)
        metadata.roles.clear()
        for actress_name in roles:
            role = metadata.roles.new()
            role.name = actress_name

        posters = self.get_posters(media, data, lang)
        for poster in posters:
            metadata.posters[poster] = Proxy.Preview(HTTP.Request(poster).content)

        thumbs = self.get_thumbs(media, data, lang)
        for key in metadata.art.keys():
            del metadata.art[key]
        for thumb in thumbs:
            metadata.art[thumb] = Proxy.Preview(HTTP.Request(thumb).content)

        genres = self.get_genres(media, data, lang)
        for genre in genres:
            metadata.genres.add(genre)

        collections = self.get_collections(media, data, lang)
        for collection in collections:
            metadata.collections.add(collection)

    def is_match(self, media):
        return bool(self.get_id(media))

    def get_id(self, media, data=None, lang=None):
        pass

    def get_results(self, media, lang):
        return []

    def crawl(self, media, lang):
        pass

    def get_title(self, media, data, lang):
        return self.get_original_title(media, data, lang)

    def get_title_sort(self, media, data, lang):
        return self.get_original_title(media, data, lang)

    def get_original_title(self, media, data, lang):
        pass

    def get_originally_available_at(self, media, data, lang):
        pass

    def get_tagline(self, media, data, lang):
        pass

    def get_summary(self, media, data, lang):
        pass

    def get_trivia(self, media, data, lang):
        pass

    def get_quotes(self, media, data, lang):
        pass

    def get_studio(self, media, data, lang):
        pass

    def get_rating(self, media, data, lang):
        pass

    def get_duration(self, media, data, lang):
        pass

    def get_countries(self, media, data, lang):
        return []

    def get_directors(self, media, data, lang):
        return []

    def get_producers(self, media, data, lang):
        return []

    def get_roles(self, media, data, lang):
        return []

    def get_posters(self, media, data, lang):
        return []

    def get_thumbs(self, media, data, lang):
        return self.get_posters(media, data, lang)

    def get_genres(self, media, data, lang):
        return []

    def get_collections(self, media, data, lang):
        return []

    def get_filename(self, media):
        filename = media.items[0].parts[0].file
        return os.path.basename(filename)

    def get_dirname(self, media):
        filename = media.items[0].parts[0].file
        return os.path.dirname(filename)
