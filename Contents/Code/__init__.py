# coding=utf-8

from cached_property import cached_property


def Start():
    pass


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

    def search(self, results, media, lang):
        for agent in self.agents:
            if agent.is_match(media):
                movie_id = agent.get_id(media)
                Log("Pattern matched by agent {0}, movie id is {1}".format(
                    agent.name, movie_id))
                search_results = agent.get_results(media, lang)
                Log(str(len(search_results)) + " results has been found.")
                if search_results:
                    for result in search_results:
                        results.Append(MetadataSearchResult(**result))
                        return

    def update(self, metadata, media, lang):
        for agent in self.agents:
            if agent.is_match(media):
                movie_id = agent.get_id(media)
                Log("Start update metadata by using agent {0}, movie id is {1}".format(
                    agent.name, movie_id))
                try:
                    agent.update(metadata, media, lang)
                    Log("Update metadata successfully")

                    from gfriends import gfriends
                    for role in metadata.roles:
                        role.photo = gfriends.get(role.name.upper(), "")
                    return
                except Exception as e:
                    raise
                    Log("An error occured when loading data: " + str(e))

    @cached_property
    def agents(self):
        from agents import Caribbean, CaribbeanLocal, Heyzo, Pondo
        return [
            Caribbean(),
            Heyzo(),
            Pondo(),
            CaribbeanLocal()
        ]
