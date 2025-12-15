"""Configuration management for mbuzz SDK."""

from dataclasses import dataclass, field
from typing import List, Optional

DEFAULT_API_URL = "https://mbuzz.co/api/v1"
DEFAULT_TIMEOUT = 5.0

DEFAULT_SKIP_PATHS = [
    "/health",
    "/healthz",
    "/ping",
    "/up",
    "/static",
    "/assets",
    "/media",
    "/admin/jsi18n",
    "/__debug__",
]

DEFAULT_SKIP_EXTENSIONS = [
    ".js",
    ".css",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
]


@dataclass
class Config:
    """SDK configuration singleton."""

    api_key: str = ""
    api_url: str = DEFAULT_API_URL
    enabled: bool = True
    debug: bool = False
    timeout: float = DEFAULT_TIMEOUT
    skip_paths: List[str] = field(default_factory=list)
    skip_extensions: List[str] = field(default_factory=list)
    _initialized: bool = False

    def init(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        enabled: bool = True,
        debug: bool = False,
        timeout: Optional[float] = None,
        skip_paths: Optional[List[str]] = None,
        skip_extensions: Optional[List[str]] = None,
    ) -> None:
        """Initialize configuration."""
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.api_url = api_url or DEFAULT_API_URL
        self.enabled = enabled
        self.debug = debug
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.skip_paths = DEFAULT_SKIP_PATHS + (skip_paths or [])
        self.skip_extensions = DEFAULT_SKIP_EXTENSIONS + (skip_extensions or [])
        self._initialized = True

    def should_skip_path(self, path: str) -> bool:
        """Check if path should be skipped from tracking."""
        if any(path.startswith(skip) for skip in self.skip_paths):
            return True
        if any(path.endswith(ext) for ext in self.skip_extensions):
            return True
        return False

    def reset(self) -> None:
        """Reset configuration (for testing)."""
        self.api_key = ""
        self.api_url = DEFAULT_API_URL
        self.enabled = True
        self.debug = False
        self.timeout = DEFAULT_TIMEOUT
        self.skip_paths = []
        self.skip_extensions = []
        self._initialized = False


# Singleton instance
config = Config()
