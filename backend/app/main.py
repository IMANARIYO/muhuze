from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware
from app.shared.exceptions.handlers import register_exception_handlers
from app.shared.responses.helpers import success_response

configure_logging()

app = FastAPI(
    title=settings.app_name,
)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    return success_response(data={"status": "ok"}, message="Service is healthy")
