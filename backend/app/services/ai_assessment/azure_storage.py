"""
Azure Blob Storage Service.
Handles uploading audio files and generating SAS URLs for secure access.
"""
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from app.config import settings
import uuid

# Import logging
from app.core.logging import error_logger

class AzureStorageService:
    def __init__(self):
        self.container_client = None
        self.blob_service_client = None
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        
        try:
            self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Ensure container exists
            if not self.container_client.exists():
                self.container_client.create_container()
        except Exception as e:
            error_logger.warning(f"Azure Storage Service initialization warning: {str(e)}")

    def _ensure_configured(self):
        if not self.container_client:
            raise Exception("Azure Storage Connection String is missing or invalid.")

    def upload_file(self, file_data: bytes, filename: str = None, content_type: str = "audio/wav") -> str:
        """
        Uploads a file to Azure Blob Storage.
        Returns the blob name.
        """
        self._ensure_configured()
        if not filename:
            filename = f"{uuid.uuid4()}.wav"
            
        blob_client = self.container_client.get_blob_client(filename)
        blob_client.upload_blob(file_data, overwrite=True, content_settings={"content_type": content_type})
        
        return filename

    def generate_sas_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """
        Generates a SAS URL for a blob.
        """
        self._ensure_configured()
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
