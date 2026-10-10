"""Products through the HTTP API, against a real PostgreSQL database.
Two shops (Amina's and Brian's) check that nothing leaks between them, and
images go to an in-memory fake storage."""

import uuid

import pytest
from httpx import AsyncClient, Response

from app.modules.products.product_constants import IMAGE_MAX_BYTES, IMAGES_PER_PRODUCT_MAX

API = "/api/v1"
PRODUCTS = f"{API}/products"
MINE = f"{PRODUCTS}/mine"
MODERATION = f"{PRODUCTS}/moderation"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20
PNG = b"\x89PNG\r\n\x1a\n" + b"png-bytes" * 20


class Shop:
    """A seller with a "Phones" category that has one attribute of each type."""

    def __init__(self, actor, category: dict, attributes: dict[str, dict]) -> None:
        self.headers = actor.headers
        self.seller_id = actor.seller_id
        self.category_id = category["id"]
        self.attributes = attributes

    def option(self, code: str, value: str) -> str:
        return next(o["id"] for o in self.attributes[code]["options"] if o["value"] == value)

    def attribute_url(self, code: str) -> str:
        return f"{API}/categories/{self.category_id}/attributes/{self.attributes[code]['id']}"


@pytest.fixture
def make_shop(db_client: AsyncClient, sign_up, open_shop):
    async def _make_shop(email: str, name: str) -> Shop:
        actor = await sign_up(email)
        actor.seller_id = await open_shop(actor, name)
        category = (
            await db_client.post(
                f"{API}/categories", json={"name": "Phones"}, headers=actor.headers
            )
        ).json()["data"]
        definitions = [
            {"name": "Storage", "data_type": "number", "unit": "GB", "is_required": True},
            {"name": "Colour", "data_type": "select", "options": ["Black", "White"]},
            {"name": "Features", "data_type": "multi_select", "options": ["NFC", "5G", "Dual SIM"]},
            {"name": "Refurbished", "data_type": "boolean"},
            {"name": "Model", "data_type": "text"},
        ]
        attributes = {}
        for definition in definitions:
            response = await db_client.post(
                f"{API}/categories/{category['id']}/attributes",
                json=definition,
                headers=actor.headers,
            )
            assert response.status_code == 201, response.text
            attributes[response.json()["data"]["code"]] = response.json()["data"]
        return Shop(actor, category, attributes)

    return _make_shop


@pytest.fixture
async def amina(make_shop) -> Shop:
    return await make_shop("amina@example.com", "Amina Shop")


@pytest.fixture
async def brian(make_shop) -> Shop:
    return await make_shop("brian@example.com", "Brian Shop")


@pytest.fixture
def create_product(db_client: AsyncClient):
    async def _create_product(shop: Shop, name: str = "Galaxy S24", **fields: object) -> dict:
        payload = {"name": name, "price": "850000", "category_id": shop.category_id, **fields}
        response = await db_client.post(PRODUCTS, json=payload, headers=shop.headers)
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _create_product


@pytest.fixture
def add_image(db_client: AsyncClient):
    async def _add_image(shop: Shop, product_id: str, content: bytes = JPEG) -> Response:
        return await db_client.post(
            f"{MINE}/{product_id}/images",
            files={"file": ("photo.jpg", content)},
            headers=shop.headers,
        )

    return _add_image


@pytest.fixture
def published_product(db_client: AsyncClient, create_product, add_image):
    """A complete product that is on sale."""

    async def _published_product(shop: Shop, name: str = "Galaxy S24", **fields: object) -> dict:
        fields.setdefault("attributes", {"storage": 256})
        product = await create_product(shop, name, **fields)
        assert (await add_image(shop, product["id"])).status_code == 201
        response = await db_client.post(f"{MINE}/{product['id']}/publish", headers=shop.headers)
        assert response.status_code == 200, response.text
        return response.json()["data"]

    return _published_product


def attribute_values(product: dict) -> dict[str, object]:
    """{"storage": 256, "colour": "Black", "features": ["NFC", "5G"]}"""
    simple = {}
    for attribute in product["attributes"]:
        value = attribute["value"]
        if isinstance(value, dict):
            value = value["value"]
        elif isinstance(value, list):
            value = [option["value"] for option in value]
        simple[attribute["code"]] = value
    return simple


# ── Creating ─────────────────────────────────────────────────────────────


