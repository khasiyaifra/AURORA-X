from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select

from app.database import SessionLocal
from app.models import BuyerProfile, Conversation, Message, SellerProfile, User
from app.security import decode_access_token

router = APIRouter()
connections: dict[str, set[WebSocket]] = defaultdict(set)


def authenticated_user(db, token: str) -> User | None:
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None
    user = db.scalar(select(User).where(User.id == payload.get("sub")))
    if user is None or not user.is_active or user.token_version != payload.get("version"):
        return None
    return user


def can_access(db, conversation: Conversation, user: User) -> bool:
    if user.role.name == "admin":
        return True
    if user.role.name == "buyer":
        buyer = db.scalar(select(BuyerProfile).where(BuyerProfile.id == conversation.buyer_id))
        return buyer is not None and buyer.user_id == user.id
    if user.role.name == "seller":
        seller = db.scalar(select(SellerProfile).where(SellerProfile.id == conversation.seller_id))
        return seller is not None and seller.user_id == user.id
    return False


@router.websocket("/api/ws/conversations/{conversation_id}")
async def conversation_socket(websocket: WebSocket, conversation_id: str, token: str):
    await websocket.accept()
    db = SessionLocal()
    try:
        user = authenticated_user(db, token)
        conversation = db.get(Conversation, conversation_id)
        if user is None or conversation is None or not can_access(db, conversation, user):
            await websocket.close(code=4403)
            return
        connections[conversation_id].add(websocket)
        while True:
            payload = await websocket.receive_json()
            event_type = payload.get("type")
            if event_type == "typing":
                for peer in list(connections[conversation_id]):
                    if peer is not websocket:
                        await peer.send_json({"type": "typing", "user_id": user.id})
                continue
            if event_type != "message":
                await websocket.send_json({"type": "error", "detail": "Unsupported event"})
                continue
            client_message_id = str(payload.get("client_message_id", ""))[:128]
            text = str(payload.get("text", "")).strip()
            if len(client_message_id) < 8 or len(text) < 1 or len(text) > 5000:
                await websocket.send_json({"type": "error", "detail": "Invalid message"})
                continue
            existing = db.scalar(select(Message).where(
                Message.conversation_id == conversation_id,
                Message.client_message_id == client_message_id,
            ))
            if existing:
                await websocket.send_json({"type": "duplicate", "message_id": existing.id})
                continue
            message = Message(
                conversation_id=conversation_id,
                sender_id=user.id,
                client_message_id=client_message_id,
                text=text,
                original_language=str(payload.get("original_language", "en"))[:12],
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            event = {
                "type": "message",
                "id": message.id,
                "sender_id": user.id,
                "text": message.text,
                "original_language": message.original_language,
                "created_at": message.created_at.isoformat(),
            }
            for peer in list(connections[conversation_id]):
                await peer.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        connections[conversation_id].discard(websocket)
        db.close()
