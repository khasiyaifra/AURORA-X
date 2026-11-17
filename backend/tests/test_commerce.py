from decimal import Decimal
import uuid

from fastapi import status

from app.commerce import calculate_commission, calculate_refund, DEFAULT_COMMISSION_RATE


def register(client, email, role="buyer"):
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "strong-pass",
        "display_name": email.split("@")[0],
        "role": role,
    })
    assert response.status_code == status.HTTP_201_CREATED
    login = client.post("/api/auth/login", json={"email": email, "password": "strong-pass"})
    return login.json()["access_token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_store_and_product(client, token, store_name, product_name, price=1000, quantity=5):
    store = client.post("/api/stores", headers=headers(token), json={
        "name": store_name,
        "description": "Test store",
        "category": "Home",
    })
    assert store.status_code == status.HTTP_201_CREATED
    product = client.post("/api/products", headers=headers(token), json={
        "store_id": store.json()["id"],
        "category": "Home",
        "name": product_name,
        "sku": f"{store_name[:3].upper()}-{product_name[:3].upper()}-{uuid.uuid4().hex[:8]}",
        "description": "Test product",
        "price": price,
        "quantity": quantity,
    })
    assert product.status_code == status.HTTP_201_CREATED
    return store.json(), product.json()


def test_decimal_commission_standard_discount_and_precision():
    commission, seller = calculate_commission(Decimal("10000.00"), Decimal("0.0300"))
    assert commission == Decimal("300.00")
    assert seller == Decimal("9700.00")

    discounted_eligible = Decimal("10000.00") - Decimal("1000.00")
    commission, seller = calculate_commission(discounted_eligible)
    assert commission == Decimal("270.00")
    assert seller == Decimal("8730.00")
    assert DEFAULT_COMMISSION_RATE == Decimal("0.0300")

    commission, seller = calculate_commission(Decimal("0.05"), Decimal("0.0300"))
    assert commission == Decimal("0.00")
    assert seller == Decimal("0.05")

    net_refund, commission_reversal = calculate_refund(Decimal("100.00"), Decimal("10000.00"))
    assert net_refund == Decimal("97.00")
    assert commission_reversal == Decimal("3.00")


def test_cart_validation_multi_seller_checkout_and_idempotency(client):
    buyer = register(client, "buyer-commerce@example.com")
    seller1 = register(client, "seller-one@example.com", "seller")
    seller2 = register(client, "seller-two@example.com", "seller")
    _, product1 = create_store_and_product(client, seller1, "First Store", "Lamp", 1000, 5)
    _, product2 = create_store_and_product(client, seller2, "Second Store", "Chair", 2000, 3)

    add1 = client.post("/api/cart/items", headers=headers(buyer), json={"product_id": product1["id"], "quantity": 2})
    add2 = client.post("/api/cart/items", headers=headers(buyer), json={"product_id": product2["id"], "quantity": 1})
    assert add1.status_code == status.HTTP_201_CREATED
    assert add2.status_code == status.HTTP_201_CREATED

    cart = client.get("/api/cart", headers=headers(buyer))
    assert cart.status_code == status.HTTP_200_OK
    assert len(cart.json()["items"]) == 2
    assert set(item["store_id"] for item in cart.json()["items"]) == {product1["store_id"], product2["store_id"]}

    checkout_payload = {
        "idempotency_key": "checkout-key-001",
        "discount_code": "AURORA10",
        "address": {
            "recipient_name": "Test Buyer",
            "phone": "9999999999",
            "line1": "1 Market Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
        },
    }
    first = client.post("/api/checkout", headers=headers(buyer), json=checkout_payload)
    assert first.status_code == status.HTTP_201_CREATED
    order = first.json()
    assert len(order["seller_orders"]) == 2
    assert order["subtotal"] == "4000.00"
    assert order["discount_total"] == "400.00"
    assert order["shipping_total"] == "198.00"
    assert order["total"] == "3798.00"

    second = client.post("/api/checkout", headers=headers(buyer), json=checkout_payload)
    assert second.status_code == status.HTTP_201_CREATED
    assert second.json()["id"] == order["id"]

    buyer_orders = client.get("/api/orders", headers=headers(buyer))
    assert buyer_orders.status_code == status.HTTP_200_OK
    assert len(buyer_orders.json()) == 1


def test_inventory_validation_oversell_and_failed_checkout_leave_stock(client):
    buyer = register(client, "buyer-stock@example.com")
    seller = register(client, "seller-stock@example.com", "seller")
    _, product = create_store_and_product(client, seller, "Stock Store", "Pen", 25, 2)

    over_cart = client.post("/api/cart/items", headers=headers(buyer), json={"product_id": product["id"], "quantity": 3})
    assert over_cart.status_code == status.HTTP_409_CONFLICT

    added = client.post("/api/cart/items", headers=headers(buyer), json={"product_id": product["id"], "quantity": 2})
    assert added.status_code == status.HTTP_201_CREATED
    no_address = client.post("/api/checkout", headers=headers(buyer), json={
        "idempotency_key": "checkout-key-002",
        "address": {
            "recipient_name": "Buyer",
            "phone": "1234567890",
            "line1": "Address",
            "city": "City",
            "state": "State",
            "postal_code": "123456",
        },
    })
    assert no_address.status_code == status.HTTP_201_CREATED
    inventory_product = client.get(f"/api/products/{product['id']}")
    assert inventory_product.json()["quantity"] == 0


def test_seller_isolation_status_transition_cancellation_and_inventory_rollback(client):
    buyer = register(client, "buyer-flow@example.com")
    seller1 = register(client, "seller-flow-one@example.com", "seller")
    seller2 = register(client, "seller-flow-two@example.com", "seller")
    store1, product1 = create_store_and_product(client, seller1, "Flow One", "Item One", 500, 4)
    _, product2 = create_store_and_product(client, seller2, "Flow Two", "Item Two", 700, 4)

    client.post("/api/cart/items", headers=headers(buyer), json={"product_id": product1["id"], "quantity": 1})
    client.post("/api/cart/items", headers=headers(buyer), json={"product_id": product2["id"], "quantity": 1})
    order = client.post("/api/checkout", headers=headers(buyer), json={
        "idempotency_key": "checkout-key-003",
        "address": {
            "recipient_name": "Flow Buyer",
            "phone": "9876543210",
            "line1": "Flow Address",
            "city": "Pune",
            "state": "Maharashtra",
            "postal_code": "411001",
        },
    }).json()

    seller1_rows = client.get("/api/seller/orders", headers=headers(seller1)).json()
    seller2_rows = client.get("/api/seller/orders", headers=headers(seller2)).json()
    assert len(seller1_rows) == 1
    assert len(seller2_rows) == 1
    assert seller1_rows[0]["store_id"] != seller2_rows[0]["store_id"]

    accepted = client.patch(
        f"/api/seller/orders/{seller1_rows[0]['id']}",
        headers=headers(seller1),
        json={"status": "ACCEPTED"},
    )
    assert accepted.status_code == status.HTTP_200_OK
    assert accepted.json()["status"] == "ACCEPTED"

    wrong_seller = client.patch(
        f"/api/seller/orders/{seller1_rows[0]['id']}",
        headers=headers(seller2),
        json={"status": "PROCESSING"},
    )
    assert wrong_seller.status_code == status.HTTP_404_NOT_FOUND

    cancelled = client.post(f"/api/orders/{order['id']}/cancel", headers=headers(buyer))
    assert cancelled.status_code == status.HTTP_200_OK
    assert cancelled.json()["status"] == "CANCELLED"
    restored_product = client.get(f"/api/products/{product1['id']}").json()
    restored_product2 = client.get(f"/api/products/{product2['id']}").json()
    assert restored_product["quantity"] == 4
    assert restored_product2["quantity"] == 4

    other_buyer = register(client, "buyer-other@example.com")
    assert client.get(f"/api/orders/{order['id']}", headers=headers(other_buyer)).status_code == status.HTTP_404_NOT_FOUND
