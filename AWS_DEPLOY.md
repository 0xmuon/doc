# Deploy ABC Shop on AWS

This is the console guide for this repo. Region: **ap-south-1 (Mumbai)**. Do the sections in order.

The browser keeps calling `/api`. CloudFront serves the React build and forwards `/api` to the API. The API talks to Postgres and to the fake payment process. Those two stay on a private network.

## What runs where

| Piece | AWS service | Why this one |
| --- | --- | --- |
| React site (`frontend/dist`) | S3, in front of **CloudFront** | CloudFront needs an origin. S3 holds the files. You did not name S3, but CloudFront does not store the files itself. |
| FastAPI (`app/`) and the fake payment API (`provider/`) | **EC2** | Both keep state in the process. The circuit breaker count is in memory. The provider’s mode (`ok` / `fail` / `slow`) and its charge list are in memory. Checkout also sends the email with a FastAPI background task after the response. A new Lambda sandbox would reset that state and can freeze before the email runs. |
| Shop database | **RDS for PostgreSQL** | Private Postgres inside the VPC. Not Postgres installed on the EC2 box. |
| Network | **VPC** | RDS, EC2, and Lambda share it. The database is not on the public internet. |
| One-off database check and seed | **Lambda** in the VPC | You invoke it from the Lambda console. It reaches RDS on the private network. It is not the shop API. |

```text
Browser
  → CloudFront (HTTPS)
       → S3            pages, /, /products, /cart, ...
       → EC2 :8000     /api/*
            → RDS Postgres          :5432  private
            → provider container    :9000  only on the EC2 Docker network
Lambda (invoke only) → RDS :5432
```

Leave these closed to the internet: Postgres `5432`, provider `9000`, debugpy `5678`.

## Cost before you click

RDS, a NAT gateway, and a load balancer are the bills that surprise people. This guide skips NAT and the load balancer. The EC2 instance has a public IP so CloudFront can reach port 8000. Lambda does not need the internet. Delete the stack when you are done: CloudFront distribution, EC2, RDS, NAT if you added one, and unattached Elastic IPs.

## 0. Account

1. Sign in as an IAM admin user, not the root account, with a billing alarm.
2. Pick **ap-south-1** in the console and stay in that region for VPC, RDS, EC2, Lambda, and S3.
3. The CloudFront certificate, if you use your own domain, must be requested in **us-east-1**. The CloudFront default `*.cloudfront.net` name works without a certificate you create.

## 1. VPC

1. VPC → Create VPC → **VPC and more**.
2. Name: `shopping`. IPv4 CIDR: `10.0.0.0/16`.
3. Two availability zones. **2 public subnets**, **2 private subnets**.
4. One NAT gateway: **None**. One VPC endpoint: **None**.
5. DNS hostnames: on.

You get an internet gateway and public route tables. Private route tables have no route to the internet. That is what you want for RDS and Lambda.

Write down:

- VPC id
- Public subnet ids (EC2 goes in one of these)
- Private subnet ids (RDS and Lambda)

## 2. Security groups

Create these in the VPC. Each rule is inbound. Outbound can stay “all”.

**`shopping-db`** (RDS)

- PostgreSQL `5432` from `shopping-api`
- PostgreSQL `5432` from `shopping-lambda`

**`shopping-api`** (EC2)

- TCP `8000` from `0.0.0.0/0` so CloudFront can call the API. After the distribution exists, tighten this to the CloudFront origin-facing prefix list `com.amazonaws.global.cloudfront.origin-facing` instead of the whole internet.
- TCP `22` from your current IP only, so you can SSH. Remove it if you use EC2 Instance Connect and then close it.

Do not add `5432`, `9000`, or `5678`.

**`shopping-lambda`**

- No inbound rules. Lambda only makes outbound calls to RDS.

## 3. RDS Postgres

1. RDS → Create database → **PostgreSQL**. Engine **17** if it is offered, otherwise the newest 16.
2. Template: **Free tier** if you are practicing. Production: a Multi-AZ instance.
3. DB identifier: `shopping`. Master user: `shop`. Master password: a long password you generate. Do not reuse `shop`.
4. Instance: `db.t4g.micro` or the free-tier class.
5. Storage: 20 GB gp3. Public access: **No**.
6. VPC: `shopping`. Subnet group: the **two private** subnets. Security group: `shopping-db` only. Remove the default group if the wizard adds it.
7. Initial database name: `shopping`.
8. Backups: 1 day is enough for a demo.

Wait until status is **Available**. Copy the endpoint. It looks like `shopping.xxxx.ap-south-1.rds.amazonaws.com`. The port is `5432`.

