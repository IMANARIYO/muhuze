import uuid

from fastapi import APIRouter, Depends, Query

from app.modules.catalog.controller import CatalogController
from app.modules.catalog.dependencies import get_catalog_controller
from app.modules.catalog.schemas import (
    CatalogFilters,
    CatalogListingDetail,
    CatalogListingItem,
    CatalogProductDetail,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/filters")
async def get_filters(
    category_id: uuid.UUID | None = Query(
        default=None,
        description="Optional category; the response also covers all its subcategories",
    ),
    controller: CatalogController = Depends(get_catalog_controller),
) -> APIResponse[CatalogFilters]:
    """Get the dynamic filter sidebar for a category (or the whole catalog).

    Nothing here is hardcoded per category. The endpoint looks at which
    attributes are marked `is_filterable` in `category_attributes` for the
    category (and its descendants), and only returns values that actually
    have an active offer behind them. The frontend renders checkboxes
    straight from this payload — no `if category == 'phones'` logic needed.

    Fields returned: `category_ids` (selected category + descendants),
    `brands`, `attributes` (each with its live `values`), `price_range`
    (min/max across active offers), and `conditions`. Feed these straight
    back into `GET /api/v1/catalog` as query params. Public — no auth.
    """
    filters = await controller.get_filters(category_id)
    return success_response(data=filters, message="Catalog filters retrieved successfully")


@router.get("")
async def search_catalog(
    category_id: uuid.UUID | None = Query(
        default=None,
        description="Show only products in this category (and all its subcategories)",
    ),
    brand_id: uuid.UUID | None = Query(
        default=None, description="Show only products of this brand"
    ),
    search: str | None = Query(
        default=None,
        description="Case-insensitive match on product name, brand name, category name, "
        "or any variant attribute value (e.g. 'black iphone 256gb')",
    ),
    min_price: float | None = Query(
        default=None, ge=0, description="Only offers at or above this price"
    ),
    max_price: float | None = Query(
        default=None, ge=0, description="Only offers at or below this price"
    ),
    condition: list[str] | None = Query(
        default=None, description="Only offers with these conditions: new | like_new | used"
    ),
    in_stock: bool = Query(
        default=False, description="Only offers with stock remaining (stock > 0)"
    ),
    attribute_id: list[uuid.UUID] | None = Query(
        default=None,
        description="Attribute to filter on. Pair with `value` by index — repeat both "
        "for multiple filters (e.g. attribute_id=UUID1&value=128GB&attribute_id=UUID2&value=Black). "
        "All pairs must match the same variant (AND).",
    ),
    value: list[str] | None = Query(
        default=None,
        description="Attribute filter value(s); zipped with `attribute_id` by index.",
    ),
    sort: str | None = Query(
        default="price_asc",
        description="'price_asc' (cheapest first) | 'price_desc' | 'newest'",
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

    Filters (all optional, combinable):
    - `category_id`: selected category plus all its descendants
    - `brand_id`: exact brand
    - `search`: name / brand / category / variant-attribute match
    - `min_price` / `max_price`: seller-listing price bounds
    - `condition`: new, like_new, used (repeat to select several)
    - `in_stock=true`: only offers with stock > 0
    - `attribute_id` + `value` (parallel lists): variant-attribute filters,
      e.g. Storage=256GB AND Color=Black

    `sort` defaults to cheapest-first; use `price_desc` or `newest` to
    change it. There is no pagination yet — the catalog is small in v1 and
    every matching row comes back at once.
    """
    filters = None
    if attribute_id or value:
        if not attribute_id or not value or len(attribute_id) != len(value):
            # Mismatched pairs — treat as no attribute filter rather than 422.
            filters = None
        else:
            filters = {
                "attribute_ids": attribute_id,
                "attribute_values": value,
            }

    items = await controller.search_active_listings(
        category_id=category_id,
        brand_id=brand_id,
        search=search,
        sort=sort,
        min_price=min_price,
        max_price=max_price,
        conditions=condition,
        in_stock=in_stock,
        filters=filters,
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


@router.get("/listings/{listing_id}")
async def get_listing_detail(
    listing_id: uuid.UUID,
    controller: CatalogController = Depends(get_catalog_controller),
) -> APIResponse[CatalogListingDetail]:
    """Get the customer's detail page for one *selected* seller listing.

    This is the endpoint a storefront card links to. Unlike `/products/{id}`
    (all variants + every seller), this returns the exact seller offer the
    customer clicked: the product, the variant with its admin-defined
    attribute values, the selling seller, all images, price/stock/condition,
    the seller's own SKU, and when it was listed. Only active rows are ever
    returned; anything archived/suspended/rejected is a 404. Public — no
    auth required.
    """
    detail = await controller.get_listing_detail(listing_id)
    return success_response(data=detail, message="Listing detail retrieved successfully")
