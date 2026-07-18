from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RetrainingHistory(Base):
    __tablename__ = "retraining_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    version_label: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    triggered_by: Mapped[str] = mapped_column(String(50), nullable=False)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="SET NULL"),
        nullable=True,
    )
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
