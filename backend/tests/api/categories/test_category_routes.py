"""Seller-owned categories through the HTTP API, against a real PostgreSQL
database. Two shops (Amina's and Brian's) check that nothing leaks between them."""

import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"
CATEGORIES = f"{API}/categories"


@pytest.fixture
async def amina(sign_up, open_shop):
    actor = await sign_up("amina@example.com")
    actor.seller_id = await open_shop(actor, "Amina Shop")
    return actor


@pytest.fixture
async def brian(sign_up, open_shop):
    actor = await sign_up("brian@example.com")
    actor.seller_id = await open_shop(actor, "Brian Shop")
    return actor


@pytest.fixture
def create_category(db_client: AsyncClient):
    async def _create_category(actor, name: str = "Phones", **fields: object) -> dict:
        response = await db_client.post(
            CATEGORIES, json={"name": name, **fields}, headers=actor.headers
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _create_category


@pytest.fixture
def add_attribute(db_client: AsyncClient):
    async def _add_attribute(actor, category_id: str, **fields: object) -> dict:
        response = await db_client.post(
            f"{CATEGORIES}/{category_id}/attributes", json=fields, headers=actor.headers
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _add_attribute


def values(attribute: dict) -> list[str]:
    return [option["value"] for option in attribute["options"]]


# ── Who may manage categories ────────────────────────────────────────────


async def test_only_an_active_seller_can_create_categories(
    db_client: AsyncClient, user, admin, amina
) -> None:
    payload = {"json": {"name": "Phones"}}

    anonymous = await db_client.post(CATEGORIES, **payload)
    buyer = await db_client.post(CATEGORIES, headers=user.headers, **payload)
    seller = await db_client.post(CATEGORIES, headers=amina.headers, **payload)

    assert anonymous.status_code == 401
    assert buyer.status_code == 403  # no seller role, so no category.manage permission
    assert seller.status_code == 201

    # Suspended: still holds the seller role and the permission, but may not trade.
    await db_client.post(
        f"{API}/sellers/{amina.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    suspended = await db_client.post(CATEGORIES, json={"name": "Laptops"}, headers=amina.headers)
    assert suspended.status_code == 403
    assert suspended.json()["message"] == "Only an approved, active seller can do this"


# ── Categories ───────────────────────────────────────────────────────────


async def test_create_category(db_client: AsyncClient, amina) -> None:
    response = await db_client.post(
        CATEGORIES,
        json={"name": "  Phones & Tablets ", "description": "Mobile devices", "sort_order": 3},
        headers=amina.headers,
    )

    assert response.status_code == 201
    category = response.json()["data"]
    assert category["seller_id"] == amina.seller_id
    assert category["name"] == "Phones & Tablets"
    assert category["slug"] == "phones-tablets"
    assert category["description"] == "Mobile devices"
    assert category["sort_order"] == 3
    assert category["is_active"] is True
    assert category["hidden_by_staff_at"] is None
    assert category["attributes"] == []

    fetched = await db_client.get(f"{CATEGORIES}/{category['id']}", headers=amina.headers)
    assert fetched.json()["data"] == category


async def test_names_are_unique_within_a_shop_but_not_across_shops(
    db_client: AsyncClient, amina, brian, create_category
) -> None:
    await create_category(amina, "Phones")

    same_shop = await db_client.post(CATEGORIES, json={"name": "PHONES"}, headers=amina.headers)
    other_shop = await db_client.post(CATEGORIES, json={"name": "Phones"}, headers=brian.headers)

    assert same_shop.status_code == 409
    assert same_shop.json()["message"] == "You already have a category with this name"
    assert other_shop.status_code == 201  # Brian's "Phones" is a different category


async def test_slugs_stay_unique_when_names_differ_only_by_punctuation(
    amina, create_category
) -> None:
    first = await create_category(amina, "T-Shirts")
    second = await create_category(amina, "T Shirts")
    third = await create_category(amina, "T_Shirts!")

    assert [first["slug"], second["slug"], third["slug"]] == [
        "t-shirts",
        "t-shirts-2",
        "t-shirts-3",
    ]


@pytest.mark.parametrize(
    "payload",
    [{}, {"name": ""}, {"name": "   "}, {"name": "x" * 101}, {"name": "Ok", "sort_order": -1}],
)
async def test_create_category_validates_its_input(
    db_client: AsyncClient, amina, payload: dict
) -> None:
    response = await db_client.post(CATEGORIES, json=payload, headers=amina.headers)
    assert response.status_code == 422


async def test_update_category(db_client: AsyncClient, amina, create_category) -> None:
    category = await create_category(amina, "Phones", description="Old")
    await create_category(amina, "Laptops")
    url = f"{CATEGORIES}/{category['id']}"

    renamed = await db_client.patch(
        url, json={"name": "Smartphones", "description": None}, headers=amina.headers
    )
    switched_off = await db_client.patch(url, json={"is_active": False}, headers=amina.headers)
    taken = await db_client.patch(url, json={"name": "laptops"}, headers=amina.headers)
    not_nullable = await db_client.patch(url, json={"name": None}, headers=amina.headers)

    assert renamed.status_code == 200
    assert renamed.json()["data"]["name"] == "Smartphones"
    assert renamed.json()["data"]["slug"] == "smartphones"
    assert renamed.json()["data"]["description"] is None
    # Only the fields that were sent change.
    assert switched_off.json()["data"]["name"] == "Smartphones"
    assert switched_off.json()["data"]["is_active"] is False
    assert taken.status_code == 409
    assert not_nullable.status_code == 422


async def test_own_list_is_ordered_filtered_and_searched(
    db_client: AsyncClient, amina, brian, create_category
) -> None:
    await create_category(amina, "Tablets", sort_order=2)
    await create_category(amina, "phones", sort_order=1)
    laptops = await create_category(amina, "Laptops", sort_order=1)
    await create_category(brian, "Brian's Things")
    await db_client.patch(
        f"{CATEGORIES}/{laptops['id']}", json={"is_active": False}, headers=amina.headers
    )

    async def names(**params: object) -> list[str]:
        response = await db_client.get(f"{CATEGORIES}/mine", params=params, headers=amina.headers)
        assert response.status_code == 200, response.text
        return [category["name"] for category in response.json()["data"]["items"]]

    # The seller's order first, then the name; never another shop's categories.
    assert await names() == ["Laptops", "phones", "Tablets"]
    assert await names(is_active=True) == ["phones", "Tablets"]
    assert await names(is_active=False) == ["Laptops"]
    assert await names(q="TAB") == ["Tablets"]
    assert await names(page=2, page_size=2) == ["Tablets"]


async def test_delete_category_removes_its_attributes(
    db_client: AsyncClient, amina, create_category, add_attribute
) -> None:
    category = await create_category(amina)
    await add_attribute(
        amina, category["id"], name="Colour", data_type="select", options=["Black", "White"]
    )
    url = f"{CATEGORIES}/{category['id']}"

    deleted = await db_client.delete(url, headers=amina.headers)

    assert deleted.status_code == 200
    assert (await db_client.get(url, headers=amina.headers)).status_code == 404
    assert (await db_client.delete(url, headers=amina.headers)).status_code == 404
    # The name is free again.
    assert (
        await db_client.post(CATEGORIES, json={"name": "Phones"}, headers=amina.headers)
    ).status_code == 201


# ── Ownership ────────────────────────────────────────────────────────────


async def test_another_sellers_category_looks_like_it_does_not_exist(
    db_client: AsyncClient, amina, brian, create_category, add_attribute
) -> None:
    category = await create_category(amina)
    attribute = await add_attribute(
        amina, category["id"], name="Colour", data_type="select", options=["Black"]
    )
    base = f"{CATEGORIES}/{category['id']}"
    attribute_url = f"{base}/attributes/{attribute['id']}"
    option_url = f"{attribute_url}/options/{attribute['options'][0]['id']}"

    attempts = [
        await db_client.get(base, headers=brian.headers),
        await db_client.patch(base, json={"name": "Hacked"}, headers=brian.headers),
        await db_client.delete(base, headers=brian.headers),
        await db_client.post(
            f"{base}/attributes", json={"name": "X", "data_type": "text"}, headers=brian.headers
        ),
        await db_client.patch(attribute_url, json={"name": "Hacked"}, headers=brian.headers),
        await db_client.delete(attribute_url, headers=brian.headers),
        await db_client.post(
            f"{attribute_url}/options", json={"value": "Hacked"}, headers=brian.headers
        ),
        await db_client.patch(option_url, json={"value": "Hacked"}, headers=brian.headers),
        await db_client.delete(option_url, headers=brian.headers),
    ]

    for response in attempts:
        assert response.status_code == 404
        assert response.json()["message"] == "Category not found"
    # Nothing changed.
    mine = (await db_client.get(base, headers=amina.headers)).json()["data"]
    assert mine["name"] == "Phones"
    assert values(mine["attributes"][0]) == ["Black"]


# ── Attributes ───────────────────────────────────────────────────────────


async def test_add_attributes_of_each_kind(amina, create_category, add_attribute) -> None:
    category = await create_category(amina)

    storage = await add_attribute(
        amina,
        category["id"],
        name="Storage Size",
        data_type="number",
        unit="GB",
        is_required=True,
        is_filterable=True,
    )
    colour = await add_attribute(
        amina, category["id"], name="Colour", data_type="select", options=["Black", "White", "Blue"]
    )
    refurbished = await add_attribute(
        amina, category["id"], name="Refurbished?", data_type="boolean"
    )

    assert storage["code"] == "storage_size"  # a stable key made from the name
    assert (storage["data_type"], storage["unit"]) == ("number", "GB")
    assert (storage["is_required"], storage["is_filterable"], storage["is_active"]) == (
        True,
        True,
        True,
    )
    assert storage["options"] == []
    assert values(colour) == ["Black", "White", "Blue"]  # in the order they were sent
    assert refurbished["code"] == "refurbished"


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "Notes"},  # no type
        {"name": "Notes", "data_type": "paragraph"},
        {"name": "Notes", "data_type": "text", "options": ["a", "b"]},
        {"name": "Notes", "data_type": "text", "unit": "kg"},
        {"name": "Colour", "data_type": "select", "options": ["Black", "black"]},
        {"name": "", "data_type": "text"},
    ],
)
async def test_add_attribute_validates_its_input(
    db_client: AsyncClient, amina, create_category, payload: dict
) -> None:
    category = await create_category(amina)

    response = await db_client.post(
        f"{CATEGORIES}/{category['id']}/attributes", json=payload, headers=amina.headers
    )

    assert response.status_code == 422


