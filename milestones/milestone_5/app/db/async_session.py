"""async engine for the few routes that await the database."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import DATABASE_URL


def _async_url(url: str) -> str:
    # psycopg 3 speaks asyncio on the same postgres url.sqlite tests need aiosqlite.
    if url.startswith("sqlite+aiosqlite"):
        return url
    if url.startswith("sqlite"):
        return "sqlite+aiosqlite" + url[len("sqlite") :]
    return url


ASYNC_DATABASE_URL = _async_url(DATABASE_URL)
async_engine_kwargs: dict = {}
if ASYNC_DATABASE_URL.startswith("sqlite"):
    async_engine_kwargs["connect_args"] = {"check_same_thread": False}

async_engine = create_async_engine(ASYNC_DATABASE_URL, **async_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_db():
    """one async session for the request.then it closes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
