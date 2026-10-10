"""Products: what sellers offer for sale.
Rules are documented in docs/features/007_products.md and README §7.

    draft → published ⇄ archived

A product belongs to one seller and sits in one of that seller's categories.
Its category-specific details are attribute values, validated here against
the category's attributes. Every method that changes a product takes the
acting seller's id: a product of another shop looks exactly like one that
doesn't exist. Buyers see a product only when it is published, not hidden by
staff, in a visible category, and its shop is open.
Every public method is one unit of work and commits it.
"""

import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.infrastructure.storage.file_storage import FileStorage, FileStorageError
from app.modules.categories.category_constants import AttributeDataType
from app.modules.categories.category_schema import AttributeResponse, CategoryResponse
from app.modules.categories.category_service import CategoryService, visible_category_ids
from app.modules.products.product_constants import (
    ATTRIBUTE_NUMBER_LIMIT,
    ATTRIBUTE_NUMBER_QUANTUM,
    ATTRIBUTE_TEXT_MAX_LENGTH,
    IMAGE_MAX_BYTES,
    IMAGE_SIGNATURES,
    IMAGES_PER_PRODUCT_MAX,
    PRODUCT_SLUG_MAX_LENGTH,
    ProductStatus,
)
from app.modules.products.product_exceptions import (
    ImageStorageUnavailableError,
    InvalidImageOrderError,
    InvalidProductAttributesError,
    InvalidProductImageError,
    ProductHiddenByStaffError,
    ProductImageNotFoundError,
    ProductImageTooLargeError,
    ProductNotDeletableError,
    ProductNotFoundError,
    ProductNotPublishableError,
    ProductStatusConflictError,
    TooManyProductImagesError,
)
from app.modules.products.product_model import Product, ProductAttributeValue, ProductImage
from app.modules.products.product_repository import ProductRepository
from app.modules.products.product_schema import (
    OptionValueResponse,
    OwnProductFilters,
    OwnProductResponse,
    ProductAttributeValueResponse,
    ProductCreateRequest,
    ProductImageResponse,
    ProductResponse,
    ProductSummaryResponse,
    ProductUpdateRequest,
    PublicProductFilters,
    PublicProductResponse,
    ShopSummaryResponse,
    StaffProductFilters,
)
from app.modules.sellers.seller_exceptions import SellerNotFoundError
from app.modules.sellers.seller_service import SellerService, open_shop_ids
from app.shared.responses.pagination import Page, PaginationParams
from app.shared.slugs import slugify, unique_among

logger = get_logger(__name__)

# Leaves room for a "-2", "-3" … suffix when two names give the same slug.
SLUG_BASE_MAX_LENGTH = PRODUCT_SLUG_MAX_LENGTH - 6


