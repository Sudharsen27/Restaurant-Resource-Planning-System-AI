from datetime import date

from sqlalchemy import Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class AccuracyHistory(BaseModel):
    __tablename__ = "accuracy_history"

    recorded_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    mae: Mapped[float] = mapped_column(Float, nullable=False)
    rmse: Mapped[float] = mapped_column(Float, nullable=False)
    mape: Mapped[float] = mapped_column(Float, nullable=False)
    average_error: Mapped[float] = mapped_column(Float, nullable=False)
    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    model_version: Mapped["ModelVersion | None"] = relationship(
        "ModelVersion",
        back_populates="accuracy_records",
        lazy="joined",
    )
