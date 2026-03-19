# coding=utf-8

from __future__ import absolute_import

from collections import OrderedDict
import json
import logging
import os
import requests
from urlparse import urlparse

import agents
from agents import BaseAgent, Metadata, MetadataAgent, PartialMetadataAgent, SearchAgent


def Start():
    agents_logger = logging.getLogger("agents")
    if not agents_logger.handlers:
        agents_logger.addHandler(PlexLogHandler())
        agents_logger.setLevel(logging.DEBUG)
        agents_logger.propagate = False

    log_prefs()


def ValidatePrefs():
    fs_url = Prefs["flaresolverr_url"]
    if fs_url and fs_url.strip():
        parsed = urlparse(fs_url.strip())
        if not parsed.scheme or not parsed.netloc:
            return MessageContainer("Invalid Preference",
                                    "Flaresolverr URL is not a valid URL.")

    log_prefs()


class JAVAgent(Agent.Movies):
    name = "JAV (V2)"
    languages = [
        Locale.Language.NoLanguage,
        Locale.Language.Japanese,
        Locale.Language.English,
        Locale.Language.Chinese,
    ]
    primary_provider = True
    accepts_from = [
        "com.plexapp.agents.localmedia",
    ]

    def search(self, results, hints, lang, manual=False):
        filename = os.path.basename(hints.items[0].parts[0].file)
        directory = os.path.basename(
            os.path.dirname(hints.items[0].parts[0].file))

        name = getattr(hints, "name", "")
        Log.Info(
            "Search start name=%s filename=%s directory=%s lang=%s manual=%s",
            name, filename, directory, lang, manual
        )
        lang = self.normalize_lang(lang)

        # search with all search agents
        search_results = []
        for agent in filter(lambda a: isinstance(a, SearchAgent), self.agents):
            keywords = agent.guess_keywords(name, filename, directory)
            if not keywords:
                agent.logger.debug("No keywords guessed")
                continue
            agent.logger.debug("Guessed keywords: %s", keywords)
            try:
                agent_results = agent.search(keywords, lang)
                agent.logger.debug("Search results: %s", agent_results)
            except Exception as e:
                agent.logger.exception("Search failed: %s", e)
                continue

            # merge search results
            for ar in agent_results:
                for sr in search_results:
                    if ar.video_code == sr.video_code:
                        sr.id = update_metadata_id(sr.id, agent.name, ar.id)
                        break
                else:
                    ar.id = update_metadata_id(
                        ar.video_code, agent.name, ar.id)
                    search_results.append(ar)

        # convert to Plex search results
        search_results.sort(key=lambda r: r.score, reverse=True)
        for sr in search_results:
            results.Append(MetadataSearchResult(
                id=sr.id,
                name=self.uncensor_text(sr.title, lang),
                year=sr.year,
                score=sr.score,
                lang=lang,
                thumb=sr.thumb,
            ))

        # log final outcome
        best = None
        if len(search_results):
            best = search_results[0]
        if best:
            Log.Info("Search done count=%d best_metadata_id=%s best_title=%s",
                     len(search_results), best.id, best.title)
        else:
            Log.Info("Search done count=0")

    def update(self, movie, media, lang, force=False, periodic=False):
        Log.Info("Update start metadata_id=%s lang=%s force=%s periodic=%s",
                 movie.id, lang, force, periodic)
        lang = self.normalize_lang(lang)

        if is_legacy_metadata_id(movie.id):
            Log.Debug("Legacy metadata ID detected, running search: %s", movie.id)
            results = SearchResultCollection()
            self.search(results, media, lang, manual=False)
            if results:
                Log.Info("Resolved legacy metadata ID: %s -> %s", movie.id, results[0].id)
                movie.id = results[0].id
            else:
                Log.Info("Search returned no results for legacy metadata ID: %s",
                         movie.id)

        video_code, agent_ids = parse_metadata_id(movie.id)
        metadata = Metadata()
        for agent in filter(lambda a: isinstance(a, MetadataAgent) or isinstance(
                a, PartialMetadataAgent), self.agents):
            if isinstance(agent, PartialMetadataAgent):
                try:
                    agent.partial_update(video_code, metadata, lang)
                except Exception as e:
                    agent.logger.exception("Partial update failed: %s", e)
                continue

            agent_id = agent_ids.get(agent.name)
            if not agent_id:
                continue

            try:
                agent_metadata = agent.get_metadata(agent_id, video_code, lang)
                agent.logger.debug("Metadata: %s", agent_metadata)
            except Exception as e:
                agent.logger.exception("Metadata retrieval failed: %s", e)
                continue

            # merge metadata
            for attr in dir(agent_metadata):
                new_value = getattr(agent_metadata, attr)
                if agent.should_contribute_to(metadata, attr, new_value):
                    current_value = getattr(metadata, attr)
                    contribution_value = agent.get_contribution_value(
                        new_value, attr, current_value)
                    setattr(metadata, attr, contribution_value)

        if force:
            self.clear_metadata(movie)

        self.apply_metadata(movie, metadata, lang)
        Log.Info("Update done: %s", repr(metadata))

    def clear_metadata(self, metadata):
        metadata.art.validate_keys([])
        metadata.rating = None
        metadata.collections.clear()
        metadata.directors.clear()
        metadata.duration = None
        metadata.genres.clear()
        metadata.originally_available_at = None
        metadata.original_title = ""
        metadata.posters.validate_keys([])
        metadata.roles.clear()
        metadata.similar.clear()
        metadata.studio = ""
        metadata.summary = ""
        metadata.tags.clear()
        metadata.title = ""
        metadata.title_sort = ""
        metadata.year = None

    def apply_metadata(self, movie, metadata, lang):
        movie.content_rating_age = 18
        movie.countries.clear()
        movie.countries.add("JP")

        similar = set()
        tags = set()

        if metadata.code_group:
            similar.add(metadata.code_group)
        movie.title = self.uncensor_text(metadata.title, lang)
        if metadata.japanese_title:
            movie.original_title = self.uncensor_text(metadata.japanese_title, lang)
        if metadata.release_date:
            movie.originally_available_at = metadata.release_date
            movie.year = metadata.release_date.year
        if metadata.studio:
            movie.studio = metadata.studio
            similar.add(metadata.studio)
        if metadata.series:
            series = self.uncensor_text(metadata.series, lang)
            similar.add(series)
            tags.add(series)
            if Prefs["series_as_collection"]:
                movie.collections.add(series)
        if metadata.duration:
            movie.duration = metadata.duration

        if metadata.actresses:
            movie.roles.clear()
            for o in metadata.actresses:
                role = movie.roles.new()
                role.name = o
                role.photo = o.photo
        if metadata.directors:
            movie.directors.clear()
            for o in metadata.directors:
                director = movie.directors.new()
                director.name = o
                director.photo = o.photo

        for attr in ["posters", "art"]:
            data = getattr(metadata, attr)
            if data:
                container = getattr(movie, attr)
                container.validate_keys([])
                for r in data:
                    if r.thumb:
                        klass = Proxy.Preview
                        thumb_url = r.thumb
                    else:
                        klass = Proxy.Media
                        thumb_url = r
                    try:
                        resp = requests.get(thumb_url)
                        resp.raise_for_status()
                    except Exception as e:
                        Log.Exception("Failed to download %s from %s: %s",
                                      attr, thumb_url, e)
                        continue
                    container[r] = klass(resp.content)
                    break  # only use the first valid image

        if metadata.trailers:
            trailer = TrailerObject(
                file=metadata.trailers[0],
                thumb=metadata.trailers[0].thumb
            )
            movie.extras.add(trailer)

        title_sort = metadata.title_sort or metadata.title
        if title_sort:
            movie.title_sort = self.uncensor_text(title_sort, lang)
        if metadata.genres:
            movie.genres.clear()
            for g in metadata.genres:
                movie.genres.add(g)
        if metadata.labels:
            labels = {self.uncensor_text(l, lang) for l in metadata.labels}
            tags.update(labels)
            similar.update(labels)
        if metadata.summary:
            movie.summary = metadata.summary
        if metadata.rating is not None:
            movie.rating = metadata.rating

        if similar:
            movie.similar.clear()
            for s in similar:
                movie.similar.add(s)
        if tags:
            movie.tags.clear()
            for t in tags:
                movie.tags.add(t)

    @classmethod
    def normalize_lang(cls, lang):
        if lang != Locale.Language.NoLanguage and lang in cls.languages:
            return lang
        return Locale.Language.Japanese

    CENSORED_SYMBOLS = [u"\u25cb", u"\u25ef", u"\u3007"]  # ○ ◯ 〇
    CANONICAL_CENSORED = u"\u25cf"  # ●
    censored_words_cache = None

    @staticmethod
    def uncensor_text(title, lang):
        if not title:
            return title
        if JAVAgent.censored_words_cache is None:
            try:
                raw = Resource.Load('censored_words.ja.json')
                JAVAgent.censored_words_cache = json.loads(raw)
            except Exception as e:
                Log.Exception("Failed to load censored words: %s", e)
                return title
        for symbol in JAVAgent.CENSORED_SYMBOLS:
            title = title.replace(symbol, JAVAgent.CANONICAL_CENSORED)
        for censored, replacement in JAVAgent.censored_words_cache.items():
            title = title.replace(censored, replacement)
        return title

    cached_agents = None  # type: list | None

    @property
    def agents(self):
        """Return enabled agents sorted by weight (highest first).

        Returns:
            list[BaseAgent]: Enabled agents sorted by weight descending.
        """
        if self.cached_agents is None:
            self.cached_agents = []
            for cls in dir(agents):
                if not isinstance(getattr(agents, cls), type):
                    continue
                if not issubclass(getattr(agents, cls), BaseAgent):
                    continue
                agent = getattr(agents, cls)(Prefs)
                if not agent.name:
                    continue
                self.cached_agents.append(agent)
        return sorted([a for a in self.cached_agents if a.enabled],
                      key=lambda a: a.weight, reverse=True)