class ProductService:
    def __init__(
        self,
        session: AsyncSession,
        category_service: CategoryService,
        seller_service: SellerService,
        file_storage: FileStorage,
    ) -> None:
        self._session = session
        self._categories = category_service
        self._sellers = seller_service
        self._file_storage = file_storage
        self._repository = ProductRepository(session)

    # ── A seller's own products ──────────────────────────────────────────

    async def create_product(
        self, *, seller_id: uuid.UUID, payload: ProductCreateRequest
    ) -> OwnProductResponse:
        """Start a product as a draft. It may be incomplete; `publish` checks it."""
        # Raises "Category not found" for a category of another shop.
        category = await self._categories.get_own_category(
            seller_id=seller_id, category_id=payload.category_id
        )
        product = Product(
            seller_id=seller_id,
            category_id=category.id,
            name=payload.name,
            slug=await self._unique_slug(seller_id, payload.name),
            description=payload.description or None,
            price=_money(payload.price),
            status=ProductStatus.DRAFT.value,
        )
        await self._repository.add(product)
        await self._set_attribute_values(product, category, payload.attributes, current=[])
        await self._session.commit()
        logger.info(
            "product created", extra={"product_id": str(product.id), "seller_id": str(seller_id)}
        )
        return await self._own_response(product, category)

    async def list_own_products(
        self, *, seller_id: uuid.UUID, pagination: PaginationParams, filters: OwnProductFilters
    ) -> Page[ProductSummaryResponse]:
        products, total = await self._repository.list_products(
            pagination,
            sort=filters.sort,
            seller_id=seller_id,
            category_id=filters.category_id,
            status=filters.status.value if filters.status else None,
            search=_search(filters.q),
        )
        return await self._summary_page(products, total, pagination)

    async def get_own_product(
        self, *, seller_id: uuid.UUID, product_id: uuid.UUID
    ) -> OwnProductResponse:
        product = await self._own(seller_id, product_id)
        return await self._own_response(product)

    async def update_product(
        self, *, seller_id: uuid.UUID, product_id: uuid.UUID, payload: ProductUpdateRequest
    ) -> OwnProductResponse:
        """Change a product. A published product must stay publishable: an
        edit that would leave it incomplete is refused."""
        product = await self._own(seller_id, product_id, for_update=True)
        changes = payload.model_dump(exclude_unset=True, exclude={"attributes", "category_id"})

        new_name = changes.get("name")
        if new_name is not None and new_name != product.name:
            product.name = new_name
            product.slug = await self._unique_slug(seller_id, new_name, except_id=product.id)
        if "description" in changes:
            product.description = changes["description"] or None
        if "price" in changes:
            product.price = _money(changes["price"])

        current = await self._repository.list_values(product.id)
        if payload.category_id is not None and payload.category_id != product.category_id:
            category = await self._categories.get_own_category(
                seller_id=seller_id, category_id=payload.category_id
            )
            # The old category's attributes mean nothing in the new one.
            await self._repository.delete_values(product.id)
            product.category_id = category.id
            current = []
        else:
            category = await self._categories.get_category_definition(product.category_id)
        if payload.attributes is not None:
            await self._set_attribute_values(product, category, payload.attributes, current=current)

        if product.status == ProductStatus.PUBLISHED:
            await self._require_publishable(product, category)
        await self._session.commit()
        logger.info("product updated", extra={"product_id": str(product.id)})
        return await self._own_response(product, category)

    async def publish(self, *, seller_id: uuid.UUID, product_id: uuid.UUID) -> OwnProductResponse:
        """Make a draft or archived product visible to buyers."""
        product = await self._own(seller_id, product_id, for_update=True)
        if product.status == ProductStatus.PUBLISHED:
            raise ProductStatusConflictError("This product is already published")
        if product.hidden_by_staff_at is not None:
            raise ProductHiddenByStaffError()
        category = await self._categories.get_category_definition(product.category_id)
        await self._require_publishable(product, category)

        product.status = ProductStatus.PUBLISHED.value
        if product.published_at is None:
            product.published_at = utc_now()
        await self._session.commit()
        logger.info("product published", extra={"product_id": str(product.id)})
        return await self._own_response(product, category)

    async def archive(self, *, seller_id: uuid.UUID, product_id: uuid.UUID) -> OwnProductResponse:
        """Take a published product off sale. It can be published again."""
        product = await self._own(seller_id, product_id, for_update=True)
        if product.status != ProductStatus.PUBLISHED:
            raise ProductStatusConflictError("Only a published product can be archived")
        product.status = ProductStatus.ARCHIVED.value
        await self._session.commit()
        logger.info("product archived", extra={"product_id": str(product.id)})
        return await self._own_response(product)

    async def delete_product(self, *, seller_id: uuid.UUID, product_id: uuid.UUID) -> None:
        """Delete a draft that was never published. Anything that has been on
        sale is archived instead, so later orders can still refer to it."""
        product = await self._own(seller_id, product_id, for_update=True)
        if product.published_at is not None:
            raise ProductNotDeletableError()
        images = await self._repository.list_images([product.id])
        await self._repository.delete(product)
        await self._session.commit()
        for image in images:
            await self._discard_image(image.storage_public_id, product_id)
        logger.info("product deleted", extra={"product_id": str(product_id)})

    # ── Images of a seller's own product ─────────────────────────────────

    async def add_image(
        self, *, seller_id: uuid.UUID, product_id: uuid.UUID, content: bytes
    ) -> OwnProductResponse:
        product = await self._own(seller_id, product_id, for_update=True)
        images = await self._repository.list_images([product.id])
        if len(images) >= IMAGES_PER_PRODUCT_MAX:
            raise TooManyProductImagesError(
                f"A product can have at most {IMAGES_PER_PRODUCT_MAX} images"
            )
        if len(content) > IMAGE_MAX_BYTES:
            raise ProductImageTooLargeError(
                f"The image is larger than {IMAGE_MAX_BYTES // (1024 * 1024)} MB"
            )
        if not content.startswith(IMAGE_SIGNATURES):
            raise InvalidProductImageError()

        try:
            stored = await self._file_storage.upload_public_image(
                content, folder=f"muhuze/products/{product.id}"
            )
        except FileStorageError as exc:
            logger.exception("product image upload failed", extra={"product_id": str(product.id)})
            raise ImageStorageUnavailableError() from exc
        await self._repository.add_image(
            ProductImage(
                product_id=product.id,
                storage_public_id=stored.public_id,
                storage_format=stored.format,
                width=stored.width,
                height=stored.height,
                # After the current last image.
                sort_order=max((image.sort_order for image in images), default=-1) + 1,
            )
        )
        await self._session.commit()
        logger.info("product image added", extra={"product_id": str(product.id)})
        return await self._own_response(product)

    async def delete_image(
        self, *, seller_id: uuid.UUID, product_id: uuid.UUID, image_id: uuid.UUID
    ) -> OwnProductResponse:
        product = await self._own(seller_id, product_id, for_update=True)
        image = await self._repository.get_image(product.id, image_id)
        if image is None:
            raise ProductImageNotFoundError()
        public_id = image.storage_public_id
        await self._repository.delete_image(image)
        if product.status == ProductStatus.PUBLISHED:
            # A published product keeps at least one image.
            await self._require_publishable(product)
        await self._session.commit()
        await self._discard_image(public_id, product.id)
        return await self._own_response(product)

    async def reorder_images(
        self, *, seller_id: uuid.UUID, product_id: uuid.UUID, image_ids: list[uuid.UUID]
    ) -> OwnProductResponse:
        """Put the images in the given order. The first becomes the main image."""
        product = await self._own(seller_id, product_id, for_update=True)
        images = {image.id: image for image in await self._repository.list_images([product.id])}
        if len(image_ids) != len(images) or set(image_ids) != set(images):
            raise InvalidImageOrderError()
        for position, image_id in enumerate(image_ids):
            images[image_id].sort_order = position
        await self._session.commit()
        return await self._own_response(product)

    # ── What buyers see ──────────────────────────────────────────────────

    async def list_public_products(
        self, pagination: PaginationParams, filters: PublicProductFilters
    ) -> Page[ProductSummaryResponse]:
        products, total = await self._repository.list_products(
            pagination,
            sort=filters.sort,
            seller_id=filters.seller_id,
            category_id=filters.category_id,
            search=_search(filters.q),
            min_price=filters.min_price,
            max_price=filters.max_price,
            visible_to_buyers=(open_shop_ids(), visible_category_ids()),
        )
        return await self._summary_page(products, total, pagination)

    async def get_public_product(self, product_id: uuid.UUID) -> PublicProductResponse:
        """A product as a buyer sees it. Anything not on sale right now, for
        whatever reason, is simply "not found"."""
        product = await self._repository.get(product_id)
        if (
            product is None
            or product.status != ProductStatus.PUBLISHED
            or product.hidden_by_staff_at is not None
        ):
            raise ProductNotFoundError()
        try:
            shop = await self._sellers.get_open_shop(product.seller_id)
        except SellerNotFoundError as exc:
            raise ProductNotFoundError() from exc
        category = await self._categories.get_category_definition(product.category_id)
        if not category.is_active:
            raise ProductNotFoundError()

        detail = await self._detail(product, category, active_only=True)
        return PublicProductResponse(
            **detail.model_dump(), shop=ShopSummaryResponse(id=shop.id, name=shop.business_name)
        )

    # ── Staff ────────────────────────────────────────────────────────────

    async def list_all_products(
        self, pagination: PaginationParams, filters: StaffProductFilters
    ) -> Page[ProductSummaryResponse]:
        products, total = await self._repository.list_products(
            pagination,
            sort=filters.sort,
            seller_id=filters.seller_id,
            category_id=filters.category_id,
            status=filters.status.value if filters.status else None,
            search=_search(filters.q),
        )
        return await self._summary_page(products, total, pagination)

    async def get_any_product(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self._existing(product_id)
        category = await self._categories.get_category_definition(product.category_id)
        return await self._detail(product, category, active_only=False)

    async def hide_product(
        self, *, product_id: uuid.UUID, staff_id: uuid.UUID
    ) -> ProductSummaryResponse:
        """Hide a product that breaks the rules. Buyers stop seeing it at
        once, and its seller cannot publish it."""
        product = await self._existing(product_id, for_update=True)
        if product.hidden_by_staff_at is None:
            product.hidden_by_staff_at = utc_now()
        await self._session.commit()
        logger.info(
            "product hidden by staff",
            extra={"product_id": str(product.id), "by_account_id": str(staff_id)},
        )
        return (await self._summaries([product]))[0]

    async def restore_product(
        self, *, product_id: uuid.UUID, staff_id: uuid.UUID
    ) -> ProductSummaryResponse:
        product = await self._existing(product_id, for_update=True)
        product.hidden_by_staff_at = None
        await self._session.commit()
        logger.info(
            "product restored by staff",
            extra={"product_id": str(product.id), "by_account_id": str(staff_id)},
        )
        return (await self._summaries([product]))[0]

    # ── Loading and ownership ────────────────────────────────────────────

    async def _existing(self, product_id: uuid.UUID, *, for_update: bool = False) -> Product:
        product = await self._repository.get(product_id, for_update=for_update)
        if product is None:
            raise ProductNotFoundError()
        return product

    async def _own(
        self, seller_id: uuid.UUID, product_id: uuid.UUID, *, for_update: bool = False
    ) -> Product:
        """The ownership check: another shop's product is "not found"."""
        product = await self._repository.get(product_id, for_update=for_update)
        if product is None or product.seller_id != seller_id:
            raise ProductNotFoundError()
        return product

    async def _unique_slug(
        self, seller_id: uuid.UUID, name: str, *, except_id: uuid.UUID | None = None
    ) -> str:
        base = slugify(name, max_length=SLUG_BASE_MAX_LENGTH) or "product"
        taken = await self._repository.slugs_starting_with(seller_id, base, except_id=except_id)
        return unique_among(base, taken)

    # ── Attribute values ─────────────────────────────────────────────────

    async def _set_attribute_values(
        self,
        product: Product,
        category: CategoryResponse,
        submitted: dict[str, object],
        *,
        current: list[ProductAttributeValue],
    ) -> None:
        """Validate the submitted values against the category and store them.
        Only the attributes that were submitted are touched; null clears one.
        Every problem is reported at once."""
        by_code = {attribute.code: attribute for attribute in category.attributes}
        current_options = {value.option_id for value in current if value.option_id is not None}
        rows: list[ProductAttributeValue] = []
        touched: list[uuid.UUID] = []
        problems: list[str] = []

        for code, raw in submitted.items():
            attribute = by_code.get(code)
            if attribute is None:
                problems.append(f"{code}: is not an attribute of this category")
                continue
            touched.append(attribute.id)
            if raw is None:
                continue  # clear it
            if not attribute.is_active:
                problems.append(f"{code}: is no longer used")
                continue
            try:
                rows.extend(_to_rows(product.id, attribute, raw, current_options))
            except ValueError as exc:
                problems.append(f"{code}: {exc}")

        if problems:
            raise InvalidProductAttributesError("; ".join(problems))
        await self._repository.delete_values(product.id, attribute_ids=touched)
        await self._repository.add_values(rows)

    # ── Publishing rules ─────────────────────────────────────────────────

    async def _publish_blockers(
        self, product: Product, category: CategoryResponse | None = None
    ) -> list[str]:
        """Everything that stops this product being on sale (README §7)."""
        if category is None:
            category = await self._categories.get_category_definition(product.category_id)
        valued = {value.attribute_id for value in await self._repository.list_values(product.id)}
        images = await self._repository.list_images([product.id])

        blockers = []
        if not category.is_active:
            blockers.append("Its category is switched off")
        blockers.extend(
            f"Missing required attribute: {attribute.name}"
            for attribute in category.attributes
            if attribute.is_active and attribute.is_required and attribute.id not in valued
        )
        if not images:
            blockers.append("Add at least one image")
        return blockers

    async def _require_publishable(
        self, product: Product, category: CategoryResponse | None = None
    ) -> None:
        blockers = await self._publish_blockers(product, category)
        if blockers:
            raise ProductNotPublishableError("; ".join(blockers))

    # ── Responses ────────────────────────────────────────────────────────

    async def _own_response(
        self, product: Product, category: CategoryResponse | None = None
    ) -> OwnProductResponse:
        if category is None:
            category = await self._categories.get_category_definition(product.category_id)
        detail = await self._detail(product, category, active_only=False)
        return OwnProductResponse(
            **detail.model_dump(), publish_blockers=await self._publish_blockers(product, category)
        )

    async def _detail(
        self, product: Product, category: CategoryResponse, *, active_only: bool
    ) -> ProductResponse:
        images = await self._repository.list_images([product.id])
        values = await self._repository.list_values(product.id)
        image_responses = [self._image_response(image) for image in images]
        return ProductResponse(
            **ProductSummaryResponse.model_validate(product).model_dump(exclude={"main_image_url"}),
            main_image_url=image_responses[0].url if image_responses else None,
            description=product.description,
            images=image_responses,
            attributes=_attribute_values(category, values, active_only=active_only),
        )

    async def _summaries(self, products: list[Product]) -> list[ProductSummaryResponse]:
        """One extra query for the main images of the whole page."""
        main_image: dict[uuid.UUID, ProductImage] = {}
        for image in await self._repository.list_images([product.id for product in products]):
            main_image.setdefault(image.product_id, image)  # first = lowest sort_order
        summaries = []
        for product in products:
            summary = ProductSummaryResponse.model_validate(product)
            image = main_image.get(product.id)
            if image is not None:
                summary.main_image_url = self._image_response(image).url
            summaries.append(summary)
        return summaries

    async def _summary_page(
        self, products: list[Product], total: int, pagination: PaginationParams
    ) -> Page[ProductSummaryResponse]:
        return Page[ProductSummaryResponse].build(
            await self._summaries(products), total, pagination
        )

    def _image_response(self, image: ProductImage) -> ProductImageResponse:
        try:
            url = self._file_storage.public_image_url(image.storage_public_id, image.storage_format)
        except FileStorageError as exc:
            raise ImageStorageUnavailableError() from exc
        return ProductImageResponse(
            id=image.id,
            url=url,
            width=image.width,
            height=image.height,
            sort_order=image.sort_order,
        )

    async def _discard_image(self, public_id: str, product_id: uuid.UUID) -> None:
        """Remove a file that no row points to any more. A failure is logged,
        not raised: the database is already correct."""
        try:
            await self._file_storage.delete_public_image(public_id)
        except FileStorageError:
            logger.exception(
                "orphaned product image left in storage", extra={"product_id": str(product_id)}
            )


def _money(amount: Decimal) -> Decimal:
    """Always two decimal places, as the column stores it: 850000 → 850000.00."""
    return amount.quantize(Decimal("0.01"))


def _search(query: str | None) -> str | None:
    return query.strip() or None if query else None


def _to_rows(
    product_id: uuid.UUID,
    attribute: AttributeResponse,
    raw: object,
    current_options: set[uuid.UUID],
) -> list[ProductAttributeValue]:
    """Turn one submitted value into rows, or raise ValueError saying what is
    wrong in words a seller can act on."""

    def row(**value: object) -> ProductAttributeValue:
        return ProductAttributeValue(product_id=product_id, attribute_id=attribute.id, **value)

    match attribute.data_type:
        case AttributeDataType.TEXT:
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError("must be text")
            if len(raw.strip()) > ATTRIBUTE_TEXT_MAX_LENGTH:
                raise ValueError(f"must be at most {ATTRIBUTE_TEXT_MAX_LENGTH} characters")
            return [row(value_text=raw.strip())]

        case AttributeDataType.NUMBER:
            # bool is a subclass of int in Python; true/false is not a number here.
            if isinstance(raw, bool) or not isinstance(raw, int | float):
                raise ValueError("must be a number")
            try:
                number = Decimal(str(raw)).quantize(ATTRIBUTE_NUMBER_QUANTUM)
            except InvalidOperation as exc:
                raise ValueError("must be a number") from exc
            if not number.is_finite() or abs(number) > ATTRIBUTE_NUMBER_LIMIT:
                raise ValueError("is out of range")
            return [row(value_number=number)]

        case AttributeDataType.BOOLEAN:
            if not isinstance(raw, bool):
                raise ValueError("must be true or false")
            return [row(value_boolean=raw)]

        case AttributeDataType.SELECT:
            return [row(option_id=_option_id(attribute, raw, current_options))]

        case AttributeDataType.MULTI_SELECT:
            if not isinstance(raw, list) or not raw:
                raise ValueError("must be a list with at least one option")
            option_ids = [_option_id(attribute, item, current_options) for item in raw]
            if len(option_ids) != len(set(option_ids)):
                raise ValueError("must not repeat an option")
            return [row(option_id=option_id) for option_id in option_ids]

    raise ValueError("has an unsupported type")


def _option_id(
    attribute: AttributeResponse, raw: object, current_options: set[uuid.UUID]
) -> uuid.UUID:
    try:
        option_id = uuid.UUID(raw) if isinstance(raw, str) else None
    except ValueError:
        option_id = None
    option = next((o for o in attribute.options if o.id == option_id), None)
    # A retired option stays valid for a product that already has it.
    if option is None or (not option.is_active and option.id not in current_options):
        raise ValueError("must be one of this attribute's options (send the option id)")
    return option.id


def _attribute_values(
    category: CategoryResponse, values: list[ProductAttributeValue], *, active_only: bool
) -> list[ProductAttributeValueResponse]:
    """The product's values in the category's display order."""
    rows_of: dict[uuid.UUID, list[ProductAttributeValue]] = {}
    for value in values:
        rows_of.setdefault(value.attribute_id, []).append(value)

    result = []
    for attribute in category.attributes:
        rows = rows_of.get(attribute.id)
        if not rows or (active_only and not attribute.is_active):
            continue
        options = {option.id: option for option in attribute.options}
        chosen = [
            OptionValueResponse(id=option.id, value=option.value)
            for option in attribute.options  # the attribute's own option order
            if any(row.option_id == option.id for row in rows) and option.id in options
        ]
        first = rows[0]
        value: object
        match attribute.data_type:
            case AttributeDataType.TEXT:
                value = first.value_text
            case AttributeDataType.NUMBER:
                value = _plain_number(first.value_number)
            case AttributeDataType.BOOLEAN:
                value = first.value_boolean
            case AttributeDataType.SELECT:
                value = chosen[0] if chosen else None
            case _:
                value = chosen
        if value is None:
            continue
        result.append(
            ProductAttributeValueResponse(
                code=attribute.code,
                name=attribute.name,
                data_type=attribute.data_type,
                unit=attribute.unit,
                value=value,
            )
        )
    return result


def _plain_number(number: Decimal) -> int | float:
    """128.0000 → 128; 6.7000 → 6.7. Measurements, not money."""
    return int(number) if number == number.to_integral_value() else float(number)
