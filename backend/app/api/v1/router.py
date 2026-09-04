from fastapi import APIRouter

from app.modules.addresses.router import router as addresses_router
from app.modules.auth.router import router as auth_router
from app.modules.carts.router import router as carts_router
from app.modules.catalog.router import router as catalog_router
from app.modules.categories.router import router as categories_router
from app.modules.orders.fulfillment_router import router as fulfillment_router
from app.modules.orders.router import router as orders_router
from app.modules.payments.router import router as payments_router
from app.modules.premium.router import router as premium_router
from app.modules.products.router import (
    attributes_router,
    brands_router,
    listings_router,
    products_router,
)
from app.modules.revenue.router import router as revenue_router
from app.modules.sellers.router import router as sellers_router
from app.modules.users.router import router as users_router
from app.modules.wallets.router import router as wallets_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(sellers_router)
api_router.include_router(categories_router)
api_router.include_router(brands_router)
api_router.include_router(attributes_router)
api_router.include_router(products_router)
api_router.include_router(listings_router)
api_router.include_router(premium_router)
api_router.include_router(catalog_router)
api_router.include_router(addresses_router)
api_router.include_router(carts_router)
api_router.include_router(fulfillment_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(revenue_router)
api_router.include_router(wallets_router)
