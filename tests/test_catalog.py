from decimal import Decimal

from tests.conftest import auth


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_home_has_seed_data(client):
    data = client.get("/api/v1/home").json()["data"]
    assert len(data["metal_rates"]) == 7
    assert len(data["categories"]) == 10
    assert len(data["banners"]) == 3
    assert len(data["collections"]) == 4
    assert data["featured"] and all(product["is_featured"] for product in data["featured"])
    assert len(data["new_arrivals"]) == 10


def test_product_filters_and_sorting(client):
    rings = client.get("/api/v1/products", params={"category": "rings"}).json()["data"]
    assert rings["total"] == 3
    assert {item["category_slug"] for item in rings["items"]} == {"rings"}

    silver = client.get("/api/v1/products", params={"metal": "silver"}).json()["data"]
    assert [item["sku"] for item in silver["items"]] == ["LS-ER-003"]

    search = client.get("/api/v1/products", params={"q": "jhumka"}).json()["data"]
    assert search["total"] == 2

    cheap_first = client.get(
        "/api/v1/products", params={"sort": "price_low_to_high", "page_size": 100}
    ).json()["data"]["items"]
    prices = [item["price"] for item in cheap_first]
    assert prices == sorted(prices)

    budget = client.get("/api/v1/products", params={"max_price": 50000}).json()["data"]
    assert budget["total"] > 0
    assert all(item["price"] <= 50000 for item in budget["items"])

    page = client.get("/api/v1/products", params={"page": 2, "page_size": 5}).json()["data"]
    assert page["total"] == 16 and page["total_pages"] == 4 and len(page["items"]) == 5


def test_product_price_breakup_adds_up(client):
    ring = client.get("/api/v1/products", params={"q": "LS-RG-001"}).json()["data"]["items"][0]
    detail = client.get(f"/api/v1/products/{ring['id']}").json()["data"]
    price = detail["price_breakup"]

    metal_value = Decimal("2.900") * Decimal("9640.00")  # 18K gold sample rate
    assert price["metal_value"] == float(metal_value)
    assert price["making_charges"] == round(price["metal_value"] * 0.18, 2)
    assert price["making_discount"] == round(price["making_charges"] * 0.10, 2)
    subtotal = price["metal_value"] + price["making_charges"] - price["making_discount"] + 38000
    assert round(price["subtotal"], 2) == round(subtotal, 2)
    assert price["total"] == round(price["subtotal"] + price["gst"], 2)
    assert detail["price"] == price["total"]
    assert detail["original_price"] > detail["price"]
    assert detail["is_wishlisted"] is False


def test_unknown_product_returns_error_format(client):
    response = client.get("/api/v1/products/99999")
    assert response.status_code == 404
    assert response.json() == {"success": False, "message": "Product not found", "data": None}


def test_stores_filter_by_city(client):
    stores = client.get("/api/v1/stores", params={"city": "kochi"}).json()["data"]
    assert [store["city"] for store in stores] == ["Kochi"]


def test_admin_metal_rate_update_reprices_products(client, admin, customer):
    coin = client.get("/api/v1/products", params={"q": "LS-GC-001"}).json()["data"]["items"][0]

    forbidden = client.put(
        "/api/v1/admin/metal-rates",
        json={"rates": [{"metal": "gold", "purity": "24K", "rate_per_gram": 13000}]},
        headers=auth(customer["token"]),
    )
    assert forbidden.status_code == 403

    response = client.put(
        "/api/v1/admin/metal-rates",
        json={"rates": [{"metal": "gold", "purity": "24k", "rate_per_gram": 13000}]},
        headers=auth(admin["token"]),
    )
    assert response.status_code == 200
    new_coin = client.get(f"/api/v1/products/{coin['id']}").json()["data"]
    assert new_coin["price_breakup"]["metal_value"] == 130000.0
    assert new_coin["price"] > coin["price"]


def test_admin_product_crud(client, admin):
    category_id = client.get("/api/v1/categories").json()["data"][0]["id"]
    body = {
        "name": "Test Pendant",
        "slug": "test-pendant",
        "sku": "LS-TEST-001",
        "category_id": category_id,
        "metal": "gold",
        "purity": "22K",
        "gross_weight": 2,
        "net_weight": 2,
        "making_charge_percent": 10,
        "stock": 3,
    }
    created = client.post("/api/v1/admin/products", json=body, headers=auth(admin["token"]))
    assert created.status_code == 201, created.text
    product_id = created.json()["data"]["id"]

    duplicate = client.post("/api/v1/admin/products", json=body, headers=auth(admin["token"]))
    assert duplicate.status_code == 409

    updated = client.put(
        f"/api/v1/admin/products/{product_id}", json={"stock": 0}, headers=auth(admin["token"])
    )
    assert updated.json()["data"]["in_stock"] is False

    deleted = client.delete(f"/api/v1/admin/products/{product_id}", headers=auth(admin["token"]))
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/products/{product_id}").status_code == 404


def test_admin_upload_image(client, admin):
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    response = client.post(
        "/api/v1/admin/uploads",
        files={"file": ("ring.png", png, "image/png")},
        data={"folder": "products"},
        headers=auth(admin["token"]),
    )
    assert response.status_code == 201, response.text
    url = response.json()["data"]["url"]
    assert client.get(url).status_code == 200

    bad = client.post(
        "/api/v1/admin/uploads",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=auth(admin["token"]),
    )
    assert bad.status_code == 400

    from app.core.config import settings

    (settings.media_dir / url.removeprefix("/media/")).unlink()
