from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.repositories.product_repository import product_repository
from app.repositories.review_repository import review_repository
from app.repositories.wishlist_repository import wishlist_repository
from app.schemas.common import page_data
from app.schemas.product import ProductCard, ProductCreate, ProductDetail, ProductUpdate, ReviewCreate
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


def to_product_card(row: dict) -> ProductCard:
    return ProductCard(
        id=row["id"],
        name=row["name"],
        slug=row["slug"],
        sku=row["sku"],
        category_name=row["category_name"],
        category_slug=row["category_slug"],
        metal=row["metal"],
        purity=row["purity"],
        net_weight=row["net_weight"],
        gross_weight=row["gross_weight"],
        image_url=row["image_urls"][0] if row["image_urls"] else "",
        price=row["total"],
        original_price=row["original_total"],
        discount_percent=row["making_discount_percent"],
        rating=row["rating"],
        review_count=row["review_count"],
        in_stock=row["stock"] > 0,
        is_featured=row["is_featured"],
    )


def to_product_detail(row: dict, is_wishlisted: bool = False) -> ProductDetail:
    return ProductDetail(
        **to_product_card(row).model_dump(),
        description=row["description"],
        collection_name=row["collection_name"],
        collection_slug=row["collection_slug"],
        image_urls=row["image_urls"],
        gender=row["gender"],
        occasion=row["occasion"],
        sizes=row["sizes"],
        stone_type=row["stone_type"],
        stone_weight_carat=row["stone_weight_carat"],
        stone_quality=row["stone_quality"],
        making_charge_percent=row["making_charge_percent"],
        stock=row["stock"],
        is_active=row["is_active"],
        is_wishlisted=is_wishlisted,
        price_breakup={
            key: row[key]
            for key in ("metal_rate", "metal_value", "making_charges", "making_discount",
                        "stone_value", "subtotal", "gst_percent", "gst", "total")
        },
        created_at=row["created_at"],
    )


class ProductService:
    def list_products(self, page: int, page_size: int, **filters) -> dict:
        rows, total = product_repository.search(
            limit=page_size, offset=(page - 1) * page_size, **filters
        )
        return page_data([to_product_card(row) for row in rows], page, page_size, total)

    def get_product(self, product_id: int, user: dict | None = None, admin: bool = False) -> ProductDetail:
        row = product_repository.get_by_id(product_id, include_inactive=admin)
        if row is None:
            raise NotFoundError("Product not found")
        is_wishlisted = user is not None and wishlist_repository.contains(user["id"], product_id)
        return to_product_detail(row, is_wishlisted)

    def create_product(self, product_data: ProductCreate) -> ProductDetail:
        try:
            row = product_repository.create(product_data.model_dump())
        except UniqueViolation:
            raise ConflictError("A product with this slug or SKU already exists")
        except ForeignKeyViolation:
            raise BadRequestError("Category or collection does not exist")
        return to_product_detail(row)

    def update_product(self, product_id: int, product_data: ProductUpdate) -> ProductDetail:
        try:
            row = product_repository.update(product_id, product_data.model_dump(exclude_unset=True))
        except UniqueViolation:
            raise ConflictError("A product with this slug or SKU already exists")
        except ForeignKeyViolation:
            raise BadRequestError("Category or collection does not exist")
        if row is None:
            raise NotFoundError("Product not found")
        return to_product_detail(row)

    def delete_product(self, product_id: int):
        # Soft delete: old orders still point to the product
        if not product_repository.deactivate(product_id):
            raise NotFoundError("Product not found")

    def get_reviews(self, product_id: int, page: int, page_size: int) -> dict:
        if not product_repository.exists(product_id):
            raise NotFoundError("Product not found")
        rows, total = review_repository.get_for_product(product_id, page_size, (page - 1) * page_size)
        return page_data(rows, page, page_size, total)

    def add_review(self, user: dict, product_id: int, review_data: ReviewCreate) -> dict:
        if not product_repository.exists(product_id):
            raise NotFoundError("Product not found")
        return review_repository.upsert(
            product_id, user["id"], review_data.rating, review_data.comment.strip()
        )


product_service = ProductService()
