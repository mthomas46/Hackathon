"""
Expert-Augmented Roadmap Orchestrator

Extends roadmap generation with expert-finder integration to:
- Identify SMEs for each technology
- Find code reviewers
- Suggest team augmentation
- Provide expert context in development plans

Phase 4.1: Planning Service Integration
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import date
import logging

from ..entities.feature import Feature
from ..entities.roadmap import Roadmap
from .roadmap_orchestrator import (
    RoadmapOrchestrator,
    ComprehensiveRoadmapRequest,
    ComprehensiveRoadmap
)
from ...infrastructure.expert_finder_client import ExpertFinderClient


logger = logging.getLogger(__name__)


@dataclass
class ExpertContext:
    """Expert recommendations for a project."""
    technology_experts: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    component_smes: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    code_reviewers: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    team_augmentation_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    skill_gaps: List[str] = field(default_factory=list)
    expert_finder_available: bool = True
    
    def summary(self) -> Dict[str, Any]:
        """Generate summary of expert context."""
        total_experts = sum(len(experts) for experts in self.technology_experts.values())
        total_smes = sum(len(smes) for smes in self.component_smes.values())
        total_reviewers = sum(len(reviewers) for reviewers in self.code_reviewers.values())
        
        return {
            "expert_finder_available": self.expert_finder_available,
            "total_technologies": len(self.technology_experts),
            "total_experts_identified": total_experts,
            "total_smes_identified": total_smes,
            "total_reviewers_identified": total_reviewers,
            "team_augmentation_suggestions": len(self.team_augmentation_suggestions),
            "skill_gaps": len(self.skill_gaps)
        }


@dataclass
class ExpertAugmentedRoadmap(ComprehensiveRoadmap):
    """Comprehensive roadmap with expert context."""
    expert_context: Optional[ExpertContext] = None
    
    def summary(self) -> Dict[str, Any]:
        """Generate enhanced summary with expert context."""
        base_summary = super().summary()
        
        if self.expert_context:
            base_summary["expert_context"] = self.expert_context.summary()
        
        return base_summary


class ExpertAugmentedOrchestrator:
    """
    Enhanced roadmap orchestrator with expert-finder integration.
    
    Extends standard orchestration with:
    - Expert discovery for technologies
    - SME identification for components
    - Code reviewer recommendations
    - Team augmentation suggestions
    - Skill gap analysis
    """
    
    def __init__(
        self,
        expert_finder_url: str = "http://localhost:5160",
        enable_expert_discovery: bool = True
    ):
        """
        Initialize expert-augmented orchestrator.
        
        Args:
            expert_finder_url: URL of expert-finder service
            enable_expert_discovery: Enable expert discovery (can disable for fallback)
        """
        self.base_orchestrator = RoadmapOrchestrator()
        self.expert_finder_url = expert_finder_url
        self.enable_expert_discovery = enable_expert_discovery
        logger.info(f"Expert-Augmented Orchestrator initialized (expert discovery: {enable_expert_discovery})")
    
    async def generate_comprehensive_roadmap_with_experts(
        self,
        request: ComprehensiveRoadmapRequest,
        technologies: Optional[List[str]] = None,
        components: Optional[List[str]] = None
    ) -> ExpertAugmentedRoadmap:
        """
        Generate comprehensive roadmap with expert recommendations.
        
        Args:
            request: Comprehensive roadmap request
            technologies: List of technologies (extracted from features if not provided)
            components: List of components (extracted from features if not provided)
        
        Returns:
            ExpertAugmentedRoadmap with expert context
        """
        # Step 1: Generate base roadmap (synchronous)
        logger.info("Generating base roadmap...")
        base_roadmap = self.base_orchestrator.generate_comprehensive_roadmap(request)
        
        # Step 2: Extract technologies and components if not provided
        if technologies is None:
            technologies = self._extract_technologies(request.features)
        if components is None:
            components = self._extract_components(request.features)
        
        logger.info(f"Identified {len(technologies)} technologies and {len(components)} components")
        
        # Step 3: Discover experts (async)
        expert_context = None
        if self.enable_expert_discovery:
            try:
                expert_context = await self._discover_experts(
                    technologies=technologies,
                    components=components,
                    team_id=request.team_id
                )
                
                # Add expert-based recommendations
                self._enhance_recommendations_with_experts(
                    base_roadmap.recommendations,
                    expert_context
                )
            except Exception as e:
                logger.error(f"Expert discovery failed: {e}")
                base_roadmap.warnings.append(
                    f"Expert discovery unavailable: {str(e)}"
                )
                expert_context = ExpertContext(expert_finder_available=False)
        
        # Step 4: Create expert-augmented roadmap
        return ExpertAugmentedRoadmap(
            roadmap=base_roadmap.roadmap,
            generation_result=base_roadmap.generation_result,
            decomposition_results=base_roadmap.decomposition_results,
            timeline_estimate=base_roadmap.timeline_estimate,
            dependency_analysis=base_roadmap.dependency_analysis,
            milestone_plan=base_roadmap.milestone_plan,
            warnings=base_roadmap.warnings,
            recommendations=base_roadmap.recommendations,
            expert_context=expert_context
        )
    
    def _extract_technologies(self, features: List[Feature]) -> List[str]:
        """
        Extract unique technologies from features.
        
        Args:
            features: List of features
        
        Returns:
            List of unique technology names
        """
        technologies = set()
        
        for feature in features:
            # Check feature metadata for technologies
            if hasattr(feature, 'metadata') and feature.metadata:
                tech_list = feature.metadata.get('technologies', [])
                if isinstance(tech_list, list):
                    technologies.update(tech_list)
                elif isinstance(tech_list, str):
                    technologies.add(tech_list)
            
            # Check feature tags
            if hasattr(feature, 'tags') and feature.tags:
                for tag in feature.tags:
                    if self._is_technology(tag):
                        technologies.add(tag)
        
        return list(technologies)
    
    def _extract_components(self, features: List[Feature]) -> List[str]:
        """
        Extract unique components from features.
        
        Args:
            features: List of features
        
        Returns:
            List of unique component names
        """
        components = set()
        
        for feature in features:
            # Check feature metadata for components
            if hasattr(feature, 'metadata') and feature.metadata:
                comp_list = feature.metadata.get('components', [])
                if isinstance(comp_list, list):
                    components.update(comp_list)
                elif isinstance(comp_list, str):
                    components.add(comp_list)
            
            # Use feature title as component if no specific components
            if not components and hasattr(feature, 'title'):
                components.add(feature.title)
        
        return list(components)
    
    def _is_technology(self, tag: str) -> bool:
        """
        Heuristic to determine if a tag represents a technology.
        
        Args:
            tag: Tag to check
        
        Returns:
            True if likely a technology
        """
        # Common technology patterns
        tech_indicators = [
            'python', 'java', 'javascript', 'typescript', 'go', 'rust',
            'react', 'vue', 'angular', 'fastapi', 'django', 'flask',
            'docker', 'kubernetes', 'k8s', 'postgres', 'mysql', 'redis',
            'aws', 'gcp', 'azure', 'kafka', 'rabbitmq', 'graphql', 'rest'
        ]
        
        tag_lower = tag.lower()
        return any(indicator in tag_lower for indicator in tech_indicators)
    
    async def _discover_experts(
        self,
        technologies: List[str],
        components: List[str],
        team_id: str
    ) -> ExpertContext:
        """
        Discover experts using expert-finder service.
        
        Args:
            technologies: List of technologies
            components: List of components
            team_id: Team identifier
        
        Returns:
            ExpertContext with all expert recommendations
        """
        expert_context = ExpertContext()
        
        async with ExpertFinderClient(base_url=self.expert_finder_url) as client:
            # Check service health
            is_healthy = await client.health_check()
            expert_context.expert_finder_available = is_healthy
            
            if not is_healthy:
                logger.warning("Expert-finder service is not healthy")
                return expert_context
            
            # 1. Find experts for each technology
            logger.info("Discovering technology experts...")
            expert_context.technology_experts = await client.get_experts_for_tech_stack(
                technologies=technologies,
                max_per_tech=5
            )
            
            # 2. Find SMEs for each component
            logger.info("Identifying component SMEs...")
            expert_context.component_smes = await client.get_smes_for_components(
                components=components,
                max_per_component=3
            )
            
            # 3. Find code reviewers for technologies
            logger.info("Finding code reviewers...")
            expert_context.code_reviewers = await client.find_reviewers_for_tech_stack(
                technologies=technologies,
                quality="high",
                max_per_tech=3
            )
            
            # 4. Identify skill gaps
            for tech, experts in expert_context.technology_experts.items():
                if len(experts) == 0:
                    expert_context.skill_gaps.append(tech)
                    logger.warning(f"Skill gap detected: {tech}")
            
            # 5. Suggest team augmentation for skill gaps
            if expert_context.skill_gaps:
                logger.info(f"Suggesting team augmentation for {len(expert_context.skill_gaps)} skill gaps...")
                expert_context.team_augmentation_suggestions = await client.suggest_team_augmentation(
                    required_skills=expert_context.skill_gaps,
                    current_team_id=team_id,
                    experience_level="mid",
                    max_suggestions=5
                )
        
        logger.info(f"Expert discovery complete: {len(expert_context.technology_experts)} technologies covered")
        return expert_context
    
    def _enhance_recommendations_with_experts(
        self,
        recommendations: List[str],
        expert_context: ExpertContext
    ) -> None:
        """
        Add expert-based recommendations to roadmap.
        
        Args:
            recommendations: List of recommendations to enhance
            expert_context: Expert context with discoveries
        """
        if not expert_context.expert_finder_available:
            recommendations.append(
                "⚠️ Expert-finder service unavailable - expert recommendations not included"
            )
            return
        
        # Technology expert recommendations
        tech_with_experts = [
            tech for tech, experts in expert_context.technology_experts.items()
            if len(experts) > 0
        ]
        if tech_with_experts:
            recommendations.append(
                f"✅ Identified experts for {len(tech_with_experts)} technologies: {', '.join(tech_with_experts[:5])}"
            )
        
        # SME recommendations
        components_with_smes = [
            comp for comp, smes in expert_context.component_smes.items()
            if len(smes) > 0
        ]
        if components_with_smes:
            recommendations.append(
                f"✅ Identified Subject Matter Experts for {len(components_with_smes)} components"
            )
        
        # Skill gap warnings
        if expert_context.skill_gaps:
            recommendations.append(
                f"⚠️ Skill gaps detected: {', '.join(expert_context.skill_gaps)} - Consider team augmentation"
            )
        
        # Team augmentation suggestions
        if expert_context.team_augmentation_suggestions:
            suggested_experts = [
                f"{s.get('username')} ({s.get('suggested_for')})"
                for s in expert_context.team_augmentation_suggestions[:3]
            ]
            recommendations.append(
                f"💡 Team augmentation suggestions: {', '.join(suggested_experts)}"
            )
        
        # Code reviewer availability
        total_reviewers = sum(
            len(reviewers) for reviewers in expert_context.code_reviewers.values()
        )
        if total_reviewers > 0:
            recommendations.append(
                f"✅ {total_reviewers} qualified code reviewers available across technologies"
            )
        else:
            recommendations.append(
                "⚠️ Limited code reviewer availability - consider reviewer training or hiring"
            )


# Convenience function for quick usage
async def generate_expert_augmented_roadmap(
    request: ComprehensiveRoadmapRequest,
    technologies: Optional[List[str]] = None,
    components: Optional[List[str]] = None,
    expert_finder_url: str = "http://localhost:5160"
) -> ExpertAugmentedRoadmap:
    """
    Convenience function to generate expert-augmented roadmap.
    
    Args:
        request: Comprehensive roadmap request
        technologies: Optional list of technologies
        components: Optional list of components
        expert_finder_url: Expert-finder service URL
    
    Returns:
        ExpertAugmentedRoadmap with expert context
    """
    orchestrator = ExpertAugmentedOrchestrator(expert_finder_url=expert_finder_url)
    return await orchestrator.generate_comprehensive_roadmap_with_experts(
        request=request,
        technologies=technologies,
        components=components
    )

