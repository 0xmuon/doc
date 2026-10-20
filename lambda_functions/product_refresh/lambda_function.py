"""Product refresh check for ABC Shop.

Runs on a schedule (EventBridge rate(5 minutes) — see README.md).
Fetches the live product list from the backend and verifies it is healthy:
HTTP 200, valid JSON list, at least one product. This keeps the products
endpoint + RDS path exercised and leaves a CloudWatch log line per run, so a
dead backend or empty catalog shows up within 5 minutes instead of when a
customer notices.

Why 5 minutes, not 1: the catalog is seeded and changes rarely. 1 minute
would mean ~43k Lambda calls and ~43k RDS queries a month for the same
signal; 5 minutes (~8.6k/month) detects a problem just as usefully and
costs almost nothing.

Environment:
  PRODUCTS_URL  e.g. http://<ec2-public-ip>/api/products
                (Apache on port 80 proxies to FastAPI on 127.0.0.1:8000,
                so no :8000 here. Locally: http://127.0.0.1:8000/api/products)
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

TIMEOUT_SECONDS = 5


def _fetch_products(url):
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.status, json.loads(response.read().decode())


def lambda_handler(event, context):
    url = os.environ.get("PRODUCTS_URL", "").strip()
    checked_at = datetime.now(timezone.utc).isoformat()
    if not url:
        print("product_refresh ok=False error=PRODUCTS_URL not set")
        return {"ok": False, "error": "PRODUCTS_URL not set", "checked_at": checked_at}

    try:
        status, products = _fetch_products(url)
    except urllib.error.HTTPError as exc:
        print(f"product_refresh ok=False status={exc.code} url={url}")
        return {"ok": False, "status_code": exc.code, "url": url, "checked_at": checked_at}
    except Exception as exc:  # timeout, DNS, connection refused, bad JSON
        print(f"product_refresh ok=False error={exc} url={url}")
        return {"ok": False, "error": str(exc), "url": url, "checked_at": checked_at}

    if not isinstance(products, list):
        print(f"product_refresh ok=False status={status} error=response is not a list url={url}")
        return {"ok": False, "status_code": status, "error": "response is not a list", "checked_at": checked_at}

    in_stock = sum(1 for p in products if isinstance(p, dict) and (p.get("available_quantity") or 0) > 0)
    ok = status == 200 and len(products) > 0
    print(
        f"product_refresh ok={ok} status={status} products={len(products)} "
        f"in_stock={in_stock} url={url}"
    )
    return {
        "ok": ok,
        "status_code": status,
        "product_count": len(products),
        "in_stock_count": in_stock,
        "checked_at": checked_at,
    }
