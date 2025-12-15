"""Tests for API module."""

import json
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import URLError

from mbuzz.api import post, post_with_response, _make_request
from mbuzz.config import config


class TestPost:
    """Test post function."""

    def setup_method(self):
        """Set up config before each test."""
        config.reset()
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")

    def teardown_method(self):
        """Reset config after each test."""
        config.reset()

    def test_returns_false_when_not_initialized(self):
        """Should return False if SDK not initialized."""
        config.reset()
        result = post("/events", {"test": "data"})
        assert result is False

    def test_returns_false_when_disabled(self):
        """Should return False if SDK disabled."""
        config.init(api_key="sk_test_123", enabled=False)
        result = post("/events", {"test": "data"})
        assert result is False

    @patch("mbuzz.api.urlopen")
    def test_returns_true_on_success(self, mock_urlopen):
        """Should return True on successful request."""
        mock_response = MagicMock()
        mock_response.status = 202
        mock_urlopen.return_value = mock_response

        result = post("/events", {"test": "data"})
        assert result is True

    @patch("mbuzz.api.urlopen")
    def test_returns_true_on_200(self, mock_urlopen):
        """Should return True on 200 response."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = post("/events", {"test": "data"})
        assert result is True

    @patch("mbuzz.api.urlopen")
    def test_returns_false_on_error_status(self, mock_urlopen):
        """Should return False on error status."""
        mock_response = MagicMock()
        mock_response.status = 400
        mock_urlopen.return_value = mock_response

        result = post("/events", {"test": "data"})
        assert result is False

    @patch("mbuzz.api.urlopen")
    def test_returns_false_on_network_error(self, mock_urlopen):
        """Should return False on network error."""
        mock_urlopen.side_effect = URLError("Connection refused")

        result = post("/events", {"test": "data"})
        assert result is False

    @patch("mbuzz.api.urlopen")
    def test_sends_authorization_header(self, mock_urlopen):
        """Should send Bearer token in Authorization header."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        post("/events", {"test": "data"})

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.get_header("Authorization") == "Bearer sk_test_123"

    @patch("mbuzz.api.urlopen")
    def test_sends_json_content_type(self, mock_urlopen):
        """Should send JSON content type."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        post("/events", {"test": "data"})

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.get_header("Content-type") == "application/json"

    @patch("mbuzz.api.urlopen")
    def test_sends_json_body(self, mock_urlopen):
        """Should send JSON body."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        post("/events", {"test": "data", "count": 42})

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode("utf-8"))
        assert body == {"test": "data", "count": 42}


class TestPostWithResponse:
    """Test post_with_response function."""

    def setup_method(self):
        """Set up config before each test."""
        config.reset()
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")

    def teardown_method(self):
        """Reset config after each test."""
        config.reset()

    def test_returns_none_when_not_initialized(self):
        """Should return None if SDK not initialized."""
        config.reset()
        result = post_with_response("/events", {"test": "data"})
        assert result is None

    def test_returns_none_when_disabled(self):
        """Should return None if SDK disabled."""
        config.init(api_key="sk_test_123", enabled=False)
        result = post_with_response("/events", {"test": "data"})
        assert result is None

    @patch("mbuzz.api.urlopen")
    def test_returns_parsed_json_on_success(self, mock_urlopen):
        """Should return parsed JSON on success."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"id": "evt_123", "status": "accepted"}'
        mock_urlopen.return_value = mock_response

        result = post_with_response("/events", {"test": "data"})
        assert result == {"id": "evt_123", "status": "accepted"}

    @patch("mbuzz.api.urlopen")
    def test_returns_none_on_error_status(self, mock_urlopen):
        """Should return None on error status."""
        mock_response = MagicMock()
        mock_response.status = 400
        mock_urlopen.return_value = mock_response

        result = post_with_response("/events", {"test": "data"})
        assert result is None

    @patch("mbuzz.api.urlopen")
    def test_returns_none_on_network_error(self, mock_urlopen):
        """Should return None on network error."""
        mock_urlopen.side_effect = URLError("Connection refused")

        result = post_with_response("/events", {"test": "data"})
        assert result is None


class TestMakeRequest:
    """Test _make_request URL construction."""

    def setup_method(self):
        """Set up config before each test."""
        config.reset()
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")

    def teardown_method(self):
        """Reset config after each test."""
        config.reset()

    @patch("mbuzz.api.urlopen")
    def test_constructs_url_correctly(self, mock_urlopen):
        """Should construct correct URL from base and path."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        post("/events", {"test": "data"})

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.full_url == "http://localhost:3000/api/v1/events"

    @patch("mbuzz.api.urlopen")
    def test_handles_path_with_leading_slash(self, mock_urlopen):
        """Should handle path with leading slash."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        post("/events", {"test": "data"})

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.full_url == "http://localhost:3000/api/v1/events"

    @patch("mbuzz.api.urlopen")
    def test_handles_path_without_leading_slash(self, mock_urlopen):
        """Should handle path without leading slash."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        post("events", {"test": "data"})

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.full_url == "http://localhost:3000/api/v1/events"

    @patch("mbuzz.api.urlopen")
    def test_handles_base_url_with_trailing_slash(self, mock_urlopen):
        """Should handle base URL with trailing slash."""
        config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1/")
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        post("/events", {"test": "data"})

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.full_url == "http://localhost:3000/api/v1/events"
