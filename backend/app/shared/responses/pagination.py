"""The standard pagination contract for collection endpoints.

Usage in a route:

    @router.get("", response_model=APIResponse[Page[ProductOut]])
    async def list_products(pagination: Annotated[PaginationParams, Query()]):
        page = await product_service.list_products(pagination)
        return success_response(data=page)

The repository applies `pagination.offset` / `pagination.limit` in SQL and
returns the matching total; the service builds `Page.build(...)`.
"""

from math import ceil
from typing import Self

from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="1-based page number")
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Page[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int = Field(description="Total matching records across all pages")
    total_pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PaginationParams) -> Self:
        return cls(
            items=items,
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=ceil(total / params.page_size) if total else 0,
        )
