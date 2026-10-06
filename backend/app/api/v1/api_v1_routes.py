from fastapi import APIRouter

from app.modules.auth.auth_routes import auth_router
from app.modules.authorization.authorization_routes import authorization_router
from app.modules.categories.category_routes import category_router
from app.modules.orders.order_routes import order_router
from app.modules.payments.payment_routes import payment_router
from app.modules.products.product_routes import product_router
from app.modules.seller_plans.seller_plan_routes import seller_plan_router
from app.modules.sellers.seller_routes import seller_router
from app.modules.wallets.wallet_routes import wallet_router

API_V1_PREFIX = "/api/v1"

# Every feature module's router is included here, once, so main.py mounts a
# single router regardless of how many modules exist.
api_v1_router = APIRouter(prefix=API_V1_PREFIX)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(authorization_router)
api_v1_router.include_router(seller_router)
api_v1_router.include_router(category_router)
api_v1_router.include_router(product_router)
api_v1_router.include_router(seller_plan_router)
api_v1_router.include_router(order_router)
api_v1_router.include_router(payment_router)
api_v1_router.include_router(wallet_router)
