# mbuzz

Server-side multi-touch attribution for Python. Track customer journeys, attribute conversions, know which channels drive revenue.

Unlike client-side analytics, mbuzz runs server-side — no ad-blocker blind spots, no iOS tracking gaps, no browser privacy loss. Captures 30–40% more touchpoints than client-side tools.

## Installation

```bash
pip install mbuzz
```

Requires Python 3.9+.

## Quick Start

### 1. Initialize

```python
import mbuzz

mbuzz.init(api_key="sk_live_...")
```

Call `init()` once on app boot. For Flask apps, see [Flask Integration](#flask-integration) below.

### 2. Track Events

Track steps in the customer journey:

```python
mbuzz.event("page_view", url="/pricing")
mbuzz.event("add_to_cart", product_id="SKU-123", price=49.99)
mbuzz.event("checkout_started", cart_total=99.99)

# Group events into funnels for focused analysis
mbuzz.event("signup_start", funnel="signup", source="homepage")
mbuzz.event("signup_complete", funnel="signup")
```

### 3. Track Conversions

Record revenue-generating outcomes:

```python
mbuzz.conversion(
    "purchase",
    revenue=99.99,
    funnel="purchase",   # optional: group into funnel
    order_id=order.id,
)
```

### 4. Identify Users

Link visitors to known users (enables cross-device attribution):

```python
# On signup or login
mbuzz.identify(
    user.id,
    traits={
        "email": user.email,
        "name": user.name,
    },
)
```

## Funnels

Group related events into **funnels** for focused conversion analysis in your dashboard.

```python
# Signup funnel
mbuzz.event("pricing_view", funnel="signup")
mbuzz.event("signup_start", funnel="signup")
mbuzz.event("signup_complete", funnel="signup")

# Purchase funnel
mbuzz.event("add_to_cart", funnel="purchase")
mbuzz.event("checkout_started", funnel="purchase")
mbuzz.conversion("purchase", funnel="purchase", revenue=99.99)
```

**Why funnels?**
- Separate signup flow from purchase flow
- Analyze each conversion path independently
- Filter dashboard to specific customer journeys

## Flask Integration

mbuzz ships with a Flask middleware that handles visitor cookies, session resolution, and request context automatically.

```python
from flask import Flask
import mbuzz
from mbuzz.middleware.flask import init_app

app = Flask(__name__)

mbuzz.init(api_key="sk_live_...")
init_app(app)
```

After `init_app`, every request carries a `visitor_id` in context. Track events from anywhere in your request lifecycle:

```python
@app.route("/pricing")
def pricing():
    mbuzz.event("page_view", page="/pricing")
    return render_template("pricing.html")
```

Access the current visitor or user from context:

```python
mbuzz.visitor_id()   # Current visitor ID (from cookie)
mbuzz.user_id()      # Current user ID (if identify() was called)
```

## Django / FastAPI / Other Frameworks

The core `mbuzz.event`, `mbuzz.conversion`, and `mbuzz.identify` functions are framework-agnostic. You can call them from any Python web app or background job.

For framework-specific middleware contributions, see [Contributing](#contributing) below.

## Background Jobs

For tracking from Celery, RQ, or other background workers, pass `visitor_id` explicitly:

```python
# Capture at request time
@app.route("/checkout")
def checkout():
    visitor_id = mbuzz.visitor_id()
    process_order.delay(order.id, visitor_id)
    return redirect("/thank-you")

# Use in the job
@celery.task
def process_order(order_id, visitor_id):
    order = Order.get(order_id)
    mbuzz.conversion(
        "purchase",
        visitor_id=visitor_id,
        revenue=order.total,
    )
```

## Configuration Options

```python
mbuzz.init(
    api_key="sk_live_...",       # Required
    enabled=True,                # Default: True — toggle without code changes
    debug=False,                 # Default: False — enables verbose logging
    timeout=5.0,                 # Default: 5.0s — API request timeout
    skip_paths=["/health"],      # Optional — paths to skip tracking
    skip_extensions=[".css"],    # Optional — file extensions to skip
)
```

## The 4-Call Model

| Method | When to Use |
|---|---|
| `init` | Once on app boot |
| `event` | User interactions, funnel steps |
| `conversion` | Purchases, signups, any revenue event |
| `identify` | Login, signup, when you know the user |

## Error Handling

mbuzz never raises exceptions. All methods fail silently and log errors in debug mode — your application flow is never interrupted by tracking failures.

## Why Server-Side?

Client-side tracking loses 30–40% of marketing data to ad blockers, iOS tracking protections, and 7-day cookie caps. Server-side attribution runs inside your application, where requests flow through your own domain as first-party data — so you see the full customer journey.

Full explainer: [mbuzz.co/articles/server-side-vs-client-side-tracking](https://mbuzz.co/articles/server-side-vs-client-side-tracking)

## Attribution Models

mbuzz runs 8 attribution models side-by-side out of the box — first-touch, last-touch, linear, time-decay, position-based, Markov, Shapley, and data-driven — so you can see how much each model disagrees about which channel deserves credit.

## Requirements

- Python 3.9+
- No required dependencies for the core SDK
- `flask` only required if using the Flask middleware

## Links

- [Getting started](https://mbuzz.co/docs/getting-started)
- [Dashboard](https://mbuzz.co/dashboard)
- [Changelog](CHANGELOG.md)

## Contributing

PRs welcome — especially framework adapters (Django, FastAPI, Starlette) and async support.

## License

MIT License
