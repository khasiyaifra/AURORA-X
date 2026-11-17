from abc import ABC, abstractmethod
import hmac
import hashlib
from fastapi import HTTPException

from app.config import get_settings


class PaymentProvider(ABC):
    @abstractmethod
    def create_pending_payment(self, amount: str, currency: str = "INR") -> dict:
        """Create provider intent or return a demo pending payment."""


class DemoPaymentProvider(PaymentProvider):
    def create_pending_payment(self, amount: str, currency: str = "INR") -> dict:
        return {
            "status": "PENDING",
            "provider": "demo",
            "amount": amount,
            "currency": currency,
            "provider_reference": None,
        }


class RazorpayPaymentProvider(PaymentProvider):
    def create_pending_payment(self, amount: str, currency: str = "INR") -> dict:
        settings = get_settings()
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise HTTPException(status_code=503, detail="Razorpay sandbox credentials are not configured")
        # Provider SDK/API call is intentionally not attempted without an order context.
        return {
            "status": "CONFIGURED_NOT_CREATED",
            "provider": "razorpay",
            "amount": amount,
            "currency": currency,
            "provider_reference": None,
        }


def verify_razorpay_signature(raw_body: bytes, signature: str) -> bool:
    settings = get_settings()
    secret = settings.webhook_secret
    if not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
