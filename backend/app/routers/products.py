from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_seller
from app.models import Category, Inventory, Product, SellerProfile, Store, User
from app.schemas import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["products"])


def product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        store_id=product.store_id,
        store_name=product.store.name,
        category=product.category.name,
        name=product.name,
        description=product.description,
        price=float(product.price),
        image_url=product.image_url,
        quantity=product.inventory.quantity if product.inventory else 0,
        is_active=product.is_active,
    )


def get_category(db: Session, name: str) -> Category:
    category = db.scalar(select(Category).where(Category.name == name))
    if category is None:
        slug = name.lower().replace(" ", "-")
        category = Category(name=name, slug=slug)
        db.add(category)
        db.flush()
    return category


def owned_store(db: Session, user: User, store_id: str) -> Store:
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seller profile required")
    store = db.scalar(select(Store).where(Store.id == store_id))
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    if store.seller_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this store")
    return store


@router.get("", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.created_at.desc())).all()
    return [product_response(product) for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.id == product_id, Product.is_active.is_(True)))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product_response(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, user: User = Depends(require_seller), db: Session = Depends(get_db)):
    store = owned_store(db, user, payload.store_id)
    category = get_category(db, payload.category)
    product = Product(
        store_id=store.id,
        category_id=category.id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        image_url=payload.image_url,
    )
    db.add(product)
    db.flush()
    db.add(Inventory(product_id=product.id, quantity=payload.quantity))
    db.commit()
    db.refresh(product)
    return product_response(product)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, payload: ProductUpdate, user: User = Depends(require_seller), db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    owned_store(db, user, product.store_id)

    data = payload.model_dump(exclude_unset=True)
    quantity = data.pop("quantity", None)
    category_name = data.pop("category", None)
    if category_name is not None:
        data["category_id"] = get_category(db, category_name).id
    for field, value in data.items():
        setattr(product, field, value)
    if quantity is not None:
        product.inventory.quantity = quantity
    db.commit()
    db.refresh(product)
    return product_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, user: User = Depends(require_seller), db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    owned_store(db, user, product.store_id)
    db.delete(product)
    db.commit()
    return None
