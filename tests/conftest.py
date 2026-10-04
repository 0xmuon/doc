"""sqlite file so the sync pool and the async pool see the same rows."""

import os
from pathlib import Path

_db = Path(__file__).resolve().parents[1] / ".pytest_shopping.db"
if _db.exists():
    _db.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_db.as_posix()}"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters-long"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "admin12345"
os.environ["SUPPORT_EMAIL"] = "support@example.com"
os.environ["SUPPORT_PASSWORD"] = "support12345"
os.environ["PAYMENT_FORCE"] = "ok"
os.environ["PAYMENT_API_URL"] = ""
os.environ["PAYMENT_RETRY_BASE_DELAY"] = "0"
os.environ["NOTIFY_API_URL"] = ""

import pytest
from fastapi.testclient import TestClient

from app.integrations.payment_gateway import reset_breaker
from app.main import app
from app.utils.metrics import reset_metrics


@pytest.fixture
def client():
    reset_breaker()
    reset_metrics()
    with TestClient(app) as test_client:
        yield test_client
