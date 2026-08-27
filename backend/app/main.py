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
4. **Catalog curation (admin-only in v1)** — Categories, Brands,
   Attributes, Products, Variants, and Product Images are all
   admin-curated for now: an approved seller cannot yet create or list
   anything themselves. See the Products tag description for exactly
   where that line is drawn today, and what's deliberately deferred.

## Conventions

- IDs are UUIDs everywhere.
- List endpoints are unpaginated in v1 (catalog is still small).
- A `404` always means "not found *or* you can't see it" — never used to
  distinguish those two cases, to avoid leaking existence.
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
                "a seller. Being an active seller is a prerequisite for "
                "the (not yet built) seller-listing flow — it doesn't by "
                "itself grant catalog write access; see Products."
            ),
        },
        {
            "name": "Categories",
            "description": (
                "The category tree products are classified into. Reads are "
                "public; only admins create/edit categories, to keep the "
                "tree from fragmenting (\"Phones\" vs \"Mobile Phones\")."
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
                "Images. **v1 status: admin-only end to end** — creating, "
                "editing, submitting/approving/rejecting/archiving "
                "products, creating variants, and uploading images all "
                "require the admin role. There is no seller-facing "
                "'publish my listing' endpoint yet — that's a separate, "
                "not-yet-built piece (`seller_listings`: price, stock, "
                "seller SKU) that will sit on top of an approved seller "
                "plus an existing product/variant."
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
