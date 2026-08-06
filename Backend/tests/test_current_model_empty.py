"""GET /model/current soft-empty behavior when no production model exists."""

from unittest.mock import MagicMock, patch

from app.schemas.learning_feedback import CurrentModelResponse
from app.services.learning_service import get_current_model


def test_get_current_model_returns_unavailable_when_empty():
    db = MagicMock()
    with (
        patch("app.services.learning_service.ModelVersioning") as versioning_cls,
        patch("app.services.learning_service.ModelManager") as manager_cls,
    ):
        versioning_cls.return_value.get_current_production.return_value = None
        manager_cls.return_value.models_exist.return_value = False

        result = get_current_model(db)

    assert isinstance(result, CurrentModelResponse)
    assert result.available is False
    assert result.is_production is False
    assert result.model_name is None
