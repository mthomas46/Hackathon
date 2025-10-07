"""Storage Repository Interface - Domain Layer.

Handles binary storage (S3/MinIO) for .mcp package files.
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class StorageRepository(ABC):
    """
    Abstract base class for binary storage (S3/MinIO).
    
    Handles upload/download of .mcp package files.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def delete(self, file_path: str) -> None:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path/key for the file in storage
            
        Raises:
            StorageError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            file_path: Path/key for the file in storage
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def copy(self, source_path: str, dest_path: str) -> None:
        """
        Copy a file within storage.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            
        Raises:
            StorageError: If copy fails
        """
        pass
