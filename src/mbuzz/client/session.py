"""Session request for creating sessions."""

from datetime import datetime, timezone
from typing import Optional

from ..api import post


def create_session(
    visitor_id: str,
    session_id: str,
    url: str,
    referrer: Optional[str] = None,
) -> bool:
    """Create a new session.

    Called async from middleware on first request.

    Args:
        visitor_id: Visitor ID
        session_id: Session ID
        url: Current page URL
        referrer: Referring URL

    Returns:
        True on success, False on failure
    """
    payload = {
        "session": {
            "visitor_id": visitor_id,
            "session_id": session_id,
            "url": url,
            "referrer": referrer,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
    }

    return post("/sessions", payload)
