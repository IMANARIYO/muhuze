from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health_routes import health_router
from app.api.v1.api_v1_routes import api_v1_router
from app.config.settings import Settings, get_settings
from app.core.database import create_database_engine, create_session_factory
from app.core.logging import configure_logging, get_logger
from app.core.request_context_middleware import RequestContextMiddleware
from app.core.security import build_password_hasher
from app.infrastructure.notifications.email_sender import build_email_sender
from app.shared.exceptions.exception_handlers import register_exception_handlers

logger = get_logger(__name__)

API_DESCRIPTION = """
MUHUZE Global Link — multi-seller marketplace API.

Every response, success or error, uses the same envelope:

```json
{"success": true, "data": {}, "message": "Request successful", "status_code": 200}
```

Every response carries an `X-Request-ID` header; send your own (letters,
digits, `.`, `_`, `:`, `-`, up to 128 chars) to correlate client and server logs.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    engine = create_database_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("application started", extra={"environment": settings.environment})
        yield
        await engine.dispose()
        logger.info("application stopped")

    app = FastAPI(title=settings.app_name, description=API_DESCRIPTION, lifespan=lifespan)
    # Shared, request-independent objects. Dependencies read them from
    # `request.app.state`, which also lets tests swap them.
    app.state.settings = settings
    app.state.session_factory = create_session_factory(engine)
    app.state.password_hasher = build_password_hasher(settings)
    app.state.email_sender = build_email_sender(settings)

    register_exception_handlers(app)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health_router)
    app.include_router(api_v1_router)
    return app


app = create_app()