class SearchResultCollection(list):
    def Append(self, obj):
        self.append(obj)


class PlexLogHandler(logging.Handler):
    def emit(self, record):
        try:
            agent_name = record.name
            if agent_name.startswith("agents."):
                agent_name = agent_name[len("agents."):]
            msg = u"[%s] %s" % (agent_name, record.getMessage())
            if record.exc_info:
                Log.Exception(msg)
            elif record.levelno >= logging.CRITICAL:
                Log.Critical(msg)
            elif record.levelno >= logging.ERROR:
                Log.Error(msg)
            elif record.levelno >= logging.WARNING:
                Log.Warn(msg)
            elif record.levelno >= logging.INFO:
                Log.Info(msg)
            else:
                Log.Debug(msg)
            if getattr(record, "stack_info", None):
                Log.Stack()
        except Exception:
            self.handleError(record)


def log_prefs():
    prefs = [(key, Prefs[key]) for key in [
        "series_as_collection",
        "proxy",
        "flaresolverr_url",
        "user_agent",
        "javlibrary_enabled",
        "javlibrary_cf_clearance",
        "dmm_enabled",
        "mgstage_enabled",
        "seesaawiki_enabled",
        "gfriends_enabled",
        "warashipornstars_enabled",
    ]]
    Log.Info("Current preferences: %s", prefs)


