from app.dataset.data_loader import DatasetLoader
from app.schemas.dataset import DatasetInfoResponse, DatasetRegenerateResponse


def get_dataset_info() -> DatasetInfoResponse:
    loader = DatasetLoader()
    info = loader.get_info()
    return DatasetInfoResponse(**info)


def regenerate_dataset() -> DatasetRegenerateResponse:
    loader = DatasetLoader()
    df = loader.build_and_save()
    validation = loader.validate(df)
    info = loader.get_info()

    return DatasetRegenerateResponse(
        message="Dataset regenerated successfully",
        total_rows=info["total_rows"],
        columns=len(info["columns"]),
        min_date=info["min_date"],
        max_date=info["max_date"],
        dataset_size_mb=info["dataset_size_mb"],
        validation=validation,
    )
