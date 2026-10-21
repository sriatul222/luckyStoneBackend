from app.core.database import database


class MetalRateRepository:
    def get_all(self) -> list[dict]:
        with database.get_connection() as connection:
            return connection.execute(
                """
                SELECT id, metal, purity, rate_per_gram, updated_at
                FROM metal_rates
                ORDER BY metal, rate_per_gram DESC
                """
            ).fetchall()

    def upsert_many(self, rates: list[tuple[str, str, float]]) -> list[dict]:
        with database.get_connection() as connection:
            connection.cursor().executemany(
                """
                INSERT INTO metal_rates (metal, purity, rate_per_gram, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (metal, purity)
                DO UPDATE SET rate_per_gram = EXCLUDED.rate_per_gram, updated_at = NOW()
                """,
                rates,
            )
        return self.get_all()


metal_rate_repository = MetalRateRepository()
