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


API_DESCRIPTION = """
MUHUZE Global Link — multi-seller marketplace API. Every response is
wrapped in the same envelope: `{"status": "success"|"error", "message":
str, "data": <endpoint-specific>}`.

## Typical flow

1. **Register & log in** — `POST /auth/register`, then `POST /auth/login`
   to get an `access_token` / `refresh_token` pair. Send the access token
   as `Authorization: Bearer <token>` on every endpoint below marked
   as requiring auth. `POST /auth/refresh` rotates it before it expires.
2. **Browse the catalog** — `GET /categories`, `GET /brands`,
   `GET /products` and friends need no auth at all; anyone can browse.
3. **Want to sell?** — `POST /sellers` registers a seller profile tied to
   your account (separate from your login identity — see the Sellers tag
   description). Upload identity documents, `POST /sellers/me/submit`,
   then wait for an admin to `POST /sellers/{id}/approve`.
4. **Catalog curation** — Categories, Brands, and Attributes stay
   admin-only (controlled vocabulary, prevents catalog fragmentation).
   Products are different: an active seller can request a new one
   (`POST /products`, tagged as theirs) and manage it while it's
   `draft`/`pending_review`/`rejected`; once admin approves it, *any*
   active seller can extend it with new variants/images. See the
   Products tag description and `POST /products/mine`.

## Conventions

- IDs are UUIDs everywhere.
- List endpoints are unpaginated in v1 (catalog is still small) — filter
  params (`category_id`, `status`, `search`, etc.) narrow *which* rows
  come back, but every matching row comes back in one response; there's
  no `limit`/`offset` yet. Fine at today's scale, not forever.
- `404` vs `403` is not uniform on purpose, not an oversight: identity
  documents (`sellers/*/documents`) 404 on someone else's document —
  hides whether it even exists, since it's private KYC data.
  Product/listing ownership violations (editing another seller's
  product or listing) return `403` instead — nothing sensitive to hide
  there, and "you don't own this" is a far more useful error than a
  confusing 404 on an ID that clearly exists.
"""

app = FastAPI(
    title=settings.app_name,
    description=API_DESCRIPTION,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": (
                "Register, log in, verify email, reset password, and manage "
                "roles/permissions. Start here — almost everything else "
                "requires the access token this section issues."
            ),
        },
        {
            "name": "Users",
            "description": (
                "The caller's own profile (name, date of birth) — separate "
                "from Account (login identity) on purpose, so identity and "
                "personal-info concerns don't get tangled together."
            ),
        },
        {
            "name": "Sellers",
            "description": (
                "Becoming a seller: register a business profile tied to "
                "your account, upload identity documents, submit for "
                "review, and the admin actions that approve/reject/suspend "
                "a seller. Being an active seller is what unlocks writing "
                "to the catalog (Products tag) and creating listings "
                "(Seller Listings tag) — nothing here grants that on its "
                "own until status is `active`."
            ),
        },
        {
            "name": "Categories",
            "description": (
                "The category tree products are classified into. Reads are "
                "public; only admins create/edit categories, to keep the "
                'tree from fragmenting ("Phones" vs "Mobile Phones").'
            ),
        },
        {
            "name": "Brands",
            "description": (
                "The brand registry (Samsung, Nike, etc). Reads are "
                "public; only admins create/edit brands, same reasoning "
                "as Categories."
            ),
        },
        {
            "name": "Attributes",
            "description": (
                "The global vocabulary of things that can vary between "
                "products — Color, RAM, Size, etc. Admin-managed; sellers "
                "(once they can create variants) pick from existing "
                "attributes rather than inventing free-text fields."
            ),
        },
        {
            "name": "Products",
            "description": (
                "The catalog: Products (canonical SPU) -> Variants (SKUs, "
                "each a specific combination of attribute values) -> "
                "Images. Creatable by admin *or* any active seller "
                "(`POST /products`, tagged via `created_by_seller_id`) — "
                "see `GET /products/mine`. While a product is "
                "draft/pending_review/rejected, only its requesting "
                "seller (or admin) can edit/submit it or add "
                "variants/images (`403` otherwise); once admin approves "
                "it, any active seller may extend it with new "
                "variants/images. Approve/reject/archive stay admin-only "
                "regardless of who created it. This tag does not cover "
                "actually selling something — a Product/Variant has no "
                "price or stock. See the Seller Listings tag for that."
            ),
        },
        {
            "name": "Seller Listings",
            "description": (
                "A seller's own offer for an existing, active variant — "
                "price, stock, seller SKU, condition, and the seller's own "
                "photos. This is what actually puts something up for sale: "
                "a Product/Variant existing in the catalog is not enough "
                "on its own, a seller still needs a listing against it. "
                "Lifecycle mirrors Products: "
                "draft -> pending_review -> active, with "
                "suspend/reactivate/archive/unarchive alongside it. "
                "Fully self-service for the owning seller; approve/reject/"
                "suspend/reactivate are admin-only."
            ),
        },
    ],
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
