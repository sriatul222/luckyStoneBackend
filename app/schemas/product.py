from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.catalog import SLUG, Metal


Gender = Literal["women", "men", "kids", "unisex"]
ProductSort = Literal["newest", "price_low_to_high", "price_high_to_low", "popular", "rating"]


class ProductCard(BaseModel):
    """Small product shape for lists, home, wishlist and cart."""

    id: int
    name: str
    slug: str
    sku: str
    category_name: str
    category_slug: str
    metal: str
    purity: str
    net_weight: float
    gross_weight: float
    image_url: str
    price: float
    original_price: float
    discount_percent: float
    rating: float
    review_count: int
    in_stock: bool
    is_featured: bool


class PriceBreakup(BaseModel):
    metal_rate: float
    metal_value: float
    making_charges: float
    making_discount: float
    stone_value: float
    subtotal: float
    gst_percent: float
    gst: float
    total: float


class ProductDetail(ProductCard):
    description: str
    collection_name: str | None
    collection_slug: str | None
    image_urls: list[str]
    gender: str
    occasion: str
    sizes: list[str]
    stone_type: str
    stone_weight_carat: float
    stone_quality: str
    making_charge_percent: float
    stock: int
    is_active: bool
    is_wishlisted: bool
    price_breakup: PriceBreakup
    created_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., pattern=SLUG, max_length=220)
    sku: str = Field(..., min_length=2, max_length=50)
    description: str = ""
    category_id: int
    collection_id: int | None = None
    metal: Metal
    purity: str = Field(..., max_length=10, examples=["22K"])
    gross_weight: float = Field(..., gt=0)
    net_weight: float = Field(..., gt=0)
    making_charge_percent: float = Field(0, ge=0, le=100)
    making_discount_percent: float = Field(0, ge=0, le=100)
    stone_type: str = ""
    stone_weight_carat: float = Field(0, ge=0)
    stone_quality: str = ""
    stone_price: float = Field(0, ge=0)
    gender: Gender = "women"
    occasion: str = ""
    sizes: list[str] = []
    image_urls: list[str] = []
    stock: int = Field(0, ge=0)
    is_featured: bool = False
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    slug: str | None = Field(None, pattern=SLUG, max_length=220)
    sku: str | None = Field(None, min_length=2, max_length=50)
    description: str | None = None
    category_id: int | None = None
    collection_id: int | None = None
    metal: Metal | None = None
    purity: str | None = Field(None, max_length=10)
    gross_weight: float | None = Field(None, gt=0)
    net_weight: float | None = Field(None, gt=0)
    making_charge_percent: float | None = Field(None, ge=0, le=100)
    making_discount_percent: float | None = Field(None, ge=0, le=100)
    stone_type: str | None = None
    stone_weight_carat: float | None = Field(None, ge=0)
    stone_quality: str | None = None
    stone_price: float | None = Field(None, ge=0)
    gender: Gender | None = None
    occasion: str | None = None
    sizes: list[str] | None = None
    image_urls: list[str] | None = None
    stock: int | None = Field(None, ge=0)
    is_featured: bool | None = None
    is_active: bool | None = None


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    user_name: str
    rating: int
    comment: str
    created_at: datetime
