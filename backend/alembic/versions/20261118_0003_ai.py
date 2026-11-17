"""Stage 4 AI and search state

Revision ID: 20261118_0003
Revises: 20261118_0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261118_0003"
down_revision: Union[str, None] = "20261118_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=True),
        sa.Column("session_key", sa.String(128), nullable=False),
        sa.Column("query", sa.String(500), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_search_history_buyer_id", "search_history", ["buyer_id"])
    op.create_index("ix_search_history_session_key", "search_history", ["session_key"])

    op.create_table(
        "personalization_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("buyer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("preferred_categories", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("buyer_id", name="uq_personalization_buyer"),
    )
    op.create_index("ix_personalization_preferences_buyer_id", "personalization_preferences", ["buyer_id"], unique=True)

    op.create_table(
        "ai_usage",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_usage_user_id", "ai_usage", ["user_id"])
    op.create_index("ix_ai_usage_operation", "ai_usage", ["operation"])

    op.create_table(
        "ai_response_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("sensitive_data_excluded", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_response_logs_user_id", "ai_response_logs", ["user_id"])
    op.create_index("ix_ai_response_logs_operation", "ai_response_logs", ["operation"])


def downgrade() -> None:
    op.drop_table("ai_response_logs")
    op.drop_table("ai_usage")
    op.drop_table("personalization_preferences")
    op.drop_table("search_history")
