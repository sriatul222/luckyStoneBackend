from app.core.database import database


class ReviewRepository:
    def get_for_product(self, product_id: int, limit: int, offset: int) -> tuple[list[dict], int]:
        with database.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT r.id, r.product_id, r.user_id, u.name AS user_name,
                       r.rating, r.comment, r.created_at,
                       COUNT(*) OVER() AS total_count
                FROM reviews r
                JOIN users u ON u.id = r.user_id
                WHERE r.product_id = %s
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT %s OFFSET %s
                """,
                (product_id, limit, offset),
            ).fetchall()

        total = rows[0]["total_count"] if rows else 0
        return rows, total

    def upsert(self, product_id: int, user_id: int, rating: int, comment: str) -> dict:
        """One review per user per product; posting again edits it."""
        with database.get_connection() as connection:
            return connection.execute(
                """
                WITH saved AS (
                    INSERT INTO reviews (product_id, user_id, rating, comment)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (product_id, user_id)
                    DO UPDATE SET rating = EXCLUDED.rating, comment = EXCLUDED.comment,
                                  created_at = NOW()
                    RETURNING *
                )
                SELECT saved.id, saved.product_id, saved.user_id, u.name AS user_name,
                       saved.rating, saved.comment, saved.created_at
                FROM saved JOIN users u ON u.id = saved.user_id
                """,
                (product_id, user_id, rating, comment),
            ).fetchone()


review_repository = ReviewRepository()
