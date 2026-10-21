import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseModel):
    project_name: str = "Lucky Stone API"
    api_prefix: str = "/api/v1"

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "luckystone_db")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    # Database to connect to when creating / dropping ours: "postgres" on a
    # normal server, "defaultdb" on Aiven (it has no "postgres" database)
    postgres_maintenance_db: str = os.getenv("POSTGRES_MAINTENANCE_DB", "postgres")

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-env")
    jwt_algorithm: str = "HS256"
    # Mobile app keeps the user logged in for 30 days
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 30))
    )

    # GST on gold / diamond / silver jewellery in India
    gst_percent: float = float(os.getenv("GST_PERCENT", "3"))

    media_dir: Path = BASE_DIR / "media"
    media_url: str = "/media"
    max_upload_size_mb: int = 5

    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")


settings = Settings()
