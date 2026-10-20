# WEEK 5 — COMPLETE INTERVIEW GUIDE

Project: **ABC Shop** — React frontend, FastAPI backend, PostgreSQL, fake
payment/notification provider, deployed manually on AWS
(S3 + EC2/Apache + RDS + Lambda + CloudWatch). HTTPS/CloudFront is
deliberately **deferred**; the working deployment is HTTP.

Read in this order if time is short: §1 (what Week 5 was), §3 (architecture),
§4 (request flows), §6 (frontend changes), §10 (AWS services), §13 (10k users),
§14 (rapid Q&A). 12-hour plan is in §15.

---

# 1. What is in `week5.pdf` — step by step

Title: *Python Application Deployment on AWS Cloud Platform.*

## A. Provision PostgreSQL on Amazon RDS

- Full configuration, PostgreSQL Community, Sandbox template
- `db.t3.micro`, region **us-east-1**, identifier `ecommerce_database`
- Master username/password chosen by us, default VPC/AZ/subnets,
  security groups `default` + `rds-ec2-1`
- 20 GB storage, autoscaling to 100 GB, port **5432**
- Automated backup, 1-day retention, backup window 18:00

**Concept to say in interview:** RDS is managed Postgres — AWS handles
patching, backups, storage scaling; we only changed config, not code,
because SQLAlchemy just needs a different connection host.

## B. Provision EC2 backend application server

- `ecommerce_backend`, Ubuntu LTS, `t2.medium`, 25 GB, key `mykey`,
  security groups Launch-Wizard-1 + `ec2-rds-1`
- Terminal setup: `apt update/upgrade`, install python3, pip, FastAPI,
  **apache2**, postgresql client, zip/unzip, virtualenv
- Apache as reverse proxy:
  `a2enmod proxy proxy_http`, `ProxyPreserveHost On`,
  `ProxyPass / http://127.0.0.1:8000/`, `ProxyPassReverse` same

**Concept:** Apache is the public door (port 80). Uvicorn only listens on
`127.0.0.1:8000`, so FastAPI is never directly exposed. Apache preserves
the original Host header; proxying is why `http://<public-IP>/docs` works
without `:8000`.

## C. Create S3 buckets for source + frontend deployment

Three general-purpose buckets, **Block Public Access OFF**, **Versioning ON**:
- `sourcecode-xy-1234` — holds the ZIPs (source of truth)
- `frontend-http-xy-1234` — built site calling the HTTP API
- `frontend-https-xy-1234` — built site calling an HTTPS API (built, but
  HTTPS itself is deferred by our decision)

Permissions + **static website hosting** on the two frontend buckets
(index document `index.html`).

**Concept:** S3 website endpoints are HTTP-only. Bucket name, objects and
the website endpoint URL become important for CORS later (§7).

## D. Credentials in AWS Secrets Manager

- Secret `ecommerce-db-secrets`, type RDS, master username/password,
  linked to the DB instance so AWS fills host/port

**Concept:** Secrets leave the codebase/disk; applications fetch them
with an IAM identity, can be rotated, and access is audited in
CloudTrail. Our migration of this is implemented in code — see §8.

## E. Build frontend for S3 + upload backend

- Edit frontend `.env.production`/`.env` so the build points at
  `http://<public-IP>` (the EC2/Apache address)
- ZIP the frontend directory → upload to `sourcecode-*`
- Edit the env to the HTTPS URL → ZIP again with `-https` suffix → upload
- ZIP the backend → upload to `sourcecode-*`

**Concept (important):** in Vite, `VITE_API_BASE_URL` is **baked into the
JS bundle at build time** (`frontend/src/api/client.js` reads
`import.meta.env`). There is no runtime config on S3 — changing the API
address means rebuilding and re-uploading. Two buckets = two builds.

## F. CodeBuild projects

- `frontend-build-http`: source `s3://sourcecode-*/frontend-http.zip`,
  buildspec builds and syncs output to the `frontend-http-*` bucket
- Twin project for https → `frontend-https-*` bucket
- Run builds; attach `S3FullAccess` to the CodeBuild role if denied

**Concept:** CodeBuild is a managed build server — no build machine to
maintain; the buildspec YAML is the pipeline in code. Builds are started
**manually** in our final scope (the S3-trigger Lambda was decided
against and removed).

## G. Connect backend to database

1. Download backend ZIP from S3 on EC2, unzip into the app folder
2. `pip install -r requirements.txt` in the venv
3. Create `.env` if required
4. Change DB code to fetch credentials with **boto3** from Secrets
   Manager (secret name + region) instead of hardcoding