From your laptop you cannot open that host. It has no public route. EC2 and Lambda can.

## 4. EC2 for the API and the payment provider

1. EC2 → Launch instance. Name: `shopping-api`.
2. AMI: **Amazon Linux 2023**. Type: `t3.micro`.
3. Key pair: create one and keep the `.pem` private.
4. Network: VPC `shopping`, a **public** subnet, **auto-assign public IP** on.
5. Security group: `shopping-api`.
6. Disk: 20 GB gp3.

SSH in:

```bash
ssh -i shopping.pem ec2-user@<public-ip>
```

Install Docker:

```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
```

Log out and back in so the `docker` group applies. Install the Compose plugin from Docker’s Amazon Linux instructions if `docker compose version` fails.

Clone the repo into `/home/ec2-user/ecommerce`. On the instance, create `/home/ec2-user/ecommerce/.env.aws` (do not commit it):

```bash
POSTGRES_USER=shop
POSTGRES_PASSWORD=<the RDS password>
POSTGRES_DB=shopping
DATABASE_URL=postgresql+psycopg://shop:<password>@<rds-endpoint>:5432/shopping
JWT_SECRET=<a new random string, 32+ characters>
JWT_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=7
PAYMENT_FORCE=ok
PAYMENT_MAX_ATTEMPTS=3
PAYMENT_TIMEOUT_SECONDS=2
PAYMENT_RETRY_BASE_DELAY=0.05
CIRCUIT_MAX_FAILURES=3
CIRCUIT_RESET_SECONDS=30
PAYMENT_API_URL=http://provider:9000/payments/charge
NOTIFY_API_URL=http://provider:9000/notify
NOTIFY_MAX_ATTEMPTS=3
```

URL-encode the password if it contains `@`, `:`, or `/`.

Create `/home/ec2-user/ecommerce/docker-compose.aws.yml` next to the existing compose file. This file does not start Postgres and does not publish the provider port:

```yaml
name: shopping-simple

services:
  api:
    build: .
    env_file:
      - .env.aws
    ports:
      - "8000:8000"
    depends_on:
      provider:
        condition: service_started
    command:
      - uvicorn
      - app.main:app
      - --host=0.0.0.0
      - --port=8000

  provider:
    build: .
    command: ["uvicorn", "provider.main:app", "--host", "0.0.0.0", "--port", "9000"]
```

Start only those two:

```bash
cd /home/ec2-user/ecommerce
docker compose -f docker-compose.aws.yml up -d --build
```

The API process creates the tables on startup (`Base.metadata.create_all`) and seeds categories, products, and the three demo users if their emails are missing. A second boot does not reset those users’ passwords. Product prices are updated to the seed prices when the row already exists.

Check from the instance:

```bash
curl -s http://127.0.0.1:8000/health
```

Do not curl port 9000 from your laptop. The provider is only on the Docker network, which is what `PAYMENT_API_URL=http://provider:9000/...` uses.

Change the demo passwords (`rudraksh1234`, `navya1234`, `het12345`) before anyone but you can open the site. Those accounts are created by `app/db/seed.py` on first boot.

## 5. Lambda inside the VPC

This function proves the private network and can seed an empty database if the EC2 app has not booted yet. It is not on the request path.

1. IAM → Roles → Create role → trusted entity **Lambda**.
2. Attach the AWS managed policy **AWSLambdaVPCAccessExecutionRole**. Name the role `shopping-lambda-vpc`.
3. Lambda → Create function. Name: `shopping-db-check`. Runtime: **Python 3.12**. Architecture: arm64. Role: `shopping-lambda-vpc`.
4. After it exists: Configuration → VPC. VPC `shopping`, both **private** subnets, security group `shopping-lambda`.
5. Configuration → General → Timeout **30 seconds**. Memory 256 MB.
6. Add a layer, or a deployment package, that includes `psycopg` (binary). The console editor cannot pip-install into a VPC function by itself. From your PC:

```bash
mkdir -p lambda-db-check
cd lambda-db-check
pip install psycopg[binary] -t . --platform manylinux2014_aarch64 --python-version 3.12 --only-binary=:all:
```

Save `lambda_function.py` in that folder:

```python
import os
import psycopg

def lambda_handler(event, context):
    url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
    return {"ok": row[0] == 1}
```

Zip the folder contents (the packages at the root of the zip, not a nested folder) and upload it.

7. Configuration → Environment variables: `DATABASE_URL` set to the same URL as on EC2.
8. Test with an empty event `{}`. The result you want is `{"ok": true}`.

