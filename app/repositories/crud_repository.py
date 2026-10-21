from psycopg import sql

from app.core.database import database


class CrudRepository:
    """Shared GET/POST/PUT/DELETE SQL for simple tables
    (categories, collections, banners, stores).

    Table and column names come from code (never from the request), and are
    still quoted with sql.Identifier.
    """

    def __init__(self, table: str, columns: list[str], order_by: str = "id"):
        self.table = table
        self.columns = columns
        self.order_by = order_by

    def _select(self) -> sql.Composed:
        return sql.SQL("SELECT {columns} FROM {table}").format(
            columns=sql.SQL(", ").join(map(sql.Identifier, ["id", *self.columns])),
            table=sql.Identifier(self.table),
        )

    def get_all(self, active_only: bool = True, filters: dict | None = None) -> list[dict]:
        conditions = []
        params = []
        if active_only:
            conditions.append(sql.SQL("is_active = TRUE"))
        for column, value in (filters or {}).items():
            if column in self.columns and value is not None:
                conditions.append(sql.SQL("LOWER({}) = LOWER(%s)").format(sql.Identifier(column)))
                params.append(value)

        query = self._select()
        if conditions:
            query += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
        query += sql.SQL(" ORDER BY {}, id").format(sql.Identifier(self.order_by))

        with database.get_connection() as connection:
            return connection.execute(query, params).fetchall()

    def get_by_id(self, item_id: int) -> dict | None:
        query = self._select() + sql.SQL(" WHERE id = %s")
        with database.get_connection() as connection:
            return connection.execute(query, (item_id,)).fetchone()

    def create(self, values: dict) -> dict:
        values = {key: value for key, value in values.items() if key in self.columns}
        query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values}) RETURNING {returning}").format(
            table=sql.Identifier(self.table),
            columns=sql.SQL(", ").join(map(sql.Identifier, values.keys())),
            values=sql.SQL(", ").join(sql.Placeholder() * len(values)),
            returning=sql.SQL(", ").join(map(sql.Identifier, ["id", *self.columns])),
        )
        with database.get_connection() as connection:
            return connection.execute(query, list(values.values())).fetchone()

    def update(self, item_id: int, values: dict) -> dict | None:
        values = {key: value for key, value in values.items() if key in self.columns}
        if not values:
            return self.get_by_id(item_id)

        query = sql.SQL("UPDATE {table} SET {assignments} WHERE id = %s RETURNING {returning}").format(
            table=sql.Identifier(self.table),
            assignments=sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(key)) for key in values
            ),
            returning=sql.SQL(", ").join(map(sql.Identifier, ["id", *self.columns])),
        )
        with database.get_connection() as connection:
            return connection.execute(query, [*values.values(), item_id]).fetchone()

    def delete(self, item_id: int) -> bool:
        query = sql.SQL("DELETE FROM {table} WHERE id = %s").format(table=sql.Identifier(self.table))
        with database.get_connection() as connection:
            return connection.execute(query, (item_id,)).rowcount > 0


category_repository = CrudRepository(
    "categories", ["name", "slug", "image_url", "display_order", "is_active"], "display_order"
)
collection_repository = CrudRepository(
    "collections",
    ["name", "slug", "description", "image_url", "display_order", "is_active"],
    "display_order",
)
banner_repository = CrudRepository(
    "banners",
    ["title", "subtitle", "image_url", "redirect_type", "redirect_value", "display_order", "is_active"],
    "display_order",
)
store_repository = CrudRepository(
    "stores",
    ["name", "address", "city", "state", "pincode", "phone", "latitude", "longitude", "opening_hours", "is_active"],
    "city",
)
