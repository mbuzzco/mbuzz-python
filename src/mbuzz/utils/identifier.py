"""ID generation utilities."""

import secrets


def generate_id() -> str:
    """Generate 64-character hex string (256 bits of entropy)."""
    return secrets.token_hex(32)
