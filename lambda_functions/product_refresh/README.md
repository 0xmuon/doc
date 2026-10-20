# Lambda: product refresh

Periodically fetches `GET /api/products` from the deployed backend and logs
whether the catalog is healthy (200 + non-empty product list). Catches a dead
backend / broken RDS path within one interval.

## Rate: every 5 minutes

EventBridge schedule: `rate(5 minutes)` (~8,640 runs/month).

The catalog is seeded and rarely changes, so 1-minute polling (the PDF's
health-check rate) would only multiply Lambda + RDS load ~5x for no better
signal. 5 minutes is the sweet spot for this project; use `rate(1 minute)`
only while demoing the trigger live.

## Deploy (console)

1. Lambda → Create function: name `ecommerce-product-refresh`,
   runtime **Python 3.12**, no VPC (it calls the public EC2 address).
2. Paste `lambda_function.py` → Deploy.
3. Configuration → Environment variables:
   `PRODUCTS_URL = http://<ec2-public-ip>/api/products`
   (Apache :80 → FastAPI :8000. Local test value:
   `http://127.0.0.1:8000/api/products`.)
4. Timeout: 15 s. Memory: 128 MB.
5. Test with `{}` → expect
   `{"ok": true, "status_code": 200, "product_count": 10, ...}`.
6. Add trigger → EventBridge (CloudWatch Events) → new rule →
   Schedule expression `rate(5 minutes)`.

## Verify

- CloudWatch → Log groups → `/aws/lambda/ecommerce-product-refresh`:
  one `product_refresh ok=True ... products=10` line every 5 minutes.
- Stop the backend on EC2 → within 5 minutes logs show `ok=False`.
- Start it again → `ok=True` returns.

## Zip (if you prefer uploading over pasting)

From this folder: `Compress-Archive lambda_function.py lambda_function.zip`
(PowerShell) and upload the zip in the Lambda console.
