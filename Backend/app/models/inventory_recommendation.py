from sqlalchemy import CheckConstraint, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class InventoryRecommendation(BaseModel):
    __tablename__ = "inventory_recommendations"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inv_rec_quantity"),
        CheckConstraint("estimated_cost >= 0", name="ck_inv_rec_cost"),
    )

    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("customer_forecasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)

    forecast: Mapped["CustomerForecast"] = relationship(
        "CustomerForecast",
        back_populates="inventory_recommendations",
        lazy="joined",
    )
