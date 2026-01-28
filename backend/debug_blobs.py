from azure.storage.blob import BlobServiceClient
from app.config import settings
import os

def list_blobs():
    print(f"Connecting to container: {settings.AZURE_STORAGE_CONTAINER_NAME}")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)
        
        blobs = container_client.list_blobs()
        print("\n--- Blob List ---")
        count = 0
        for blob in blobs:
            print(f"- {blob.name}")
            count += 1
        print(f"-----------------\nTotal blobs found: {count}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_blobs()