async def test_attribute_names_are_unique_within_a_category(
    db_client: AsyncClient, amina, create_category, add_attribute
) -> None:
    phones = await create_category(amina, "Phones")
    laptops = await create_category(amina, "Laptops")
    await add_attribute(amina, phones["id"], name="Colour", data_type="text")

    duplicate = await db_client.post(
        f"{CATEGORIES}/{phones['id']}/attributes",
        json={"name": "COLOUR", "data_type": "text"},
        headers=amina.headers,
    )
    other_category = await add_attribute(amina, laptops["id"], name="Colour", data_type="text")

    assert duplicate.status_code == 409
    assert other_category["code"] == "colour"


async def test_update_attribute_keeps_its_code_and_type(
    db_client: AsyncClient, amina, create_category, add_attribute
) -> None:
    category = await create_category(amina)
    attribute = await add_attribute(amina, category["id"], name="Colour", data_type="select")
    weight = await add_attribute(amina, category["id"], name="Weight", data_type="number")
    url = f"{CATEGORIES}/{category['id']}/attributes"

    renamed = await db_client.patch(
        f"{url}/{attribute['id']}",
        json={"name": "Color", "is_required": True, "is_active": False},
        headers=amina.headers,
    )
    unit_on_select = await db_client.patch(
        f"{url}/{attribute['id']}", json={"unit": "kg"}, headers=amina.headers
    )
    unit_on_number = await db_client.patch(
        f"{url}/{weight['id']}", json={"unit": "kg"}, headers=amina.headers
    )
    type_change = await db_client.patch(
        f"{url}/{attribute['id']}", json={"data_type": "text"}, headers=amina.headers
    )

    data = renamed.json()["data"]
    assert (data["name"], data["code"]) == ("Color", "colour")  # the code never changes
    assert (data["is_required"], data["is_active"]) == (True, False)
    assert unit_on_select.status_code == 422
    assert unit_on_number.json()["data"]["unit"] == "kg"
    # data_type is not an updatable field: it is ignored, and the type stays.
    assert type_change.json()["data"]["data_type"] == "select"


