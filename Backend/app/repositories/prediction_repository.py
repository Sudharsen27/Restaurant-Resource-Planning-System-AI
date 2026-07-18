"""PredictionHistory data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction_history import PredictionHistory
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[PredictionHistory]):
    model = PredictionHistory

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_latest(self) -> PredictionHistory | None:
        stmt = (
            select(PredictionHistory)
            .order_by(PredictionHistory.created_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def list_recent(self, *, limit: int = 100) -> list[PredictionHistory]:
        stmt = (
            select(PredictionHistory)
            .order_by(PredictionHistory.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
