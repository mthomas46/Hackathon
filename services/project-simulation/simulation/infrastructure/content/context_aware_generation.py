"""Context-Aware Document Generation - Advanced Content Generation with Project Intelligence.

This module implements sophisticated context-aware document generation that leverages
project context, team dynamics, timeline awareness, and personality traits to create
realistic, intelligent content that reflects the actual project environment and team
characteristics.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime, timedelta
from enum import Enum
import random
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.utilities.simulation_utilities import get_simulation_cache, get_simulation_validator
from simulation.infrastructure.integration.service_clients import get_ecosystem_client

# Import simulation domain
from simulation.domain.value_objects import ProjectType, ComplexityLevel, TeamMemberRole


class PersonalityTrait(Enum):
    """Personality traits for team members."""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    DETAIL_ORIENTED = "detail_oriented"
    STRATEGIC = "strategic"
    COLLABORATIVE = "collaborative"
    PRAGMATIC = "pragmatic"
    INNOVATIVE = "innovative"
    METHODICAL = "methodical"


class CommunicationStyle(Enum):
    """Communication styles for team members."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    BUSINESS = "business"
    CONCISE = "concise"
    DETAILED = "detailed"


class ContentContext:
    """Comprehensive context for content generation."""

    def __init__(self,
                 project_config: Dict[str, Any],
                 team_members: List[Dict[str, Any]],
                 timeline: Dict[str, Any],
                 phase_context: Optional[Dict[str, Any]] = None):
        """Initialize content context."""
        self.project_config = project_config
        self.team_members = team_members
        self.timeline = timeline
        self.phase_context = phase_context or {}
        self.generation_timestamp = datetime.now()

        # Enhanced team member profiles
        self.team_profiles = self._build_team_profiles()
        self.team_dynamics = self._analyze_team_dynamics()

        # Project intelligence
        self.project_intelligence = self._build_project_intelligence()

        # Timeline awareness
        self.timeline_awareness = self._build_timeline_awareness()

    def _build_team_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Build detailed team member profiles with personality traits."""
        profiles = {}

        for member in self.team_members:
            member_id = member.get("member_id", member.get("id", f"member_{len(profiles)}"))

            # Assign personality traits based on role and experience
            personality = self._assign_personality_trait(member)
            communication_style = self._assign_communication_style(member)

            # Calculate influence and expertise
            influence_score = self._calculate_influence_score(member)
            expertise_score = self._calculate_expertise_score(member)

            profiles[member_id] = {
                "name": member.get("name", "Unknown"),
                "role": member.get("role", "developer"),
                "experience_years": member.get("experience_years", 2),
                "skills": member.get("skills", []),
                "personality_trait": personality,
                "communication_style": communication_style,
                "influence_score": influence_score,
                "expertise_score": expertise_score,
                "work_patterns": self._generate_work_patterns(member),
                "collaboration_style": self._generate_collaboration_style(member)
            }

        return profiles

    def _assign_personality_trait(self, member: Dict[str, Any]) -> PersonalityTrait:
        """Assign personality trait based on member characteristics."""
        role = member.get("role", "").lower()
        experience = member.get("experience_years", 2)

        # Role-based personality assignment
        if "architect" in role or "lead" in role:
            return PersonalityTrait.STRATEGIC
        elif "designer" in role or "ux" in role:
            return PersonalityTrait.CREATIVE
        elif "qa" in role or "analyst" in role:
            return PersonalityTrait.DETAIL_ORIENTED
        elif experience > 8:
            return PersonalityTrait.METHODICAL
        elif experience < 3:
            return PersonalityTrait.INNOVATIVE
        else:
            return random.choice([PersonalityTrait.ANALYTICAL, PersonalityTrait.PRAGMATIC])

    def _assign_communication_style(self, member: Dict[str, Any]) -> CommunicationStyle:
        """Assign communication style based on member characteristics."""
        role = member.get("role", "").lower()
        experience = member.get("experience_years", 2)

        if "architect" in role or "manager" in role:
            return CommunicationStyle.FORMAL
        elif "developer" in role and experience > 5:
            return CommunicationStyle.TECHNICAL
        elif experience < 3:
            return CommunicationStyle.CASUAL
        else:
            return random.choice([CommunicationStyle.BUSINESS, CommunicationStyle.CONCISE])

    def _calculate_influence_score(self, member: Dict[str, Any]) -> float:
        """Calculate team member influence score."""
        role = member.get("role", "").lower()
        experience = member.get("experience_years", 2)

        # Base score from role
        role_score = {
            "architect": 0.9, "lead": 0.8, "manager": 0.8,
            "senior": 0.7, "developer": 0.6, "qa": 0.5,
            "junior": 0.3
        }

        base_score = 0.5  # Default
        for role_key, score in role_score.items():
            if role_key in role:
                base_score = score
                break

        # Experience multiplier
        experience_multiplier = min(1.5, 1.0 + (experience * 0.1))

        return min(1.0, base_score * experience_multiplier)

    def _calculate_expertise_score(self, member: Dict[str, Any]) -> float:
        """Calculate team member expertise score."""
        skills = member.get("skills", [])
        experience = member.get("experience_years", 2)

        # Skill-based scoring
        skill_score = len(skills) * 0.1
        experience_score = min(1.0, experience * 0.1)

        return min(1.0, (skill_score + experience_score) / 2)

    def _generate_work_patterns(self, member: Dict[str, Any]) -> Dict[str, Any]:
        """Generate work patterns for team member."""
        role = member.get("role", "").lower()
        experience = member.get("experience_years", 2)

        if "architect" in role:
            return {
                "planning_focus": 0.8,
                "coding_focus": 0.2,
                "review_focus": 0.9,
                "meeting_frequency": "daily"
            }
        elif "developer" in role:
            return {
                "planning_focus": 0.3,
                "coding_focus": 0.8,
                "review_focus": 0.6,
                "meeting_frequency": "weekly"
            }
        elif "qa" in role:
            return {
                "planning_focus": 0.4,
                "coding_focus": 0.1,
                "review_focus": 0.8,
                "meeting_frequency": "bi_weekly"
            }
        else:
            return {
                "planning_focus": 0.5,
                "coding_focus": 0.5,
                "review_focus": 0.5,
                "meeting_frequency": "weekly"
            }

    def _generate_collaboration_style(self, member: Dict[str, Any]) -> str:
        """Generate collaboration style for team member."""
        personality = self._assign_personality_trait(member)

        if personality == PersonalityTrait.COLLABORATIVE:
            return "team_player"
        elif personality == PersonalityTrait.STRATEGIC:
            return "mentor"
        elif personality == PersonalityTrait.DETAIL_ORIENTED:
            return "quality_focused"
        elif personality == PersonalityTrait.CREATIVE:
            return "idea_generator"
        else:
            return "balanced"

    def _analyze_team_dynamics(self) -> Dict[str, Any]:
        """Analyze team dynamics and relationships."""
        total_members = len(self.team_profiles)
        roles = {}
        experience_levels = {"junior": 0, "mid": 0, "senior": 0}

        for profile in self.team_profiles.values():
            role = profile["role"]
            roles[role] = roles.get(role, 0) + 1

            exp = profile["experience_years"]
            if exp < 3:
                experience_levels["junior"] += 1
            elif exp < 7:
                experience_levels["mid"] += 1
            else:
                experience_levels["senior"] += 1

        # Calculate diversity scores
        role_diversity = len(roles) / max(1, total_members)
        experience_balance = 1 - (max(experience_levels.values()) / max(1, total_members))

        return {
            "team_size": total_members,
            "role_distribution": roles,
            "experience_distribution": experience_levels,
            "role_diversity_score": role_diversity,
            "experience_balance_score": experience_balance,
            "collaboration_patterns": self._analyze_collaboration_patterns()
        }

    def _analyze_collaboration_patterns(self) -> Dict[str, Any]:
        """Analyze team collaboration patterns."""
        collaboration_styles = {}
        for profile in self.team_profiles.values():
            style = profile["collaboration_style"]
            collaboration_styles[style] = collaboration_styles.get(style, 0) + 1

        dominant_style = max(collaboration_styles.items(), key=lambda x: x[1])[0] if collaboration_styles else "balanced"

        return {
            "dominant_style": dominant_style,
            "style_distribution": collaboration_styles,
            "communication_effectiveness": self._calculate_communication_effectiveness()
        }

    def _calculate_communication_effectiveness(self) -> float:
        """Calculate team communication effectiveness."""
        # Simplified calculation based on team composition
        team_size = len(self.team_profiles)

        if team_size <= 3:
            return 0.9  # Small teams communicate well
        elif team_size <= 7:
            return 0.7  # Medium teams have good balance
        else:
            return 0.5  # Large teams have communication challenges

    def _build_project_intelligence(self) -> Dict[str, Any]:
        """Build project intelligence based on configuration."""
        project_type = self.project_config.get("type", "web_application")
        complexity = self.project_config.get("complexity", "medium")
        duration_weeks = self.project_config.get("duration_weeks", 8)

        # Project complexity factors
        complexity_factors = {
            "simple": {"technical_debt": 0.2, "requirement_stability": 0.8, "innovation_required": 0.3},
            "medium": {"technical_debt": 0.4, "requirement_stability": 0.6, "innovation_required": 0.5},
            "complex": {"technical_debt": 0.7, "requirement_stability": 0.4, "innovation_required": 0.8}
        }

        # Project type characteristics
        type_characteristics = {
            "web_application": {"frontend_focus": 0.6, "backend_focus": 0.7, "database_focus": 0.5},
            "api_service": {"frontend_focus": 0.1, "backend_focus": 0.9, "database_focus": 0.8},
            "mobile_application": {"frontend_focus": 0.8, "backend_focus": 0.5, "database_focus": 0.4},
            "data_science": {"frontend_focus": 0.3, "backend_focus": 0.6, "database_focus": 0.9},
            "devops_tool": {"frontend_focus": 0.2, "backend_focus": 0.8, "database_focus": 0.3}
        }

        factors = complexity_factors.get(complexity, complexity_factors["medium"])
        characteristics = type_characteristics.get(project_type, type_characteristics["web_application"])

        return {
            "project_type": project_type,
            "complexity": complexity,
            "duration_weeks": duration_weeks,
            "complexity_factors": factors,
            "type_characteristics": characteristics,
            "estimated_effort": self._calculate_estimated_effort(duration_weeks, factors),
            "risk_factors": self._identify_risk_factors(factors, characteristics)
        }

    def _calculate_estimated_effort(self, duration_weeks: int, factors: Dict[str, float]) -> float:
        """Calculate estimated project effort."""
        base_effort = duration_weeks * 40  # 40 hours per week
        complexity_multiplier = 1 + factors["technical_debt"] + (1 - factors["requirement_stability"])
        return base_effort * complexity_multiplier

    def _identify_risk_factors(self, factors: Dict[str, float], characteristics: Dict[str, Any]) -> List[str]:
        """Identify project risk factors."""
        risks = []

        if factors["technical_debt"] > 0.6:
            risks.append("high_technical_debt")
        if factors["requirement_stability"] < 0.5:
            risks.append("unstable_requirements")
        if factors["innovation_required"] > 0.7:
            risks.append("high_innovation_requirement")
        if characteristics["frontend_focus"] > 0.7:
            risks.append("frontend_complexity")
        if characteristics["database_focus"] > 0.8:
            risks.append("data_complexity")

        return risks

    def _build_timeline_awareness(self) -> Dict[str, Any]:
        """Build timeline awareness for content generation."""
        phases = self.timeline.get("phases", [])
        current_date = datetime.now()

        # Calculate timeline metrics
        total_duration = sum(phase.get("duration_days", 7) for phase in phases)
        elapsed_phases = 0
        current_phase = None

        for i, phase in enumerate(phases):
            phase_start = phase.get("start_date")
            phase_end = phase.get("end_date")

            if isinstance(phase_start, str):
                phase_start = datetime.fromisoformat(phase_start)
            if isinstance(phase_end, str):
                phase_end = datetime.fromisoformat(phase_end)

            if phase_start and phase_end:
                if current_date >= phase_start and current_date <= phase_end:
                    current_phase = i
                elif current_date > phase_end:
                    elapsed_phases += 1

        progress_percentage = (elapsed_phases / max(1, len(phases))) * 100
        time_pressure = 1.0 if current_date > phases[-1].get("end_date") else 0.5

        return {
            "total_phases": len(phases),
            "current_phase_index": current_phase,
            "elapsed_phases": elapsed_phases,
            "progress_percentage": progress_percentage,
            "time_pressure": time_pressure,
            "phase_context": phases[current_phase] if current_phase is not None else {},
            "milestones": self._extract_milestones(phases)
        }

    def _extract_milestones(self, phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract important milestones from timeline."""
        milestones = []

        for i, phase in enumerate(phases):
            if phase.get("name", "").lower() in ["planning", "design", "development", "testing", "deployment"]:
                milestones.append({
                    "phase": phase["name"],
                    "phase_index": i,
                    "due_date": phase.get("end_date"),
                    "importance": "critical" if i in [0, len(phases)-1] else "normal"
                })

        return milestones


