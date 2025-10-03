"""
Knowledge Gap Detector - Phase 9.4
Detects documentation, skills, and configuration gaps.
"""

from typing import List, Dict, Any
from datetime import datetime

from ..entities.external_service_entities import (
    ServiceCatalogEntry,
    KnowledgeGap,
    KnowledgeGapAnalysis,
    IssueSeverity
)


class KnowledgeGapDetector:
    """
    Detects gaps in:
    - Documentation (internal knowledge)
    - Team skills (training needs)
    - Configuration (setup requirements)
    """
    
    def __init__(
        self,
        doc_store_client=None,
        user_store_client=None,
        summarizer_hub_client=None,
        log_client=None
    ):
        """Initialize the gap detector."""
        self.doc_store = doc_store_client
        self.user_store = user_store_client
        self.summarizer_hub = summarizer_hub_client
        self.log_client = log_client
    
    async def detect_gaps(
        self,
        cataloged_services: List[ServiceCatalogEntry]
    ) -> List[KnowledgeGapAnalysis]:
        """
        Detect knowledge gaps for all services.
        
        Returns:
            List of gap analyses
        """
        if self.log_client:
            await self.log_client.log_info(
                f"Detecting knowledge gaps for {len(cataloged_services)} services"
            )
        
        analyses = []
        
        for entry in cataloged_services:
            service = entry.service_match
            
            # Detect documentation gaps
            doc_gaps = await self._detect_documentation_gaps(entry)
            
            # Detect skills gaps
            skills_gaps = await self._detect_skills_gaps(entry)
            
            # Detect configuration gaps
            config_gaps = await self._detect_configuration_gaps(entry)
            
            # Calculate totals
            all_gaps = doc_gaps + skills_gaps + config_gaps
            total_sp = sum(gap.story_points_to_add for gap in all_gaps)
            total_days = sum(gap.timeline_impact_days for gap in all_gaps)
            
            # Generate enrichment actions
            enrichment_actions = self._generate_enrichment_actions(
                doc_gaps, skills_gaps, config_gaps
            )
            
            analysis = KnowledgeGapAnalysis(
                service_id=service.service_id,
                service_name=service.name,
                documentation_gaps=doc_gaps,
                skills_gaps=skills_gaps,
                configuration_gaps=config_gaps,
                total_story_points_to_add=total_sp,
                total_timeline_impact_days=total_days,
                enrichment_actions=enrichment_actions
            )
            
            analyses.append(analysis)
            
            if self.log_client and all_gaps:
                await self.log_client.log_info(
                    f"Knowledge gaps found for {service.name}: {len(all_gaps)} gaps",
                    context={
                        "service_id": service.service_id,
                        "doc_gaps": len(doc_gaps),
                        "skills_gaps": len(skills_gaps),
                        "config_gaps": len(config_gaps)
                    }
                )
        
        return analyses
    
    async def _detect_documentation_gaps(
        self,
        entry: ServiceCatalogEntry
    ) -> List[KnowledgeGap]:
        """Detect documentation gaps."""
        gaps = []
        
        # Check if we have internal documentation
        internal_docs = [
            doc for doc in entry.documentation_links
            if doc.get("type") in ["confluence", "github_pr", "github_issue"]
        ]
        
        if len(internal_docs) < 2:
            # Mock gap for Firebase Admin SDK
            if "firebase" in entry.service_match.service_id.lower():
                gaps.append(KnowledgeGap(
                    gap_type="documentation",
                    severity=IssueSeverity.MEDIUM,
                    description="Firebase Admin SDK integration patterns not documented internally",
                    impact="Team has no internal knowledge base, relies on external docs",
                    remediation_actions=[
                        {
                            "action": "Create Confluence page: 'Firebase Admin SDK Integration Guide'",
                            "owner": "Sarah Chen",
                            "effort_hours": 4,
                            "priority": "HIGH"
                        },
                        {
                            "action": "Document quota management patterns",
                            "owner": "Sarah Chen",
                            "effort_hours": 2,
                            "priority": "MEDIUM"
                        }
                    ],
                    story_points_to_add=0,  # Documentation tasks
                    timeline_impact_days=0.5,
                    assignee="Sarah Chen"
                ))
        
        return gaps
    
    async def _detect_skills_gaps(
        self,
        entry: ServiceCatalogEntry
    ) -> List[KnowledgeGap]:
        """Detect skills gaps."""
        gaps = []
        
        # Check skills coverage
        skills_coverage = entry.skills_coverage
        team_coverage = skills_coverage.get("team_coverage", [])
        
        for skill_info in team_coverage:
            skill = skill_info.get("skill", "")
            proficiency = skill_info.get("proficiency", "")
            team_members = skill_info.get("team_members", [])
            
            # Check for low proficiency or missing team members
            if not team_members or proficiency == "Beginner":
                # Mock gap
                if "firebase" in entry.service_match.service_id.lower() and "Admin" in skill:
                    gaps.append(KnowledgeGap(
                        gap_type="skills",
                        severity=IssueSeverity.MEDIUM,
                        description=f"Team member needs ramp-up on Firebase Admin SDK",
                        impact="May slow initial implementation",
                        remediation_actions=[
                            {
                                "action": "Complete Firebase Admin SDK tutorial + examples",
                                "owner": "Sarah Chen",
                                "effort_hours": 4,
                                "priority": "HIGH",
                                "can_parallel": True
                            }
                        ],
                        story_points_to_add=0,
                        timeline_impact_days=0.5,  # Can be done in parallel
                        assignee="Sarah Chen"
                    ))
        
        return gaps
    
    async def _detect_configuration_gaps(
        self,
        entry: ServiceCatalogEntry
    ) -> List[KnowledgeGap]:
        """Detect configuration gaps."""
        gaps = []
        
        # Mock implementation - would check for documented config processes
        if "firebase" in entry.service_match.service_id.lower():
            gaps.append(KnowledgeGap(
                gap_type="configuration",
                severity=IssueSeverity.HIGH,
                description="Backend service account credentials setup not documented",
                impact="Backend cannot send notifications",
                remediation_actions=[
                    {
                        "action": "Document secure credential management",
                        "owner": "Sarah Chen + Security Team",
                        "effort_hours": 3,
                        "priority": "HIGH"
                    }
                ],
                story_points_to_add=2,  # Includes secure setup implementation
                timeline_impact_days=0.4,
                assignee="Sarah Chen"
            ))
        
        return gaps
    
    def _generate_enrichment_actions(
        self,
        doc_gaps: List[KnowledgeGap],
        skills_gaps: List[KnowledgeGap],
        config_gaps: List[KnowledgeGap]
    ) -> List[Dict[str, Any]]:
        """Generate consolidated enrichment actions."""
        actions = []
        
        for gap in doc_gaps + skills_gaps + config_gaps:
            actions.extend(gap.remediation_actions)
        
        return actions

