from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InventoryPlanRecord(Base):
    __tablename__ = "inventory_plan_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    ingredients_json: Mapped[list] = mapped_column(JSONB, nullable=False)
    inventory_cost: Mapped[float] = mapped_column(Float, nullable=False)
    ingredient_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    prediction: Mapped["PredictionHistory | None"] = relationship(
        "PredictionHistory",
        back_populates="inventory_plans",
    )
