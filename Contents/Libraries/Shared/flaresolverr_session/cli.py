#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import base64
import json
import os
import sys
import time
import warnings

from flaresolverr_session.rpc import RPC
from flaresolverr_session.exceptions import (
    FlareSolverrChallengeError,
    FlareSolverrResponseError,
)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    main_parser = _build_main_parser()

    # Handle top-level -h/--help when no command specified
    if not argv or argv == ["-h"] or argv == ["--help"]:
        main_parser.print_help()
        return 0

    first_args, remaining = main_parser.parse_known_args(argv)

    # Determine command from remaining args.
    if remaining and remaining[0] in ("session", "request"):
        command = remaining.pop(0)
    else:
        command = "request"

    rpc = RPC(first_args.flaresolverr_url)
    try:
        if command == "session":
            parser = _build_session_parser()
            args = parser.parse_args([command] + remaining)
            res = _handle_session(rpc, args)
        else:
            parser = _build_request_parser()
            args = parser.parse_args([command] + remaining)
            res = _handle_request(rpc, args)
            _truncate_response_body(res)

        format_output(res)
        return 0
    except FlareSolverrResponseError as exc:
        format_output(exc.response_data, file=sys.stderr)
        return 1


def _build_main_parser():
    parser = argparse.ArgumentParser(
        prog="flaresolverr-cli",
        description="Interact with a FlareSolverr instance",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "commands:\n"
            "  session             Manage FlareSolverr sessions\n"
            "  request (default)   Send an HTTP request through FlareSolverr\n\n"
            "Run 'flaresolverr-cli session --help' or "
            "'flaresolverr-cli request --help' for more information."
        ),
    )
    parser.add_argument(
        "-f",
        "--flaresolverr",
        dest="flaresolverr_url",
        default=os.environ.get("FLARESOLVERR_URL", "http://localhost:8191/v1"),
        help=(
            "FlareSolverr API endpoint (default: FLARESOLVERR_URL "
            "env var or http://localhost:8191/v1)"
        ),
    )
    return parser


def _build_session_parser():
    parser = argparse.ArgumentParser(
        prog="flaresolverr-cli",
        description="Interact with a FlareSolverr instance",
    )
    subparsers = parser.add_subparsers(dest="command")
    sub_parser = subparsers.add_parser(
        "session",
        help="Manage FlareSolverr sessions",
    )
    session_sub = sub_parser.add_subparsers(dest="session_action")
    session_sub.required = True

    # session create
    create_parser = session_sub.add_parser("create", help="Create a session")
    create_parser.add_argument(
        "name",
        nargs="+",
        help="One or more session names to create",
    )
    create_parser.add_argument(
        "--proxy",
        default=None,
        help="Proxy URL (e.g. http://proxy:8080)",
    )

    # session list
    session_sub.add_parser("list", help="List active sessions")

    # session destroy
    destroy_parser = session_sub.add_parser("destroy", help="Destroy a session")
    destroy_parser.add_argument(
        "session_id",
        help="Session identifier to destroy",
    )

    # session clear
    session_sub.add_parser("clear", help="Destroy all sessions")

    return parser


def _build_request_parser():
    parser = argparse.ArgumentParser(
        prog="flaresolverr-cli",
        description="Send an HTTP request through FlareSolverr",
    )
    subparsers = parser.add_subparsers(dest="command")
    sub_parser = subparsers.add_parser(
        "request",
        help="Send an HTTP request through FlareSolverr",
    )

    sub_parser.add_argument(
        "url",
        help="URL to request",
    )
    sub_parser.add_argument(
        "-m",
        "--method",
        default=None,
        choices=["GET", "POST"],
        help="HTTP method (default: GET, or POST when -d is given)",
    )
    sub_parser.add_argument(
        "-s",
        "--session",
        "--session-id",
        dest="session_id",
        default=None,
        help="FlareSolverr session id to use",
    )
    sub_parser.add_argument(
        "-d",
        "--data",
        default=None,
        help="POST data (x-www-form-urlencoded)",
    )
    sub_parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        default=None,
        help="Write response body to file",
    )
    sub_parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=None,
        help="Request timeout in milliseconds (default: 60000)",
    )
    sub_parser.add_argument(
        "--proxy",
        default=None,
        help="Proxy URL (e.g. http://proxy:8080)",
    )
    sub_parser.add_argument(
        "--session-ttl-minutes",
        dest="session_ttl_minutes",
        type=int,
        default=None,
        help="Auto-rotate sessions older than this many minutes",
    )
    # Return only cookies flag (previously -c/--cookies)
    sub_parser.add_argument(
        "-c",
        "--cookies-only",
        dest="cookies_only",
        action="store_true",
        default=False,
        help="Return only cookies, omitting the response body",
    )
    sub_parser.add_argument(
        "--cookies",
        dest="cookies",
        action="append",
        default=None,
        help="Provide cookie as name=value. Can be repeated.",
    )
    sub_parser.add_argument(
        "--screenshot",
        dest="screenshot",
        default=None,
        help="Write PNG screenshot of the final rendered page after all challenges and waits are completed to given path",
    )
    sub_parser.add_argument(
        "--wait",
        dest="wait_in_seconds",
        type=int,
        default=None,
        help="Extra seconds to wait after the challenge is solved",
    )
    sub_parser.add_argument(
        "--disable-media",
        dest="disable_media",
        action="store_true",
        default=False,
        help="Disable loading images, CSS and fonts",
    )
    sub_parser.add_argument(
        "--retries",
        dest="retries",
        type=int,
        default=0,
        help=(
            "Number of times to retry on a FlareSolverr challenge timeout "
            "(default: 0, disabled). The FlareSolverr timeout (-t/--timeout) "
            "is applied per attempt, not across all attempts combined."
        ),
    )

    return parser


