"""Add supplier category and lead_days columns."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("suppliers", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column(
        "suppliers",
        sa.Column("lead_days", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_index("ix_suppliers_category", "suppliers", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_suppliers_category", table_name="suppliers")
    op.drop_column("suppliers", "lead_days")
    op.drop_column("suppliers", "category")
