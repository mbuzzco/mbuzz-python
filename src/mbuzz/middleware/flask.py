"""Flask middleware for mbuzz tracking."""
# NOTE: Session cookie removed in 0.7.0 - server handles session resolution

from flask import Flask, request, g, Response

from ..config import config
from ..context import RequestContext, set_context, clear_context
from ..cookies import VISITOR_COOKIE, VISITOR_MAX_AGE
from ..utils.identifier import generate_id


def init_app(app: Flask) -> None:
    """Initialize mbuzz tracking for Flask app."""

    @app.before_request
    def before_request():
        if _should_skip():
            return

        visitor_id = _get_or_create_visitor_id()
        ip = _get_client_ip()
        user_agent = _get_user_agent()

        _set_request_context(visitor_id, ip, user_agent)
        _store_in_g(visitor_id)

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
    """Store tracking IDs in Flask g object for after_request."""
    g.mbuzz_visitor_id = visitor_id
    g.mbuzz_is_new_visitor = VISITOR_COOKIE not in request.cookies


def _set_cookies(response: Response) -> None:
    """Set visitor cookie on response."""
    secure = request.is_secure

    response.set_cookie(
        VISITOR_COOKIE,
        g.mbuzz_visitor_id,
        max_age=VISITOR_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=secure,
    )
