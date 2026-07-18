"""CRUD customer forecasts — integer PK (path /forecast/{id})."""

from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class CustomerForecast(BaseModel):
    __tablename__ = "customer_forecasts"
    __table_args__ = (
        Index("ix_customer_forecasts_date_hour", "forecast_date", "forecast_hour"),
        CheckConstraint(
            "forecast_hour >= 0 AND forecast_hour <= 23",
            name="ck_customer_forecasts_hour",
        ),
        CheckConstraint("predicted_customers >= 0", name="ck_customer_forecasts_predicted"),
        CheckConstraint("confidence_score >= 0", name="ck_customer_forecasts_confidence"),
    )

    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    forecast_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_customers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    staff_recommendations: Mapped[list["StaffRecommendation"]] = relationship(
        "StaffRecommendation",
        back_populates="forecast",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    inventory_recommendations: Mapped[list["InventoryRecommendation"]] = relationship(
        "InventoryRecommendation",
        back_populates="forecast",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    feedback_entries: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="forecast",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
