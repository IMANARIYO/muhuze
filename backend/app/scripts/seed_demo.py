"""Seed demo catalog data for local development.

Idempotent demo data so the frontend finally has something to render:

    - registers a Seller profile for the configured test-seller account
      (seller@muhuze.com by default) and has an admin approve it
    - creates categories, brands and attributes (via the admin)
    - creates 4+ products, each with ~8 variants, by that seller
    - submits + approves each product and each listing, so everything
      shows up as active in GET /api/v1/catalog

Run against the database configured in backend/.env:

    cd backend
    uv run python -m app.scripts.seed_demo

It talks to the running app's code directly (ASGI in-process), exactly like
the test suite does, and stubs Cloudinary so no real uploads happen — a
placeholder image URL is stored so catalog cards render.

Safe to re-run: each step skips cleanly if the row already exists.
"""

import asyncio

from httpx import ASGITransport, AsyncClient

# --- storage stub: keep the seed offline, no Cloudinary required ------------
from app.core import storage
from app.main import app


def _install_storage_stub() -> None:
    storage.settings.cloudinary_cloud_name = "seed-placeholder"
    storage.settings.cloudinary_api_key = "seed-placeholder"
    storage.settings.cloudinary_api_secret = "seed-placeholder"

    def _fake_do_upload(file_obj, *, folder, public_id, delivery_type):
        return {
            "public_id": public_id,
            "url": f"http://res.cloudinary.com/seed/{public_id}",
            "secure_url": f"https://res.cloudinary.com/seed/{public_id}",
            "format": "jpg",
            "resource_type": "image",
            "type": delivery_type,
            "bytes": 1234,
        }

    storage._do_upload = _fake_do_upload
    storage._do_delete = lambda *a, **k: None
    storage._do_get_signed_url = lambda public_id, **k: f"https://cdn/{public_id}"
    storage._do_get_public_url = lambda public_id, **k: f"https://cdn/{public_id}"


_install_storage_stub()


# --- config ------------------------------------------------------------------

from app.core.config import settings


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _email(payload: dict) -> dict:
    return {"email": payload["email"], "password": payload["password"]}


# Category tree under one top-level "Electronics" root.
_CATEGORIES = ["Electronics", "Phones", "Audio", "Computers"]

# (attribute name, input_type)
_ATTRIBUTES = [
    ("Color", "select"),
    ("Storage", "select"),
    ("RAM", "select"),
]

# (brand name)
_BRANDS = ["Apple", "Samsung", "Sony", "Dell", "JBL"]


async def _ensure_login(client: AsyncClient) -> tuple[dict, dict]:
    admin_login = await client.post(
        "/api/v1/auth/login",
        json=_email(
            {"email": settings.super_admin_email, "password": settings.super_admin_password}
        ),
    )
    admin_login.raise_for_status()
    admin_tokens = admin_login.json()["data"]

    seller_login = await client.post(
        "/api/v1/auth/login",
        json=_email(
            {"email": settings.test_seller_email, "password": settings.test_seller_password}
        ),
    )
    seller_login.raise_for_status()
    seller_tokens = seller_login.json()["data"]
    return admin_tokens, seller_tokens


async def _ensure_catalog_taxonomy(
    client: AsyncClient, admin_tokens: dict
) -> dict[str, str]:
    """Create categories/brands/attributes if missing. Returns id maps."""
    admin_headers = _auth(admin_tokens)

    cats = (await client.get("/api/v1/categories")).json()["data"]
    by_name = {c["name"]: c["id"] for c in cats}
    child_parent = {}

    for name in _CATEGORIES:
        if name in by_name:
            continue
        parent_id = None if name == "Electronics" else by_name["Electronics"]
        resp = await client.post(
            "/api/v1/categories",
            json={"name": name, "parent_id": parent_id},
            headers=admin_headers,
        )
        resp.raise_for_status()
        child = resp.json()["data"]
        by_name[name] = child["id"]
        if name != "Electronics":
            child_parent[name] = child["id"]

    brands = (await client.get("/api/v1/brands")).json()["data"]
    brand_by_name = {b["name"]: b["id"] for b in brands}
    for name in _BRANDS:
        if name not in brand_by_name:
            resp = await client.post(
                "/api/v1/brands", json={"name": name}, headers=admin_headers
            )
            resp.raise_for_status()
            brand_by_name[name] = resp.json()["data"]["id"]

    attrs = (await client.get("/api/v1/attributes")).json()["data"]
    attr_by_name = {a["name"]: a["id"] for a in attrs}
    for name, iptype in _ATTRIBUTES:
        if name not in attr_by_name:
            resp = await client.post(
                "/api/v1/attributes",
                json={"name": name, "input_type": iptype},
                headers=admin_headers,
            )
            resp.raise_for_status()
            attr_by_name[name] = resp.json()["data"]["id"]

    return {
        "category_ids": by_name,
        "brand_ids": brand_by_name,
        "attribute_ids": attr_by_name,
    }


