"""Conversion request for tracking conversions."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from ..api import post_with_response
from ..context import get_context


@dataclass
class ConversionResult:
    """Result of tracking a conversion."""

    success: bool
    conversion_id: Optional[str] = None
    attribution: Optional[Dict[str, Any]] = None


def conversion(
    conversion_type: str,
    visitor_id: Optional[str] = None,
    user_id: Optional[Union[str, int]] = None,
    event_id: Optional[str] = None,
    revenue: Optional[float] = None,
    currency: str = "USD",
    is_acquisition: bool = False,
    inherit_acquisition: bool = False,
    properties: Optional[Dict[str, Any]] = None,
) -> ConversionResult:
    """Track a conversion.

    Args:
        conversion_type: Type of conversion (e.g., "purchase", "signup")
        visitor_id: Visitor ID (uses context if not provided)
        user_id: User ID (uses context if not provided)
        event_id: Optional event ID to link conversion to
        revenue: Revenue amount
        currency: Currency code (default: USD)
        is_acquisition: Whether this is a customer acquisition
        inherit_acquisition: Whether to inherit acquisition from previous conversion
        properties: Additional conversion properties

    Returns:
        ConversionResult with success status, conversion ID, and attribution data
    """
    ctx = get_context()

    visitor_id = visitor_id or (ctx.visitor_id if ctx else None)
    user_id = user_id or (ctx.user_id if ctx else None)

    if not visitor_id and not user_id:
        return ConversionResult(success=False)

    payload = {
        "conversion_type": conversion_type,
        "visitor_id": visitor_id,
        "user_id": str(user_id) if user_id else None,
        "event_id": event_id,
        "revenue": revenue,
        "currency": currency,
        "is_acquisition": is_acquisition,
        "inherit_acquisition": inherit_acquisition,
        "properties": properties or {},
    }

    response = post_with_response("/conversions", payload)
    if not response:
        return ConversionResult(success=False)

    return ConversionResult(
        success=True,
        conversion_id=response.get("conversion", {}).get("id"),
        attribution=response.get("attribution"),
    )
