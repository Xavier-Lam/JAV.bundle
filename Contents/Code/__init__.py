# coding=utf-8

import os

from cached_property import cached_property

import agents


def Start():
    pass


class UncensoredJAVAgent(Agent.Movies):
    name = "UncensoredJAV"
    languages = [
        Locale.Language.NoLanguage
    ]
    accepts_from = [
        'com.plexapp.agents.localmedia'
    ]
    contributes_to = [
        'com.plexapp.agents.none'
    ]

    def search(self, results, media, lang):
        agent = self.get_agent(media)
        if agent:
            movie_id = self.get_id(media)
            search_results = agent.get_results(movie_id)
            for result in search_results:
                result.lang = lang
                results.Append(result)

    def update(self, metadata, media, lang):
        movie_id = metadata.id
        agent = self.get_agent(media)
        agent.get_info(movie_id, metadata)
        return metadata

    def get_agent(self, media):
        filename = media.items[0].parts[0].file
        dirname = os.path.dirname(filename)
        for agent in self.agents:
            if agent.match(filename) or agent.match(dirname):
                return agent

    def get_id(self, media):
        filename = media.items[0].parts[0].file
        dirname = os.path.dirname(filename)
        for agent in self.agents:
            media_id = agent.match(filename) or agent.match(dirname)
            return media_id

    @cached_property
    def agents(self):
        return [
            agents.Caribbean()
        ]
