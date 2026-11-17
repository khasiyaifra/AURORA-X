"""Stage 5 messaging trust support disputes

Revision ID: 20261118_0004
Revises: 20261118_0003
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261118_0004"
down_revision: Union[str, None] = "20261118_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def create_timestamp_columns(table):
    table.extend([
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    ])


def upgrade() -> None:
    conversations = [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_id", sa.String(36), sa.ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("archived_by_buyer", sa.Boolean(), nullable=False),
        sa.Column("archived_by_seller", sa.Boolean(), nullable=False),
    ]
    create_timestamp_columns(conversations)
    op.create_table("conversations", *conversations)
    op.create_index("ix_conversations_buyer_id", "conversations", ["buyer_id"])
    op.create_index("ix_conversations_seller_id", "conversations", ["seller_id"])
    op.create_index("ix_conversations_order_id", "conversations", ["order_id"])
    op.create_index("ix_conversations_product_id", "conversations", ["product_id"])

    messages = [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_message_id", sa.String(128), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("original_language", sa.String(12), nullable=False),
        sa.Column("attachment_name", sa.String(255), nullable=True),
        sa.Column("attachment_path", sa.String(500), nullable=True),
        sa.Column("attachment_type", sa.String(100), nullable=True),
        sa.Column("attachment_size", sa.Integer(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("conversation_id", "client_message_id", name="uq_message_client_id"),
    ]
    create_timestamp_columns(messages)
    op.create_table("messages", *messages)
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])

    def simple_table(name, extra):
        columns = [sa.Column("id", sa.String(36), primary_key=True)]
        columns.extend(extra)
        create_timestamp_columns(columns)
        op.create_table(name, *columns)

    simple_table("notifications", [
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", sa.String(36), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
    ])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])

    simple_table("seller_verifications", [
        sa.Column("seller_id", sa.String(36), sa.ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("business_name", sa.String(200), nullable=False),
        sa.Column("business_details", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reviewer_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=True),
        sa.Column("document_path", sa.String(500), nullable=True),
        sa.Column("document_type", sa.String(100), nullable=True),
    ])
    op.create_index("ix_seller_verifications_seller_id", "seller_verifications", ["seller_id"])
    op.create_index("ix_seller_verifications_status", "seller_verifications", ["status"])

    simple_table("product_moderations", [
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("policy_category", sa.String(80), nullable=True),
        sa.Column("reviewer_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=False),
    ])
    op.create_index("ix_product_moderations_product_id", "product_moderations", ["product_id"])
    op.create_index("ix_product_moderations_status", "product_moderations", ["status"])

    simple_table("trustshield_alerts", [
        sa.Column("seller_id", sa.String(36), sa.ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=True),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        sa.Column("human_review_status", sa.String(32), nullable=False),
    ])

    simple_table("support_tickets", [
        sa.Column("requester_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_agent_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("resolution_summary", sa.Text(), nullable=False),
    ])
    op.create_index("ix_support_tickets_requester_id", "support_tickets", ["requester_id"])
    op.create_index("ix_support_tickets_assigned_agent_id", "support_tickets", ["assigned_agent_id"])
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])
    op.create_index("ix_support_tickets_priority", "support_tickets", ["priority"])

    simple_table("support_messages", [
        sa.Column("ticket_id", sa.String(36), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("internal", sa.Boolean(), nullable=False),
    ])
    op.create_index("ix_support_messages_ticket_id", "support_messages", ["ticket_id"])

    simple_table("disputes", [
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seller_id", sa.String(36), sa.ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("seller_response", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("refund_recommendation", sa.String(32), nullable=False),
    ])
    op.create_index("ix_disputes_order_id", "disputes", ["order_id"])
    op.create_index("ix_disputes_buyer_id", "disputes", ["buyer_id"])
    op.create_index("ix_disputes_seller_id", "disputes", ["seller_id"])
    op.create_index("ix_disputes_status", "disputes", ["status"])

    simple_table("dispute_evidence", [
        sa.Column("dispute_id", sa.String(36), sa.ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitted_by_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("private_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
    ])
    op.create_index("ix_dispute_evidence_dispute_id", "dispute_evidence", ["dispute_id"])

    simple_table("audit_logs", [
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=False),
    ])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])


def downgrade() -> None:
    for name in ["audit_logs", "dispute_evidence", "disputes", "support_messages",
                 "support_tickets", "trustshield_alerts", "product_moderations",
                 "seller_verifications", "notifications", "messages", "conversations"]:
        op.drop_table(name)
