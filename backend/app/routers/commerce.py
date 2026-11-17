from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin, require_buyer, require_seller
from app.models import (
    Address, BuyerProfile, Cart, CartItem, Commission, Inventory, InventoryMovement,
    Order, OrderItem, OrderStatusHistory, PaymentRecord, Product, RefundRecord,
    SellerOrder, SellerProfile, Shipment, Store, User,
)
from app.schemas_commerce import (
    AddressCreate, CartItemCreate, CartItemResponse, CartItemUpdate, CartResponse,
    CheckoutRequest, InventoryAdjustment, OrderItemResponse, OrderResponse,
    SellerStatusUpdate, ShipmentUpdate, SellerOrderResponse,
)
from app.commerce import DEFAULT_COMMISSION_RATE, calculate_commission, money
from app.payment import DemoPaymentProvider
from app.payment import verify_razorpay_signature

router = APIRouter(tags=["commerce"])
ZERO = Decimal("0.00")


def buyer_profile(db: Session, user: User) -> BuyerProfile:
    profile = db.scalar(select(BuyerProfile).where(BuyerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Buyer profile missing")
    return profile


def get_or_create_cart(db: Session, user: User) -> Cart:
    profile = buyer_profile(db, user)
    cart = db.scalar(select(Cart).where(Cart.buyer_id == profile.id))
    if cart is None:
        cart = Cart(buyer_id=profile.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def cart_totals(db: Session, cart: Cart, discount_code: str | None = None):
    subtotal = ZERO
    store_ids: set[str] = set()
    for item in cart.items:
        product = db.scalar(select(Product).where(Product.id == item.product_id))
        if product is None:
            continue
        subtotal += Decimal(str(product.price)) * item.quantity
        store_ids.add(product.store_id)
    discount = money(subtotal * Decimal("0.10")) if discount_code and discount_code.upper() == "AURORA10" else ZERO
    shipping = money(Decimal("99.00") * len(store_ids)) if store_ids else ZERO
    tax = ZERO
    total = money(subtotal - discount + shipping + tax)
    return money(subtotal), money(discount), shipping, tax, total


def cart_response(db: Session, cart: Cart) -> CartResponse:
    subtotal, discount, shipping, tax, total = cart_totals(db, cart)
    items = []
    for item in cart.items:
        product = db.get(Product, item.product_id)
        if product is None:
            continue
        unit = money(Decimal(str(product.price)))
        available = max(product.inventory.quantity - product.inventory.reserved_quantity, 0) if product.inventory else 0
        items.append(CartItemResponse(
            id=item.id,
            product_id=product.id,
            product_name=product.name,
            quantity=item.quantity,
            unit_price=str(unit),
            line_total=str(money(unit * item.quantity)),
            available_quantity=available,
            store_id=product.store_id,
            store_name=product.store.name,
        ))
    return CartResponse(
        id=cart.id,
        items=items,
        subtotal=str(subtotal),
        discount=str(discount),
        shipping=str(shipping),
        tax=str(tax),
        total=str(total),
    )


@router.get("/api/cart", response_model=CartResponse)
def view_cart(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    return cart_response(db, get_or_create_cart(db, user))


@router.post("/api/cart/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_cart_item(payload: CartItemCreate, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, user)
    product = db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id).with_for_update())
    available = inventory.quantity - inventory.reserved_quantity if inventory else 0
    existing = next((item for item in cart.items if item.product_id == product.id), None)
    requested = payload.quantity + (existing.quantity if existing else 0)
    if requested > available:
        raise HTTPException(status_code=409, detail="Requested quantity exceeds available stock")
    if existing:
        existing.quantity = requested
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=payload.quantity))
    db.commit()
    db.refresh(cart)
    return cart_response(db, cart)


@router.patch("/api/cart/items/{item_id}", response_model=CartResponse)
def update_cart_item(item_id: str, payload: CartItemUpdate, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, user)
    item = db.get(CartItem, item_id)
    if item is None or item.cart_id != cart.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    inventory = db.scalar(select(Inventory).where(Inventory.product_id == item.product_id).with_for_update())
    available = inventory.quantity - inventory.reserved_quantity if inventory else 0
    if payload.quantity > available:
        raise HTTPException(status_code=409, detail="Requested quantity exceeds available stock")
    item.quantity = payload.quantity
    db.commit()
    db.refresh(cart)
    return cart_response(db, cart)


@router.delete("/api/cart/items/{item_id}", response_model=CartResponse)
def remove_cart_item(item_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, user)
    item = db.get(CartItem, item_id)
    if item is None or item.cart_id != cart.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return cart_response(db, cart)


@router.delete("/api/cart", response_model=CartResponse)
def clear_cart(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, user)
    for item in list(cart.items):
        db.delete(item)
    db.commit()
    db.refresh(cart)
    return cart_response(db, cart)


def order_item_response(item: OrderItem) -> OrderItemResponse:
    return OrderItemResponse(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product_name_snapshot,
        sku=item.sku_snapshot,
        unit_price=str(money(Decimal(str(item.unit_price_snapshot)))),
        quantity=item.quantity,
        line_total=str(money(Decimal(str(item.line_total_snapshot)))),
    )


def order_response(order: Order) -> OrderResponse:
    seller_rows = []
    for seller_order in order.seller_orders:
        seller_rows.append(SellerOrderResponse(
            id=seller_order.id,
            seller_id=seller_order.seller_id,
            store_id=seller_order.store_id,
            store_name=seller_order.store.name,
            status=seller_order.status,
            subtotal=str(money(Decimal(str(seller_order.subtotal)))),
            shipping=str(money(Decimal(str(seller_order.shipping)))),
            items=[order_item_response(item) for item in seller_order.items],
        ))
    return OrderResponse(
        id=order.id,
        status=order.status,
        subtotal=str(money(Decimal(str(order.subtotal)))),
        discount_total=str(money(Decimal(str(order.discount_total)))),
        shipping_total=str(money(Decimal(str(order.shipping_total)))),
        tax_total=str(money(Decimal(str(order.tax_total)))),
        total=str(money(Decimal(str(order.total)))),
        created_at=order.created_at,
        items=[order_item_response(item) for item in order.items],
        seller_orders=seller_rows,
    )


@router.post("/api/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    payload: CheckoutRequest,
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    profile = buyer_profile(db, user)
    existing = db.scalar(select(Order).where(Order.buyer_id == profile.id, Order.idempotency_key == payload.idempotency_key))
    if existing:
        return order_response(existing)

    cart = get_or_create_cart(db, user)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    address = Address(
        buyer_id=profile.id,
        recipient_name=payload.address.recipient_name,
        phone=payload.address.phone,
        line1=payload.address.line1,
        line2=payload.address.line2,
        city=payload.address.city,
        state=payload.address.state,
        postal_code=payload.address.postal_code,
        country=payload.address.country,
    )
    db.add(address)
    db.flush()

    subtotal = ZERO
    discount = ZERO
    seller_groups: dict[str, list[tuple[CartItem, Product, Inventory]]] = {}
    for cart_item in cart.items:
        product = db.scalar(select(Product).where(Product.id == cart_item.product_id).with_for_update())
        if product is None or not product.is_active:
            raise HTTPException(status_code=409, detail="Cart contains an unavailable product")
        inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id).with_for_update())
        if inventory is None:
            raise HTTPException(status_code=409, detail="Inventory record missing")
        available = inventory.quantity - inventory.reserved_quantity
        if cart_item.quantity > available:
            raise HTTPException(status_code=409, detail=f"Insufficient stock for {product.name}")
        subtotal += Decimal(str(product.price)) * cart_item.quantity
        seller_groups.setdefault(product.store_id, []).append((cart_item, product, inventory))

    if payload.discount_code and payload.discount_code.upper() == "AURORA10":
        discount = money(subtotal * Decimal("0.10"))
    shipping = money(Decimal("99.00") * len(seller_groups))
    tax = ZERO
    total = money(subtotal - discount + shipping + tax)

    order = Order(
        buyer_id=profile.id,
        address_id=address.id,
        idempotency_key=payload.idempotency_key,
        status="PENDING",
        subtotal=money(subtotal),
        discount_total=discount,
        shipping_total=shipping,
        tax_total=tax,
        total=total,
    )
    db.add(order)
    db.flush()

    for store_id, group in seller_groups.items():
        store = db.get(Store, store_id)
        seller_subtotal = ZERO
        for _, product, _ in group:
            cart_item = next(item for item, grouped_product, _ in group if grouped_product.id == product.id)
            seller_subtotal += Decimal(str(product.price)) * cart_item.quantity
        seller_subtotal = money(seller_subtotal)
        seller_shipping = Decimal("99.00")
        seller_discount = money(discount * seller_subtotal / subtotal) if subtotal else ZERO
        eligible_amount = money(seller_subtotal - seller_discount)
        commission_amount, seller_amount = calculate_commission(eligible_amount, DEFAULT_COMMISSION_RATE)

        seller_order = SellerOrder(
            order_id=order.id,
            seller_id=store.seller_id,
            store_id=store.id,
            status="PENDING",
            subtotal=seller_subtotal,
            shipping=seller_shipping,
        )
        db.add(seller_order)
        db.flush()
        db.add(Commission(
            seller_order_id=seller_order.id,
            eligible_amount=eligible_amount,
            rate=DEFAULT_COMMISSION_RATE,
            commission_amount=commission_amount,
            seller_amount=seller_amount,
        ))

        for cart_item, product, inventory in group:
            unit = money(Decimal(str(product.price)))
            line_total = money(unit * cart_item.quantity)
            db.add(OrderItem(
                order_id=order.id,
                seller_order_id=seller_order.id,
                product_id=product.id,
                product_name_snapshot=product.name,
                sku_snapshot=product.sku,
                unit_price_snapshot=unit,
                quantity=cart_item.quantity,
                line_total_snapshot=line_total,
            ))
            inventory.quantity -= cart_item.quantity
            db.add(InventoryMovement(
                product_id=product.id,
                quantity_delta=-cart_item.quantity,
                reserved_delta=0,
                reason="CHECKOUT",
                reference_id=order.id,
                actor_id=user.id,
            ))

    db.add(PaymentRecord(order_id=order.id, provider="demo", status="PENDING", amount=total))
    db.add(OrderStatusHistory(order_id=order.id, from_status=None, to_status="PENDING", actor_id=user.id))
    for item in list(cart.items):
        db.delete(item)
    db.commit()
    db.refresh(order)
    return order_response(order)


