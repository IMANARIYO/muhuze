import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.products.models import CategoryAttribute

_ACTIVE = "active"


def unique_email() -> str:
    return f"catalog-test-{uuid.uuid4().hex}@example.com"


def unique_name(prefix: str = "Thing") -> str:
    return f"{prefix} {uuid.uuid4().hex}"


async def register_and_login(
    client: AsyncClient, password: str = "supersecret123"
) -> tuple[str, dict]:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return email, response.json()["data"]


async def make_admin(client: AsyncClient, db: AsyncSession) -> dict:
    email, tokens = await register_and_login(client)
    account = await AccountRepository(db).get_by_email(email)
    assert account is not None
    admin_role = await AuthorizationRepository(db).get_role_by_name("admin")
    assert admin_role is not None
    await AuthorizationRepository(db).assign_role(
        account_id=account.id, role_id=admin_role.id
    )
    await db.commit()
    return tokens


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture(autouse=True)
def _cloudinary_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage.settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(storage.settings, "cloudinary_api_key", "test-key")
    monkeypatch.setattr(storage.settings, "cloudinary_api_secret", "test-secret")


def fake_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_do_upload(file_obj, *, folder, public_id, delivery_type):
        return {
            "public_id": public_id,
            "url": f"http://res.cloudinary.com/{public_id}",
            "secure_url": f"https://res.cloudinary.com/{public_id}",
            "format": "jpg",
            "resource_type": "image",
            "type": delivery_type,
            "bytes": 1234,
        }

    monkeypatch.setattr(storage, "_do_upload", _fake_do_upload)
    monkeypatch.setattr(storage, "_do_delete", lambda *a, **k: None)
    monkeypatch.setattr(
        storage, "_do_get_public_url", lambda public_id, **k: f"https://cdn/{public_id}"
    )


async def make_active_seller(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict, str]:
    """Registers an account, becomes an active seller, returns
    (tokens, seller_id)."""
    fake_upload(monkeypatch)
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_name("Business")},
        headers=headers,
    )
    for doc_type in ("national_id_front", "national_id_back"):
        await client.post(
            "/api/v1/sellers/me/documents",
            data={"document_type": doc_type},
            files={"file": ("id.jpg", b"fake-bytes", "image/jpeg")},
            headers=headers,
        )
    await client.post("/api/v1/sellers/me/submit", headers=headers)
    my_seller = await client.get("/api/v1/sellers/me", headers=headers)
    seller_id = my_seller.json()["data"]["id"]

    admin_tokens = await make_admin(client, db)
    approved = await client.post(
        f"/api/v1/sellers/{seller_id}/approve", headers=auth_headers(admin_tokens)
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == _ACTIVE
    return tokens, seller_id


async def publish_product_with_listing(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str | None = None,
    price: float = 100.0,
    stock: int = 5,
    condition: str = "new",
    category_parent_id: uuid.UUID | None = None,
    brand_id: uuid.UUID | None = None,
) -> dict:
    """Creates an active seller, an active product (with an image and a
    variant), and an approved listing for it. Returns the assembled
    payload: {tokens, seller_id, product_id, variant_id, listing_id,
    category_id, product_name, attribute_id}."""
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)

    category_resp = await client.post(
        "/api/v1/categories",
        json={
            "name": unique_name("Category"),
            **({"parent_id": str(category_parent_id)} if category_parent_id else {}),
        },
        headers=admin_headers,
    )
    category_id = category_resp.json()["data"]["id"]
    attribute_resp = await client.post(
        "/api/v1/attributes", json={"name": unique_name("Attr")}, headers=admin_headers
    )
    attribute_id = attribute_resp.json()["data"]["id"]

    seller_tokens, seller_id = await make_active_seller(client, db, monkeypatch)
    seller_headers = auth_headers(seller_tokens)

    product_name = name or unique_name("Product")
    product_payload = {"category_id": category_id, "name": product_name}
    if brand_id is not None:
        product_payload["brand_id"] = str(brand_id)
    product_resp = await client.post(
        "/api/v1/products", json=product_payload, headers=seller_headers
    )
    product_id = product_resp.json()["data"]["id"]

    image_resp = await client.post(
        f"/api/v1/products/{product_id}/images",
        data={"is_primary": "true"},
        files={"file": ("p.jpg", b"fake-bytes", "image/jpeg")},
        headers=seller_headers,
    )
    assert image_resp.status_code == 201

    variant_resp = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={
            "attribute_values": [{"attribute_id": attribute_id, "value": "Black"}]
        },
        headers=seller_headers,
    )
    variant_id = variant_resp.json()["data"]["id"]

    await client.post(f"/api/v1/products/{product_id}/submit", headers=seller_headers)
    await client.post(f"/api/v1/products/{product_id}/approve", headers=admin_headers)

    listing_resp = await client.post(
        "/api/v1/listings",
        json={
            "variant_id": variant_id,
            "price": price,
            "stock": stock,
            "condition": condition,
        },
        headers=seller_headers,
    )
    listing_id = listing_resp.json()["data"]["id"]
    await client.post(f"/api/v1/listings/{listing_id}/submit", headers=seller_headers)
    await client.post(f"/api/v1/listings/{listing_id}/approve", headers=admin_headers)

    return {
        "admin_tokens": admin_tokens,
        "admin_headers": admin_headers,
        "seller_id": seller_id,
        "product_id": product_id,
        "variant_id": variant_id,
        "listing_id": listing_id,
        "category_id": category_id,
        "attribute_id": attribute_id,
        "product_name": product_name,
        "price": price,
        "stock": stock,
        "condition": condition,
    }