async def _ensure_active_seller(
    client: AsyncClient, seller_tokens: dict, admin_tokens: dict
) -> str:
    headers = _auth(seller_tokens)
    me = await client.get("/api/v1/sellers/me", headers=headers)
    if me.status_code == 200:
        seller_id = me.json()["data"]["id"]
    else:
        created = await client.post(
            "/api/v1/sellers",
            json={
                "business_name": "Muhuze Seed Shop",
                "business_description": "Demo catalog data for local development.",
            },
            headers=headers,
        )
        created.raise_for_status()
        seller_id = created.json()["data"]["id"]

    status = me.json()["data"]["status"] if me.status_code == 200 else "draft"

    if status not in ("active", "pending_review"):
        for doc_type in ("national_id_front", "national_id_back"):
            await client.post(
                "/api/v1/sellers/me/documents",
                data={"document_type": doc_type},
                files={"file": ("id.jpg", b"fake-bytes", "image/jpeg")},
                headers=headers,
            )
        await client.post("/api/v1/sellers/me/submit", headers=headers)
        status = "pending_review"

    if status == "pending_review":
        resp = await client.post(
            f"/api/v1/sellers/{seller_id}/approve", headers=_auth(admin_tokens)
        )
        resp.raise_for_status()

    return seller_id


# Each product: name, brand, category, list of variant value sets. Values
# reference attributes by the key used in _ATTRIBUTES above.
_PRODUCTS = [
    {
        "name": "iPhone 15 Pro",
        "brand": "Apple",
        "category": "Phones",
        "description": "Apple flagship smartphone.",
        "variants": [
            {"Color": "Black", "Storage": "128GB"},
            {"Color": "Black", "Storage": "256GB"},
            {"Color": "Blue", "Storage": "256GB"},
            {"Color": "White", "Storage": "256GB"},
            {"Color": "Blue", "Storage": "512GB"},
            {"Color": "White", "Storage": "512GB"},
            {"Color": "Natural", "Storage": "256GB"},
            {"Color": "Natural", "Storage": "1TB"},
        ],
    },
    {
        "name": "Samsung Galaxy S24",
        "brand": "Samsung",
        "category": "Phones",
        "description": "Samsung flagship smartphone.",
        "variants": [
            {"Color": "Black", "Storage": "128GB"},
            {"Color": "Black", "Storage": "256GB"},
            {"Color": "Gray", "Storage": "256GB"},
            {"Color": "Violet", "Storage": "256GB"},
            {"Color": "Gray", "Storage": "512GB"},
            {"Color": "Green", "Storage": "256GB"},
            {"Color": "Black", "Storage": "512GB"},
            {"Color": "Violet", "Storage": "512GB"},
        ],
    },
    {
        "name": "Wireless Earbuds Pro",
        "brand": "Sony",
        "category": "Audio",
        "description": "Noise-cancelling wireless earbuds.",
        "variants": [
            {"Color": "Black", "Storage": "Standard"},
            {"Color": "White", "Storage": "Standard"},
            {"Color": "Black", "Storage": "With Case"},
            {"Color": "White", "Storage": "With Case"},
            {"Color": "Blue", "Storage": "Standard"},
            {"Color": "Silver", "Storage": "With Case"},
            {"Color": "Black", "Storage": "Ultra"},
            {"Color": "White", "Storage": "Ultra"},
        ],
    },
    {
        "name": "Laptop 15.6\" Ultrabook",
        "brand": "Dell",
        "category": "Computers",
        "description": "15.6 inch ultrabook.",
        "variants": [
            {"RAM": "8GB", "Storage": "256GB"},
            {"RAM": "8GB", "Storage": "512GB"},
            {"RAM": "16GB", "Storage": "512GB"},
            {"RAM": "16GB", "Storage": "1TB"},
            {"RAM": "32GB", "Storage": "1TB"},
            {"RAM": "16GB", "Storage": "2TB"},
            {"RAM": "8GB", "Storage": "1TB"},
            {"RAM": "32GB", "Storage": "2TB"},
        ],
    },
]