@router.get("/api/orders", response_model=list[OrderResponse])
def buyer_orders(user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    profile = buyer_profile(db, user)
    orders = db.scalars(select(Order).where(Order.buyer_id == profile.id).order_by(Order.created_at.desc())).all()
    return [order_response(order) for order in orders]


@router.get("/api/orders/{order_id}", response_model=OrderResponse)
def buyer_order(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    profile = buyer_profile(db, user)
    order = db.scalar(select(Order).where(Order.id == order_id, Order.buyer_id == profile.id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_response(order)


PARENT_CANCELABLE = {"PENDING", "CONFIRMED"}


@router.post("/api/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    profile = buyer_profile(db, user)
    order = db.scalar(select(Order).where(Order.id == order_id, Order.buyer_id == profile.id).with_for_update())
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in PARENT_CANCELABLE:
        raise HTTPException(status_code=409, detail="Order can no longer be cancelled")
    previous = order.status
    order.status = "CANCELLED"
    for seller_order in order.seller_orders:
        seller_order.status = "CANCELLED"
        for item in seller_order.items:
            product = db.get(Product, item.product_id) if item.product_id else None
            if product:
                inventory = db.get(Inventory, product.inventory.id)
                inventory.quantity += item.quantity
                db.add(InventoryMovement(
                    product_id=product.id,
                    quantity_delta=item.quantity,
                    reserved_delta=0,
                    reason="CANCEL_ORDER",
                    reference_id=order.id,
                    actor_id=user.id,
                ))
    if order.payment:
        order.payment.status = "REFUND_PENDING" if order.payment.status == "PAID" else "CANCELLED"
    db.add(OrderStatusHistory(order_id=order.id, from_status=previous, to_status="CANCELLED", actor_id=user.id))
    db.commit()
    db.refresh(order)
    return order_response(order)


SELLER_TRANSITIONS = {
    "PENDING": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"READY_TO_SHIP", "CANCELLED"},
    "READY_TO_SHIP": {"SHIPPED"},
    "SHIPPED": {"DELIVERED"},
}


@router.get("/api/seller/orders", response_model=list[SellerOrderResponse])
def seller_orders(user: User = Depends(require_seller), db: Session = Depends(get_db)):
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Seller profile missing")
    rows = db.scalars(select(SellerOrder).where(SellerOrder.seller_id == profile.id).order_by(SellerOrder.created_at.desc())).all()
    return [
        SellerOrderResponse(
            id=row.id,
            seller_id=row.seller_id,
            store_id=row.store_id,
            store_name=row.store.name,
            status=row.status,
            subtotal=str(money(Decimal(str(row.subtotal)))),
            shipping=str(money(Decimal(str(row.shipping)))),
            items=[order_item_response(item) for item in row.items],
        )
        for row in rows
    ]


@router.patch("/api/seller/orders/{seller_order_id}", response_model=SellerOrderResponse)
def update_seller_order(
    seller_order_id: str,
    payload: SellerStatusUpdate,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    row = db.scalar(select(SellerOrder).where(SellerOrder.id == seller_order_id).with_for_update())
    if profile is None or row is None or row.seller_id != profile.id:
        raise HTTPException(status_code=404, detail="Seller order not found")
    target = payload.status.upper()
    if target not in SELLER_TRANSITIONS.get(row.status, set()):
        raise HTTPException(status_code=409, detail=f"Invalid transition: {row.status} -> {target}")
    previous = row.status
    row.status = target
    if target == "SHIPPED":
        shipment = db.scalar(select(Shipment).where(Shipment.seller_order_id == row.id))
        if shipment is None:
            shipment = Shipment(seller_order_id=row.id)
            db.add(shipment)
        shipment.status = "SHIPPED"
        shipment.shipped_at = datetime.utcnow()
    sibling_statuses = [item.status for item in row.order.seller_orders]
    if target == "ACCEPTED" or target == "PROCESSING":
        row.order.status = "CONFIRMED" if target == "ACCEPTED" else "PROCESSING"
    if all(status_name == "SHIPPED" for status_name in sibling_statuses):
        row.order.status = "SHIPPED"
    if all(status_name == "DELIVERED" for status_name in sibling_statuses):
        row.order.status = "DELIVERED"
    db.add(OrderStatusHistory(
        order_id=row.order_id,
        seller_order_id=row.id,
        from_status=previous,
        to_status=target,
        actor_id=user.id,
    ))
    db.commit()
    db.refresh(row)
    return SellerOrderResponse(
        id=row.id,
        seller_id=row.seller_id,
        store_id=row.store_id,
        store_name=row.store.name,
        status=row.status,
        subtotal=str(money(Decimal(str(row.subtotal)))),
        shipping=str(money(Decimal(str(row.shipping)))),
        items=[order_item_response(item) for item in row.items],
    )


@router.patch("/api/seller/orders/{seller_order_id}/shipment", response_model=SellerOrderResponse)
def update_shipment(
    seller_order_id: str,
    payload: ShipmentUpdate,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    row = db.scalar(select(SellerOrder).where(SellerOrder.id == seller_order_id))
    if profile is None or row is None or row.seller_id != profile.id:
        raise HTTPException(status_code=404, detail="Seller order not found")
    if row.status not in {"SHIPPED", "DELIVERED"}:
        raise HTTPException(status_code=409, detail="Shipment can only be tracked after dispatch")
    shipment = db.scalar(select(Shipment).where(Shipment.seller_order_id == row.id))
    if shipment is None:
        shipment = Shipment(seller_order_id=row.id)
        db.add(shipment)
    shipment.status = payload.status.upper()
    shipment.carrier = payload.carrier
    shipment.tracking_number = payload.tracking_number
    if shipment.status == "DELIVERED":
        shipment.delivered_at = datetime.utcnow()
        if row.status == "SHIPPED":
            row.status = "DELIVERED"
    db.commit()
    db.refresh(row)
    return SellerOrderResponse(
        id=row.id,
        seller_id=row.seller_id,
        store_id=row.store_id,
        store_name=row.store.name,
        status=row.status,
        subtotal=str(money(Decimal(str(row.subtotal)))),
        shipping=str(money(Decimal(str(row.shipping)))),
        items=[order_item_response(item) for item in row.items],
    )


@router.post("/api/seller/products/{product_id}/inventory", response_model=dict)
def adjust_inventory(
    product_id: str,
    payload: InventoryAdjustment,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    product = db.scalar(select(Product).where(Product.id == product_id).with_for_update())
    if profile is None or product is None or product.store.seller_id != profile.id:
        raise HTTPException(status_code=404, detail="Product not found")
    inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id).with_for_update())
    if inventory.quantity + payload.quantity_delta < inventory.reserved_quantity:
        raise HTTPException(status_code=409, detail="Adjustment would make stock below reserved quantity")
    inventory.quantity += payload.quantity_delta
    db.add(InventoryMovement(
        product_id=product.id,
        quantity_delta=payload.quantity_delta,
        reserved_delta=0,
        reason=payload.reason,
        reference_id=product.id,
        actor_id=user.id,
    ))
    db.commit()
    return {
        "product_id": product.id,
        "quantity": inventory.quantity,
        "reserved_quantity": inventory.reserved_quantity,
        "available_quantity": inventory.quantity - inventory.reserved_quantity,
    }


@router.get("/api/admin/orders", response_model=list[OrderResponse])
def admin_orders(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    orders = db.scalars(select(Order).order_by(Order.created_at.desc())).all()
    return [order_response(order) for order in orders]


@router.post("/api/payments/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    if not verify_razorpay_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid Razorpay webhook signature")

    payload = await request.json()
    event_id = str(payload.get("event_id") or payload.get("id") or "")
    if not event_id:
        raise HTTPException(status_code=400, detail="Webhook event ID is required")

    existing = db.scalar(select(PaymentRecord).where(PaymentRecord.provider_reference == event_id))
    if existing:
        return {"status": "duplicate", "event_id": event_id}

    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_reference = str(payment_entity.get("notes", {}).get("aurora_order_id") or "")
    if not order_reference:
        raise HTTPException(status_code=400, detail="Webhook does not identify an Aurora order")
    order = db.scalar(select(Order).where(Order.id == order_reference))
    if order is None:
        raise HTTPException(status_code=404, detail="Aurora order not found")

    payment = db.scalar(select(PaymentRecord).where(PaymentRecord.order_id == order.id))
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment record not found")
    event_name = str(payload.get("event", ""))
    if event_name == "payment.captured":
        payment.status = "PAID"
    elif event_name in {"payment.failed", "payment.authorized"}:
        payment.status = "FAILED" if event_name == "payment.failed" else "AUTHORIZED"
    else:
        payment.status = "PENDING"
    payment.provider_reference = event_id
    db.commit()
    return {"status": "processed", "event_id": event_id}
