from fastapi import APIRouter, Depends, Query, status

from app.core.config import settings
from app.core.dependencies import require_admin
from app.schemas.common import ApiResponse, PageData
from app.schemas.product import ProductCard, ProductCreate, ProductDetail, ProductUpdate
from app.services.product_service import product_service


router = APIRouter(
    prefix=f"{settings.api_prefix}/admin/products",
    tags=["Admin - Products"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=ApiResponse[PageData[ProductCard]])
def get_all_products(
    q: str | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Includes hidden (is_active=false) products."""
    data = product_service.list_products(
        page=page, page_size=page_size, q=q, category=category, include_inactive=True
    )
    return {"success": True, "message": "Products fetched successfully", "data": data}


@router.get("/{product_id}", response_model=ApiResponse[ProductDetail])
def get_product(product_id: int):
    return {
        "success": True,
        "message": "Product fetched successfully",
        "data": product_service.get_product(product_id, admin=True),
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[ProductDetail])
def create_product(product_data: ProductCreate):
    return {"success": True, "message": "Product created", "data": product_service.create_product(product_data)}


@router.put("/{product_id}", response_model=ApiResponse[ProductDetail])
def update_product(product_id: int, product_data: ProductUpdate):
    """Send only the fields you want to change."""
    return {
        "success": True,
        "message": "Product updated",
        "data": product_service.update_product(product_id, product_data),
    }


@router.delete("/{product_id}", response_model=ApiResponse)
def delete_product(product_id: int):
    """Hides the product (is_active=false). Old orders keep their details."""
    product_service.delete_product(product_id)
    return {"success": True, "message": "Product deleted", "data": None}