5. Run Uvicorn on `127.0.0.1:8000`
6. Test backend+DB on Uvicorn
7. Manually test endpoints in Swagger UI

## Last page — the four remaining items

1. Lambda health check every 1 minute
2. (Optional) Lambda triggered by S3 update for frontend/backend
3. OpenSSL + Apache config on EC2 (HTTPS)
4. S3 + CloudFront edge distribution

**Our final scope decision (say this confidently):** we implemented
CORS for HTTP only, **one** Lambda (product refresh — ours fetches the
products endpoint every 5 minutes instead of a bare /health ping, which
exercises Apache→FastAPI→RDS), CloudWatch basics, and the Secrets
Manager migration. HTTPS items (3) and (4), and the S3-trigger Lambda
(2), were consciously deferred — sandbox limits + self-signed IP certs
can't serve a browser frontend anyway.

The companion checklist (`week5-overview-checklist.pdf`) phrases the same
work as 6 milestones: 1 S3 frontend, 2 EC2 backend, 3 RDS,
4 Lambda event-driven, 5 CloudWatch, 6 end-to-end test & validate.

---

# 2. System architecture

## 2.1 On AWS (Week 5 target, HTTP scope)

```text
                         ┌──────────────────── EC2 ecommerce_backend (Ubuntu, t2.medium)
Browser ──HTTP──────────►│ Apache :80 (public, ProxyPass)
 (S3 website)            │    │ 127.0.0.1:8000
                         │    ▼
                         │ Uvicorn/FastAPI :8000 ──► provider (Uvicorn :9000, 127.0.0.1 only)
                         │    │                         ▲ card charge + email notify
                         │    └── boto3 at boot ──► Secrets Manager (DB creds + jwt_secret)
                         └────┼────────────────────────────────────────────
                              │ 5432 (security group rds-ec2-1)
                              ▼
                         RDS PostgreSQL (db.t3.micro, us-east-1)

S3 frontend-http bucket ──serves──► Browser (JS bundle calls http://<public-IP>/api/...)
S3 sourcecode bucket ──ZIPs──► CodeBuild frontend-build-http ──► frontend-http bucket
Lambda ecommerce-product-refresh ──EventBridge rate(5m)──► GET http://<public-IP>/api/products
CloudWatch ◄── Lambda logs/metrics, EC2 metrics, RDS metrics, alarms (SNS restricted in sandbox)
```

Key properties to verbalise:
- **Only Apache :80 and SSH :22 are public.** FastAPI :8000, provider
  :9000 and RDS :5432 are private/local — defence in depth via binding +
  security groups.
- The frontend is a static bundle; the browser talks **only** to the
  backend. It never calls :9000 (payment) or the DB.
- Lambda sits *outside* the request path — monitoring/synthetic check,
  not a runtime dependency. If Lambda dies, the shop still works.

## 2.2 Locally (how we develop)

Docker Compose `shopping-simple`: `db` Postgres 17 (:5433 host),
`api` FastAPI with debugpy+reload (:8000, :5678), `provider` (:9000).
Vite (:5173) proxies `/api` → :8000, so in dev there is effectively no
CORS and no `VITE_API_BASE_URL`. The same code runs both places; only
configuration changes (env/systemd/Secrets Manager).

---

# 3. Backend codebase tour (know these cold)

Layered flow: **Router → Service → Repository → SQLAlchemy model**,
Pydantic schema validates in/out. `app/main.py` builds the FastAPI app,
adds CORSMiddleware then RequestLogMiddleware (added last ⇒ runs first,
sees final status), exception handlers return `{detail, request_id}`,
`/health`, `/health/db` (runs `SELECT 1`), `/metrics`.

| Area | Files | What to say |
|---|---|---|
| Auth | `routers/auth_router.py`, `utils/security.py`, `utils/deps.py`, `utils/permissions.py` | Argon2 password hashing (pwdlib). JWT HS256 access (60m) + refresh (7d) tokens, `type` claim separates them; routes trust the **Users row's** role, not the token's stale role claim. Casbin enforces `order:read:own` etc.; owner checks on top. |
| Products | `product_router`, `product_service`, `product_repository` | Search by name/category, out-of-stock sorted last (also enforced again in the UI). |
| Cart | `cart_router/service/repository` | One OPEN cart per user; quantity validated against stock and `MAX_QUANTITY_PER_ITEM`. |
| Orders | `order_router`, `order_service`, `integrations/payment_gateway.py`, `integrations/circuit_breaker.py`, `integrations/notification.py` | The heart — see §4.3. |
| Provider | `provider/main.py` | Stand-in payment+email API, modes ok/fail/slow, idempotency-key on charges, `/sent` for verification. |
| DB | `db/session.py`, `db/async_session.py`, `db/seed.py`, `app/secrets.py` | Sync engine for most routes, async session for checkout/health-db. Seed creates categories/products/users idempotently; prices end in 99 INR. |
| Ops | `utils/logging_setup.py`, `utils/metrics.py` | Structured JSON log events with `request_id` per request; circuit state transitions logged (`circuit_off`, `payment_result`, `notification_failed`); `/metrics` route counters + breaker state. |

