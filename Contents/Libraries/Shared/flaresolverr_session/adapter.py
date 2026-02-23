# -*- coding: utf-8 -*-

import logging
import time
import warnings

try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse

from requests.adapters import BaseAdapter, HTTPAdapter
from requests.cookies import RequestsCookieJar
from requests.utils import select_proxy

from flaresolverr_session.detection import is_cloudflare_challenge
from flaresolverr_session.rpc import RPC


logger = logging.getLogger(__name__)


class Adapter(BaseAdapter):
    """A ``requests`` transport adapter that retries requests blocked by
    Cloudflare by solving challenges through FlareSolverr.

    Normal (non-challenged) requests are forwarded directly through the
    *base_adapter*.  When a Cloudflare challenge is detected the adapter
    automatically:

    1. Sends the *challenge_url* (or the blocked URL) to FlareSolverr.
    2. Caches the ``cf_clearance`` cookie and User-Agent per site.
    3. Retries the original request with the obtained cookie and UA.

    Parameters:
        flaresolverr_url (str or None): The FlareSolverr API endpoint.
            Ignored when *rpc* is provided.
        rpc (flaresolverr_session.rpc.RPC or None):
            A pre-configured :class:`~flaresolverr_session.rpc.RPC`
            instance.  When provided, *flaresolverr_url* is ignored.
        challenge_url (str or None): URL to use for solving challenges.
            When *None*, the adapter sends the blocked URL itself for
            challenge solving.  Can be an absolute path without domain
            (e.g. ``"/"``) — it will be combined with the domain of
            the blocked URL.
        base_adapter (requests.adapters.BaseAdapter or None): The
            adapter used to perform actual HTTP requests.
    """

    def __init__(
        self,
        flaresolverr_url=None,
        rpc=None,
        challenge_url=None,
        base_adapter=None,
    ):
        super(Adapter, self).__init__()

        if rpc is not None and flaresolverr_url is not None:
            warnings.warn(
                "Both 'rpc' and 'flaresolverr_url' are provided. "
                "The 'rpc' instance will be used and "
                "'flaresolverr_url' will be ignored.",
                stacklevel=2,
            )
        if not rpc:
            rpc = RPC(flaresolverr_url)
        self._rpc = rpc
        self._challenge_url = challenge_url

        if base_adapter is None:
            base_adapter = HTTPAdapter()
        self._base_adapter = base_adapter

        # Per-site caches keyed by hostname.
        self._cf_cookies = {}
        self._user_agents = {}

    def send(
        self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
    ):
        kwargs = dict(
            stream=stream,
            timeout=timeout,
            verify=verify,
            cert=cert,
            proxies=proxies,
        )

        self._log(logging.DEBUG, "Adapter received request", request)
        self._prepare_request(request)
        response = self._base_adapter.send(request, **kwargs)

        if is_cloudflare_challenge(response):
            self._log(logging.DEBUG, "Challenge detected", request)
            self._solve_challenge(request.url, proxies=proxies)
            self._prepare_request(request)
            response = self._base_adapter.send(request, **kwargs)
            if is_cloudflare_challenge(response):
                self._log(
                    logging.WARNING,
                    "Challenge still present after solve attempt",
                    request,
                )
            else:
                self._log(logging.DEBUG, "Challenge has been solved", request)

        return response

    def _prepare_request(self, request):
        parsed = urlparse(request.url)
        domain = _get_root_domain(parsed.hostname)

        jar = self._cf_cookies.get(domain)
        if jar:
            # Merge cookies into the Cookie header.
            existing = RequestsCookieJar()
            # Parse existing Cookie header if present.
            cookie_header = request.headers.get("Cookie")
            if cookie_header:
                for pair in cookie_header.split(";"):
                    pair = pair.strip()
                    if "=" in pair:
                        name, value = pair.split("=", 1)
                        existing.set(name.strip(), value.strip())
            for cookie in jar:
                if cookie.expires is not None and cookie.expires < time.time():
                    continue
                existing.set(cookie.name, cookie.value)

            # Re-build Cookie header.
            cookie_str = "; ".join("%s=%s" % (c.name, c.value) for c in existing)
            if cookie_str:
                request.headers["Cookie"] = cookie_str

        user_agent = self._user_agents.get(domain)
        if user_agent:
            request.headers["User-Agent"] = user_agent

    def _solve_challenge(self, original_url, proxies=None):
        challenge_url = self._get_challenge_url(original_url)
        rpc_kwargs = {
            "url": challenge_url,
            "return_only_cookies": True,
            "disable_media": True,
        }

        if proxies:
            proxy_url = select_proxy(challenge_url, proxies)
            if proxy_url:
                rpc_kwargs["proxy"] = {"url": proxy_url}

        data = self._rpc.request.get(**rpc_kwargs)
        solution = data.get("solution", {})

        # Cloudflare cookies are scoped per zone (root domain)
        domain = _get_root_domain(urlparse(original_url).hostname)

        user_agent = solution.get("userAgent")
        if user_agent:
            self._user_agents[domain] = user_agent

        jar = RequestsCookieJar()
        for cd in solution.get("cookies", []):
            if cd.get("name") == "cf_clearance":
                jar.set(
                    cd["name"],
                    cd.get("value", ""),
                    expires=cd.get("expiry"),
                )
                break
        self._cf_cookies[domain] = jar

    def _get_challenge_url(self, original_url):
        if self._challenge_url is None:
            return original_url

        if self._challenge_url.startswith("/"):
            parsed = urlparse(original_url)
            return urlunparse(
                (parsed.scheme, parsed.netloc, self._challenge_url, "", "", "")
            )

        return self._challenge_url

    def _log(self, level, message, request):
        logger.log(
            level,
            "%s - [%s] %s",
            message,
            request.method,
            request.url,
        )


def _get_root_domain(hostname):
    parts = hostname.split(".")
    return ".".join(parts[-2:])
