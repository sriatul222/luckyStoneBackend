from tests.conftest import auth, register


ADDRESS = {
    "full_name": "Priya Nair",
    "mobile": "9876500001",
    "line1": "12, Marine Drive",
    "city": "Kochi",
    "state": "Kerala",
    "pincode": "682031",
}


def product_by_sku(client, sku):
    return client.get("/api/v1/products", params={"q": sku}).json()["data"]["items"][0]


def test_register_validation_and_login(client, customer):
    duplicate = client.post(
        "/api/v1/auth/register",
        json={"name": "Other", "email": "PRIYA@example.com", "mobile": "9876509999", "password": "Secret@123"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["message"] == "Email already registered"

    bad_mobile = client.post(
        "/api/v1/auth/register",
        json={"name": "Other", "email": "x@example.com", "mobile": "12345", "password": "Secret@123"},
    )
    assert bad_mobile.status_code == 422
    assert bad_mobile.json()["success"] is False
    assert bad_mobile.json()["message"].startswith("mobile:")

    by_mobile = client.post("/api/v1/auth/login", json={"username": "9876500001", "password": "Secret@123"})
    assert by_mobile.status_code == 200
    assert by_mobile.json()["data"]["user"]["email"] == "priya@example.com"
    assert "password_hash" not in by_mobile.json()["data"]["user"]

    wrong = client.post("/api/v1/auth/login", json={"username": "priya@example.com", "password": "nope"})
    assert wrong.status_code == 401

    me = client.get("/api/v1/auth/me", headers=auth(customer["token"]))
    assert me.json()["data"]["role"] == "customer"


def test_login_required(client):
    response = client.get("/api/v1/cart")
    assert response.status_code == 401
    assert response.json()["success"] is False

    bad_token = client.get("/api/v1/cart", headers=auth("not-a-token"))
    assert bad_token.status_code == 401


def test_wishlist(client, customer):
    headers = auth(customer["token"])
    pendant = product_by_sku(client, "LS-PD-001")

    added = client.post("/api/v1/wishlist", json={"product_id": pendant["id"]}, headers=headers)
    assert added.status_code == 201
    client.post("/api/v1/wishlist", json={"product_id": pendant["id"]}, headers=headers)  # no duplicate
    assert [item["id"] for item in client.get("/api/v1/wishlist", headers=headers).json()["data"]] == [pendant["id"]]

    detail = client.get(f"/api/v1/products/{pendant['id']}", headers=headers).json()["data"]
    assert detail["is_wishlisted"] is True

    removed = client.delete(f"/api/v1/wishlist/{pendant['id']}", headers=headers)
    assert removed.json()["data"] == []
    assert client.delete(f"/api/v1/wishlist/{pendant['id']}", headers=headers).status_code == 404


def test_cart_order_and_cancel_flow(client, customer, admin):
    headers = auth(customer["token"])
    ring = product_by_sku(client, "LS-RG-001")  # needs a size, stock 6
    earrings = product_by_sku(client, "LS-ER-002")  # no size

    no_size = client.post("/api/v1/cart/items", json={"product_id": ring["id"]}, headers=headers)
    assert no_size.status_code == 400
    assert "size" in no_size.json()["message"]

    client.post("/api/v1/cart/items", json={"product_id": ring["id"], "size": "12"}, headers=headers)
    cart = client.post(
        "/api/v1/cart/items", json={"product_id": ring["id"], "size": "12"}, headers=headers
    ).json()["data"]
    assert len(cart["items"]) == 1 and cart["items"][0]["quantity"] == 2

    too_many = client.post(
        "/api/v1/cart/items", json={"product_id": ring["id"], "size": "12", "quantity": 5}, headers=headers
    )
    assert too_many.status_code == 400

    cart = client.post(
        "/api/v1/cart/items", json={"product_id": earrings["id"], "size": "ignored"}, headers=headers
    ).json()["data"]
    earring_item = next(item for item in cart["items"] if item["product"]["id"] == earrings["id"])
    assert earring_item["size"] == ""

    cart = client.put(f"/api/v1/cart/items/{earring_item['id']}", json={"quantity": 3}, headers=headers).json()["data"]
    summary = cart["summary"]
    assert summary["item_count"] == 2 and summary["total_quantity"] == 5
    assert summary["total"] == round(sum(item["line_total"] for item in cart["items"]), 2)
    assert round(summary["subtotal"] - summary["discount"] + summary["gst"], 2) == summary["total"]

    address = client.post("/api/v1/addresses", json=ADDRESS, headers=headers).json()["data"]
    assert address["is_default"] is True

    order_response = client.post(
        "/api/v1/orders", json={"address_id": address["id"], "payment_method": "COD"}, headers=headers
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()["data"]
    assert order["order_number"].startswith("LS")
    assert order["status"] == "PLACED" and order["item_count"] == 5
    assert order["total"] == summary["total"]
    assert order["shipping_address"]["city"] == "Kochi"

    assert client.get("/api/v1/cart", headers=headers).json()["data"]["items"] == []
    assert client.get(f"/api/v1/products/{ring['id']}").json()["data"]["stock"] == 4

    empty = client.post("/api/v1/orders", json={"address_id": address["id"]}, headers=headers)
    assert empty.status_code == 400 and empty.json()["message"] == "Your cart is empty"

    my_orders = client.get("/api/v1/orders", headers=headers).json()["data"]
    assert my_orders["total"] == 1

    other = register(client, "Rahul", "rahul@example.com", "9876500003")
    assert client.get(f"/api/v1/orders/{order['id']}", headers=auth(other["access_token"])).status_code == 404

    cancelled = client.post(f"/api/v1/orders/{order['id']}/cancel", headers=headers).json()["data"]
    assert cancelled["status"] == "CANCELLED"
    assert client.get(f"/api/v1/products/{ring['id']}").json()["data"]["stock"] == 6
    assert client.post(f"/api/v1/orders/{order['id']}/cancel", headers=headers).status_code == 400

    # Admin moves a second order through the full flow
    client.post("/api/v1/cart/items", json={"product_id": earrings["id"]}, headers=headers)
    second = client.post("/api/v1/orders", json={"address_id": address["id"]}, headers=headers).json()["data"]
    admin_headers = auth(admin["token"])

    skip = client.put(f"/api/v1/admin/orders/{second['id']}/status", json={"status": "DELIVERED"}, headers=admin_headers)
    assert skip.status_code == 400
    for status in ("CONFIRMED", "SHIPPED", "DELIVERED"):
        moved = client.put(f"/api/v1/admin/orders/{second['id']}/status", json={"status": status}, headers=admin_headers)
        assert moved.status_code == 200, moved.text
    assert moved.json()["data"]["payment_status"] == "PAID"
    assert client.post(f"/api/v1/orders/{second['id']}/cancel", headers=headers).status_code == 400

    all_orders = client.get("/api/v1/admin/orders", params={"status": "DELIVERED"}, headers=admin_headers).json()["data"]
    assert [item["id"] for item in all_orders["items"]] == [second["id"]]


def test_addresses_default_switch(client):
    user = register(client, "Anu", "anu@example.com", "9876500004")
    headers = auth(user["access_token"])

    first = client.post("/api/v1/addresses", json=ADDRESS, headers=headers).json()["data"]
    second = client.post("/api/v1/addresses", json={**ADDRESS, "is_default": True}, headers=headers).json()["data"]
    addresses = client.get("/api/v1/addresses", headers=headers).json()["data"]
    assert [a["id"] for a in addresses if a["is_default"]] == [second["id"]]

    client.delete(f"/api/v1/addresses/{second['id']}", headers=headers)
    addresses = client.get("/api/v1/addresses", headers=headers).json()["data"]
    assert addresses[0]["id"] == first["id"] and addresses[0]["is_default"] is True


def test_reviews(client, customer):
    headers = auth(customer["token"])
    chain = product_by_sku(client, "LS-CH-001")

    client.post(f"/api/v1/products/{chain['id']}/reviews", json={"rating": 3}, headers=headers)
    review = client.post(
        f"/api/v1/products/{chain['id']}/reviews", json={"rating": 5, "comment": "Beautiful!"}, headers=headers
    )
    assert review.status_code == 201

    reviews = client.get(f"/api/v1/products/{chain['id']}/reviews").json()["data"]
    assert reviews["total"] == 1 and reviews["items"][0]["user_name"] == "Priya Nair"

    detail = client.get(f"/api/v1/products/{chain['id']}").json()["data"]
    assert detail["rating"] == 5.0 and detail["review_count"] == 1

    invalid = client.post(f"/api/v1/products/{chain['id']}/reviews", json={"rating": 6}, headers=headers)
    assert invalid.status_code == 422
