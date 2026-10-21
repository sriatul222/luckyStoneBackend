from app.core.database import database


ADDRESS_COLUMNS = """
    id, user_id, full_name, mobile, line1, line2, landmark, city, state,
    pincode, address_type, is_default, created_at
"""


class AddressRepository:
    def get_all(self, user_id: int) -> list[dict]:
        with database.get_connection() as connection:
            return connection.execute(
                f"""
                SELECT {ADDRESS_COLUMNS} FROM addresses
                WHERE user_id = %s ORDER BY is_default DESC, id DESC
                """,
                (user_id,),
            ).fetchall()

    def get_by_id(self, user_id: int, address_id: int) -> dict | None:
        with database.get_connection() as connection:
            return connection.execute(
                f"SELECT {ADDRESS_COLUMNS} FROM addresses WHERE id = %s AND user_id = %s",
                (address_id, user_id),
            ).fetchone()

    def create(self, user_id: int, values: dict) -> dict:
        with database.get_connection() as connection:
            has_address = connection.execute(
                "SELECT 1 FROM addresses WHERE user_id = %s LIMIT 1", (user_id,)
            ).fetchone()
            # The first address is always the default one
            is_default = values.get("is_default", False) or has_address is None
            if is_default:
                connection.execute(
                    "UPDATE addresses SET is_default = FALSE WHERE user_id = %s", (user_id,)
                )

            return connection.execute(
                f"""
                INSERT INTO addresses (
                    user_id, full_name, mobile, line1, line2, landmark,
                    city, state, pincode, address_type, is_default
                )
                VALUES (
                    %(user_id)s, %(full_name)s, %(mobile)s, %(line1)s, %(line2)s, %(landmark)s,
                    %(city)s, %(state)s, %(pincode)s, %(address_type)s, %(is_default)s
                )
                RETURNING {ADDRESS_COLUMNS}
                """,
                {**values, "user_id": user_id, "is_default": is_default},
            ).fetchone()

    def update(self, user_id: int, address_id: int, values: dict) -> dict | None:
        with database.get_connection() as connection:
            if values.get("is_default"):
                connection.execute(
                    "UPDATE addresses SET is_default = FALSE WHERE user_id = %s", (user_id,)
                )

            return connection.execute(
                f"""
                UPDATE addresses SET
                    full_name = %(full_name)s, mobile = %(mobile)s, line1 = %(line1)s,
                    line2 = %(line2)s, landmark = %(landmark)s, city = %(city)s,
                    state = %(state)s, pincode = %(pincode)s, address_type = %(address_type)s,
                    is_default = is_default OR %(is_default)s
                WHERE id = %(address_id)s AND user_id = %(user_id)s
                RETURNING {ADDRESS_COLUMNS}
                """,
                {**values, "user_id": user_id, "address_id": address_id},
            ).fetchone()

    def delete(self, user_id: int, address_id: int) -> bool:
        with database.get_connection() as connection:
            deleted = connection.execute(
                "DELETE FROM addresses WHERE id = %s AND user_id = %s RETURNING is_default",
                (address_id, user_id),
            ).fetchone()
            if deleted and deleted["is_default"]:
                # Make the newest remaining address the default
                connection.execute(
                    """
                    UPDATE addresses SET is_default = TRUE
                    WHERE id = (SELECT id FROM addresses WHERE user_id = %s ORDER BY id DESC LIMIT 1)
                    """,
                    (user_id,),
                )
        return deleted is not None


address_repository = AddressRepository()