async def _ensure_product(
    client: AsyncClient,
    seller_tokens: dict,
    admin_tokens: dict,
    taxonomy: dict,
    product_cfg: dict,
) -> int:
    seller_headers = _auth(seller_tokens)
    admin_headers = _auth(admin_tokens)

    category_id = taxonomy["category_ids"][product_cfg["category"]]
    brand_id = taxonomy["brand_ids"][product_cfg["brand"]]

    # Skip if the product already exists and is active.
    existing = (await client.get("/api/v1/products", params={"search": product_cfg["name"]})).json()["data"]
    for prod in existing:
        if prod["name"] == product_cfg["name"]:
            return 0

    created = await client.post(
        "/api/v1/products",
        json={
            "category_id": category_id,
            "brand_id": brand_id,
            "name": product_cfg["name"],
            "description": product_cfg["description"],
        },
        headers=seller_headers,
    )
    created.raise_for_status()
    product_id = created.json()["data"]["id"]

    # One placeholder product image so cards render.
    await client.post(
        f"/api/v1/products/{product_id}/images",
        data={"is_primary": "true"},
        files={"file": ("p.jpg", b"fake-bytes", "image/jpeg")},
        headers=seller_headers,
    )

    # Create every variant first (while the product is still draft only the
    # requesting seller or admin may add them).
    variant_ids = []
    for vs in product_cfg["variants"]:
        values = [
            {"attribute_id": taxonomy["attribute_ids"][k], "value": v}
            for k, v in vs.items()
        ]
        vresp = await client.post(
            f"/api/v1/products/{product_id}/variants",
            json={"attribute_values": values},
            headers=seller_headers,
        )
        vresp.raise_for_status()
        variant_ids.append(vresp.json()["data"]["id"])

    # A listing / variant must exist only once the parent product is active.
    await client.post(f"/api/v1/products/{product_id}/submit", headers=seller_headers)
    await client.post(f"/api/v1/products/{product_id}/approve", headers=admin_headers)

    for variant_id in variant_ids:
        listing = await client.post(
            "/api/v1/listings",
            json={
                "variant_id": variant_id,
                "price": _price_for(product_cfg["name"]),
                "stock": 25,
                "condition": "new",
            },
            headers=seller_headers,
        )
        listing.raise_for_status()
        listing_id = listing.json()["data"]["id"]
        await client.post(f"/api/v1/listings/{listing_id}/submit", headers=seller_headers)
        await client.post(f"/api/v1/listings/{listing_id}/approve", headers=admin_headers)

    return len(product_cfg["variants"])


def _price_for(product_name: str) -> float:
    table = {
        "iPhone 15 Pro": 949.99,
        "Samsung Galaxy S24": 799.99,
        "Wireless Earbuds Pro": 199.99,
        'Laptop 15.6" Ultrabook': 1099.99,
    }
    return table.get(product_name, 299.99)


async def main() -> None:
    transport = ASGITransport(app=app)
    total_variants = 0
    async with AsyncClient(transport=transport, base_url="http://seed") as client:
        admin_tokens, seller_tokens = await _ensure_login(client)
        taxonomy = await _ensure_catalog_taxonomy(client, admin_tokens)
        await _ensure_active_seller(client, seller_tokens, admin_tokens)

        for product_cfg in _PRODUCTS:
            n = await _ensure_product(
                client, seller_tokens, admin_tokens, taxonomy, product_cfg
            )
            total_variants += n

    print(f"Done. Seeded products/variants in this run: {total_variants}")
    print("Browse http://127.0.0.1:8000/api/v1/catalog to see the data.")


if __name__ == "__main__":
    asyncio.run(main())
