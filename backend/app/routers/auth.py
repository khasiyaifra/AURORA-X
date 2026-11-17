from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import BuyerProfile, Role, SellerProfile, User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import create_access_token, hash_password, verify_password
from collections import defaultdict, deque
import time

auth_attempts: dict[str, deque[float]] = defaultdict(deque)


def auth_rate_limit(email: str) -> None:
    now = time.monotonic()
    queue = auth_attempts[email.lower()]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= 10:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    queue.append(now)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def ensure_roles(db: Session) -> dict[str, Role]:
    roles = {}
    for name in ("buyer", "seller", "admin"):
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name)
            db.add(role)
            db.flush()
        roles[name] = role
    return roles


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    role = ensure_roles(db)[payload.role]
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role_id=role.id,
    )
    db.add(user)
    db.flush()
    if payload.role == "buyer":
        db.add(BuyerProfile(user_id=user.id))
    else:
        db.add(SellerProfile(user_id=user.id))
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.name,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    auth_rate_limit(payload.email)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(user.id, user.role.name, user.token_version)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.token_version += 1
    db.commit()
    return None


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.name,
        created_at=user.created_at,
    )
