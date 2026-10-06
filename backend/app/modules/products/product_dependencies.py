from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.categories.category_dependencies import get_category_service
from app.modules.categories.category_service import CategoryService
from app.modules.products.product_service import ProductService
from app.modules.sellers.seller_dependencies import get_seller_service
from app.modules.sellers.seller_service import SellerService


def get_product_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
) -> ProductService:
    return ProductService(
        session=session,
        category_service=category_service,
        seller_service=seller_service,
        file_storage=request.app.state.file_storage,
    )
