"""Cookie constants for mbuzz SDK."""
# NOTE: Session cookie removed in 0.7.0 - server handles session resolution

VISITOR_COOKIE = "_mbuzz_vid"
VISITOR_MAX_AGE = 63072000  # 2 years in seconds

# The one request that always reaches the app on a cached page. A cache never
# stores a POST, so this path is the only place the server can still mint.
SESSION_ENDPOINT_PATH = "/_mbuzz/session"
