"""db engine and the session we open for each request."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# postgresql+psycopg://user:password@db:5432/shopping
# sqlite+aiosqlite:///./ecommerce.db
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://shop:shop@localhost:5433/shopping",
)


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
