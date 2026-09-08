"""Tests for the uncached session endpoint.

A full-page cache serves HTML without invoking the application, so the
tracking middleware never runs and no visitor cookie is minted. Every later
event is then dropped for having no one to attribute it to — silently, while
the page renders perfectly.

These tests cover the one request on such a page that still reaches the app.
"""

from unittest.mock import patch

from mbuzz.config import config
from mbuzz.context import clear_context
from mbuzz.cookies import SESSION_ENDPOINT_PATH, VISITOR_COOKIE, VISITOR_MAX_AGE
from mbuzz.session_endpoint import build_session_payload, is_session_request


class TestIsSessionRequest:
    """Only a POST to the endpoint path counts."""

    def test_matches_post_to_the_endpoint_path(self):
        assert is_session_request("POST", SESSION_ENDPOINT_PATH) is True

    def test_rejects_get_because_a_cache_may_store_it(self):
        """A GET is cacheable by an intermediary, which reintroduces the bug."""
        assert is_session_request("GET", SESSION_ENDPOINT_PATH) is False

    def test_rejects_another_path(self):
        assert is_session_request("POST", "/checkout") is False


class TestBuildSessionPayload:
    """The session belongs to the page, not to this endpoint."""

    def test_records_the_pages_url_not_the_endpoints(self):
        payload = build_session_payload(
            visitor_id="vis_123",
            body={"url": "https://shop.test/pricing", "referrer": "https://google.com"},
            ip="203.0.113.9",
            user_agent="Mozilla/5.0",
        )

        session = payload["session"]
        assert session["url"] == "https://shop.test/pricing"
        assert session["referrer"] == "https://google.com"
        assert SESSION_ENDPOINT_PATH not in (session["url"] or "")

    def test_carries_the_visitor_and_a_fingerprint(self):
        payload = build_session_payload(
            visitor_id="vis_123", body={}, ip="203.0.113.9", user_agent="Mozilla/5.0"
        )

        session = payload["session"]
        assert session["visitor_id"] == "vis_123"
        assert session["device_fingerprint"]
        assert session["session_id"]

    def test_survives_a_body_that_is_not_a_dict(self):
        """The customer's body-parser config is not something the fix can depend on."""
        payload = build_session_payload(
            visitor_id="vis_123", body=None, ip="1.1.1.1", user_agent="UA"
        )

        assert payload["session"]["url"] is None


class TestFlaskSessionEndpoint:
    """The endpoint, mounted in the Flask middleware."""

    def setup_method(self):
        config.reset()
        clear_context()

        from flask import Flask

        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

        @self.app.route("/")
        def index():
            return "OK"

    def teardown_method(self):
        config.reset()
        clear_context()

    def _init(self, **kwargs):
        from mbuzz.middleware.flask import init_app

        config.init(api_key="sk_test_123", **kwargs)
        init_app(self.app)

    def test_mints_a_visitor_cookie(self):
        self._init()

        with self.app.test_client() as client:
            with patch("mbuzz.session_endpoint.post"):
                response = client.post(SESSION_ENDPOINT_PATH, json={})

            assert response.status_code == 204
            assert VISITOR_COOKIE in response.headers.get("Set-Cookie", "")

    def test_the_cookie_stays_httponly_and_long_lived(self):
        """JS triggers the request; it never reads or writes the id.

        A cookie written by document.cookie is capped at 7 days under Safari's
        ITP — 24 hours after an ad click — which would be worse than the bug.
        """
        self._init()

        with self.app.test_client() as client:
            with patch("mbuzz.session_endpoint.post"):
                response = client.post(SESSION_ENDPOINT_PATH, json={})

            cookie = response.headers.get("Set-Cookie", "")
            assert "HttpOnly" in cookie
            assert f"Max-Age={VISITOR_MAX_AGE}" in cookie

    def test_the_response_is_never_cacheable(self):
        self._init()

        with self.app.test_client() as client:
            with patch("mbuzz.session_endpoint.post"):
                response = client.post(SESSION_ENDPOINT_PATH, json={})

            assert "no-store" in response.headers.get("Cache-Control", "")

    def test_reuses_an_existing_visitor_cookie(self):
        """Two visitors on the same cached page must stay distinct.

        A cached Set-Cookie handing everyone the same id is corruption, not
        loss, and far harder to notice than a missing row.
        """
        self._init()

        with self.app.test_client() as client:
            client.set_cookie(VISITOR_COOKIE, "vis_existing", domain="localhost")

            with patch("mbuzz.session_endpoint.post") as mock_post:
                client.post(SESSION_ENDPOINT_PATH, json={})

            payload = mock_post.call_args[0][1]
            assert payload["session"]["visitor_id"] == "vis_existing"

    def test_records_the_session_against_the_page(self):
        self._init()

        with self.app.test_client() as client:
            with patch("mbuzz.session_endpoint.post") as mock_post:
                client.post(
                    SESSION_ENDPOINT_PATH,
                    json={"url": "https://shop.test/pricing", "referrer": "https://google.com"},
                )

            path, payload = mock_post.call_args[0]
            assert path == "/sessions"
            assert payload["session"]["url"] == "https://shop.test/pricing"

    def test_runs_even_when_the_path_is_skipped(self):
        """A customer's own skip_paths must not swallow the one request that
        still reaches the app on a cached page."""
        self._init(skip_paths=["/_mbuzz"])

        with self.app.test_client() as client:
            with patch("mbuzz.session_endpoint.post"):
                response = client.post(SESSION_ENDPOINT_PATH, json={})

            assert response.status_code == 204
            assert VISITOR_COOKIE in response.headers.get("Set-Cookie", "")

    def test_creates_a_session_despite_the_navigation_gate(self):
        """A fetch() can never satisfy sec-fetch-mode: navigate.

        Leaving that gate in front of the endpoint would mint the cookie and
        then silently skip the session — the same invisible half-failure.
        """
        self._init()

        with self.app.test_client() as client:
            with patch("mbuzz.session_endpoint.post") as mock_post:
                client.post(
                    SESSION_ENDPOINT_PATH,
                    json={},
                    headers={"Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty"},
                )

            assert mock_post.called

    def test_ignores_the_endpoint_when_the_sdk_is_disabled(self):
        self._init(enabled=False)

        with self.app.test_client() as client:
            response = client.post(SESSION_ENDPOINT_PATH, json={})

            assert VISITOR_COOKIE not in response.headers.get("Set-Cookie", "")