Errors are `AppException` → consistent JSON. Unhandled exceptions are
logged and returned as plain 500 (no stack traces to clients).

---

# 4. Request flows (draw these on a whiteboard)

## 4.1 Browse products

Browser loads bundle from S3 → JS `GET {API_BASE}/api/products` →
Apache → FastAPI `product_router` → service → repository → RDS →
JSON (name, price, `available_quantity`, image URL) → ProductCard grid.
Search is debounced 300 ms; a race guard stops an older slow response
replacing a newer one.

## 4.2 Login / session

`POST /api/auth/login {email,password}` → Argon2 verify → access +
refresh JWTs → browser stores them in localStorage
(`abcshop.accessToken/RefreshToken`). `api()` attaches
`Authorization: Bearer`. On **401** it calls `/api/auth/refresh` once
(single-flight — concurrent 401s share one refresh promise), retries
the original call once; if refresh fails it clears tokens and fires
the session-expired handler (redirect to login). That's in
`frontend/src/api/client.js` and is a favourite interview topic.

## 4.3 Card checkout (the flow that broke and we fixed)

1. `POST /api/orders/checkout` (async session). Order row is written
   first: stock reserved (quantities decremented), cart marked ordered,
   prices copied — one transaction.
2. `charge_order` POSTs `{PAYMENT_API_URL}` = provider
   `/payments/charge` with `Idempotency-Key: <order_number>`; retries
   (default 3, backoff) on timeout/5xx; a 402 decline is **not**
   retried and does not count against the breaker.
3. **Circuit breaker**: 3 gateway failures → half-open; next failure →
   open (`circuit breaker is off`) and charges are skipped fast for
   30 s; before failing fast it probes the provider
   `/mode` — if `ok`, it half-opens and tries one real charge.
4. Success → order `CONFIRMED/PAID` with `PAY-xxxx` reference. Failure
   → `PAYMENT_FAILED`, stock released back.
5. Notification is a **BackgroundTask after the response**
   (`POST /notify`), retried 3×; a failed email never changes the order.

**Our production bug (great story):** provider was up (`curl
127.0.0.1:9000/mode` fine) but payments failed with "gateway
unreachable". Logs showed the breaker open and *only our curls* in the
provider log — the backend process had `PAYMENT_API_URL=http://provider:9000`
(a Docker hostname) from the old env, so its calls died on DNS. Fix:
restart the backend with `http://127.0.0.1:9000/...`; restarting also
reset the in-memory breaker. Lesson: verify the *process's* environment
(`/proc/<pid>/environ`), not your shell's.

COD instead skips the provider entirely: `PENDING + CONFIRMED` always.

## 4.4 Product refresh Lambda

EventBridge `rate(5 minutes)` → Lambda GET
`http://<public-IP>/api/products` → validates 200 + non-empty list →
logs `product_refresh ok=True products=10 in_stock=8`. Chosen over
1-minute health pings: catalog is near-static, 5 min ≈ 8.6k
invocations/month vs 43k, same detection value. CloudWatch metric
filter on `ok=False` is the real “shop is down” alarm (the Lambda
returns 200 even when the backend is dead).

---

# 5. Frontend changes compared to last week (codebase terms)

Last week's frontend was a locally-run Vite app. This week's is a
**deployable production bundle**. Concrete changes:

## 5.1 Build-time API configuration (the Week-5 enabler)
- `src/api/client.js`: `const API_BASE = import.meta.env.VITE_API_BASE_URL || ""`.
  Dev: empty ⇒ relative `/api` ⇒ Vite proxy to :8000. S3 build: set to
  `http://<public-IP>` before `npm run build`; the value is inlined into
  the bundle. No runtime config exists on S3 — rebuild to change it.
- Two ZIPs/builds (http/https) exist precisely because of this inlining.

## 5.2 Central API client hardening (`client.js`)
- All calls go through one `api()` helper: JSON, `Authorization: Bearer`,
  error normalisation into `ApiError {message, status, fieldErrors, requestId}`.
- FastAPI validation arrays (`detail: [...]`) are flattened into
  per-field errors + a readable message; 502/503/504 become
  "shop is unavailable"; backend `request_id` is appended as `(ref: …)`.
