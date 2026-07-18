from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class InventoryPlanRecord(BaseModel):
    __tablename__ = "inventory_plan_records"
    __table_args__ = (
        CheckConstraint("predicted_customers >= 0", name="ck_inv_plan_customers"),
        CheckConstraint("inventory_cost >= 0", name="ck_inv_plan_cost"),
        CheckConstraint("ingredient_count >= 0", name="ck_inv_plan_count"),
    )

    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    ingredients_json: Mapped[list] = mapped_column(JSONB, nullable=False)
    inventory_cost: Mapped[float] = mapped_column(Float, nullable=False)
    ingredient_count: Mapped[int] = mapped_column(Integer, nullable=False)

    prediction: Mapped["PredictionHistory | None"] = relationship(
        "PredictionHistory",
        back_populates="inventory_plans",
        lazy="joined",
    )
