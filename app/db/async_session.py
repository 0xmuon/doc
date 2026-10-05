"""async engine for the few routes that await the database."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import DATABASE_URL


def _async_url(url: str) -> str:
    # psycopg 3 speaks asyncio on the same postgres url.a plain sqlite url needs aiosqlite.
    if url.startswith("sqlite") and not url.startswith("sqlite+aiosqlite"):
        return "sqlite+aiosqlite" + url[len("sqlite") :]
    return url


ASYNC_DATABASE_URL = _async_url(DATABASE_URL)
connect_args = {"check_same_thread": False} if ASYNC_DATABASE_URL.startswith("sqlite") else {}
async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_db():
    """one async session for the request.then it closes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
