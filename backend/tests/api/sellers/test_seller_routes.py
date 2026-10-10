"""Seller applications and their review through the HTTP API, against a
real PostgreSQL database. Uploaded files go to an in-memory fake storage."""

import uuid

import pytest
from httpx import AsyncClient, Response

from app.infrastructure.storage.file_storage import UnconfiguredFileStorage
from app.modules.authorization.authorization_service import AuthorizationService
from app.modules.sellers.seller_constants import DOCUMENT_MAX_BYTES
from app.modules.sellers.seller_exceptions import SellerNotActiveError
from app.modules.sellers.seller_service import SellerService

API = "/api/v1"
SELLERS = f"{API}/sellers"
ME = f"{SELLERS}/me"

JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20
PNG = b"\x89PNG\r\n\x1a\n" + b"png-bytes" * 20
PDF = b"%PDF-1.7\n" + b"pdf-bytes" * 20


def application(**overrides: object) -> dict[str, object]:
    return {
        "business_name": "Amina Fashion",
        "business_description": "Clothes and shoes",
        "business_phone": "+250788123456",
        "identity_document_type": "national_id",
        "identity_document_number": "1199080012345678",
        "location": {"province": "Kigali", "district": "Gasabo", "sector": "Remera"},
        **overrides,
    }


@pytest.fixture
def apply(db_client: AsyncClient):
    async def _apply(actor, **overrides: object) -> Response:
        return await db_client.post(ME, json=application(**overrides), headers=actor.headers)

    return _apply


@pytest.fixture
def upload(db_client: AsyncClient):
    async def _upload(
        actor, document_type: str, content: bytes = JPEG, filename: str = "scan.jpg"
    ) -> Response:
        return await db_client.put(
            f"{ME}/documents/{document_type}",
            files={"file": (filename, content)},
            headers=actor.headers,
        )

    return _upload


@pytest.fixture
def submitted_seller(db_client: AsyncClient, apply, upload):
    """An application with its required documents, sent for review. Returns the seller id."""

    async def _submitted_seller(actor, **overrides: object) -> str:
        assert (await apply(actor, **overrides)).status_code == 201
        assert (await upload(actor, "identity_front")).status_code == 200
        assert (await upload(actor, "identity_back")).status_code == 200
        response = await db_client.post(f"{ME}/submit", headers=actor.headers)
        assert response.status_code == 200, response.text
        return response.json()["data"]["id"]

    return _submitted_seller


@pytest.fixture
def active_seller(db_client: AsyncClient, submitted_seller, admin):
    async def _active_seller(actor, **overrides: object) -> str:
        seller_id = await submitted_seller(actor, **overrides)
        response = await db_client.post(f"{SELLERS}/{seller_id}/approve", headers=admin.headers)
        assert response.status_code == 200, response.text
        return seller_id

    return _active_seller


# ── Applying ─────────────────────────────────────────────────────────────


async def test_apply_starts_a_draft_application(db_client: AsyncClient, user, apply) -> None:
    response = await apply(user)

    assert response.status_code == 201
    seller = response.json()["data"]
    assert seller["account_id"] == user.id
    assert seller["business_name"] == "Amina Fashion"
    assert seller["status"] == "draft"
    assert seller["status_reason"] is None
    assert seller["submitted_at"] is None
    assert seller["documents"] == []
    assert seller["missing_documents"] == ["identity_front", "identity_back"]
    assert seller["location"] == {
        "country_code": "RW",
        "province": "Kigali",
        "district": "Gasabo",
        "sector": "Remera",
        "cell": None,
        "village": None,
        "street_address": None,
        "latitude": None,
        "longitude": None,
        "accuracy_m": None,
        "source": None,
    }

    mine = await db_client.get(ME, headers=user.headers)
    assert mine.json()["data"] == seller
    # Applying does not make the account a seller yet.
    roles = (await db_client.get(f"{API}/authorization/me", headers=user.headers)).json()["data"]
    assert roles["roles"] == ["buyer"]


