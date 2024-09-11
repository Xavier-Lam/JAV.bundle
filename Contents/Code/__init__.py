# coding=utf-8

import os
import re

import agents
from .utils import OrderedSet


def Start():
    if Prefs["proxy"]:
        os.environ.setdefault("HTTP_PROXY", Prefs["proxy"])
        os.environ.setdefault("HTTPS_PROXY", Prefs["proxy"])
        Log("Start with proxy: {0}".format(Prefs["proxy"]))


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
    agent_collections = {}

    def search(self, results, media, lang):
        got_ids = set()
        names = self.get_media_names(media)
        for agent in self.agents(lang).filter(agents.QueryAgent):
            keywords = OrderedSet()
            for name in names:
                keywords.union(agent.guess_keywords(name))
            for keyword in keywords:
                try:
                    query_results = agent.query(keyword)
                except Exception as e:
                    Log.Exception("%s", e)
                    continue
                for r in query_results:
                    if r.id not in got_ids:
                        got_ids.add(r.id)
                        r.id = "{0},{1}".format(keyword, r.id)
                        results.Append(r)
                Log("Search for movie: {0} by {1}, found {2} records.".format(
                    keyword, agent.get_name(), len(query_results)))

    def update(self, metadata, media, lang):
        metadata_id = metadata.id

        # Compatible with JAVLibrary.bundle
        if "." not in metadata_id and re.match(r"jav[a-z0-9]{6,10}$"):
            metadata_id = "JAVLibrary.{0}".format(metadata_id)

        # Compatible with old version
        if "." in metadata_id and "," not in metadata_id:
            metadata_id = ",{0}".format(metadata_id)

        meta_dict = {
            "agent_ids": {}
        }

        # Get data from third party library first
        for agent in self.agents(lang).filter(agents.LibraryAgent):
            if agent.is_match(metadata_id):
                third_party_data = agent.get_metadata(metadata_id)
                Log("Get metadata from {0} for movie {1}: {2}".format(
                    agent.get_name(), metadata_id, third_party_data))
                if third_party_data:
                    meta_dict["agent_ids"][agent.get_name()] = third_party_data.pop(
                        "agent_id")
                    meta_dict.update({
                        k: v for k, v in third_party_data.items()
                        if v is not None
                    })
                    # Only use first matched agent
                    break

        # Override data from studio agent
        for agent in self.agents(lang).filter(agents.StudioAgent):
            if meta_dict.get("studio") and agent.is_studio(meta_dict["studio"])\
                    or agent.is_match(metadata_id):
                studio_data = agent.get_metadata(metadata_id)
                Log("Get metadata from {0} for movie {1}: {2}".format(
                    agent.get_name(), metadata_id, studio_data))
                if studio_data:
                    meta_dict["agent_ids"][agent.get_name()] = studio_data.pop(
                        "agent_id")
                    meta_dict.update({
                        k: v for k, v in studio_data.items()
                        if v is not None
                    })
                    # Only use first matched agent
                    break

        # # Revise actress name
        # for agent in self.agents(lang).filter(agents.ActressAgent):
        #     for role in meta_dict.roles:
        #         role.update(agent.get_roledata())
        #     # Only use highest priority agent
        #     break

        # Get actress photo
        for agent in self.agents(lang).filter(agents.AvatarAgent):
            for role in meta_dict["roles"]:
                role.update(agent.get_roledata(role["name"]))
            # Only use highest priority agent
            break

        # Update metadata
        self.update_metadata(metadata, meta_dict)

    def get_media_names(self, media):
        rv = []

        # media name
        name = getattr(media, "name", "")
        if name:
            rv.append(name)

        # filename and dirname
        filename = media.items[0].parts[0].file
        rv.append(os.path.basename(filename))
        rv.append(os.path.basename(os.path.dirname(filename)))

        return rv

    def agents(self, lang):
        if lang not in self.agent_collections:
            self.agent_collections[lang] = AgentCollection(lang)
        return self.agent_collections[lang]

    def update_metadata(self, metadata, meta_dict):
        Log("Update {0}: {1}".format(metadata.id, meta_dict))

        agent_ids = meta_dict.pop("agent_ids")
        if not agent_ids:
            return

        meta_dict["id"] = "{0},{1}".format(
            meta_dict.pop("movie_id"),
            ";".join(["{0}.{1}".format(k, v)
                     for k, v in agent_ids.items()])
        )

        if "original_title" not in meta_dict:
            meta_dict["original_title"] = meta_dict["title"]
        if "title_sort" not in meta_dict:
            meta_dict["title_sort"] = meta_dict["title"]
        if "originally_available_at" in meta_dict:
            meta_dict["year"] = meta_dict["originally_available_at"].year

        for key, value in meta_dict.items():
            if key in ("directors", "producers", "roles"):
                getattr(metadata, key).clear()
                for item in value:
                    obj = getattr(metadata, key).new()
                    for item_key, item_value in item.items():
                        setattr(obj, item_key, item_value)

            elif key in ("posters", "art"):
                for image_url in value:
                    getattr(metadata, key)[image_url] = Proxy.Preview(
                        HTTP.Request(image_url).content)

            elif key in ("genres", "collections"):
                for title in value:
                    getattr(metadata, key).add(title)

            else:
                setattr(metadata, key, value)


class AgentCollection(object):
    def __init__(self, lang):
        self.agents = [
            agents.Caribbean(lang),
            agents.CaribbeanPr(lang),
            agents.Heyzo(lang),
            agents.Pondo(lang),
            agents.TokyoHot(lang),
            agents.JAVLibrary(lang),
            agents.AVE(lang),
            agents.GFriend(lang),
            agents.WarashiPornstars(lang),
            agents.FC2(lang),
            agents.JavDB(lang),
        ]

    def filter(self, agent_type):
        return [
            agent for agent in self.agents
            if isinstance(agent, agent_type)
        ]

    def get(self, name):
        for agent in self.agents:
            if agent.get_name() == name:
                return agent
