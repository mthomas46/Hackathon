"""
User Store Service Integration Client
======================================

Client for interacting with the User Store service for team capacity
management, user information, and resource allocation.
"""

import httpx
import os
from typing import Dict, Any, List, Optional
import time


class UserStoreClient:
    """Client for User Store service integration."""
    
    def __init__(self, base_url: Optional[str] = None, log_client=None):
        """
        Initialize user store client.
        
        Args:
            base_url: User Store service URL
            log_client: Log collector client for logging
        """
        self.base_url = base_url or os.getenv("USER_STORE_URL", "http://user-store:5150")
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.log_client = log_client
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User information including name, email, role
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/users/{user_id}"
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "user-store",
                            "get_user",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    error_msg = f"Failed to get user with status {response.status_code}"
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "user-store",
                            "get_user",
                            False,
                            duration_ms,
                            error_msg
                        )
                    
                    return {"error": error_msg}
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"User store call failed: {str(e)}"
            
            if self.log_client:
                await self.log_client.log_integration_call(
                    "user-store",
                    "get_user",
                    False,
                    duration_ms,
                    error_msg
                )
            
            return {"error": error_msg}
    
    async def get_team_members(self, team_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get team members with capacity and skills.
        
        Args:
            team_id: Optional team identifier to filter by
            
        Returns:
            List of team members with capacity and skills information
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"team_id": team_id} if team_id else {}
                
                response = await client.get(
                    f"{self.base_url}/users",
                    params=params
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "user-store",
                            "get_team_members",
                            True,
                            duration_ms
                        )
                    
                    # Extract users list from response
                    users = result.get("users", []) if isinstance(result, dict) else result
                    return users
                else:
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "user-store",
                            "get_team_members",
                            False,
                            duration_ms,
                            f"Failed with status {response.status_code}"
                        )
                    
                    return []
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            if self.log_client:
                await self.log_client.log_integration_call(
                    "user-store",
                    "get_team_members",
                    False,
                    duration_ms,
                    str(e)
                )
            
            return []
    
    async def get_user_capacity(self, user_id: str) -> Dict[str, Any]:
        """
        Get user capacity information.
        
        Args:
            user_id: User identifier
            
        Returns:
            User capacity details including hours per week and current allocation
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/capacity"
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "user-store",
                            "get_user_capacity",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    # Return default capacity if service call fails
                    return {
                        "user_id": user_id,
                        "capacity_hours_per_week": 40.0,
                        "allocated_hours": 0.0,
                        "available_hours": 40.0
                    }
                    
        except Exception as e:
            # Return default capacity on error
            return {
                "user_id": user_id,
                "capacity_hours_per_week": 40.0,
                "allocated_hours": 0.0,
                "available_hours": 40.0,
                "error": str(e)
            }
    
    async def get_user_skills(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get user skills and proficiency levels.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of skills with proficiency levels
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/skills"
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "user-store",
                            "get_user_skills",
                            True,
                            duration_ms
                        )
                    
                    # Extract skills list from response
                    skills = result.get("skills", []) if isinstance(result, dict) else result
                    return skills
                else:
                    return []
                    
        except Exception as e:
            return []
    
    async def find_best_assignee(
        self,
        required_skills: List[str],
        estimated_hours: float,
        team_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best team member to assign a task to based on skills and capacity.
        
        Args:
            required_skills: Skills required for the task
            estimated_hours: Estimated hours needed
            team_id: Optional team to search within
            
        Returns:
            Best matching user or None if no suitable match found
        """
        # Get team members
        team_members = await self.get_team_members(team_id)
        
        if not team_members:
            return None
        
        # Score each member based on skills match and availability
        best_match = None
        best_score = 0.0
        
        for member in team_members:
            user_id = member.get("id") or member.get("user_id")
            if not user_id:
                continue
            
            # Get capacity and skills
            capacity = await self.get_user_capacity(user_id)
            skills = await self.get_user_skills(user_id)
            
            # Calculate availability score
            available_hours = capacity.get("available_hours", 0)
            if available_hours < estimated_hours:
                continue  # Skip if not enough capacity
            
            availability_score = min(1.0, available_hours / estimated_hours)
            
            # Calculate skills match score
            member_skills = {s.get("skill_name", "").lower() for s in skills}
            required_skills_lower = {s.lower() for s in required_skills}
            
            if required_skills_lower:
                skills_match = len(required_skills_lower & member_skills) / len(required_skills_lower)
            else:
                skills_match = 1.0
            
            # Combined score (weighted)
            total_score = (skills_match * 0.7) + (availability_score * 0.3)
            
            if total_score > best_score:
                best_score = total_score
                best_match = {
                    "user_id": user_id,
                    "name": member.get("name", "Unknown"),
                    "email": member.get("email"),
                    "skills_match_score": skills_match,
                    "availability_score": availability_score,
                    "total_score": total_score,
                    "available_hours": available_hours
                }
        
        return best_match
    
    async def allocate_capacity(
        self,
        user_id: str,
        task_id: str,
        hours: float
    ) -> bool:
        """
        Allocate user capacity to a task.
        
        Args:
            user_id: User identifier
            task_id: Task identifier
            hours: Hours to allocate
            
        Returns:
            True if allocation successful
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "task_id": task_id,
                    "hours": hours
                }
                
                response = await client.post(
                    f"{self.base_url}/users/{user_id}/allocate",
                    json=payload
                )
                
                duration_ms = (time.time() - start_time) * 1000
                success = response.status_code == 200
                
                if self.log_client:
                    await self.log_client.log_integration_call(
                        "user-store",
                        "allocate_capacity",
                        success,
                        duration_ms,
                        None if success else f"Failed with status {response.status_code}"
                    )
                
                return success
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            if self.log_client:
                await self.log_client.log_integration_call(
                    "user-store",
                    "allocate_capacity",
                    False,
                    duration_ms,
                    str(e)
                )
            
            return False