async def test_apply_keeps_a_detected_location(db_client: AsyncClient, user, apply) -> None:
    location = {
        "province": "Kigali",
        "district": "Gasabo",
        "sector": "Remera",
        "cell": "Rukiri I",
        "street_address": "KG 11 Ave, near the stadium",
        "latitude": -1.9535713,
        "longitude": 30.1127351,
        "accuracy_m": 12,
        "source": "device",
    }

    response = await apply(user, location=location)

    assert response.status_code == 201
    stored = response.json()["data"]["location"]
    assert stored["latitude"] == -1.953571  # six decimal places
    assert stored["longitude"] == 30.112735
    assert stored["accuracy_m"] == 12
    assert stored["source"] == "device"
    assert stored["cell"] == "Rukiri I"


async def test_an_account_has_one_application_and_business_names_are_unique(
    db_client: AsyncClient, user, admin, apply
) -> None:
    assert (await apply(user)).status_code == 201

    again = await apply(user, business_name="Another Shop")
    same_name = await apply(admin, business_name="AMINA fashion")

    assert again.status_code == 409
    assert again.json()["message"] == "You already have a seller application"
    assert same_name.status_code == 409
    assert same_name.json()["message"] == "This business name is already taken"


ADDRESS = {"province": "Kigali", "district": "Gasabo", "sector": "Remera"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"business_name": "A"},
        {"business_phone": "0788123456"},
        {"identity_document_type": "library_card"},
        {"identity_document_number": ""},
        {"location": {"province": "Kigali", "district": "Gasabo"}},  # sector missing
        {"location": {**ADDRESS, "latitude": -1.95}},  # longitude missing
        {"location": {**ADDRESS, "latitude": -1.95, "longitude": 30.11}},  # source missing
        {"location": {**ADDRESS, "latitude": 95, "longitude": 30.11, "source": "manual"}},
        {"location": {**ADDRESS, "source": "device"}},  # source without coordinates
    ],
)
async def test_apply_validates_its_input(user, apply, overrides: dict[str, object]) -> None:
    response = await apply(user, **overrides)
    assert response.status_code == 422


async def test_own_application_needs_a_login_and_must_exist(db_client: AsyncClient, user) -> None:
    assert (await db_client.post(ME, json=application())).status_code == 401
    assert (await db_client.get(ME)).status_code == 401

    missing = await db_client.get(ME, headers=user.headers)
    assert missing.status_code == 404
    assert missing.json()["message"] == "You have not applied to become a seller"


# ── Editing a draft ──────────────────────────────────────────────────────


async def test_update_changes_only_what_is_sent(db_client: AsyncClient, user, apply) -> None:
    await apply(user)

    response = await db_client.patch(
        ME,
        json={
            "business_name": "Amina Boutique",
            "business_description": None,
            "location": {
                "province": "Southern",
                "district": "Huye",
                "sector": "Ngoma",
                "latitude": -2.6,
                "longitude": 29.74,
                "source": "manual",
            },
        },
        headers=user.headers,
    )

    assert response.status_code == 200
    seller = response.json()["data"]
    assert seller["business_name"] == "Amina Boutique"
    assert seller["business_description"] is None
    assert seller["business_phone"] == "+250788123456"  # not sent, unchanged
    assert seller["location"]["district"] == "Huye"
    assert seller["location"]["source"] == "manual"

    not_nullable = await db_client.patch(ME, json={"business_name": None}, headers=user.headers)
    assert not_nullable.status_code == 422


async def test_update_cannot_take_another_sellers_name(
    db_client: AsyncClient, user, admin, apply
) -> None:
    await apply(user)
    await apply(admin, business_name="Kigali Electronics")

    response = await db_client.patch(
        ME, json={"business_name": "kigali electronics"}, headers=user.headers
    )
    own_name = await db_client.patch(
        ME, json={"business_name": "AMINA FASHION"}, headers=user.headers
    )

    assert response.status_code == 409
    assert own_name.status_code == 200  # re-casing your own name is fine


