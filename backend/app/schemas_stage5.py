from datetime import datetime
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    seller_id: str
    order_id: str | None = None
    product_id: str | None = None


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    client_message_id: str = Field(min_length=8, max_length=128)
    original_language: str = Field(default="en", max_length=12)


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source_language: str = Field(default="auto", max_length=12)
    target_language: str = Field(min_length=2, max_length=12)


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str
    read_at: datetime | None
    created_at: datetime


class VerificationCreate(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    business_details: str = Field(default="", max_length=5000)


class VerificationDecision(BaseModel):
    status: str = Field(pattern="^(APPROVED|REJECTED|MORE_INFO_REQUIRED)$")
    review_notes: str = Field(max_length=5000, default="")


class ModerationDecision(BaseModel):
    status: str = Field(pattern="^(APPROVED|REJECTED|NEEDS_REVIEW)$")
    policy_category: str | None = Field(default=None, max_length=80)
    decision_note: str = Field(default="", max_length=5000)


class SupportTicketCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=10000)
    order_id: str | None = None
    priority: str = Field(default="NORMAL", pattern="^(LOW|NORMAL|HIGH|URGENT)$")


class SupportTicketUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(OPEN|ASSIGNED|ESCALATED|RESOLVED|REOPENED)$")
    priority: str | None = Field(default=None, pattern="^(LOW|NORMAL|HIGH|URGENT)$")
    assigned_agent_id: str | None = None
    resolution_summary: str | None = Field(default=None, max_length=10000)


class SupportMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    internal: bool = False


class DisputeCreate(BaseModel):
    order_id: str
    reason: str = Field(min_length=1, max_length=10000)


class DisputeSellerResponse(BaseModel):
    seller_response: str = Field(min_length=1, max_length=10000)


class DisputeDecision(BaseModel):
    status: str = Field(pattern="^(UNDER_REVIEW|AWAITING_BUYER|RESOLVED|REJECTED|ESCALATED)$")
    decision: str = Field(min_length=1, max_length=10000)
    refund_recommendation: str = Field(default="NONE", pattern="^(NONE|FULL|PARTIAL)$")
