"""A dropped call must say why, instead of nothing at all.

Every SDK dropped a hit with no request and no log. That is why the page-cache
bug cost a full day on a live account: from the caller's side, a dropped
conversion and a delivered one look identical.

The warning is not behind a debug flag — the customers who hit this are
precisely the ones not running in debug.
"""

import logging

from mbuzz.client.conversion import conversion
from mbuzz.client.track import track
from mbuzz.config import config
from mbuzz.context import clear_context


class TestDroppedEvent:
    def setup_method(self):
        config.reset()
        clear_context()
        config.init(api_key="sk_test_123")

    def teardown_method(self):
        config.reset()
        clear_context()

    def test_warns_when_an_event_has_no_identity(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = track(event_type="page_view")

        assert result.success is False
        assert "page_view" in caplog.text
        assert "visitor_id" in caplog.text

    def test_the_warning_names_the_fix(self, caplog):
        """A warning the caller cannot act on is barely better than silence."""
        with caplog.at_level(logging.WARNING):
            track(event_type="page_view")

        assert "cache" in caplog.text.lower()

    def test_says_nothing_when_the_event_has_an_identity(self, caplog):
        with caplog.at_level(logging.WARNING):
            track(event_type="page_view", visitor_id="vis_123")

        assert "dropped" not in caplog.text


class TestDroppedConversion:
    def setup_method(self):
        config.reset()
        clear_context()
        config.init(api_key="sk_test_123")

    def teardown_method(self):
        config.reset()
        clear_context()

    def test_warns_when_a_conversion_has_no_identity(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = conversion(conversion_type="purchase")

        assert result.success is False
        assert "purchase" in caplog.text

    def test_says_nothing_when_the_conversion_has_an_identity(self, caplog):
        """Guarded so the warning cannot fire on the healthy path."""
        with caplog.at_level(logging.WARNING):
            conversion(conversion_type="purchase", visitor_id="vis_123")

        assert "dropped" not in caplog.text
