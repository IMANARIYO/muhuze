from fastapi import APIRouter

from app.modules.auth.auth_routes import auth_router
from app.modules.authorization.authorization_routes import authorization_router
from app.modules.sellers.seller_routes import seller_router

API_V1_PREFIX = "/api/v1"

# Every feature module's router is included here, once, so main.py mounts a
# single router regardless of how many modules exist.
api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(authorization_router)
api_v1_router.include_router(seller_router)
