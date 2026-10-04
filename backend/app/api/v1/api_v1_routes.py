from fastapi import APIRouter

API_V1_PREFIX = "/api/v1"

# Every feature module's router is included here, once, so main.py mounts a
# single router regardless of how many modules exist.
api_v1_router = APIRouter(prefix=API_V1_PREFIX)
