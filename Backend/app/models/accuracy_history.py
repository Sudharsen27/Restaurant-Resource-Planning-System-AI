from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AccuracyHistory(Base):
    __tablename__ = "accuracy_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    mae: Mapped[float] = mapped_column(Float, nullable=False)
    rmse: Mapped[float] = mapped_column(Float, nullable=False)
    mape: Mapped[float] = mapped_column(Float, nullable=False)
    average_error: Mapped[float] = mapped_column(Float, nullable=False)
    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
