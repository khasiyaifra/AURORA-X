"""initial marketplace models

Revision ID: 20261117_0001
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261117_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)

    op.create_table("buyer_profiles", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_buyer_profiles_user_id", "buyer_profiles", ["user_id"], unique=True)
    op.create_table("seller_profiles", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_seller_profiles_user_id", "seller_profiles", ["user_id"], unique=True)

    op.create_table("stores", sa.Column("id", sa.String(36), primary_key=True), sa.Column("seller_id", sa.String(36), sa.ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(160), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("category", sa.String(80), nullable=False), sa.Column("personality", sa.String(80), nullable=False), sa.Column("accent", sa.String(16), nullable=False), sa.Column("published", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("seller_id", name="uq_store_seller"))
    op.create_index("ix_stores_seller_id", "stores", ["seller_id"], unique=True)

    op.create_table("categories", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("slug", sa.String(80), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table("products", sa.Column("id", sa.String(36), primary_key=True), sa.Column("store_id", sa.String(36), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False), sa.Column("category_id", sa.String(36), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("price", sa.Numeric(12, 2), nullable=False), sa.Column("image_url", sa.String(500), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_products_store_id", "products", ["store_id"], unique=False)
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index("ix_products_name", "products", ["name"], unique=False)

    op.create_table("inventory", sa.Column("id", sa.String(36), primary_key=True), sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonnegative"))
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"], unique=True)


def downgrade() -> None:
    op.drop_table("inventory")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("stores")
    op.drop_table("seller_profiles")
    op.drop_table("buyer_profiles")
    op.drop_table("users")
    op.drop_table("roles")
