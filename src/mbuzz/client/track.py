"""Track request for event tracking."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..api import post_with_response
from ..context import get_context


@dataclass
class TrackResult:
    """Result of tracking an event."""

    success: bool
    event_id: Optional[str] = None
    event_type: Optional[str] = None
    visitor_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class TrackOptions:
    """Options for tracking an event."""

    event_type: str
    visitor_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


def _resolve_ids(options: TrackOptions) -> TrackOptions:
    """Resolve visitor/session/user IDs from context if not provided."""
    ctx = get_context()
    if not ctx:
        return options

    return TrackOptions(
        event_type=options.event_type,
        visitor_id=options.visitor_id or ctx.visitor_id,
        session_id=options.session_id or ctx.session_id,
        user_id=options.user_id or ctx.user_id,
        properties=options.properties,
    )


def _enrich_properties(options: TrackOptions) -> Dict[str, Any]:
    """Enrich properties with url/referrer from context."""
    ctx = get_context()
    props = options.properties or {}

    if ctx:
        return ctx.enrich_properties(props)
    return props


def _validate(options: TrackOptions) -> bool:
    """Validate track options. Must have visitor_id or user_id."""
    return bool(options.visitor_id or options.user_id)


def _build_payload(options: TrackOptions, properties: Dict[str, Any]) -> Dict[str, Any]:
    """Build API payload from options."""
    return {
        "events": [
            {
                "event_type": options.event_type,
                "visitor_id": options.visitor_id,
                "session_id": options.session_id,
                "user_id": options.user_id,
                "properties": properties,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }


def _parse_response(response: Optional[Dict[str, Any]], options: TrackOptions) -> TrackResult:
    """Parse API response into TrackResult."""
    if not response or not response.get("events"):
        return TrackResult(success=False)

    event = response["events"][0]
    return TrackResult(
        success=True,
        event_id=event.get("id"),
        event_type=options.event_type,
        visitor_id=options.visitor_id,
        session_id=options.session_id,
    )


def track(
    event_type: str,
    visitor_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> TrackResult:
    """Track an event.

    Args:
        event_type: Type of event (e.g., "page_view", "button_click")
        visitor_id: Visitor ID (uses context if not provided)
        session_id: Session ID (uses context if not provided)
        user_id: User ID (uses context if not provided)
        properties: Additional event properties

    Returns:
        TrackResult with success status and event details
    """
    options = TrackOptions(
        event_type=event_type,
        visitor_id=visitor_id,
        session_id=session_id,
        user_id=user_id,
        properties=properties,
    )

    options = _resolve_ids(options)

    if not _validate(options):
        return TrackResult(success=False)

    enriched_props = _enrich_properties(options)
    payload = _build_payload(options, enriched_props)
    response = post_with_response("/events", payload)

    return _parse_response(response, options)
