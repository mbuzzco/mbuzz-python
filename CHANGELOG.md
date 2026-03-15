# Changelog

## 0.8.2 (2026-03-15)

### Changed

- **Removed `api_url` from `init()` parameters** — the proxy URL (`https://api.mbuzz.co/api/v1`) is now hardcoded. This prevents accidental bypass of the edge ingest proxy. For development, `config.api_url` can still be set directly after init.

### Fixed

- **`event()` and `conversion()` now handle proxy-buffered responses gracefully** — when the edge proxy accepts a request but Rails is temporarily unreachable, the SDK returns `TrackResult(success=True)` with nil IDs instead of `TrackResult(success=False)`.

## 0.8.0 (2026-03-13)

### Changed

- **Default API URL updated to `https://api.mbuzz.co/api/v1`** — traffic now routes through the edge ingest proxy for improved reliability.

## 0.7.4 (2026-02-17)

### Fixed

- **`identify()` now writes `user_id` back to context** — after a successful API call, `user_id` is stored in the `RequestContext` so that subsequent `conversion()` calls in the same request can resolve it.

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