The first invoke can take about ten seconds while Lambda creates the network interface in the private subnet. A timeout means the security group or the subnet is wrong: the function must be in the private subnets, and `shopping-db` must allow `5432` from `shopping-lambda`.

## 6. Build the frontend

On your PC, in `frontend`:

```bash
npm ci
npm run build
```

Leave `VITE_API_BASE_URL` unset. `client.js` then calls `/api/...` on the same host as the page. CloudFront will own that host and forward `/api` to EC2. Do not point the built site at `http://<ec2>:8000`. That skips CloudFront and mixes HTTP with the HTTPS page.

`npm run build` writes `frontend/dist`.

## 7. S3

1. S3 → Create bucket. Name: `shopping-frontend-<account-id>`. Region: ap-south-1.
2. Block all public access: **On**. CloudFront reads the bucket with an origin access control. The bucket is not a public website.
3. Upload the **contents** of `frontend/dist` (so `index.html` is at the bucket root, not inside a `dist/` folder).

## 8. CloudFront

1. CloudFront → Create distribution.
2. Origin 1: the S3 bucket. Origin access: **Origin access control**. Let the console update the bucket policy when it asks.
3. Add origin 2: custom origin. Domain: the EC2 **public DNS** name. Protocol: **HTTP only**. Port: **8000**. Name this origin `api`.
4. Default behavior: origin S3. Viewer protocol: **Redirect HTTP to HTTPS**. Allowed methods: GET, HEAD. Cache policy: CachingOptimized.
5. Create a second behavior. Path pattern: `api/*`. Origin: `api`. Allowed methods: **GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE**. Cache policy: **CachingDisabled**. Origin request policy: **AllViewer** (forward the `Authorization` header and the body). Viewer protocol: Redirect HTTP to HTTPS.
6. Default root object: `index.html`.
7. On the **S3 behavior only**, add a CloudFront Function for the viewer request so React routes such as `/cart` serve `index.html`. Do not attach this function to `api/*`. An API 404 must stay JSON.

```javascript
function handler(event) {
  var request = event.request;
  var uri = request.uri;
  if (uri.includes(".")) {
    return request;
  }
  request.uri = "/index.html";
  return request;
}
```

8. Wait until the distribution status is **Deployed**. Copy the domain `https://dxxxx.cloudfront.net`.

Open that URL. Home should load. Register or log in. If the page loads and `/api` returns HTML, the `api/*` behavior is missing or ordered after a rewrite. If the browser shows a network error to port 8000, the build was created with the wrong `VITE_API_BASE_URL`.

Tighten `shopping-api` so port 8000 is allowed from the CloudFront origin-facing prefix list instead of `0.0.0.0/0`.

## 9. Your own domain, optional

1. Request a public certificate in **us-east-1** for `shop.example.com`.
2. Validate it with the DNS record ACM shows.
3. CloudFront → Alternate domain name → attach that certificate.
4. In Route 53, alias `shop.example.com` to the distribution.

Rebuild is not required if the site still uses relative `/api`.

## 10. After a code change

Frontend:

```bash
npm run build
```

Upload `frontend/dist` to the bucket again and invalidate CloudFront path `/*`.

API or provider: SSH to EC2, pull, then `docker compose -f docker-compose.aws.yml up -d --build`.

## What not to put on Lambda

Do not move `app.main:app` onto Lambda for this codebase without a redesign.

- `payment_breaker` in `app/integrations/circuit_breaker.py` stores `state` and `failures` on the object. Each Lambda environment has its own object. A cold start starts the breaker at closed with 0 failures. Two warm environments do not share a count, so “three failures then off” is not one breaker.
- `provider/main.py` stores `mode`, `charges`, and `sent` in process memory. Mode `fail` would reset to `ok` on a new sandbox, and idempotency keys would be forgotten.
- `order_router.checkout` queues `send_order_notification` with FastAPI `BackgroundTasks`. Lambda can freeze the process when the response is returned, so the email may never be sent.
- The API calls `seed_database()` on startup. A Lambda cold start would run that on a request.

EC2 is the process that stays up. Lambda’s job in this guide is the private database check.

## Check list

- `https://<distribution>/` shows ABC Shop over HTTPS.
- `https://<distribution>/api/health` returns JSON, not `index.html`.
- Login works. A refresh of the page still shows the user (`localStorage` plus `GET /api/auth/me`).
- A card checkout with the provider left at its default `ok` mode creates an order and a `order_notification_sent` line in `docker compose logs api`.
- From your laptop, `nc -vz <rds-endpoint> 5432` fails.
- From your laptop, port 9000 on the EC2 public IP is closed.
- Lambda test returns `{"ok": true}`.
