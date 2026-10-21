from app.core.database import database
from app.repositories.product_repository import PRODUCT_SELECT


class CartRepository:
    def get_items(self, user_id: int) -> list[dict]:
        """Cart rows with the product's live price (metal rate of today)."""
        with database.get_connection() as connection:
            return connection.execute(
                f"""
                SELECT ci.id AS cart_item_id, ci.quantity, ci.size, product.*
                FROM cart_items ci
                JOIN ({PRODUCT_SELECT}) AS product ON product.id = ci.product_id
                WHERE ci.user_id = %s
                ORDER BY ci.created_at DESC, ci.id DESC
                """,
                (user_id,),
            ).fetchall()

    def get_item(self, user_id: int, item_id: int) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                "SELECT id, product_id, size, quantity FROM cart_items WHERE id = %s AND user_id = %s",
                (item_id, user_id),
            ).fetchone()

    def get_quantity(self, user_id: int, product_id: int, size: str) -> int:
        with database.get_connection() as connection:
            row = connection.execute(
                """
                SELECT quantity FROM cart_items
                WHERE user_id = %s AND product_id = %s AND size = %s
                """,
                (user_id, product_id, size),
            ).fetchone()
        return row["quantity"] if row else 0

    def add(self, user_id: int, product_id: int, size: str, quantity: int):
        """Adding the same product + size again increases its quantity."""
        with database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO cart_items (user_id, product_id, size, quantity)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, product_id, size)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
                """,
                (user_id, product_id, size, quantity),
            )

    def update_quantity(self, user_id: int, item_id: int, quantity: int) -> bool:
        with database.get_connection() as connection:
            cursor = connection.execute(
                "UPDATE cart_items SET quantity = %s WHERE id = %s AND user_id = %s",
                (quantity, item_id, user_id),
            )
        return cursor.rowcount > 0

    def remove(self, user_id: int, item_id: int) -> bool:
        with database.get_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM cart_items WHERE id = %s AND user_id = %s",
                (item_id, user_id),
            )
        return cursor.rowcount > 0

    def clear(self, user_id: int):
        with database.get_connection() as connection:
            connection.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))


cart_repository = CartRepository()
