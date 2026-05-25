"""Conversion request for tracking conversions."""
# NOTE: Session ID removed in 0.7.0 - server handles session resolution

import warnings
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
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    identifier: Optional[Dict[str, str]] = None,
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
        ip: Client IP address for server-side session resolution
        user_agent: Client user agent for server-side session resolution
        identifier: DEPRECATED — pass the email/external ID as ``user_id`` instead.
            The backend ``/conversions`` endpoint has never permitted this field
            and the events endpoint treats ``identifier.email`` exactly as
            ``user_id``. Will be removed in a future major release.

    Returns:
        ConversionResult with success status, conversion ID, and attribution data
    """
    if identifier is not None:
        warnings.warn(
            "The `identifier` parameter on conversion() is deprecated and ignored "
            "by the backend on /conversions. Pass the email or external ID as "
            "`user_id` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    ctx = get_context()

    visitor_id = visitor_id or (ctx.visitor_id if ctx else None)
    user_id = user_id or (ctx.user_id if ctx else None)
    ip = ip or (ctx.ip if ctx else None)
    user_agent = user_agent or (ctx.user_agent if ctx else None)

    if not visitor_id and not user_id:
        return ConversionResult(success=False)

    payload: Dict[str, Any] = {
        "conversion_type": conversion_type,
        "currency": currency,
        "is_acquisition": is_acquisition,
        "inherit_acquisition": inherit_acquisition,
        "properties": properties or {},
    }

    # Only include non-None values
    if visitor_id:
        payload["visitor_id"] = visitor_id
    if user_id:
        payload["user_id"] = str(user_id)
    if event_id:
        payload["event_id"] = event_id
    if revenue is not None:
        payload["revenue"] = revenue
    if ip:
        payload["ip"] = ip
    if user_agent:
        payload["user_agent"] = user_agent
    if identifier:
        payload["identifier"] = identifier

    response = post_with_response("/conversions", payload)
    if not response:
        return ConversionResult(success=False)

    return ConversionResult(
        success=True,
        conversion_id=response.get("conversion", {}).get("id"),
        attribution=response.get("attribution"),
    )