def _handle_session(rpc, args):
    action = args.session_action

    if action == "create":
        names = getattr(args, "name", None)
        proxy = getattr(args, "proxy", None)
        return [rpc.session.create(session_id=n, proxy=proxy) for n in names]
    elif action == "list":
        return rpc.session.list()
    elif action == "destroy":
        return rpc.session.destroy(args.session_id)
    elif action == "clear":
        payload = rpc.session.list()
        return [rpc.session.destroy(s) for s in payload["sessions"]]
    else:
        raise ValueError("Unknown session action: %s" % action)


def _handle_request(rpc, args):
    """Send a request through FlareSolverr and display the result.

    Parameters:
        rpc (RPC): RPC client instance.
        args (argparse.Namespace): Parsed CLI arguments.
    """
    method = getattr(args, "method", None)
    data = getattr(args, "data", None)
    if method is None:
        method = "POST" if data else "GET"

    kwargs = {}
    session_id = getattr(args, "session_id", None)
    if session_id:
        kwargs["session_id"] = session_id
    timeout = getattr(args, "timeout", None)
    if timeout:
        kwargs["max_timeout"] = timeout
    proxy = getattr(args, "proxy", None)
    if proxy:
        kwargs["proxy"] = proxy
    elif os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY"):
        warnings.warn(
            "Detected HTTP_PROXY or HTTPS_PROXY environment variable, "
            "it will be ignored, use --proxy option instead",
            stacklevel=2,
        )
    session_ttl_minutes = getattr(args, "session_ttl_minutes", None)
    if session_ttl_minutes is not None:
        kwargs["session_ttl_minutes"] = session_ttl_minutes
    # Return-only flag
    if getattr(args, "cookies_only", False):
        kwargs["return_only_cookies"] = True
    # Explicit cookies passed to forward to FlareSolverr
    cookies = getattr(args, "cookies", None)
    if cookies:
        parsed = []
        for c in cookies:
            parts = c.split("=", 1)
            if len(parts) == 2:
                name, value = parts[0], parts[1]
            else:
                raise ValueError("Invalid cookie format: %s (expected name=value)" % c)
            parsed.append({"name": name, "value": value})
        kwargs["cookies"] = parsed
    screenshot_path = getattr(args, "screenshot", None)
    if screenshot_path:
        kwargs["return_screenshot"] = True
    wait_in_seconds = getattr(args, "wait_in_seconds", None)
    if wait_in_seconds is not None:
        kwargs["wait_in_seconds"] = wait_in_seconds
    if getattr(args, "disable_media", False):
        kwargs["disable_media"] = True

    retries = getattr(args, "retries", 0)
    attempts = 0
    while True:
        try:
            if method == "POST":
                result = rpc.request.post(args.url, data=data, **kwargs)
            else:
                result = rpc.request.get(args.url, **kwargs)
            break
        except FlareSolverrChallengeError:
            if attempts >= retries:
                raise
            attempts += 1
            time.sleep(1)

    # Write body to file if requested
    output_file = getattr(args, "output_file", None)
    if output_file:
        body = result.get("solution", {}).get("response", "")
        if isinstance(body, bytes):
            content = body
        else:
            content = body.encode("utf-8")
        with open(output_file, "wb") as f:
            f.write(content)

    # Write screenshot to file if requested
    if screenshot_path:
        screenshot_b64 = result["solution"]["screenshot"]
        data = base64.b64decode(screenshot_b64)
        with open(screenshot_path, "wb") as f:
            f.write(data)

    return result


def _truncate_response_body(data, max_length=200):
    solution = data["solution"]
    body = solution.get("response", "")
    if len(body) > max_length:
        solution["response"] = body[:max_length] + "...[%d letters]" % len(body)
    if solution.get("screenshot"):
        solution["screenshot"] = "[%d bytes of PNG data]" % len(solution["screenshot"])
    return data


def format_output(data, file=None):
    if file is None:
        file = sys.stdout
    print(json.dumps(data, indent=2), file=file)


if __name__ == "__main__":
    sys.exit(main())
