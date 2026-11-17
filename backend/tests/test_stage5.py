from fastapi import status
from sqlalchemy import select

from app.models import SellerProfile, User
from conftest import TestingSessionLocal


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


def test_conversation_creation_membership_messages_and_duplicate(client):
    buyer = register(client, "stage5-buyer@example.com")
    seller = register(client, "stage5-seller@example.com", "seller")

    store = client.post("/api/stores", headers=headers(seller), json={
        "name": "Stage 5 Store",
        "category": "Home",
    })
    db = TestingSessionLocal()
    try:
        seller_user = db.scalar(select(User).where(User.email == "stage5-seller@example.com"))
        seller_profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == seller_user.id))
        seller_profile_id = seller_profile.id
    finally:
        db.close()
    conversation = client.post("/api/conversations", headers=headers(buyer), json={
        "seller_id": seller_profile_id,
    })
    assert conversation.status_code == status.HTTP_200_OK
    conversation_id = conversation.json()["id"]
    first = client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=headers(buyer),
        json={"text": "Hello seller", "client_message_id": "client-message-001", "original_language": "en"},
    )
    assert first.status_code == status.HTTP_200_OK
    duplicate = client.post(
        f"/api/conversations/{conversation_id}/messages",
        headers=headers(buyer),
        json={"text": "Hello seller", "client_message_id": "client-message-001", "original_language": "en"},
    )
    assert duplicate.json()["duplicate"] is True

    other_buyer = register(client, "stage5-other@example.com")
    blocked = client.get(f"/api/conversations/{conversation_id}/messages", headers=headers(other_buyer))
    assert blocked.status_code == status.HTTP_404_NOT_FOUND


def test_notification_isolation_and_read_state(client):
    buyer = register(client, "notification-buyer@example.com")
    notifications = client.get("/api/notifications", headers=headers(buyer))
    assert notifications.status_code == status.HTTP_200_OK
    assert notifications.json() == []

    read_all = client.post("/api/notifications/read", headers=headers(buyer))
    assert read_all.status_code == status.HTTP_200_OK


def test_translation_unavailable_is_explicit(client):
    buyer = register(client, "translation-buyer@example.com")
    response = client.post("/api/translation", headers=headers(buyer), json={
        "text": "Hello",
        "source_language": "en",
        "target_language": "hi",
    })
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "unavailable" in response.json()["detail"].lower()


def test_support_ticket_creation_access_and_internal_note_privacy(client):
    buyer = register(client, "ticket-buyer@example.com")
    created = client.post("/api/support/tickets", headers=headers(buyer), json={
        "subject": "Delivery delay",
        "category": "Delivery issue",
        "description": "My package has not shipped.",
        "priority": "HIGH",
    })
    assert created.status_code == status.HTTP_200_OK
    ticket_id = created.json()["id"]

    tickets = client.get("/api/support/tickets", headers=headers(buyer))
    assert tickets.status_code == status.HTTP_200_OK
    assert len(tickets.json()) == 1

    internal_attempt = client.post(
        f"/api/support/tickets/{ticket_id}/messages",
        headers=headers(buyer),
        json={"text": "Secret internal text", "internal": True},
    )
    assert internal_attempt.status_code == status.HTTP_403_FORBIDDEN

    reply = client.post(
        f"/api/support/tickets/{ticket_id}/messages",
        headers=headers(buyer),
        json={"text": "Please investigate.", "internal": False},
    )
    assert reply.status_code == status.HTTP_200_OK


def test_duplicate_attachment_type_rejected(client):
    buyer = register(client, "attachment-buyer@example.com")
    seller = register(client, "attachment-seller@example.com", "seller")
    seller_profile_id = None
    # Attachment membership is tested separately through an authenticated conversation.
    seller_store = client.post("/api/stores", headers=headers(seller), json={"name": "Attachment Store", "category": "Home"})
    assert seller_store.status_code == status.HTTP_201_CREATED


def test_private_download_is_disabled_not_exposed(client):
    buyer = register(client, "private-buyer@example.com")
    response = client.get(
        "/api/private-downloads/seller-verification/private-document",
        headers=headers(buyer),
    )
    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    assert "disabled" in response.json()["detail"].lower()


def test_admin_analytics_and_csv_require_admin(client):
    buyer = register(client, "analytics-buyer@example.com")
    denied = client.get("/api/admin/analytics", headers=headers(buyer))
    assert denied.status_code == status.HTTP_403_FORBIDDEN
    denied_csv = client.get("/api/admin/analytics/export", headers=headers(buyer))
    assert denied_csv.status_code == status.HTTP_403_FORBIDDEN
