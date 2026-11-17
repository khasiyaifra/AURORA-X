# AURORA X database schema

Stage 3 adds persistent commerce state on top of users, roles, profiles, stores, products and inventory.

## Commerce tables

- `carts`: one persistent cart per buyer profile.
- `cart_items`: product and quantity; unique by cart and product.
- `addresses`: buyer shipping snapshots.
- `orders`: parent order, server-calculated totals and idempotency key.
- `order_items`: immutable purchase snapshot containing product name, SKU, unit price and line total.
- `seller_orders`: independent fulfilment record for every seller/store in an order.
- `inventory_movements`: stock and reserved-stock audit trail.
- `commissions`: seller order commission base, 3% default rate, commission and seller amount.
- `payment_records`: demo/pending payment abstraction record.
- `refund_records`: future refund requests and status audit.
- `shipments`: seller fulfilment carrier and tracking state.
- `order_status_history`: append-only order and seller-order transitions.

## Currency and integrity

Currency columns use `NUMERIC(12, 2)`. Python commission and checkout arithmetic uses `Decimal` and half-up two-decimal rounding. Frontend prices and totals are never authoritative.

Cart quantity and order item quantity constraints require positive quantities. Inventory quantity and reserved quantity cannot be negative. Checkout locks inventory rows and deducts stock inside the order transaction. The order idempotency key is unique.
