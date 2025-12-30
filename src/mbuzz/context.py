"""Request context management using contextvars."""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RequestContext:
    """Holds request-scoped data for tracking."""

    visitor_id: str
    session_id: str
    user_id: Optional[str] = None
    url: Optional[str] = None
    referrer: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None

    def enrich_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Add url and referrer to properties if not already present."""
        result: Dict[str, Any] = {}
        if self.url:
            result["url"] = self.url
        if self.referrer:
            result["referrer"] = self.referrer
        result.update(properties)
        return result


# Context variable for current request
_context: ContextVar[Optional[RequestContext]] = ContextVar("mbuzz_context", default=None)


def get_context() -> Optional[RequestContext]:
    """Get the current request context."""
    return _context.get()


def set_context(ctx: RequestContext) -> None:
    """Set the current request context."""
    _context.set(ctx)


def clear_context() -> None:
    """Clear the current request context."""
    _context.set(None)
