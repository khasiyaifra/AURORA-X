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
    cart: Mapped[Optional["Cart"]] = relationship(back_populates="buyer", uselist=False)


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
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, default="SKU")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store: Mapped["Store"] = relationship(back_populates="products")
    category: Mapped["Category"] = relationship(back_populates="products")
    inventory: Mapped["Inventory"] = relationship(back_populates="product", uselist=False, cascade="all, delete-orphan")


class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_inventory_reserved_lte_quantity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped["Product"] = relationship(back_populates="inventory")


class Cart(Base, TimestampMixin):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("buyer_profiles.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    buyer: Mapped["BuyerProfile"] = relationship(back_populates="cart")
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
        CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("buyer_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    line2: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="India")


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_order_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("buyer_profiles.id", ondelete="RESTRICT"), index=True, nullable=False)
    address_id: Mapped[str] = mapped_column(ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    shipping_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    buyer: Mapped["BuyerProfile"] = relationship()
    address: Mapped["Address"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    seller_orders: Mapped[list["SellerOrder"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payment: Mapped[Optional["PaymentRecord"]] = relationship(back_populates="order", uselist=False)


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
        CheckConstraint("unit_price_snapshot >= 0", name="ck_order_item_price_nonnegative"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    seller_order_id: Mapped[str] = mapped_column(ForeignKey("seller_orders.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), index=True, nullable=True)
    product_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    sku_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_price_snapshot: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_snapshot: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    order: Mapped["Order"] = relationship(back_populates="items")
    seller_order: Mapped["SellerOrder"] = relationship(back_populates="items")


class SellerOrder(Base, TimestampMixin):
    __tablename__ = "seller_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    seller_id: Mapped[str] = mapped_column(ForeignKey("seller_profiles.id", ondelete="RESTRICT"), index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id", ondelete="RESTRICT"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    shipping: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    order: Mapped["Order"] = relationship(back_populates="seller_orders")
    seller: Mapped["SellerProfile"] = relationship()
    store: Mapped["Store"] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="seller_order")
    shipment: Mapped[Optional["Shipment"]] = relationship(back_populates="seller_order", uselist=False)
    commission: Mapped[Optional["Commission"]] = relationship(back_populates="seller_order", uselist=False)


class InventoryMovement(Base, TimestampMixin):
    __tablename__ = "inventory_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)


class Commission(Base, TimestampMixin):
    __tablename__ = "commissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    seller_order_id: Mapped[str] = mapped_column(ForeignKey("seller_orders.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    eligible_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    commission_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    seller_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    seller_order: Mapped["SellerOrder"] = relationship(back_populates="commission")


class PaymentRecord(Base, TimestampMixin):
    __tablename__ = "payment_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="demo")
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    order: Mapped["Order"] = relationship(back_populates="payment")


class RefundRecord(Base, TimestampMixin):
    __tablename__ = "refund_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payment_records.id", ondelete="RESTRICT"), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    seller_order_id: Mapped[str] = mapped_column(ForeignKey("seller_orders.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="NOT_SHIPPED")
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(150), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(nullable=True)
    seller_order: Mapped["SellerOrder"] = relationship(back_populates="shipment")


class OrderStatusHistory(Base, TimestampMixin):
    __tablename__ = "order_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    seller_order_id: Mapped[str | None] = mapped_column(ForeignKey("seller_orders.id", ondelete="CASCADE"), index=True, nullable=True)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order: Mapped["Order"] = relationship(back_populates="status_history")


class SearchHistory(Base, TimestampMixin):
    __tablename__ = "search_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    buyer_id: Mapped[str | None] = mapped_column(ForeignKey("buyer_profiles.id", ondelete="CASCADE"), index=True, nullable=True)
    session_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PersonalizationPreference(Base, TimestampMixin):
    __tablename__ = "personalization_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("buyer_profiles.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferred_categories: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class AIUsage(Base, TimestampMixin):
    __tablename__ = "ai_usage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    operation: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AIResponseLog(Base, TimestampMixin):
    __tablename__ = "ai_response_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    operation: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    output_json: Mapped[str] = mapped_column(Text, nullable=False)
    sensitive_data_excluded: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("buyer_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    seller_id: Mapped[str] = mapped_column(ForeignKey("seller_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), index=True, nullable=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), index=True, nullable=True)
    archived_by_buyer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived_by_seller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("conversation_id", "client_message_id", name="uq_message_client_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    client_message_id: Mapped[str] = mapped_column(String(128), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    original_language: Mapped[str] = mapped_column(String(12), nullable=False, default="en")
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attachment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attachment_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)


class SellerVerification(Base, TimestampMixin):
    __tablename__ = "seller_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    seller_id: Mapped[str] = mapped_column(ForeignKey("seller_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    document_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ProductModeration(Base, TimestampMixin):
    __tablename__ = "product_moderations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="PENDING")
    policy_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    decision_note: Mapped[str] = mapped_column(Text, nullable=False, default="")


class TrustShieldAlert(Base, TimestampMixin):
    __tablename__ = "trustshield_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    seller_id: Mapped[str | None] = mapped_column(ForeignKey("seller_profiles.id", ondelete="CASCADE"), index=True, nullable=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    human_review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")


class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    assigned_agent_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), index=True, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="NORMAL")
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="OPEN")
    resolution_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")


class SupportMessage(Base, TimestampMixin):
    __tablename__ = "support_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Dispute(Base, TimestampMixin):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("buyer_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    seller_id: Mapped[str] = mapped_column(ForeignKey("seller_profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="OPEN")
    seller_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decision: Mapped[str] = mapped_column(Text, nullable=False, default="")
    refund_recommendation: Mapped[str] = mapped_column(String(32), nullable=False, default="NONE")


class DisputeEvidence(Base, TimestampMixin):
    __tablename__ = "dispute_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    dispute_id: Mapped[str] = mapped_column(ForeignKey("disputes.id", ondelete="CASCADE"), index=True, nullable=False)
    submitted_by_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    private_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
