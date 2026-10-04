"""api start file.

request goes router then service then repository then models.
schema checks input first.tables are made when app starts.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  so tables get registered before create_all
from app.db.base import Base
from app.db.migrate import ensure_columns
from app.db.seed import seed_database, seed_staff
from app.db.session import engine
from app.routers import admin_router, auth_router, cart_router, order_router, product_router, user_router, ops_router
from app.utils.exceptions import AppException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # first make tables,then put sample products only if db is empty.
    Base.metadata.create_all(bind=engine)
    ensure_columns(engine)
    seed_database()
    seed_staff()
    yield


app = FastAPI(
    title="Online Shopping Application API",
    description="JWT login, roles, admin catalog, and payment retry.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# not found,conflict and bad cart or order all come as {"detail": message}
@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# anything else we log and send a plain 500,so error details dont go out.
@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Online Shopping API", "docs": "/docs"}


app.include_router(user_router.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(product_router.router, prefix="/api")
app.include_router(cart_router.router, prefix="/api")
app.include_router(order_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")
app.include_router(ops_router.router, prefix="/api")
