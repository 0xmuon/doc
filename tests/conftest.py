"""postgres tests use shopping_test.a sqlite url uses test_ecommerce.db instead."""

import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg
from dotenv import load_dotenv

load_dotenv()

os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters-long"
os.environ["PAYMENT_FORCE"] = "ok"
os.environ["PAYMENT_API_URL"] = ""
os.environ["PAYMENT_RETRY_BASE_DELAY"] = "0"
os.environ["NOTIFY_API_URL"] = ""


def _with_database(url: str, name: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{name}", parts.query, parts.fragment))


_base = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://shop:shop@localhost:5433/shopping",
)
if _base.startswith("sqlite"):
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_ecommerce.db"
else:
    os.environ["DATABASE_URL"] = _with_database(_base, "shopping_test")

import pytest
from fastapi.testclient import TestClient

from app.integrations import reset_breaker
from app.main import app
from app.utils import reset_metrics


def _recreate_database() -> None:
    url = os.environ["DATABASE_URL"]
    if url.startswith("sqlite"):
        path = Path("test_ecommerce.db")
        if path.exists():
            path.unlink()
        return
    admin = _with_database(url, "postgres").replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute("DROP DATABASE IF EXISTS shopping_test WITH (FORCE)")
        conn.execute("CREATE DATABASE shopping_test")


@pytest.fixture(scope="session")
def _test_database():
    _recreate_database()


@pytest.fixture
def client(_test_database):
    reset_breaker()
    reset_metrics()
    with TestClient(app) as test_client:
        yield test_client
