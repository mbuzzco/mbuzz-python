"""Tests for client methods."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from mbuzz.client.track import track, TrackResult
from mbuzz.client.identify import identify
from mbuzz.client.conversion import conversion, ConversionResult
from mbuzz.client.session import create_session
from mbuzz.context import RequestContext, set_context, clear_context
from mbuzz.config import config


class TestTrack:
    """Test track function."""

    def setup_method(self):
        """Set up before each test."""
        config.reset()
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")
        clear_context()

    def teardown_method(self):
        """Clean up after each test."""
        config.reset()
        clear_context()

    def test_returns_failure_without_visitor_or_user(self):
        """Should return failure if no visitor_id or user_id."""
        result = track(event_type="page_view")
        assert result.success is False

    @patch("mbuzz.client.track.post_with_response")
    def test_returns_success_with_visitor_id(self, mock_post):
        """Should succeed with visitor_id."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}

        result = track(event_type="page_view", visitor_id="vid_123")
        assert result.success is True
        assert result.event_id == "evt_123"

    @patch("mbuzz.client.track.post_with_response")
    def test_returns_success_with_user_id(self, mock_post):
        """Should succeed with user_id only."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}

        result = track(event_type="page_view", user_id="user_123")
        assert result.success is True

    @patch("mbuzz.client.track.post_with_response")
    def test_uses_context_visitor_id(self, mock_post):
        """Should use visitor_id from context."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}
        set_context(RequestContext(visitor_id="ctx_vid", session_id="ctx_sid"))

        result = track(event_type="page_view")
        assert result.success is True

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["events"][0]["visitor_id"] == "ctx_vid"

    @patch("mbuzz.client.track.post_with_response")
    def test_enriches_properties_from_context(self, mock_post):
        """Should enrich properties with url/referrer from context."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}
        set_context(RequestContext(
            visitor_id="vid_123",
            session_id="sid_456",
            url="https://example.com/page",
            referrer="https://google.com",
        ))

        track(event_type="page_view", properties={"custom": "value"})

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        props = payload["events"][0]["properties"]
        assert props["url"] == "https://example.com/page"
        assert props["referrer"] == "https://google.com"
        assert props["custom"] == "value"

    @patch("mbuzz.client.track.post_with_response")
    def test_sends_correct_payload_structure(self, mock_post):
        """Should send correctly structured payload."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}

        track(
            event_type="button_click",
            visitor_id="vid_123",
            session_id="sid_456",
            properties={"button": "signup"},
        )

        call_args = mock_post.call_args
        assert call_args[0][0] == "/events"
        payload = call_args[0][1]
        assert "events" in payload
        event = payload["events"][0]
        assert event["event_type"] == "button_click"
        assert event["visitor_id"] == "vid_123"
        assert event["session_id"] == "sid_456"
        assert event["properties"]["button"] == "signup"
        assert "timestamp" in event

    @patch("mbuzz.client.track.post_with_response")
    def test_returns_failure_on_api_error(self, mock_post):
        """Should return failure on API error."""
        mock_post.return_value = None

        result = track(event_type="page_view", visitor_id="vid_123")
        assert result.success is False

    # Server-side session resolution tests (v0.2.0+)

    @patch("mbuzz.client.track.post_with_response")
    def test_accepts_ip_parameter(self, mock_post):
        """Should accept and forward ip parameter."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}

        result = track(
            event_type="page_view",
            visitor_id="vid_123",
            ip="192.168.1.100"
        )
        assert result.success is True

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["events"][0]["ip"] == "192.168.1.100"

    @patch("mbuzz.client.track.post_with_response")
    def test_accepts_user_agent_parameter(self, mock_post):
        """Should accept and forward user_agent parameter."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}

        result = track(
            event_type="page_view",
            visitor_id="vid_123",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        )
        assert result.success is True

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["events"][0]["user_agent"] == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

    @patch("mbuzz.client.track.post_with_response")
    def test_accepts_both_ip_and_user_agent(self, mock_post):
        """Should accept both ip and user_agent parameters."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}

        result = track(
            event_type="page_view",
            visitor_id="vid_123",
            ip="10.0.0.1",
            user_agent="Chrome/120"
        )
        assert result.success is True

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["events"][0]["ip"] == "10.0.0.1"
        assert payload["events"][0]["user_agent"] == "Chrome/120"

    @patch("mbuzz.client.track.post_with_response")
    def test_uses_context_ip_and_user_agent(self, mock_post):
        """Should use ip and user_agent from context if not explicitly provided."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}
        set_context(RequestContext(
            visitor_id="ctx_vid",
            session_id="ctx_sid",
            ip="203.0.113.50",
            user_agent="Safari/17.0"
        ))

        result = track(event_type="page_view")
        assert result.success is True

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["events"][0]["ip"] == "203.0.113.50"
        assert payload["events"][0]["user_agent"] == "Safari/17.0"

    @patch("mbuzz.client.track.post_with_response")
    def test_explicit_ip_overrides_context(self, mock_post):
        """Should use explicit ip/user_agent over context."""
        mock_post.return_value = {"events": [{"id": "evt_123"}]}
        set_context(RequestContext(
            visitor_id="ctx_vid",
            session_id="ctx_sid",
            ip="context_ip",
            user_agent="context_ua"
        ))

        result = track(
            event_type="page_view",
            ip="explicit_ip",
            user_agent="explicit_ua"
        )
        assert result.success is True

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["events"][0]["ip"] == "explicit_ip"
        assert payload["events"][0]["user_agent"] == "explicit_ua"


