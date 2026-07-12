from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class InventoryRecommendation(Base):
    __tablename__ = "inventory_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("customer_forecasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)

    forecast: Mapped["CustomerForecast"] = relationship(
        "CustomerForecast",
        back_populates="inventory_recommendations",
    )
