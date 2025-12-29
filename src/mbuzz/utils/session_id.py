"""Deterministic session ID generation."""

import hashlib
import secrets
import time

SESSION_TIMEOUT_SECONDS = 1800
SESSION_ID_LENGTH = 64
FINGERPRINT_LENGTH = 32


def generate_deterministic(visitor_id: str, timestamp: int | None = None) -> str:
    """Generate session ID for returning visitors."""
    if timestamp is None:
        timestamp = int(time.time())
    time_bucket = timestamp // SESSION_TIMEOUT_SECONDS
    raw = f"{visitor_id}_{time_bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()[:SESSION_ID_LENGTH]


def generate_from_fingerprint(
    client_ip: str,
    user_agent: str,
    timestamp: int | None = None
) -> str:
    """Generate session ID for new visitors using IP+UA fingerprint."""
    if timestamp is None:
        timestamp = int(time.time())
    fingerprint = hashlib.sha256(
        f"{client_ip}|{user_agent}".encode()
    ).hexdigest()[:FINGERPRINT_LENGTH]
    time_bucket = timestamp // SESSION_TIMEOUT_SECONDS
    raw = f"{fingerprint}_{time_bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()[:SESSION_ID_LENGTH]


def generate_random() -> str:
    """Generate random session ID (fallback)."""
    return secrets.token_hex(32)
