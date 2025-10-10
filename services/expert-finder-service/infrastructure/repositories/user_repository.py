"""
User repository for interacting with user-store service.
"""

from typing import Optional, List, Dict, Any
import logging

from .base_repository import BaseRepository
from domain.entities.expert import Expert
from utils.transformers import user_dict_to_expert

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for user-store service operations.
    
    Provides methods to fetch user data from the user-store service
    and transform it into Expert entities.
    
    Inherits HTTP client and retry logic from BaseRepository,
    eliminating duplication.
    """
    
    async def get_user(self, user_id: str) -> Optional[Expert]:
        """
        Get a single user by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            Expert entity or None if not found
        """
        user_data = await self._get(f"users/{user_id}")
        
        if user_data is None:
            logger.warning(f"User not found: {user_id}")
            return None
        
        # Transform to Expert entity
        expert_data = user_dict_to_expert(user_data)
        return Expert(**expert_data)
    
    async def search_users(
        self,
        query: str,
        role: Optional[str] = None,
        limit: int = 100
    ) -> List[Expert]:
        """
        Search for users matching criteria.
        
        Args:
            query: Search query text
            role: Optional role filter
            limit: Maximum number of results
            
        Returns:
            List of Expert entities
        """
        params = {
            "q": query,
            "limit": limit
        }
        if role:
            params["role"] = role
        
        results = await self._get("users/search", params=params, default=[])
        
        # Transform to Expert entities
        experts = []
        for user_data in results:
            try:
                expert_data = user_dict_to_expert(user_data)
                expert = Expert(**expert_data)
                experts.append(expert)
            except Exception as e:
                logger.error(f"Error transforming user data: {str(e)}")
                continue
        
        logger.info(f"Found {len(experts)} users for query '{query}'")
        return experts
    
    async def get_users_by_role(self, role: str, limit: int = 100) -> List[Expert]:
        """
        Get users by role.
        
        Args:
            role: Role to filter by
            limit: Maximum number of results
            
        Returns:
            List of Expert entities
        """
        results = await self._get(
            "users/by-role",
            params={"role": role, "limit": limit},
            default=[]
        )
        
        experts = []
        for user_data in results:
            try:
                expert_data = user_dict_to_expert(user_data)
                expert = Expert(**expert_data)
                experts.append(expert)
            except Exception as e:
                logger.error(f"Error transforming user data: {str(e)}")
                continue
        
        return experts
    
    async def get_users_by_topic(self, topic: str, limit: int = 100) -> List[Expert]:
        """
        Get users by topic.
        
        Args:
            topic: Topic to filter by
            limit: Maximum number of results
            
        Returns:
            List of Expert entities
        """
        results = await self._get(
            "users/by-topic",
            params={"topic": topic, "limit": limit},
            default=[]
        )
        
        experts = []
        for user_data in results:
            try:
                expert_data = user_dict_to_expert(user_data)
                expert = Expert(**expert_data)
                experts.append(expert)
            except Exception as e:
                logger.error(f"Error transforming user data: {str(e)}")
                continue
        
        return experts
    
    async def get_team_members(self, team_id: str) -> List[Expert]:
        """
        Get all members of a team.
        
        Args:
            team_id: Team identifier
            
        Returns:
            List of Expert entities
        """
        results = await self._get(f"teams/{team_id}/members", default=[])
        
        experts = []
        for user_data in results:
            try:
                expert_data = user_dict_to_expert(user_data)
                expert = Expert(**expert_data)
                experts.append(expert)
            except Exception as e:
                logger.error(f"Error transforming user data: {str(e)}")
                continue
        
        logger.info(f"Found {len(experts)} members for team {team_id}")
        return experts

