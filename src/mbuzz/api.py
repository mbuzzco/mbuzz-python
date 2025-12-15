"""HTTP client for mbuzz API communication."""

import json
import logging
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .config import config

logger = logging.getLogger("mbuzz")

VERSION = "0.1.0"


def post(path: str, payload: Dict[str, Any]) -> bool:
    """POST to API, return True on success, False on any failure.

    Never raises exceptions - all errors are caught and logged.
    """
    if not config._initialized or not config.enabled:
        return False

    try:
        response = _make_request(path, payload)
        return 200 <= response.status < 300
    except Exception as e:
        if config.debug:
            logger.error(f"mbuzz API error: {e}")
        return False


def post_with_response(path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """POST to API, return parsed JSON on success, None on failure.

    Never raises exceptions - all errors are caught and logged.
    """
    if not config._initialized or not config.enabled:
        return None

    try:
        response = _make_request(path, payload)
        if 200 <= response.status < 300:
            body = response.read().decode("utf-8")
            if config.debug:
                logger.debug(f"mbuzz response: {body}")
            return json.loads(body)
        return None
    except Exception as e:
        if config.debug:
            logger.error(f"mbuzz API error: {e}")
        return None


def _make_request(path: str, payload: Dict[str, Any]):
    """Make HTTP request to API."""
    base_url = config.api_url.rstrip("/")
    clean_path = path.lstrip("/")
    url = f"{base_url}/{clean_path}"

    data = json.dumps(payload).encode("utf-8")

    req = Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {config.api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", f"mbuzz-python/{VERSION}")

    if config.debug:
        logger.debug(f"mbuzz POST {url}: {payload}")

    return urlopen(req, timeout=config.timeout)
