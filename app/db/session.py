"""db engine and the session we open for each request."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _database_url() -> str:
    """Where the database credentials come from, in order:

    1. ``DATABASE_URL`` env var — local dev, Docker Compose, tests.
    2. AWS Secrets Manager — on EC2 (``USE_SECRETS_MANAGER=1``), so the
       deployed box needs no .env file at all. See SECRETS_MANAGER.md.
    3. Local Postgres default for a bare ``uvicorn`` run.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    from app.secrets import secrets_enabled

    if secrets_enabled():
        from app.secrets import database_url_from_secret

        return database_url_from_secret()
    # postgresql+psycopg://user:password@db:5432/shopping
    return "postgresql+psycopg://shop:shop@localhost:5433/shopping"


DATABASE_URL = _database_url()


def _sync_url(url: str) -> str:
    # a sqlite url names the async driver.the sync engine uses the plain sqlite driver.
    if url.startswith("sqlite+aiosqlite"):
        return "sqlite" + url[len("sqlite+aiosqlite") :]
    return url


SYNC_DATABASE_URL = _sync_url(DATABASE_URL)
connect_args = {"check_same_thread": False} if SYNC_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SYNC_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    """one session per request.if something fails we rollback and then close it."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
