import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.auth.repository import AccountRepository, AuthorizationRepository


def unique_email() -> str:
    return f"product-test-{uuid.uuid4().hex}@example.com"


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


async def create_category(client: AsyncClient, headers: dict) -> str:
    response = await client.post(
        "/api/v1/categories", json={"name": unique_name("Category")}, headers=headers
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


async def create_brand(client: AsyncClient, headers: dict) -> str:
    response = await client.post(
        "/api/v1/brands", json={"name": unique_name("Brand")}, headers=headers
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


async def create_attribute(client: AsyncClient, headers: dict) -> str:
    response = await client.post(
        "/api/v1/attributes", json={"name": unique_name("Attr")}, headers=headers
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


async def create_product(
    client: AsyncClient, headers: dict, *, category_id: str, brand_id: str | None = None
) -> str:
    response = await client.post(
        "/api/v1/products",
        json={
            "category_id": category_id,
            "brand_id": brand_id,
            "name": unique_name("Product"),
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


async def make_active_seller(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> dict:
    """Registers a fresh account, becomes a seller, uploads the required
    identity documents, submits for review, and has a fresh admin approve
    it. Returns the seller's own auth tokens."""
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
    assert approved.json()["data"]["status"] == "active"
    return tokens


# --- brands ------------------------------------------------------------------


async def test_create_brand_requires_admin(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.post(
        "/api/v1/brands", json={"name": unique_name()}, headers=auth_headers(tokens)
    )
    assert response.status_code == 403


async def test_admin_creates_brand(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    name = unique_name("Samsung")
    response = await client.post(
        "/api/v1/brands", json={"name": name}, headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    assert response.json()["data"]["name"] == name
    assert response.json()["data"]["status"] == "active"


async def test_duplicate_brand_name_is_409(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    name = unique_name("Nike")
    first = await client.post("/api/v1/brands", json={"name": name}, headers=headers)
    second = await client.post("/api/v1/brands", json={"name": name}, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 409


async def test_get_unknown_brand_is_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/brands/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_admin_updates_brand(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    brand_id = await create_brand(client, headers)

    response = await client.patch(
        f"/api/v1/brands/{brand_id}",
        json={"name": "Renamed Brand", "status": "inactive"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Renamed Brand"
    assert response.json()["data"]["status"] == "inactive"


# --- attributes ----------------------------------------------------------


async def test_create_attribute_requires_admin(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.post(
        "/api/v1/attributes", json={"name": "Color"}, headers=auth_headers(tokens)
    )
    assert response.status_code == 403


async def test_admin_creates_attribute(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    response = await client.post(
        "/api/v1/attributes",
        json={"name": "Color", "input_type": "select"},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 201
    assert response.json()["data"]["slug"] == "color"


async def test_admin_updates_attribute(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    attribute_id = await create_attribute(client, headers)

    response = await client.patch(
        f"/api/v1/attributes/{attribute_id}",
        json={
            "name": "Storage",
            "input_type": "number",
            "unit": "GB",
            "status": "active",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["unit"] == "GB"


# --- products: create/edit --------------------------------------------------


async def test_create_product_requires_admin(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    category_id = await create_category(client, auth_headers(tokens))
    _, buyer_tokens = await register_and_login(client)

    response = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(buyer_tokens),
    )
    assert response.status_code == 403


async def test_create_product_defaults_to_draft(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)

    response = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "draft"


async def test_create_product_with_unknown_category_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    response = await client.post(
        "/api/v1/products",
        json={"category_id": str(uuid.uuid4()), "name": unique_name()},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 404


async def test_create_product_with_unknown_brand_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)

    response = await client.post(
        "/api/v1/products",
        json={
            "category_id": category_id,
            "brand_id": str(uuid.uuid4()),
            "name": unique_name(),
        },
        headers=headers,
    )
    assert response.status_code == 404


async def test_update_active_product_is_409(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    await client.post(f"/api/v1/products/{product_id}/submit", headers=headers)
    await client.post(f"/api/v1/products/{product_id}/approve", headers=headers)

    response = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"category_id": category_id, "name": "New name"},
        headers=headers,
    )
    assert response.status_code == 409


# --- products: lifecycle -----------------------------------------------


async def test_full_lifecycle_draft_to_active(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    submitted = await client.post(
        f"/api/v1/products/{product_id}/submit", headers=headers
    )
    assert submitted.json()["data"]["status"] == "pending_review"

    approved = await client.post(
        f"/api/v1/products/{product_id}/approve", headers=headers
    )
    assert approved.json()["data"]["status"] == "active"


async def test_reject_sets_reason_and_allows_edit(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)
    await client.post(f"/api/v1/products/{product_id}/submit", headers=headers)

    rejected = await client.post(
        f"/api/v1/products/{product_id}/reject",
        json={"reason": "Duplicate of existing product"},
        headers=headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "rejected"
    assert (
        rejected.json()["data"]["rejection_reason"] == "Duplicate of existing product"
    )

    edited = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"category_id": category_id, "name": "Fixed name"},
        headers=headers,
    )
    assert edited.status_code == 200


async def test_approve_requires_pending_review(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    response = await client.post(
        f"/api/v1/products/{product_id}/approve", headers=headers
    )
    assert response.status_code == 409


async def test_archive_requires_active(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    response = await client.post(
        f"/api/v1/products/{product_id}/archive", headers=headers
    )
    assert response.status_code == 409


async def test_list_products_filters_by_category(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_a = await create_category(client, headers)
    category_b = await create_category(client, headers)
    product_a = await create_product(client, headers, category_id=category_a)
    await create_product(client, headers, category_id=category_b)

    response = await client.get("/api/v1/products", params={"category_id": category_a})
    ids = [p["id"] for p in response.json()["data"]]
    assert ids == [product_a]


# --- variants ----------------------------------------------------------------


async def test_create_variant_with_attribute_values(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)
    color_id = await create_attribute(client, headers)

    response = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={
            "sku_code": "SKU-1",
            "attribute_values": [{"attribute_id": color_id, "value": "Black"}],
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["sku_code"] == "SKU-1"
    assert body["attribute_values"] == [{"attribute_id": color_id, "value": "Black"}]


async def test_duplicate_attribute_in_same_request_is_422(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)
    color_id = await create_attribute(client, headers)

    response = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={
            "attribute_values": [
                {"attribute_id": color_id, "value": "Black"},
                {"attribute_id": color_id, "value": "Blue"},
            ]
        },
        headers=headers,
    )
    assert response.status_code == 422


async def test_duplicate_combination_across_variants_is_422(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)
    color_id = await create_attribute(client, headers)

    payload = {"attribute_values": [{"attribute_id": color_id, "value": "Black"}]}
    first = await client.post(
        f"/api/v1/products/{product_id}/variants", json=payload, headers=headers
    )
    second = await client.post(
        f"/api/v1/products/{product_id}/variants", json=payload, headers=headers
    )
    assert first.status_code == 201
    assert second.status_code == 422


async def test_create_variant_with_unknown_attribute_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    response = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={
            "attribute_values": [{"attribute_id": str(uuid.uuid4()), "value": "Black"}]
        },
        headers=headers,
    )
    assert response.status_code == 404


async def test_create_variant_for_unknown_product_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    response = await client.post(
        f"/api/v1/products/{uuid.uuid4()}/variants",
        json={"attribute_values": []},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 404


async def test_list_and_update_variant(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)
    created = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"sku_code": "SKU-1", "attribute_values": []},
        headers=headers,
    )
    variant_id = created.json()["data"]["id"]

    listed = await client.get(
        f"/api/v1/products/{product_id}/variants", headers=headers
    )
    assert listed.status_code == 200
    assert [v["id"] for v in listed.json()["data"]] == [variant_id]

    updated = await client.patch(
        f"/api/v1/products/{product_id}/variants/{variant_id}",
        json={"sku_code": "SKU-1-NEW", "status": "inactive"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["sku_code"] == "SKU-1-NEW"
    assert updated.json()["data"]["status"] == "inactive"


# --- images ------------------------------------------------------------------


async def test_upload_image_requires_admin(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    _, buyer_tokens = await register_and_login(client)
    response = await client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("photo.jpg", b"fake-bytes", "image/jpeg")},
        headers=auth_headers(buyer_tokens),
    )
    assert response.status_code == 403


async def test_upload_first_image_is_primary_by_default(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_upload(monkeypatch)
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    response = await client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("photo.jpg", b"fake-bytes", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["is_primary"] is True
    assert body["url"].startswith("https://cdn/")


async def test_list_and_delete_image(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_upload(monkeypatch)
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    uploaded = await client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("photo.jpg", b"fake-bytes", "image/jpeg")},
        headers=headers,
    )
    image_id = uploaded.json()["data"]["id"]

    listed = await client.get(f"/api/v1/products/{product_id}/images", headers=headers)
    assert [i["id"] for i in listed.json()["data"]] == [image_id]

    deleted = await client.delete(
        f"/api/v1/products/{product_id}/images/{image_id}", headers=headers
    )
    assert deleted.status_code == 200

    listed_after = await client.get(
        f"/api/v1/products/{product_id}/images", headers=headers
    )
    assert listed_after.json()["data"] == []


async def test_delete_unknown_image_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    product_id = await create_product(client, headers, category_id=category_id)

    response = await client.delete(
        f"/api/v1/products/{product_id}/images/{uuid.uuid4()}", headers=headers
    )
    assert response.status_code == 404


# --- seller-initiated product requests ----------------------------------


async def test_non_seller_non_admin_cannot_create_product(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    category_id = await create_category(client, auth_headers(tokens))
    _, buyer_tokens = await register_and_login(client)

    response = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(buyer_tokens),
    )
    assert response.status_code == 403


async def test_active_seller_can_create_product_request(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    category_id = await create_category(client, auth_headers(admin_tokens))
    seller_tokens = await make_active_seller(client, db, monkeypatch)

    response = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(seller_tokens),
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["status"] == "draft"
    assert body["created_by_seller_id"] is not None


async def test_seller_can_update_and_submit_own_product(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    category_id = await create_category(client, admin_headers)
    seller_tokens = await make_active_seller(client, db, monkeypatch)
    seller_headers = auth_headers(seller_tokens)

    created = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=seller_headers,
    )
    product_id = created.json()["data"]["id"]

    updated = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"category_id": category_id, "name": "Renamed by seller"},
        headers=seller_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Renamed by seller"

    submitted = await client.post(
        f"/api/v1/products/{product_id}/submit", headers=seller_headers
    )
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "pending_review"

    approved = await client.post(
        f"/api/v1/products/{product_id}/approve", headers=admin_headers
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "active"


async def test_seller_cannot_touch_another_sellers_product(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    category_id = await create_category(client, auth_headers(admin_tokens))
    seller_a_tokens = await make_active_seller(client, db, monkeypatch)
    seller_b_tokens = await make_active_seller(client, db, monkeypatch)

    created = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(seller_a_tokens),
    )
    product_id = created.json()["data"]["id"]

    update_response = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"category_id": category_id, "name": "Hijacked"},
        headers=auth_headers(seller_b_tokens),
    )
    assert update_response.status_code == 403

    submit_response = await client.post(
        f"/api/v1/products/{product_id}/submit", headers=auth_headers(seller_b_tokens)
    )
    assert submit_response.status_code == 403


async def test_only_creator_can_add_variant_before_approval(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    category_id = await create_category(client, auth_headers(admin_tokens))
    seller_a_tokens = await make_active_seller(client, db, monkeypatch)
    seller_b_tokens = await make_active_seller(client, db, monkeypatch)

    created = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(seller_a_tokens),
    )
    product_id = created.json()["data"]["id"]

    other_seller_attempt = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"attribute_values": []},
        headers=auth_headers(seller_b_tokens),
    )
    assert other_seller_attempt.status_code == 403

    own_attempt = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"attribute_values": []},
        headers=auth_headers(seller_a_tokens),
    )
    assert own_attempt.status_code == 201


async def test_any_active_seller_can_add_variant_once_active(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    category_id = await create_category(client, admin_headers)
    seller_a_tokens = await make_active_seller(client, db, monkeypatch)
    seller_b_tokens = await make_active_seller(client, db, monkeypatch)

    created = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(seller_a_tokens),
    )
    product_id = created.json()["data"]["id"]
    await client.post(
        f"/api/v1/products/{product_id}/submit", headers=auth_headers(seller_a_tokens)
    )
    await client.post(f"/api/v1/products/{product_id}/approve", headers=admin_headers)

    response = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"attribute_values": []},
        headers=auth_headers(seller_b_tokens),
    )
    assert response.status_code == 201


async def test_list_my_products_returns_only_own(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    category_id = await create_category(client, auth_headers(admin_tokens))
    seller_a_tokens = await make_active_seller(client, db, monkeypatch)
    seller_b_tokens = await make_active_seller(client, db, monkeypatch)

    mine = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(seller_a_tokens),
    )
    mine_id = mine.json()["data"]["id"]
    await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name()},
        headers=auth_headers(seller_b_tokens),
    )

    response = await client.get(
        "/api/v1/products/mine", headers=auth_headers(seller_a_tokens)
    )
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()["data"]]
    assert ids == [mine_id]


async def test_search_filters_products_by_name(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    category_id = await create_category(client, headers)
    unique_word = uuid.uuid4().hex
    await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": f"Samsung {unique_word}"},
        headers=headers,
    )
    await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name("Unrelated")},
        headers=headers,
    )

    response = await client.get("/api/v1/products", params={"search": unique_word})
    results = response.json()["data"]
    assert len(results) == 1
    assert unique_word in results[0]["name"]
