from fastapi import APIRouter, Query

from app.core.config import settings
from app.schemas.catalog import (
    BannerResponse,
    CategoryResponse,
    CollectionResponse,
    MetalRateResponse,
    StoreResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.shop import HomeData
from app.services.catalog_service import (
    banner_service,
    category_service,
    collection_service,
    metal_rate_service,
    store_service,
)
from app.services.shop_service import home_service


router = APIRouter(prefix=settings.api_prefix, tags=["Catalog"])


@router.get("/home", response_model=ApiResponse[HomeData])
def get_home():
    """Everything the home screen needs in one call."""
    return {"success": True, "message": "Home data fetched successfully", "data": home_service.get_home()}


@router.get("/metal-rates", response_model=ApiResponse[list[MetalRateResponse]])
def get_metal_rates():
    return {"success": True, "message": "Metal rates fetched successfully", "data": metal_rate_service.get_rates()}


@router.get("/categories", response_model=ApiResponse[list[CategoryResponse]])
def get_categories():
    return {"success": True, "message": "Categories fetched successfully", "data": category_service.get_all()}


@router.get("/collections", response_model=ApiResponse[list[CollectionResponse]])
def get_collections():
    return {"success": True, "message": "Collections fetched successfully", "data": collection_service.get_all()}


@router.get("/banners", response_model=ApiResponse[list[BannerResponse]])
def get_banners():
    return {"success": True, "message": "Banners fetched successfully", "data": banner_service.get_all()}


@router.get("/stores", response_model=ApiResponse[list[StoreResponse]])
def get_stores(city: str | None = Query(None, description="Filter by city, e.g. Kochi")):
    return {"success": True, "message": "Stores fetched successfully", "data": store_service.get_all(city=city)}
