"""Establishes the visitor from a page the cache served.

A cached page never enters the application, so the tracking middleware never
runs and no visitor cookie is set — every later event is then rejected for
having no one to attribute it to, silently, while the page renders perfectly.

This endpoint is the one request on such a page that always reaches the app. A
small script on the page POSTs here; the SERVER mints the cookie on the
response. The id is never created or read in JS, so it stays HttpOnly and keeps
its full two-year life — a cookie written by document.cookie is capped at 7 days
under Safari's ITP, and 24 hours after an ad click.

Framework-agnostic on purpose: Flask, Django and FastAPI all call the same two
functions, so there is nothing to keep in sync.
"""

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .api import post
from .cookies import SESSION_ENDPOINT_PATH
from .utils.fingerprint import device_fingerprint

# Nothing to return: the response exists for its Set-Cookie header.
NO_CONTENT_STATUS = 204

NO_STORE = "no-store, no-cache, must-revalidate, private"


# A page response may be stored by a full-page cache and replayed to every
# visitor, so it must NEVER carry a Set-Cookie for the visitor id: a cached one
# hands everyone the same id and merges unrelated people into a single journey.
# That is corruption rather than loss — every row exists, each is simply
# attributed to the wrong person, and nothing looks missing.
#
# Only the session endpoint mints, because no cache stores a POST. This mirrors
# CookieBootstrap::CONTEXT_PAGE in the WordPress plugin, which got here first.
MINT_ON_PAGE_RESPONSE = False


def is_session_request(method: str, path: str) -> bool:
    """POST only: a GET is cacheable by an intermediary, which would
    reintroduce the very bug this endpoint exists to fix."""
    return method == "POST" and path == SESSION_ENDPOINT_PATH


def build_session_payload(
    visitor_id: str,
    body: Optional[Dict[str, Any]],
    ip: str,
    user_agent: str,
) -> Dict[str, Any]:
    """Build the session payload for a page that called the endpoint."""
    # The customer's body-parser config is not something the fix can depend on.
    fields = body if isinstance(body, dict) else {}

    return {
        "session": {
            "visitor_id": visitor_id,
            "session_id": str(uuid.uuid4()),
            # The page's URL, not ours — a script on the page called us, so our
            # own path would attribute every session to this endpoint.
            "url": fields.get("url"),
            "referrer": fields.get("referrer"),
            "device_fingerprint": device_fingerprint(ip, user_agent),
            "user_agent": user_agent,
            "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    }


def create_session_async(
    visitor_id: str,
    body: Optional[Dict[str, Any]],
    ip: str,
    user_agent: str,
) -> None:
    """Fire-and-forget session creation via background thread.

    All data is captured before the thread starts — no request-object access
    inside the thread (it would be invalid after the response).
    """
    payload = build_session_payload(visitor_id, body, ip, user_agent)

    threading.Thread(target=post, args=("/sessions", payload), daemon=True).start()
