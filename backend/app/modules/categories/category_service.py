"""Categories: the sections of a seller's own shop, and the attributes the
products in each one are described by.
Rules are documented in docs/features/006_categories.md and README §7.2.

There is no shared marketplace tree. A category belongs to exactly one
seller, and every method that changes one takes the acting seller's id and
refuses anything that isn't theirs: a category of another shop looks exactly
like one that doesn't exist.
Every public method is one unit of work and commits it.
"""

import uuid

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.modules.categories.category_constants import (
    ATTRIBUTE_CODE_MAX_LENGTH,
    CATEGORY_SLUG_MAX_LENGTH,
    OPTION_DATA_TYPES,
    AttributeDataType,
)
from app.modules.categories.category_exceptions import (
    CategoryAttributeInUseError,
    CategoryAttributeNameTakenError,
    CategoryAttributeNotFoundError,
    CategoryAttributeOptionInUseError,
    CategoryAttributeOptionNotFoundError,
    CategoryAttributeOptionTakenError,
    CategoryHiddenByStaffError,
    CategoryInUseError,
    CategoryNameTakenError,
    CategoryNotFoundError,
    OptionsNotSupportedError,
    UnitNotSupportedError,
)
from app.modules.categories.category_model import (
    Category,
    CategoryAttribute,
    CategoryAttributeOption,
)
from app.modules.categories.category_repository import CategoryRepository
from app.modules.categories.category_schema import (
    AttributeCreateRequest,
    AttributeResponse,
    AttributeUpdateRequest,
    CategoryCreateRequest,
    CategoryResponse,
    CategorySummaryResponse,
    CategoryUpdateRequest,
    OptionCreateRequest,
    OptionResponse,
    OptionUpdateRequest,
    OwnCategoryFilters,
    StaffCategoryFilters,
)
from app.shared.responses.pagination import Page, PaginationParams
from app.shared.slugs import slugify, unique_among

logger = get_logger(__name__)

# Leaves room for a "-2", "-3" … suffix when two names give the same slug.
SLUG_BASE_MAX_LENGTH = CATEGORY_SLUG_MAX_LENGTH - 6
CODE_BASE_MAX_LENGTH = ATTRIBUTE_CODE_MAX_LENGTH - 6