- **401 handling:** single-flight token refresh (§4.2) shared via a
  module-level `refreshing` promise; retry once; on failure clear
  tokens + session-expired callback. Tokens in localStorage keys
  `abcshop.accessToken` / `abcshop.refreshToken`.

## 5.3 Pages & routing (`App.jsx`, `pages/`)
- React Router with `Layout` (Header/main/Footer) around every page;
  `/` and `/home` both render Home.
- Pages: Home, Products, ProductDetails, Cart, Checkout, Orders,
  OrderDetails, Profile, Login, Register, NotFound. Cart/checkout/
  orders/profile are `ProtectedRoute` (redirect to /login remembering
  the intended path).
- Register shows a success dialog → routes to Login; signed-in home
  greets `Hi <firstName>`.

## 5.4 State (React Context, no Redux — deliberate)
- `AuthContext` (user/token/ready gate), `CartContext` (cart state per
  user-id, `itemCount`, `overStock` flag, `notifyAdded` → 5-second
  cart toast via `CartToast`).
- Header shows cart icon + red count badge beside the profile link;
  logging out clears session, cart resets via context.

## 5.5 Products UX (`ProductsPage`, `SearchBar`, `ProductCard`)
- Debounced (300 ms) search with stale-response guard; search merges
  name matches + category matches when no category filter is set,
  de-dupes by product_id, and pins out-of-stock products last.
- **`type=search` bug we fixed:** our unlayered `.field{width:100%}`
  overrode Tailwind's layered `sm:w-52` on the category `<select>`,
  squeezing the search box to 0 px. Fix: `.field` moved into
  `@layer components` (utilities then win) + a dedicated `.search-bar`
  (2 px border, icon, solid placeholder, focus ring, Clear button).
  Same fix healed `w-20/w-24` quantity inputs. *Know this story — it's
  a pure CSS-cascade-layers explanation.*
- Cards: category label, truncated/clamped description
  (`line-clamp-2`), price in INR (`utils/money.js` `inr()`),
  `In cart: N`, full-width yellow Add to Cart, red Out-of-stock badge.
- **Low-stock urgency** (`utils/stock.js`, tested): 
  `remaining = available_quantity − in-cart`; at 1–5 shows
  "Only N items left — hurry!", counting down 5→4→3 as you add;
  at 0, "All available stock is in your cart". On card + details page.

## 5.6 Validation & feedback (`utils/validate.js`, `hooks/useForm.js`)
- Name ≥ 6 letters (letters/spaces), email shape, +91-style phone via
  profile forms, quantity 1..stock and ≤ `VITE_MAX_QUANTITY_PER_ITEM`.
- Field errors show on blur/submit (`useForm` touched-state pattern).
- `utils/loadError.js` (`describeLoadError/describeActionError`) maps
  failures to friendly Loading/Error/Empty states
  (`components/common/StatusMessage.jsx`) used on every page — a failed
  fetch is never rendered as "empty data".
- Status pills (`StatusBadge`, `utils/statusLabels.js`) for order/
  payment states; after checkout the app navigates to
  `/orders/{orderId}`; failed orders offer Pay-again / Return-to-cart.

## 5.7 Visual system (the "doesn't look AI-generated" pass)
- Typography: Bricolage Grotesque (display) + Public Sans (body) via
  Google Fonts in `index.html`; earlier Fraunces/cream look removed.
- Flat `#f5f5f5` background (grid pattern removed), hard 2 px borders,
  2 px radii, red brand accents, blue primary, yellow cart CTA —
  defined once in `src/index.css` as `@theme` tokens + plain-CSS
  component classes (panels, buttons, hero, product cards).
- Home hero: full-bleed Unsplash store photo, dark left shade, two
  CTAs; header: red 3 px top stripe, underline active nav, sticky.

## 5.8 Tests
- Vitest unit tests next to utils: `validate.test.js`, `stock.test.js`
  (countdown, singular/plural, silence above threshold). 9 tests pass.

**One-line summary for the interviewer:** "Last week the frontend only
ran behind the Vite dev proxy; this week it's a self-contained build
whose API endpoint, token-refresh API client, low-stock/search UX and
deploy packaging were built for S3 + CodeBuild."

# 6. CORS — exactly how it is set up now

- Browser origin = the S3 website endpoint, copied exactly from
  bucket → Properties → Static website hosting:
  `http://frontend-http-xy-1234.s3-website-us-east-1.amazonaws.com`.
- Backend: `app/main.py` `_cors_allowed_origins()` reads the
  `CORS_ALLOWED_ORIGINS` env var (systemd `Environment=` on EC2).
  Unset locally ⇒ Vite origins only.
