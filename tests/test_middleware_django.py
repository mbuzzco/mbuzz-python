"""Tests for the Django middleware.

pyproject.toml has advertised `Framework :: Django` since before any Django
middleware existed. Those users got no cookie minting at all.
"""

from unittest.mock import patch

import pytest

from mbuzz.config import config
from mbuzz.context import clear_context
from mbuzz.cookies import SESSION_ENDPOINT_PATH, VISITOR_COOKIE

django = pytest.importorskip("django")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DEBUG=True,
        ALLOWED_HOSTS=["*"],
        DATABASES={},
        INSTALLED_APPS=[],
        SECRET_KEY="test-only-not-a-credential",
    )
    django.setup()

from django.http import HttpResponse  # noqa: E402
from django.test import RequestFactory  # noqa: E402

from mbuzz.middleware.django import MbuzzMiddleware  # noqa: E402


def _middleware():
    return MbuzzMiddleware(lambda request: HttpResponse("OK"))


class TestDjangoMiddleware:
    def setup_method(self):
        config.reset()
        clear_context()
        self.factory = RequestFactory()

    def teardown_method(self):
        config.reset()
        clear_context()

    def test_does_nothing_when_not_initialized(self):
        response = _middleware()(self.factory.get("/"))

        assert response.status_code == 200
        assert VISITOR_COOKIE not in response.cookies

    def test_mints_a_visitor_cookie_on_a_page_view(self):
        config.init(api_key="sk_test_123")

        request = self.factory.get(
            "/", HTTP_SEC_FETCH_MODE="navigate", HTTP_SEC_FETCH_DEST="document"
        )
        with patch("mbuzz.session_endpoint.post"):
            response = _middleware()(request)

        assert VISITOR_COOKIE in response.cookies
        assert response.cookies[VISITOR_COOKIE]["httponly"]

    def test_reuses_an_existing_visitor_cookie(self):
        config.init(api_key="sk_test_123")

        request = self.factory.get(
            "/", HTTP_SEC_FETCH_MODE="navigate", HTTP_SEC_FETCH_DEST="document"
        )
        request.COOKIES[VISITOR_COOKIE] = "vis_existing"

        with patch("mbuzz.session_endpoint.post") as mock_post:
            _middleware()(request)

        assert mock_post.call_args[0][1]["session"]["visitor_id"] == "vis_existing"

    def test_skips_a_sub_request(self):
        config.init(api_key="sk_test_123")

        request = self.factory.get("/", HTTP_SEC_FETCH_MODE="cors", HTTP_SEC_FETCH_DEST="empty")
        with patch("mbuzz.session_endpoint.post") as mock_post:
            _middleware()(request)

        assert not mock_post.called

    def test_serves_the_session_endpoint(self):
        """The one request that still reaches the app on a cached page."""
        config.init(api_key="sk_test_123")

        request = self.factory.post(
            SESSION_ENDPOINT_PATH,
            data={"url": "https://shop.test/x"},
            content_type="application/json",
        )
        with patch("mbuzz.session_endpoint.post") as mock_post:
            response = _middleware()(request)

        assert response.status_code == 204
        assert VISITOR_COOKIE in response.cookies
        assert mock_post.call_args[0][1]["session"]["url"] == "https://shop.test/x"
