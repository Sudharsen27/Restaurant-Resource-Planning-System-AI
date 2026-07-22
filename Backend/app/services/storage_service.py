"""Abstract multi-provider object storage (local, S3, R2, Azure, GCS)."""

from __future__ import annotations

import logging
import mimetypes
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings
from app.core.constants import BACKEND_ROOT

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes | BinaryIO, content_type: str | None = None) -> str:
        """Persist object; return storage key."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    def url(self, key: str) -> str:
        ...

    def health(self) -> dict:
        return {"backend": self.__class__.__name__, "ok": True}


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path | None = None, public_base: str | None = None) -> None:
        raw = root or settings.storage_local_root
        self.root = raw if raw.is_absolute() else (BACKEND_ROOT / raw)
        self.root.mkdir(parents=True, exist_ok=True)
        self.public_base = (public_base or settings.storage_public_base_url).rstrip("/")

    def _path(self, key: str) -> Path:
        safe = key.lstrip("/").replace("..", "")
        path = self.root / safe
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def save(self, key: str, data: bytes | BinaryIO, content_type: str | None = None) -> str:
        path = self._path(key)
        payload = data.read() if hasattr(data, "read") else data  # type: ignore[union-attr]
        path.write_bytes(payload)  # type: ignore[arg-type]
        return key

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def url(self, key: str) -> str:
        return f"{self.public_base}/{key.lstrip('/')}"


class S3CompatibleBackend(StorageBackend):
    """AWS S3 or Cloudflare R2 / MinIO via endpoint_url."""

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
        public_base: str | None = None,
    ) -> None:
        import boto3

        self.bucket = bucket
        self.public_base = public_base
        kwargs: dict = {
            "aws_access_key_id": access_key or None,
            "aws_secret_access_key": secret_key or None,
            "region_name": region,
        }
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.client = boto3.client("s3", **{k: v for k, v in kwargs.items() if v is not None})

    def save(self, key: str, data: bytes | BinaryIO, content_type: str | None = None) -> str:
        body = data.read() if hasattr(data, "read") else data
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, **extra)
        return key

    def read(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def url(self, key: str) -> str:
        if self.public_base:
            return f"{self.public_base.rstrip('/')}/{key}"
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=3600,
        )

    def health(self) -> dict:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return {"backend": "s3_compatible", "ok": True, "bucket": self.bucket}
        except Exception as exc:
            return {"backend": "s3_compatible", "ok": False, "error": str(exc)}


class AzureBlobBackend(StorageBackend):
    def __init__(self, connection_string: str, container: str, public_base: str | None = None) -> None:
        from azure.storage.blob import BlobServiceClient

        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = container
        self.public_base = public_base
        try:
            self.client.create_container(container)
        except Exception:
            pass

    def save(self, key: str, data: bytes | BinaryIO, content_type: str | None = None) -> str:
        body = data.read() if hasattr(data, "read") else data
        blob = self.client.get_blob_client(self.container, key)
        blob.upload_blob(body, overwrite=True, content_type=content_type)
        return key

    def read(self, key: str) -> bytes:
        blob = self.client.get_blob_client(self.container, key)
        return blob.download_blob().readall()

    def delete(self, key: str) -> None:
        blob = self.client.get_blob_client(self.container, key)
        blob.delete_blob()

    def exists(self, key: str) -> bool:
        blob = self.client.get_blob_client(self.container, key)
        return bool(blob.exists())

    def url(self, key: str) -> str:
        if self.public_base:
            return f"{self.public_base.rstrip('/')}/{key}"
        blob = self.client.get_blob_client(self.container, key)
        return blob.url

    def health(self) -> dict:
        try:
            self.client.get_container_client(self.container).get_container_properties()
            return {"backend": "azure", "ok": True, "container": self.container}
        except Exception as exc:
            return {"backend": "azure", "ok": False, "error": str(exc)}


class GCSBackend(StorageBackend):
    def __init__(self, bucket: str, credentials_json: str = "", public_base: str | None = None) -> None:
        from google.cloud import storage

        if credentials_json:
            import json
            from google.oauth2 import service_account

            info = json.loads(credentials_json)
            creds = service_account.Credentials.from_service_account_info(info)
            self.client = storage.Client(credentials=creds, project=info.get("project_id"))
        else:
            self.client = storage.Client()
        self.bucket = self.client.bucket(bucket)
        self.bucket_name = bucket
        self.public_base = public_base

    def save(self, key: str, data: bytes | BinaryIO, content_type: str | None = None) -> str:
        body = data.read() if hasattr(data, "read") else data
        blob = self.bucket.blob(key)
        blob.upload_from_string(body, content_type=content_type)
        return key

    def read(self, key: str) -> bytes:
        return self.bucket.blob(key).download_as_bytes()

    def delete(self, key: str) -> None:
        self.bucket.blob(key).delete()

    def exists(self, key: str) -> bool:
        return bool(self.bucket.blob(key).exists())

    def url(self, key: str) -> str:
        if self.public_base:
            return f"{self.public_base.rstrip('/')}/{key}"
        return self.bucket.blob(key).generate_signed_url(expiration=3600)

    def health(self) -> dict:
        try:
            return {
                "backend": "gcs",
                "ok": self.bucket.exists(),
                "bucket": self.bucket_name,
            }
        except Exception as exc:
            return {"backend": "gcs", "ok": False, "error": str(exc)}


class StorageService:
    """Facade over configured storage backend."""

    def __init__(self, backend: StorageBackend | None = None) -> None:
        self.backend = backend or self._build_backend()

    @staticmethod
    def _build_backend() -> StorageBackend:
        kind = settings.storage_backend
        if kind in {"s3", "r2"}:
            return S3CompatibleBackend(
                bucket=settings.s3_bucket,
                region=settings.aws_region,
                access_key=settings.aws_access_key_id,
                secret_key=settings.aws_secret_access_key,
                endpoint_url=settings.s3_endpoint_url or None,
                public_base=settings.storage_public_base_url or None,
            )
        if kind == "azure":
            return AzureBlobBackend(
                settings.azure_storage_connection_string,
                settings.azure_storage_container,
                public_base=settings.storage_public_base_url or None,
            )
        if kind == "gcs":
            return GCSBackend(
                settings.gcs_bucket,
                credentials_json=settings.gcs_credentials_json,
                public_base=settings.storage_public_base_url or None,
            )
        return LocalStorageBackend()

    def save_upload(
        self,
        *,
        data: bytes | BinaryIO,
        filename: str,
        folder: str = "misc",
        content_type: str | None = None,
    ) -> dict:
        ext = Path(filename).suffix
        key = f"{folder.strip('/')}/{uuid.uuid4().hex}{ext}"
        ctype = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        saved = self.backend.save(key, data, content_type=ctype)
        return {
            "key": saved,
            "url": self.backend.url(saved),
            "content_type": ctype,
            "backend": settings.storage_backend,
        }

    def read(self, key: str) -> bytes:
        return self.backend.read(key)

    def delete(self, key: str) -> None:
        self.backend.delete(key)

    def exists(self, key: str) -> bool:
        return self.backend.exists(key)

    def url(self, key: str) -> str:
        return self.backend.url(key)

    def health(self) -> dict:
        return self.backend.health()


_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