async def test_create_product_starts_a_draft(db_client: AsyncClient, amina: Shop) -> None:
    response = await db_client.post(
        PRODUCTS,
        json={
            "name": "  Galaxy S24 Ultra ",
            "description": "Brand new, sealed.",
            "price": "850000",
            "category_id": amina.category_id,
            "attributes": {
                "storage": 256,
                "colour": amina.option("colour", "Black"),
                "features": [amina.option("features", "5G"), amina.option("features", "NFC")],
                "refurbished": False,
                "model": "SM-S928B",
            },
        },
        headers=amina.headers,
    )

    assert response.status_code == 201
    product = response.json()["data"]
    assert product["seller_id"] == amina.seller_id
    assert product["category_id"] == amina.category_id
    assert product["name"] == "Galaxy S24 Ultra"
    assert product["slug"] == "galaxy-s24-ultra"
    assert product["price"] == "850000.00"  # money is a decimal string, never a float
    assert product["currency"] == "RWF"
    assert product["status"] == "draft"
    assert product["published_at"] is None
    assert product["images"] == []
    assert product["main_image_url"] is None
    assert attribute_values(product) == {
        "storage": 256,
        "colour": "Black",
        "features": ["NFC", "5G"],  # in the attribute's own option order
        "refurbished": False,
        "model": "SM-S928B",
    }
    storage = next(a for a in product["attributes"] if a["code"] == "storage")
    assert (storage["name"], storage["data_type"], storage["unit"]) == ("Storage", "number", "GB")
    assert product["publish_blockers"] == ["Add at least one image"]

    fetched = await db_client.get(f"{MINE}/{product['id']}", headers=amina.headers)
    assert fetched.json()["data"] == product


async def test_a_draft_can_be_incomplete(amina: Shop, create_product) -> None:
    product = await create_product(amina)

    assert product["attributes"] == []
    assert product["publish_blockers"] == [
        "Missing required attribute: Storage",
        "Add at least one image",
    ]


async def test_attribute_values_are_checked_against_the_category(
    db_client: AsyncClient, amina: Shop
) -> None:
    response = await db_client.post(
        PRODUCTS,
        json={
            "name": "Bad",
            "price": "1000",
            "category_id": amina.category_id,
            "attributes": {
                "storage": "big",
                "colour": "Black",  # the option's text, not its id
                "features": [],
                "refurbished": "yes",
                "model": 42,
                "weight": 5,  # not an attribute of this category
            },
        },
        headers=amina.headers,
    )

    assert response.status_code == 422
    message = response.json()["message"]
    # Every problem is reported at once, named by attribute.
    for expected in (
        "storage: must be a number",
        "colour: must be one of this attribute's options",
        "features: must be a list with at least one option",
        "refurbished: must be true or false",
        "model: must be text",
        "weight: is not an attribute of this category",
    ):
        assert expected in message
    listed = await db_client.get(MINE, headers=amina.headers)
    assert listed.json()["data"]["total"] == 0  # nothing was saved


async def test_true_is_not_accepted_as_a_number_and_options_must_not_repeat(
    db_client: AsyncClient, amina: Shop
) -> None:
    nfc = amina.option("features", "NFC")

    response = await db_client.post(
        PRODUCTS,
        json={
            "name": "Bad",
            "price": "1000",
            "category_id": amina.category_id,
            "attributes": {"storage": True, "features": [nfc, nfc]},
        },
        headers=amina.headers,
    )

    assert response.status_code == 422
    assert "storage: must be a number" in response.json()["message"]
    assert "features: must not repeat an option" in response.json()["message"]


@pytest.mark.parametrize(
    "fields",
    [
        {"name": ""},
        {"name": "x" * 201},
        {"price": "0"},
        {"price": "-5"},
        {"price": "10.999"},  # more than two decimal places
        {"price": "abc"},
        {"category_id": "not-a-uuid"},
    ],
)
async def test_create_product_validates_its_input(
    db_client: AsyncClient, amina: Shop, fields: dict
) -> None:
    payload = {"name": "Phone", "price": "1000", "category_id": amina.category_id, **fields}
    response = await db_client.post(PRODUCTS, json=payload, headers=amina.headers)
    assert response.status_code == 422


