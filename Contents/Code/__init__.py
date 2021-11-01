# coding=utf-8

import os


def Start():
    if Prefs["proxy"]:
        os.environ.setdefault("HTTP_PROXY", Prefs["proxy"])
        os.environ.setdefault("HTTPS_PROXY", Prefs["proxy"])


class JAVAgent(Agent.Movies):
    name = "JAV"
    languages = [
        Locale.Language.NoLanguage
    ]
    accepts_from = [
        'com.plexapp.agents.localmedia'
    ]
    contributes_to = [
        'com.plexapp.agents.none'
    ]
    agents = {}

    def search(self, results, media, lang):
        for agent in self.get_agents(lang):
            if agent.is_match(media):
                movie_id = agent.get_id(media)
                Log("Pattern matched by agent {0}, movie id is {1}".format(
                    agent.name, movie_id))
                search_results = agent.get_results(media)
                Log(str(len(search_results)) + " results has been found.")
                if search_results:
                    for result in search_results:
                        results.Append(MetadataSearchResult(**result))

    def update(self, metadata, media, lang):
        media.metadata_id = metadata.id
        for agent in self.get_agents(lang):
            if agent.is_match(media):
                movie_id = agent.get_id(media)
                Log("Start update metadata by using agent {0}, movie id is {1}".format(
                    agent.name, movie_id))
                try:
                    agent.update(metadata, media)
                    Log("Update metadata successfully")

                    from gfriends import gfriends
                    for role in metadata.roles:
                        role.photo = gfriends.get(role.name.upper(), "")
                    return
                except Exception as e:
                    raise
                    Log("An error occured when loading data: " + str(e))

    def get_agents(self, lang):
        from agents import AVE, Caribbean, Heyzo, JAVLibrary, Pondo, TokyoHot
        if lang not in self.agents:
            self.agents[lang] = [
                Caribbean(lang),
                Heyzo(lang),
                Pondo(lang),
                TokyoHot(lang),
                JAVLibrary(lang),
                AVE(lang)
            ]
        return self.agents[lang]
