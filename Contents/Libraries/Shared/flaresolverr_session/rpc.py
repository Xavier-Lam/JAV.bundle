# -*- coding: utf-8 -*-

import json
import os

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import requests

from flaresolverr_session.exceptions import (
    FlareSolverrChallengeError,
    FlareSolverrResponseError,
)

__all__ = [
    "RPC",
    "SessionCommand",
    "RequestCommand",
]


class RPC(object):
    """RPC client for FlareSolverr.

    Provides two sub-command namespaces:

    - :attr:`session` -- :class:`SessionCommand` for session management.
    - :attr:`request` -- :class:`RequestCommand` for HTTP requests.

    Parameters:
        flaresolverr_url (str): The FlareSolverr API endpoint
            (e.g. ``"http://localhost:8191/v1"``).
        api_session (requests.Session or None): Session object used to
            communicate with the FlareSolverr instance.
    """

    def __init__(self, flaresolverr_url=None, api_session=None):
        if flaresolverr_url is None:
            flaresolverr_url = os.environ.get(
                "FLARESOLVERR_URL", "http://localhost:8191/v1"
            )
        if api_session is None:
            api_session = requests.Session()

        self._flaresolverr_url = flaresolverr_url
        self._api_session = api_session
        self.session = SessionCommand(self)
        self.request = RequestCommand(self)

    def send(self, payload):
        """Send a JSON payload to the FlareSolverr endpoint.

        Parameters:
            payload (dict): The JSON-serialisable payload to send.

        Returns:
            dict: The parsed JSON response from FlareSolverr.

        Raises:
            FlareSolverrResponseError: If the response status is
                not ``"ok"``.
        """
        headers = {"Content-Type": "application/json"}
        resp = self._api_session.post(
            self._flaresolverr_url,
            headers=headers,
            data=json.dumps(payload),
        )
        data = resp.json()
        status = data.get("status", "")
        if status != "ok":
            raise FlareSolverrResponseError(data.get("message"), data, response=resp)
        return data


class SessionCommand(object):
    """Manage FlareSolverr browser sessions.

    Parameters:
        rpc (RPC): The parent RPC instance
    """

    def __init__(self, rpc):
        self._rpc = rpc

    def create(self, session_id=None, proxy=None):
        """Create a new FlareSolverr browser session.

        Parameters:
            session_id (str or None): An optional identifier for the
                session.  When *None*, FlareSolverr generates one.
            proxy (str, dict or None): Proxy specification.
                When a *str*, interpreted as a URL
                (e.g. ``"http://proxy:8080"``).
                When a *dict*, should contain ``"url"`` and optionally
                ``"username"`` and ``"password"`` keys.

        Returns:
            dict: The JSON response from FlareSolverr with keys:

                - **status** (*str*) -- ``"ok"`` on success.
                - **message** (*str*) -- Human-readable message
                  (e.g. ``"Session created successfully."``).
                - **session** (*str*) -- The session identifier.
                - **version** (*str*) -- FlareSolverr server version.
                - **startTimestamp** (*int*) -- Request start
                  timestamp (ms).
                - **endTimestamp** (*int*) -- Request end
                  timestamp (ms).
        """
        payload = {"cmd": "sessions.create"}
        if session_id:
            payload["session"] = session_id
        if proxy:
            if isinstance(proxy, dict):
                payload["proxy"] = proxy
            else:
                payload["proxy"] = {"url": proxy}
        return self._rpc.send(payload)

    def list(self):
        """List all active FlareSolverr browser sessions.

        Returns:
            dict: The JSON response from FlareSolverr with keys:

                - **status** (*str*) -- ``"ok"`` on success.
                - **message** (*str*) -- Human-readable message.
                - **sessions** (*list of str*) -- List of active
                  session identifiers.
                - **version** (*str*) -- FlareSolverr server version.
                - **startTimestamp** (*int*) -- Request start
                  timestamp (ms).
                - **endTimestamp** (*int*) -- Request end
                  timestamp (ms).
        """
        payload = {"cmd": "sessions.list"}
        return self._rpc.send(payload)

    def destroy(self, session_id):
        """Destroy an existing FlareSolverr browser session.

        Parameters:
            session_id (str): The session identifier to destroy.

        Returns:
            dict: The JSON response from FlareSolverr with keys:

                - **status** (*str*) -- ``"ok"`` on success.
                - **message** (*str*) -- Human-readable message
                  (e.g. ``"The session has been removed."``).
                - **version** (*str*) -- FlareSolverr server version.
                - **startTimestamp** (*int*) -- Request start
                  timestamp (ms).
                - **endTimestamp** (*int*) -- Request end
                  timestamp (ms).
        """
        payload = {
            "cmd": "sessions.destroy",
            "session": session_id,
        }
        return self._rpc.send(payload)


