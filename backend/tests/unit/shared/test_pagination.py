import pytest
from pydantic import ValidationError

from app.shared.responses.pagination import MAX_PAGE_SIZE, Page, PaginationParams


def test_defaults_and_offset() -> None:
    params = PaginationParams()
    assert (params.page, params.page_size, params.offset, params.limit) == (1, 20, 0, 20)
    assert PaginationParams(page=3, page_size=10).offset == 20


@pytest.mark.parametrize(
    "kwargs", [{"page": 0}, {"page_size": 0}, {"page_size": MAX_PAGE_SIZE + 1}]
)
def test_rejects_out_of_range_values(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        PaginationParams(**kwargs)


@pytest.mark.parametrize(("total", "expected_pages"), [(0, 0), (1, 1), (20, 1), (21, 2)])
def test_page_build_computes_total_pages(total: int, expected_pages: int) -> None:
    page = Page[int].build(items=[1], total=total, params=PaginationParams(page_size=20))
    assert page.total == total
    assert page.total_pages == expected_pages
    assert (page.page, page.page_size) == (1, 20)
