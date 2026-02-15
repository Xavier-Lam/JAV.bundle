# coding=utf-8

import re


ID_PATTERN = re.compile(
    r"(?:^|\s|\[|\(|\.|\\|\/)([a-zA-Z\d]+[-][a-zA-Z\d]+)(?:$|\s|\]|\)|\.)")


class Base(object):
    def __init__(self, lang=None):
        self.lang = lang

    def get_name(self):
        raise NotImplemented()

    def is_match(self, metadata_id):
        """
        The struct of metadata_id is {MovieId},{agent1}.{id};{agent2}.id

        For example: 
        """
        return self.get_agent_id(metadata_id)

    def get_agent_id(self, metadata_id):
        agent_id_str = metadata_id.split(",", 2)[1]
        if not agent_id_str:
            return
        agent_ids = agent_id_str.split(";")
        for agent_id in agent_ids:
            if agent_id.startswith("{0}.".format(self.get_name())):
                return agent_id.split(".")[1]

    def get_movie_id(self, metadata_id):
        return metadata_id.split(",")[0]

    def build_metadata_id(self, agent_id):
        return "{0}.{1}".format(self.get_name(), agent_id)


class QueryAgent(Base):
    """An agent available for search"""

    def query(self, keyword):
        raise NotImplemented()

    def make_result(self, agent_id, name, year=None, score=100, thumb=None):
        return MetadataSearchResult(
            id=self.build_metadata_id(agent_id),
            name=name,
            year=year,
            score=score,
            lang=self.lang,
            thumb=thumb
        )


class MetadataAgent(Base):
    """"""

    def get_metadata(self, metadata_id):
        raise NotImplemented()


class LibraryAgent(QueryAgent, MetadataAgent):
    """
    Third party agent

    A third party agent used for fill the basic data of a movie, provide some
    common data like genres or ratings to avoid discrepancy in studio sites.
    """


class StudioAgent(MetadataAgent):
    """Studio official site agent"""

    def is_studio(self, name):
        return False


class ActressAgent(MetadataAgent):
    def get_roledata(self, name):
        raise NotImplemented()


class AvatarAgent(ActressAgent):
    """"""
