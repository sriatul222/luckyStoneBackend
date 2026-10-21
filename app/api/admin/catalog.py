from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.core.dependencies import require_admin
from app.schemas.catalog import (
    BannerCreate,
    BannerResponse,
    BannerUpdate,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    MetalRateResponse,
    MetalRatesUpdateRequest,
    StoreCreate,
    StoreResponse,
    StoreUpdate,
)
from app.schemas.common import ApiResponse
from app.services.catalog_service import (
    banner_service,
    category_service,
    collection_service,
    metal_rate_service,
    store_service,
)


router = APIRouter(
    prefix=f"{settings.api_prefix}/admin",
    tags=["Admin - Catalog"],
    dependencies=[Depends(require_admin)],
)


# ---------------- Metal rates ----------------

@router.put("/metal-rates", response_model=ApiResponse[list[MetalRateResponse]])
def update_metal_rates(rates_data: MetalRatesUpdateRequest):
    """Update today's rates. Every product price changes instantly."""
    return {
        "success": True,
        "message": "Metal rates updated successfully",
        "data": metal_rate_service.update_rates(rates_data),
    }


# ---------------- Categories ----------------

@router.get("/categories", response_model=ApiResponse[list[CategoryResponse]])
def get_all_categories():
    return {"success": True, "message": "Categories fetched successfully", "data": category_service.get_all(active_only=False)}


@router.post("/categories", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[CategoryResponse])
def create_category(category_data: CategoryCreate):
    return {"success": True, "message": "Category created", "data": category_service.create(category_data.model_dump())}


@router.put("/categories/{category_id}", response_model=ApiResponse[CategoryResponse])
def update_category(category_id: int, category_data: CategoryUpdate):
    return {
        "success": True,
        "message": "Category updated",
        "data": category_service.update(category_id, category_data.model_dump(exclude_unset=True)),
    }


@router.delete("/categories/{category_id}", response_model=ApiResponse)
def delete_category(category_id: int):
    category_service.delete(category_id)
    return {"success": True, "message": "Category deleted", "data": None}


# ---------------- Collections ----------------

@router.get("/collections", response_model=ApiResponse[list[CollectionResponse]])
def get_all_collections():
    return {"success": True, "message": "Collections fetched successfully", "data": collection_service.get_all(active_only=False)}


@router.post("/collections", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[CollectionResponse])
def create_collection(collection_data: CollectionCreate):
    return {"success": True, "message": "Collection created", "data": collection_service.create(collection_data.model_dump())}


@router.put("/collections/{collection_id}", response_model=ApiResponse[CollectionResponse])
def update_collection(collection_id: int, collection_data: CollectionUpdate):
    return {
        "success": True,
        "message": "Collection updated",
        "data": collection_service.update(collection_id, collection_data.model_dump(exclude_unset=True)),
    }


@router.delete("/collections/{collection_id}", response_model=ApiResponse)
def delete_collection(collection_id: int):
    collection_service.delete(collection_id)
    return {"success": True, "message": "Collection deleted", "data": None}


# ---------------- Banners ----------------

@router.get("/banners", response_model=ApiResponse[list[BannerResponse]])
def get_all_banners():
    return {"success": True, "message": "Banners fetched successfully", "data": banner_service.get_all(active_only=False)}


@router.post("/banners", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[BannerResponse])
def create_banner(banner_data: BannerCreate):
    return {"success": True, "message": "Banner created", "data": banner_service.create(banner_data.model_dump())}


@router.put("/banners/{banner_id}", response_model=ApiResponse[BannerResponse])
def update_banner(banner_id: int, banner_data: BannerUpdate):
    return {
        "success": True,
        "message": "Banner updated",
        "data": banner_service.update(banner_id, banner_data.model_dump(exclude_unset=True)),
    }


@router.delete("/banners/{banner_id}", response_model=ApiResponse)
def delete_banner(banner_id: int):
    banner_service.delete(banner_id)
    return {"success": True, "message": "Banner deleted", "data": None}


# ---------------- Stores ----------------

@router.get("/stores", response_model=ApiResponse[list[StoreResponse]])
def get_all_stores():
    return {"success": True, "message": "Stores fetched successfully", "data": store_service.get_all(active_only=False)}


@router.post("/stores", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[StoreResponse])
def create_store(store_data: StoreCreate):
    return {"success": True, "message": "Store created", "data": store_service.create(store_data.model_dump())}


@router.put("/stores/{store_id}", response_model=ApiResponse[StoreResponse])
def update_store(store_id: int, store_data: StoreUpdate):
    return {
        "success": True,
        "message": "Store updated",
        "data": store_service.update(store_id, store_data.model_dump(exclude_unset=True)),
    }


@router.delete("/stores/{store_id}", response_model=ApiResponse)
def delete_store(store_id: int):
    store_service.delete(store_id)
    return {"success": True, "message": "Store deleted", "data": None}
