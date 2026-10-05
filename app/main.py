"""api start file.

request goes router then service then repository then models.
schema checks input first.tables are made when app starts.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text

import app.models  # noqa: F401  so tables get registered before create_all
from app.db import AsyncSessionLocal, Base, engine
from app.db.seed import seed_database, seed_users
from app.integrations import payment_breaker
from app.routers import admin_router, auth_router, cart_router, ops_router, order_router, product_router, user_router
from app.utils import AppException, RequestLogMiddleware, configure_logging, log_event, metrics_report, request_id_var

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # a fresh database comes from docker compose down -v.create_all builds the tables.
    configure_logging()
    Base.metadata.create_all(bind=engine)
    seed_database()
    seed_users()
    yield


app = FastAPI(
    title="Online Shopping Application API",
    description="",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# added last so it runs first and sees the final status code.
app.add_middleware(RequestLogMiddleware)


# not found,conflict and bad cart or order all come as {"detail": message}
@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "request_id": request_id_var.get()},
    )


# anything else we log and send a plain 500,so error details dont go out.
@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    log_event("unhandled_error", error=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id_var.get()},
    )


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Online Shopping API", "docs": "/docs"}


@app.get("/docs", include_in_schema=False)
async def swagger_ui():
    page = get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{app.title} - Swagger UI")
    html = page.body.decode().replace("</head>", "<style>.scope-def{display:none}</style></head>")
    return HTMLResponse(html)


@app.get("/health", summary="Health")
def health():
    return {"status": "ok"}


@app.get("/health/db", summary="Database")
async def health_db():
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/metrics", summary="Metrics")
def metrics():
    return {
        "routes": metrics_report(),
        "payment_circuit": {"state": payment_breaker.state, "failures": payment_breaker.failures},
    }


def custom_openapi():
    """authorize shows login (email as username) or a pasted jwt.either one is enough."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schemes = schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schemes["Login"] = {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/api/auth/token",
                "scopes": {},
            }
        },
    }
    http_methods = {"get", "post", "put", "patch", "delete"}
    for path_item in schema.get("paths", {}).values():
        for method, operation in path_item.items():
            if method not in http_methods or not isinstance(operation, dict):
                continue
            security = operation.get("security")
            if not security or not any("JWT" in item for item in security):
                continue
            operation["security"] = [*security, {"Login": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

app.include_router(user_router.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(product_router.router, prefix="/api")
app.include_router(cart_router.router, prefix="/api")
app.include_router(order_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")
app.include_router(ops_router.router, prefix="/api")
