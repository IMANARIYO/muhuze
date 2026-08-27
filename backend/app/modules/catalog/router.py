import uuid

from fastapi import APIRouter, Depends, Query

from app.modules.catalog.controller import CatalogController
from app.modules.catalog.dependencies import get_catalog_controller
from app.modules.catalog.schemas import (
    CatalogListingItem,
    CatalogProductDetail,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("")
async def search_catalog(
    category_id: uuid.UUID | None = Query(
        default=None, description="Show only products in this category"
    ),
    brand_id: uuid.UUID | None = Query(
        default=None, description="Show only products of this brand"
    ),
    search: str | None = Query(
        default=None, description="Case-insensitive substring match on product name"
    ),
    sort: str | None = Query(
        default="price_asc",
        description="Price ordering: 'price_asc' (cheapest first) or 'price_desc'",
    ),
    controller: CatalogController = Depends(get_catalog_controller),
) -> APIResponse[list[CatalogListingItem]]:
    """Browse what's actually for sale.

    Returns every **active listing** currently offered by an active
    seller, joined with its product, variant (with attribute values), and
    the seller's business name — so a storefront card has everything it
    needs in one call. Only `active` product/variant/listing rows are
    ever returned; nothing draft, rejected, suspended, or archived is
    visible here. Public — no auth required.

    `sort` defaults to cheapest-first; use `sort=price_desc` for the
    reverse. Filter on `category_id`, `brand_id`, and/or `search` to
    narrow the results. There is no pagination yet — the catalog is
    small in v1 and every matching row comes back at once.
    """
    items = await controller.search_active_listings(
        category_id=category_id,
        brand_id=brand_id,
        search=search,
        sort=sort,
    )
    return success_response(data=items, message="Catalog retrieved successfully")


@router.get("/products/{product_id}")
async def get_product_detail(
    product_id: uuid.UUID,
    controller: CatalogController = Depends(get_catalog_controller),
) -> APIResponse[CatalogProductDetail]:
    """Get a buyer-facing product detail page.

    Returns the product (name, slug, description), its canonical images,
    and every **active variant** with the list of current **active
    sellers** offering it (each with price, stock, condition). Use this
    page to show variants side by side and pick which seller to buy
    from. Public — no auth required.
    """
    detail = await controller.get_product_detail(product_id)
    return success_response(data=detail, message="Product detail retrieved successfully")
