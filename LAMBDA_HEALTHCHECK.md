# Lambda health check of the EC2 API

Lambda calls the FastAPI process on EC2 and returns that process’s health JSON. The route is already in `app/main.py`:

```text
GET /health     →  {"status": "ok"}
GET /health/db  →  {"status": "ok"}   only if Postgres answers
```

`/health` is not under `/api`. The call from Lambda is:

```text
GET http://<ec2-private-ip>:8000/health
```

Use the private IP (`10.0.x.x` from the EC2 instance details). Do not use the public IP or the CloudFront domain. Lambda in this VPC has no route to the public internet, and the private IP stays inside the VPC.

## 1. Let Lambda reach port 8000

EC2 security group `shopping-api`:

1. Edit inbound rules.
2. Add TCP **8000**. Source: security group **`shopping-lambda`**.
3. Leave the CloudFront rule as it is. This extra rule is only for Lambda.

Lambda’s own security group needs no inbound rule. It only makes an outbound call.

Both must be in VPC `shopping`. Lambda uses the **private** subnets. EC2 can stay in a public subnet. Private and public subnets in the same VPC can still talk on the private IP.

## 2. Create the function

1. IAM role `shopping-lambda-vpc` with the managed policy **AWSLambdaVPCAccessExecutionRole** (the same role as the database check, if you already made it).
2. Lambda → Create function. Name: `shopping-api-health`. Runtime: **Python 3.12**. Architecture: arm64.
3. Configuration → VPC: VPC `shopping`, both private subnets, security group `shopping-lambda`.
4. Timeout: **15 seconds**. Memory: 128 MB is enough.
5. Environment variable:

| Key | Value |
| --- | --- |
| `API_HEALTH_URL` | `http://<ec2-private-ip>:8000/health` |

Replace the IP with the current private IPv4 of `shopping-api`. It changes if you stop and start the instance (a reboot keeps it).

6. Paste this into the code editor and Deploy. The standard library is enough. No layer and no zip.

```python
import json
import os
import urllib.error
import urllib.request


def lambda_handler(event, context):
    url = os.environ["API_HEALTH_URL"].strip()
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read().decode()
            body = json.loads(raw)
            return {
                "ok": response.status == 200 and body.get("status") == "ok",
                "status_code": response.status,
                "health": body,
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status_code": exc.code,
            "health": exc.read().decode(),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}
```

## 3. Invoke it

Lambda → Test → Event JSON `{}` → Test.

A live API returns:

```json
{
  "ok": true,
  "status_code": 200,
  "health": {
    "status": "ok"
  }
}
```

`health` is the FastAPI body. `ok` is Lambda saying that body was a 200 with `"status": "ok"`.

The first call after a VPC change can take about ten seconds while Lambda places a network interface. Later calls are shorter.

CloudWatch → Log groups → `/aws/lambda/shopping-api-health` shows the same result and any Python traceback.

## 4. Also check the database through FastAPI

Set `API_HEALTH_URL` to:

```text
http://<ec2-private-ip>:8000/health/db
```

That route runs `SELECT 1` on RDS from the API process. The response is still `{"status": "ok"}`. If RDS is down, FastAPI returns a 500 and the Lambda result has `"ok": false` and the error text in `health`.

Switch the variable back to `/health` if you only want “is the process up”.

## When the test fails

| Lambda result | Cause |
| --- | --- |
| `timed out` | Lambda is not in the VPC, or it is in a subnet that cannot route to the EC2 private IP, or port 8000 is not allowed from `shopping-lambda`. |
| `Connection refused` | The URL is right but nothing is listening. On EC2 run `curl -s http://127.0.0.1:8000/health`. Start the API with `docker compose -f docker-compose.aws.yml up -d`. |
| `Name or service not known` / timeout to a public DNS name | The URL uses the public IP or a public DNS name. Change it to the private IP. |
| `404` HTML or JSON | The path is `/api/health`. This app’s route is `/health`. |
| `ok: false` and a 500 body | `/health/db` could not run `SELECT 1`. The process is up. The database call from the API failed. |
