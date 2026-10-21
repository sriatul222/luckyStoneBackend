import secrets
from datetime import datetime

from psycopg.types.json import Jsonb

from app.core.database import database
from app.services.exceptions import BadRequestError, NotFoundError


ORDER_COLUMNS = """
    o.id, o.order_number, o.user_id, o.status, o.payment_method, o.payment_status,
    o.shipping_address, o.subtotal, o.discount, o.gst, o.total, o.created_at, o.updated_at
"""

ORDER_ITEM_COLUMNS = """
    id, order_id, product_id, product_name, sku, image_url, metal, purity, net_weight,
    size, quantity, unit_price, line_total, price_breakup
"""


def _new_order_number() -> str:
    return f"LS{datetime.now():%y%m%d}{secrets.randbelow(10**6):06d}"


class OrderRepository:
    def create_from_cart(self, user_id: int, address: dict, payment_method: str) -> int:
        """Places an order for everything in the user's cart in ONE transaction:
        lock products -> check stock -> save order + items -> reduce stock -> empty cart.
        Any error rolls everything back."""
        with database.get_connection() as connection:
            cart_rows = connection.execute(
                """
                SELECT ci.product_id, ci.size, ci.quantity,
                       p.name, p.sku, p.image_urls, p.metal, p.purity, p.net_weight,
                       p.stock, p.is_active,
                       pp.metal_rate, pp.metal_value, pp.making_charges, pp.making_discount,
                       pp.stone_value, pp.subtotal, pp.gst_percent, pp.gst, pp.total
                FROM cart_items ci
                JOIN products p ON p.id = ci.product_id
                JOIN product_prices pp ON pp.product_id = p.id
                WHERE ci.user_id = %s
                ORDER BY ci.id
                FOR UPDATE OF p
                """,
                (user_id,),
            ).fetchall()

            if not cart_rows:
                raise BadRequestError("Your cart is empty")

            quantity_by_product: dict[int, int] = {}
            for row in cart_rows:
                quantity_by_product[row["product_id"]] = (
                    quantity_by_product.get(row["product_id"], 0) + row["quantity"]
                )
            for row in cart_rows:
                if not row["is_active"]:
                    raise BadRequestError(f"{row['name']} is no longer available")
                if quantity_by_product[row["product_id"]] > row["stock"]:
                    raise BadRequestError(f"Only {row['stock']} left in stock for {row['name']}")

            subtotal = sum((r["metal_value"] + r["making_charges"] + r["stone_value"]) * r["quantity"] for r in cart_rows)
            discount = sum(r["making_discount"] * r["quantity"] for r in cart_rows)
            gst = sum(r["gst"] * r["quantity"] for r in cart_rows)
            total = sum(r["total"] * r["quantity"] for r in cart_rows)

            shipping_address = {
                key: address[key]
                for key in ("full_name", "mobile", "line1", "line2", "landmark", "city", "state", "pincode", "address_type")
            }

            order = connection.execute(
                """
                INSERT INTO orders (
                    order_number, user_id, payment_method, shipping_address,
                    subtotal, discount, gst, total
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    _new_order_number(), user_id, payment_method, Jsonb(shipping_address),
                    subtotal, discount, gst, total,
                ),
            ).fetchone()

            for row in cart_rows:
                price_breakup = {
                    key: float(row[key])
                    for key in ("metal_rate", "metal_value", "making_charges", "making_discount",
                                "stone_value", "subtotal", "gst_percent", "gst", "total")
                }
                connection.execute(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, product_name, sku, image_url, metal, purity,
                        net_weight, size, quantity, unit_price, line_total, price_breakup
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order["id"], row["product_id"], row["name"], row["sku"],
                        row["image_urls"][0] if row["image_urls"] else "",
                        row["metal"], row["purity"], row["net_weight"], row["size"],
                        row["quantity"], row["total"], row["total"] * row["quantity"],
                        Jsonb(price_breakup),
                    ),
                )
                connection.execute(
                    "UPDATE products SET stock = stock - %s WHERE id = %s",
                    (row["quantity"], row["product_id"]),
                )

            connection.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))

        return order["id"]

    def get_for_user(self, user_id: int, limit: int, offset: int) -> tuple[list[dict], int]:
        return self._list("WHERE o.user_id = %s", [user_id], limit, offset)

    def get_all(self, status: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
        if status:
            return self._list("WHERE o.status = %s", [status], limit, offset)
        return self._list("", [], limit, offset)

    def _list(self, where: str, params: list, limit: int, offset: int) -> tuple[list[dict], int]:
        with database.get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {ORDER_COLUMNS},
                       (SELECT COALESCE(SUM(quantity), 0) FROM order_items WHERE order_id = o.id) AS item_count,
                       COUNT(*) OVER() AS total_count
                FROM orders o
                {where}
                ORDER BY o.created_at DESC, o.id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, limit, offset],
            ).fetchall()

        total = rows[0]["total_count"] if rows else 0
        return rows, total

    def get_by_id(self, order_id: int, user_id: int | None = None) -> dict | None:
        """user_id=None is used by admin to read any order."""
        condition = "" if user_id is None else "AND o.user_id = %s"
        params = [order_id] if user_id is None else [order_id, user_id]

        with database.get_connection() as connection:
            order = connection.execute(
                f"""
                SELECT {ORDER_COLUMNS},
                       (SELECT COALESCE(SUM(quantity), 0) FROM order_items WHERE order_id = o.id) AS item_count
                FROM orders o WHERE o.id = %s {condition}
                """,
                params,
            ).fetchone()
            if order is None:
                return None

            order["items"] = connection.execute(
                f"SELECT {ORDER_ITEM_COLUMNS} FROM order_items WHERE order_id = %s ORDER BY id",
                (order_id,),
            ).fetchall()
        return order

    def change_status(
        self,
        order_id: int,
        allowed_from: tuple[str, ...],
        new_status: str,
        user_id: int | None = None,
    ) -> None:
        """Moves an order to new_status. A cancelled order puts its stock back."""
        condition = "" if user_id is None else "AND user_id = %s"
        params = [order_id] if user_id is None else [order_id, user_id]

        with database.get_connection() as connection:
            order = connection.execute(
                f"SELECT id, status, payment_status FROM orders WHERE id = %s {condition} FOR UPDATE",
                params,
            ).fetchone()
            if order is None:
                raise NotFoundError("Order not found")
            if order["status"] not in allowed_from:
                raise BadRequestError(
                    f"Order is {order['status']} and cannot be changed to {new_status}"
                )

            payment_status = order["payment_status"]
            if new_status == "CANCELLED":
                connection.execute(
                    """
                    UPDATE products p SET stock = p.stock + oi.quantity
                    FROM order_items oi
                    WHERE oi.order_id = %s AND oi.product_id = p.id
                    """,
                    (order_id,),
                )
                if payment_status == "PAID":
                    payment_status = "REFUND_INITIATED"
            elif new_status == "DELIVERED" and payment_status == "PENDING":
                # Cash on delivery is collected at the door
                payment_status = "PAID"

            connection.execute(
                """
                UPDATE orders SET status = %s, payment_status = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (new_status, payment_status, order_id),
            )


order_repository = OrderRepository()
