# AURORA X API documentation

Interactive OpenAPI documentation is available at `/docs` on the running FastAPI service.

## Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## Cart

- `GET /api/cart`
- `POST /api/cart/items`
- `PATCH /api/cart/items/{item_id}`
- `DELETE /api/cart/items/{item_id}`
- `DELETE /api/cart`

Cart quantities are validated against available stock. AURORA10 is a server-recognized 10% demo discount code.

## Checkout and buyer orders

- `POST /api/checkout`
- `GET /api/orders`
- `GET /api/orders/{order_id}`
- `POST /api/orders/{order_id}/cancel`

Checkout requires an 8-128 character idempotency key. Repeating a key for the same buyer returns the original order. Server prices, inventory and totals are authoritative.

## Seller fulfilment

- `GET /api/seller/orders`
- `PATCH /api/seller/orders/{seller_order_id}`
- `PATCH /api/seller/orders/{seller_order_id}/shipment`
- `POST /api/seller/products/{product_id}/inventory`

## Admin

- `GET /api/admin/orders`

Admin and seller operations require server-derived roles from authenticated users.
