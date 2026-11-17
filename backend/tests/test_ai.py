from fastapi import status

from app.ai_service import extract_intent, rank_products


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


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_product(client, token, name, category="Electronics", price=50000, quantity=5):
    store = client.post("/api/stores", headers=auth(token), json={
        "name": f"Store {name}",
        "category": category,
    })
    if store.status_code == status.HTTP_409_CONFLICT:
        stores = client.get("/api/stores").json()
        store_name = f"Store {name}"
        existing = next((item for item in stores if item["name"] == store_name), None)
        if existing is None:
            stores = client.get("/api/stores").json()
            existing = stores[0]
        store_id = existing["id"]
    else:
        assert store.status_code == status.HTTP_201_CREATED
        store_id = store.json()["id"]
    product = client.post("/api/products", headers=auth(token), json={
        "store_id": store_id,
        "category": category,
        "name": name,
        "description": "Laptop for Python machine learning and gaming",
        "price": price,
        "quantity": quantity,
    })
    assert product.status_code == status.HTTP_201_CREATED
    return product.json()


def test_intent_budget_category_and_specs():
    intent = extract_intent("I need a laptop for AI engineering under ₹85,000 with 16GB")
    assert intent["category"] == "Electronics"
    assert intent["budget"] == "85000"
    assert "16gb" in intent["specifications"]


def test_semantic_search_uses_actual_database_and_budget(client):
    seller = register(client, "ai-seller@example.com", "seller")
    suitable = create_product(client, seller, "Aurora ML Laptop", "Electronics", 80000, 4)
    create_product(client, seller, "Aurora Desktop", "Electronics", 120000, 2)

    response = client.post("/api/ai/search", json={
        "q": "laptop for Python machine learning under ₹85000",
        "limit": 10,
        "session_key": "test",
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["mode"] == "deterministic local fallback"
    assert data["intent"]["budget"] == "85000"
    assert any(result["id"] == suitable["id"] for result in data["results"])
    assert all(float(result["price"]) <= 85000 for result in data["results"])


def test_copilot_never_executes_purchase(client):
    buyer = register(client, "ai-buyer@example.com")
    seller = register(client, "ai-copilot-seller@example.com", "seller")
    create_product(client, seller, "Gaming Laptop", "Electronics", 70000, 3)

    response = client.post("/api/ai/copilot", headers=auth(buyer), json={
        "message": "I need a gaming laptop with Python support under ₹90000",
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["mode"] == "deterministic local fallback"
    assert data["purchase_executed"] is False
    assert len(data["products"]) >= 1


def test_comparison_and_seller_isolation(client):
    seller1 = register(client, "compare-seller-1@example.com", "seller")
    seller2 = register(client, "compare-seller-2@example.com", "seller")
    buyer = register(client, "compare-buyer@example.com")
    product1 = create_product(client, seller1, "Value Laptop", "Electronics", 60000, 2)
    product2 = create_product(client, seller2, "Gaming Laptop", "Electronics", 70000, 1)

    comparison = client.post("/api/ai/compare", headers=auth(buyer), json={
        "product_ids": [product1["id"], product2["id"]],
    })
    assert comparison.status_code == status.HTTP_200_OK
    data = comparison.json()
    assert data["best_budget"] == product1["id"]
    assert len(data["products"]) == 2
    assert "Warranty and return policy" in data["disadvantages"][0]

    seller_tool = client.post("/api/ai/seller/tool", headers=auth(seller1), json={
        "tool": "title",
        "product_name": "Value Laptop",
        "category": "Electronics",
        "price": "60000",
    })
    assert seller_tool.status_code == status.HTTP_200_OK
    assert seller_tool.json()["label"] == "LOCAL FALLBACK"


def test_personalisation_controls_and_recommendations(client):
    buyer = register(client, "personal-buyer@example.com")
    disable = client.post("/api/ai/personalization", headers=auth(buyer), json={
        "enabled": False,
        "preferred_categories": ["Electronics"],
    })
    assert disable.status_code == status.HTTP_200_OK
    recommendations = client.get("/api/ai/recommendations", headers=auth(buyer))
    assert recommendations.status_code == status.HTTP_200_OK
    assert recommendations.json()["enabled"] is False
    assert recommendations.json()["results"] == []


def test_trustshield_returns_explainable_warnings(client):
    seller = register(client, "trust-seller@example.com", "seller")
    create_product(client, seller, "Repeated Listing", "Home", 1000, 1)
    create_product(client, seller, "Repeated Listing", "Home", 1000, 1)

    response = client.get("/api/ai/trustshield", headers=auth(seller))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["automatic_penalties"] is False
    assert any(warning["signal"] == "duplicate_listing" for warning in data["warnings"])
    assert all("reason" in warning and "confidence" in warning for warning in data["warnings"])
