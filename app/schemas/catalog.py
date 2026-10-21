from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
Metal = Literal["gold", "silver", "platinum"]


# ---------- Metal rates ----------

class MetalRateResponse(BaseModel):
    id: int
    metal: str
    purity: str
    rate_per_gram: float
    updated_at: datetime


class MetalRateItem(BaseModel):
    metal: Metal
    purity: str = Field(..., max_length=10, examples=["22K"])
    rate_per_gram: float = Field(..., gt=0)


class MetalRatesUpdateRequest(BaseModel):
    rates: list[MetalRateItem] = Field(..., min_length=1)


# ---------- Categories ----------

class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    image_url: str
    display_order: int
    is_active: bool


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., pattern=SLUG, max_length=120)
    image_url: str = ""
    display_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    slug: str | None = Field(None, pattern=SLUG, max_length=120)
    image_url: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


# ---------- Collections ----------

class CollectionResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    image_url: str
    display_order: int
    is_active: bool


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., pattern=SLUG, max_length=120)
    description: str = ""
    image_url: str = ""
    display_order: int = 0
    is_active: bool = True


class CollectionUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    slug: str | None = Field(None, pattern=SLUG, max_length=120)
    description: str | None = None
    image_url: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


# ---------- Banners ----------

RedirectType = Literal["none", "category", "collection", "product", "url"]


class BannerResponse(BaseModel):
    id: int
    title: str
    subtitle: str
    image_url: str
    redirect_type: str
    redirect_value: str
    display_order: int
    is_active: bool


class BannerCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    subtitle: str = ""
    image_url: str = ""
    redirect_type: RedirectType = "none"
    redirect_value: str = ""
    display_order: int = 0
    is_active: bool = True


class BannerUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=150)
    subtitle: str | None = None
    image_url: str | None = None
    redirect_type: RedirectType | None = None
    redirect_value: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


# ---------- Stores ----------

class StoreResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    state: str
    pincode: str
    phone: str
    latitude: float | None
    longitude: float | None
    opening_hours: str
    is_active: bool


class StoreCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    address: str
    city: str
    state: str
    pincode: str = Field(..., pattern=r"^\d{6}$")
    phone: str = ""
    latitude: float | None = None
    longitude: float | None = None
    opening_hours: str = ""
    is_active: bool = True


class StoreUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = Field(None, pattern=r"^\d{6}$")
    phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    opening_hours: str | None = None
    is_active: bool | None = None
