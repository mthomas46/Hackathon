"""
External Service Cataloger - Phase 9.2
Catalogs discovered services and links to team, docs, and history.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..entities.external_service_entities import (
    ExternalServiceMatch,
    ServiceCatalogEntry
)


class ExternalServiceCataloger:
    """
    Catalogs external services by:
    - Storing in external-service-store
    - Linking to team skills
    - Linking to historical tickets
    - Linking to documentation
    """
    
    def __init__(
        self,
        external_service_store_client=None,
        user_store_client=None,
        source_agent_client=None,
        doc_store_client=None,
        log_client=None
    ):
        """Initialize the cataloger."""
        self.external_service_store = external_service_store_client
        self.user_store = user_store_client
        self.source_agent = source_agent_client
        self.doc_store = doc_store_client
        self.log_client = log_client
    
    async def catalog_services(
        self,
        services: List[ExternalServiceMatch],
        feature_context: str
    ) -> List[ServiceCatalogEntry]:
        """
        Catalog all discovered services with full relationship data.
        
        Args:
            services: List of discovered services
            feature_context: Context about the feature being planned
        
        Returns:
            List of cataloged services with all relationships
        """
        if self.log_client:
            await self.log_client.log_info(
                f"Cataloging {len(services)} discovered services",
                context={"feature_context": feature_context}
            )
        
        cataloged = []
        
        for service in services:
            # Store in external-service-store
            await self._store_service(service, feature_context)
            
            # Link to skills
            skills_coverage = await self._link_to_skills(service)
            
            # Link to historical tickets
            historical_tickets = await self._link_to_history(service)
            
            # Link to documentation
            documentation = await self._link_to_documentation(service)
            
            # Calculate coverage score
            coverage_score = self._calculate_coverage_score(
                skills_coverage,
                historical_tickets,
                documentation
            )
            
            # Determine documentation quality
            doc_quality = self._assess_documentation_quality(documentation)
            
            # Extract team members
            team_members = self._extract_team_members(skills_coverage)
            
            # Create catalog entry
            entry = ServiceCatalogEntry(
                service_match=service,
                skills_coverage=skills_coverage,
                historical_tickets=historical_tickets,
                documentation_links=documentation,
                team_members=team_members,
                coverage_score=coverage_score,
                documentation_quality=doc_quality
            )
            
            cataloged.append(entry)
            
            if self.log_client:
                await self.log_client.log_debug(
                    f"Cataloged service: {service.name}",
                    context={
                        "service_id": service.service_id,
                        "coverage_score": coverage_score,
                        "doc_quality": doc_quality,
                        "team_members": len(team_members)
                    }
                )
        
        if self.log_client:
            await self.log_client.log_info(
                f"Cataloging complete: {len(cataloged)} services",
                context={
                    "avg_coverage": sum(s.coverage_score for s in cataloged) / len(cataloged) if cataloged else 0,
                    "excellent_docs": len([s for s in cataloged if s.documentation_quality == "Excellent"])
                }
            )
        
        return cataloged
    
    async def _store_service(
        self,
        service: ExternalServiceMatch,
        feature_context: str
    ) -> None:
        """Store service in external-service-store."""
        if not self.external_service_store:
            return
        
        # Would call: await self.external_service_store.create_or_update(...)
        # Mock implementation for now
        pass
    
    async def _link_to_skills(
        self,
        service: ExternalServiceMatch
    ) -> Dict[str, Any]:
        """
        Link service to team skills.
        
        Returns dict with:
        - required_skills: List of skill requirements
        - team_coverage: List of team members with each skill
        - coverage_score: 0.0-1.0
        """
        if not self.user_store:
            return {"required_skills": [], "team_coverage": [], "coverage_score": 0.0}
        
        # Mock implementation - would query user-store for skills
        # For demonstration, return mock data based on service
        if "firebase" in service.service_id.lower():
            return {
                "required_skills": ["iOS (Swift)", "Android (Kotlin)", "Backend (Python)"],
                "team_coverage": [
                    {
                        "skill": "iOS (Swift)",
                        "team_members": ["Marcus Johnson"],
                        "proficiency": "Expert",
                        "years_experience": 6
                    },
                    {
                        "skill": "Android (Kotlin)",
                        "team_members": ["Priya Patel"],
                        "proficiency": "Expert",
                        "years_experience": 5
                    },
                    {
                        "skill": "Backend (Python)",
                        "team_members": ["Sarah Chen"],
                        "proficiency": "Expert",
                        "years_experience": 8
                    }
                ],
                "coverage_score": 1.0
            }
        elif "sendgrid" in service.service_id.lower():
            return {
                "required_skills": ["Backend (Python)", "Email Systems"],
                "team_coverage": [
                    {
                        "skill": "Backend (Python)",
                        "team_members": ["Sarah Chen"],
                        "proficiency": "Expert",
                        "years_experience": 8
                    },
                    {
                        "skill": "Email Systems",
                        "team_members": [],
                        "proficiency": None,
                        "years_experience": 0
                    }
                ],
                "coverage_score": 0.5
            }
        else:
            return {
                "required_skills": service.technologies,
                "team_coverage": [],
                "coverage_score": 0.0
            }
    
    async def _link_to_history(
        self,
        service: ExternalServiceMatch
    ) -> List[Dict[str, Any]]:
        """Link service to historical Jira tickets."""
        if not self.source_agent:
            return []
        
        # Mock implementation - would query source-agent for related tickets
        if "firebase" in service.service_id.lower():
            return [
                {
                    "ticket_id": "MOBILE-045",
                    "title": "Firebase integration for analytics",
                    "story_points": 8,
                    "status": "DONE",
                    "assignee": "Sarah Chen",
                    "relevance": 0.97,
                    "completed_date": "2024-08-15"
                },
                {
                    "ticket_id": "NOTIF-001",
                    "title": "Implement push notifications with FCM",
                    "story_points": 13,
                    "status": "DONE",
                    "assignee": "Marcus Johnson",
                    "relevance": 0.96,
                    "completed_date": "2024-09-20"
                }
            ]
        elif "sendgrid" in service.service_id.lower():
            return [
                {
                    "ticket_id": "EMAIL-012",
                    "title": "SendGrid email templating",
                    "story_points": 5,
                    "status": "DONE",
                    "assignee": "Emily Wu",
                    "relevance": 0.89,
                    "completed_date": "2024-07-10"
                }
            ]
        else:
            return []
    
    async def _link_to_documentation(
        self,
        service: ExternalServiceMatch
    ) -> List[Dict[str, Any]]:
        """Link service to documentation."""
        if not self.doc_store:
            return []
        
        # Mock implementation - would query doc-store
        if "firebase" in service.service_id.lower():
            return [
                {
                    "doc_id": "CONF-001",
                    "title": "Firebase Integration Best Practices",
                    "type": "confluence",
                    "relevance": 0.94,
                    "word_count": 2500,
                    "last_updated": "2024-09-01"
                },
                {
                    "doc_id": "PR-456",
                    "title": "feat: Add Firebase push notification support",
                    "type": "github_pr",
                    "relevance": 0.97,
                    "files_changed": 15,
                    "last_updated": "2024-09-20"
                },
                {
                    "doc_id": "EXTERNAL",
                    "title": "Firebase Cloud Messaging Documentation",
                    "type": "external",
                    "url": "https://firebase.google.com/docs/cloud-messaging",
                    "relevance": 0.92,
                    "quality_score": 0.92
                }
            ]
        elif "sendgrid" in service.service_id.lower():
            return [
                {
                    "doc_id": "EXTERNAL",
                    "title": "SendGrid API Documentation",
                    "type": "external",
                    "url": "https://docs.sendgrid.com/",
                    "relevance": 0.95,
                    "quality_score": 0.90
                }
            ]
        else:
            return []
    
    def _calculate_coverage_score(
        self,
        skills: Dict[str, Any],
        history: List[Dict[str, Any]],
        docs: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall coverage score.
        
        Factors:
        - Skills coverage: 50%
        - Historical experience: 30%
        - Documentation: 20%
        """
        skills_score = skills.get("coverage_score", 0.0)
        history_score = 1.0 if len(history) >= 2 else (0.5 if len(history) == 1 else 0.0)
        doc_score = min(len(docs) / 3.0, 1.0)  # Max score at 3+ docs
        
        return (skills_score * 0.5) + (history_score * 0.3) + (doc_score * 0.2)
    
    def _assess_documentation_quality(
        self,
        docs: List[Dict[str, Any]]
    ) -> str:
        """Assess documentation quality."""
        if len(docs) >= 3:
            return "Excellent"
        elif len(docs) == 2:
            return "Good"
        elif len(docs) == 1:
            return "Fair"
        else:
            return "None"
    
    def _extract_team_members(
        self,
        skills: Dict[str, Any]
    ) -> List[str]:
        """Extract unique team member names."""
        members = set()
        for coverage in skills.get("team_coverage", []):
            members.update(coverage.get("team_members", []))
        return list(members)

