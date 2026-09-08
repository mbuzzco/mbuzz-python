"""FastAPI / Starlette middleware for mbuzz tracking.

`Framework :: FastAPI` was advertised in the package metadata long before any
FastAPI middleware existed, so these users got no cookie minting at all — a
silent-drop path with nothing to do with caching.

Works with any Starlette app; FastAPI is Starlette underneath.
"""

import json
from typing import Any, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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


def should_create_session(request: Request) -> bool:
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

    return (
        not request.headers.get("Turbo-Frame")
        and not request.headers.get("HX-Request")
        and not request.headers.get("X-Up-Version")
        and request.headers.get("X-Requested-With") != "XMLHttpRequest"
    )


class MbuzzMiddleware(BaseHTTPMiddleware):
    """Mints the visitor cookie and opens a session on a page navigation."""

    async def dispatch(self, request: Request, call_next):
        if not config._initialized or not config.enabled:
            return await call_next(request)

        # Checked ahead of the skip_paths check and the navigation gate below,
        # both deliberately. A customer's own skip_paths must not swallow the
        # one request that still reaches the app on a cached page, and a
        # fetch() can never satisfy sec-fetch-mode: navigate — leaving that
        # gate in front would mint the cookie and then silently skip the
        # session.
        if is_session_request(request.method, request.url.path):
            return await self._handle_session_request(request)

        if config.should_skip_path(request.url.path):
            return await call_next(request)

        visitor_id = _get_or_create_visitor_id(request)
        ip = _get_client_ip(request)
        user_agent = _get_user_agent(request)

        _set_request_context(request, visitor_id, ip, user_agent)

        if should_create_session(request):
            create_session_async(
                visitor_id,
                {"url": str(request.url), "referrer": request.headers.get("referer")},
                ip,
                user_agent,
            )

        try:
            response = await call_next(request)
        finally:
            clear_context()

        _set_visitor_cookie(response, visitor_id, request.url.scheme == "https")
        return response

    async def _handle_session_request(self, request: Request) -> Response:
        """Answer the session request: mint the cookie, record the session
        against the page, and return an empty, uncacheable 204."""
        visitor_id = _get_or_create_visitor_id(request)

        create_session_async(
            visitor_id,
            await _read_json(request),
            _get_client_ip(request),
            _get_user_agent(request),
        )

        response = Response(status_code=NO_CONTENT_STATUS)
        response.headers["Cache-Control"] = NO_STORE
        _set_visitor_cookie(response, visitor_id, request.url.scheme == "https")
        return response


async def _read_json(request: Request) -> Optional[Dict[str, Any]]:
    """The customer's body-parser config is not something the fix can depend on."""
    try:
        return json.loads(await request.body() or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None


def _get_or_create_visitor_id(request: Request) -> str:
    return request.cookies.get(VISITOR_COOKIE) or generate_id()


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")


def _set_request_context(
    request: Request, visitor_id: str, ip: str, user_agent: str
) -> None:
    set_context(
        RequestContext(
            visitor_id=visitor_id,
            ip=ip,
            user_agent=user_agent,
            user_id=None,
            url=str(request.url),
            referrer=request.headers.get("referer"),
        )
    )


def _set_visitor_cookie(response: Response, visitor_id: str, secure: bool) -> None:
    response.set_cookie(
        VISITOR_COOKIE,
        visitor_id,
        max_age=VISITOR_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=secure,
    )
