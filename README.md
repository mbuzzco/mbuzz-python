# mbuzz-python

Python SDK for mbuzz multi-touch attribution.

## Installation

```bash
pip install mbuzz
```

## Quick Start

```python
import mbuzz

# Initialize (once on app start)
mbuzz.init(api_key="sk_live_...")

# Track events
mbuzz.event("page_view", url="/pricing")

# Track conversions
mbuzz.conversion("purchase", revenue=99.99)

# Identify users
mbuzz.identify("user_123", traits={"email": "user@example.com"})
```

## Documentation

See [mbuzz.co/docs/getting-started](https://mbuzz.co/docs/getting-started) for full documentation.