async def test_a_product_must_go_in_one_of_the_sellers_own_categories(
    db_client: AsyncClient, amina: Shop, brian: Shop
) -> None:
    payload = {"name": "Phone", "price": "1000"}

    theirs = await db_client.post(
        PRODUCTS, json={**payload, "category_id": brian.category_id}, headers=amina.headers
    )
    missing = await db_client.post(
        PRODUCTS, json={**payload, "category_id": str(uuid.uuid4())}, headers=amina.headers
    )

    assert theirs.status_code == missing.status_code == 404
    assert theirs.json()["message"] == "Category not found"


async def test_only_an_active_seller_can_create_products(
    db_client: AsyncClient, admin, user, amina: Shop
) -> None:
    payload = {"name": "Phone", "price": "1000", "category_id": amina.category_id}

    assert (await db_client.post(PRODUCTS, json=payload)).status_code == 401
    assert (await db_client.post(PRODUCTS, json=payload, headers=user.headers)).status_code == 403

    await db_client.post(
        f"{API}/sellers/{amina.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    suspended = await db_client.post(PRODUCTS, json=payload, headers=amina.headers)
    assert suspended.status_code == 403
    assert suspended.json()["message"] == "Only an approved, active seller can do this"


async def test_slugs_are_unique_within_a_shop(amina: Shop, brian: Shop, create_product) -> None:
    first = await create_product(amina, "iPhone 15")
    second = await create_product(amina, "iPhone 15")  # the same name is allowed
    other_shop = await create_product(brian, "iPhone 15")

    assert [first["slug"], second["slug"], other_shop["slug"]] == [
        "iphone-15",
        "iphone-15-2",
        "iphone-15",
    ]


# ── Updating ─────────────────────────────────────────────────────────────


async def test_update_changes_only_what_is_sent(
    db_client: AsyncClient, amina: Shop, create_product
) -> None:
    product = await create_product(
        amina,
        description="Old",
        attributes={"storage": 128, "model": "A1", "colour": amina.option("colour", "Black")},
    )
    url = f"{MINE}/{product['id']}"

    response = await db_client.patch(
        url,
        json={
            "name": "Galaxy S24 FE",
            "price": "799000.5",
            "description": None,
            # Only the codes sent are touched: storage changes, model is cleared,
            # colour (not sent) stays.
            "attributes": {"storage": 512, "model": None},
        },
        headers=amina.headers,
    )

    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["name"] == "Galaxy S24 FE"
    assert updated["slug"] == "galaxy-s24-fe"
    assert updated["price"] == "799000.50"
    assert updated["description"] is None
    assert attribute_values(updated) == {"storage": 512, "colour": "Black"}

    not_nullable = await db_client.patch(url, json={"price": None}, headers=amina.headers)
    assert not_nullable.status_code == 422


async def test_moving_to_another_category_drops_the_old_attribute_values(
    db_client: AsyncClient, amina: Shop, create_product
) -> None:
    product = await create_product(amina, attributes={"storage": 128})
    laptops = (
        await db_client.post(f"{API}/categories", json={"name": "Laptops"}, headers=amina.headers)
    ).json()["data"]

    response = await db_client.patch(
        f"{MINE}/{product['id']}", json={"category_id": laptops["id"]}, headers=amina.headers
    )

    assert response.status_code == 200
    assert response.json()["data"]["category_id"] == laptops["id"]
    assert response.json()["data"]["attributes"] == []


# ── Images ───────────────────────────────────────────────────────────────


async def test_images_are_added_ordered_and_removed(
    db_client: AsyncClient, amina: Shop, create_product, add_image, file_storage
) -> None:
    product = await create_product(amina)
    url = f"{MINE}/{product['id']}"

    await add_image(amina, product["id"], JPEG)
    response = await add_image(amina, product["id"], PNG)

    assert response.status_code == 201
    first, second = response.json()["data"]["images"]
    assert [first["sort_order"], second["sort_order"]] == [0, 1]
    assert first["url"].startswith("https://images.example.test/muhuze/products/")
    assert response.json()["data"]["main_image_url"] == first["url"]
    assert len(file_storage.public_images) == 2

    reordered = await db_client.put(
        f"{url}/images/order",
        json={"image_ids": [second["id"], first["id"]]},
        headers=amina.headers,
    )
    assert [image["id"] for image in reordered.json()["data"]["images"]] == [
        second["id"],
        first["id"],
    ]
    assert reordered.json()["data"]["main_image_url"] == second["url"]

    for bad_order in ([first["id"]], [first["id"], first["id"]], [first["id"], str(uuid.uuid4())]):
        response = await db_client.put(
            f"{url}/images/order", json={"image_ids": bad_order}, headers=amina.headers
        )
        assert response.status_code == 422

    removed = await db_client.delete(f"{url}/images/{first['id']}", headers=amina.headers)
    again = await db_client.delete(f"{url}/images/{first['id']}", headers=amina.headers)
    assert [image["id"] for image in removed.json()["data"]["images"]] == [second["id"]]
    assert again.status_code == 404
    assert len(file_storage.public_images) == 1  # the file left storage too


async def test_image_uploads_are_checked(
    amina: Shop, create_product, add_image, file_storage
) -> None:
    product = await create_product(amina)

    not_an_image = await add_image(amina, product["id"], b"%PDF-1.7 a document")
    too_large = await add_image(amina, product["id"], JPEG + b"0" * IMAGE_MAX_BYTES)

    assert not_an_image.status_code == 422
    assert not_an_image.json()["message"] == "The image must be a JPEG or PNG"
    assert too_large.status_code == 422
    assert too_large.json()["message"] == "The image is larger than 5 MB"
    assert file_storage.public_images == {}

    for _ in range(IMAGES_PER_PRODUCT_MAX):
        assert (await add_image(amina, product["id"])).status_code == 201
    one_too_many = await add_image(amina, product["id"])
    assert one_too_many.status_code == 422
    assert one_too_many.json()["message"] == "A product can have at most 8 images"


# ── Publishing ───────────────────────────────────────────────────────────


async def test_publish_needs_required_attributes_and_an_image(
    db_client: AsyncClient, amina: Shop, create_product, add_image
) -> None:
    product = await create_product(amina)
    url = f"{MINE}/{product['id']}"

    blocked = await db_client.post(f"{url}/publish", headers=amina.headers)
    assert blocked.status_code == 422
    assert blocked.json()["message"] == (
        "Missing required attribute: Storage; Add at least one image"
    )

    await db_client.patch(url, json={"attributes": {"storage": 256}}, headers=amina.headers)
    await add_image(amina, product["id"])
    published = await db_client.post(f"{url}/publish", headers=amina.headers)

    assert published.status_code == 200
    data = published.json()["data"]
    assert data["status"] == "published"
    assert data["published_at"] is not None
    assert data["publish_blockers"] == []
    twice = await db_client.post(f"{url}/publish", headers=amina.headers)
    assert twice.status_code == 409


async def test_a_published_product_must_stay_complete(
    db_client: AsyncClient, amina: Shop, published_product
) -> None:
    product = await published_product(amina)
    url = f"{MINE}/{product['id']}"

    cleared = await db_client.patch(
        url, json={"attributes": {"storage": None}}, headers=amina.headers
    )
    no_image = await db_client.delete(
        f"{url}/images/{product['images'][0]['id']}", headers=amina.headers
    )

    assert cleared.status_code == 422
    assert cleared.json()["message"] == "Missing required attribute: Storage"
    assert no_image.status_code == 422
    assert no_image.json()["message"] == "Add at least one image"
    # Both were refused as a whole: nothing changed.
    current = (await db_client.get(url, headers=amina.headers)).json()["data"]
    assert attribute_values(current) == {"storage": 256}
    assert len(current["images"]) == 1
    # Ordinary edits are still fine.
    edited = await db_client.patch(url, json={"price": "900000"}, headers=amina.headers)
    assert edited.json()["data"]["price"] == "900000.00"


async def test_archive_and_publish_again(
    db_client: AsyncClient, amina: Shop, published_product
) -> None:
    product = await published_product(amina)
    url = f"{MINE}/{product['id']}"

    archived = await db_client.post(f"{url}/archive", headers=amina.headers)
    archived_again = await db_client.post(f"{url}/archive", headers=amina.headers)
    assert archived.json()["data"]["status"] == "archived"
    assert archived_again.status_code == 409
    assert (await db_client.get(f"{PRODUCTS}/{product['id']}")).status_code == 404

    republished = await db_client.post(f"{url}/publish", headers=amina.headers)
    assert republished.json()["data"]["status"] == "published"
    # published_at is the FIRST publication and does not move.
    assert republished.json()["data"]["published_at"] == product["published_at"]


async def test_only_a_never_published_draft_can_be_deleted(
    db_client: AsyncClient, amina: Shop, create_product, add_image, published_product, file_storage
) -> None:
    draft = await create_product(amina, "Draft")
    await add_image(amina, draft["id"])
    on_sale = await published_product(amina, "On sale")
    await db_client.post(f"{MINE}/{on_sale['id']}/archive", headers=amina.headers)

    deleted = await db_client.delete(f"{MINE}/{draft['id']}", headers=amina.headers)
    refused = await db_client.delete(f"{MINE}/{on_sale['id']}", headers=amina.headers)

    assert deleted.status_code == 200
    assert (await db_client.get(f"{MINE}/{draft['id']}", headers=amina.headers)).status_code == 404
    assert len(file_storage.public_images) == 1  # the draft's image was removed with it
    assert refused.status_code == 409  # archived, but it has been on sale
    assert refused.json()["message"] == (
        "A product that has been published cannot be deleted. Archive it instead."
    )


# ── Ownership ────────────────────────────────────────────────────────────


async def test_another_sellers_product_looks_like_it_does_not_exist(
    db_client: AsyncClient, amina: Shop, brian: Shop, published_product
) -> None:
    product = await published_product(amina)
    url = f"{MINE}/{product['id']}"
    image_id = product["images"][0]["id"]

    attempts = [
        await db_client.get(url, headers=brian.headers),
        await db_client.patch(url, json={"price": "1"}, headers=brian.headers),
        await db_client.delete(url, headers=brian.headers),
        await db_client.post(f"{url}/archive", headers=brian.headers),
        await db_client.post(f"{url}/publish", headers=brian.headers),
        await db_client.post(
            f"{url}/images", files={"file": ("x.jpg", JPEG)}, headers=brian.headers
        ),
        await db_client.delete(f"{url}/images/{image_id}", headers=brian.headers),
        await db_client.put(
            f"{url}/images/order", json={"image_ids": [image_id]}, headers=brian.headers
        ),
    ]

    for response in attempts:
        assert response.status_code == 404
        assert response.json()["message"] == "Product not found"
    untouched = (await db_client.get(url, headers=amina.headers)).json()["data"]
    assert (untouched["price"], untouched["status"]) == ("850000.00", "published")
    # Brian's own list never contains Amina's products.
    assert (await db_client.get(MINE, headers=brian.headers)).json()["data"]["total"] == 0


# ── Own list ─────────────────────────────────────────────────────────────


async def test_own_list_filters_searches_and_sorts(
    db_client: AsyncClient, amina: Shop, create_product, published_product
) -> None:
    await create_product(amina, "Zenfone", price="300000")
    await published_product(amina, "apple iPhone", price="900000")
    await create_product(amina, "Pixel 8", price="600000")

    async def names(**params: object) -> list[str]:
        response = await db_client.get(MINE, params=params, headers=amina.headers)
        assert response.status_code == 200, response.text
        return [product["name"] for product in response.json()["data"]["items"]]

    assert await names(sort="name") == ["apple iPhone", "Pixel 8", "Zenfone"]
    assert await names(sort="-price") == ["apple iPhone", "Pixel 8", "Zenfone"]
    assert await names(sort="price") == ["Zenfone", "Pixel 8", "apple iPhone"]
    assert await names(status="published") == ["apple iPhone"]
    assert await names(status="draft", sort="name") == ["Pixel 8", "Zenfone"]
    assert await names(q="PIXEL") == ["Pixel 8"]
    assert await names(category_id=amina.category_id, sort="name", page=2, page_size=2) == [
        "Zenfone"
    ]
    assert await names(category_id=str(uuid.uuid4())) == []

    bad_sort = await db_client.get(MINE, params={"sort": "seller_id"}, headers=amina.headers)
    assert bad_sort.status_code == 422


# ── What buyers see ──────────────────────────────────────────────────────


async def test_buyers_see_published_products_without_logging_in(
    db_client: AsyncClient, amina: Shop, brian: Shop, create_product, published_product
) -> None:
    phone = await published_product(
        amina, "Galaxy S24", price="850000", attributes={"storage": 256, "model": "SM-S921"}
    )
    await published_product(brian, "Budget Phone", price="90000")
    await create_product(amina, "Unfinished Draft")

    listing = await db_client.get(PRODUCTS, params={"sort": "price"})  # no token
    detail = await db_client.get(f"{PRODUCTS}/{phone['id']}")

    assert listing.status_code == 200
    items = listing.json()["data"]["items"]
    assert [(item["name"], item["price"]) for item in items] == [
        ("Budget Phone", "90000.00"),
        ("Galaxy S24", "850000.00"),
    ]
    assert all(item["main_image_url"] for item in items)

    assert detail.status_code == 200
    product = detail.json()["data"]
    assert product["shop"] == {"id": amina.seller_id, "name": "Amina Shop"}
    assert attribute_values(product) == {"storage": 256, "model": "SM-S921"}
    assert len(product["images"]) == 1
    assert "publish_blockers" not in product  # a seller-only field


async def test_public_list_filters(
    db_client: AsyncClient, amina: Shop, brian: Shop, published_product
) -> None:
    await published_product(amina, "Galaxy S24", price="850000")
    await published_product(amina, "Galaxy A15", price="200000")
    await published_product(brian, "Pixel 8", price="600000")

    async def names(**params: object) -> list[str]:
        response = await db_client.get(PRODUCTS, params={"sort": "name", **params})
        assert response.status_code == 200, response.text
        return [product["name"] for product in response.json()["data"]["items"]]

    assert await names() == ["Galaxy A15", "Galaxy S24", "Pixel 8"]
    assert await names(seller_id=amina.seller_id) == ["Galaxy A15", "Galaxy S24"]
    assert await names(category_id=brian.category_id) == ["Pixel 8"]
    assert await names(q="galaxy") == ["Galaxy A15", "Galaxy S24"]
    assert await names(min_price=500000) == ["Galaxy S24", "Pixel 8"]
    assert await names(min_price=500000, max_price=700000) == ["Pixel 8"]
    assert await names(page=2, page_size=2) == ["Pixel 8"]


async def test_products_disappear_for_buyers_when_anything_behind_them_is_switched_off(
    db_client: AsyncClient, admin, amina: Shop, published_product
) -> None:
    product = await published_product(amina)
    public_url = f"{PRODUCTS}/{product['id']}"

    async def visible() -> bool:
        detail = await db_client.get(public_url)
        listing = await db_client.get(PRODUCTS, params={"seller_id": amina.seller_id})
        in_list = listing.json()["data"]["total"] == 1
        assert (detail.status_code == 200) == in_list  # the list and the page always agree
        return in_list

    assert await visible()

    # 1. The category is switched off.
    category_url = f"{API}/categories/{amina.category_id}"
    await db_client.patch(category_url, json={"is_active": False}, headers=amina.headers)
    assert not await visible()
    await db_client.patch(category_url, json={"is_active": True}, headers=amina.headers)
    assert await visible()

    # 2. Staff hide the product; the seller cannot publish it back.
    await db_client.post(f"{MODERATION}/{product['id']}/hide", headers=admin.headers)
    assert not await visible()
    await db_client.post(f"{MINE}/{product['id']}/archive", headers=amina.headers)
    republish = await db_client.post(f"{MINE}/{product['id']}/publish", headers=amina.headers)
    assert republish.status_code == 409
    assert republish.json()["message"] == (
        "This product was hidden by MUHUZE and cannot be published"
    )
    await db_client.post(f"{MODERATION}/{product['id']}/restore", headers=admin.headers)
    await db_client.post(f"{MINE}/{product['id']}/publish", headers=amina.headers)
    assert await visible()

    # 3. The shop is suspended.
    await db_client.post(
        f"{API}/sellers/{amina.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    assert not await visible()
    missing = await db_client.get(public_url)
    assert missing.json()["message"] == "Product not found"  # never says why


async def test_switched_off_attributes_are_hidden_from_buyers_but_kept(
    db_client: AsyncClient, amina: Shop, published_product
) -> None:
    product = await published_product(amina, attributes={"storage": 256, "model": "SM-S921"})

    await db_client.patch(
        amina.attribute_url("model"), json={"is_active": False}, headers=amina.headers
    )

    public = (await db_client.get(f"{PRODUCTS}/{product['id']}")).json()["data"]
    own = (await db_client.get(f"{MINE}/{product['id']}", headers=amina.headers)).json()["data"]
    assert attribute_values(public) == {"storage": 256}
    assert attribute_values(own) == {"storage": 256, "model": "SM-S921"}  # the value is kept
    # A switched-off attribute can no longer be set.
    refused = await db_client.patch(
        f"{MINE}/{product['id']}", json={"attributes": {"model": "X"}}, headers=amina.headers
    )
    assert refused.status_code == 422
    assert "model: is no longer used" in refused.json()["message"]


# ── Categories and attributes that products use ──────────────────────────


async def test_what_products_use_cannot_be_deleted_only_switched_off(
    db_client: AsyncClient, amina: Shop, create_product
) -> None:
    black, white = amina.option("colour", "Black"), amina.option("colour", "White")
    await create_product(amina, attributes={"storage": 128, "colour": black})
    category_url = f"{API}/categories/{amina.category_id}"

    category = await db_client.delete(category_url, headers=amina.headers)
    attribute = await db_client.delete(amina.attribute_url("storage"), headers=amina.headers)
    option = await db_client.delete(
        f"{amina.attribute_url('colour')}/options/{black}", headers=amina.headers
    )
    unused_option = await db_client.delete(
        f"{amina.attribute_url('colour')}/options/{white}", headers=amina.headers
    )
    unused_attribute = await db_client.delete(amina.attribute_url("model"), headers=amina.headers)

    assert category.status_code == attribute.status_code == option.status_code == 409
    assert category.json()["message"] == (
        "This category still has products. Move them or switch the category off."
    )
    assert attribute.json()["message"] == (
        "Products already use this attribute. Switch it off instead."
    )
    assert option.json()["message"] == "Products already use this option. Switch it off instead."
    assert unused_option.status_code == unused_attribute.status_code == 200
    # Everything that was refused is still there.
    remaining = (await db_client.get(category_url, headers=amina.headers)).json()["data"]
    codes = {attribute["code"] for attribute in remaining["attributes"]}
    assert {"storage", "colour"} <= codes
    assert "model" not in codes


async def test_a_retired_option_stays_on_products_that_have_it(
    db_client: AsyncClient, amina: Shop, create_product
) -> None:
    black = amina.option("colour", "Black")
    has_it = await create_product(amina, "Has black", attributes={"colour": black})
    other = await create_product(amina, "Other")
    await db_client.patch(
        f"{amina.attribute_url('colour')}/options/{black}",
        json={"is_active": False},
        headers=amina.headers,
    )

    kept = await db_client.patch(
        f"{MINE}/{has_it['id']}", json={"attributes": {"colour": black}}, headers=amina.headers
    )
    new_use = await db_client.patch(
        f"{MINE}/{other['id']}", json={"attributes": {"colour": black}}, headers=amina.headers
    )

    assert attribute_values(kept.json()["data"]) == {"colour": "Black"}
    assert new_use.status_code == 422  # a retired option can't be chosen afresh


# ── Staff moderation ─────────────────────────────────────────────────────


async def test_staff_see_every_product_and_sellers_do_not(
    db_client: AsyncClient, admin, amina: Shop, brian: Shop, create_product, published_product
) -> None:
    draft = await create_product(amina, "Amina Draft")
    await published_product(brian, "Brian Phone")

    everything = await db_client.get(MODERATION, params={"sort": "name"}, headers=admin.headers)
    drafts = await db_client.get(
        MODERATION, params={"status": "draft", "seller_id": amina.seller_id}, headers=admin.headers
    )
    detail = await db_client.get(f"{MODERATION}/{draft['id']}", headers=admin.headers)

    assert [p["name"] for p in everything.json()["data"]["items"]] == ["Amina Draft", "Brian Phone"]
    assert [p["name"] for p in drafts.json()["data"]["items"]] == ["Amina Draft"]
    assert detail.json()["data"]["status"] == "draft"  # staff can open a draft
    for path in ("", f"/{draft['id']}", f"/{draft['id']}/hide", f"/{draft['id']}/restore"):
        method = "POST" if path.endswith(("hide", "restore")) else "GET"
        as_seller = await db_client.request(method, MODERATION + path, headers=amina.headers)
        anonymous = await db_client.request(method, MODERATION + path)
        assert (as_seller.status_code, anonymous.status_code) == (403, 401)
    missing = await db_client.post(f"{MODERATION}/{uuid.uuid4()}/hide", headers=admin.headers)
    assert missing.status_code == 404