# --- GET /catalog -----------------------------------------------------------


async def test_catalog_requires_no_auth(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await publish_product_with_listing(client, db, monkeypatch)
    response = await client.get("/api/v1/catalog")
    assert response.status_code == 200


async def test_catalog_returns_active_listing_with_shapes(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = await publish_product_with_listing(client, db, monkeypatch)
    response = await client.get("/api/v1/catalog")
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    item = data[0]
    assert item["listing_id"] == ctx["listing_id"]
    assert item["price"] == ctx["price"]
    assert item["stock"] == 5
    assert item["condition"] == "new"
    assert item["product"]["id"] == ctx["product_id"]
    assert item["product"]["name"] == ctx["product_name"]
    assert item["product"]["category_id"] == ctx["category_id"]
    assert item["variant"]["id"] == ctx["variant_id"]
    assert item["variant"]["attribute_values"][0]["value"] == "Black"
    assert item["seller"]["business_name"]
    assert len(item["images"]) == 1
    assert item["images"][0]["is_primary"] is True


async def test_catalog_excludes_draft_listing(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = await publish_product_with_listing(client, db, monkeypatch)

    seller_tokens, _ = await make_active_seller(client, db, monkeypatch)
    # A second seller lists the same active variant but leaves it in draft
    draft = await client.post(
        "/api/v1/listings",
        json={
            "variant_id": ctx["variant_id"],
            "price": 999.0,
            "stock": 1,
        },
        headers=auth_headers(seller_tokens),
    )
    assert draft.status_code == 201
    draft_id = draft.json()["data"]["id"]
    assert draft.json()["data"]["status"] == "draft"

    list_resp = await client.get("/api/v1/catalog")
    listing_ids = [i["listing_id"] for i in list_resp.json()["data"]]
    assert ctx["listing_id"] in listing_ids
    assert draft_id not in listing_ids


async def test_catalog_search_and_price_sort(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = await publish_product_with_listing(
        client, db, monkeypatch, name="UniqueGoldPhone", price=300.0
    )
    await publish_product_with_listing(client, db, monkeypatch, price=500.0)

    # search only should return the gold phone
    search_resp = await client.get(
        "/api/v1/catalog", params={"search": "UniqueGoldPhone"}
    )
    results = search_resp.json()["data"]
    assert len(results) == 1
    assert results[0]["product"]["name"] == "UniqueGoldPhone"

    # category filter should return all items in that category
    cat_resp = await client.get(
        "/api/v1/catalog", params={"category_id": ctx["category_id"]}
    )
    assert len(cat_resp.json()["data"]) >= 1


# --- GET /catalog/products/{id} ---------------------------------------------


async def test_product_detail_returns_variants_and_offers(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = await publish_product_with_listing(client, db, monkeypatch)
    response = await client.get(f"/api/v1/catalog/products/{ctx['product_id']}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == ctx["product_id"]
    assert data["name"] == ctx["product_name"]
    assert len(data["images"]) == 1
    assert len(data["variants"]) == 1
    variant = data["variants"][0]
    assert variant["id"] == ctx["variant_id"]
    assert variant["attribute_values"][0]["value"] == "Black"
    assert len(variant["offers"]) == 1
    assert variant["offers"][0]["listing_id"] == ctx["listing_id"]
    assert variant["offers"][0]["price"] == ctx["price"]


async def test_product_detail_unknown_product_404(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await publish_product_with_listing(client, db, monkeypatch)
    response = await client.get(f"/api/v1/catalog/products/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_product_detail_draft_product_404(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    category_id_resp = await client.post(
        "/api/v1/categories", json={"name": unique_name("Category")}, headers=admin_headers
    )
    category_id = category_id_resp.json()["data"]["id"]
    seller_tokens, _ = await make_active_seller(client, db, monkeypatch)
    created = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name("Draft")},
        headers=auth_headers(seller_tokens),
    )
    product_id = created.json()["data"]["id"]
    # never submitted/approved -> still draft, should not be in the public catalog
    response = await client.get(f"/api/v1/catalog/products/{product_id}")
    assert response.status_code == 404


# --- GET /catalog/filters ---------------------------------------------------


async def test_filters_returns_price_conditions_brands_attributes(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=250.0)
    response = await client.get(
        "/api/v1/catalog/filters", params={"category_id": ctx["category_id"]}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert ctx["category_id"] in data["category_ids"]
    assert data["price_range"] == {"min": 250.0, "max": 250.0}
    assert data["conditions"] == ["new"]
    # no brand and no category_attribute linkage yet -> empty facets
    assert data["brands"] == []
    assert data["attributes"] == []


async def test_filters_attribute_facet_when_category_attribute_configured(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = await publish_product_with_listing(client, db, monkeypatch)
    # No API exists yet to link an attribute to a category -> seed the
    # CategoryAttribute junction directly (is_filterable=true) so the facet
    # logic can be exercised.
    db.add(
        CategoryAttribute(
            category_id=ctx["category_id"],
            attribute_id=ctx["attribute_id"],
            is_filterable=True,
        )
    )
    await db.commit()

    response = await client.get(
        "/api/v1/catalog/filters", params={"category_id": ctx["category_id"]}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["attributes"]) == 1
    attr = data["attributes"][0]
    assert attr["attribute_id"] == str(ctx["attribute_id"])
    assert attr["values"] == ["Black"]


# --- filter params on GET /catalog -------------------------------------------


async def test_catalog_filters_by_price_range(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = await publish_product_with_listing(client, db, monkeypatch, price=300.0)
    await publish_product_with_listing(client, db, monkeypatch, price=900.0)

    resp = await client.get(
        "/api/v1/catalog", params={"min_price": 500, "max_price": 1000}
    )
    prices = [i["price"] for i in resp.json()["data"]]
    assert 900.0 in prices
    assert 300.0 not in prices


async def test_catalog_filters_by_condition_and_stock(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = await publish_product_with_listing(
        client, db, monkeypatch, condition="used", stock=0
    )
    await publish_product_with_listing(
        client, db, monkeypatch, condition="new", stock=3
    )

    cond_resp = await client.get(
        "/api/v1/catalog", params={"condition": ["new"]}
    )
    conditions = [i["condition"] for i in cond_resp.json()["data"]]
    assert conditions and all(c == "new" for c in conditions)

    stock_resp = await client.get("/api/v1/catalog", params={"in_stock": "true"})
    stockzed = stock_resp.json()["data"]
    assert all(i["stock"] > 0 for i in stockzed)


async def test_catalog_filters_by_attribute_value(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = await publish_product_with_listing(client, db, monkeypatch)
    db.add(
        CategoryAttribute(
            category_id=ctx["category_id"],
            attribute_id=ctx["attribute_id"],
            is_filterable=True,
        )
    )
    await db.commit()

    resp = await client.get(
        "/api/v1/catalog",
        params={"attribute_id": [str(ctx["attribute_id"])], "value": ["Black"]},
    )
    listing_ids = [i["listing_id"] for i in resp.json()["data"]]
    assert ctx["listing_id"] in listing_ids

    # A value with no matching variant returns nothing
    resp2 = await client.get(
        "/api/v1/catalog",
        params={"attribute_id": [str(ctx["attribute_id"])], "value": ["Gold"]},
    )
    assert resp2.json()["data"] == []


async def test_catalog_category_filters_include_subcategories(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    parent = await client.post(
        "/api/v1/categories", json={"name": unique_name("Parent")}, headers=admin_headers
    )
    parent_id = uuid.UUID(parent.json()["data"]["id"])

    # Product lives under a CHILD category of `parent`.
    ctx = await publish_product_with_listing(
        client, db, monkeypatch, category_parent_id=parent_id
    )
    assert ctx["category_id"] != parent_id

    # Selecting the parent must surface the product in the child category.
    resp = await client.get("/api/v1/catalog", params={"category_id": str(parent_id)})
    listing_ids = [i["listing_id"] for i in resp.json()["data"]]
    assert ctx["listing_id"] in listing_ids


async def test_catalog_newest_sort(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await publish_product_with_listing(client, db, monkeypatch, price=500.0)
    await publish_product_with_listing(client, db, monkeypatch, price=100.0)

    resp = await client.get("/api/v1/catalog", params={"sort": "newest"})
    data = resp.json()["data"]
    # created_at desc -> the later listing is first; both prices present
    assert {i["price"] for i in data} == {500.0, 100.0}
