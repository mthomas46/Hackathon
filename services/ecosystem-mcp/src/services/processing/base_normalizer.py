"""
Base Normalizer

Abstract base class for all document normalizers.
Defines the interface for converting various file formats to markdown.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseNormalizer(ABC):
    """
    Abstract base class for document normalizers.
    
    All normalizers must implement the normalize() method which
    converts the input content to a standardized markdown format.
    """
    
    @abstractmethod
    async def normalize(
        self,
        content: str,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize document content to markdown.
        
        Args:
            content: Raw file content
            file_path: Path to the file
            metadata: Additional metadata about the document
        
        Returns:
            Dict with:
            {
                "content": str,  # Normalized markdown content
                "metadata": Dict[str, Any],  # Enhanced metadata
                "tokens": int  # Estimated token count
            }
        """
        pass
    
    def _extract_service_name(self, file_path: str) -> str:
        """
        Extract service name from file path.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Service name
        """
        parts = file_path.split('/')
        
        # Look for 'services/' directory
        if 'services' in parts:
            service_idx = parts.index('services')
            if service_idx + 1 < len(parts):
                return parts[service_idx + 1]
        
        # Look for known service names
        known_services = [
            'ecosystem-mcp', 'code-analyzer', 'discovery-agent',
            'analysis-service', 'architecture-digitizer', 'expert-finder-service',
            'bedrock-proxy', 'data-services-dashboard'
        ]
        
        for service in known_services:
            if service in file_path:
                return service
        
        return 'unknown'
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses simple heuristic: ~4 characters per token.
        
        Args:
            text: Text to estimate tokens for
        
        Returns:
            Estimated token count
        """
        return len(text) // 4

