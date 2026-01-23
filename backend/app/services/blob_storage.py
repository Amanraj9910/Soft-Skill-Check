"""
Azure Blob Storage service for audio file management.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from app.config import settings


class BlobStorageService:
    """Service for Azure Blob Storage operations."""
    
    def __init__(self):
        """Initialize Blob Storage client."""
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.sas_expiry_hours = settings.AZURE_BLOB_SAS_EXPIRY_HOURS
        
        # Create blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        
        # Ensure container exists
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist."""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                container_client.create_container()
                print(f"Created container: {self.container_name}")
        except Exception as e:
            print(f"Error ensuring container exists: {e}")
    
    async def upload_audio(
        self,
        file_path: str,
        user_id: str,
        assessment_id: str,
        section: str,
        is_full_conversation: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload audio file to blob storage.
        
        Args:
            file_path: Local file path
            user_id: User UUID
            assessment_id: Assessment UUID
            section: Section name (or 'full_conversation')
            is_full_conversation: If True, names as full_conversation.wav
        
        Returns:
            Tuple of (success, blob_url, error_message)
        """
        try:
            # Construct blob name
            if is_full_conversation:
                blob_name = f"{user_id}/{assessment_id}/full_conversation.wav"
            else:
                blob_name = f"{user_id}/{assessment_id}/{section}.wav"
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload file
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            # Generate SAS URL
            sas_url = self._generate_sas_url(blob_name)
            
            return True, sas_url, None
        
        except Exception as e:
            return False, None, str(e)
    
    async def upload_audio_bytes(
        self,
        audio_bytes: bytes,
        user_id: str,
        assessment_id: str,
        section: str,
        is_full_conversation: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload audio from bytes.
        
        Args:
            audio_bytes: Audio file bytes
            user_id: User UUID
            assessment_id: Assessment UUID
            section: Section name
            is_full_conversation: If True, names as full_conversation
        
        Returns:
            Tuple of (success, blob_url, error_message)
        """
        try:
            if is_full_conversation:
                blob_name = f"{user_id}/{assessment_id}/full_conversation.wav"
            else:
                blob_name = f"{user_id}/{assessment_id}/{section}.wav"
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(audio_bytes, overwrite=True)
            sas_url = self._generate_sas_url(blob_name)
            
            return True, sas_url, None
        
        except Exception as e:
            return False, None, str(e)
    
    async def download_audio(
        self,
        blob_url: str,
        output_path: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Download audio file from blob storage.
        
        Args:
            blob_url: Full blob URL or blob name
            output_path: Where to save the file
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Extract blob name from URL if needed
            if blob_url.startswith("http"):
                blob_name = blob_url.split(f"{self.container_name}/")[-1].split("?")[0]
            else:
                blob_name = blob_url
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            with open(output_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            return True, None
        
        except Exception as e:
            return False, str(e)
    
    async def delete_audio(self, blob_name: str) -> Tuple[bool, Optional[str]]:
        """
        Delete audio file from blob storage.
        
        Args:
            blob_name: Name of blob to delete
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            return True, None
        
        except Exception as e:
            return False, str(e)
    
    async def delete_assessment_audio(
        self,
        user_id: str,
        assessment_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete all audio files for an assessment.
        
        Args:
            user_id: User UUID
            assessment_id: Assessment UUID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            # List all blobs for this assessment
            prefix = f"{user_id}/{assessment_id}/"
            blob_list = container_client.list_blobs(name_starts_with=prefix)
            
            # Delete each blob
            for blob in blob_list:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob.name
                )
                blob_client.delete_blob()
            
            return True, None
        
        except Exception as e:
            return False, str(e)
    
    def _generate_sas_url(self, blob_name: str) -> str:
        """
        Generate SAS URL for blob with time-limited access.
        
        Args:
            blob_name: Name of the blob
        
        Returns:
            Full URL with SAS token
        """
        try:
            # Extract account info from connection string
            account_name = None
            account_key = None
            
            for item in self.connection_string.split(";"):
                if item.startswith("AccountName="):
                    account_name = item.split("=", 1)[1]
                elif item.startswith("AccountKey="):
                    account_key = item.split("=", 1)[1]
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=self.sas_expiry_hours)
            )
            
            # Construct full URL
            blob_url = f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
            
            return blob_url
        
        except Exception as e:
            print(f"Error generating SAS URL: {e}")
            # Return blob URL without SAS (will require public access)
            return f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
    
    async def get_audio_metadata(self, blob_name: str) -> Optional[dict]:
        """
        Get metadata for audio blob.
        
        Args:
            blob_name: Name of the blob
        
        Returns:
            Blob properties dictionary
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            properties = blob_client.get_blob_properties()
            
            return {
                "name": blob_name,
                "size": properties.size,
                "created": properties.creation_time,
                "modified": properties.last_modified,
                "content_type": properties.content_settings.content_type
            }
        
        except Exception as e:
            print(f"Error getting blob metadata: {e}")
            return None


# Create singleton instance
blob_storage_service = BlobStorageService()


def get_blob_storage_service() -> BlobStorageService:
    """Dependency for accessing Blob Storage service."""
    return blob_storage_service
