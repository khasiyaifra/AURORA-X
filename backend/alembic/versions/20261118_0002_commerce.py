"""Stage 3 commerce engine

Revision ID: 20261118_0002
Revises: 20261117_0001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261118_0002"
down_revision: Union[str, None] = "20261117_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("sku", sa.String(100), nullable=True))
    products = sa.table("products", sa.column("id", sa.String()), sa.column("sku", sa.String()))
    connection = op.get_bind()
    rows = connection.execute(sa.select(products.c.id)).all()
    for row in rows:
        connection.execute(products.update().where(products.c.id == row.id).values(sku=f"SKU-{row.id[:12]}"))
    with op.batch_alter_table("products") as batch:
        batch.alter_column("sku", existing_type=sa.String(100), nullable=False)
        batch.create_unique_constraint("uq_products_sku", ["sku"])
        batch.create_index("ix_products_sku", ["sku"], unique=True)

    op.add_column("inventory", sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "carts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("buyer_id", name="uq_carts_buyer"),
    )
    op.create_index("ix_carts_buyer_id", "carts", ["buyer_id"], unique=True)

    op.create_table(
        "addresses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("line1", sa.String(200), nullable=False),
        sa.Column("line2", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("country", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_addresses_buyer_id", "addresses", ["buyer_id"], unique=False)

    op.create_table(
        "cart_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cart_id", sa.String(36), sa.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
        sa.CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"], unique=False)
    op.create_index("ix_cart_items_product_id", "cart_items", ["product_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyer_profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("address_id", sa.String(36), sa.ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("shipping_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_order_idempotency"),
    )
    op.create_index("ix_orders_buyer_id", "orders", ["buyer_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_idempotency_key", "orders", ["idempotency_key"])

    op.create_table(
        "seller_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_id", sa.String(36), sa.ForeignKey("seller_profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("store_id", sa.String(36), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("shipping", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_seller_orders_order_id", "seller_orders", ["order_id"])
    op.create_index("ix_seller_orders_seller_id", "seller_orders", ["seller_id"])
    op.create_index("ix_seller_orders_store_id", "seller_orders", ["store_id"])
    op.create_index("ix_seller_orders_status", "seller_orders", ["status"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_order_id", sa.String(36), sa.ForeignKey("seller_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("product_name_snapshot", sa.String(200), nullable=False),
        sa.Column("sku_snapshot", sa.String(100), nullable=False),
        sa.Column("unit_price_snapshot", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total_snapshot", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
        sa.CheckConstraint("unit_price_snapshot >= 0", name="ck_order_item_price_nonnegative"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_seller_order_id", "order_items", ["seller_order_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])

    op.create_table("inventory_movements", sa.Column("id", sa.String(36), primary_key=True), sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False), sa.Column("quantity_delta", sa.Integer(), nullable=False), sa.Column("reserved_delta", sa.Integer(), nullable=False), sa.Column("reason", sa.String(100), nullable=False), sa.Column("reference_id", sa.String(36), nullable=True), sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_inventory_movements_product_id", "inventory_movements", ["product_id"])

    op.create_table("commissions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("seller_order_id", sa.String(36), sa.ForeignKey("seller_orders.id", ondelete="CASCADE"), nullable=False), sa.Column("eligible_amount", sa.Numeric(12, 2), nullable=False), sa.Column("rate", sa.Numeric(5, 4), nullable=False), sa.Column("commission_amount", sa.Numeric(12, 2), nullable=False), sa.Column("seller_amount", sa.Numeric(12, 2), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("seller_order_id", name="uq_commission_seller_order"))
    op.create_index("ix_commissions_seller_order_id", "commissions", ["seller_order_id"], unique=True)

    op.create_table("payment_records", sa.Column("id", sa.String(36), primary_key=True), sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("provider", sa.String(50), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("provider_reference", sa.String(128), nullable=True), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("order_id", name="uq_payment_order"))
    op.create_index("ix_payment_records_order_id", "payment_records", ["order_id"], unique=True)
    op.create_index("ix_payment_records_status", "payment_records", ["status"])

    op.create_table("refund_records", sa.Column("id", sa.String(36), primary_key=True), sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("payment_id", sa.String(36), sa.ForeignKey("payment_records.id", ondelete="RESTRICT"), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_refund_records_order_id", "refund_records", ["order_id"])
    op.create_index("ix_refund_records_payment_id", "refund_records", ["payment_id"])

    op.create_table("shipments", sa.Column("id", sa.String(36), primary_key=True), sa.Column("seller_order_id", sa.String(36), sa.ForeignKey("seller_orders.id", ondelete="CASCADE"), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("carrier", sa.String(100), nullable=True), sa.Column("tracking_number", sa.String(150), nullable=True), sa.Column("shipped_at", sa.DateTime(), nullable=True), sa.Column("delivered_at", sa.DateTime(), nullable=True), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("seller_order_id", name="uq_shipment_seller_order"))
    op.create_index("ix_shipments_seller_order_id", "shipments", ["seller_order_id"], unique=True)
    op.create_index("ix_shipments_status", "shipments", ["status"])

    op.create_table("order_status_history", sa.Column("id", sa.String(36), primary_key=True), sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("seller_order_id", sa.String(36), sa.ForeignKey("seller_orders.id", ondelete="CASCADE"), nullable=True), sa.Column("from_status", sa.String(32), nullable=True), sa.Column("to_status", sa.String(32), nullable=False), sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True), sa.Column("reason", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_order_status_history_order_id", "order_status_history", ["order_id"])
    op.create_index("ix_order_status_history_seller_order_id", "order_status_history", ["seller_order_id"])
    op.create_index("ix_order_status_history_to_status", "order_status_history", ["to_status"])


def downgrade() -> None:
    op.drop_table("order_status_history")
    op.drop_table("shipments")
    op.drop_table("refund_records")
    op.drop_table("payment_records")
    op.drop_table("commissions")
    op.drop_table("inventory_movements")
    op.drop_table("order_items")
    op.drop_table("seller_orders")
    op.drop_table("orders")
    op.drop_table("cart_items")
    op.drop_table("addresses")
    op.drop_table("carts")
    op.drop_column("inventory", "reserved_quantity")
    op.drop_column("products", "sku")
