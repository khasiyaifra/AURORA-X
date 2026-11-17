from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_seller
from app.models import SellerProfile, Store, User
from app.schemas import StoreCreate, StoreResponse

router = APIRouter(prefix="/api/stores", tags=["stores"])


def store_response(store: Store) -> StoreResponse:
    return StoreResponse(
        id=store.id,
        name=store.name,
        description=store.description,
        category=store.category,
        personality=store.personality,
        accent=store.accent,
        published=store.published,
    )


@router.get("", response_model=list[StoreResponse])
def list_stores(db: Session = Depends(get_db)):
    stores = db.scalars(select(Store).where(Store.published.is_(True)).order_by(Store.created_at.desc())).all()
    return [store_response(store) for store in stores]


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(payload: StoreCreate, user: User = Depends(require_seller), db: Session = Depends(get_db)):
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seller profile missing")
    if db.scalar(select(Store).where(Store.seller_id == profile.id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seller already has a store")
    store = Store(
        seller_id=profile.id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        personality=payload.personality,
        accent=payload.accent,
        published=payload.published,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store_response(store)


@router.get("/{store_id}", response_model=StoreResponse)
def get_store(store_id: str, db: Session = Depends(get_db)):
    store = db.scalar(select(Store).where(Store.id == store_id, Store.published.is_(True)))
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store_response(store)
