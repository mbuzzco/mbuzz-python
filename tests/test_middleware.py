"""Tests for Flask middleware."""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, g

from mbuzz.middleware.flask import init_app
from mbuzz.config import config
from mbuzz.context import get_context, clear_context
from mbuzz.cookies import VISITOR_COOKIE, SESSION_COOKIE, VISITOR_MAX_AGE, SESSION_MAX_AGE


class TestFlaskMiddleware:
    """Test Flask middleware."""

    def setup_method(self):
        """Set up before each test."""
        config.reset()
        clear_context()
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

        @self.app.route("/")
        def index():
            return "OK"

        @self.app.route("/api/data")
        def api_data():
            return "data"

    def teardown_method(self):
        """Clean up after each test."""
        config.reset()
        clear_context()

    def test_does_nothing_when_not_initialized(self):
        """Should skip tracking when SDK not initialized."""
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            assert response.status_code == 200
            assert VISITOR_COOKIE not in response.headers.get("Set-Cookie", "")

    def test_does_nothing_when_disabled(self):
        """Should skip tracking when SDK is disabled."""
        config.init(api_key="sk_test_123", enabled=False)
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            assert response.status_code == 200
            assert VISITOR_COOKIE not in response.headers.get("Set-Cookie", "")

    def test_skips_health_check_paths(self):
        """Should skip tracking for health check paths."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        @self.app.route("/health")
        def health():
            return "healthy"

        with self.app.test_client() as client:
            response = client.get("/health")

            assert response.status_code == 200
            assert VISITOR_COOKIE not in response.headers.get("Set-Cookie", "")

    def test_skips_static_file_extensions(self):
        """Should skip tracking for static file extensions."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        @self.app.route("/app.js")
        def js():
            return "javascript"

        with self.app.test_client() as client:
            response = client.get("/app.js")

            assert response.status_code == 200
            assert VISITOR_COOKIE not in response.headers.get("Set-Cookie", "")

    def test_creates_visitor_id_for_new_visitor(self):
        """Should create visitor ID for new visitor."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            visitor_cookie = next(
                (c for c in cookies if VISITOR_COOKIE in c), None
            )

            assert visitor_cookie is not None
            assert VISITOR_COOKIE in visitor_cookie

    def test_creates_session_id_for_new_visitor(self):
        """Should create session ID for new visitor."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            session_cookie = next(
                (c for c in cookies if SESSION_COOKIE in c), None
            )

            assert session_cookie is not None
            assert SESSION_COOKIE in session_cookie

    def test_reuses_visitor_id_from_cookie(self):
        """Should reuse existing visitor ID from cookie."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        existing_vid = "abc123" * 10 + "abcd"

        with self.app.test_client() as client:
            client.set_cookie(VISITOR_COOKIE, existing_vid)
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            visitor_cookie = next(
                (c for c in cookies if VISITOR_COOKIE in c), None
            )

            assert existing_vid in visitor_cookie

    def test_reuses_session_id_from_cookie(self):
        """Should reuse existing session ID from cookie."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        existing_sid = "xyz789" * 10 + "xyzw"

        with self.app.test_client() as client:
            client.set_cookie(SESSION_COOKIE, existing_sid)
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            session_cookie = next(
                (c for c in cookies if SESSION_COOKIE in c), None
            )

            assert existing_sid in session_cookie

    def test_sets_context_during_request(self):
        """Should set request context during request handling."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        captured_context = {}

        @self.app.route("/capture")
        def capture():
            ctx = get_context()
            if ctx:
                captured_context["visitor_id"] = ctx.visitor_id
                captured_context["session_id"] = ctx.session_id
                captured_context["url"] = ctx.url
            return "captured"

        with self.app.test_client() as client:
            client.get("/capture")

            assert "visitor_id" in captured_context
            assert "session_id" in captured_context
            assert len(captured_context["visitor_id"]) == 64
            assert len(captured_context["session_id"]) == 64

    def test_clears_context_after_request(self):
        """Should clear context after request completes."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            client.get("/")

            # Context should be cleared after request
            assert get_context() is None

    def test_sets_url_in_context(self):
        """Should set URL in request context."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        captured_url = {}

        @self.app.route("/page")
        def page():
            ctx = get_context()
            if ctx:
                captured_url["url"] = ctx.url
            return "page"

        with self.app.test_client() as client:
            client.get("/page")

            assert "/page" in captured_url.get("url", "")

    def test_sets_referrer_in_context(self):
        """Should set referrer in request context."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        captured_referrer = {}

        @self.app.route("/landing")
        def landing():
            ctx = get_context()
            if ctx:
                captured_referrer["referrer"] = ctx.referrer
            return "landing"

        with self.app.test_client() as client:
            client.get("/landing", headers={"Referer": "https://google.com"})

            assert captured_referrer.get("referrer") == "https://google.com"

    @patch("mbuzz.middleware.flask.create_session")
    def test_calls_create_session_for_new_session(self, mock_create_session):
        """Should call create_session for new sessions."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            client.get("/")

            # Give thread time to start
            import time
            time.sleep(0.1)

            assert mock_create_session.called

    @patch("mbuzz.middleware.flask.create_session")
    def test_does_not_call_create_session_for_existing_session(self, mock_create_session):
        """Should not call create_session for existing sessions."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            client.set_cookie(SESSION_COOKIE, "existing_session_id_abc123")
            client.get("/")

            assert not mock_create_session.called

    def test_sets_visitor_cookie_max_age(self):
        """Should set visitor cookie with correct max age."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            visitor_cookie = next(
                (c for c in cookies if VISITOR_COOKIE in c), None
            )

            assert f"Max-Age={VISITOR_MAX_AGE}" in visitor_cookie

    def test_sets_session_cookie_max_age(self):
        """Should set session cookie with correct max age."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            session_cookie = next(
                (c for c in cookies if SESSION_COOKIE in c), None
            )

            assert f"Max-Age={SESSION_MAX_AGE}" in session_cookie

    def test_sets_httponly_on_cookies(self):
        """Should set HttpOnly flag on cookies."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            visitor_cookie = next(
                (c for c in cookies if VISITOR_COOKIE in c), None
            )
            session_cookie = next(
                (c for c in cookies if SESSION_COOKIE in c), None
            )

            assert "HttpOnly" in visitor_cookie
            assert "HttpOnly" in session_cookie

    def test_sets_samesite_lax_on_cookies(self):
        """Should set SameSite=Lax on cookies."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        with self.app.test_client() as client:
            response = client.get("/")

            cookies = response.headers.getlist("Set-Cookie")
            visitor_cookie = next(
                (c for c in cookies if VISITOR_COOKIE in c), None
            )
            session_cookie = next(
                (c for c in cookies if SESSION_COOKIE in c), None
            )

            assert "SameSite=Lax" in visitor_cookie
            assert "SameSite=Lax" in session_cookie

    def test_generates_64_char_visitor_id(self):
        """Should generate 64-character visitor ID."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        captured = {}

        @self.app.route("/check")
        def check():
            ctx = get_context()
            if ctx:
                captured["visitor_id"] = ctx.visitor_id
            return "ok"

        with self.app.test_client() as client:
            client.get("/check")

            assert len(captured.get("visitor_id", "")) == 64

    def test_generates_64_char_session_id(self):
        """Should generate 64-character session ID."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        captured = {}

        @self.app.route("/check")
        def check():
            ctx = get_context()
            if ctx:
                captured["session_id"] = ctx.session_id
            return "ok"

        with self.app.test_client() as client:
            client.get("/check")

            assert len(captured.get("session_id", "")) == 64

    def test_skips_custom_paths(self):
        """Should skip custom skip paths."""
        config.init(api_key="sk_test_123", skip_paths=["/internal"])
        init_app(self.app)

        @self.app.route("/internal/metrics")
        def metrics():
            return "metrics"

        with self.app.test_client() as client:
            response = client.get("/internal/metrics")

            assert response.status_code == 200
            assert VISITOR_COOKIE not in response.headers.get("Set-Cookie", "")

    def test_request_still_works_on_error(self):
        """Should allow request to complete even if exception occurs in route."""
        config.init(api_key="sk_test_123")
        init_app(self.app)

        @self.app.route("/error")
        def error_route():
            raise ValueError("Test error")

        @self.app.errorhandler(ValueError)
        def handle_error(e):
            return "Error handled", 500

        with self.app.test_client() as client:
            response = client.get("/error")

            assert response.status_code == 500
            # Context should still be cleared
            assert get_context() is None