- **Hardening enforced in code** regardless of env: drop `*`, drop any
  `https://` origin (HTTP-only scope), drop origins containing a path;
  methods limited to GET/POST/PUT/PATCH/DELETE/OPTIONS; headers to
  `Authorization, Content-Type`. `allow_credentials=True` with explicit
  origins only (credentials + `*` is rejected by browsers anyway).
- Swagger needs no CORS (same origin). The frontend never calls :9000,
  so the provider needs no CORS at all.
- Verify: `curl -i -X OPTIONS <api>/api/products -H "Origin: <site>"`
  → allowed echoes `access-control-allow-origin`; https/random → 400
  with no such header. Apache must NOT add CORS headers (duplicates
  invalidate responses).
- Preflight: browsers send OPTIONS before cross-origin requests with
  `Authorization`; CORS is a *browser* rule — curl/Postman ignore it,
  which is why "it works in Postman" proves nothing.

---

# 7. Secrets Manager migration (implemented, ours to demo)

- Secret `ecommerce-db-secrets` (us-east-1) JSON:
  `username, password, host, port, dbname, jwt_secret`.
- `app/secrets.py`: boto3 `get_secret_value`, cached per process
  (`lru_cache`), **fail-fast** — if enabled but unreadable, boot raises
  instead of silently using default creds.
- Callers: `app/db/session.py` builds
  `postgresql+psycopg://…` (credentials URL-quoted); `app/utils/security.py`
  reads `jwt_secret`. Priority: plain env var (local/Docker/tests)
  → Secrets Manager when `USE_SECRETS_MANAGER=1`.
- EC2 identity: IAM role `ecommerce-ec2-secrets-role`, inline policy
  `GetSecretValue` on that one secret ARN, attached as the instance
  profile. No access keys on the box.
- `.env` deleted on EC2 (`shred -u`); non-secrets (region, secret name,
  CORS origin, provider URLs) live as systemd `Environment=` lines.
  Full runbook: `SECRETS_MANAGER.md`.
- Rotation story: rotate in Secrets Manager/RDS → restart service
  (cached per process) → picked up. Managed rotation for RDS is the
  production upgrade.

---

# 8. Lambda + CloudWatch (what we run)

- **One Lambda**: `ecommerce-product-refresh`
  (`lambda_functions/product_refresh/`), Python 3.12, stdlib only,
  EventBridge `rate(5 minutes)`, env `PRODUCTS_URL`. Tested locally:
  `ok=True products=10 in_stock=8`.
- **CloudWatch dashboard** `ecommerce-overview`
  (`CLOUDWATCH_SDE_GUIDE.md`): top-row health (EC2 `StatusCheckFailed`
  gauge, Lambda invocations bar, product-refresh failures number),
  EC2 CPU/credits/network, RDS storage/connections/latency, Lambda
  errors/duration p95, a Logs widget (Table for recent runs; Line/Bar
  only for `stats by bin` queries), and an alarm-status tile.
- **Alarms**: product-refresh failure metric filter (`ok=False` ≥ 1/5m),
  EC2 status check, EC2 CPU > 80%/15m, RDS free storage < 2 GB, RDS
  connections > 80, Lambda errors ≥ 1.
- **SNS** (email alerting): restricted in the sandbox → alarms run
  action-less and are watched on the dashboard; production = one SNS
  topic `ecommerce-alerts`, confirmed email subscription.
- Widget vocabulary to drop in conversation: Number (latest health),
  Gauge (bounded ranges — storage in **bytes** is the classic trap:
  20 GB = 21474836480), Line (trends/latency p95), Stacked area
  (in+out volumes), Bar (counts per period), Pie (share — low value
  here), Logs (Insights results), Text (row labels).

# 9. AWS — everything that exists for this project

## 9.1 Used (implemented)

| Service | Role here |
|---|---|
| S3 | Static frontend hosting (website endpoints), sourcecode ZIP bucket, versioning |
| EC2 | Backend host (Ubuntu, t2.medium), Apache reverse proxy + Uvicorn processes |
| RDS PostgreSQL | Managed DB (db.t3.micro, 20→100 GB autoscale, daily backups) |
| Apache (not AWS, on EC2) | Public entry :80 → Uvicorn :8000, host preservation |
| CodeBuild | Managed builds: ZIP → `npm run build` → sync to frontend bucket |
| Secrets Manager | DB creds + JWT secret, fetched by boto3 at boot |
| IAM | Instance profile for EC2 (least-privilege single-secret read), CodeBuild role |
| Security Groups | The firewall: 80/22 public; 5432 only from EC2 group; 8000/9000 never public |
| Lambda | Synthetic product-refresh check on a schedule |
| EventBridge | The schedule (`rate(5 minutes)`) that invokes the Lambda |
| CloudWatch | Metrics, Lambda log groups, Logs Insights, metric filters, alarms, dashboards |
| SNS | Designed (alert emails) — restricted in sandbox, production step |
| Swagger/OpenAPI | `/docs` is also our manual test harness (G.7) |

