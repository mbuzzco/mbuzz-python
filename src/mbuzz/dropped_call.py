"""A dropped call must say why, instead of nothing at all.

Every SDK dropped a hit with no request and no log: from the caller's side a
dropped conversion and a delivered one look identical. That silence is why the
page-cache bug cost a full day on a live account.

Deliberately NOT behind the debug flag — the customers who hit this are
precisely the ones not running in debug.
"""

import logging

logger = logging.getLogger("mbuzz")

_CACHE_HINT = (
    "If your pages are served from a full-page cache, mount the mbuzz "
    "middleware and call POST /_mbuzz/session from the page — see the README's "
    '"Full-page caching" section.'
)


def warn_missing_identity(call: str, name: str) -> None:
    """Warn that a call was dropped for having nobody to attribute it to."""
    logger.warning(
        '[mbuzz] dropped %s "%s": no visitor_id and no user_id. %s',
        call,
        name,
        _CACHE_HINT,
    )
