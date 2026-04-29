from __future__ import annotations

import base64
import functools
import logging
from typing import Callable, TypeVar

from flask import Response, current_app, request

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., object])


def require_basic(f: F) -> F:
    """HTTP Basic for browser + curl; does not log passwords."""

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        cfg = current_app.config["UPLOAD_WEB"]
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Basic "):
            log.info("auth_missing path=%s ip=%s", request.path, request.remote_addr)
            return _unauthorized()
        try:
            try:
                raw = base64.b64decode(auth[6:], validate=True).decode("utf-8")
            except TypeError:
                raw = base64.b64decode(auth[6:]).decode("utf-8")
            username, _, password = raw.partition(":")
        except (OSError, UnicodeError, ValueError):
            log.info("auth_bad_encoding path=%s ip=%s", request.path, request.remote_addr)
            return _unauthorized()
        if username != cfg.basic_user or password != cfg.upload_web_password:
            log.info(
                "auth_failed user=%s path=%s ip=%s",
                username,
                request.path,
                request.remote_addr,
            )
            return _unauthorized()
        return f(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def _unauthorized() -> Response:
    return Response(
        "Unauthorized\n",
        401,
        {"WWW-Authenticate": 'Basic realm="Upload"'},
    )