## 9.2 Not used, but could be (know what each would replace)

| Service | What we'd gain | Replaces/fixes |
|---|---|---|
| CloudFront | HTTPS for the frontend, CDN caching, one domain for site+API | The deferred HTTPS story; S3 website endpoints are HTTP-only |
| ACM | Free managed TLS certificates | Self-signed OpenSSL certs (browsers reject them for fetch) |
| Route 53 | Real domain/DNS (`api.shop.example`) | Bare public-IP URLs; certs can't cover IPs |
| ALB | HTTPS termination, load balancing across EC2s, health checks | Single-Apache entry point; enables multi-instance scaling |
| Auto Scaling Group | Adds/removes EC2s with load, self-healing | One hand-managed t2.medium |
| ECS Fargate / EKS | Container orchestration without managing hosts | Our systemd/Docker-on-EC2 hand-ops |
| API Gateway | Managed API front door, throttling, keys, WAF integration | Apache-as-gateway duties |
| WAF | Blocks common exploits/SQLi patterns at the edge | Nothing today beyond app validation |
| ElastiCache (Redis) | Cache products/sessions, rate-limit counters | Repeated identical RDS reads |
| SQS | Decouple payment/notification work from checkout | BackgroundTasks that die with the process |
| SES | Real transactional email | Fake provider `/notify` |
| Real payment gateway (Stripe/Razorpay) | Real charges, webhooks, PCI handled by them | Fake provider `/payments/charge` |
| RDS Proxy | Connection pooling + failover smoothing | Raw connections per process |
| RDS Multi-AZ / Read Replicas | HA + read scaling | Single-AZ db.t3.micro |
| CloudFormation / Terraform / CDK | Infrastructure as code, reproducible envs | All the manual console steps in Week 5 |
| CodePipeline / CodeDeploy | CI/CD with approvals and rollback | Manual ZIP → CodeBuild → restart flow |
| SSM Parameter Store | Cheap non-secret config | systemd Environment lines (secrets still belong in Secrets Manager) |
| KMS | Envelope encryption control, key rotation policies | Default AWS-managed encryption keys |
| CloudTrail / Config / GuardDuty | Audit who changed what, compliance, threat detection | Only app-level audit logs today |
| VPC Endpoints / NAT | Private subnets reaching S3/Secrets without internet | Everything currently in public-ish networking |
| CloudWatch Synthetics / X-Ray | Browser-level canaries, distributed tracing | Our single-endpoint Lambda canary; log-based debugging |
| Elastic IP | Stable public IP across stop/start | IP changes that break builds/CORS/env |

Be ready to say *why not yet*: sandbox scope, cost, and each adds
operational surface; the manual deployment was the learning objective.

---

# 10. Performance — how it works today, honestly

Bottlenecks in the current build, in the order they'd bite:

1. **One Uvicorn process on one t2.medium.** A single event loop +
   mostly sync DB routes; CPU credits mean sustained load throttles.
2. **Apache + single instance = single point of failure** and a hard
   throughput ceiling; restarts are downtime.
3. **db.t3.micro RDS**: small CPU/RAM, storage IOPS limits; connection
   count per process multiplies with every worker we add.
4. **No caching anywhere**: every products/search request hits RDS;
   product images come from Unsplash (third-party latency).
5. **Checkout does payment inline** (retries + up to 2 s timeouts +
   breaker probes add tail latency); notifications are fire-and-forget
   BackgroundTasks (lost if the process dies).
6. **Frontend**: single bundle, no CDN, S3 website endpoint latency
   varies by geography; images not resized/CDN-optimised.

What is already good: stateless JWT auth (no session store to scale),
idempotent seeded reads, debounced search, idempotency keys on
charges, circuit breaker prevents cascading waits, async checkout
route + background notification, consistent request-id logging.

Cheap wins (mention these first — they show judgement):
indexes on product name/category + cart user lookups (verify with
`EXPLAIN`), Uvicorn workers ≈ 2×vCPU on the same box, keep-alive +
gzip in Apache, cache headers for static assets, frontend code-splitting
(`React.lazy`) + image resizing, connection pooling settings, moving
images to our own S3+CDN instead of hot-linking Unsplash.

---

# 11. 10,000 simultaneous users — what changes

