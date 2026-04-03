"""Device fingerprint generation — matches server-side SHA256(ip|user_agent)[0:32]."""

import hashlib


def device_fingerprint(ip: str, user_agent: str) -> str:
    """Compute a device fingerprint from IP and User-Agent.

    Produces a 32-char hex string identical to the server-side computation
    and the Ruby/Node SDKs.
    """
    return hashlib.sha256(f"{ip}|{user_agent}".encode()).hexdigest()[:32]
