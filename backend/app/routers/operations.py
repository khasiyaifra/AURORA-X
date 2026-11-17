import json
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user, require_admin, require_buyer, require_seller
from app.models import (
    AuditLog, BuyerProfile, Conversation, Dispute, DisputeEvidence, Message, Notification,
    Order, Product, ProductModeration, SellerProfile, SellerVerification, SupportMessage,
    SupportTicket, TrustShieldAlert, User,
)
from app.schemas_stage5 import *

router = APIRouter(tags=["stage5"])

ALLOWED_ATTACHMENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024


def buyer_profile(db: Session, user: User) -> BuyerProfile:
    profile = db.scalar(select(BuyerProfile).where(BuyerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Buyer profile missing")
    return profile


def seller_profile(db: Session, user: User) -> SellerProfile:
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Seller profile missing")
    return profile


def conversation_member(db: Session, conversation: Conversation, user: User) -> bool:
    if user.role.name == "admin":
        return True
    buyer = db.scalar(select(BuyerProfile).where(BuyerProfile.id == conversation.buyer_id))
    seller = db.scalar(select(SellerProfile).where(SellerProfile.id == conversation.seller_id))
    return (buyer is not None and buyer.user_id == user.id) or (seller is not None and seller.user_id == user.id)


def audit(db: Session, actor_id: str | None, action: str, resource_type: str, resource_id: str | None, details: dict):
    db.add(AuditLog(actor_id=actor_id, action=action, resource_type=resource_type,
                    resource_id=resource_id, details_json=json.dumps(details, ensure_ascii=True)))


@router.post("/api/conversations")
def create_conversation(payload: ConversationCreate, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    buyer = buyer_profile(db, user)
    seller = db.get(SellerProfile, payload.seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="Seller not found")
    conversation = db.scalar(select(Conversation).where(
        Conversation.buyer_id == buyer.id,
        Conversation.seller_id == seller.id,
        Conversation.order_id == payload.order_id,
        Conversation.product_id == payload.product_id,
    ))
    if conversation is None:
        conversation = Conversation(
            buyer_id=buyer.id,
            seller_id=seller.id,
            order_id=payload.order_id,
            product_id=payload.product_id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return {"id": conversation.id, "buyer_id": conversation.buyer_id, "seller_id": conversation.seller_id,
            "order_id": conversation.order_id, "product_id": conversation.product_id}


@router.get("/api/conversations")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role.name == "admin":
        conversations = db.scalars(select(Conversation).order_by(Conversation.updated_at.desc())).all()
    elif user.role.name == "buyer":
        buyer = buyer_profile(db, user)
        conversations = db.scalars(select(Conversation).where(Conversation.buyer_id == buyer.id).order_by(Conversation.updated_at.desc())).all()
    elif user.role.name == "seller":
        seller = seller_profile(db, user)
        conversations = db.scalars(select(Conversation).where(Conversation.seller_id == seller.id).order_by(Conversation.updated_at.desc())).all()
    else:
        conversations = []
    return [{"id": item.id, "buyer_id": item.buyer_id, "seller_id": item.seller_id,
             "order_id": item.order_id, "product_id": item.product_id,
             "archived": item.archived_by_buyer or item.archived_by_seller} for item in conversations]


@router.get("/api/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or not conversation_member(db, conversation, user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)).all()
    return [{"id": message.id, "sender_id": message.sender_id, "text": message.text,
             "original_language": message.original_language, "client_message_id": message.client_message_id,
             "delivered_at": message.delivered_at, "read_at": message.read_at,
             "attachment_name": message.attachment_name,
             "has_attachment": message.attachment_path is not None,
             "created_at": message.created_at} for message in messages]


@router.post("/api/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, payload: MessageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or not conversation_member(db, conversation, user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    existing = db.scalar(select(Message).where(
        Message.conversation_id == conversation_id,
        Message.client_message_id == payload.client_message_id,
    ))
    if existing:
        return {"id": existing.id, "duplicate": True}
    message = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        client_message_id=payload.client_message_id,
        text=payload.text,
        original_language=payload.original_language,
        delivered_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    recipient_ids = []
    if user.role.name == "buyer":
        seller = db.get(SellerProfile, conversation.seller_id)
        if seller:
            recipient_ids.append(seller.user_id)
    elif user.role.name == "seller":
        buyer = db.get(BuyerProfile, conversation.buyer_id)
        if buyer:
            recipient_ids.append(buyer.user_id)
    for recipient_id in recipient_ids:
        db.add(Notification(user_id=recipient_id, type="NEW_MESSAGE",
                            title="New marketplace message",
                            body="You received a new buyer-seller message.",
                            reference_type="conversation", reference_id=conversation.id))
    db.commit()
    return {"id": message.id, "duplicate": False}


@router.post("/api/conversations/{conversation_id}/read")
def mark_conversation_read(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or not conversation_member(db, conversation, user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    for message in db.scalars(select(Message).where(Message.conversation_id == conversation_id, Message.sender_id != user.id)).all():
        if message.read_at is None:
            message.read_at = datetime.utcnow()
    db.commit()
    return {"status": "read"}


@router.post("/api/conversations/{conversation_id}/attachments")
async def upload_attachment(conversation_id: str, file: UploadFile = File(...),
                            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or not conversation_member(db, conversation, user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    content = await file.read(MAX_ATTACHMENT_SIZE + 1)
    if len(content) > MAX_ATTACHMENT_SIZE:
        raise HTTPException(status_code=413, detail="Attachment exceeds 5 MB")
    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(status_code=415, detail="Attachment type is not allowed")
    settings = get_settings()
    os.makedirs(settings.private_upload_dir, exist_ok=True)
    safe_name = os.path.basename(file.filename or "attachment")
    stored_name = f"{uuid.uuid4().hex}-{safe_name}"
    path = os.path.join(settings.private_upload_dir, stored_name)
    with open(path, "wb") as output:
        output.write(content)
    message = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        client_message_id=f"upload-{uuid.uuid4().hex}",
        text="",
        delivered_at=datetime.utcnow(),
        attachment_name=safe_name,
        attachment_path=path,
        attachment_type=file.content_type,
        attachment_size=len(content),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"id": message.id, "attachment_name": safe_name, "has_attachment": True}


@router.post("/api/translation")
def translate(payload: TranslateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.translation_provider != "configured" or not settings.translation_api_url:
        raise HTTPException(status_code=503,
                            detail="Translation is unavailable: no translation provider is configured")
    # Provider implementation intentionally requires credentials and preserves original text.
    raise HTTPException(status_code=503, detail="Translation provider integration is not configured")


@router.get("/api/notifications")
def notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())).all()
    return [{"id": row.id, "type": row.type, "title": row.title, "body": row.body,
             "read_at": row.read_at, "created_at": row.created_at} for row in rows]


@router.post("/api/notifications/read")
def mark_notifications_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for row in db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))).all():
        row.read_at = datetime.utcnow()
    db.commit()
    return {"status": "all_read"}


@router.post("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.read_at = datetime.utcnow()
    db.commit()
    return {"status": "read"}


@router.post("/api/seller/verification")
def create_verification(payload: VerificationCreate, user: User = Depends(require_seller), db: Session = Depends(get_db)):
    seller = seller_profile(db, user)
    existing = db.scalar(select(SellerVerification).where(SellerVerification.seller_id == seller.id).order_by(SellerVerification.created_at.desc()))
    if existing and existing.status in {"PENDING", "MORE_INFO_REQUIRED"}:
        raise HTTPException(status_code=409, detail="A verification request is already active")
    request = SellerVerification(
        seller_id=seller.id,
        business_name=payload.business_name,
        business_details=payload.business_details,
        status="PENDING",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    audit(db, user.id, "SELLER_VERIFICATION_REQUESTED", "seller_verification", request.id, {})
    db.commit()
    return {"id": request.id, "status": request.status}


@router.get("/api/admin/verifications")
def verification_queue(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(SellerVerification).order_by(SellerVerification.created_at.desc())).all()
    return [{"id": row.id, "seller_id": row.seller_id, "business_name": row.business_name,
             "status": row.status, "review_notes": row.review_notes,
             "created_at": row.created_at} for row in rows]


@router.patch("/api/admin/verifications/{request_id}")
def decide_verification(request_id: str, payload: VerificationDecision,
                        user: User = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(SellerVerification, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Verification request not found")
    row.status = payload.status
    row.reviewer_id = user.id
    row.review_notes = payload.review_notes
    audit(db, user.id, "SELLER_VERIFICATION_DECISION", "seller_verification", row.id,
          {"status": payload.status, "note": bool(payload.review_notes)})
    db.commit()
    return {"id": row.id, "status": row.status}


@router.get("/api/admin/moderation")
def moderation_queue(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(ProductModeration).order_by(ProductModeration.created_at.desc())).all()
    return [{"id": row.id, "product_id": row.product_id, "status": row.status,
             "policy_category": row.policy_category, "decision_note": row.decision_note}
            for row in rows]


@router.post("/api/admin/moderation/{product_id}")
def moderate_product(product_id: str, payload: ModerationDecision,
                     user: User = Depends(require_admin), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    row = db.scalar(select(ProductModeration).where(ProductModeration.product_id == product_id))
    if row is None:
        row = ProductModeration(product_id=product_id)
        db.add(row)
    row.status = payload.status
    row.policy_category = payload.policy_category
    row.decision_note = payload.decision_note
    row.reviewer_id = user.id
    audit(db, user.id, "PRODUCT_MODERATION_DECISION", "product", product_id,
          {"status": payload.status, "policy_category": payload.policy_category})
    db.commit()
    return {"id": row.id, "status": row.status}


@router.get("/api/trustshield/seller")
def calculate_seller_trustshield(user: User = Depends(require_seller), db: Session = Depends(get_db)):
    seller = seller_profile(db, user)
    stores = seller.stores
    product_count = sum(len(store.products) for store in stores)
    evidence = {
        "account_age_days": max((datetime.utcnow() - seller.created_at).days, 0),
        "verification_status": "NOT_RECORDED",
        "product_count": product_count,
    }
    verification = db.scalar(select(SellerVerification).where(SellerVerification.seller_id == seller.id).order_by(SellerVerification.created_at.desc()))
    if verification:
        evidence["verification_status"] = verification.status
    risk = "LOW" if evidence["account_age_days"] >= 30 and verification and verification.status == "APPROVED" else "MEDIUM"
    reason = "Automated evidence includes account age and recorded verification status only."
    alert = TrustShieldAlert(
        seller_id=seller.id,
        risk_level=risk,
        evidence_json=json.dumps(evidence),
        reason=reason,
        confidence="EVIDENCE_LIMITED",
        calculated_at=datetime.utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {"id": alert.id, "risk_level": alert.risk_level, "evidence": evidence,
            "reason": alert.reason, "confidence": alert.confidence,
            "calculated_at": alert.calculated_at, "human_review_status": alert.human_review_status,
            "verified_facts": ["Recorded account age", "Recorded verification status"] ,
            "automated_signals": ["Risk level based on available evidence"]}


@router.post("/api/support/tickets")
def create_support_ticket(payload: SupportTicketCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.category not in {
        "Payment issue", "Delivery issue", "Refund request", "Product complaint",
        "Seller complaint", "Account issue", "Technical issue", "Other",
    }:
        raise HTTPException(status_code=422, detail="Unsupported ticket category")
    ticket = SupportTicket(
        requester_id=user.id,
        order_id=payload.order_id,
        category=payload.category,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        status="OPEN",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    db.add(Notification(user_id=user.id, type="SUPPORT_UPDATE",
                        title="Support ticket created",
                        body=f"Your ticket {ticket.id} is open.",
                        reference_type="ticket", reference_id=ticket.id))
    db.commit()
    return {"id": ticket.id, "status": ticket.status, "priority": ticket.priority}


@router.get("/api/support/tickets")
def list_support_tickets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role.name == "admin":
        rows = db.scalars(select(SupportTicket).order_by(SupportTicket.created_at.desc())).all()
    else:
        rows = db.scalars(select(SupportTicket).where(SupportTicket.requester_id == user.id).order_by(SupportTicket.created_at.desc())).all()
    return [{"id": row.id, "subject": row.subject, "category": row.category, "priority": row.priority,
             "status": row.status, "assigned_agent_id": row.assigned_agent_id,
             "resolution_summary": row.resolution_summary, "created_at": row.created_at}
            for row in rows]


@router.patch("/api/support/tickets/{ticket_id}")
def update_support_ticket(ticket_id: str, payload: SupportTicketUpdate,
                          user: User = Depends(require_admin), db: Session = Depends(get_db)):
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if payload.status is not None:
        ticket.status = payload.status
    if payload.priority is not None:
        ticket.priority = payload.priority
    if payload.assigned_agent_id is not None:
        agent = db.get(User, payload.assigned_agent_id)
        if agent is None or agent.role.name not in {"admin"}:
            raise HTTPException(status_code=422, detail="Assigned agent must be an admin user")
        ticket.assigned_agent_id = agent.id
    if payload.resolution_summary is not None:
        ticket.resolution_summary = payload.resolution_summary
    audit(db, user.id, "SUPPORT_TICKET_UPDATE", "support_ticket", ticket.id,
          {"status": ticket.status, "priority": ticket.priority})
    db.commit()
    return {"id": ticket.id, "status": ticket.status, "priority": ticket.priority,
            "assigned_agent_id": ticket.assigned_agent_id}


@router.get("/api/support/tickets/{ticket_id}/messages")
def ticket_messages(ticket_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None or (user.role.name != "admin" and ticket.requester_id != user.id):
        raise HTTPException(status_code=404, detail="Ticket not found")
    rows = db.scalars(select(SupportMessage).where(SupportMessage.ticket_id == ticket_id).order_by(SupportMessage.created_at)).all()
    if user.role.name != "admin":
        rows = [row for row in rows if not row.internal]
    return [{"id": row.id, "author_id": row.author_id, "text": row.text,
             "internal": row.internal, "created_at": row.created_at} for row in rows]


@router.post("/api/support/tickets/{ticket_id}/messages")
def ticket_reply(ticket_id: str, payload: SupportMessageCreate,
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if payload.internal and user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Internal notes require admin access")
    if user.role.name != "admin" and ticket.requester_id != user.id:
        raise HTTPException(status_code=403, detail="Ticket access denied")
    message = SupportMessage(ticket_id=ticket.id, author_id=user.id, text=payload.text, internal=payload.internal)
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"id": message.id, "internal": message.internal}


@router.post("/api/disputes")
def create_dispute(payload: DisputeCreate, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    buyer = buyer_profile(db, user)
    order = db.get(Order, payload.order_id)
    if order is None or order.buyer_id != buyer.id:
        raise HTTPException(status_code=404, detail="Order not found")
    seller_order = order.seller_orders[0] if order.seller_orders else None
    if seller_order is None:
        raise HTTPException(status_code=409, detail="Order has no seller suborder")
    dispute = Dispute(
        order_id=order.id,
        buyer_id=buyer.id,
        seller_id=seller_order.seller_id,
        reason=payload.reason,
        status="OPEN",
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    db.add(Notification(
        user_id=seller_order.seller.user_id,
        type="DISPUTE_UPDATE",
        title="An order dispute was opened",
        body="A buyer opened a dispute linked to an order.",
        reference_type="dispute",
        reference_id=dispute.id,
    ))
    db.commit()
    return {"id": dispute.id, "status": dispute.status}


@router.get("/api/disputes")
def list_disputes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role.name == "admin":
        rows = db.scalars(select(Dispute).order_by(Dispute.created_at.desc())).all()
    elif user.role.name == "buyer":
        buyer = buyer_profile(db, user)
        rows = db.scalars(select(Dispute).where(Dispute.buyer_id == buyer.id).order_by(Dispute.created_at.desc())).all()
    elif user.role.name == "seller":
        seller = seller_profile(db, user)
        rows = db.scalars(select(Dispute).where(Dispute.seller_id == seller.id).order_by(Dispute.created_at.desc())).all()
    else:
        rows = []
    return [{"id": row.id, "order_id": row.order_id, "status": row.status,
             "seller_response": row.seller_response, "decision": row.decision,
             "refund_recommendation": row.refund_recommendation,
             "created_at": row.created_at} for row in rows]


@router.post("/api/disputes/{dispute_id}/seller-response")
def dispute_seller_response(dispute_id: str, payload: DisputeSellerResponse,
                            user: User = Depends(require_seller), db: Session = Depends(get_db)):
    seller = seller_profile(db, user)
    dispute = db.get(Dispute, dispute_id)
    if dispute is None or dispute.seller_id != seller.id:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute.seller_response = payload.seller_response
    if dispute.status == "OPEN":
        dispute.status = "AWAITING_SELLER"
    db.commit()
    return {"id": dispute.id, "status": dispute.status}


@router.patch("/api/admin/disputes/{dispute_id}")
def decide_dispute(dispute_id: str, payload: DisputeDecision,
                   user: User = Depends(require_admin), db: Session = Depends(get_db)):
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute.status = payload.status
    dispute.decision = payload.decision
    dispute.refund_recommendation = payload.refund_recommendation
    audit(db, user.id, "DISPUTE_ADMIN_DECISION", "dispute", dispute.id,
          {"status": payload.status, "refund_recommendation": payload.refund_recommendation})
    db.commit()
    return {"id": dispute.id, "status": dispute.status,
            "refund_recommendation": dispute.refund_recommendation}


@router.post("/api/admin/audit")
def write_audit_placeholder():
    raise HTTPException(status_code=405, detail="Audit records are append-only")


@router.get("/api/private-downloads/{resource_type}/{resource_id}")
def private_download_disabled(resource_type: str, resource_id: str,
                             user: User = Depends(get_current_user)):
    raise HTTPException(
        status_code=501,
        detail="Private document download is disabled until per-resource authorization and secure object storage are configured",
    )


@router.get("/api/admin/audit")
def audit_log(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500)).all()
    return [{"id": row.id, "actor_id": row.actor_id, "action": row.action,
             "resource_type": row.resource_type, "resource_id": row.resource_id,
             "details": json.loads(row.details_json), "created_at": row.created_at}
            for row in rows]


@router.get("/api/admin/platform")
def platform_health(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "status": "operational",
        "orders": db.query(Order).count(),
        "conversations": db.query(Conversation).count(),
        "open_support_tickets": db.query(SupportTicket).filter(SupportTicket.status.in_(["OPEN", "ASSIGNED", "ESCALATED"])).count(),
        "open_disputes": db.query(Dispute).filter(Dispute.status.notin_(["RESOLVED", "REJECTED"])).count(),
        "pending_verifications": db.query(SellerVerification).filter(SellerVerification.status == "PENDING").count(),
    }