def visible_category_ids() -> Select:
    """The ids of categories buyers may see, as a subquery for other
    features' list queries: `.where(Product.category_id.in_(visible_category_ids()))`.
    """
    return select(Category.id).where(Category.is_active.is_(True))


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = CategoryRepository(session)

    # ── Used by other features ───────────────────────────────────────────

    async def get_category_definition(self, category_id: uuid.UUID) -> CategoryResponse:
        """A category with ALL its attributes and options, active or not,
        whoever owns it. For features that validate or display data against
        it; callers do their own access checks."""
        return await self._category_response(await self._existing(category_id))

    # ── A seller's own categories ────────────────────────────────────────

    async def create_category(
        self, *, seller_id: uuid.UUID, payload: CategoryCreateRequest
    ) -> CategoryResponse:
        if await self._repository.name_exists(seller_id, payload.name):
            raise CategoryNameTakenError()
        category = Category(
            seller_id=seller_id,
            name=payload.name,
            slug=await self._unique_slug(seller_id, payload.name),
            description=payload.description or None,
            sort_order=payload.sort_order,
        )
        try:
            await self._repository.add(category)
        except IntegrityError as exc:
            # Lost a race with a concurrent request using the same name.
            await self._session.rollback()
            raise CategoryNameTakenError() from exc
        await self._session.commit()
        logger.info(
            "category created",
            extra={"category_id": str(category.id), "seller_id": str(seller_id)},
        )
        return await self._category_response(category)

    async def list_own_categories(
        self, *, seller_id: uuid.UUID, pagination: PaginationParams, filters: OwnCategoryFilters
    ) -> Page[CategorySummaryResponse]:
        categories, total = await self._repository.list_categories(
            pagination, seller_id=seller_id, is_active=filters.is_active, search=_search(filters.q)
        )
        return _summary_page(categories, total, pagination)

    async def get_own_category(
        self, *, seller_id: uuid.UUID, category_id: uuid.UUID
    ) -> CategoryResponse:
        return await self._category_response(await self._own(seller_id, category_id))

    async def update_category(
        self, *, seller_id: uuid.UUID, category_id: uuid.UUID, payload: CategoryUpdateRequest
    ) -> CategoryResponse:
        category = await self._own(seller_id, category_id, for_update=True)
        changes = payload.model_dump(exclude_unset=True)

        new_name = changes.get("name")
        if new_name is not None and new_name != category.name:
            if await self._repository.name_exists(seller_id, new_name, except_id=category.id):
                raise CategoryNameTakenError()
            category.name = new_name
            category.slug = await self._unique_slug(seller_id, new_name, except_id=category.id)
        if "description" in changes:
            category.description = changes["description"] or None
        if "sort_order" in changes:
            category.sort_order = changes["sort_order"]
        if "is_active" in changes:
            if changes["is_active"] and category.hidden_by_staff_at is not None:
                raise CategoryHiddenByStaffError()
            category.is_active = changes["is_active"]

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise CategoryNameTakenError() from exc
        logger.info("category updated", extra={"category_id": str(category.id)})
        return await self._category_response(category)

    async def delete_category(self, *, seller_id: uuid.UUID, category_id: uuid.UUID) -> None:
        """Remove a category with its attributes and options. A category that
        still has products is refused: the database's foreign keys are what
        say "in use", so this feature needs to know nothing about products."""
        category = await self._own(seller_id, category_id, for_update=True)
        try:
            await self._repository.delete(category)
        except IntegrityError as exc:
            await self._session.rollback()
            raise CategoryInUseError() from exc
        await self._session.commit()
        logger.info(
            "category deleted", extra={"category_id": str(category_id), "seller_id": str(seller_id)}
        )

    # ── Attributes of a seller's own category ────────────────────────────

    async def add_attribute(
        self, *, seller_id: uuid.UUID, category_id: uuid.UUID, payload: AttributeCreateRequest
    ) -> AttributeResponse:
        category = await self._own(seller_id, category_id, for_update=True)
        if await self._repository.attribute_name_exists(category.id, payload.name):
            raise CategoryAttributeNameTakenError()

        attribute = CategoryAttribute(
            category_id=category.id,
            code=unique_among(
                slugify(payload.name, separator="_", max_length=CODE_BASE_MAX_LENGTH)
                or "attribute",
                await self._repository.attribute_codes(category.id),
                separator="_",
            ),
            name=payload.name,
            data_type=payload.data_type.value,
            unit=payload.unit,
            is_required=payload.is_required,
            is_filterable=payload.is_filterable,
            sort_order=payload.sort_order,
        )
        await self._repository.add_attribute(attribute)
        options = [
            CategoryAttributeOption(attribute_id=attribute.id, value=value, sort_order=position)
            for position, value in enumerate(payload.options)
        ]
        await self._repository.add_options(options)
        await self._session.commit()
        logger.info(
            "category attribute added",
            extra={"category_id": str(category.id), "attribute_id": str(attribute.id)},
        )
        return _attribute_response(attribute, options)

    async def update_attribute(
        self,
        *,
        seller_id: uuid.UUID,
        category_id: uuid.UUID,
        attribute_id: uuid.UUID,
        payload: AttributeUpdateRequest,
    ) -> AttributeResponse:
        attribute = await self._own_attribute(seller_id, category_id, attribute_id)
        changes = payload.model_dump(exclude_unset=True)

        new_name = changes.get("name")
        if new_name is not None and new_name != attribute.name:
            if await self._repository.attribute_name_exists(
                attribute.category_id, new_name, except_id=attribute.id
            ):
                raise CategoryAttributeNameTakenError()
            # The code deliberately stays as it is: it is the stable key.
            attribute.name = new_name
        if "unit" in changes:
            if changes["unit"] is not None and attribute.data_type != AttributeDataType.NUMBER:
                raise UnitNotSupportedError()
            attribute.unit = changes["unit"]
        for field in ("is_required", "is_filterable", "sort_order", "is_active"):
            if field in changes:
                setattr(attribute, field, changes[field])

        await self._session.commit()
        logger.info("category attribute updated", extra={"attribute_id": str(attribute.id)})
        return _attribute_response(attribute, await self._repository.list_options([attribute.id]))

    async def delete_attribute(
        self, *, seller_id: uuid.UUID, category_id: uuid.UUID, attribute_id: uuid.UUID
    ) -> None:
        """Remove an attribute and its options. Refused once products have
        values for it; it can be switched off instead."""
        attribute = await self._own_attribute(seller_id, category_id, attribute_id)
        try:
            await self._repository.delete_attribute(attribute)
        except IntegrityError as exc:
            await self._session.rollback()
            raise CategoryAttributeInUseError() from exc
        await self._session.commit()
        logger.info("category attribute deleted", extra={"attribute_id": str(attribute_id)})

    # ── Options of a select attribute ────────────────────────────────────

    async def add_option(
        self,
        *,
        seller_id: uuid.UUID,
        category_id: uuid.UUID,
        attribute_id: uuid.UUID,
        payload: OptionCreateRequest,
    ) -> AttributeResponse:
        attribute = await self._own_attribute(seller_id, category_id, attribute_id)
        if attribute.data_type not in OPTION_DATA_TYPES:
            raise OptionsNotSupportedError()
        if await self._repository.option_value_exists(attribute.id, payload.value):
            raise CategoryAttributeOptionTakenError()
        existing = await self._repository.list_options([attribute.id])
        sort_order = payload.sort_order
        if sort_order is None:
            # At the end of the list.
            sort_order = max((option.sort_order for option in existing), default=-1) + 1
        await self._repository.add_options(
            [
                CategoryAttributeOption(
                    attribute_id=attribute.id, value=payload.value, sort_order=sort_order
                )
            ]
        )
        await self._session.commit()
        return _attribute_response(attribute, await self._repository.list_options([attribute.id]))

    async def update_option(
        self,
        *,
        seller_id: uuid.UUID,
        category_id: uuid.UUID,
        attribute_id: uuid.UUID,
        option_id: uuid.UUID,
        payload: OptionUpdateRequest,
    ) -> AttributeResponse:
        attribute = await self._own_attribute(seller_id, category_id, attribute_id)
        option = await self._option(attribute, option_id)
        changes = payload.model_dump(exclude_unset=True)

        new_value = changes.get("value")
        if new_value is not None and new_value != option.value:
            if await self._repository.option_value_exists(
                attribute.id, new_value, except_id=option.id
            ):
                raise CategoryAttributeOptionTakenError()
            option.value = new_value
        for field in ("sort_order", "is_active"):
            if field in changes:
                setattr(option, field, changes[field])

        await self._session.commit()
        return _attribute_response(attribute, await self._repository.list_options([attribute.id]))

    async def delete_option(
        self,
        *,
        seller_id: uuid.UUID,
        category_id: uuid.UUID,
        attribute_id: uuid.UUID,
        option_id: uuid.UUID,
    ) -> AttributeResponse:
        attribute = await self._own_attribute(seller_id, category_id, attribute_id)
        option = await self._option(attribute, option_id)
        try:
            await self._repository.delete_option(option)
        except IntegrityError as exc:
            await self._session.rollback()
            raise CategoryAttributeOptionInUseError() from exc
        await self._session.commit()
        return _attribute_response(attribute, await self._repository.list_options([attribute.id]))

    # ── What buyers see ──────────────────────────────────────────────────

    async def list_shop_categories(
        self, *, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[CategoryResponse]:
        """A shop's active categories with their active attributes and options.
        The caller has already checked that the shop is open to buyers."""
        categories, total = await self._repository.list_categories(
            pagination, seller_id=seller_id, is_active=True, search=None
        )
        items = await self._category_responses(categories, active_only=True)
        return Page[CategoryResponse].build(items, total, pagination)

    # ── Staff ────────────────────────────────────────────────────────────

    async def list_all_categories(
        self, pagination: PaginationParams, filters: StaffCategoryFilters
    ) -> Page[CategorySummaryResponse]:
        categories, total = await self._repository.list_categories(
            pagination,
            seller_id=filters.seller_id,
            is_active=filters.is_active,
            search=_search(filters.q),
        )
        return _summary_page(categories, total, pagination)

    async def hide_category(
        self, *, category_id: uuid.UUID, staff_id: uuid.UUID
    ) -> CategorySummaryResponse:
        """Hide a category that breaks the rules. The seller cannot undo it."""
        category = await self._existing(category_id, for_update=True)
        category.is_active = False
        if category.hidden_by_staff_at is None:
            category.hidden_by_staff_at = utc_now()
        await self._session.commit()
        logger.info(
            "category hidden by staff",
            extra={"category_id": str(category.id), "by_account_id": str(staff_id)},
        )
        return CategorySummaryResponse.model_validate(category)

    async def restore_category(
        self, *, category_id: uuid.UUID, staff_id: uuid.UUID
    ) -> CategorySummaryResponse:
        category = await self._existing(category_id, for_update=True)
        if category.hidden_by_staff_at is not None:
            category.hidden_by_staff_at = None
            category.is_active = True
        await self._session.commit()
        logger.info(
            "category restored by staff",
            extra={"category_id": str(category.id), "by_account_id": str(staff_id)},
        )
        return CategorySummaryResponse.model_validate(category)

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _existing(self, category_id: uuid.UUID, *, for_update: bool = False) -> Category:
        category = await self._repository.get(category_id, for_update=for_update)
        if category is None:
            raise CategoryNotFoundError()
        return category

    async def _own(
        self, seller_id: uuid.UUID, category_id: uuid.UUID, *, for_update: bool = False
    ) -> Category:
        """The ownership check: another shop's category is "not found"."""
        category = await self._repository.get(category_id, for_update=for_update)
        if category is None or category.seller_id != seller_id:
            raise CategoryNotFoundError()
        return category

    async def _own_attribute(
        self, seller_id: uuid.UUID, category_id: uuid.UUID, attribute_id: uuid.UUID
    ) -> CategoryAttribute:
        category = await self._own(seller_id, category_id, for_update=True)
        attribute = await self._repository.get_attribute(category.id, attribute_id)
        if attribute is None:
            raise CategoryAttributeNotFoundError()
        return attribute

    async def _option(
        self, attribute: CategoryAttribute, option_id: uuid.UUID
    ) -> CategoryAttributeOption:
        option = await self._repository.get_option(attribute.id, option_id)
        if option is None:
            raise CategoryAttributeOptionNotFoundError()
        return option

    async def _unique_slug(
        self, seller_id: uuid.UUID, name: str, *, except_id: uuid.UUID | None = None
    ) -> str:
        base = slugify(name, separator="-", max_length=SLUG_BASE_MAX_LENGTH) or "category"
        taken = await self._repository.slugs_starting_with(seller_id, base, except_id=except_id)
        return unique_among(base, taken, separator="-")

    async def _category_response(self, category: Category) -> CategoryResponse:
        (response,) = await self._category_responses([category], active_only=False)
        return response

    async def _category_responses(
        self, categories: list[Category], *, active_only: bool
    ) -> list[CategoryResponse]:
        """Two queries for any number of categories: their attributes, then
        those attributes' options."""
        attributes = await self._repository.list_attributes(
            [category.id for category in categories], active_only=active_only
        )
        options = await self._repository.list_options(
            [attribute.id for attribute in attributes], active_only=active_only
        )
        options_of: dict[uuid.UUID, list[CategoryAttributeOption]] = {}
        for option in options:
            options_of.setdefault(option.attribute_id, []).append(option)
        attributes_of: dict[uuid.UUID, list[AttributeResponse]] = {}
        for attribute in attributes:
            attributes_of.setdefault(attribute.category_id, []).append(
                _attribute_response(attribute, options_of.get(attribute.id, []))
            )
        return [
            CategoryResponse(
                **CategorySummaryResponse.model_validate(category).model_dump(),
                attributes=attributes_of.get(category.id, []),
            )
            for category in categories
        ]


def _attribute_response(
    attribute: CategoryAttribute, options: list[CategoryAttributeOption]
) -> AttributeResponse:
    return AttributeResponse(
        id=attribute.id,
        code=attribute.code,
        name=attribute.name,
        data_type=attribute.data_type,
        unit=attribute.unit,
        is_required=attribute.is_required,
        is_filterable=attribute.is_filterable,
        sort_order=attribute.sort_order,
        is_active=attribute.is_active,
        options=[OptionResponse.model_validate(option) for option in options],
    )


def _summary_page(
    categories: list[Category], total: int, pagination: PaginationParams
) -> Page[CategorySummaryResponse]:
    items = [CategorySummaryResponse.model_validate(category) for category in categories]
    return Page[CategorySummaryResponse].build(items, total, pagination)


def _search(query: str | None) -> str | None:
    return query.strip() or None if query else None
