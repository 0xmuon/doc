# Week 5 — Remaining steps after G (HTTP only)

Source: `week5.pdf`, steps after **G. Connect Backend to Database**.
HTTPS work (OpenSSL/Apache 443, CloudFront, the frontend-https bucket) is
**deferred by decision** — ignore anything https-related below and in the
PDF's last page until you decide to pick it up again.

Current state: EC2 `ecommerce_backend`, Apache on port 80 proxying to
FastAPI `127.0.0.1:8000`, RDS in us-east-1, Swagger at
`http://<public-IP>/docs`, the http frontend bucket serving the site over
plain HTTP.

## 1. Lambda: product refresh — every 5 minutes

Code is ready in this repo: `lambda_functions/product_refresh/`
(`lambda_function.py` + deploy README there).

It fetches `GET /api/products` from the live backend and logs
`ok / product_count / in_stock_count` per run. That exercises Apache →
FastAPI → RDS every interval, so a dead backend shows in CloudWatch within
5 minutes.

Why 5 minutes and not the PDF's 1-minute health-check rate: the catalog is
seeded and changes rarely. 1 minute ≈ 43k Lambda calls + 43k RDS queries a
month for the same signal; 5 minutes ≈ 8.6k and detects problems just as
well. Use `rate(1 minute)` only if you demo it live and want to see log
lines arrive quickly.

Deploy in short (full steps in the lambda README):

1. Lambda `ecommerce-product-refresh`, Python 3.12, **no VPC**.
2. Paste/zip-upload `lambda_function.py`, Deploy.
3. Env: `PRODUCTS_URL=http://<public-IP>/api/products` (port 80 via Apache —
   never `:8000`; Uvicorn only listens on localhost). Timeout 15 s.
4. Test `{}` → expect `{"ok": true, "product_count": 10, ...}`.
5. Trigger: EventBridge schedule `rate(5 minutes)`.

## 2. (Optional) Lambda triggered by an S3 update

Uploading a new ZIP stops being a manual CodeBuild click:

1. IAM role for Lambda with `codebuild:StartBuild` on `frontend-build-http`.
2. Lambda `ecommerce-s3-deploy-trigger` (Python 3.12) that calls
   `codebuild.start_build(projectName="frontend-build-http")` when a key
   ending in `frontend-http.zip` arrives (handler skeleton: parse
   `event["Records"][0]["s3"]["object"]["key"]`).
3. `sourcecode-*` bucket → Properties → Event notifications → object-created,
   suffix `.zip`, destination = this Lambda.
4. Test: re-upload `frontend-http.zip` → CodeBuild history shows a build
   that started by itself.

Backend variant (only if asked): S3 event → Lambda → SSM Run Command on EC2
to download/unzip/restart. Lambda alone cannot deploy onto EC2.

## 3. Deferred (skip for now)

- OpenSSL + Apache 443 on EC2 (PDF last page, point 3)
- S3 + CloudFront edge distribution (PDF last page, point 4)
- The frontend-https bucket/build

When you resume these, CORS below changes: https origins are currently
**rejected by the code**, so they must be allowed again deliberately.

## CORS setup now (HTTP only, secure)

Code: `app/main.py` → `_cors_allowed_origins()` reads `CORS_ALLOWED_ORIGINS`
from the backend `.env` on EC2. No Apache header config — don't add
`Header set Access-Control-Allow-Origin` in Apache; duplicate CORS headers
invalidate the response in browsers.

On EC2, the backend `.env` should contain exactly the http frontend's
website endpoint (S3 → frontend-http bucket → Properties → Static website
hosting → Bucket website endpoint — copy it, don't type it):

```env
CORS_ALLOWED_ORIGINS=http://frontend-http-xy-1234.s3-website-us-east-1.amazonaws.com
```

Then restart the backend process (Uvicorn), not Apache.

Security enforced in code, regardless of what the env says:

- `"*"` is dropped — a wildcard must never be combined with
  `allow_credentials=True` (browsers reject it, and any site could ride a
  logged-in user's browser).
- Only `http://` origins pass for now; any `https://` entry is dropped and
  logged, so nothing https is allowed until HTTPS is deliberately deployed.
- Origins with a path (`http://host/app`) are dropped — an Origin is
  scheme + host (+ port) only; entries must be exact.
- Methods are limited to `GET, POST, PUT, PATCH, DELETE, OPTIONS` and
  headers to `Authorization, Content-Type` — no wildcard method/header echo.
- Local dev is unaffected: unset env falls back to
  `http://127.0.0.1:5173`, `http://localhost:5173`.

Verify from any terminal (replace with your real bucket endpoint):

```bash
# allowed origin → 200, header echoes the origin
curl -i -X OPTIONS http://<public-IP>/api/products \
  -H "Origin: http://frontend-http-xy-1234.s3-website-us-east-1.amazonaws.com" \
  -H "Access-Control-Request-Method: GET"

# https origin → must NOT be allowed right now (400, no allow-origin header)
curl -i -X OPTIONS http://<public-IP>/api/products \
  -H "Origin: https://frontend-http-xy-1234.s3-website-us-east-1.amazonaws.com" \
  -H "Access-Control-Request-Method: GET"

# random site → 400, no allow-origin header
curl -i -X OPTIONS http://<public-IP>/api/products \
  -H "Origin: http://evil.example.com" \
  -H "Access-Control-Request-Method: GET"
```

Swagger (`http://<public-IP>/docs`) needs no CORS entry — it is same-origin
with the API. The frontend ZIP that calls this backend must be built with
`VITE_API_BASE_URL=http://<public-IP>` (baked in at build time by
`frontend/src/api/client.js`).
