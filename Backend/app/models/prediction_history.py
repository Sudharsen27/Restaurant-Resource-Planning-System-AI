from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class PredictionHistory(BaseModel):
    __tablename__ = "prediction_history"
    __table_args__ = (
        Index("ix_prediction_history_date_hour", "forecast_date", "forecast_hour"),
        CheckConstraint(
            "forecast_hour >= 0 AND forecast_hour <= 23",
            name="ck_prediction_history_hour",
        ),
        CheckConstraint("predicted_customers >= 0", name="ck_prediction_history_predicted"),
    )

    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_customers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    forecast_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version_label: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    feature_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    absolute_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    staff_plans: Mapped[list["StaffPlanRecord"]] = relationship(
        "StaffPlanRecord",
        back_populates="prediction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    inventory_plans: Mapped[list["InventoryPlanRecord"]] = relationship(
        "InventoryPlanRecord",
        back_populates="prediction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    dashboard_summaries: Mapped[list["DashboardSummaryRecord"]] = relationship(
        "DashboardSummaryRecord",
        back_populates="prediction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
