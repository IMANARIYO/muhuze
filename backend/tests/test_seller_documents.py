import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.auth.repository import AccountRepository, AuthorizationRepository


def unique_email() -> str:
    return f"seller-doc-test-{uuid.uuid4().hex}@example.com"


def unique_business_name() -> str:
    return f"Business {uuid.uuid4().hex}"


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


def fake_do_upload_returning():
    calls = []

    def _fake(file_obj, *, folder, public_id, delivery_type):
        calls.append(
            {"folder": folder, "public_id": public_id, "delivery_type": delivery_type}
        )
        return {
            "public_id": public_id,
            "url": f"http://res.cloudinary.com/{public_id}",
            "secure_url": f"https://res.cloudinary.com/{public_id}",
            "format": "jpg",
            "resource_type": "image",
            "type": delivery_type,
            "bytes": 999,
        }

    return _fake, calls


async def create_seller(client: AsyncClient, headers: dict) -> None:
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )


async def test_upload_requires_seller_to_exist(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("p.jpg", b"bytes", "image/jpeg")},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 404


async def test_upload_while_draft_succeeds_and_uses_authenticated_delivery(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    fake, calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)

    response = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("passport.jpg", b"bytes", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["document_type"] == "passport"
    assert "url" in body
    assert calls[0]["folder"] == "seller_verification"
    assert calls[0]["delivery_type"] == "authenticated"


async def test_upload_rejects_disallowed_content_type(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    response = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("virus.exe", b"bytes", "application/x-msdownload")},
        headers=headers,
    )
    assert response.status_code == 400


async def test_upload_while_pending_review_is_409(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    fake, _calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)
    monkeypatch.setattr(storage, "_do_delete", lambda *a, **k: None)

    for doc_type in ("national_id_front", "national_id_back"):
        await client.post(
            "/api/v1/sellers/me/documents",
            data={"document_type": doc_type},
            files={"file": ("id.jpg", b"bytes", "image/jpeg")},
            headers=headers,
        )
    await client.post("/api/v1/sellers/me/submit", headers=headers)

    response = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("passport.jpg", b"bytes", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 409


async def test_reuploading_same_document_type_replaces_and_deletes_old_asset(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    fake, calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)
    deleted = []
    monkeypatch.setattr(
        storage,
        "_do_delete",
        lambda public_id, *, resource_type, delivery_type: deleted.append(public_id),
    )

    first = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("v1.jpg", b"bytes-v1", "image/jpeg")},
        headers=headers,
    )
    first_public_id = calls[0]["public_id"]

    second = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("v2.jpg", b"bytes-v2-longer", "image/jpeg")},
        headers=headers,
    )
    assert second.status_code == 201
    # Same document id, updated content — a replace, not a second row.
    assert second.json()["data"]["id"] == first.json()["data"]["id"]
    assert deleted == [first_public_id]

    list_response = await client.get("/api/v1/sellers/me/documents", headers=headers)
    assert len(list_response.json()["data"]) == 1


async def test_upload_cleans_up_cloudinary_asset_when_db_write_fails(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact edge case the design called out: Cloudinary succeeds,
    then the database write fails — must not leave an orphaned file."""
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    fake, calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)
    deleted = []
    monkeypatch.setattr(
        storage,
        "_do_delete",
        lambda public_id, *, resource_type, delivery_type: deleted.append(public_id),
    )

    from app.modules.sellers.repository import SellerDocumentRepository

    async def failing_create(self, **kwargs):
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(SellerDocumentRepository, "create", failing_create)

    # The shared `client` fixture's ASGITransport re-raises server exceptions
    # by default (see tests/test_exception_handlers.py's dedicated
    # raise_app_exceptions=False client for the "500 JSON envelope" case) —
    # what matters here is that the compensation cleanup still ran.
    with pytest.raises(RuntimeError, match="simulated database failure"):
        await client.post(
            "/api/v1/sellers/me/documents",
            data={"document_type": "passport"},
            files={"file": ("passport.jpg", b"bytes", "image/jpeg")},
            headers=headers,
        )
    assert deleted == [calls[0]["public_id"]]


async def test_list_my_documents(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    fake, _calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)

    await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("p.jpg", b"bytes", "image/jpeg")},
        headers=headers,
    )
    response = await client.get("/api/v1/sellers/me/documents", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


async def test_delete_my_document(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    fake, _calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)
    monkeypatch.setattr(storage, "_do_delete", lambda *a, **k: None)

    upload_response = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("p.jpg", b"bytes", "image/jpeg")},
        headers=headers,
    )
    document_id = upload_response.json()["data"]["id"]

    delete_response = await client.delete(
        f"/api/v1/sellers/me/documents/{document_id}", headers=headers
    )
    assert delete_response.status_code == 200

    list_response = await client.get("/api/v1/sellers/me/documents", headers=headers)
    assert list_response.json()["data"] == []


async def test_delete_unknown_document_is_404(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await create_seller(client, headers)

    response = await client.delete(
        f"/api/v1/sellers/me/documents/{uuid.uuid4()}", headers=headers
    )
    assert response.status_code == 404


async def test_delete_someone_elses_document_is_404(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, tokens_a = await register_and_login(client)
    headers_a = auth_headers(tokens_a)
    await create_seller(client, headers_a)

    fake, _calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)

    upload_response = await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("p.jpg", b"bytes", "image/jpeg")},
        headers=headers_a,
    )
    document_id = upload_response.json()["data"]["id"]

    _, tokens_b = await register_and_login(client)
    headers_b = auth_headers(tokens_b)
    await create_seller(client, headers_b)

    response = await client.delete(
        f"/api/v1/sellers/me/documents/{document_id}", headers=headers_b
    )
    assert response.status_code == 404


async def test_admin_can_list_a_sellers_documents(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_tokens = await make_admin(client, db)
    _, seller_tokens = await register_and_login(client)
    seller_headers = auth_headers(seller_tokens)
    await create_seller(client, seller_headers)

    fake, _calls = fake_do_upload_returning()
    monkeypatch.setattr(storage, "_do_upload", fake)

    await client.post(
        "/api/v1/sellers/me/documents",
        data={"document_type": "passport"},
        files={"file": ("p.jpg", b"bytes", "image/jpeg")},
        headers=seller_headers,
    )
    seller_id = (await client.get("/api/v1/sellers/me", headers=seller_headers)).json()[
        "data"
    ]["id"]

    response = await client.get(
        f"/api/v1/sellers/{seller_id}/documents", headers=auth_headers(admin_tokens)
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


async def test_non_admin_cannot_list_another_sellers_documents(
    client: AsyncClient,
) -> None:
    _, tokens = await register_and_login(client)
    response = await client.get(
        f"/api/v1/sellers/{uuid.uuid4()}/documents", headers=auth_headers(tokens)
    )
    assert response.status_code == 403