def is_legacy_metadata_id(metadata_id):
    """Return True if *metadata_id* uses the legacy format.

    Legacy formats are:

    * bare video code with no separator: ``ABC-123``
    * old comma-separated format: ``ABC-123,agent.id``
    """
    return "," in metadata_id


def parse_metadata_id(metadata_id):
    """
    Parse a composite metadata ID string.

    The canonical format uses a pipe as the first separator:

        {video_code}|{agent_name1}.{agent_id1};{agent_name2}.{agent_id2};...

    For backward compatibility the legacy comma-separated format is also
    accepted:

        {video_code},{agent_name1}.{agent_id1};{agent_name2}.{agent_id2};...

    A bare video code with no separator is also accepted.

    Args:
        metadata_id (str): The raw metadata ID.

    Returns:
        tuple[str, dict[str, str]]: ``(video_code, agent_dict)`` where
        *agent_dict* maps agent names to their IDs.
    """
    if "|" in metadata_id:
        part = metadata_id.split("|", 1)
    elif "," in metadata_id:
        part = metadata_id.split(",", 1)
    else:
        part = [metadata_id]
    video_code = part[0]
    agent_dict = OrderedDict()
    if len(part) > 1 and part[1]:
        for segment in part[1].split(";"):
            if "." in segment:
                name, aid = segment.split(".", 1)
                agent_dict[name] = aid
    return video_code, agent_dict


def update_metadata_id(metadata_id, agent_name, agent_id):
    video_code, agent_ids = parse_metadata_id(metadata_id)
    agent_ids[agent_name] = agent_id
    segments = ";".join("%s.%s" % (n, i) for n, i in agent_ids.items())
    return "%s|%s" % (video_code, segments)
