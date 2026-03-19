# coding=utf-8

import re


# Pattern for standard JAV video codes (e.g. "JBD-226")
VIDEO_CODE_PATTERN = re.compile(
    r"(?:^|\s|\[|\(|\.|\\|/)"
    r"([a-zA-Z]+-[a-zA-Z]*\d+)"
    r"(?:$|\s|\]|\)|\.)",
)


def guess_video_code(text):
    """Try to extract a JAV video code (e.g. ``ABC-123``) from *text*.

    Args:
        text (str): Arbitrary string such as a filename or directory name.

    Returns:
        str or None: The upper-cased video code, or ``None``.
    """
    match = VIDEO_CODE_PATTERN.search(text)
    if match:
        return match.group(1).upper()
    return None


def get_code_group(video_code):
    """Extract the code group from a video code, e.g. "ABC" from "ABC-123".

    Args:
        video_code (str): A JAV video code.

    Returns:
        str or None: The code group, or ``None`` if the input is not a valid video code.
    """
    if not video_code:
        return None
    parts = video_code.split("-", 1)
    if len(parts) == 2:
        return parts[0].upper()
    return None
