# Changelog

## 0.7.3 (2026-02-03)

### Added

- **Navigation-aware session creation** — middleware now only creates server-side sessions for real page navigations, filtering out Turbo frames, htmx partials, fetch/XHR, prefetch, and other sub-requests. Uses browser-enforced `Sec-Fetch-*` headers as the primary signal with a framework-specific blacklist fallback for old browsers.
- `device_fingerprint()` utility — computes `SHA256(ip|user_agent)[0:32]`, matching the server-side fingerprint for session deduplication.
- Async session creation via `POST /sessions` — fire-and-forget background thread on real navigations.

### Fixed

- **5x visit count inflation** caused by concurrent sub-requests (Turbo frames, htmx) each creating separate sessions on first page load.

## 0.7.0 (2026-01-15)

- Initial release with Flask middleware, visitor cookie management, event tracking, user identification, and conversion tracking.
- Session cookie removed — server handles session resolution via device fingerprint.
