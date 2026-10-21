"""Home screen, wishlist, cart, addresses and orders."""

from app.repositories.address_repository import address_repository
from app.repositories.cart_repository import cart_repository
from app.repositories.crud_repository import (
    banner_repository,
    category_repository,
    collection_repository,
)
from app.repositories.metal_rate_repository import metal_rate_repository
from app.repositories.order_repository import order_repository
from app.repositories.product_repository import product_repository
from app.repositories.wishlist_repository import wishlist_repository
from app.schemas.common import page_data
from app.schemas.shop import AddressRequest, CartAddRequest, PlaceOrderRequest
from app.services.exceptions import BadRequestError, NotFoundError
from app.services.product_service import to_product_card


class HomeService:
    def get_home(self) -> dict:
        featured, _ = product_repository.search(featured=True, limit=10)
        new_arrivals, _ = product_repository.search(sort="newest", limit=10)
        return {
            "metal_rates": metal_rate_repository.get_all(),
            "banners": banner_repository.get_all(),
            "categories": category_repository.get_all(),
            "collections": collection_repository.get_all(),
            "featured": [to_product_card(row) for row in featured],
            "new_arrivals": [to_product_card(row) for row in new_arrivals],
        }


class WishlistService:
    def get_wishlist(self, user: dict) -> list:
        return [to_product_card(row) for row in wishlist_repository.get_products(user["id"])]

    def add(self, user: dict, product_id: int):
        if not product_repository.exists(product_id):
            raise NotFoundError("Product not found")
        wishlist_repository.add(user["id"], product_id)

    def remove(self, user: dict, product_id: int):
        if not wishlist_repository.remove(user["id"], product_id):
            raise NotFoundError("Product is not in your wishlist")


class CartService:
    def get_cart(self, user: dict) -> dict:
        rows = cart_repository.get_items(user["id"])
        items = []
        subtotal = discount = gst = total = 0.0
        for row in rows:
            quantity = row["quantity"]
            items.append({
                "id": row["cart_item_id"],
                "product": to_product_card(row),
                "size": row["size"],
                "quantity": quantity,
                "unit_price": float(row["total"]),
                "line_total": round(float(row["total"]) * quantity, 2),
                "available_stock": row["stock"] if row["is_active"] else 0,
            })
            subtotal += float(row["metal_value"] + row["making_charges"] + row["stone_value"]) * quantity
            discount += float(row["making_discount"]) * quantity
            gst += float(row["gst"]) * quantity
            total += float(row["total"]) * quantity

        return {
            "items": items,
            "summary": {
                "item_count": len(items),
                "total_quantity": sum(item["quantity"] for item in items),
                "subtotal": round(subtotal, 2),
                "discount": round(discount, 2),
                "gst": round(gst, 2),
                "total": round(total, 2),
            },
        }

    def add_item(self, user: dict, cart_data: CartAddRequest) -> dict:
        product = product_repository.get_by_id(cart_data.product_id)
        if product is None:
            raise NotFoundError("Product not found")

        size = cart_data.size.strip()
        if product["sizes"] and size not in product["sizes"]:
            raise BadRequestError(f"Please select a size: {', '.join(product['sizes'])}")
        if not product["sizes"]:
            size = ""

        already_in_cart = cart_repository.get_quantity(user["id"], product["id"], size)
        if already_in_cart + cart_data.quantity > product["stock"]:
            raise BadRequestError(f"Only {product['stock']} left in stock")

        cart_repository.add(user["id"], product["id"], size, cart_data.quantity)
        return self.get_cart(user)

    def update_item(self, user: dict, item_id: int, quantity: int) -> dict:
        item = cart_repository.get_item(user["id"], item_id)
        if item is None:
            raise NotFoundError("Cart item not found")
        product = product_repository.get_by_id(item["product_id"])
        if product is None:
            raise BadRequestError("This product is no longer available, please remove it")
        if quantity > product["stock"]:
            raise BadRequestError(f"Only {product['stock']} left in stock")

        cart_repository.update_quantity(user["id"], item_id, quantity)
        return self.get_cart(user)

    def remove_item(self, user: dict, item_id: int) -> dict:
        if not cart_repository.remove(user["id"], item_id):
            raise NotFoundError("Cart item not found")
        return self.get_cart(user)

    def clear(self, user: dict):
        cart_repository.clear(user["id"])


class AddressService:
    def get_addresses(self, user: dict) -> list[dict]:
        return address_repository.get_all(user["id"])

    def create(self, user: dict, address_data: AddressRequest) -> dict:
        return address_repository.create(user["id"], address_data.model_dump())

    def update(self, user: dict, address_id: int, address_data: AddressRequest) -> dict:
        address = address_repository.update(user["id"], address_id, address_data.model_dump())
        if address is None:
            raise NotFoundError("Address not found")
        return address

    def delete(self, user: dict, address_id: int):
        if not address_repository.delete(user["id"], address_id):
            raise NotFoundError("Address not found")


# Which status an order may move to, and from where
ORDER_FLOW = {
    "PLACED": ("CONFIRMED", "CANCELLED"),
    "CONFIRMED": ("SHIPPED", "CANCELLED"),
    "SHIPPED": ("DELIVERED",),
    "DELIVERED": (),
    "CANCELLED": (),
}
CUSTOMER_CANCELLABLE = ("PLACED", "CONFIRMED")


class OrderService:
    def place_order(self, user: dict, order_data: PlaceOrderRequest) -> dict:
        address = address_repository.get_by_id(user["id"], order_data.address_id)
        if address is None:
            raise NotFoundError("Address not found")

        order_id = order_repository.create_from_cart(user["id"], address, order_data.payment_method)
        return order_repository.get_by_id(order_id, user["id"])

    def get_my_orders(self, user: dict, page: int, page_size: int) -> dict:
        rows, total = order_repository.get_for_user(user["id"], page_size, (page - 1) * page_size)
        return page_data(rows, page, page_size, total)

    def get_order(self, order_id: int, user: dict | None = None) -> dict:
        order = order_repository.get_by_id(order_id, user["id"] if user else None)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    def cancel_order(self, user: dict, order_id: int) -> dict:
        order_repository.change_status(order_id, CUSTOMER_CANCELLABLE, "CANCELLED", user["id"])
        return self.get_order(order_id, user)

    def get_all_orders(self, status: str | None, page: int, page_size: int) -> dict:
        rows, total = order_repository.get_all(status, page_size, (page - 1) * page_size)
        return page_data(rows, page, page_size, total)

    def update_status(self, order_id: int, new_status: str) -> dict:
        allowed_from = tuple(status for status, next_steps in ORDER_FLOW.items() if new_status in next_steps)
        order_repository.change_status(order_id, allowed_from, new_status)
        return self.get_order(order_id)


home_service = HomeService()
wishlist_service = WishlistService()
cart_service = CartService()
address_service = AddressService()
order_service = OrderService()
