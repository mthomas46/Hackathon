"""
Expert Finder Client for Project Planning Service

Integrates with expert-finder-service to:
- Query experts for required technologies
- Identify Subject Matter Experts (SMEs)
- Find code reviewers
- Suggest team augmentation
- Enhance development plans with expert context

Phase 4.1: Planning Service Integration
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class ExpertFinderClient:
    """
    Client for communicating with the expert-finder-service.
    
    Provides methods to query for experts based on various criteria:
    - Natural language queries
    - Topic-based queries
    - Service-based queries
    - SME discovery
    - Experience level queries
    - Code review expertise
    - Component ownership
    - Merge authority
    - Activity-based queries
    """
    
    def __init__(self, base_url: str = "http://localhost:5160", timeout: float = 10.0):
        """
        Initialize the Expert Finder client.
        
        Args:
            base_url: Base URL of the expert-finder-service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = None
        logger.info(f"Expert Finder Client initialized: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GET request to expert-finder service.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
        
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"
        try:
            if not self.client:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params or {})
            else:
                response = await self.client.get(url, params=params or {})
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error querying expert-finder: {e}")
            if e.response.status_code == 404:
                return {"experts": [], "count": 0}
            raise
        except Exception as e:
            logger.error(f"Error querying expert-finder: {e}")
            raise
    
    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make POST request to expert-finder service.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
        
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"
        try:
            if not self.client:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=data)
            else:
                response = await self.client.post(url, json=data)
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error querying expert-finder: {e}")
            raise
        except Exception as e:
            logger.error(f"Error querying expert-finder: {e}")
            raise
    
    # ========================================================================
    # CORE QUERY METHODS
    # ========================================================================
    
    async def find_experts(
        self,
        query: str,
        max_results: int = 10,
        team_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Natural language expert search.
        
        Args:
            query: Natural language query (e.g., "Python expert with FastAPI experience")
            max_results: Maximum number of experts to return
            team_id: Optional team filter
        
        Returns:
            List of expert matches with relevance scores
        """
        data = {
            "query": query,
            "max_results": max_results
        }
        if team_id:
            data["team_id"] = team_id
        
        result = await self._post("/experts/find", data)
        return result.get("experts", [])
    
    async def find_experts_by_topic(
        self,
        topic: str,
        max_results: int = 10,
        min_documents: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find experts for a specific topic/technology.
        
        Args:
            topic: Technology or topic (e.g., "Python", "Docker", "FastAPI")
            max_results: Maximum number of experts to return
            min_documents: Minimum document count threshold
        
        Returns:
            List of experts with topic expertise
        """
        params = {
            "max_results": max_results,
            "min_documents": min_documents
        }
        
        result = await self._get(f"/experts/by-topic/{topic}", params)
        return result.get("experts", [])
    
    async def find_subject_matter_experts(
        self,
        area: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identify Subject Matter Experts (SMEs) for a domain.
        
        Args:
            area: Domain or expertise area
            max_results: Maximum number of SMEs to return
        
        Returns:
            List of SMEs with expertise scores
        """
        params = {"max_results": max_results}
        
        result = await self._get(f"/experts/sme/{area}", params)
        return result.get("experts", [])
    
    async def find_experts_by_service(
        self,
        service: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find experts for a specific service/component.
        
        Args:
            service: Service or component name
            max_results: Maximum number of experts to return
        
        Returns:
            List of service experts
        """
        params = {"max_results": max_results}
        
        result = await self._get(f"/experts/by-service/{service}", params)
        return result.get("experts", [])
    
    async def find_teammates(
        self,
        user_id: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find potential teammates based on collaboration history.
        
        Args:
            user_id: User ID to find teammates for
            max_results: Maximum number of teammates to return
        
        Returns:
            List of potential teammates
        """
        params = {"max_results": max_results}
        
        result = await self._get(f"/experts/teammates/{user_id}", params)
        return result.get("teammates", [])
    
    async def get_team_expertise(
        self,
        team_id: str
    ) -> Dict[str, Any]:
        """
        Get expertise summary for a team.
        
        Args:
            team_id: Team identifier
        
        Returns:
            Team expertise summary with topics, services, member count
        """
        result = await self._get(f"/teams/{team_id}/expertise")
        return result
    
    # ========================================================================
    # ENHANCED METADATA QUERY METHODS (Phase 2.3)
    # ========================================================================
    
    async def find_experts_by_experience(
        self,
        level: str,
        domain: Optional[str] = None,
        min_contributions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find experts by experience level.
        
        Args:
            level: Experience level ("junior", "mid", "senior")
            domain: Optional domain filter ("backend", "frontend", "devops", etc.)
            min_contributions: Minimum contributions threshold
        
        Returns:
            List of experts matching experience criteria
        """
        params = {
            "level": level,
            "min_contributions": min_contributions
        }
        if domain:
            params["domain"] = domain
        
        result = await self._get("/experts/by-experience", params)
        return result.get("experts", [])
    
    async def find_code_reviewers(
        self,
        quality: str = "high",
        technology: Optional[str] = None,
        min_reviews: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find code review experts.
        
        Args:
            quality: Review quality level ("low", "medium", "high")
            technology: Optional technology filter
            min_reviews: Minimum reviews count
        
        Returns:
            List of code review experts
        """
        params = {
            "quality": quality,
            "min_reviews": min_reviews
        }
        if technology:
            params["technology"] = technology
        
        result = await self._get("/experts/reviewers", params)
        return result.get("experts", [])
    
    async def find_component_leads(
        self,
        component: str,
        min_contributions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find component ownership experts.
        
        Args:
            component: Component or domain name
            min_contributions: Minimum contributions threshold
        
        Returns:
            List of component leads
        """
        params = {
            "component": component,
            "min_contributions": min_contributions
        }
        
        result = await self._get("/experts/component-leads", params)
        return result.get("experts", [])
    
    async def find_merge_authority(
        self,
        repo: Optional[str] = None,
        min_merges: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find users with merge authority.
        
        Args:
            repo: Optional repository filter
            min_merges: Minimum merges count
        
        Returns:
            List of users with merge permissions
        """
        params = {"min_merges": min_merges}
        if repo:
            params["repo"] = repo
        
        result = await self._get("/experts/merge-authority", params)
        return result.get("experts", [])
    
    async def find_active_experts(
        self,
        recency: str = "last_30_days",
        activity_frequency: Optional[str] = None,
        min_contributions: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Find experts by activity recency.
        
        Args:
            recency: Recency filter ("last_7_days", "last_30_days", "last_90_days")
            activity_frequency: Optional frequency filter ("daily", "weekly", "monthly")
            min_contributions: Minimum recent contributions
        
        Returns:
            List of active experts
        """
        params = {
            "recency": recency,
            "min_contributions": min_contributions
        }
        if activity_frequency:
            params["activity_frequency"] = activity_frequency
        
        result = await self._get("/experts/by-activity", params)
        return result.get("experts", [])
    
    # ========================================================================
    # PLANNING-SPECIFIC HELPER METHODS
    # ========================================================================
    
    async def get_experts_for_tech_stack(
        self,
        technologies: List[str],
        max_per_tech: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get experts for each technology in a tech stack.
        
        Args:
            technologies: List of technologies/topics
            max_per_tech: Maximum experts per technology
        
        Returns:
            Dictionary mapping technology to list of experts
        """
        results = {}
        
        for tech in technologies:
            try:
                experts = await self.find_experts_by_topic(
                    topic=tech,
                    max_results=max_per_tech,
                    min_documents=2
                )
                results[tech] = experts
                logger.info(f"Found {len(experts)} experts for {tech}")
            except Exception as e:
                logger.warning(f"Could not find experts for {tech}: {e}")
                results[tech] = []
        
        return results
    
    async def get_smes_for_components(
        self,
        components: List[str],
        max_per_component: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get SMEs for each component in the system.
        
        Args:
            components: List of components/domains
            max_per_component: Maximum SMEs per component
        
        Returns:
            Dictionary mapping component to list of SMEs
        """
        results = {}
        
        for component in components:
            try:
                smes = await self.find_subject_matter_experts(
                    area=component,
                    max_results=max_per_component
                )
                results[component] = smes
                logger.info(f"Found {len(smes)} SMEs for {component}")
            except Exception as e:
                logger.warning(f"Could not find SMEs for {component}: {e}")
                results[component] = []
        
        return results
    
    async def suggest_team_augmentation(
        self,
        required_skills: List[str],
        current_team_id: Optional[str] = None,
        experience_level: str = "mid",
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest team members to fill skill gaps.
        
        Args:
            required_skills: List of required skills/technologies
            current_team_id: Current team ID (to exclude existing members)
            experience_level: Desired experience level
            max_suggestions: Maximum suggestions to return
        
        Returns:
            List of suggested team members
        """
        suggestions = []
        
        for skill in required_skills:
            try:
                # Find experts with required experience level
                experts = await self.find_experts_by_experience(
                    level=experience_level,
                    domain=skill,
                    min_contributions=10
                )
                
                # Add to suggestions
                for expert in experts[:max_suggestions]:
                    expert["suggested_for"] = skill
                    if expert not in suggestions:
                        suggestions.append(expert)
            except Exception as e:
                logger.warning(f"Could not find experts for skill {skill}: {e}")
        
        return suggestions[:max_suggestions]
    
    async def find_reviewers_for_tech_stack(
        self,
        technologies: List[str],
        quality: str = "high",
        max_per_tech: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find code reviewers for each technology.
        
        Args:
            technologies: List of technologies
            quality: Review quality level
            max_per_tech: Maximum reviewers per technology
        
        Returns:
            Dictionary mapping technology to list of reviewers
        """
        results = {}
        
        for tech in technologies:
            try:
                reviewers = await self.find_code_reviewers(
                    quality=quality,
                    technology=tech,
                    min_reviews=5
                )
                results[tech] = reviewers[:max_per_tech]
                logger.info(f"Found {len(results[tech])} reviewers for {tech}")
            except Exception as e:
                logger.warning(f"Could not find reviewers for {tech}: {e}")
                results[tech] = []
        
        return results
    
    async def health_check(self) -> bool:
        """
        Check if expert-finder service is available.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            result = await self._get("/health")
            return result.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Expert-finder health check failed: {e}")
            return False

