"""
Base repository with shared HTTP client functionality.

Eliminates 45 lines of duplicated HTTP client code (found 3 times).
MANDATORY from Phase 2.8 (item #3 - HIGH priority).

Uses httpx (MANDATORY Phase 2.7) and tenacity (MANDATORY Phase 2.7).
"""

import httpx
import logging
from typing import Optional, Any, Dict, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Base repository with HTTP client and retry logic.
    
    Provides shared functionality for all repository classes:
    - HTTP client configuration (httpx.AsyncClient)
    - Retry logic with exponential backoff (tenacity)
    - Error handling
    - Logging
    
    This eliminates ~45 lines of duplicated code that was repeated
    across UserRepository, DocumentRepository, and ServiceRepository.
    
    Attributes:
        base_url: Base URL for the external service
        timeout: HTTP timeout in seconds
    """
    
    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize repository.
        
        Args:
            base_url: Base URL for the service (e.g., "http://user-store:5120")
            timeout: HTTP timeout in seconds (default 10.0)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"Initialized {self.__class__.__name__} with base_url={base_url}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        default: Any = None
    ) -> Optional[Any]:
        """
        Execute GET request with retry logic.
        
        Uses tenacity for automatic retry with exponential backoff:
        - Retries up to 3 times
        - Waits 1s, 2s, 4s, ... (exponential with min=1s, max=10s)
        - Only retries on timeout or network errors
        
        Args:
            endpoint: API endpoint (relative to base_url)
            params: Query parameters (optional)
            default: Default value to return on error
            
        Returns:
            Response JSON or default value on error
            
        Examples:
            >>> repo = BaseRepository("http://api:5000")
            >>> result = await repo._get("users/123")
            >>> result = await repo._get("search", params={"q": "python"}, default=[])
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug(f"GET {url} params={params}")
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"GET {url} → {response.status_code}")
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error fetching {url}: {e.response.status_code} - {e.response.text}"
                )
                return default
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching {url}: {str(e)}")
                raise  # Let tenacity retry
                
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {str(e)}")
                return default
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        default: Any = None
    ) -> Optional[Any]:
        """
        Execute POST request with retry logic.
        
        Args:
            endpoint: API endpoint (relative to base_url)
            json_data: JSON body to send
            default: Default value to return on error
            
        Returns:
            Response JSON or default value on error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug(f"POST {url}")
                response = await client.post(url, json=json_data)
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"POST {url} → {response.status_code}")
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error posting to {url}: {e.response.status_code} - {e.response.text}"
                )
                return default
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error posting to {url}: {str(e)}")
                raise  # Let tenacity retry
                
            except Exception as e:
                logger.error(f"Unexpected error posting to {url}: {str(e)}")
                return default
    
    async def health_check(self) -> bool:
        """
        Check if the external service is healthy.
        
        Returns:
            True if service is reachable, False otherwise
        """
        try:
            # Try to reach the health endpoint
            result = await self._get("health", default=None)
            return result is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.base_url}: {str(e)}")
            return False

