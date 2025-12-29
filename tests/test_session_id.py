"""Tests for deterministic session ID generation."""

import pytest
from mbuzz.utils.session_id import (
    generate_deterministic,
    generate_from_fingerprint,
    generate_random,
)


class TestGenerateDeterministic:
    sample_visitor_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    sample_timestamp = 1735500000

    def test_returns_64_char_hex_string(self):
        result = generate_deterministic(self.sample_visitor_id, self.sample_timestamp)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_is_consistent(self):
        result1 = generate_deterministic(self.sample_visitor_id, self.sample_timestamp)
        result2 = generate_deterministic(self.sample_visitor_id, self.sample_timestamp)
        assert result1 == result2

    def test_same_within_time_bucket(self):
        # bucket = timestamp / 1800
        # 1735500000 / 1800 = 964166
        # 1735500599 / 1800 = 964166 (last second of bucket)
        timestamp1 = 1735500000
        timestamp2 = 1735500001
        timestamp3 = 1735500599

        result1 = generate_deterministic(self.sample_visitor_id, timestamp1)
        result2 = generate_deterministic(self.sample_visitor_id, timestamp2)
        result3 = generate_deterministic(self.sample_visitor_id, timestamp3)

        assert result1 == result2
        assert result1 == result3

    def test_different_across_time_buckets(self):
        timestamp1 = 1735500000
        timestamp2 = 1735501800  # Next bucket

        result1 = generate_deterministic(self.sample_visitor_id, timestamp1)
        result2 = generate_deterministic(self.sample_visitor_id, timestamp2)

        assert result1 != result2

    def test_different_for_different_visitors(self):
        result1 = generate_deterministic("visitor_a", self.sample_timestamp)
        result2 = generate_deterministic("visitor_b", self.sample_timestamp)

        assert result1 != result2


class TestGenerateFromFingerprint:
    sample_ip = "203.0.113.42"
    sample_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    sample_timestamp = 1735500000

    def test_returns_64_char_hex_string(self):
        result = generate_from_fingerprint(
            self.sample_ip, self.sample_user_agent, self.sample_timestamp
        )
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_is_consistent(self):
        result1 = generate_from_fingerprint(
            self.sample_ip, self.sample_user_agent, self.sample_timestamp
        )
        result2 = generate_from_fingerprint(
            self.sample_ip, self.sample_user_agent, self.sample_timestamp
        )
        assert result1 == result2

    def test_same_within_time_bucket(self):
        timestamp1 = 1735500000
        timestamp2 = 1735500001

        result1 = generate_from_fingerprint(
            self.sample_ip, self.sample_user_agent, timestamp1
        )
        result2 = generate_from_fingerprint(
            self.sample_ip, self.sample_user_agent, timestamp2
        )

        assert result1 == result2

    def test_different_across_time_buckets(self):
        timestamp1 = 1735500000
        timestamp2 = 1735501800

        result1 = generate_from_fingerprint(
            self.sample_ip, self.sample_user_agent, timestamp1
        )
        result2 = generate_from_fingerprint(
            self.sample_ip, self.sample_user_agent, timestamp2
        )

        assert result1 != result2

    def test_different_for_different_ips(self):
        result1 = generate_from_fingerprint(
            "192.168.1.1", self.sample_user_agent, self.sample_timestamp
        )
        result2 = generate_from_fingerprint(
            "192.168.1.2", self.sample_user_agent, self.sample_timestamp
        )

        assert result1 != result2

    def test_different_for_different_user_agents(self):
        result1 = generate_from_fingerprint(
            self.sample_ip, "Mozilla/5.0 Chrome", self.sample_timestamp
        )
        result2 = generate_from_fingerprint(
            self.sample_ip, "Mozilla/5.0 Safari", self.sample_timestamp
        )

        assert result1 != result2


class TestGenerateRandom:
    def test_returns_64_char_hex_string(self):
        result = generate_random()
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_returns_unique_ids(self):
        result1 = generate_random()
        result2 = generate_random()
        assert result1 != result2


class TestCrossMethod:
    def test_deterministic_and_fingerprint_produce_different_ids(self):
        visitor_id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        ip = "203.0.113.42"
        user_agent = "Mozilla/5.0"
        timestamp = 1735500000

        deterministic = generate_deterministic(visitor_id, timestamp)
        fingerprint = generate_from_fingerprint(ip, user_agent, timestamp)

        assert deterministic != fingerprint
