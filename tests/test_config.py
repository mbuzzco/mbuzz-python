"""Tests for configuration module."""

import pytest
from mbuzz.config import Config, DEFAULT_API_URL, DEFAULT_TIMEOUT


class TestConfig:
    """Test Config class."""

    def setup_method(self):
        """Reset config before each test."""
        self.config = Config()

    def test_init_requires_api_key(self):
        """Should raise ValueError if api_key is missing."""
        with pytest.raises(ValueError, match="api_key is required"):
            self.config.init(api_key="")

        with pytest.raises(ValueError, match="api_key is required"):
            self.config.init(api_key=None)

    def test_init_sets_api_key(self):
        """Should set api_key on init."""
        self.config.init(api_key="sk_test_123")
        assert self.config.api_key == "sk_test_123"

    def test_init_sets_default_api_url(self):
        """Should use default API URL if not provided."""
        self.config.init(api_key="sk_test_123")
        assert self.config.api_url == DEFAULT_API_URL

    def test_init_allows_custom_api_url(self):
        """Should allow custom API URL."""
        self.config.init(api_key="sk_test_123", api_url="http://localhost:3000/api/v1")
        assert self.config.api_url == "http://localhost:3000/api/v1"

    def test_init_sets_default_timeout(self):
        """Should use default timeout if not provided."""
        self.config.init(api_key="sk_test_123")
        assert self.config.timeout == DEFAULT_TIMEOUT

    def test_init_allows_custom_timeout(self):
        """Should allow custom timeout."""
        self.config.init(api_key="sk_test_123", timeout=10.0)
        assert self.config.timeout == 10.0

    def test_init_sets_enabled_true_by_default(self):
        """Should enable tracking by default."""
        self.config.init(api_key="sk_test_123")
        assert self.config.enabled is True

    def test_init_allows_disabling(self):
        """Should allow disabling tracking."""
        self.config.init(api_key="sk_test_123", enabled=False)
        assert self.config.enabled is False

    def test_init_sets_debug_false_by_default(self):
        """Should disable debug by default."""
        self.config.init(api_key="sk_test_123")
        assert self.config.debug is False

    def test_init_allows_enabling_debug(self):
        """Should allow enabling debug mode."""
        self.config.init(api_key="sk_test_123", debug=True)
        assert self.config.debug is True

    def test_init_sets_initialized_flag(self):
        """Should set _initialized flag after init."""
        assert self.config._initialized is False
        self.config.init(api_key="sk_test_123")
        assert self.config._initialized is True

    def test_init_includes_default_skip_paths(self):
        """Should include default skip paths."""
        self.config.init(api_key="sk_test_123")
        assert "/health" in self.config.skip_paths
        assert "/static" in self.config.skip_paths
        assert "/assets" in self.config.skip_paths

    def test_init_merges_custom_skip_paths(self):
        """Should merge custom skip paths with defaults."""
        self.config.init(api_key="sk_test_123", skip_paths=["/custom"])
        assert "/health" in self.config.skip_paths
        assert "/custom" in self.config.skip_paths

    def test_init_includes_default_skip_extensions(self):
        """Should include default skip extensions."""
        self.config.init(api_key="sk_test_123")
        assert ".js" in self.config.skip_extensions
        assert ".css" in self.config.skip_extensions
        assert ".png" in self.config.skip_extensions

    def test_init_merges_custom_skip_extensions(self):
        """Should merge custom skip extensions with defaults."""
        self.config.init(api_key="sk_test_123", skip_extensions=[".custom"])
        assert ".js" in self.config.skip_extensions
        assert ".custom" in self.config.skip_extensions


class TestShouldSkipPath:
    """Test should_skip_path method."""

    def setup_method(self):
        """Set up config before each test."""
        self.config = Config()
        self.config.init(api_key="sk_test_123")

    def test_skips_health_endpoint(self):
        """Should skip health check endpoints."""
        assert self.config.should_skip_path("/health") is True
        assert self.config.should_skip_path("/healthz") is True
        assert self.config.should_skip_path("/ping") is True

    def test_skips_static_assets(self):
        """Should skip static asset paths."""
        assert self.config.should_skip_path("/static/app.js") is True
        assert self.config.should_skip_path("/assets/style.css") is True

    def test_skips_file_extensions(self):
        """Should skip paths with asset extensions."""
        assert self.config.should_skip_path("/bundle.js") is True
        assert self.config.should_skip_path("/style.css") is True
        assert self.config.should_skip_path("/logo.png") is True
        assert self.config.should_skip_path("/favicon.ico") is True

    def test_does_not_skip_regular_paths(self):
        """Should not skip regular page paths."""
        assert self.config.should_skip_path("/") is False
        assert self.config.should_skip_path("/about") is False
        assert self.config.should_skip_path("/pricing") is False
        assert self.config.should_skip_path("/api/users") is False


class TestReset:
    """Test reset method."""

    def test_reset_clears_configuration(self):
        """Should reset all configuration to defaults."""
        config = Config()
        config.init(
            api_key="sk_test_123",
            api_url="http://custom.url",
            debug=True,
            timeout=15.0,
        )

        config.reset()

        assert config.api_key == ""
        assert config.api_url == DEFAULT_API_URL
        assert config.debug is False
        assert config.timeout == DEFAULT_TIMEOUT
        assert config._initialized is False