async def test_delete_attribute(
    db_client: AsyncClient, amina, create_category, add_attribute
) -> None:
    category = await create_category(amina)
    attribute = await add_attribute(amina, category["id"], name="Colour", data_type="text")
    url = f"{CATEGORIES}/{category['id']}/attributes/{attribute['id']}"

    assert (await db_client.delete(url, headers=amina.headers)).status_code == 200
    assert (await db_client.delete(url, headers=amina.headers)).status_code == 404
    fetched = await db_client.get(f"{CATEGORIES}/{category['id']}", headers=amina.headers)
    assert fetched.json()["data"]["attributes"] == []


# ── Options ──────────────────────────────────────────────────────────────


async def test_options_are_added_renamed_retired_and_removed(
    db_client: AsyncClient, amina, create_category, add_attribute
) -> None:
    category = await create_category(amina)
    colour = await add_attribute(
        amina, category["id"], name="Colour", data_type="multi_select", options=["Black", "White"]
    )
    url = f"{CATEGORIES}/{category['id']}/attributes/{colour['id']}/options"
    white = colour["options"][1]["id"]

    added = await db_client.post(url, json={"value": "Red"}, headers=amina.headers)
    duplicate = await db_client.post(url, json={"value": "BLACK"}, headers=amina.headers)
    renamed = await db_client.patch(
        f"{url}/{white}", json={"value": "Ivory"}, headers=amina.headers
    )
    clash = await db_client.patch(f"{url}/{white}", json={"value": "red"}, headers=amina.headers)
    retired = await db_client.patch(
        f"{url}/{white}", json={"is_active": False}, headers=amina.headers
    )

    assert added.status_code == 201
    assert values(added.json()["data"]) == ["Black", "White", "Red"]  # new options go last
    assert duplicate.status_code == 409
    assert values(renamed.json()["data"]) == ["Black", "Ivory", "Red"]
    assert clash.status_code == 409
    assert [(o["value"], o["is_active"]) for o in retired.json()["data"]["options"]] == [
        ("Black", True),
        ("Ivory", False),
        ("Red", True),
    ]

    removed = await db_client.delete(f"{url}/{white}", headers=amina.headers)
    again = await db_client.delete(f"{url}/{white}", headers=amina.headers)
    assert values(removed.json()["data"]) == ["Black", "Red"]
    assert again.status_code == 404
    assert again.json()["message"] == "Option not found"


