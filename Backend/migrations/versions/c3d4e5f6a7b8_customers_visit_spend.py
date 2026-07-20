"""Customer analytics fields for ERP UI."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("visit_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "customers",
        sa.Column("lifetime_spend", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "customers",
        sa.Column("last_visit_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("customers", "last_visit_at")
    op.drop_column("customers", "lifetime_spend")
    op.drop_column("customers", "visit_count")
