from app.core.database import database
from app.repositories.crud_repository import CrudRepository


# Product + category/collection names + live price (from product_prices view)
# + average rating. Reused by wishlist and cart queries.
PRODUCT_SELECT = """
    SELECT
        p.id, p.name, p.slug, p.sku, p.description,
        p.category_id, c.name AS category_name, c.slug AS category_slug,
        p.collection_id, col.name AS collection_name, col.slug AS collection_slug,
        p.metal, p.purity, p.gross_weight, p.net_weight,
        p.making_charge_percent, p.making_discount_percent,
        p.stone_type, p.stone_weight_carat, p.stone_quality, p.stone_price,
        p.gender, p.occasion, p.sizes, p.image_urls, p.stock,
        p.is_featured, p.is_active, p.created_at,
        pp.metal_rate, pp.metal_value, pp.making_charges, pp.making_discount,
        pp.stone_value, pp.subtotal, pp.gst_percent, pp.gst, pp.total, pp.original_total,
        COALESCE(r.avg_rating, 0) AS rating,
        COALESCE(r.review_count, 0) AS review_count
    FROM products p
    JOIN product_prices pp ON pp.product_id = p.id
    JOIN categories c ON c.id = p.category_id
    LEFT JOIN collections col ON col.id = p.collection_id
    LEFT JOIN (
        SELECT product_id, ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS review_count
        FROM reviews GROUP BY product_id
    ) r ON r.product_id = p.id
"""

# Column names of the PRODUCT_SELECT result (sorting happens on the outer query)
SORT_OPTIONS = {
    "newest": "created_at DESC, id DESC",
    "price_low_to_high": "total ASC, id",
    "price_high_to_low": "total DESC, id",
    "popular": "review_count DESC, rating DESC, id DESC",
    "rating": "rating DESC, review_count DESC, id DESC",
}

PRODUCT_COLUMNS = [
    "name", "slug", "sku", "description", "category_id", "collection_id",
    "metal", "purity", "gross_weight", "net_weight",
    "making_charge_percent", "making_discount_percent",
    "stone_type", "stone_weight_carat", "stone_quality", "stone_price",
    "gender", "occasion", "sizes", "image_urls", "stock", "is_featured", "is_active",
]


class ProductRepository:
    # Admin create/update writes go through the shared CRUD helper
    table = CrudRepository("products", PRODUCT_COLUMNS)

    def search(
        self,
        q: str | None = None,
        category: str | None = None,
        collection: str | None = None,
        metal: str | None = None,
        purity: str | None = None,
        gender: str | None = None,
        occasion: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        featured: bool | None = None,
        in_stock: bool | None = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
        include_inactive: bool = False,
    ) -> tuple[list[dict], int]:
        conditions = []
        params: list = []

        if not include_inactive:
            conditions.append("p.is_active = TRUE")
        if q:
            conditions.append(
                "(p.name ILIKE %s OR p.description ILIKE %s OR p.sku ILIKE %s OR c.name ILIKE %s)"
            )
            params.extend([f"%{q}%"] * 4)
        if category:
            conditions.append("c.slug = %s")
            params.append(category)
        if collection:
            conditions.append("col.slug = %s")
            params.append(collection)
        if metal:
            conditions.append("p.metal = %s")
            params.append(metal.lower())
        if purity:
            conditions.append("p.purity = %s")
            params.append(purity.upper())
        if gender:
            # unisex pieces show up for men and women
            conditions.append("(p.gender = %s OR p.gender = 'unisex')")
            params.append(gender.lower())
        if occasion:
            conditions.append("p.occasion = %s")
            params.append(occasion.lower())
        if min_price is not None:
            conditions.append("pp.total >= %s")
            params.append(min_price)
        if max_price is not None:
            conditions.append("pp.total <= %s")
            params.append(max_price)
        if featured is not None:
            conditions.append("p.is_featured = %s")
            params.append(featured)
        if in_stock:
            conditions.append("p.stock > 0")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        order_by = SORT_OPTIONS.get(sort, SORT_OPTIONS["newest"])

        query = f"""
            SELECT *, COUNT(*) OVER() AS total_count FROM ({PRODUCT_SELECT} {where}) AS products_with_price
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """
        with database.get_connection() as connection:
            rows = connection.execute(query, [*params, limit, offset]).fetchall()

        total = rows[0]["total_count"] if rows else 0
        return rows, total

    def get_by_id(self, product_id: int, include_inactive: bool = False) -> dict | None:
        condition = "" if include_inactive else "AND p.is_active = TRUE"
        with database.get_connection() as connection:
            return connection.execute(
                f"{PRODUCT_SELECT} WHERE p.id = %s {condition}", (product_id,)
            ).fetchone()

    def exists(self, product_id: int) -> bool:
        return self.get_by_id(product_id) is not None

    def create(self, values: dict) -> dict:
        created = self.table.create(values)
        return self.get_by_id(created["id"], include_inactive=True)

    def update(self, product_id: int, values: dict) -> dict | None:
        updated = self.table.update(product_id, values)
        if updated is None:
            return None
        return self.get_by_id(product_id, include_inactive=True)

    def deactivate(self, product_id: int) -> bool:
        return self.table.update(product_id, {"is_active": False}) is not None


product_repository = ProductRepository()
