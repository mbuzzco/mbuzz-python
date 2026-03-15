"""Mbuzz - Multi-touch attribution SDK for Python."""
# NOTE: Session ID removed in 0.7.0 - server handles session resolution

from typing import Any, Dict, Optional, Union

from .config import config
from .context import get_context
from .client.track import track, TrackResult
from .client.identify import identify
from .client.conversion import conversion, ConversionResult

__version__ = "0.8.2"


def init(
    api_key: str,
    enabled: bool = True,
    debug: bool = False,
    timeout: Optional[float] = None,
    skip_paths: Optional[list] = None,
    skip_extensions: Optional[list] = None,
) -> None:
    """Initialize the mbuzz SDK.

    Args:
        api_key: Your mbuzz API key (required)
        enabled: Enable/disable tracking (default: True)
        debug: Enable debug logging (default: False)
        timeout: Request timeout in seconds (default: 5.0)
        skip_paths: Additional paths to skip tracking
        skip_extensions: Additional file extensions to skip
    """
    config.init(
        api_key=api_key,
        enabled=enabled,
        debug=debug,
        timeout=timeout,
        skip_paths=skip_paths or [],
        skip_extensions=skip_extensions or [],
    )


def event(event_type: str, **properties: Any) -> TrackResult:
    """Track an event.

    Args:
        event_type: Type of event (e.g., "page_view", "button_click")
        **properties: Additional event properties

    Returns:
        TrackResult with success status and event details
    """
    return track(event_type=event_type, properties=properties)


def visitor_id() -> Optional[str]:
    """Get current visitor ID from context."""
    ctx = get_context()
    return ctx.visitor_id if ctx else None


def user_id() -> Optional[str]:
    """Get current user ID from context."""
    ctx = get_context()
    return ctx.user_id if ctx else None


__all__ = [
    "init",
    "event",
    "conversion",
    "identify",
    "visitor_id",
    "user_id",
    "TrackResult",
    "ConversionResult",
    "__version__",
]
