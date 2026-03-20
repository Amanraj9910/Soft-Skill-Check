"""
Azure Blob Storage Service.
Handles uploading audio files and generating SAS URLs for secure access.
"""
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta
from typing import Optional, Tuple
from app.config import settings
import asyncio
import uuid

# Import logging and circuit breaker
from app.core.logging import error_logger, db_logger
from app.core.circuit_breakers import blob_breaker, call_async_native

class AzureStorageService:
    def __init__(self):
        self.container_client = None
        self.blob_service_client = None
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.sas_expiry_hours = getattr(settings, 'AZURE_BLOB_SAS_EXPIRY_HOURS', 24)
        
        try:
            self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Ensure container exists
            if not self.container_client.exists():
                self.container_client.create_container()
                db_logger.info(f"Blob container created: {self.container_name}")
        except Exception as e:
            error_logger.warning(f"Azure Storage Service initialization warning: {str(e)}")

    def _ensure_configured(self):
        if not self.container_client:
            raise Exception("Azure Storage Connection String is missing or invalid.")

    async def upload_file(self, file_data: bytes, filename: str = None, content_type: str = "audio/wav") -> str:
        """
        Uploads a file to Azure Blob Storage.
        Returns the blob name.
        """
        self._ensure_configured()
        if not filename:
            filename = f"{uuid.uuid4()}.wav"
            
        blob_client = self.container_client.get_blob_client(filename)
        await call_async_native(
            blob_breaker,
            asyncio.to_thread,
            blob_client.upload_blob, file_data, overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )
        
        return filename

    async def upload_audio_bytes(
        self,
        audio_data: bytes,
        blob_path: str,
        content_type: str = "audio/wav"
    ) -> str:
        """
        Upload audio bytes directly to Blob Storage at a specific path.
        Returns the blob URL with SAS token.
        """
        self._ensure_configured()
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path
        )
        await call_async_native(
            blob_breaker,
            asyncio.to_thread,
            blob_client.upload_blob,
            audio_data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )
        return self.generate_sas_url(blob_path)

    async def upload_audio_for_user(
        self,
        audio_bytes: bytes,
        user_id: str,
        assessment_id: str,
        section: str,
        is_full_conversation: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload audio bytes with user/assessment path structure.
        Compatible with the old BlobStorageService.upload_audio_bytes API.
        """
        try:
            if is_full_conversation:
                blob_name = f"{user_id}/{assessment_id}/full_conversation.wav"
            else:
                blob_name = f"{user_id}/{assessment_id}/{section}.wav"
            
            blob_url = await self.upload_audio_bytes(audio_bytes, blob_name)
            return True, blob_url, None
        except Exception as e:
            return False, None, str(e)

    async def download_blob_bytes(self, blob_path: str) -> Optional[bytes]:
        """
        Download a blob's content as bytes.
        """
        self._ensure_configured()
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            download_stream = await call_async_native(
                blob_breaker,
                asyncio.to_thread,
                blob_client.download_blob
            )
            data = await asyncio.to_thread(download_stream.readall)
            return data
        except Exception as e:
            error_logger.error(f"Failed to download blob {blob_path}: {e}")
            return None

    async def delete_blob(self, blob_path: str) -> bool:
        """Delete a single blob."""
        self._ensure_configured()
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            await asyncio.to_thread(blob_client.delete_blob)
            return True
        except Exception as e:
            error_logger.error(f"Failed to delete blob {blob_path}: {e}")
            return False

    async def list_blobs(self, prefix: str) -> list:
        """List blob names matching a prefix."""
        self._ensure_configured()
        try:
            blob_list = await asyncio.to_thread(
                lambda: list(self.container_client.list_blobs(name_starts_with=prefix))
            )
            return [b.name for b in blob_list]
        except Exception as e:
            error_logger.error(f"Failed to list blobs with prefix {prefix}: {e}")
            return []

    def generate_sas_url(self, blob_name: str, expiry_hours: int = None) -> str:
        """
        Generates a SAS URL for a blob.
        """
        self._ensure_configured()
        if expiry_hours is None:
            expiry_hours = self.sas_expiry_hours

        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        return f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

# Singleton instance
storage_service = AzureStorageService()

def get_storage_service() -> AzureStorageService:
    """Dependency provider for AzureStorageService."""
    return storage_service

# Alias for backward compatibility
def get_blob_storage_service() -> AzureStorageService:
    """Alias — use get_storage_service() for new code."""
    return storage_service
