"""Identify request for user identification."""

from typing import Any, Dict, Optional, Union

from ..api import post
from ..context import get_context


def identify(
    user_id: Union[str, int, None],
    visitor_id: Optional[str] = None,
    traits: Optional[Dict[str, Any]] = None,
) -> bool:
    """Identify a user and link to visitor.

    Args:
        user_id: User ID to identify (required)
        visitor_id: Visitor ID (uses context if not provided)
        traits: User traits/attributes

    Returns:
        True on success, False on failure
    """
    if not user_id:
        return False

    ctx = get_context()
    visitor_id = visitor_id or (ctx.visitor_id if ctx else None)

    payload = {
        "user_id": str(user_id),
        "visitor_id": visitor_id,
        "traits": traits or {},
    }

    return post("/identify", payload)
