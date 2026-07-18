from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CustomerForecast(Base):
    __tablename__ = "customer_forecasts"
    __table_args__ = (
        Index("ix_customer_forecasts_date_hour", "forecast_date", "forecast_hour"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    forecast_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_customers: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_customers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    staff_recommendations: Mapped[list["StaffRecommendation"]] = relationship(
        "StaffRecommendation",
        back_populates="forecast",
        cascade="all, delete-orphan",
    )
    inventory_recommendations: Mapped[list["InventoryRecommendation"]] = relationship(
        "InventoryRecommendation",
        back_populates="forecast",
        cascade="all, delete-orphan",
    )
    feedback_entries: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="forecast",
        cascade="all, delete-orphan",
    )
