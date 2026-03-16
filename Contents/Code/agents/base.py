# coding=utf-8

import logging

import flaresolverr_session
import requests


class FlareSolverrSessionCache(object):
    flaresolverr_session = None  # type: flaresolverr_session.Session
    flaresolverr_url = ""


flaresolverr_session_cache = FlareSolverrSessionCache()


class BaseAgent(object):
    """
    Base class for all agents.
    """

    name = None  # type: str
    weight = 0  # type: int

    def __init__(self, prefs):
        self.prefs = prefs

    @property
    def enabled(self):
        """
        Whether the agent is enabled in user preferences.

        Returns:
            bool: True if the agent is enabled
        """
        try:
            return bool(self.prefs[self.name.lower() + "_enabled"])
        except Exception:
            return True  # unconfigurable agents are enabled

    def validate_resource(self, url, expected_mime_type=None):
        """
        Validate that the resource at the given URL has the expected MIME type.

        Args:
            url (str): The URL of the resource to validate.
            expected_mime_type (str): The expected MIME type of the resource.

        Returns:
            bool: True if the resource is valid, False otherwise.
        """
        try:
            resp = requests.head(url, allow_redirects=True)
            resp.raise_for_status()
            actual_mime_type = resp.headers.get("Content-Type", "")
        except Exception as e:
            self.logger.warning("Failed to validate resource %r: %s", url, e)
            return False
        if expected_mime_type and not actual_mime_type.startswith(expected_mime_type):
            self.logger.warning("Resource %r has unexpected MIME type: expected %r, got %r",
                                url, expected_mime_type, actual_mime_type)
            return False
        return True

    requests_session = None     # type: requests.Session

    def create_session(self):
        """
        Create and return a new :class:`requests.Session`.

        Sub-classes that need special session initialization (e.g. setting
        cookies) should override this method.

        Returns:
            requests.Session: A freshly created session.
        """
        return requests.Session()

    @property
    def session(self):
        """
        Return a cached :class:`requests.Session`, recreating it when the
        proxy setting has changed since the last call.

        Returns:
            requests.Session: The cached session.
        """
        if self.requests_session is None:
            self.requests_session = self.create_session()
        self.requests_session.proxies = self.http_proxy
        self.requests_session.trust_env = not self.http_proxy
        if self.prefs["user_agent"]:
            self.requests_session.headers["User-Agent"] = self.prefs["user_agent"]
        else:
            self.requests_session.headers.pop("User-Agent", None)
        return self.requests_session

    @property
    def flaresolverr_session(self):
        """
        Return a cached :class:`flaresolverr_session.Session`, recreating it
        when the proxy or FlareSolverr URL settings have changed since the last
        call.

        Returns:
            flaresolverr_session.Session: The cached FlareSolverr session.
        """
        url = self.prefs["flaresolverr_url"] or ""
        if not url:
            flaresolverr_session_cache.flaresolverr_session = None
            flaresolverr_session_cache.flaresolverr_url = ""
            return None
        if flaresolverr_session_cache.flaresolverr_url != url:
            flaresolverr_session_cache.flaresolverr_session = flaresolverr_session.Session(
                url,
                session_id="com.plexapp.agents.jav",
                timeout=20000,
                max_retries=2,
            )
            flaresolverr_session_cache.flaresolverr_url = url
        fss = flaresolverr_session_cache.flaresolverr_session
        fss.proxies = self.http_proxy
        return fss

    @property
    def http_proxy(self):
        """
        Return the configured HTTP proxy URL, or ``None`` if not set.

        Returns:
            dict: A dictionary with "http" and "https" keys for the proxy
                  URLs, or an empty dictionary if no proxy is configured.
        """
        proxy = self.prefs["proxy"] or None
        if proxy:
            return {"http": proxy, "https": proxy}
        return {}

    @property
    def logger(self):
        """
        Return a logger for the agent.

        Returns:
            logging.Logger: The logger for the agent.
        """
        return logging.getLogger("agents").getChild(self.name)


