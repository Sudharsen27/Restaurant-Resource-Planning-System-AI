"""Add restaurants.code and restaurants.city for ERP UI parity."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "298a40641d4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("restaurants", sa.Column("code", sa.String(length=32), nullable=True))
    op.add_column("restaurants", sa.Column("city", sa.String(length=120), nullable=True))

    # Backfill existing rows before enforcing NOT NULL / unique
    op.execute(
        """
        UPDATE restaurants
        SET code = CONCAT('RST-', UPPER(SUBSTRING(REPLACE(id::text, '-', ''), 1, 6))),
            city = COALESCE(city, 'Unknown')
        WHERE code IS NULL
        """
    )

    op.alter_column("restaurants", "code", existing_type=sa.String(length=32), nullable=False)
    op.create_index("ix_restaurants_code", "restaurants", ["code"], unique=True)
    op.create_index("ix_restaurants_city", "restaurants", ["city"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_restaurants_city", table_name="restaurants")
    op.drop_index("ix_restaurants_code", table_name="restaurants")
    op.drop_column("restaurants", "city")
    op.drop_column("restaurants", "code")
