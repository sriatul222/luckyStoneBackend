from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.repositories.crud_repository import (
    CrudRepository,
    banner_repository,
    category_repository,
    collection_repository,
    store_repository,
)
from app.repositories.metal_rate_repository import metal_rate_repository
from app.schemas.catalog import MetalRatesUpdateRequest
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


class CatalogItemService:
    """Same create/update/delete rules for categories, collections, banners and stores."""

    def __init__(self, repository: CrudRepository, label: str):
        self.repository = repository
        self.label = label

    def get_all(self, active_only: bool = True, **filters) -> list[dict]:
        return self.repository.get_all(active_only=active_only, filters=filters)

    def create(self, values: dict) -> dict:
        try:
            return self.repository.create(values)
        except UniqueViolation:
            raise ConflictError(f"{self.label} with this slug already exists")

    def update(self, item_id: int, values: dict) -> dict:
        try:
            item = self.repository.update(item_id, values)
        except UniqueViolation:
            raise ConflictError(f"{self.label} with this slug already exists")
        if item is None:
            raise NotFoundError(f"{self.label} not found")
        return item

    def delete(self, item_id: int):
        try:
            deleted = self.repository.delete(item_id)
        except ForeignKeyViolation:
            raise BadRequestError(
                f"{self.label} is used by products. Set is_active=false to hide it instead"
            )
        if not deleted:
            raise NotFoundError(f"{self.label} not found")


category_service = CatalogItemService(category_repository, "Category")
collection_service = CatalogItemService(collection_repository, "Collection")
banner_service = CatalogItemService(banner_repository, "Banner")
store_service = CatalogItemService(store_repository, "Store")


class MetalRateService:
    def get_rates(self) -> list[dict]:
        return metal_rate_repository.get_all()

    def update_rates(self, rates_data: MetalRatesUpdateRequest) -> list[dict]:
        rates = [(rate.metal, rate.purity.upper(), rate.rate_per_gram) for rate in rates_data.rates]
        return metal_rate_repository.upsert_many(rates)


metal_rate_service = MetalRateService()