async def test_only_choice_attributes_have_options(
    db_client: AsyncClient, amina, create_category, add_attribute
) -> None:
    category = await create_category(amina)
    weight = await add_attribute(amina, category["id"], name="Weight", data_type="number")

    response = await db_client.post(
        f"{CATEGORIES}/{category['id']}/attributes/{weight['id']}/options",
        json={"value": "Heavy"},
        headers=amina.headers,
    )

    assert response.status_code == 422
    assert response.json()["message"] == "Only select and multi_select attributes have options"


# ── What buyers see ──────────────────────────────────────────────────────


async def test_shop_page_shows_only_what_is_active_and_needs_no_login(
    db_client: AsyncClient, amina, brian, create_category, add_attribute
) -> None:
    phones = await create_category(amina, "Phones")
    old = await create_category(amina, "Discontinued")
    await create_category(brian, "Brian's Things")
    colour = await add_attribute(
        amina, phones["id"], name="Colour", data_type="select", options=["Black", "White"]
    )
    notes = await add_attribute(amina, phones["id"], name="Internal notes", data_type="text")
    base = f"{CATEGORIES}/{phones['id']}/attributes"
    await db_client.patch(
        f"{base}/{colour['id']}/options/{colour['options'][1]['id']}",
        json={"is_active": False},
        headers=amina.headers,
    )
    await db_client.patch(f"{base}/{notes['id']}", json={"is_active": False}, headers=amina.headers)
    await db_client.patch(
        f"{CATEGORIES}/{old['id']}", json={"is_active": False}, headers=amina.headers
    )

    response = await db_client.get(f"{API}/sellers/{amina.seller_id}/categories")  # no token

    assert response.status_code == 200
    page = response.json()["data"]
    assert [category["name"] for category in page["items"]] == ["Phones"]
    (attribute,) = page["items"][0]["attributes"]
    assert attribute["code"] == "colour"
    assert values(attribute) == ["Black"]


