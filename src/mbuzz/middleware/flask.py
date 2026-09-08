"""Flask middleware for mbuzz tracking."""
# NOTE: Session cookie removed in 0.7.0 - server handles session resolution

from flask import Flask, Response, g, request

from ..config import config
from ..context import RequestContext, clear_context, set_context
from ..cookies import VISITOR_COOKIE, VISITOR_MAX_AGE
from ..session_endpoint import (
    NO_CONTENT_STATUS,
    NO_STORE,
    create_session_async,
    is_session_request,
)
from ..utils.identifier import generate_id


def should_create_session() -> bool:
    """Determine whether this request is a real page navigation.

    Primary signal: Sec-Fetch-* headers (modern browsers, unforgeable).
    Fallback: blacklist known sub-request framework headers (old browsers/bots).
    """
    mode = request.headers.get("Sec-Fetch-Mode")
    dest = request.headers.get("Sec-Fetch-Dest")

    if mode:
        return (
            mode == "navigate"
            and dest == "document"
            and not request.headers.get("Sec-Purpose")
        )

    # Fallback for old browsers / bots: blacklist known sub-requests
    return (
        not request.headers.get("Turbo-Frame")
        and not request.headers.get("HX-Request")
        and not request.headers.get("X-Up-Version")
        and request.headers.get("X-Requested-With") != "XMLHttpRequest"
    )


def init_app(app: Flask) -> None:
    """Initialize mbuzz tracking for Flask app."""

    @app.before_request
    def before_request():
        if not config._initialized or not config.enabled:
            return

        # Checked ahead of the skip_paths check and the navigation gate below,
        # both deliberately. A customer's own skip_paths must not swallow the one
        # request that still reaches the app on a cached page, and a fetch()
        # can never satisfy sec-fetch-mode: navigate — leaving that gate in
        # front would mint the cookie and then silently skip the session.
        if is_session_request(request.method, request.path):
            return _handle_session_request()

        if config.should_skip_path(request.path):
            return

        # Only a cookie the browser already holds. This response may be stored
        # by a full-page cache and replayed to everyone, so minting here would
        # hand every later visitor the same id — see MINT_ON_PAGE_RESPONSE. A
        # first-time visitor is established a moment later by the session
        # endpoint, whose response no cache stores.
        visitor_id = request.cookies.get(VISITOR_COOKIE)
        if not visitor_id:
            return

        ip = _get_client_ip()
        user_agent = _get_user_agent()

        _set_request_context(visitor_id, ip, user_agent)
        _store_in_g(visitor_id)

        if should_create_session():
            create_session_async(
                visitor_id,
                {"url": request.url, "referrer": request.referrer},
                ip,
                user_agent,
            )

    @app.teardown_request
    def teardown_request(exception=None):
        clear_context()


def _handle_session_request() -> Response:
    """Answer the session request: mint the cookie, record the session against
    the page, and return an empty, uncacheable 204."""
    visitor_id = _get_or_create_visitor_id()

    create_session_async(
        visitor_id,
        request.get_json(silent=True),
        _get_client_ip(),
        _get_user_agent(),
    )

    return _session_response(visitor_id)


def _session_response(visitor_id: str) -> Response:
    """The endpoint's response: no body, one Set-Cookie, never cacheable."""
    response = Response(status=NO_CONTENT_STATUS)
    response.headers["Cache-Control"] = NO_STORE

    response.set_cookie(
        VISITOR_COOKIE,
        visitor_id,
        max_age=VISITOR_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure,
    )
    return response


def _get_or_create_visitor_id() -> str:
    """Get visitor ID from cookie or generate new one."""
    return request.cookies.get(VISITOR_COOKIE) or generate_id()


def _get_client_ip() -> str:
    """Get client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _get_user_agent() -> str:
    """Get user agent from request."""
    return request.headers.get("User-Agent", "unknown")


def _set_request_context(visitor_id: str, ip: str, user_agent: str) -> None:
    """Set request context for tracking calls."""
    ctx = RequestContext(
        visitor_id=visitor_id,
        ip=ip,
        user_agent=user_agent,
        user_id=None,
        url=request.url,
        referrer=request.referrer,
    )
    set_context(ctx)


def _store_in_g(visitor_id: str) -> None:
    """Expose the visitor to the app for the rest of the request."""
    g.mbuzz_visitor_id = visitor_id
