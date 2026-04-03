"""Tests for device fingerprint utility."""

from mbuzz.utils.fingerprint import device_fingerprint


class TestDeviceFingerprint:
    """Test device_fingerprint matches server-side SHA256(ip|user_agent)[0:32]."""

    def test_ruby_parity(self):
        """Must produce identical output to Ruby: Digest::SHA256.hexdigest('127.0.0.1|Mozilla/5.0')[0,32]."""
        result = device_fingerprint("127.0.0.1", "Mozilla/5.0")
        assert result == "ea687534a507e203bdef87cee3cc60c5"

    def test_deterministic(self):
        """Same input must always produce same output."""
        a = device_fingerprint("10.0.0.1", "TestAgent/1.0")
        b = device_fingerprint("10.0.0.1", "TestAgent/1.0")
        assert a == b

    def test_unique_for_different_inputs(self):
        """Different inputs must produce different outputs."""
        a = device_fingerprint("10.0.0.1", "Agent-A")
        b = device_fingerprint("10.0.0.2", "Agent-A")
        c = device_fingerprint("10.0.0.1", "Agent-B")
        assert a != b
        assert a != c
        assert b != c

    def test_returns_32_char_hex(self):
        """Must return exactly 32 lowercase hex characters."""
        result = device_fingerprint("192.168.1.1", "Chrome/120")
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)
