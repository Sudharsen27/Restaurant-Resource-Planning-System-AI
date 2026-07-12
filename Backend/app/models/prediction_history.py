from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_customers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    forecast_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    feature_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    absolute_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    staff_plans: Mapped[list["StaffPlanRecord"]] = relationship(
        "StaffPlanRecord",
        back_populates="prediction",
        cascade="all, delete-orphan",
    )
    inventory_plans: Mapped[list["InventoryPlanRecord"]] = relationship(
        "InventoryPlanRecord",
        back_populates="prediction",
        cascade="all, delete-orphan",
    )
    dashboard_summaries: Mapped[list["DashboardSummaryRecord"]] = relationship(
        "DashboardSummaryRecord",
        back_populates="prediction",
        cascade="all, delete-orphan",
    )
