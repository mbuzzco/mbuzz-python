"""Cookie constants for mbuzz SDK."""
import re
from typing import Optional

# NOTE: Session cookie removed in 0.7.0 - server handles session resolution

VISITOR_COOKIE = "_mbuzz_vid"
VISITOR_MAX_AGE = 63072000  # 2 years in seconds

# The one request that always reaches the app on a cached page. A cache never
# stores a POST, so this path is the only place the server can still mint.
SESSION_ENDPOINT_PATH = "/_mbuzz/session"

# Meta's browser id, written client-side by the customer's Meta Pixel. Read
# only, never set: forwarded on the session call so Meta can merge mbuzz's
# server event with the Pixel's browser event.
FBP_COOKIE = "_fbp"

# Meta's documented shape, fb.<subdomainIndex>.<creationTime>.<random>, plus
# the optional appendix Meta's server-side Parameter Builder adds
# (fb.1.<ts>.<random>.AQECAQIB). Both are valid to Meta.
_FBP_FORMAT = re.compile(r"fb\.\d+\.\d+\.\d+(?:\.[A-Za-z0-9_-]+)?")


def read_fbp(value: Optional[str]) -> Optional[str]:
    """The Pixel's _fbp, or None when absent or not in Meta's format.

    fullmatch, not match: `$` would accept a trailing newline. mbuzz never
    invents one and never rewrites what it forwards.
    """
    if not value or not _FBP_FORMAT.fullmatch(value):
        return None
    return value