class ContextAwareDocumentGenerator:
    """Advanced document generator with full project context awareness."""

    def __init__(self):
        """Initialize context-aware document generator."""
        self.logger = get_simulation_logger()
        self.cache = get_simulation_cache()
        self.validator = get_simulation_validator()
        self.mock_data_client = get_ecosystem_client("mock_data_generator")
        self.llm_client = get_ecosystem_client("llm_gateway")

        # Document templates with context awareness
        self.templates = self._load_document_templates()

    def _load_document_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load document templates with context awareness."""
        return {
            "project_requirements": {
                "structure": ["introduction", "objectives", "scope", "constraints", "acceptance_criteria"],
                "context_fields": ["team_expertise", "timeline_constraints", "technical_constraints"],
                "personality_influence": {"strategic": 0.8, "detail_oriented": 0.9}
            },
            "architecture_diagram": {
                "structure": ["overview", "components", "data_flow", "deployment"],
                "context_fields": ["team_roles", "project_complexity", "technical_stack"],
                "personality_influence": {"strategic": 0.9, "analytical": 0.8}
            },
            "user_story": {
                "structure": ["role", "goal", "benefit", "acceptance_criteria"],
                "context_fields": ["user_persona", "business_value", "team_collaboration"],
                "personality_influence": {"creative": 0.7, "collaborative": 0.8}
            },
            "technical_design": {
                "structure": ["problem_statement", "proposed_solution", "implementation_details", "risks"],
                "context_fields": ["technical_complexity", "team_expertise", "project_constraints"],
                "personality_influence": {"analytical": 0.9, "methodical": 0.8}
            }
        }

    async def generate_context_aware_document(self,
                                            document_type: str,
                                            project_config: Dict[str, Any],
                                            team_members: List[Dict[str, Any]],
                                            timeline: Dict[str, Any],
                                            **kwargs) -> Dict[str, Any]:
        """Generate document with full project context awareness."""
        try:
            # Build content context
            context = ContentContext(project_config, team_members, timeline, kwargs.get("phase_context"))

            # Generate document using context
            document = await self._generate_with_context(document_type, context, **kwargs)

            # Validate generated content
            validation_result = self.validator.validate_simulation_data("project_config", project_config)
            if not validation_result.is_valid:
                self.logger.warning("Project config validation failed", errors=validation_result.errors)

            return document

        except Exception as e:
            self.logger.error("Context-aware document generation failed",
                            document_type=document_type, error=str(e))
            raise

    async def _generate_with_context(self,
                                   document_type: str,
                                   context: ContentContext,
                                   **kwargs) -> Dict[str, Any]:
        """Generate document using built context."""
        template = self.templates.get(document_type, self._get_default_template())

        # Generate content sections
        content_sections = {}
        for section in template["structure"]:
            content_sections[section] = await self._generate_section_content(
                section, template, context, **kwargs
            )

        # Apply personality and team influence
        influenced_content = self._apply_team_influence(content_sections, context, template)

        # Add metadata and relationships
        metadata = self._build_document_metadata(document_type, context)
        relationships = self._build_document_relationships(document_type, context)

        return {
            "document_type": document_type,
            "title": self._generate_document_title(document_type, context),
            "content": influenced_content,
            "metadata": metadata,
            "relationships": relationships,
            "context_awareness": {
                "team_influence_applied": True,
                "timeline_awareness": True,
                "project_intelligence_used": True,
                "personality_traits_considered": len(context.team_profiles)
            },
            "generated_at": datetime.now(),
            "quality_score": self._calculate_content_quality(influenced_content, context)
        }

    async def _generate_section_content(self,
                                      section: str,
                                      template: Dict[str, Any],
                                      context: ContentContext,
                                      **kwargs) -> str:
        """Generate content for a specific section."""
        # Use LLM to generate context-aware content
        prompt = self._build_section_prompt(section, template, context)

        try:
            response = await self.llm_client.generate_content(
                prompt=prompt,
                model="gpt-4",
                temperature=0.7,
                max_tokens=500
            )

            content = response.get("content", "")
            return self._enhance_with_context(content, section, context)

        except Exception as e:
            self.logger.warning("LLM content generation failed, using fallback", section=section, error=str(e))
            return self._generate_fallback_content(section, context)

    def _build_section_prompt(self,
                            section: str,
                            template: Dict[str, Any],
                            context: ContentContext) -> str:
        """Build prompt for section content generation."""
        team_context = self._build_team_context(context)
        project_context = self._build_project_context(context)
        timeline_context = self._build_timeline_context(context)

        return f"""Generate {section} content for a {context.project_config.get('type', 'software')} project.

