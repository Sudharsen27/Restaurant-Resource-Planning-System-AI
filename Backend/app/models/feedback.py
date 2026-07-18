from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Feedback(BaseModel):
    __tablename__ = "feedback"

    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("customer_forecasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    forecast: Mapped["CustomerForecast"] = relationship(
        "CustomerForecast",
        back_populates="feedback_entries",
        lazy="joined",
    )
