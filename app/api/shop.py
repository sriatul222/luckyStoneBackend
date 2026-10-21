from fastapi import APIRouter, Depends, Query, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.schemas.common import ApiResponse, PageData
from app.schemas.product import ProductCard
from app.schemas.shop import (
    AddressRequest,
    AddressResponse,
    CartAddRequest,
    CartData,
    CartUpdateRequest,
    OrderDetailResponse,
    OrderSummaryResponse,
    PlaceOrderRequest,
    WishlistAddRequest,
)
from app.services.shop_service import (
    address_service,
    cart_service,
    order_service,
    wishlist_service,
)


# All these APIs need "Authorization: Bearer <token>"
wishlist_router = APIRouter(prefix=f"{settings.api_prefix}/wishlist", tags=["Wishlist"])
cart_router = APIRouter(prefix=f"{settings.api_prefix}/cart", tags=["Cart"])
address_router = APIRouter(prefix=f"{settings.api_prefix}/addresses", tags=["Addresses"])
order_router = APIRouter(prefix=f"{settings.api_prefix}/orders", tags=["Orders"])


# ---------------- Wishlist ----------------

@wishlist_router.get("", response_model=ApiResponse[list[ProductCard]])
def get_wishlist(user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Wishlist fetched successfully", "data": wishlist_service.get_wishlist(user)}


@wishlist_router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[list[ProductCard]])
def add_to_wishlist(wishlist_data: WishlistAddRequest, user: dict = Depends(get_current_user)):
    wishlist_service.add(user, wishlist_data.product_id)
    return {"success": True, "message": "Added to wishlist", "data": wishlist_service.get_wishlist(user)}


@wishlist_router.delete("/{product_id}", response_model=ApiResponse[list[ProductCard]])
def remove_from_wishlist(product_id: int, user: dict = Depends(get_current_user)):
    wishlist_service.remove(user, product_id)
    return {"success": True, "message": "Removed from wishlist", "data": wishlist_service.get_wishlist(user)}


# ---------------- Cart ----------------

@cart_router.get("", response_model=ApiResponse[CartData])
def get_cart(user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Cart fetched successfully", "data": cart_service.get_cart(user)}


@cart_router.post("/items", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[CartData])
def add_to_cart(cart_data: CartAddRequest, user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Added to cart", "data": cart_service.add_item(user, cart_data)}


@cart_router.put("/items/{item_id}", response_model=ApiResponse[CartData])
def update_cart_item(item_id: int, cart_data: CartUpdateRequest, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Cart updated",
        "data": cart_service.update_item(user, item_id, cart_data.quantity),
    }


@cart_router.delete("/items/{item_id}", response_model=ApiResponse[CartData])
def remove_cart_item(item_id: int, user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Removed from cart", "data": cart_service.remove_item(user, item_id)}


@cart_router.delete("", response_model=ApiResponse)
def clear_cart(user: dict = Depends(get_current_user)):
    cart_service.clear(user)
    return {"success": True, "message": "Cart cleared", "data": None}


# ---------------- Addresses ----------------

@address_router.get("", response_model=ApiResponse[list[AddressResponse]])
def get_addresses(user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Addresses fetched successfully", "data": address_service.get_addresses(user)}


@address_router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[AddressResponse])
def create_address(address_data: AddressRequest, user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Address added", "data": address_service.create(user, address_data)}


@address_router.put("/{address_id}", response_model=ApiResponse[AddressResponse])
def update_address(address_id: int, address_data: AddressRequest, user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "message": "Address updated",
        "data": address_service.update(user, address_id, address_data),
    }


@address_router.delete("/{address_id}", response_model=ApiResponse)
def delete_address(address_id: int, user: dict = Depends(get_current_user)):
    address_service.delete(user, address_id)
    return {"success": True, "message": "Address deleted", "data": None}


# ---------------- Orders ----------------

@order_router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[OrderDetailResponse])
def place_order(order_data: PlaceOrderRequest, user: dict = Depends(get_current_user)):
    """Buys everything in the cart. Price is locked at today's metal rate."""
    return {"success": True, "message": "Order placed successfully", "data": order_service.place_order(user, order_data)}


@order_router.get("", response_model=ApiResponse[PageData[OrderSummaryResponse]])
def get_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    return {
        "success": True,
        "message": "Orders fetched successfully",
        "data": order_service.get_my_orders(user, page, page_size),
    }


@order_router.get("/{order_id}", response_model=ApiResponse[OrderDetailResponse])
def get_order(order_id: int, user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Order fetched successfully", "data": order_service.get_order(order_id, user)}


@order_router.post("/{order_id}/cancel", response_model=ApiResponse[OrderDetailResponse])
def cancel_order(order_id: int, user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Order cancelled", "data": order_service.cancel_order(user, order_id)}
