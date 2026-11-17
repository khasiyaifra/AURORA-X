import os
import subprocess
import sys

from fastapi import status


def register(client, email="buyer@example.com", password="strong-pass", role="buyer"):
    return client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "display_name": "Aurora User",
        "role": role,
    })


def login(client, email="buyer@example.com", password="strong-pass"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_registration_login_me_and_logout(client):
    registered = register(client)
    assert registered.status_code == status.HTTP_201_CREATED
    logged_in = login(client)
    assert logged_in.status_code == status.HTTP_200_OK
    token = logged_in.json()["access_token"]

    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.status_code == status.HTTP_200_OK
    assert me.json()["email"] == "buyer@example.com"

    logout = client.post("/api/auth/logout", headers=auth_headers(token))
    assert logout.status_code == status.HTTP_204_NO_CONTENT
    assert client.get("/api/auth/me", headers=auth_headers(token)).status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_credentials(client):
    register(client)
    response = login(client, password="wrong-password")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_duplicate_email(client):
    assert register(client).status_code == status.HTTP_201_CREATED
    assert register(client).status_code == status.HTTP_409_CONFLICT


def test_role_permissions_and_store_creation(client):
    assert register(client, "buyer2@example.com", role="buyer").status_code == status.HTTP_201_CREATED
    buyer_token = login(client, "buyer2@example.com").json()["access_token"]
    buyer_store = client.post("/api/stores", headers=auth_headers(buyer_token), json={
        "name": "Buyer Store",
        "category": "Home",
    })
    assert buyer_store.status_code == status.HTTP_403_FORBIDDEN

    assert register(client, "seller@example.com", role="seller").status_code == status.HTTP_201_CREATED
    seller_token = login(client, "seller@example.com").json()["access_token"]
    seller_store = client.post("/api/stores", headers=auth_headers(seller_token), json={
        "name": "Seller Studio",
        "description": "Considered goods",
        "category": "Home",
    })
    assert seller_store.status_code == status.HTTP_201_CREATED
    assert client.get("/api/stores").json()[0]["name"] == "Seller Studio"


def test_product_creation_ownership_update_and_delete(client):
    assert register(client, "seller1@example.com", role="seller").status_code == status.HTTP_201_CREATED
    token1 = login(client, "seller1@example.com").json()["access_token"]
    store1 = client.post("/api/stores", headers=auth_headers(token1), json={"name": "One", "category": "Home"})
    store1_id = store1.json()["id"]

    created = client.post("/api/products", headers=auth_headers(token1), json={
        "store_id": store1_id,
        "category": "Home",
        "name": "Desk Lamp",
        "description": "Warm light",
        "price": 2500,
        "quantity": 12,
    })
    assert created.status_code == status.HTTP_201_CREATED
    product_id = created.json()["id"]

    assert register(client, "seller2@example.com", role="seller").status_code == status.HTTP_201_CREATED
    token2 = login(client, "seller2@example.com").json()["access_token"]
    assert client.patch(
        f"/api/products/{product_id}",
        headers=auth_headers(token2),
        json={"name": "Stolen Lamp"},
    ).status_code == status.HTTP_403_FORBIDDEN

    updated = client.patch(
        f"/api/products/{product_id}",
        headers=auth_headers(token1),
        json={"name": "Updated Lamp", "quantity": 8},
    )
    assert updated.status_code == status.HTTP_200_OK
    assert updated.json()["name"] == "Updated Lamp"
    assert updated.json()["quantity"] == 8

    deleted = client.delete(f"/api/products/{product_id}", headers=auth_headers(token1))
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert client.get(f"/api/products/{product_id}").status_code == status.HTTP_404_NOT_FOUND


def test_alembic_migration(tmp_path):
    database_file = tmp_path / "migration.db"
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{database_file}"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert database_file.exists()
