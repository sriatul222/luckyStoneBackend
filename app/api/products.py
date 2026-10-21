from fastapi import APIRouter, Depends, Query, status

from app.core.config import settings
from app.core.dependencies import get_current_user, get_optional_user
from app.schemas.catalog import Metal
from app.schemas.common import ApiResponse, PageData
from app.schemas.product import (
    Gender,
    ProductCard,
    ProductDetail,
    ProductSort,
    ReviewCreate,
    ReviewResponse,
)
from app.services.product_service import product_service


router = APIRouter(prefix=f"{settings.api_prefix}/products", tags=["Products"])


@router.get("", response_model=ApiResponse[PageData[ProductCard]])
def get_products(
    q: str | None = Query(None, description="Search in name, description, SKU, category"),
    category: str | None = Query(None, description="Category slug, e.g. rings"),
    collection: str | None = Query(None, description="Collection slug, e.g. bridal"),
    metal: Metal | None = None,
    purity: str | None = Query(None, description="e.g. 22K, 18K, 925"),
    gender: Gender | None = None,
    occasion: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    featured: bool | None = None,
    in_stock: bool | None = None,
    sort: ProductSort = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    data = product_service.list_products(
        page=page,
        page_size=page_size,
        q=q,
        category=category,
        collection=collection,
        metal=metal,
        purity=purity,
        gender=gender,
        occasion=occasion,
        min_price=min_price,
        max_price=max_price,
        featured=featured,
        in_stock=in_stock,
        sort=sort,
    )
    return {"success": True, "message": "Products fetched successfully", "data": data}


@router.get("/{product_id}", response_model=ApiResponse[ProductDetail])
def get_product(product_id: int, user: dict | None = Depends(get_optional_user)):
    """Works for guests. Send the token to also get is_wishlisted."""
    return {
        "success": True,
        "message": "Product fetched successfully",
        "data": product_service.get_product(product_id, user),
    }


@router.get("/{product_id}/reviews", response_model=ApiResponse[PageData[ReviewResponse]])
def get_reviews(
    product_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return {
        "success": True,
        "message": "Reviews fetched successfully",
        "data": product_service.get_reviews(product_id, page, page_size),
    }


@router.post("/{product_id}/reviews", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[ReviewResponse])
def add_review(product_id: int, review_data: ReviewCreate, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Review saved successfully",
        "data": product_service.add_review(user, product_id, review_data),
    }
