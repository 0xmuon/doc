# CloudWatch for ABC Shop — what an SDE must not miss

Stack covered: EC2 (`ecommerce_backend`, Apache :80 → FastAPI :8000,
provider :9000), RDS PostgreSQL, S3 http frontend buckets, Lambda
`ecommerce-product-refresh` (5-min products check), CodeBuild
`frontend-build-http` (started manually — there is no S3-trigger Lambda
in this project).

Rule of thumb (the four golden signals, applied here):
**Errors** tell you it's broken, **Latency** tells you it's slow,
**Traffic** tells you it's being used, **Saturation** tells you it's
about to break. Every must-have below maps to one of these.

Dashboard: CloudWatch → Dashboards → Create → name `ecommerce-overview`.

### Widget types in CloudWatch (what to pick, when)

CloudWatch dashboards offer these visualizations. Pick by the question
the widget answers — this choice is used in every row below.

| Widget type | Use it for | In this project |
|---|---|---|
| **Number** | Latest single value, big and glanceable (“is it 0 or not?”) | Status checks, error sums, invocations in the last period |
| **Gauge** | One value against a safe range with min/max (“how close to the edge?”) | EC2 status 0–1, RDS free storage 0–20 GB, CPU 0–100% |
| **Line** | Trend over time; anything you compare before/after a deploy | CPU, latency, connections, duration p95, memory |
| **Stacked area** | Volumes that add up (in vs out, read vs write) | NetworkIn/Out, Read/Write IOPS |
| **Bar** | Discrete counts per period (per 5 min / per hour) | Lambda invocations, errors, failed builds, `ok=False` counts |
| **Pie** | Share of a total at a glance (donut view) | Build success vs failed share — optional, low value here; skip unless demoing |
| **Alarm status / Alarm line** | Red-green state and alarm annotations on a chart | One alarm-status tile covering all alarms in §6 |
| **Logs (table/query)** | Log-derived results from Logs Insights | Failure lists, catalog counts, recent refresh runs |
| **Text** | Markdown notes/labels on the dashboard | Row headings (“IS IT UP?”) and runbook links — free, add one above each row |

Rules of thumb: current health → **Number/Gauge**, history → **Line**,
counts per bucket of time → **Bar**, totals that compose → **Stacked
area**, alarm state → **Alarm status**, text from logs → **Logs**. When
in doubt, Line for rates/percentages and Bar for event counts.

---

## MUST NOT MISS — add these first

### 1. “Is it up?” widgets (top row)

| Widget | Metric | Widget type | Healthy value |
|---|---|---|---|
| EC2 status | EC2 `StatusCheckFailed` (Max, 5m) | **Gauge** (range 0–1) or Number | 0 |
| Product refresh runs | Lambda (product-refresh) `Invocations` (Sum, 5m) | **Number** (latest) + **Bar** (per 5 min, below it) | ≥ 1 every 5 min |
| Product refresh failures | Log metric filter `ProductRefreshFailures` (§2) | **Number** (red at ≥ 1) | 0 |
| All alarms in one tile | — | **Alarm status** | all green |

Why: the product-refresh Lambda is your synthetic user — it exercises
Apache → FastAPI → RDS every 5 minutes. If it goes quiet or fails, the
shop is down even if EC2 itself looks fine.

### 2. The failure alarm that actually catches a dead backend

The product-refresh Lambda **returns 200 even when the backend is dead**
(it reports `ok=False` in logs). A Lambda `Errors` alarm alone will
never fire. So:

1. CloudWatch → Logs → `/aws/lambda/ecommerce-product-refresh` →
   Metric filters → Create: pattern `product_refresh ok=False`,
   metric name `ProductRefreshFailures`, namespace `ABCShop`, value 1.
2. Alarm: `ProductRefreshFailures >= 1` in 5 minutes → SNS email.

Same pattern is worth adding for the payment path once backend logs are
in CloudWatch: filter `payment circuit breaker is off` and
`Notification unreachable` — those exact strings appear in the backend
log when payments/notifications fail (provider :9000 unreachable).

### 3. EC2 saturation (5m period)

