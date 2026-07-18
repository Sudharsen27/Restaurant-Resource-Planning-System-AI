from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StaffPlanRecord(Base):
    __tablename__ = "staff_plan_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    roles_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    staff_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_staff: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    prediction: Mapped["PredictionHistory | None"] = relationship(
        "PredictionHistory",
        back_populates="staff_plans",
    )
