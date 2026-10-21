from app.core.database import database
from app.repositories.product_repository import PRODUCT_SELECT


class WishlistRepository:
    def get_products(self, user_id: int) -> list[dict]:
        with database.get_connection() as connection:
            return connection.execute(
                f"""
                SELECT product.* FROM ({PRODUCT_SELECT}) AS product
                JOIN wishlist_items w ON w.product_id = product.id
                WHERE w.user_id = %s AND product.is_active = TRUE
                ORDER BY w.created_at DESC
                """,
                (user_id,),
            ).fetchall()

    def add(self, user_id: int, product_id: int):
        with database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO wishlist_items (user_id, product_id) VALUES (%s, %s)
                ON CONFLICT (user_id, product_id) DO NOTHING
                """,
                (user_id, product_id),
            )

    def remove(self, user_id: int, product_id: int) -> bool:
        with database.get_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM wishlist_items WHERE user_id = %s AND product_id = %s",
                (user_id, product_id),
            )
        return cursor.rowcount > 0

    def contains(self, user_id: int, product_id: int) -> bool:
        with database.get_connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM wishlist_items WHERE user_id = %s AND product_id = %s",
                (user_id, product_id),
            ).fetchone()
        return row is not None


wishlist_repository = WishlistRepository()