class RequestCommand(object):
    """Send HTTP requests through a FlareSolverr instance.

    Parameters:
        rpc (RPC): The parent RPC instance.
    """

    DEFAULT_TIMEOUT = 60000

    def __init__(self, rpc):
        self._rpc = rpc

    def get(
        self,
        url,
        session_id=None,
        max_timeout=None,
        proxy=None,
        cookies=None,
        session_ttl_minutes=None,
        return_only_cookies=False,
        return_screenshot=False,
        wait_in_seconds=None,
        disable_media=False,
        tabs_till_verify=None,
    ):
        """Send a GET request through FlareSolverr.

        Parameters:
            url (str): Target URL.
            session_id (str or None): Use an existing FlareSolverr
                session.  When *None*, a temporary session is created
                for this request only.
            max_timeout (int or None): Maximum time in **ms** to wait
                for the challenge to be solved.  Defaults to 60000.
            proxy (str, dict or None): Proxy specification.
                A *str* is treated as a URL
                (e.g. ``"http://proxy:8080"``).  A *dict* should have
                a ``"url"`` key and optional ``"username"`` /
                ``"password"`` keys.  **Ignored when** ``session_id``
                **is set** (use a session-level proxy instead).
            cookies (list of dict or None): Extra cookies to send to
                the headless browser.  Each dict should have ``"name"``
                and ``"value"`` keys.
            session_ttl_minutes (int or None): When set, FlareSolverr
                automatically rotates sessions that have exceeded this
                TTL (in minutes).
            return_only_cookies (bool): When *True*, only the cookies
                are returned; response body, headers and other fields
                are omitted.  Default *False*.
            return_screenshot (bool): When *True*, a Base64-encoded PNG
                screenshot of the final page is included in the
                response as ``solution.screenshot``.  Default *False*.
            wait_in_seconds (int or None): Extra seconds to wait after
                the challenge is solved before returning the result.
                Useful for pages with dynamic content.
            disable_media (bool): When *True*, images, CSS and fonts
                are not loaded, speeding up navigation.  Default *False*.
            tabs_till_verify (int or None): Number of ``Tab`` presses
                needed to focus the Turnstile CAPTCHA widget.  The
                solved token is returned in
                ``solution.turnstile_token``.

        Returns:
            dict: The JSON response from FlareSolverr with keys:

                - **status** (*str*) -- ``"ok"`` on success.
                - **message** (*str*) -- Human-readable message
                  (e.g. ``"Challenge solved!"`` or
                  ``"Challenge not detected!"``).
                - **solution** (*dict*) -- Solution details:

                  - **url** (*str*) -- Final URL after redirects.
                  - **status** (*int*) -- HTTP status code.
                  - **headers** (*dict*) -- Response headers.
                  - **response** (*str*) -- Response body (HTML).
                    Empty when ``returnOnlyCookies=True``.
                  - **cookies** (*list of dict*) -- Cookies.  Each
                    item has ``"name"``, ``"value"``, ``"domain"``,
                    ``"path"``, ``"expires"``, ``"size"``,
                    ``"httpOnly"``, ``"secure"``, ``"session"``,
                    ``"sameSite"`` keys.
                  - **userAgent** (*str*) -- Browser User-Agent.
                  - **screenshot** (*str or None*) -- Base64-encoded
                    PNG screenshot (only when ``returnScreenshot``
                    is *True*).
                  - **turnstile_token** (*str or None*) -- Solved
                    Turnstile token (only when ``tabs_till_verify``
                    is set).

                - **version** (*str*) -- FlareSolverr server version.
                - **startTimestamp** (*int*) -- Request start
                  timestamp (ms).
                - **endTimestamp** (*int*) -- Request end
                  timestamp (ms).
        """
        return self._request(
            "request.get",
            url,
            session_id=session_id,
            max_timeout=max_timeout,
            proxy=proxy,
            cookies=cookies,
            session_ttl_minutes=session_ttl_minutes,
            return_only_cookies=return_only_cookies,
            return_screenshot=return_screenshot,
            wait_in_seconds=wait_in_seconds,
            disable_media=disable_media,
            tabs_till_verify=tabs_till_verify,
        )

    def post(
        self,
        url,
        data=None,
        session_id=None,
        max_timeout=None,
        proxy=None,
        cookies=None,
        session_ttl_minutes=None,
        return_only_cookies=False,
        return_screenshot=False,
        wait_in_seconds=None,
        disable_media=False,
    ):
        """Send a POST request through FlareSolverr.

        Only ``application/x-www-form-urlencoded`` POST data is
        supported (FlareSolverr limitation).

        Parameters:
            url (str): Target URL.
            data (str, dict or None): POST body.  A *dict* is
                automatically URL-encoded.
            session_id (str or None): Use an existing session.
            max_timeout (int or None): Max timeout in **ms**.
            proxy (str, dict or None): Proxy specification.
                **Ignored when** ``session_id`` **is set**.
            cookies (list of dict or None): Extra cookies.
            session_ttl_minutes (int or None): Auto-rotate sessions
                older than this many minutes.
            return_only_cookies (bool): Omit body / headers from
                the response.  Default *False*.
            return_screenshot (bool): Include a Base64 PNG screenshot
                in ``solution.screenshot``.  Default *False*.
            wait_in_seconds (int or None): Extra wait time after
                challenge is solved.
            disable_media (bool): Skip loading images, CSS, fonts.
                Default *False*.

        Returns:
            dict: Same structure as :meth:`get`.
        """
        return self._request(
            "request.post",
            url,
            data=data,
            session_id=session_id,
            max_timeout=max_timeout,
            proxy=proxy,
            cookies=cookies,
            session_ttl_minutes=session_ttl_minutes,
            return_only_cookies=return_only_cookies,
            return_screenshot=return_screenshot,
            wait_in_seconds=wait_in_seconds,
            disable_media=disable_media,
        )

    def _request(
        self,
        cmd,
        url,
        data=None,
        session_id=None,
        max_timeout=None,
        proxy=None,
        cookies=None,
        session_ttl_minutes=None,
        return_only_cookies=False,
        return_screenshot=False,
        wait_in_seconds=None,
        disable_media=False,
        tabs_till_verify=None,
    ):
        """Build and send a request payload to FlareSolverr.

        Parameters:
            cmd (str): FlareSolverr command
                (``"request.get"`` or ``"request.post"``).
            url (str): Target URL.
            data (str, dict or None): POST data (``request.post`` only).
            session_id (str or None): FlareSolverr session id.
            max_timeout (int or None): Max timeout in ms.
            proxy (str, dict or None): Proxy specification.
            cookies (list of dict or None): Cookies to send.
            session_ttl_minutes (int or None): Session TTL in minutes.
            return_only_cookies (bool): Return only cookies.
            return_screenshot (bool): Capture a screenshot.
            wait_in_seconds (int or None): Wait after challenge.
            disable_media (bool): Disable media loading.
            tabs_till_verify (int or None): Tab presses to verify
                Turnstile (``request.get`` only).

        Returns:
            dict: The JSON response from FlareSolverr.
        """
        payload = {
            "cmd": cmd,
            "url": url,
            "maxTimeout": max_timeout or self.DEFAULT_TIMEOUT,
        }
        if session_id:
            payload["session"] = session_id
        if proxy:
            if isinstance(proxy, dict):
                payload["proxy"] = proxy
            else:
                payload["proxy"] = {"url": proxy}
        if cookies:
            payload["cookies"] = cookies
        if session_ttl_minutes is not None:
            payload["session_ttl_minutes"] = session_ttl_minutes
        if return_only_cookies:
            payload["returnOnlyCookies"] = True
        if return_screenshot:
            payload["returnScreenshot"] = True
        if wait_in_seconds is not None:
            payload["waitInSeconds"] = wait_in_seconds
        if disable_media:
            payload["disableMedia"] = True
        if tabs_till_verify is not None and cmd == "request.get":
            payload["tabs_till_verify"] = tabs_till_verify
        if data is not None and cmd == "request.post":
            if isinstance(data, dict):
                data = urlencode(data)
            payload["postData"] = data
        elif cmd == "request.post":
            # FlareSolverr requires postData for request.post; send empty string
            payload["postData"] = ""
        try:
            return self._rpc.send(payload)
        except FlareSolverrResponseError as e:
            msg = e.message.lower()
            if "captcha" in msg or "timeout" in msg or "challenge" in msg:
                raise FlareSolverrChallengeError(
                    e.message, e.response_data, response=e.response
                )
            raise
