"""Flask middleware for mbuzz tracking."""

import threading
from flask import Flask, request, g, Response
from typing import Optional

from ..config import config
from ..context import RequestContext, set_context, clear_context
from ..cookies import VISITOR_COOKIE, SESSION_COOKIE, VISITOR_MAX_AGE, SESSION_MAX_AGE
from ..utils.identifier import generate_id
from ..utils.session_id import generate_deterministic, generate_from_fingerprint
from ..client.session import create_session


def init_app(app: Flask) -> None:
    """Initialize mbuzz tracking for Flask app."""

    @app.before_request
    def before_request():
        if _should_skip():
            return

        visitor_id = _get_or_create_visitor_id()
        session_id = _get_or_create_session_id()
        is_new_session = SESSION_COOKIE not in request.cookies

        _set_request_context(visitor_id, session_id)
        _store_in_g(visitor_id, session_id, is_new_session)
        _create_session_if_new(visitor_id, session_id, is_new_session)

    @app.after_request
    def after_request(response: Response) -> Response:
        if not hasattr(g, "mbuzz_visitor_id"):
            return response

        _set_cookies(response)
        return response

    @app.teardown_request
    def teardown_request(exception=None):
        clear_context()


def _should_skip() -> bool:
    """Check if request should skip tracking."""
    if not config._initialized or not config.enabled:
        return True
    if config.should_skip_path(request.path):
        return True
    return False


def _get_or_create_visitor_id() -> str:
    """Get visitor ID from cookie or generate new one."""
    return request.cookies.get(VISITOR_COOKIE) or generate_id()


def _get_or_create_session_id() -> str:
    """Get session ID from cookie or generate deterministic one."""
    existing = request.cookies.get(SESSION_COOKIE)
    if existing:
        return existing

    existing_visitor_id = request.cookies.get(VISITOR_COOKIE)
    if existing_visitor_id:
        return generate_deterministic(existing_visitor_id)
    else:
        return generate_from_fingerprint(_get_client_ip(), _get_user_agent())


def _get_client_ip() -> str:
    """Get client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _get_user_agent() -> str:
    """Get user agent from request."""
    return request.headers.get("User-Agent", "unknown")


def _set_request_context(visitor_id: str, session_id: str) -> None:
    """Set request context for tracking calls."""
    ctx = RequestContext(
        visitor_id=visitor_id,
        session_id=session_id,
        user_id=None,
        url=request.url,
        referrer=request.referrer,
    )
    set_context(ctx)


def _store_in_g(visitor_id: str, session_id: str, is_new_session: bool) -> None:
    """Store tracking IDs in Flask g object for after_request."""
    g.mbuzz_visitor_id = visitor_id
    g.mbuzz_session_id = session_id
    g.mbuzz_is_new_visitor = VISITOR_COOKIE not in request.cookies
    g.mbuzz_is_new_session = is_new_session


def _create_session_if_new(visitor_id: str, session_id: str, is_new_session: bool) -> None:
    """Create session asynchronously if new session."""
    if not is_new_session:
        return

    ctx = RequestContext(
        visitor_id=visitor_id,
        session_id=session_id,
        url=request.url,
        referrer=request.referrer,
    )
    threading.Thread(
        target=create_session,
        args=(visitor_id, session_id, ctx.url, ctx.referrer),
        daemon=True
    ).start()


def _set_cookies(response: Response) -> None:
    """Set visitor and session cookies on response."""
    secure = request.is_secure

    response.set_cookie(
        VISITOR_COOKIE,
        g.mbuzz_visitor_id,
        max_age=VISITOR_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=secure,
    )
    response.set_cookie(
        SESSION_COOKIE,
        g.mbuzz_session_id,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=secure,
    )
