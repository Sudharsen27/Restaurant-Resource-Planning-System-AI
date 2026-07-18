from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("customer_forecasts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    forecast: Mapped["CustomerForecast"] = relationship(
        "CustomerForecast",
        back_populates="feedback_entries",
    )
