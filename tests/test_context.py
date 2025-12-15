"""Tests for context module."""

import pytest
from mbuzz.context import RequestContext, get_context, set_context, clear_context


class TestRequestContext:
    """Test RequestContext dataclass."""

    def test_creates_with_required_fields(self):
        """Should create context with visitor and session IDs."""
        ctx = RequestContext(visitor_id="vid_123", session_id="sid_456")
        assert ctx.visitor_id == "vid_123"
        assert ctx.session_id == "sid_456"

    def test_optional_fields_default_to_none(self):
        """Should default optional fields to None."""
        ctx = RequestContext(visitor_id="vid_123", session_id="sid_456")
        assert ctx.user_id is None
        assert ctx.url is None
        assert ctx.referrer is None

    def test_accepts_all_fields(self):
        """Should accept all fields."""
        ctx = RequestContext(
            visitor_id="vid_123",
            session_id="sid_456",
            user_id="user_789",
            url="https://example.com/page",
            referrer="https://google.com",
        )
        assert ctx.visitor_id == "vid_123"
        assert ctx.session_id == "sid_456"
        assert ctx.user_id == "user_789"
        assert ctx.url == "https://example.com/page"
        assert ctx.referrer == "https://google.com"


class TestEnrichProperties:
    """Test enrich_properties method."""

    def test_adds_url_to_properties(self):
        """Should add url to properties."""
        ctx = RequestContext(
            visitor_id="vid_123",
            session_id="sid_456",
            url="https://example.com/page",
        )
        result = ctx.enrich_properties({})
        assert result["url"] == "https://example.com/page"

    def test_adds_referrer_to_properties(self):
        """Should add referrer to properties."""
        ctx = RequestContext(
            visitor_id="vid_123",
            session_id="sid_456",
            referrer="https://google.com",
        )
        result = ctx.enrich_properties({})
        assert result["referrer"] == "https://google.com"

    def test_custom_properties_override_context(self):
        """Custom properties should override context values."""
        ctx = RequestContext(
            visitor_id="vid_123",
            session_id="sid_456",
            url="https://example.com/page",
        )
        result = ctx.enrich_properties({"url": "custom_url"})
        assert result["url"] == "custom_url"

    def test_preserves_custom_properties(self):
        """Should preserve custom properties."""
        ctx = RequestContext(
            visitor_id="vid_123",
            session_id="sid_456",
            url="https://example.com/page",
        )
        result = ctx.enrich_properties({"custom": "value", "count": 42})
        assert result["custom"] == "value"
        assert result["count"] == 42
        assert result["url"] == "https://example.com/page"

    def test_handles_empty_context(self):
        """Should work with no url or referrer in context."""
        ctx = RequestContext(visitor_id="vid_123", session_id="sid_456")
        result = ctx.enrich_properties({"custom": "value"})
        assert result == {"custom": "value"}
        assert "url" not in result
        assert "referrer" not in result


class TestContextVar:
    """Test context variable functions."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_get_context_returns_none_by_default(self):
        """Should return None when no context set."""
        assert get_context() is None

    def test_set_context_stores_context(self):
        """Should store context."""
        ctx = RequestContext(visitor_id="vid_123", session_id="sid_456")
        set_context(ctx)
        assert get_context() is ctx

    def test_clear_context_removes_context(self):
        """Should clear stored context."""
        ctx = RequestContext(visitor_id="vid_123", session_id="sid_456")
        set_context(ctx)
        clear_context()
        assert get_context() is None

    def test_context_is_isolated_per_context(self):
        """Context should be isolated (uses contextvars)."""
        ctx1 = RequestContext(visitor_id="vid_1", session_id="sid_1")
        ctx2 = RequestContext(visitor_id="vid_2", session_id="sid_2")

        set_context(ctx1)
        assert get_context().visitor_id == "vid_1"

        set_context(ctx2)
        assert get_context().visitor_id == "vid_2"