First, clarify the unit in the interview (they will probe this):
10k *concurrent connections* ≠ 10k requests/sec. Assume a realistic
e-commerce shape: most of the 10k are browsing (products/search),
~1–5% in cart/checkout at any moment. Design for peaks, degrade
gracefully, never lose an order.

## Target architecture

```text
Route53 ─► CloudFront (static site + image caching, HTTPS via ACM)
              │
Browser ─────► ALB (HTTPS, health checks, sticky NOT needed — JWT)
              ├── EC2 ASG (min 2, multi-AZ) or ECS Fargate tasks
              │     Uvicorn workers, stateless, same image/AMI
              ├── RDS PostgreSQL: Multi-AZ, larger class (e.g. m6g.large+)
              │     + RDS Proxy (pooling) + 1–2 Read Replicas for reads
              ├── ElastiCache Redis: product catalog cache (TTL 30–60 s),
              │     search results, rate limiting
              ├── SQS: checkout side-effects — payment jobs, notification
              │     jobs (SES sends); workers consume with DLQ + retries
              └── Real payment gateway (webhook confirms PAID async)
CloudWatch + alarms + autoscaling policies on ALB req count / CPU / p95
```

## What changes behaviourally vs today

| Concern | Today | At 10k |
|---|---|---|
| Frontend delivery | S3 website endpoint | S3 + CloudFront — static scales essentially for free |
| API capacity | 1 process, 1 box | ASG/Fargate 2+ instances behind ALB; scale on CPU/p95/request count |
| DB connections | Each process opens its own | RDS Proxy pools; replicas absorb product reads; catalog cached in Redis so most reads never reach RDS |
| Checkout | Inline charge, sync wait | Order created `PENDING`, payment job to SQS, worker charges + webhook reconciles; client polls/SSE for final status — no request thread waits on a gateway |
| Notifications | BackgroundTask (lossy) | SQS + SES with DLQ; a dead consumer loses nothing |
| Stock safety | Row updates in one transaction | Keep transactional decrement + idempotency keys; add optimistic locking/row locks on hot SKUs to stop oversell races |
| Sessions | JWT (already stateless ✓) | Unchanged — this is why JWT was a good call; any instance can serve any user |
| Secrets/config | Secrets Manager at boot | Unchanged + rotation; instances fetch on boot, cache in memory |
| Rate limiting/abuse | None | ALB/WAF rules + Redis token bucket per IP/user on login/checkout |
| Monitoring | Lambda canary + dashboards | Same, plus per-instance/AZ dashboards, distributed tracing (X-Ray), alerting on p95 + queue depth, not just CPU |
| Cost shape | ~2 small always-on boxes | Pay for peak capacity; ASG scales in at night; replicas/Redis are the new fixed costs |

## Failure stories to be ready with

- One AZ dies → ALB shifts to the other AZ; Multi-AZ RDS promotes;
  users see a blip, no data loss (RPO≈seconds).
- Payment gateway down → breaker opens per-instance, orders land as
  `PAYMENT_FAILED`/pending with stock policy explicit, queue drains
  when the gateway recovers; no thread pile-up.
- A hot product goes viral → catalog reads served from Redis/CDN;
  DB only sees writes; oversell prevented by atomic decrement.
- Bad deploy → ASG rolling update/CodeDeploy rolls back; yesterday's
  manual flow (ZIP + restart) becomes the thing you apologise for.

Load-test answer: "I'd verify with k6/Locust: ramp to 10k VUs,
watch p95 on /products and /checkout, RDS connections, ALB target
response time; fix the first saturation (usually DB connections,
then instance CPU) and re-run." Numbers without a test are guesses —
say so.

# 12. Rapid-fire Q&A (short answers, rehearse out loud)

1. **Why Apache in front of Uvicorn?** One public port, host
   preservation, TLS termination later, Uvicorn stays on localhost —
   smaller attack surface.
2. **Why is FastAPI on 127.0.0.1 a problem for Lambda?** Lambda outside
   the VPC can't reach localhost-of-EC2 or :8000; it must call the
   public Apache address (or be VPC-attached to the private IP).
3. **S3 website endpoint vs REST endpoint?** Website endpoint serves
   index/spa hosting over HTTP; REST endpoint is for object APIs and
   (with OAC) CloudFront origins.
