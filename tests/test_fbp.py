"""Tests for forwarding Meta's `_fbp` cookie on the session call.

Meta merges a server event with the browser Pixel's event for the same action
on `event_name` + `fbp` when their event IDs differ. The SDK reads the cookie
the Pixel already set and forwards it verbatim: never set, changed or invented.

End to end: sdk_integration_tests/scenarios/fbp_capture_test.rb.
"""

import pytest

from mbuzz.cookies import FBP_COOKIE, read_fbp
from mbuzz.session_endpoint import build_session_payload

FBP = "fb.1.1758585600000.1234567890"


class TestReadFbp:
    def test_reads_a_well_formed_value(self):
        assert read_fbp(FBP) == FBP

    def test_reads_a_value_with_metas_appendix(self):
        """Meta's server-side Parameter Builder appends a fifth segment."""
        assert read_fbp(f"{FBP}.AQECAQIB") == f"{FBP}.AQECAQIB"

    def test_absent_is_none(self):
        assert read_fbp(None) is None
        assert read_fbp("") is None

    @pytest.mark.parametrize(
        "value",
        [
            "not-a-meta-cookie",
            f"{FBP}.",
            f"{FBP}.a b",
            f"{FBP}.AQEC.AQEC",
            f"{FBP}.AQEC\n",
            "fb.1.1758585600000.abc.AQEC",
            "xx.1.1758585600000.1234567890.AQEC",
        ],
    )
    def test_drops_a_malformed_value(self, value):
        assert read_fbp(value) is None

    def test_cookie_name(self):
        assert FBP_COOKIE == "_fbp"


class TestSessionPayload:
    def _payload(self, **kwargs):
        return build_session_payload(
            visitor_id="vis_1",
            body={"url": "https://shop.test/", "referrer": ""},
            ip="203.0.113.9",
            user_agent="Mozilla/5.0",
            **kwargs,
        )["session"]

    def test_carries_fbp_when_present(self):
        assert self._payload(fbp=FBP)["fbp"] == FBP

    def test_omits_the_key_when_absent(self):
        """Omitted, not null."""
        assert "fbp" not in self._payload()
