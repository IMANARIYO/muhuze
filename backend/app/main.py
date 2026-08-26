from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.bootstrap import seed_default_accounts
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware
from app.shared.exceptions.handlers import register_exception_handlers
from app.shared.responses.helpers import success_response

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with AsyncSessionLocal() as db:
        await seed_default_accounts(db)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return success_response(data={"status": "ok"}, message="Service is healthy")


@app.get("/health1")
async def health_check():
    return success_response(data={"status": "ok"}, message="Service is healthy1")