# ── Documents ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("content", "mime_type"),
    [(JPEG, "image/jpeg"), (PNG, "image/png"), (PDF, "application/pdf")],
)
async def test_upload_stores_the_document_privately(
    user, apply, upload, file_storage, content: bytes, mime_type: str
) -> None:
    await apply(user)

    # The client claims a .jpg whatever the content: the type comes from the bytes.
    response = await upload(user, "identity_front", content, "My ID.jpg")

    assert response.status_code == 200
    seller = response.json()["data"]
    (document,) = seller["documents"]
    assert document["document_type"] == "identity_front"
    assert document["original_filename"] == "My ID.jpg"
    assert document["mime_type"] == mime_type
    assert document["file_size"] == len(content)
    assert seller["missing_documents"] == ["identity_back"]
    # No link and no storage id is ever returned with the application.
    assert "url" not in document
    assert "storage" not in response.text
    assert list(file_storage.files.values()) == [content]


async def test_upload_rejects_wrong_types_and_oversized_files(
    db_client: AsyncClient, user, apply, upload, file_storage
) -> None:
    await apply(user)

    text_file = await upload(user, "identity_front", b"just some text", "id.jpg")
    too_large = await upload(user, "identity_front", JPEG + b"0" * DOCUMENT_MAX_BYTES)
    unknown_type = await upload(user, "selfie")

    assert text_file.status_code == 422
    assert text_file.json()["message"] == "The file must be a JPEG, PNG, or PDF"
    assert too_large.status_code == 422
    assert too_large.json()["message"] == "The file is larger than 5 MB"
    assert unknown_type.status_code == 422
    assert file_storage.files == {}


async def test_uploading_again_replaces_the_file(
    db_client: AsyncClient, user, apply, upload, file_storage
) -> None:
    await apply(user)
    await upload(user, "identity_front", JPEG)

    response = await upload(user, "identity_front", PNG, "better-scan.png")

    (document,) = response.json()["data"]["documents"]
    assert document["mime_type"] == "image/png"
    assert document["original_filename"] == "better-scan.png"
    assert list(file_storage.files.values()) == [PNG]  # the old file was removed


async def test_delete_document(db_client: AsyncClient, user, apply, upload, file_storage) -> None:
    await apply(user)
    await upload(user, "identity_front")

    deleted = await db_client.delete(f"{ME}/documents/identity_front", headers=user.headers)
    again = await db_client.delete(f"{ME}/documents/identity_front", headers=user.headers)

    assert deleted.status_code == 200
    assert deleted.json()["data"]["documents"] == []
    assert again.status_code == 404
    assert file_storage.files == {}


async def test_owner_gets_a_short_lived_link_to_their_document(
    db_client: AsyncClient, user, apply, upload
) -> None:
    await apply(user)
    await upload(user, "identity_front")

    response = await db_client.get(f"{ME}/documents/identity_front/url", headers=user.headers)
    missing = await db_client.get(f"{ME}/documents/identity_back/url", headers=user.headers)

    assert response.status_code == 200
    link = response.json()["data"]
    assert link["url"].startswith("https://files.example.test/muhuze/sellers/")
    assert link["expires_in"] == 300
    assert missing.status_code == 404


async def test_upload_reports_unavailable_storage(app, user, apply, upload) -> None:
    await apply(user)
    app.state.file_storage = UnconfiguredFileStorage()  # no storage credentials configured

    response = await upload(user, "identity_front")

    assert response.status_code == 503
    assert response.json()["success"] is False


# ── Submitting ───────────────────────────────────────────────────────────


async def test_submit_needs_the_required_documents(
    db_client: AsyncClient, user, apply, upload
) -> None:
    await apply(user)
    await upload(user, "identity_front")
    await upload(user, "tin_certificate", PDF)  # optional documents don't count

    blocked = await db_client.post(f"{ME}/submit", headers=user.headers)

    assert blocked.status_code == 422
    assert blocked.json()["message"] == "Upload these documents before submitting: identity_back"

    await upload(user, "identity_back")
    submitted = await db_client.post(f"{ME}/submit", headers=user.headers)

    assert submitted.status_code == 200
    seller = submitted.json()["data"]
    assert seller["status"] == "pending_review"
    assert seller["submitted_at"] is not None
    assert seller["missing_documents"] == []


