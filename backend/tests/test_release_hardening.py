import hashlib
import hmac
import os

from fastapi import status

from app.config import Settings
from app.config import get_settings
from app.payment import verify_razorpay_signature


def test_production_rejects_weak_jwt_secret():
    settings = Settings(
        environment="development",
        jwt_secret="change-me-in-production",
        cors_origins="http://localhost:5173",
    )
    assert len(settings.jwt_secret) < 32


def test_razorpay_signature_verification(client):
    os.environ["WEBHOOK_SECRET"] = "release-test-webhook-secret"
    get_settings.cache_clear()
    body = b'{"event_id":"evt_test","event":"payment.captured"}'
    signature = hmac.new(b"release-test-webhook-secret", body, hashlib.sha256).hexdigest()
    assert verify_razorpay_signature(body, signature) is True
    assert verify_razorpay_signature(body, "invalid") is False

    response = client.post(
        "/api/payments/webhooks/razorpay",
        content=body,
        headers={"x-razorpay-signature": "invalid"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ready_endpoint_and_private_download(client):
    ready = client.get("/api/ready")
    assert ready.status_code == status.HTTP_200_OK
    assert ready.json()["status"] == "ready"


def test_environment_secret_not_present_in_repository():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env_path = os.path.join(root, "backend", ".env")
    assert not os.path.exists(env_path)
