# No .env on EC2 — credentials from AWS Secrets Manager

Goal: the deployed backend on EC2 holds **no `.env` file and no passwords on
disk**. The DB username/password (and the JWT signing key) live in Secrets
Manager secret `ecommerce-db-secrets` (week5.pdf step D); the EC2 instance
reads them at startup through its IAM role. Local dev / Docker / tests are
unchanged — they still use environment variables.

Code that does this: `app/secrets.py`, used by `app/db/session.py`
(database URL) and `app/utils/security.py` (JWT secret). Fetching only
happens when `USE_SECRETS_MANAGER=1`.

## 1. Put everything in the secret

Secrets Manager → `ecommerce-db-secrets` → Retrieve secret value → Edit.
An RDS-type secret already has `username`, `password`, `host`, `port`,
`dbname`. Add one key, `jwt_secret` (generate on EC2:
`openssl rand -hex 32`):

```json
{
  "username": "<rds master user>",
  "password": "<rds master password>",
  "host": "<rds endpoint>",
  "port": 5432,
  "dbname": "<rds database name>",
  "jwt_secret": "<64 hex chars>"
}
```

If you created the secret as "other type" instead of RDS, add all six keys
yourself. `dbname` is on the RDS instance's Configuration tab (DB name) —
not the instance identifier.

## 2. Let EC2 read it (IAM instance profile, no access keys)

1. IAM → Roles → Create role → AWS service → EC2. Name:
   `ecommerce-ec2-secrets-role`.
2. Attach an inline policy with least privilege — this one secret only:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
    "Resource": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:ecommerce-db-secrets-*"
  }]
}
```

3. EC2 → select `ecommerce_backend` → Actions → Security → Modify IAM role →
   `ecommerce-ec2-secrets-role`.
4. Never put AWS access keys in code, `.env`, or the unit file — the
   instance profile is picked up automatically by boto3.

## 3. Remove .env, tell systemd where config lives

Non-secret settings (region, secret name, CORS origin) are not credentials,
so they go in the systemd unit as `Environment=` lines instead of `.env`:

```bash
pip install -r requirements.txt   # now includes boto3
rm ~/ecommerce/.env               # use your real app folder path
```

`/etc/systemd/system/ecommerce-backend.service`:

```ini
[Unit]
Description=ABC Shop backend
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/application
Environment=USE_SECRETS_MANAGER=1
Environment=DB_SECRET_NAME=ecommerce-db-secrets
Environment=AWS_REGION=us-east-1
Environment=CORS_ALLOWED_ORIGINS=http://frontend-http-xy-1234.s3-website-us-east-1.amazonaws.com
Environment=PAYMENT_API_URL=http://127.0.0.1:9000/payments/charge
Environment=NOTIFY_API_URL=http://127.0.0.1:9000/notify
ExecStart=/home/ubuntu/application/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
User=ubuntu
Restart=always

[Install]
WantedBy=multi-user.target
```

Adjust `WorkingDirectory`/the venv path if your app folder or virtualenv
differs (`which python` inside the activated venv shows the right one).
If you run Uvicorn manually in a console instead of systemd, export the
same `USE_SECRETS_MANAGER`/`DB_SECRET_NAME`/`AWS_REGION` lines in that
shell before starting it — and make sure `DATABASE_URL` and `JWT_SECRET`
are **not** exported there, because a set env var takes priority over
Secrets Manager.

```bash
sudo systemctl daemon-reload
sudo systemctl restart ecommerce-backend
sudo systemctl status ecommerce-backend --no-pager
```

## 3b. Run the provider (fake payment/email API, port 9000)

The provider is a second process on the **same EC2 box**. The backend calls
it at `127.0.0.1:9000` (wired by the two `Environment=` lines above), so bind
it to localhost and **do not open port 9000 in the security group** — it is
not for browsers.

Quick one-off test:

```bash
cd ~/ecommerce
python3 -m uvicorn provider.main:app --host 127.0.0.1 --port 9000
curl -s http://127.0.0.1:9000/mode        # {"mode":"ok"}
```

Permanent, as its own service — `/etc/systemd/system/ecommerce-provider.service`:

```ini
[Unit]
Description=ABC Shop provider (fake payment + email)
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/ecommerce
ExecStart=/usr/bin/python3 -m uvicorn provider.main:app --host 127.0.0.1 --port 9000
User=ubuntu
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ecommerce-provider
sudo systemctl restart ecommerce-backend   # picks up PAYMENT_API_URL / NOTIFY_API_URL
curl -s http://127.0.0.1:9000/mode                   # {"mode":"ok"}
curl -s http://127.0.0.1:9000/docs -o /dev/null -w "%{http_code}\n"   # 200
curl -X PUT http://127.0.0.1:9000/mode/ok            # always leave it on ok
```

Notes: the provider has no `/` or `/health` route — `GET /mode` is its
health check. Its mode (`ok`/`fail`/`slow`) lives in memory and resets to
`ok` on restart. To view its Swagger (`http://127.0.0.1:9000/docs`) from
your laptop, tunnel it: `ssh -L 9000:127.0.0.1:9000 ubuntu@<public-IP>`,
then open `http://localhost:9000/docs`. COD checkouts never call the
provider; card charges (`/payments/charge`) and order emails (`/notify`) do.

## 4. Verify (still no .env anywhere)

```bash
ls -la ~/ecommerce/.env                 # No such file
curl -s http://127.0.0.1:8000/health        # {"status":"ok"}
curl -s http://127.0.0.1:8000/health/db     # {"status":"ok"} = RDS via secret creds
curl -s http://127.0.0.1:8000/api/products | head -c 200
```

Then Swagger `http://<public-IP>/docs`: login, call a protected route —
that proves the `jwt_secret` from Secrets Manager signs tokens. Watch
`journalctl -u ecommerce-backend -f` for
`Loaded credentials from Secrets Manager secret ...` at startup.

## Rotation & caching

The secret is fetched once per process and cached. After rotating the RDS
password (update RDS, then the secret — or enable Secrets Manager managed
rotation for RDS), restart the service:
`sudo systemctl restart ecommerce-backend`.

## Troubleshooting

| Symptom in `journalctl` | Cause |
|---|---|
| `Could not read secret ... AccessDenied` | IAM role not attached, or policy Resource ARN/region wrong |
| `Secret is missing required keys` | Secret JSON lacks `username`/`password`/`host` — see step 1 |
| `Secrets Manager secret has no 'jwt_secret' key` | Add `jwt_secret` to the secret JSON |
| `Could not read secret ...` endpoint/region errors | Secret is not in `us-east-1`, or `AWS_REGION` in the unit is wrong |
| App works locally but not on EC2 | `USE_SECRETS_MANAGER=1` missing from the unit, so it fell back to env/defaults |

Note: the repo still ships `.env.example` and Docker Compose still reads a
local `.env` — that is only for your machine. The rule is: **no `.env` and
no passwords on the EC2 box.**