Team Context: {team_context}
Project Context: {project_context}
Timeline Context: {timeline_context}

Focus on being specific, actionable, and reflecting the team dynamics and project constraints.
Write in a professional tone that matches the team communication style.
"""

    def _build_team_context(self, context: ContentContext) -> str:
        """Build team context string for prompts."""
        team_size = context.team_dynamics["team_size"]
        dominant_style = context.team_dynamics["collaboration_patterns"]["dominant_style"]

        roles = list(context.team_dynamics["role_distribution"].keys())[:3]  # Top 3 roles

        return f"Team of {team_size} members with {dominant_style} collaboration style. Key roles: {', '.join(roles)}."

    def _build_project_context(self, context: ContentContext) -> str:
        """Build project context string for prompts."""
        project_type = context.project_intelligence["project_type"]
        complexity = context.project_intelligence["complexity"]
        duration = context.project_intelligence["duration_weeks"]

        return f"{complexity} complexity {project_type} project planned for {duration} weeks."

    def _build_timeline_context(self, context: ContentContext) -> str:
        """Build timeline context string for prompts."""
        progress = context.timeline_awareness["progress_percentage"]
        current_phase = context.timeline_awareness.get("current_phase_index")

        if current_phase is not None:
            phase_name = context.timeline["phases"][current_phase].get("name", "current phase")
            return f"Project is {progress:.1f}% complete, currently in {phase_name} phase."
        else:
            return f"Project is {progress:.1f}% complete."

    def _enhance_with_context(self, content: str, section: str, context: ContentContext) -> str:
        """Enhance generated content with additional context."""
        # Add team-specific references
        if "team" in section.lower():
            team_mentions = self._generate_team_mentions(context)
            content += f"\n\nTeam involvement: {team_mentions}"

        # Add timeline awareness
        if "timeline" in section.lower() or "schedule" in section.lower():
            timeline_notes = self._generate_timeline_notes(context)
            content += f"\n\nTimeline considerations: {timeline_notes}"

        return content

    def _generate_team_mentions(self, context: ContentContext) -> str:
        """Generate team member mentions for content."""
        key_members = []
        for profile in list(context.team_profiles.values())[:3]:  # Top 3 members
            if profile["influence_score"] > 0.7:
                key_members.append(profile["name"])

        if key_members:
            return f"Key team members: {', '.join(key_members)}"
        return "Cross-functional team collaboration"

    def _generate_timeline_notes(self, context: ContentContext) -> str:
        """Generate timeline-aware notes."""
        progress = context.timeline_awareness["progress_percentage"]
        time_pressure = context.timeline_awareness["time_pressure"]

        if time_pressure > 0.7:
            return f"Time-sensitive delivery with {progress:.1f}% completion."
        else:
            return f"Standard timeline with {progress:.1f}% completion."

    def _apply_team_influence(self,
                            content_sections: Dict[str, str],
                            context: ContentContext,
                            template: Dict[str, Any]) -> Dict[str, str]:
        """Apply team personality and dynamics influence to content."""
        influenced_content = {}

        for section, content in content_sections.items():
            # Apply personality influence
            personality_weights = template.get("personality_influence", {})
            dominant_personality = self._find_dominant_personality(context, personality_weights)

            # Adjust content based on personality
            adjusted_content = self._adjust_content_for_personality(content, dominant_personality, section)
            influenced_content[section] = adjusted_content

        return influenced_content

    def _find_dominant_personality(self,
                                 context: ContentContext,
                                 personality_weights: Dict[str, float]) -> Optional[str]:
        """Find dominant personality for content generation."""
        if not personality_weights:
            return None

        # Find team member with highest weighted influence
        best_match = None
        best_score = 0

        for profile in context.team_profiles.values():
            personality = profile["personality_trait"].value
            influence = profile["influence_score"]

            weight = personality_weights.get(personality, 0.5)
            score = influence * weight

            if score > best_score:
                best_score = score
                best_match = personality

        return best_match

    def _adjust_content_for_personality(self,
                                      content: str,
                                      personality: Optional[str],
                                      section: str) -> str:
        """Adjust content based on personality traits."""
        if not personality:
            return content

        adjustments = {
            "strategic": lambda c: f"Strategic Overview:\n{c}",
            "detail_oriented": lambda c: self._add_details(c),
            "creative": lambda c: self._add_creativity(c),
            "analytical": lambda c: self._add_analysis(c),
            "methodical": lambda c: self._add_structure(c)
        }

        adjust_func = adjustments.get(personality, lambda c: c)
        return adjust_func(content)

    def _add_details(self, content: str) -> str:
        """Add detail-oriented enhancements."""
        return content + "\n\nDetailed specifications and requirements have been documented separately."

    def _add_creativity(self, content: str) -> str:
        """Add creative enhancements."""
        return content + "\n\nThis approach includes innovative solutions and creative problem-solving."

    def _add_analysis(self, content: str) -> str:
        """Add analytical enhancements."""
        return content + "\n\nAnalysis shows optimal resource utilization and risk mitigation."

    def _add_structure(self, content: str) -> str:
        """Add methodical structure."""
        return content + "\n\nImplementation follows established methodologies and best practices."

    def _build_document_metadata(self, document_type: str, context: ContentContext) -> Dict[str, Any]:
        """Build comprehensive document metadata."""
        return {
            "document_type": document_type,
            "project_id": context.project_config.get("id"),
            "project_type": context.project_config.get("type"),
            "complexity": context.project_config.get("complexity"),
            "team_size": len(context.team_members),
            "generation_context": {
                "team_influence_applied": True,
                "timeline_aware": True,
                "personality_considered": True,
                "phase_context": context.phase_context
            },
            "quality_metrics": {
                "context_awareness_score": 0.9,
                "team_alignment_score": 0.85,
                "timeline_relevance_score": 0.95
            },
            "generated_at": datetime.now(),
            "version": "1.0"
        }

    def _build_document_relationships(self, document_type: str, context: ContentContext) -> Dict[str, Any]:
        """Build document relationships and cross-references."""
        relationships = {
            "parent_documents": [],
            "child_documents": [],
            "related_documents": [],
            "dependencies": []
        }

        # Define relationships based on document type
        if document_type == "project_requirements":
            relationships["child_documents"] = ["user_story", "technical_design"]
            relationships["related_documents"] = ["architecture_diagram"]

        elif document_type == "architecture_diagram":
            relationships["parent_documents"] = ["project_requirements"]
            relationships["child_documents"] = ["technical_design", "deployment_guide"]

        elif document_type == "user_story":
            relationships["parent_documents"] = ["project_requirements"]
            relationships["related_documents"] = ["technical_design", "code_review_comments"]

        elif document_type == "technical_design":
            relationships["parent_documents"] = ["project_requirements", "architecture_diagram"]
            relationships["child_documents"] = ["test_scenarios", "deployment_guide"]

        return relationships

    def _calculate_content_quality(self, content: Dict[str, str], context: ContentContext) -> float:
        """Calculate overall content quality score."""
        # Base quality factors
        completeness = len(content) / max(1, len(self.templates.get("project_requirements", {}).get("structure", [])))
        context_relevance = 0.9 if len(context.team_profiles) > 0 else 0.6
        team_alignment = 0.85 if context.team_dynamics["team_size"] > 0 else 0.5

        # Weighted average
        quality_score = (completeness * 0.4 + context_relevance * 0.3 + team_alignment * 0.3)

        return min(1.0, max(0.0, quality_score))

    def _get_default_template(self) -> Dict[str, Any]:
        """Get default document template."""
        return {
            "structure": ["introduction", "content", "conclusion"],
            "context_fields": ["project_type", "team_size"],
            "personality_influence": {"analytical": 0.6}
        }

    def _generate_fallback_content(self, section: str, context: ContentContext) -> str:
        """Generate fallback content when LLM fails."""
        fallbacks = {
            "introduction": f"This document covers the {section} for the {context.project_config.get('name', 'project')}.",
            "objectives": "The main objectives include delivering quality software within the specified timeline.",
            "scope": "The project scope includes all planned features and deliverables.",
            "conclusion": "This concludes the document with final recommendations and next steps."
        }

        return fallbacks.get(section, f"This section covers {section} for the project.")


# Global context-aware generator instance
_context_aware_generator: Optional[ContextAwareDocumentGenerator] = None


def get_context_aware_generator() -> ContextAwareDocumentGenerator:
    """Get the global context-aware document generator instance."""
    global _context_aware_generator
    if _context_aware_generator is None:
        _context_aware_generator = ContextAwareDocumentGenerator()
    return _context_aware_generator


__all__ = [
    'ContentContext',
    'ContextAwareDocumentGenerator',
    'PersonalityTrait',
    'CommunicationStyle',
    'get_context_aware_generator'
]
