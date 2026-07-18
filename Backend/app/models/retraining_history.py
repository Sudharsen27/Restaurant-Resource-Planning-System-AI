from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class RetrainingHistory(BaseModel):
    __tablename__ = "retraining_history"

    version_label: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    triggered_by: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_version: Mapped["ModelVersion | None"] = relationship(
        "ModelVersion",
        back_populates="retraining_records",
        lazy="joined",
    )
    prediction: Mapped["PredictionHistory | None"] = relationship(
        "PredictionHistory",
        lazy="joined",
    )