async def test_a_passport_needs_only_one_side(db_client: AsyncClient, user, apply, upload) -> None:
    created = await apply(user, identity_document_type="passport")
    assert created.json()["data"]["missing_documents"] == ["identity_front"]
    await upload(user, "identity_front")

    submitted = await db_client.post(f"{ME}/submit", headers=user.headers)

    assert submitted.status_code == 200


async def test_an_application_under_review_cannot_be_changed(
    db_client: AsyncClient, user, submitted_seller, upload
) -> None:
    await submitted_seller(user)

    edited = await db_client.patch(ME, json={"business_name": "New Name"}, headers=user.headers)
    uploaded = await upload(user, "identity_front", PNG)
    removed = await db_client.delete(f"{ME}/documents/identity_front", headers=user.headers)
    resubmitted = await db_client.post(f"{ME}/submit", headers=user.headers)

    for response in (edited, uploaded, removed, resubmitted):
        assert response.status_code == 409
    assert edited.json()["message"] == (
        "The application can only be changed while it is a draft or after a rejection"
    )


# ── Staff: access and reading ────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", ""),
        ("GET", "/{id}"),
        ("GET", "/{id}/documents/identity_front/url"),
        ("GET", "/{id}/history"),
        ("POST", "/{id}/approve"),
        ("POST", "/{id}/reject"),
        ("POST", "/{id}/suspend"),
        ("POST", "/{id}/reinstate"),
    ],
)
async def test_staff_endpoints_are_closed_to_ordinary_accounts(
    db_client: AsyncClient, user, submitted_seller, method: str, path: str
) -> None:
    # Even for the seller's OWN record: staff endpoints need the permission.
    seller_id = await submitted_seller(user)
    url = SELLERS + path.replace("{id}", seller_id)
    body = {"json": {"reason": "Because I say so"}} if method == "POST" else {}

    anonymous = await db_client.request(method, url, **body)
    ordinary = await db_client.request(method, url, headers=user.headers, **body)

    assert anonymous.status_code == 401
    assert ordinary.status_code == 403


async def test_staff_list_filters_searches_and_sorts(
    db_client: AsyncClient, admin, sign_up, apply, submitted_seller
) -> None:
    first, second, third = [await sign_up(f"seller{n}@example.com") for n in range(3)]
    await submitted_seller(first, business_name="Zebra Crafts")
    await apply(second, business_name="100% Cotton")
    await apply(third, business_name="apple market")

    async def names(**params: object) -> list[str]:
        response = await db_client.get(SELLERS, params=params, headers=admin.headers)
        assert response.status_code == 200, response.text
        return [seller["business_name"] for seller in response.json()["data"]["items"]]

    assert await names(sort="business_name") == ["100% Cotton", "apple market", "Zebra Crafts"]
    assert await names(sort="-business_name") == ["Zebra Crafts", "apple market", "100% Cotton"]
    assert await names(status="pending_review") == ["Zebra Crafts"]
    assert await names(status="draft", sort="business_name") == ["100% Cotton", "apple market"]
    assert await names(q="APPLE") == ["apple market"]  # case-insensitive
    assert await names(q="%") == ["100% Cotton"]  # % is a literal character, not a wildcard
    # The only submitted application comes first; unsubmitted ones sort last.
    assert (await names(sort="-submitted_at"))[0] == "Zebra Crafts"

    page = await db_client.get(
        SELLERS, params={"sort": "business_name", "page": 2, "page_size": 2}, headers=admin.headers
    )
    data = page.json()["data"]
    assert [seller["business_name"] for seller in data["items"]] == ["Zebra Crafts"]
    assert (data["total"], data["total_pages"]) == (3, 2)
    assert "identity_document_number" not in data["items"][0]  # the list carries no identity data

    bad_sort = await db_client.get(SELLERS, params={"sort": "password"}, headers=admin.headers)
    assert bad_sort.status_code == 422


