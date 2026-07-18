from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class ModelVersion(BaseModel):
    __tablename__ = "model_versions"

    version_label: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    pipeline_path: Mapped[str] = mapped_column(String(500), nullable=False)
    training_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dataset_size: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    mae: Mapped[float] = mapped_column(Float, nullable=False)
    rmse: Mapped[float] = mapped_column(Float, nullable=False)
    r2: Mapped[float] = mapped_column(Float, nullable=False)
    is_production: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
        index=True,
    )

    accuracy_records: Mapped[list["AccuracyHistory"]] = relationship(
        "AccuracyHistory",
        back_populates="model_version",
        lazy="selectin",
    )
    retraining_records: Mapped[list["RetrainingHistory"]] = relationship(
        "RetrainingHistory",
        back_populates="model_version",
        lazy="selectin",
    )
