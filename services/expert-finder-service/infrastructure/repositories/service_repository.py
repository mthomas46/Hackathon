"""
Service repository for interacting with external-service-store.
"""

from typing import List, Dict, Any
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ServiceRepository(BaseRepository):
    """
    Repository for external-service-store operations.
    
    Provides methods to fetch service contribution data from the
    external-service-store service.
    
    Inherits HTTP client and retry logic from BaseRepository,
    eliminating duplication.
    """
    
    async def get_services_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all services a user has contributed to.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of service contribution dictionaries
        """
        services = await self._get(f"services/by-user/{user_id}", default=[])
        
        if services:
            logger.info(f"Found {len(services)} services for user {user_id}")
        
        return services
    
    async def get_users_by_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Get all users who have contributed to a service.
        
        Args:
            service_name: Service name
            
        Returns:
            List of user contribution dictionaries
        """
        users = await self._get(
            f"services/{service_name}/contributors",
            default=[]
        )
        
        return users
    
    async def get_service_count_by_user(self, user_id: str) -> int:
        """
        Get count of services a user has contributed to.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of services
        """
        services = await self.get_services_by_user(user_id)
        return len(services)