async def test_staff_can_read_an_application_and_its_documents(
    db_client: AsyncClient, admin, user, submitted_seller
) -> None:
    seller_id = await submitted_seller(user)

    detail = await db_client.get(f"{SELLERS}/{seller_id}", headers=admin.headers)
    link = await db_client.get(
        f"{SELLERS}/{seller_id}/documents/identity_front/url", headers=admin.headers
    )
    unknown = await db_client.get(f"{SELLERS}/{uuid.uuid4()}", headers=admin.headers)

    assert detail.status_code == 200
    seller = detail.json()["data"]
    assert seller["identity_document_number"] == "1199080012345678"
    assert [d["document_type"] for d in seller["documents"]] == ["identity_back", "identity_front"]
    assert link.json()["data"]["url"].startswith("https://files.example.test/")
    assert unknown.status_code == 404
    assert unknown.json()["message"] == "Seller not found"


# ── Staff: decisions ─────────────────────────────────────────────────────


async def test_approve_makes_the_seller_active_and_grants_the_seller_role(
    db_client: AsyncClient, admin, user, submitted_seller
) -> None:
    seller_id = await submitted_seller(user)

    response = await db_client.post(f"{SELLERS}/{seller_id}/approve", headers=admin.headers)

    assert response.status_code == 200
    seller = response.json()["data"]
    assert seller["status"] == "active"
    assert seller["reviewed_by_account_id"] == admin.id
    assert seller["reviewed_at"] is not None
    assert seller["approved_at"] is not None
    access = (await db_client.get(f"{API}/authorization/me", headers=user.headers)).json()["data"]
    assert access["roles"] == ["buyer", "seller"]

    again = await db_client.post(f"{SELLERS}/{seller_id}/approve", headers=admin.headers)
    assert again.status_code == 409
    assert again.json()["message"] == (
        "Only an application waiting for review can be approved or rejected"
    )

    history = await db_client.get(f"{SELLERS}/{seller_id}/history", headers=admin.headers)
    entries = history.json()["data"]["items"]
    assert {(entry["from_status"], entry["to_status"]) for entry in entries} == {
        (None, "draft"),
        ("draft", "pending_review"),
        ("pending_review", "active"),
    }
    approval = next(entry for entry in entries if entry["to_status"] == "active")
    assert approval["changed_by_account_id"] == admin.id


async def test_a_rejected_application_can_be_fixed_and_sent_again(
    db_client: AsyncClient, admin, user, submitted_seller, upload
) -> None:
    seller_id = await submitted_seller(user)

    rejected = await db_client.post(
        f"{SELLERS}/{seller_id}/reject",
        json={"reason": "The ID photo is too blurry to read"},
        headers=admin.headers,
    )

    assert rejected.status_code == 200
    mine = (await db_client.get(ME, headers=user.headers)).json()["data"]
    assert mine["status"] == "rejected"
    assert mine["status_reason"] == "The ID photo is too blurry to read"
    roles = (await db_client.get(f"{API}/authorization/me", headers=user.headers)).json()["data"]
    assert roles["roles"] == ["buyer"]  # no seller role for a rejected application

    # The seller fixes the problem on the SAME application and sends it again.
    assert (await upload(user, "identity_front", PNG, "sharp.png")).status_code == 200
    resubmitted = await db_client.post(f"{ME}/submit", headers=user.headers)
    assert resubmitted.json()["data"]["id"] == seller_id
    assert resubmitted.json()["data"]["status"] == "pending_review"
    assert resubmitted.json()["data"]["status_reason"] is None  # the old reason is gone

    approved = await db_client.post(f"{SELLERS}/{seller_id}/approve", headers=admin.headers)
    assert approved.json()["data"]["status"] == "active"


async def test_reject_and_suspend_need_a_real_reason(
    db_client: AsyncClient, admin, user, submitted_seller
) -> None:
    seller_id = await submitted_seller(user)

    for body in ({}, {"reason": ""}, {"reason": "no"}, {"reason": "x" * 501}):
        response = await db_client.post(
            f"{SELLERS}/{seller_id}/reject", json=body, headers=admin.headers
        )
        assert response.status_code == 422


