# -*- coding: utf-8 -*-

import requests

__all__ = [
    "FlareSolverrError",
    "FlareSolverrResponseError",
    "FlareSolverrChallengeError",
    "FlareSolverrUnsupportedMethodError",
]


class FlareSolverrError(requests.RequestException):
    """Base exception for FlareSolverr errors."""


class FlareSolverrResponseError(FlareSolverrError):
    """Raised when FlareSolverr returns a non-ok response.

    Attributes:
        message (str): The error message from FlareSolverr.
        response_data (dict or None): The original FlareSolverr response dict.
    """

    def __init__(self, message, response_data=None, **kwargs):
        super(FlareSolverrResponseError, self).__init__(message, **kwargs)
        self.message = message or ""
        self.response_data = response_data


class FlareSolverrChallengeError(FlareSolverrResponseError):
    """Raised when a challenge could not be solved."""


class FlareSolverrUnsupportedMethodError(FlareSolverrError):
    """Raised when an unsupported HTTP method or content type is used."""
