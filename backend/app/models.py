import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def uuid_value() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    name: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True, nullable=False)

    role: Mapped["Role"] = relationship(back_populates="users")
    buyer_profile: Mapped[Optional["BuyerProfile"]] = relationship(back_populates="user", uselist=False)
    seller_profile: Mapped[Optional["SellerProfile"]] = relationship(back_populates="user", uselist=False)


class BuyerProfile(Base, TimestampMixin):
    __tablename__ = "buyer_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    user: Mapped["User"] = relationship(back_populates="buyer_profile")


class SellerProfile(Base, TimestampMixin):
    __tablename__ = "seller_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    user: Mapped["User"] = relationship(back_populates="seller_profile")
    stores: Mapped[list["Store"]] = relationship(back_populates="seller")


class Store(Base, TimestampMixin):
    __tablename__ = "stores"
    __table_args__ = (UniqueConstraint("seller_id", name="uq_store_seller"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    seller_id: Mapped[str] = mapped_column(ForeignKey("seller_profiles.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    personality: Mapped[str] = mapped_column(String(80), nullable=False, default="Considered")
    accent: Mapped[str] = mapped_column(String(16), nullable=False, default="#9b7bff")
    published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    seller: Mapped["SellerProfile"] = relationship(back_populates="stores")
    products: Mapped[list["Product"]] = relationship(back_populates="store")


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store: Mapped["Store"] = relationship(back_populates="products")
    category: Mapped["Category"] = relationship(back_populates="products")
    inventory: Mapped["Inventory"] = relationship(back_populates="product", uselist=False, cascade="all, delete-orphan")


class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonnegative"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped["Product"] = relationship(back_populates="inventory")