async def test_staff_cannot_review_their_own_application(
    db_client: AsyncClient, admin, submitted_seller
) -> None:
    seller_id = await submitted_seller(admin)

    approved = await db_client.post(f"{SELLERS}/{seller_id}/approve", headers=admin.headers)
    rejected = await db_client.post(
        f"{SELLERS}/{seller_id}/reject", json={"reason": "Testing myself"}, headers=admin.headers
    )

    assert approved.status_code == rejected.status_code == 422
    assert approved.json()["message"] == "You cannot review your own seller application"


async def test_only_a_waiting_application_can_be_reviewed(
    db_client: AsyncClient, admin, user, apply
) -> None:
    seller_id = (await apply(user)).json()["data"]["id"]  # still a draft

    approved = await db_client.post(f"{SELLERS}/{seller_id}/approve", headers=admin.headers)

    assert approved.status_code == 409


async def test_suspend_blocks_selling_but_not_the_account(
    db_client: AsyncClient, admin, user, active_seller
) -> None:
    seller_id = await active_seller(user)

    suspended = await db_client.post(
        f"{SELLERS}/{seller_id}/suspend",
        json={"reason": "Repeated complaints from buyers"},
        headers=admin.headers,
    )

    assert suspended.status_code == 200
    assert suspended.json()["data"]["status"] == "suspended"
    mine = (await db_client.get(ME, headers=user.headers)).json()["data"]
    assert mine["status_reason"] == "Repeated complaints from buyers"
    # The account itself still works: it can log in, and it is still a buyer.
    assert (await db_client.get(f"{API}/auth/me", headers=user.headers)).status_code == 200
    # A suspended seller cannot lift the suspension themselves.
    assert (await db_client.post(f"{ME}/reactivate", headers=user.headers)).status_code == 409
    assert (await db_client.post(f"{ME}/deactivate", headers=user.headers)).status_code == 409

    twice = await db_client.post(
        f"{SELLERS}/{seller_id}/suspend", json={"reason": "And again"}, headers=admin.headers
    )
    assert twice.status_code == 409

    reinstated = await db_client.post(f"{SELLERS}/{seller_id}/reinstate", headers=admin.headers)
    assert reinstated.json()["data"]["status"] == "active"
    assert reinstated.json()["data"]["status_reason"] is None
    assert reinstated.json()["data"]["approved_at"] is not None


async def test_a_seller_can_close_and_reopen_their_own_shop(
    db_client: AsyncClient, user, apply, active_seller
) -> None:
    await active_seller(user)

    closed = await db_client.post(f"{ME}/deactivate", headers=user.headers)
    closed_again = await db_client.post(f"{ME}/deactivate", headers=user.headers)
    reopened = await db_client.post(f"{ME}/reactivate", headers=user.headers)

    assert closed.json()["data"]["status"] == "deactivated"
    assert closed_again.status_code == 409
    assert reopened.json()["data"]["status"] == "active"


async def test_a_draft_cannot_be_deactivated(db_client: AsyncClient, user, apply) -> None:
    await apply(user)
    assert (await db_client.post(f"{ME}/deactivate", headers=user.headers)).status_code == 409


# ── The gate other features use ──────────────────────────────────────────


async def test_only_an_active_seller_passes_the_selling_gate(
    db_client: AsyncClient,
    admin,
    user,
    sign_up,
    active_seller,
    apply,
    session_factory,
    file_storage,
) -> None:
    applicant = await sign_up("applicant@example.com")
    await apply(applicant, business_name="Not Yet Approved")
    seller_id = await active_seller(user)

    async with session_factory() as session:
        service = SellerService(session, AuthorizationService(session), file_storage)

        seller = await service.get_active_seller(uuid.UUID(user.id))
        assert str(seller.id) == seller_id

        for account_id in (applicant.id, admin.id):  # a draft, and no application at all
            with pytest.raises(SellerNotActiveError):
                await service.get_active_seller(uuid.UUID(account_id))

    await db_client.post(
        f"{SELLERS}/{seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    async with session_factory() as session:
        service = SellerService(session, AuthorizationService(session), file_storage)
        with pytest.raises(SellerNotActiveError):
            await service.get_active_seller(uuid.UUID(user.id))
