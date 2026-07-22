"""Local storage backend tests."""


def test_save_read_delete(storage_service):
    result = storage_service.save_upload(
        data=b"hello-phase12",
        filename="note.txt",
        folder="tests",
        content_type="text/plain",
    )
    assert result["key"].startswith("tests/")
    assert storage_service.exists(result["key"])
    assert storage_service.read(result["key"]) == b"hello-phase12"
    assert "/tests/" in result["url"] or result["url"].endswith(result["key"].split("/")[-1])
    storage_service.delete(result["key"])
    assert not storage_service.exists(result["key"])


def test_storage_health(storage_service):
    health = storage_service.health()
    assert health.get("ok") is True
