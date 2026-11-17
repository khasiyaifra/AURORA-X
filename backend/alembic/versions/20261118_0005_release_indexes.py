"""Release indexes for commerce and audit queries

Revision ID: 20261118_0005
Revises: 20261118_0004
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261118_0005"
down_revision: Union[str, None] = "20261118_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_orders_created_status", "orders", ["created_at", "status"], unique=False)
    op.create_index("ix_seller_orders_seller_status", "seller_orders", ["seller_id", "status"], unique=False)
    op.create_index("ix_order_items_order_product", "order_items", ["order_id", "product_id"], unique=False)
    op.create_index("ix_inventory_product_quantity", "inventory", ["product_id", "quantity"], unique=False)
    op.create_index("ix_notification_user_read_created", "notifications", ["user_id", "read_at", "created_at"], unique=False)
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"], unique=False)
    op.create_index("ix_support_tickets_status_created", "support_tickets", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_support_tickets_status_created", table_name="support_tickets")
    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_index("ix_notification_user_read_created", table_name="notifications")
    op.drop_index("ix_inventory_product_quantity", table_name="inventory")
    op.drop_index("ix_order_items_order_product", table_name="order_items")
    op.drop_index("ix_seller_orders_seller_status", table_name="seller_orders")
    op.drop_index("ix_orders_created_status", table_name="orders")
