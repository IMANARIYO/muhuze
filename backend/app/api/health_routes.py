from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.shared.responses.api_response import APIResponse, success_response

# Unversioned on purpose: load balancers and uptime checks target a stable path.
health_router = APIRouter(tags=["Health"])


class HealthStatus(BaseModel):
    status: Literal["ok"]


@health_router.get("/health", response_model=APIResponse[HealthStatus])
async def health_check() -> JSONResponse:
    return success_response(data=HealthStatus(status="ok"), message="Service is healthy")
