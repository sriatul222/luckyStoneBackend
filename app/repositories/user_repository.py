from app.core.database import database


USER_COLUMNS = "id, name, email, mobile, password_hash, role, is_active, created_at"


class UserRepository:
    def get_all(self, limit: int, offset: int) -> tuple[list[dict], int]:
        with database.get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {USER_COLUMNS}, COUNT(*) OVER() AS total_count
                FROM users ORDER BY id DESC LIMIT %s OFFSET %s
                """,
                (limit, offset),
            ).fetchall()

        total = rows[0]["total_count"] if rows else 0
        return rows, total

    def get_by_id(self, user_id: int) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                f"SELECT {USER_COLUMNS} FROM users WHERE id = %s", (user_id,)
            ).fetchone()

    def get_by_email(self, email: str) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                f"SELECT {USER_COLUMNS} FROM users WHERE LOWER(email) = LOWER(%s)",
                (email,),
            ).fetchone()

    def get_by_mobile(self, mobile: str) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                f"SELECT {USER_COLUMNS} FROM users WHERE mobile = %s", (mobile,)
            ).fetchone()

    def create(self, name: str, email: str, mobile: str, password_hash: str) -> dict:
        with database.get_connection() as connection:
            return connection.execute(
                f"""
                INSERT INTO users (name, email, mobile, password_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING {USER_COLUMNS}
                """,
                (name, email.lower(), mobile, password_hash),
            ).fetchone()

    def update_profile(self, user_id: int, name: str, email: str, mobile: str) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                f"""
                UPDATE users SET name = %s, email = %s, mobile = %s
                WHERE id = %s
                RETURNING {USER_COLUMNS}
                """,
                (name, email.lower(), mobile, user_id),
            ).fetchone()

    def update_password(self, user_id: int, password_hash: str):
        with database.get_connection() as connection:
            connection.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id),
            )

    def set_role(self, user_id: int, role: str) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                f"UPDATE users SET role = %s WHERE id = %s RETURNING {USER_COLUMNS}",
                (role, user_id),
            ).fetchone()

    def set_active(self, user_id: int, is_active: bool) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                f"UPDATE users SET is_active = %s WHERE id = %s RETURNING {USER_COLUMNS}",
                (is_active, user_id),
            ).fetchone()


user_repository = UserRepository()
