"""Schemas for the logged-in shopping flow: wishlist, cart, addresses, orders."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.auth import INDIAN_MOBILE
from app.schemas.catalog import BannerResponse, CategoryResponse, CollectionResponse, MetalRateResponse
from app.schemas.product import ProductCard


# ---------- Home ----------

class HomeData(BaseModel):
    metal_rates: list[MetalRateResponse]
    banners: list[BannerResponse]
    categories: list[CategoryResponse]
    collections: list[CollectionResponse]
    featured: list[ProductCard]
    new_arrivals: list[ProductCard]


# ---------- Wishlist ----------

class WishlistAddRequest(BaseModel):
    product_id: int


# ---------- Cart ----------

class CartAddRequest(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1, le=10)
    size: str = Field("", max_length=10, description="Ring / bangle size, empty if not needed")


class CartUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=10)


class CartItem(BaseModel):
    id: int
    product: ProductCard
    size: str
    quantity: int
    unit_price: float
    line_total: float
    available_stock: int


class CartSummary(BaseModel):
    item_count: int
    total_quantity: int
    subtotal: float
    discount: float
    gst: float
    total: float


class CartData(BaseModel):
    items: list[CartItem]
    summary: CartSummary


# ---------- Addresses ----------

class AddressRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    mobile: str = Field(..., pattern=INDIAN_MOBILE)
    line1: str = Field(..., min_length=3, max_length=255)
    line2: str = Field("", max_length=255)
    landmark: str = Field("", max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., pattern=r"^[1-9]\d{5}$")
    address_type: Literal["home", "work", "other"] = "home"
    is_default: bool = False


class AddressResponse(BaseModel):
    id: int
    full_name: str
    mobile: str
    line1: str
    line2: str
    landmark: str
    city: str
    state: str
    pincode: str
    address_type: str
    is_default: bool
    created_at: datetime


# ---------- Orders ----------

OrderStatus = Literal["PLACED", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]


class PlaceOrderRequest(BaseModel):
    address_id: int
    payment_method: Literal["COD", "ONLINE"] = "COD"


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderItemResponse(BaseModel):
    id: int
    product_id: int | None
    product_name: str
    sku: str
    image_url: str
    metal: str
    purity: str
    net_weight: float
    size: str
    quantity: int
    unit_price: float
    line_total: float
    price_breakup: dict


class OrderSummaryResponse(BaseModel):
    id: int
    order_number: str
    status: str
    payment_method: str
    payment_status: str
    item_count: int
    subtotal: float
    discount: float
    gst: float
    total: float
    created_at: datetime
    updated_at: datetime


class OrderDetailResponse(OrderSummaryResponse):
    user_id: int
    shipping_address: dict
    items: list[OrderItemResponse]
