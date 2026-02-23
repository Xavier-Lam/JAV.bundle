# -*- coding: utf-8 -*-

import re

#: HTTP status codes that Cloudflare typically returns for challenge
#: or access-denied pages.
CLOUDFLARE_STATUS_CODES = (403, 503)

#: Titles that indicate a Cloudflare (or DDoS-Guard) challenge page.
CHALLENGE_TITLES = [
    "Just a moment...",
    "DDoS-Guard",
]

#: Titles that indicate Cloudflare access-denied pages.
ACCESS_DENIED_TITLES = [
    "Access denied",
    "Attention Required! | Cloudflare",
]

#: HTML ``id`` attributes commonly found on Cloudflare challenge pages.
CHALLENGE_IDS = [
    "cf-challenge-running",
    "cf-please-wait",
    "challenge-spinner",
    "trk_jschal_js",
    "turnstile-wrapper",
    "js_info",
]

#: HTML ``class`` tokens commonly found on Cloudflare challenge pages.
CHALLENGE_CLASSES = [
    "ray_id",
    "attack-box",
    "lds-ring",
]

#: Compiled pattern for ``<title>`` extraction.
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

#: Compiled pattern matching any of the known challenge ``id`` values.
_CHALLENGE_ID_RE = re.compile(
    r"""(?:id\s*=\s*["'])(%s)["']""" % "|".join(re.escape(i) for i in CHALLENGE_IDS),
    re.IGNORECASE,
)

#: Compiled pattern matching any of the known challenge ``class`` values.
_CHALLENGE_CLASS_RE = re.compile(
    r"""(?:class\s*=\s*["'][^"']*)(%s)"""
    % "|".join(re.escape(c) for c in CHALLENGE_CLASSES),
    re.IGNORECASE,
)


def is_cloudflare_challenge(response):
    """Detect whether *response* is a Cloudflare challenge page.

    Parameters:
        response (requests.Response): The response to inspect.

    Returns:
        bool: *True* when the response looks like a Cloudflare challenge page.
    """
    if response.status_code not in CLOUDFLARE_STATUS_CODES:
        return False

    body = response.text

    title_match = _TITLE_RE.search(body)
    if title_match:
        page_title = title_match.group(1).strip()
        for title in CHALLENGE_TITLES:
            if title.lower() == page_title.lower():
                return True
        for title in ACCESS_DENIED_TITLES:
            if page_title.lower().startswith(title.lower()):
                return True

    if _CHALLENGE_ID_RE.search(body):
        return True
    if _CHALLENGE_CLASS_RE.search(body):
        return True

    return False