class SearchAgent(BaseAgent):
    """
    Base class for search agents.
    """

    def guess_keywords(self, name, filename, directory):
        """
        Guess search keywords from the given media information.

        Args:
            name (str): The media title
            filename (str): The media filename
            directory (str): The media directory

        Returns:
            list[str]: The list of guessed keywords
        """
        return []

    def search(self, keywords, lang):
        """
        Search for the given keywords and language.

        Args:
            keywords (list[str]): The search keywords
            lang (str): The search language

        Returns:
            list[SearchItem]: The list of search results
        """
        raise NotImplementedError


class MetadataAgent(BaseAgent):
    """
    Base class for metadata agents.
    """

    def get_metadata(self, agent_id, video_code, lang):
        """
        Get metadata for the given agent ID, video code and language.

        Args:
            agent_id (str): The unique identifier of the agent
            video_code (str): The video code of the movie
            lang (str): The metadata language

        Returns:
            Metadata: The metadata of the movie
        """
        raise NotImplementedError

    def should_contribute_to(self, metadata, attribute, new_value):
        """
        Determine whether the agent should contribute to the given metadata
        attribute.

        Args:
            metadata (Metadata): The current metadata of the movie
            attribute (str): The name of the metadata attribute
            new_value: The new value proposed by the agent

        Returns:
            bool: True if the agent should contribute
        """
        if new_value is None:
            return False
        current_value = getattr(metadata, attribute)
        if current_value is None:
            return True
        if attribute in ["posters", "art", "themes", "trailers"]:
            return True
        return False

    def get_contribution_value(self, new_value, attribute, current_value):
        """
        Get the contribution value for the given new value, attribute and
        current value.

        Args:
            new_value: The new value proposed by the agent
            attribute (str): The name of the metadata attribute
            current_value: The current value of the metadata attribute

        Returns:
            The contribution value, which will be used to determine the final
            metadata value when multiple agents contribute to the same
            attribute.
        """
        if attribute in ["posters", "art", "themes",
                         "trailers"] and current_value:
            rv = current_value[:]
            rv.extend(new_value)
            rv.sort(key=lambda r: r.score, reverse=True)
            return rv
        return new_value


class StudioAgent(MetadataAgent):
    """
    Agent that scrapes from a studio official site.

    By default it replaces `japanese_title`, `release_date`, `studio`,
    `series`, `duration` when available.
    """

    def should_contribute_to(self, metadata, attribute, new_value):
        if attribute in [
            "japanese_title",
            "release_date",
            "studio",
            "series",
            "duration",
        ] and new_value is not None:
            return True
        return super(StudioAgent, self).should_contribute_to(
            metadata, attribute, new_value)


class PartialMetadataAgent(BaseAgent):
    """
    Base class for partial metadata agents, which only contribute to specific
    metadata attributes.
    """

    def partial_update(self, video_code, metadata, lang):
        """
        Update specific metadata attributes for the given video code and
        language.

        Args:
            video_code (str): The video code of the movie
            metadata (Metadata): The current metadata of the movie, which can
                                 be used as reference for the agent to
                                 determine whether to contribute and what
                                 value to contribute.
            lang (str): The metadata language

        Returns:
            Metadata: The metadata contributed by the agent
        """
        pass


class AvatarAgent(PartialMetadataAgent):
    """
    Agent that only contributes actress avatar photos.
    """

    def partial_update(self, video_code, metadata, lang):
        for actress in metadata.actresses:
            if actress.photo:
                continue
            try:
                avatar_url = self.get_avatar(actress, lang)
            except Exception as e:
                self.logger.exception(
                    "Failed to get avatar for actress <%s>: %s", actress, e)
                continue
            if avatar_url:
                actress.photo = avatar_url
                self.logger.debug("Got avatar URL for actress <%s>: %s",
                                  actress, avatar_url)

    def get_avatar(self, actress, lang):
        """
        Return the avatar URL for the given actress name.

        Args:
            actress (str): The actress name.
            lang (str): The language code.

        Returns:
            str or None: The avatar URL, or ``None`` if not found.
        """
        raise NotImplementedError
