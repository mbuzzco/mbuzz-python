"""Every middleware forwards the Pixel's `_fbp` on both session paths.

The payload builder and cookie reader are covered in test_fbp.py. This pins the
wiring: each framework's page path and session-endpoint path must pass the
cookie through, because a call site that forgets it fails silently.
"""

from unittest.mock import patch

import pytest

from mbuzz.config import config
from mbuzz.context import clear_context
from mbuzz.cookies import FBP_COOKIE, SESSION_ENDPOINT_PATH, VISITOR_COOKIE

FBP = "fb.1.1758585600000.1234567890.AQECAQIB"
VISITOR = "a1b2c3d4" * 8
NAVIGATE = {"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"}


def _fbp_sent(mock):
    """The fbp argument of the single create_session_async call."""
    assert mock.call_count == 1, "the session should be created exactly once"
    args = mock.call_args.args
    return args[4] if len(args) > 4 else mock.call_args.kwargs.get("fbp")


@pytest.fixture(autouse=True)
def _sdk():
    config.reset()
    clear_context()
    config.init(api_key="sk_test_123")
    yield
    config.reset()
    clear_context()


class TestFlask:
    def _client(self, with_fbp):
        from flask import Flask

        from mbuzz.middleware.flask import init_app

        app = Flask(__name__)
        app.add_url_rule("/", "index", lambda: "OK")
        init_app(app)
        client = app.test_client()
        client.set_cookie(VISITOR_COOKIE, VISITOR)
        if with_fbp:
            client.set_cookie(FBP_COOKIE, FBP)
        return client

    def test_page_path_forwards_fbp(self):
        with patch("mbuzz.middleware.flask.create_session_async") as sent:
            self._client(True).get("/", headers=NAVIGATE)
        assert _fbp_sent(sent) == FBP

    def test_page_path_sends_none_without_the_cookie(self):
        with patch("mbuzz.middleware.flask.create_session_async") as sent:
            self._client(False).get("/", headers=NAVIGATE)
        assert _fbp_sent(sent) is None

    def test_endpoint_path_forwards_fbp(self):
        with patch("mbuzz.middleware.flask.create_session_async") as sent:
            self._client(True).post(SESSION_ENDPOINT_PATH, json={"url": "https://shop.test/"})
        assert _fbp_sent(sent) == FBP


class TestFastAPI:
    def _client(self, with_fbp):
        pytest.importorskip("starlette")
        from starlette.applications import Starlette
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from mbuzz.middleware.fastapi import MbuzzMiddleware

        async def index(request):
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/", index)])
        app.add_middleware(MbuzzMiddleware)
        client = TestClient(app)
        client.cookies.set(VISITOR_COOKIE, VISITOR)
        if with_fbp:
            client.cookies.set(FBP_COOKIE, FBP)
        return client

    def test_page_path_forwards_fbp(self):
        with patch("mbuzz.middleware.fastapi.create_session_async") as sent:
            self._client(True).get("/", headers=NAVIGATE)
        assert _fbp_sent(sent) == FBP

    def test_page_path_sends_none_without_the_cookie(self):
        with patch("mbuzz.middleware.fastapi.create_session_async") as sent:
            self._client(False).get("/", headers=NAVIGATE)
        assert _fbp_sent(sent) is None

    def test_endpoint_path_forwards_fbp(self):
        with patch("mbuzz.middleware.fastapi.create_session_async") as sent:
            self._client(True).post(SESSION_ENDPOINT_PATH, json={"url": "https://shop.test/"})
        assert _fbp_sent(sent) == FBP


class TestDjango:
    def _request(self, factory_method, path, with_fbp, **extra):
        django = pytest.importorskip("django")
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                DEBUG=True,
                ALLOWED_HOSTS=["*"],
                DATABASES={},
                INSTALLED_APPS=[],
                SECRET_KEY="test-only-not-a-credential",
            )
            django.setup()

        from django.test import RequestFactory

        request = getattr(RequestFactory(), factory_method)(path, **extra)
        request.COOKIES[VISITOR_COOKIE] = VISITOR
        if with_fbp:
            request.COOKIES[FBP_COOKIE] = FBP
        return request

    def _run(self, request):
        from django.http import HttpResponse

        from mbuzz.middleware.django import MbuzzMiddleware

        with patch("mbuzz.middleware.django.create_session_async") as sent:
            MbuzzMiddleware(lambda r: HttpResponse("OK"))(request)
        return sent

    def test_page_path_forwards_fbp(self):
        request = self._request(
            "get", "/", True, HTTP_SEC_FETCH_MODE="navigate", HTTP_SEC_FETCH_DEST="document"
        )
        assert _fbp_sent(self._run(request)) == FBP

    def test_page_path_sends_none_without_the_cookie(self):
        request = self._request(
            "get", "/", False, HTTP_SEC_FETCH_MODE="navigate", HTTP_SEC_FETCH_DEST="document"
        )
        assert _fbp_sent(self._run(request)) is None

    def test_endpoint_path_forwards_fbp(self):
        request = self._request(
            "post", SESSION_ENDPOINT_PATH, True,
            data='{"url": "https://shop.test/"}', content_type="application/json",
        )
        assert _fbp_sent(self._run(request)) == FBP
