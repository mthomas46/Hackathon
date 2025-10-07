"""MinIO/S3 implementation of StorageRepository."""

import logging
from io import BytesIO
from typing import BinaryIO
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from services.mcp_store.domain.repositories.storage_repository import (
    StorageRepository,
    StorageError,
)

logger = logging.getLogger(__name__)


class MinioStorageRepository(StorageRepository):
    """
    MinIO/S3 implementation of StorageRepository.
    
    Handles binary storage of .mcp package files.
    MinIO client is compatible with S3, so this works with both.
    """
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        use_ssl: bool = False,
        region: str = "us-east-1",
    ):
        """
        Initialize MinIO storage repository.
        
        Args:
            endpoint: MinIO/S3 endpoint (e.g., "localhost:9000" or "s3.amazonaws.com")
            access_key: Access key
            secret_key: Secret key
            bucket: Bucket name
            use_ssl: Whether to use HTTPS
            region: Region name
        """
        self.bucket = bucket
        self.region = region
        
        try:
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=use_ssl,
                region=region,
            )
            
            # Create bucket if it doesn't exist
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket, location=region)
                logger.info(f"Created bucket: {bucket}")
            
            logger.info(f"MinIO storage repository initialized (bucket: {bucket})")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise StorageError(f"Failed to initialize storage: {e}") from e
    
    async def upload(
        self,
        file_path: str,
        file_content: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload a file to storage.
        
        Args:
            file_path: Path/key for the file in storage
            file_content: Raw bytes of the file
            content_type: MIME type of the file
            
        Returns:
            The storage URL/path of the uploaded file
            
        Raises:
            StorageError: If upload fails
        """
        try:
            # Convert bytes to BytesIO for MinIO
            file_stream = BytesIO(file_content)
            file_size = len(file_content)
            
            # Upload file
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=file_path,
                data=file_stream,
                length=file_size,
                content_type=content_type,
            )
            
            logger.info(f"Uploaded file: {file_path} ({file_size:,} bytes)")
            
            return file_path
        except S3Error as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise StorageError(f"Failed to upload file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file_path}: {e}")
            raise StorageError(f"Failed to upload file: {e}") from e
    
    async def download(self, file_path: str) -> bytes:
        """
        Download a file from storage.
        
        Args:
            file_path: Path/key for the file in storage
            
        Returns:
            Raw bytes of the file
            
        Raises:
            StorageError: If download fails or file not found
        """
        try:
            # Download file
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=file_path,
            )
            
            # Read all bytes
            file_content = response.read()
            
            # Close response
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded file: {file_path} ({len(file_content):,} bytes)")
            
            return file_content
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.error(f"File not found: {file_path}")
                raise StorageError(f"File not found: {file_path}") from e
            else:
                logger.error(f"Failed to download file {file_path}: {e}")
                raise StorageError(f"Failed to download file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error downloading file {file_path}: {e}")
            raise StorageError(f"Failed to download file: {e}") from e
    
    async def download_stream(self, file_path: str) -> BinaryIO:
        """
        Download a file as a stream (for large files).
        
        Args:
            file_path: Path/key for the file in storage
            
        Returns:
            Binary stream of the file
            
        Raises:
            StorageError: If download fails or file not found
        """
        try:
            # Get object response
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=file_path,
            )
            
            logger.info(f"Streaming file: {file_path}")
            
            # Return the response stream
            # Note: Caller is responsible for closing the stream
            return response
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.error(f"File not found: {file_path}")
                raise StorageError(f"File not found: {file_path}") from e
            else:
                logger.error(f"Failed to stream file {file_path}: {e}")
                raise StorageError(f"Failed to stream file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error streaming file {file_path}: {e}")
            raise StorageError(f"Failed to stream file: {e}") from e
    
    async def delete(self, file_path: str) -> None:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path/key for the file in storage
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=file_path,
            )
            
            logger.info(f"Deleted file: {file_path}")
        except S3Error as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise StorageError(f"Failed to delete file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting file {file_path}: {e}")
            raise StorageError(f"Failed to delete file: {e}") from e
    
    async def exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            file_path: Path/key for the file in storage
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            # Try to stat the object
            self.client.stat_object(
                bucket_name=self.bucket,
                object_name=file_path,
            )
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            else:
                logger.error(f"Error checking if file exists {file_path}: {e}")
                raise StorageError(f"Failed to check if file exists: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error checking file existence {file_path}: {e}")
            raise StorageError(f"Failed to check if file exists: {e}") from e
    
    async def get_file_size(self, file_path: str) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path/key for the file in storage
            
        Returns:
            File size in bytes
            
        Raises:
            StorageError: If file not found
        """
        try:
            # Get object metadata
            stat = self.client.stat_object(
                bucket_name=self.bucket,
                object_name=file_path,
            )
            
            return stat.size
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.error(f"File not found: {file_path}")
                raise StorageError(f"File not found: {file_path}") from e
            else:
                logger.error(f"Failed to get file size {file_path}: {e}")
                raise StorageError(f"Failed to get file size: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting file size {file_path}: {e}")
            raise StorageError(f"Failed to get file size: {e}") from e
    
    async def get_download_url(
        self,
        file_path: str,
        expiration_seconds: int = 3600
    ) -> str:
        """
        Generate a pre-signed download URL.
        
        Args:
            file_path: Path/key for the file in storage
            expiration_seconds: URL validity duration
            
        Returns:
            Pre-signed download URL
            
        Raises:
            StorageError: If URL generation fails
        """
        try:
            # Generate pre-signed URL
            url = self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=file_path,
                expires=timedelta(seconds=expiration_seconds),
            )
            
            logger.info(f"Generated download URL for {file_path} (expires in {expiration_seconds}s)")
            
            return url
        except S3Error as e:
            logger.error(f"Failed to generate download URL for {file_path}: {e}")
            raise StorageError(f"Failed to generate download URL: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error generating download URL for {file_path}: {e}")
            raise StorageError(f"Failed to generate download URL: {e}") from e
    
    async def copy(self, source_path: str, dest_path: str) -> None:
        """
        Copy a file within storage.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            
        Raises:
            StorageError: If copy fails
        """
        try:
            # Copy object
            self.client.copy_object(
                bucket_name=self.bucket,
                object_name=dest_path,
                source=f"{self.bucket}/{source_path}",
            )
            
            logger.info(f"Copied file: {source_path} → {dest_path}")
        except S3Error as e:
            logger.error(f"Failed to copy file {source_path} to {dest_path}: {e}")
            raise StorageError(f"Failed to copy file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error copying file {source_path} to {dest_path}: {e}")
            raise StorageError(f"Failed to copy file: {e}") from e
    
    def list_objects(self, prefix: str = "") -> list:
        """
        List objects in bucket with optional prefix.
        
        Args:
            prefix: Prefix to filter objects
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket,
                prefix=prefix,
                recursive=True,
            )
            
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Failed to list objects with prefix {prefix}: {e}")
            raise StorageError(f"Failed to list objects: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error listing objects with prefix {prefix}: {e}")
            raise StorageError(f"Failed to list objects: {e}") from e
