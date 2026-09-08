"""Tests for the FastAPI/Starlette middleware.

pyproject.toml has advertised `Framework :: FastAPI` since before any FastAPI
middleware existed. Those users got no cookie minting at all — a silent-drop
path with nothing to do with caching.
"""

from unittest.mock import patch

import pytest

from mbuzz.config import config
from mbuzz.context import clear_context
from mbuzz.cookies import SESSION_ENDPOINT_PATH, VISITOR_COOKIE

starlette = pytest.importorskip("starlette")

from starlette.applications import Starlette  # noqa: E402
from starlette.responses import PlainTextResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from mbuzz.middleware.fastapi import MbuzzMiddleware  # noqa: E402


def _app():
    async def index(request):
        return PlainTextResponse("OK")

    app = Starlette(routes=[Route("/", index)])
    app.add_middleware(MbuzzMiddleware)
    return app


class TestFastAPIMiddleware:
    def setup_method(self):
        config.reset()
        clear_context()

    def teardown_method(self):
        config.reset()
        clear_context()

    def test_does_nothing_when_not_initialized(self):
        with TestClient(_app()) as client:
            response = client.get("/")

            assert response.status_code == 200
            assert VISITOR_COOKIE not in response.cookies

    def test_never_mints_on_a_page_response(self):
        """A page response may be cached and replayed to every visitor, so a
        Set-Cookie on it would hand everyone the same id. Only the session
        endpoint mints — no cache stores a POST."""
        config.init(api_key="sk_test_123")

        with patch("mbuzz.session_endpoint.post"):
            with TestClient(_app()) as client:
                response = client.get(
                    "/", headers={"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"}
                )

        assert VISITOR_COOKIE not in response.cookies

    def test_reuses_an_existing_visitor_cookie(self):
        config.init(api_key="sk_test_123")

        with patch("mbuzz.session_endpoint.post") as mock_post:
            with TestClient(_app()) as client:
                client.cookies.set(VISITOR_COOKIE, "vis_existing")
                client.get(
                    "/", headers={"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"}
                )

            assert mock_post.call_args[0][1]["session"]["visitor_id"] == "vis_existing"

    def test_skips_a_sub_request(self):
        """Only a real page navigation opens a session."""
        config.init(api_key="sk_test_123")

        with patch("mbuzz.session_endpoint.post") as mock_post:
            with TestClient(_app()) as client:
                client.get("/", headers={"Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty"})

            assert not mock_post.called

    def test_serves_the_session_endpoint(self):
        """The one request that still reaches the app on a cached page."""
        config.init(api_key="sk_test_123")

        with patch("mbuzz.session_endpoint.post") as mock_post:
            with TestClient(_app()) as client:
                response = client.post(SESSION_ENDPOINT_PATH, json={"url": "https://shop.test/x"})

            assert response.status_code == 204
            assert VISITOR_COOKIE in response.cookies
            assert mock_post.call_args[0][1]["session"]["url"] == "https://shop.test/x"