class TestIdentify:
    """Test identify function."""

    def setup_method(self):
        """Set up before each test."""
        config.reset()
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")
        clear_context()

    def teardown_method(self):
        """Clean up after each test."""
        config.reset()
        clear_context()

    def test_returns_false_without_user_id(self):
        """Should return False if no user_id."""
        result = identify(user_id="")
        assert result is False

        result = identify(user_id=None)
        assert result is False

    @patch("mbuzz.client.identify.post")
    def test_returns_true_on_success(self, mock_post):
        """Should return True on success."""
        mock_post.return_value = True

        result = identify(user_id="user_123")
        assert result is True

    @patch("mbuzz.client.identify.post")
    def test_uses_context_visitor_id(self, mock_post):
        """Should use visitor_id from context."""
        mock_post.return_value = True
        set_context(RequestContext(visitor_id="ctx_vid", session_id="ctx_sid"))

        identify(user_id="user_123")

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["visitor_id"] == "ctx_vid"

    @patch("mbuzz.client.identify.post")
    def test_sends_correct_payload(self, mock_post):
        """Should send correctly structured payload."""
        mock_post.return_value = True

        identify(
            user_id="user_123",
            visitor_id="vid_456",
            traits={"email": "test@example.com", "plan": "pro"},
        )

        call_args = mock_post.call_args
        assert call_args[0][0] == "/identify"
        payload = call_args[0][1]
        assert payload["user_id"] == "user_123"
        assert payload["visitor_id"] == "vid_456"
        assert payload["traits"]["email"] == "test@example.com"
        assert payload["traits"]["plan"] == "pro"

    @patch("mbuzz.client.identify.post")
    def test_converts_numeric_user_id_to_string(self, mock_post):
        """Should convert numeric user_id to string."""
        mock_post.return_value = True

        identify(user_id=12345)

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["user_id"] == "12345"


class TestConversion:
    """Test conversion function."""

    def setup_method(self):
        """Set up before each test."""
        config.reset()
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")
        clear_context()

    def teardown_method(self):
        """Clean up after each test."""
        config.reset()
        clear_context()

    def test_returns_failure_without_visitor_or_user(self):
        """Should return failure if no visitor_id or user_id."""
        result = conversion(conversion_type="purchase")
        assert result.success is False

    @patch("mbuzz.client.conversion.post_with_response")
    def test_returns_success_with_visitor_id(self, mock_post):
        """Should succeed with visitor_id."""
        mock_post.return_value = {"conversion": {"id": "conv_123"}}

        result = conversion(conversion_type="purchase", visitor_id="vid_123")
        assert result.success is True
        assert result.conversion_id == "conv_123"

    @patch("mbuzz.client.conversion.post_with_response")
    def test_uses_context_visitor_id(self, mock_post):
        """Should use visitor_id from context."""
        mock_post.return_value = {"conversion": {"id": "conv_123"}}
        set_context(RequestContext(visitor_id="ctx_vid", session_id="ctx_sid"))

        result = conversion(conversion_type="purchase")
        assert result.success is True

        call_args = mock_post.call_args[0]
        payload = call_args[1]
        assert payload["visitor_id"] == "ctx_vid"

    @patch("mbuzz.client.conversion.post_with_response")
    def test_sends_correct_payload(self, mock_post):
        """Should send correctly structured payload."""
        mock_post.return_value = {"conversion": {"id": "conv_123"}, "attribution": {"model": "linear"}}

        conversion(
            conversion_type="purchase",
            visitor_id="vid_123",
            revenue=99.99,
            currency="USD",
            is_acquisition=True,
            properties={"order_id": "ORD-123"},
        )

        call_args = mock_post.call_args
        assert call_args[0][0] == "/conversions"
        payload = call_args[0][1]
        assert payload["conversion_type"] == "purchase"
        assert payload["visitor_id"] == "vid_123"
        assert payload["revenue"] == 99.99
        assert payload["currency"] == "USD"
        assert payload["is_acquisition"] is True
        assert payload["properties"]["order_id"] == "ORD-123"

    @patch("mbuzz.client.conversion.post_with_response")
    def test_returns_attribution_data(self, mock_post):
        """Should return attribution data."""
        mock_post.return_value = {
            "conversion": {"id": "conv_123"},
            "attribution": {"model": "linear", "sessions": []},
        }

        result = conversion(conversion_type="purchase", visitor_id="vid_123")
        assert result.attribution == {"model": "linear", "sessions": []}


class TestCreateSession:
    """Test create_session function."""

    def setup_method(self):
        """Set up before each test."""
        config.reset()
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")

    def teardown_method(self):
        """Clean up after each test."""
        config.reset()

    @patch("mbuzz.client.session.post")
    def test_returns_true_on_success(self, mock_post):
        """Should return True on success."""
        mock_post.return_value = True

        result = create_session(
            visitor_id="vid_123",
            session_id="sid_456",
            url="https://example.com",
        )
        assert result is True

    @patch("mbuzz.client.session.post")
    def test_sends_correct_payload(self, mock_post):
        """Should send correctly structured payload."""
        mock_post.return_value = True

        create_session(
            visitor_id="vid_123",
            session_id="sid_456",
            url="https://example.com/page",
            referrer="https://google.com",
        )

        call_args = mock_post.call_args
        assert call_args[0][0] == "/sessions"
        payload = call_args[0][1]
        session = payload["session"]
        assert session["visitor_id"] == "vid_123"
        assert session["session_id"] == "sid_456"
        assert session["url"] == "https://example.com/page"
        assert session["referrer"] == "https://google.com"
        assert "started_at" in session

    @patch("mbuzz.client.session.post")
    def test_returns_false_on_api_error(self, mock_post):
        """Should return False on API error."""
        mock_post.return_value = False

        result = create_session(
            visitor_id="vid_123",
            session_id="sid_456",
            url="https://example.com",
        )
        assert result is False