| Metric (statistic) | Widget type | Notes |
|---|---|---|
| `CPUUtilization` (Average) | **Line** (add a horizontal annotation at 80%) | Alarm > 80% for 15 min |
| `CPUCreditBalance` | **Line**, or **Gauge** (0 → your max credits) | Hitting 0 = silent throttling that looks like “app is slow” |
| `CPUCreditUsage` | **Line** (same widget as balance is fine) | t2.medium is burstable |
| `NetworkIn` / `NetworkOut` | **Stacked area** (both series stacked) | Zero in = nobody can reach Apache — check security group/Apache |
| `StatusCheckFailed` (Max) | **Gauge** (already in §1) | Instance-level failure |
| `mem_used_percent` (CWAgent, if agent installed) | **Line** + **Gauge** (0–100%, danger > 85%) | Not collected by default |
| `disk_used_percent` (CWAgent, if agent installed) | **Gauge** (0–100%) | Not collected by default |

Memory % and disk % are **not** collected by default. An SDE should
know this gap: either install the CloudWatch agent (namespace
`CWAgent`: `mem_used_percent`, `disk_used_percent`) or accept that
“out of disk/memory” is invisible until the box dies.

### 4. RDS — the database will fail before the app does (5m period)

| Metric (statistic) | Widget type | Watch for |
|---|---|---|
| `FreeStorageSpace` (Minimum) | **Gauge** (0 → 20 GB, your volume size) + Line below it | Alarm < 2 GB. Disk-full RDS stops writes = shop dead. |
| `DatabaseConnections` (Maximum) | **Line** | Steady climb that never falls = connection leak in the app. |
| `CPUUtilization` (Average) | **Line** (annotation at 80%) | > 80% sustained = queries need attention. |
| `FreeableMemory` (Minimum) | **Line** (long range, 7–30 days view) | Trending to 0 over days = restart/size-up coming. |
| `ReadLatency` / `WriteLatency` (Average, seconds) | **Line** (both series, one widget) | Sudden step-up after a deploy = bad query/code change. |
| `ReadIOPS` / `WriteIOPS` (Average) | **Stacked area** | Load shape vs the provisioned IOPS ceiling. |

### 5. Lambda — product refresh only (5m unless noted)

| Metric (statistic) | Widget type | Notes |
|---|---|---|
| `Invocations` (Sum) | **Bar** (per 5 min / per 1 h) | ~12/hour steady at `rate(5 minutes)` |
| `Errors` (Sum) | **Bar** + **Number** (latest) | Any non-zero needs a look |
| `Throttles` (Sum) | **Bar** | Non-zero = concurrency limit hit |
| `Duration` (Average + p95) | **Line** (two series) | p95 near 15 s timeout = backend hanging, not down; average alone hides this |
| `ConcurrentExecutions` (Max) | **Line** | Should sit at 1 |
| `Duration` latest | **Number** (optional) | Quick “last run took how long” glance |

### 6. Alarms → one SNS topic, your email

Create these at minimum, all pointing at one SNS topic
`ecommerce-alerts`:

| Alarm | Condition |
|---|---|
| Product refresh failures (metric filter) | >= 1 in 5 min |
| EC2 `StatusCheckFailed` | >= 1 |
| EC2 CPU | > 80% for 15 min |
| RDS `FreeStorageSpace` | < 2 GB |
| RDS `DatabaseConnections` | > 80 for 15 min |
| Lambda `Errors` (product refresh) | >= 1 in 5 min |

Add one **Alarm status widget** on the dashboard so all of the above
show as a single red/green tile.

#### Set up the SNS topic once (do this before creating alarms)

1. Console → **SNS** → Topics → Create topic:
   - Type: **Standard**, Name: `ecommerce-alerts`. Create.
2. Open the topic → Create subscription:
   - Protocol: **Email**, Endpoint: your email address. Create.
3. **Confirm it**: open the "AWS Notification - Subscription
   Confirmation" email and click *Confirm subscription*. Until you do,
   the subscription sits at `PendingConfirmation` and **no alarm will
   ever email you** — this is the step everyone forgets.
