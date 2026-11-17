# AURORA X commerce flow

## Buyer journey

1. A buyer authenticates and receives a JWT.
2. The buyer creates or reopens one persistent cart.
3. Products from multiple stores are added and server stock is validated.
4. Checkout submits only the delivery address, optional demo discount code and idempotency key.
5. The server recalculates product prices and subtotal.
6. The transaction validates inventory, creates the parent order and seller suborders, snapshots order items and deducts stock.
7. A demo pending payment record is created. No real payment credential or bank action is collected.
8. Buyers can view their order details and cancel eligible pending/confirmed orders.

## Fulfilment

Each seller sees only seller suborders owned by its seller profile:

`PENDING -> ACCEPTED -> PROCESSING -> READY_TO_SHIP -> SHIPPED -> DELIVERED`

Cancellation is allowed from pending or confirmed parent states. Cancellation restores inventory and records audit movements.

## Commission

The default Aurora platform rate is 3%. The commission base is eligible merchandise amount after the proportional seller discount, excluding shipping and tax. Commission records retain the eligible amount, rate, platform commission and seller amount. Shipping and taxes are not included in the merchandise commission base. Refund reversal is exposed through the dedicated Decimal commission service for future refund integration.

## Payments

The demo provider abstraction implements a future payment-provider interface. Real gateway verification, webhook signature validation, settlement and payout/provider settlement ledgers remain to be implemented and must not be represented as live.
