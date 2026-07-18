from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class StaffPlanRecord(BaseModel):
    __tablename__ = "staff_plan_records"
    __table_args__ = (
        CheckConstraint("predicted_customers >= 0", name="ck_staff_plan_customers"),
        CheckConstraint("staff_cost >= 0", name="ck_staff_plan_cost"),
        CheckConstraint("total_staff >= 0", name="ck_staff_plan_total"),
    )

    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    roles_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    staff_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_staff: Mapped[int] = mapped_column(Integer, nullable=False)

    prediction: Mapped["PredictionHistory | None"] = relationship(
        "PredictionHistory",
        back_populates="staff_plans",
        lazy="joined",
    )