async def test_shop_page_of_a_closed_or_unknown_shop_is_not_found(
    db_client: AsyncClient, admin, user, amina, create_category
) -> None:
    await create_category(amina)
    # An application that was never approved has a seller id, but no shop.
    draft = await db_client.post(
        f"{API}/sellers/me",
        json={
            "business_name": "Not Approved Yet",
            "business_phone": "+250788123456",
            "identity_document_type": "passport",
            "identity_document_number": "PC7654321",
            "location": {"province": "Kigali", "district": "Gasabo", "sector": "Remera"},
        },
        headers=user.headers,
    )
    await db_client.post(
        f"{API}/sellers/{amina.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )

    for seller_id in (uuid.uuid4(), draft.json()["data"]["id"], amina.seller_id):
        response = await db_client.get(f"{API}/sellers/{seller_id}/categories")
        assert response.status_code == 404
        assert response.json()["message"] == "Seller not found"


# ── Staff moderation ─────────────────────────────────────────────────────


async def test_staff_can_see_every_shops_categories_and_sellers_cannot(
    db_client: AsyncClient, admin, amina, brian, create_category
) -> None:
    await create_category(amina, "Phones")
    await create_category(brian, "Phones")
    await create_category(brian, "Laptops")

    everything = await db_client.get(CATEGORIES, headers=admin.headers)
    one_shop = await db_client.get(
        CATEGORIES, params={"seller_id": brian.seller_id, "q": "lap"}, headers=admin.headers
    )
    as_seller = await db_client.get(CATEGORIES, headers=amina.headers)

    assert everything.json()["data"]["total"] == 3
    assert [c["name"] for c in one_shop.json()["data"]["items"]] == ["Laptops"]
    assert as_seller.status_code == 403
    assert (await db_client.get(CATEGORIES)).status_code == 401


async def test_a_category_hidden_by_staff_cannot_be_reactivated_by_its_seller(
    db_client: AsyncClient, admin, amina, create_category
) -> None:
    category = await create_category(amina)
    url = f"{CATEGORIES}/{category['id']}"

    as_seller = await db_client.post(f"{url}/hide", headers=amina.headers)
    hidden = await db_client.post(f"{url}/hide", headers=admin.headers)

    assert as_seller.status_code == 403
    assert hidden.status_code == 200
    assert hidden.json()["data"]["is_active"] is False
    assert hidden.json()["data"]["hidden_by_staff_at"] is not None
    shop = await db_client.get(f"{API}/sellers/{amina.seller_id}/categories")
    assert shop.json()["data"]["items"] == []

    reactivated = await db_client.patch(url, json={"is_active": True}, headers=amina.headers)
    assert reactivated.status_code == 409
    assert reactivated.json()["message"] == (
        "This category was hidden by MUHUZE and cannot be reactivated"
    )
    # The seller can still see it, and why it is off.
    mine = (await db_client.get(url, headers=amina.headers)).json()["data"]
    assert mine["hidden_by_staff_at"] is not None

    restored = await db_client.post(f"{url}/restore", headers=admin.headers)
    assert restored.json()["data"]["is_active"] is True
    assert restored.json()["data"]["hidden_by_staff_at"] is None
    assert (
        await db_client.post(f"{CATEGORIES}/{uuid.uuid4()}/hide", headers=admin.headers)
    ).status_code == 404
