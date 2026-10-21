import os

# Tests use their own database, never the real luckystone_db
os.environ["POSTGRES_DB"] = "luckystone_test_db"

import psycopg  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402


def _drop_test_database():
    assert settings.postgres_db == "luckystone_test_db"
    with psycopg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        # "postgres", or "defaultdb" on Aiven (POSTGRES_MAINTENANCE_DB in .env)
        dbname=settings.postgres_maintenance_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        autocommit=True,
        connect_timeout=10,
    ) as connection:
        connection.execute("DROP DATABASE IF EXISTS luckystone_test_db WITH (FORCE)")


@pytest.fixture(scope="session")
def client():
    _drop_test_database()
    from app.main import app

    with TestClient(app) as test_client:  # runs startup: create db + tables + seed
        yield test_client
    _drop_test_database()


def register(client, name, email, mobile, password="Secret@123"):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "mobile": mobile, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def customer(client):
    data = register(client, "Priya Nair", "priya@example.com", "9876500001")
    return {"token": data["access_token"], "user": data["user"]}


@pytest.fixture(scope="session")
def admin(client):
    from app.repositories.user_repository import user_repository

    data = register(client, "Store Admin", "admin@example.com", "9876500002")
    user_repository.set_role(data["user"]["id"], "admin")
    login = client.post(
        "/api/v1/auth/login", json={"username": "admin@example.com", "password": "Secret@123"}
    )
    return {"token": login.json()["data"]["access_token"], "user": data["user"]}