4. (Recommended) Add a second subscription later (teammate/Slack via
   Lambda, etc.) — every alarm just points at the topic, subscribers
   can change without touching alarms. One topic → many receivers is
   the whole point of using SNS instead of per-alarm emails.

#### Point each alarm at the topic

When creating any alarm above (CloudWatch → Alarms → Create alarm →
pick metric → set condition) you reach **Configure actions**:

1. Notification → *In alarm* → **Send notification to SNS topic** →
   select `ecommerce-alerts`.
2. Also tick *Notify when OK* (optional, under the OK state action) so
   you get a "recovered" email — useful to know an incident ended.
3. Name it clearly, e.g. `abcshop-ec2-status-check-failed`.

For an alarm that already exists: open it → Edit → Actions → add the
same SNS notification. Verify by opening one alarm → Actions → **Send
test message** (or set off the product-refresh alarm by stopping the
backend for 5 minutes) and confirm the email arrives.

---

## SHOULD ADD — when the basics are in

### Log Insights widgets (widget type: **Logs**, one per query)

Each of these is added as a Logs widget and rendered as a **Bar** chart
(or table for the list-style queries — set the visualization inside the
query editor: bar for counts over time, table for raw recent events).

Product refresh failures over time (**Bar**, via `stats ... by bin`):
```
fields @timestamp, @message
| filter @message like /product_refresh ok=False/
| stats count() as failures by bin(5m)
```

Catalog size trend, what the Lambda last saw (**Table**, or Line after
adding a `stats` aggregation):
```
fields @timestamp, @message
| filter @message like /product_refresh/
| parse @message "products=* " as product_count
| sort @timestamp desc | limit 20
```

### CodeBuild

| Metric (statistic) | Widget type | Notes |
|---|---|---|
| `FailedBuilds` / `SucceededBuilds` (Sum) | **Bar** (per 1 h) or **Number** pair | Builds are started manually after uploading a new ZIP (no S3 trigger); a failed build = new frontend never shipped |
| `Duration` (Average, seconds) | **Line** | Builds getting slower = buildspec/dependency bloat |
| Success vs failed share | **Pie** (optional) | Only for demo slides; the Bar pair carries the same info better |

### S3

| Metric (statistic) | Widget type | Notes |
|---|---|---|
| `BucketSizeBytes` (Average) | **Number** or **Gauge** | Daily storage metric — expect up to a day lag; don't alarm on it |
| `NumberOfObjects` (Average) | **Number** | Same daily caveat |
| `4xxErrors` / `5xxErrors` (Sum) | **Bar** | Only exist after enabling **Request metrics** on the bucket; enable on the frontend bucket for “users hitting missing files” (usually SPA misroutes) |

### EC2 logs in CloudWatch (optional but closes the biggest blind spot)

Backend Apache/Uvicorn logs currently live only on the box. Installing
the CloudWatch agent (or a journal export) gets you metric filters for
checkout `500`s, `circuit_off` events, and CORS `400` preflights —
the difference between “user reports payment failed” and “you already
knew”.

---

## How an SDE reads this dashboard in an incident

1. Top row red? Start there: EC2 status → instance problem;
   product-refresh failures with EC2 green → app/provider/RDS layer,
   SSH in and check Uvicorn + provider (`curl 127.0.0.1:9000/mode`).
2. Latency up, errors flat → check RDS latency/connections and EC2
   CPU credits before touching code.
3. Deploy just happened and things broke → CodeBuild result →
   product-refresh trend, in that order (builds are manual, so check
   that the build actually ran for the ZIP you uploaded).
4. Nothing red but users complain → remember the blind spots: no
   memory/disk metrics without the agent, provider :9000 has no
   metrics of its own (it is only visible through backend payment
   logs), and S3 request errors need request metrics enabled.

## Deliberately skipped (per project scope)

No HTTPS/CloudFront widgets (no CloudFront), no ALB metrics (no ALB),
no X-Ray tracing, no custom business KPIs (orders/min) — those would
need app-level metric publishing and are out of the current scope.
Revisit if the architecture grows them.