4. **Why did the https build fail against a self-signed IP cert?**
   Browsers reject untrusted certs for fetch; CAs don't issue trusted
   certs for bare public IPs. Needs a domain (Let's Encrypt/ACM) or
   CloudFront's trusted domain.
5. **CORS vs authentication?** CORS only governs which *browser
   origins* may read responses. It is not security by itself — the
   JWT still authenticates every call. Never `*` with credentials.
6. **Why does Postman work when the browser fails?** No Origin/CORS
   enforcement outside browsers.
7. **JWT in localStorage — risk?** XSS could read it. Mitigations:
   short access TTL (60 m) + refresh rotation; httpOnly cookies are
   the alternative with CSRF trade-offs. Know both sides.
8. **Access vs refresh token?** Access is short-lived and sent on
   every call; refresh only mints new access tokens; `type` claim
   prevents swapping them.
9. **How does the circuit breaker help users?** Fails fast instead of
   stacking 3 retries × timeouts on a dead gateway; probes `/mode`
   to auto-recover; declines (real answers) don't trip it.
10. **Idempotency in payments?** Same order_number key → provider
    returns the original `PAY-…` reference; safe retries, no double
    charge. Real gateways do the same.
11. **Why write the order before charging?** The order is the source
    of truth for reconciliation; payment failure is a *state* of an
    order (stock released), not a lost request.
12. **Secrets Manager vs Parameter Store?** Secrets: rotation,
    per-secret ACLs, RDS integration. Parameter Store: cheap config.
    Env vars in git-tracked files lose to both.
13. **Why boto3 at boot + cache?** One fetch per process; rotation =
    restart. Fail-fast avoids silently running on default creds.
14. **Versioning on S3 buckets?** Recover overwritten ZIPs/builds,
    audit what shipped when; also protects against bad uploads.
15. **CodeBuild role needs S3FullAccess?** It reads source ZIPs and
    writes two buckets; scoped bucket policies are the tighter answer
    — call out least privilege as the improvement.
16. **What does the Lambda prove that /health doesn't?** The full
    products path (Apache→FastAPI→SQLAlchemy→RDS) with real data,
    not just "process alive" (`/health/db` is the middle ground).
17. **Gauge range trap?** CloudWatch storage metrics are in bytes;
    20 GB max = 21474836480, not 20.
18. **Logs widget: line or table?** Raw events → Table; Line/Bar only
    after `stats … by bin()` aggregates numbers over time.
19. **t2.medium CPU credits?** Burstable instances: sustained CPU
    burns balance; at 0 the box throttles — looks like an app bug.
20. **What breaks first at scale?** RDS connections/CPU and the
    single API process — see §11; static frontend is last to break.
21. **Why not just a bigger EC2 (vertical scaling)?** Buys time, keeps
    the single point of failure and a hard ceiling; horizontal behind
    an ALB is the real answer, vertical is step one.
22. **How do you know the deploy is bad?** Product-refresh trend +
    checkout error filters + CodeBuild result; today it's logs and
    the canary, in production add alarms on p95/5xx.
23. **How are prices trustworthy?** Checkout copies prices into the
    order in the transaction; later catalog edits can't rewrite
    history. Stock decremented atomically in the same commit.
24. **The searchbar bug in one line?** Unlayered CSS beats Tailwind's
    layered utilities, so `.field`'s `width:100%` crushed the input
    until `.field` moved into `@layer components`.
25. **One thing you'd do next with a free week?** CloudFront + domain
    (real HTTPS), then ALB+ASG, IaC (Terraform) so Week 5's manual
    clicks become reviewable code.

---

# 13. Your 12-hour preparation plan

- **Hour 0–2:** §1 + §2 — redraw the architecture from memory twice;
  narrate each Week-5 step and *why*.
- **Hour 2–4:** §4 flows on a whiteboard; especially 4.3 (checkout +
  breaker + the env bug story) and 4.2 (refresh single-flight).
- **Hour 4–6:** §5 frontend + §3 backend tours — open the files named
  and skim them once so filenames come naturally.
- **Hour 6–8:** §6 CORS, §7 secrets, §8 Lambda/CloudWatch — rehearse
  the verify commands (`/proc/<pid>/environ`, preflight curl,
  `/health/db`).
- **Hour 8–10:** §10–§11 — performance limits and the 10k design;
  practise saying the "concurrent ≠ RPS" caveat first.
- **Hour 10–11:** §12 out loud, timed, one breath per answer.
- **Hour 11–12:** Demo run: local docker stack + Swagger + one card
  checkout (provider mode ok), products page low-stock example,
  Lambda test invoke, dashboard screenshot open. Leave provider mode
  on `ok` and the breaker closed when you finish.

**Demo script (5 minutes, if asked to show):**
1. S3 site loads → login → products (search "Shoes", low-stock text) →
2. add to cart (badge + toast) → card checkout → order page PAID →
3. provider `/sent` shows the notice →
4. Lambda test event → `ok=True, products=10` →
5. CloudWatch dashboard top row + one alarm.

Good luck. The strongest signal you can send: every decision above has
a *reason*, a *trade-off*, and a *next step* — say all three.