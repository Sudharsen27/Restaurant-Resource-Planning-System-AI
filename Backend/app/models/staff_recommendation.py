from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class StaffRecommendation(Base):
    __tablename__ = "staff_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("customer_forecasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chefs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    waiters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cashiers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cleaners: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    forecast: Mapped["CustomerForecast"] = relationship(
        "CustomerForecast",
        back_populates="staff_recommendations",
    )
