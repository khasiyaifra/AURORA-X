from datetime import datetime
from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: str
    line_total: str
    available_quantity: int
    store_id: str
    store_name: str


class CartResponse(BaseModel):
    id: str
    items: list[CartItemResponse]
    subtotal: str
    discount: str
    shipping: str
    tax: str
    total: str


class AddressCreate(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=5, max_length=30)
    line1: str = Field(min_length=1, max_length=200)
    line2: str = Field(default="", max_length=200)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(default="India", max_length=80)


class CheckoutRequest(BaseModel):
    address: AddressCreate
    discount_code: str | None = Field(default=None, max_length=64)
    idempotency_key: str = Field(min_length=8, max_length=128)


class OrderItemResponse(BaseModel):
    id: str
    product_id: str | None
    product_name: str
    sku: str
    unit_price: str
    quantity: int
    line_total: str


class SellerOrderResponse(BaseModel):
    id: str
    seller_id: str
    store_id: str
    store_name: str
    status: str
    subtotal: str
    shipping: str
    items: list[OrderItemResponse]


class OrderResponse(BaseModel):
    id: str
    status: str
    subtotal: str
    discount_total: str
    shipping_total: str
    tax_total: str
    total: str
    created_at: datetime
    items: list[OrderItemResponse]
    seller_orders: list[SellerOrderResponse]


class SellerStatusUpdate(BaseModel):
    status: str


class ShipmentUpdate(BaseModel):
    status: str
    carrier: str | None = None
    tracking_number: str | None = None


class InventoryAdjustment(BaseModel):
    quantity_delta: int
    reason: str = Field(min_length=1, max_length=100)
