"""Credentials from AWS Secrets Manager (used on EC2, no .env file there).

The secret named by DB_SECRET_NAME (default ``ecommerce-db-secrets``,
region ``us-east-1`` per week5.pdf step D) is expected to be a JSON object:

    {
      "username": "<rds master user>",
      "password": "<rds master password>",
      "host": "<rds endpoint>",
      "port": 5432,
      "dbname": "<rds database name>",
      "jwt_secret": "<long random string, 32+ chars>"
    }

An RDS-type secret created in the console already has username/password/
host/port/dbname — just add the ``jwt_secret`` key. The EC2 instance reads
it through its IAM instance profile (``secretsmanager:GetSecretValue`` on
that one secret); no AWS keys are stored on the box.

Fetching only happens when ``USE_SECRETS_MANAGER=1`` is set (the systemd
unit sets it — see SECRETS_MANAGER.md). Local dev, Docker and tests keep
using plain environment variables, so nothing changes off EC2.
"""

import json
import logging
import os
from functools import lru_cache
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

DEFAULT_SECRET_NAME = "ecommerce-db-secrets"
DEFAULT_REGION = "us-east-1"


def secrets_enabled() -> bool:
    return os.getenv("USE_SECRETS_MANAGER", "").strip().lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def _load_secret() -> dict:
    """Fetch and cache the secret for the life of the process.

    Fail fast: on EC2 there is deliberately no fallback to default or
    .env credentials, so a broken IAM role shows up at boot, not as a
    mysterious login failure later.
    """
    import boto3  # imported lazily so local runs without AWS never need it

    name = os.getenv("DB_SECRET_NAME", DEFAULT_SECRET_NAME).strip() or DEFAULT_SECRET_NAME
    region = (
        os.getenv("AWS_REGION", "").strip()
        or os.getenv("AWS_DEFAULT_REGION", "").strip()
        or DEFAULT_REGION
    )
    client = boto3.client("secretsmanager", region_name=region)
    try:
        response = client.get_secret_value(SecretId=name)
    except Exception as exc:
        raise RuntimeError(f"Could not read secret '{name}' in {region}: {exc}") from exc
    try:
        secret = json.loads(response["SecretString"])
    except Exception as exc:
        raise RuntimeError(f"Secret '{name}' is not valid JSON") from exc
    logger.info("Loaded credentials from Secrets Manager secret '%s' (%s)", name, region)
    return secret


def database_url_from_secret() -> str:
    secret = _load_secret()
    missing = [key for key in ("username", "password", "host") if not secret.get(key)]
    if missing:
        raise RuntimeError(f"Secret is missing required keys: {', '.join(missing)}")
    user = quote_plus(str(secret["username"]))
    password = quote_plus(str(secret["password"]))
    host = str(secret["host"])
    port = int(secret.get("port") or 5432)
    dbname = quote_plus(str(secret.get("dbname") or "postgres"))
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"


def jwt_secret_from_secret() -> str | None:
    """JWT signing key stored beside the DB credentials, if present."""
    value = _load_secret().get("jwt_secret") or _load_secret().get("JWT_SECRET")
    return str(value) if value else None
