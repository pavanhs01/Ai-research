import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class StorageService:
    """Thin wrapper over S3 (or any S3-compatible Supabase Storage bucket)."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
        return self._client

    def build_key(self, owner_id: uuid.UUID, project_id: uuid.UUID, filename: str) -> str:
        return f"users/{owner_id}/projects/{project_id}/{uuid.uuid4()}-{filename}"

    def upload_bytes(self, key: str, content: bytes, content_type: str) -> str:
        if not settings.AWS_S3_BUCKET:
            raise ExternalServiceException("File storage is not configured (AWS_S3_BUCKET missing).")
        try:
            self.client.put_object(Bucket=settings.AWS_S3_BUCKET, Key=key, Body=content, ContentType=content_type)
            return key
        except (BotoCoreError, ClientError) as exc:
            logger.error("S3 upload failed for key=%s: %s", key, exc)
            raise ExternalServiceException("Failed to store the uploaded file.") from exc

    def download_bytes(self, key: str) -> bytes:
        try:
            obj = self.client.get_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
            return obj["Body"].read()
        except (BotoCoreError, ClientError) as exc:
            logger.error("S3 download failed for key=%s: %s", key, exc)
            raise ExternalServiceException("Failed to retrieve the stored file.") from exc

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
        except (BotoCoreError, ClientError) as exc:
            logger.warning("S3 delete failed for key=%s: %s", key, exc)


storage_service = StorageService()
