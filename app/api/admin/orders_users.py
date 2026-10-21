from fastapi import APIRouter, Depends, Query

from app.core.config import settings
from app.core.dependencies import require_admin
from app.schemas.common import ApiResponse, PageData
from app.schemas.shop import OrderDetailResponse, OrderStatus, OrderStatusUpdate, OrderSummaryResponse
from app.schemas.user import UserResponse, UserRoleUpdate, UserStatusUpdate
from app.services.shop_service import order_service
from app.services.user_service import user_service


router = APIRouter(
    prefix=f"{settings.api_prefix}/admin",
    tags=["Admin - Orders & Users"],
    dependencies=[Depends(require_admin)],
)


# ---------------- Orders ----------------

@router.get("/orders", response_model=ApiResponse[PageData[OrderSummaryResponse]])
def get_all_orders(
    status: OrderStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return {
        "success": True,
        "message": "Orders fetched successfully",
        "data": order_service.get_all_orders(status, page, page_size),
    }


@router.get("/orders/{order_id}", response_model=ApiResponse[OrderDetailResponse])
def get_order(order_id: int):
    return {"success": True, "message": "Order fetched successfully", "data": order_service.get_order(order_id)}


@router.put("/orders/{order_id}/status", response_model=ApiResponse[OrderDetailResponse])
def update_order_status(order_id: int, status_data: OrderStatusUpdate):
    """PLACED -> CONFIRMED -> SHIPPED -> DELIVERED. PLACED/CONFIRMED can be CANCELLED."""
    return {
        "success": True,
        "message": f"Order {status_data.status.lower()}",
        "data": order_service.update_status(order_id, status_data.status),
    }


# ---------------- Users ----------------

@router.get("/users", response_model=ApiResponse[PageData[UserResponse]])
def get_users(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    return {"success": True, "message": "Users fetched successfully", "data": user_service.get_users(page, page_size)}


@router.put("/users/{user_id}/role", response_model=ApiResponse[UserResponse])
def update_user_role(user_id: int, role_data: UserRoleUpdate, admin: dict = Depends(require_admin)):
    return {
        "success": True,
        "message": "User role updated",
        "data": user_service.set_role(admin, user_id, role_data.role),
    }


@router.put("/users/{user_id}/status", response_model=ApiResponse[UserResponse])
def update_user_status(user_id: int, status_data: UserStatusUpdate, admin: dict = Depends(require_admin)):
    return {
        "success": True,
        "message": "User status updated",
        "data": user_service.set_active(admin, user_id, status_data.is_active),
    }
