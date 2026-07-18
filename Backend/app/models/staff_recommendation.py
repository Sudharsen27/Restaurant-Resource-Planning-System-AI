from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class StaffRecommendation(BaseModel):
    __tablename__ = "staff_recommendations"
    __table_args__ = (
        CheckConstraint("chefs >= 0", name="ck_staff_rec_chefs"),
        CheckConstraint("waiters >= 0", name="ck_staff_rec_waiters"),
        CheckConstraint("cashiers >= 0", name="ck_staff_rec_cashiers"),
        CheckConstraint("cleaners >= 0", name="ck_staff_rec_cleaners"),
    )

    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("customer_forecasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chefs: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    waiters: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    cashiers: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    cleaners: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    forecast: Mapped["CustomerForecast"] = relationship(
        "CustomerForecast",
        back_populates="staff_recommendations",
        lazy="joined",
    )
