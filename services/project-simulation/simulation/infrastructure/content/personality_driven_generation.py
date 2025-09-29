"""Personality-Driven Content Generation - Team Member Personality Integration.

This module implements sophisticated personality-driven content generation that creates
realistic team interactions, communication styles, and content variations based on
individual team member personalities and their influence on project documentation.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
import random
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.content.context_aware_generation import (
    ContentContext, ContextAwareDocumentGenerator,
    PersonalityTrait, CommunicationStyle
)


class TeamRole(Enum):
    """Team roles with personality correlations."""
    ARCHITECT = "architect"
    SENIOR_DEVELOPER = "senior_developer"
    DEVELOPER = "developer"
    QA_ENGINEER = "qa_engineer"
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"
    UX_DESIGNER = "ux_designer"
    DEVOPS_ENGINEER = "devops_engineer"
    BUSINESS_ANALYST = "business_analyst"


class PersonalityProfile:
    """Comprehensive personality profile for team members."""

    def __init__(self, member_id: str, member_data: Dict[str, Any]):
        """Initialize personality profile."""
        self.member_id = member_id
        self.name = member_data.get("name", "Unknown")
        self.role = member_data.get("role", "developer")
        self.experience_years = member_data.get("experience_years", 2)

        # Core personality traits
        self.primary_trait = self._determine_primary_trait()
        self.secondary_trait = self._determine_secondary_trait()

        # Communication characteristics
        self.communication_style = self._determine_communication_style()
        self.writing_tone = self._determine_writing_tone()
        self.decision_making_style = self._determine_decision_making_style()

        # Work patterns
        self.work_preference = self._determine_work_preference()
        self.collaboration_style = self._determine_collaboration_style()
        self.problem_solving_approach = self._determine_problem_solving_approach()

        # Influence metrics
        self.influence_score = self._calculate_influence_score()
        self.expertise_score = self._calculate_expertise_score()
        self.communication_effectiveness = self._calculate_communication_effectiveness()

        # Content generation preferences
        self.content_preferences = self._build_content_preferences()

    def _determine_primary_trait(self) -> PersonalityTrait:
        """Determine primary personality trait based on role and experience."""
        role_trait_map = {
            "architect": PersonalityTrait.STRATEGIC,
            "senior_developer": PersonalityTrait.METHODICAL,
            "developer": PersonalityTrait.ANALYTICAL,
            "qa_engineer": PersonalityTrait.DETAIL_ORIENTED,
            "product_owner": PersonalityTrait.COLLABORATIVE,
            "scrum_master": PersonalityTrait.COLLABORATIVE,
            "ux_designer": PersonalityTrait.CREATIVE,
            "devops_engineer": PersonalityTrait.PRAGMATIC,
            "business_analyst": PersonalityTrait.ANALYTICAL
        }

        # Experience adjustment
        if self.experience_years > 8:
            return PersonalityTrait.STRATEGIC
        elif self.experience_years < 3:
            return PersonalityTrait.INNOVATIVE

        return role_trait_map.get(self.role.lower(), PersonalityTrait.ANALYTICAL)

    def _determine_secondary_trait(self) -> PersonalityTrait:
        """Determine secondary personality trait."""
        primary = self.primary_trait

        # Define complementary traits
        complementary_map = {
            PersonalityTrait.STRATEGIC: PersonalityTrait.ANALYTICAL,
            PersonalityTrait.METHODICAL: PersonalityTrait.DETAIL_ORIENTED,
            PersonalityTrait.ANALYTICAL: PersonalityTrait.METHODICAL,
            PersonalityTrait.DETAIL_ORIENTED: PersonalityTrait.METHODICAL,
            PersonalityTrait.COLLABORATIVE: PersonalityTrait.PRAGMATIC,
            PersonalityTrait.CREATIVE: PersonalityTrait.INNOVATIVE,
            PersonalityTrait.PRAGMATIC: PersonalityTrait.COLLABORATIVE,
            PersonalityTrait.INNOVATIVE: PersonalityTrait.CREATIVE
        }

        return complementary_map.get(primary, PersonalityTrait.PRAGMATIC)

    def _determine_communication_style(self) -> CommunicationStyle:
        """Determine communication style."""
        if self.primary_trait == PersonalityTrait.STRATEGIC:
            return CommunicationStyle.FORMAL
        elif self.primary_trait == PersonalityTrait.CREATIVE:
            return CommunicationStyle.CASUAL
        elif self.primary_trait == PersonalityTrait.ANALYTICAL:
            return CommunicationStyle.TECHNICAL
        elif self.primary_trait == PersonalityTrait.DETAIL_ORIENTED:
            return CommunicationStyle.DETAILED
        else:
            return CommunicationStyle.BUSINESS

    def _determine_writing_tone(self) -> str:
        """Determine writing tone preference."""
        tone_map = {
            PersonalityTrait.STRATEGIC: "authoritative",
            PersonalityTrait.METHODICAL: "precise",
            PersonalityTrait.ANALYTICAL: "logical",
            PersonalityTrait.DETAIL_ORIENTED: "comprehensive",
            PersonalityTrait.COLLABORATIVE: "inclusive",
            PersonalityTrait.CREATIVE: "engaging",
            PersonalityTrait.PRAGMATIC: "direct",
            PersonalityTrait.INNOVATIVE: "forward-thinking"
        }

        return tone_map.get(self.primary_trait, "professional")

    def _determine_decision_making_style(self) -> str:
        """Determine decision making style."""
        if self.primary_trait == PersonalityTrait.STRATEGIC:
            return "vision-driven"
        elif self.primary_trait == PersonalityTrait.ANALYTICAL:
            return "data-driven"
        elif self.primary_trait == PersonalityTrait.COLLABORATIVE:
            return "consensus-driven"
        elif self.primary_trait == PersonalityTrait.PRAGMATIC:
            return "practical"
        else:
            return "balanced"

    def _determine_work_preference(self) -> str:
        """Determine work preference."""
        if self.primary_trait == PersonalityTrait.STRATEGIC:
            return "planning"
        elif self.primary_trait == PersonalityTrait.CREATIVE:
            return "design"
        elif self.primary_trait == PersonalityTrait.ANALYTICAL:
            return "analysis"
        elif self.primary_trait == PersonalityTrait.DETAIL_ORIENTED:
            return "validation"
        else:
            return "execution"

    def _determine_collaboration_style(self) -> str:
        """Determine collaboration style."""
        if self.primary_trait == PersonalityTrait.COLLABORATIVE:
            return "team_oriented"
        elif self.primary_trait == PersonalityTrait.INNOVATIVE:
            return "idea_generator"
        elif self.primary_trait == PersonalityTrait.STRATEGIC:
            return "mentor"
        else:
            return "cooperative"

    def _determine_problem_solving_approach(self) -> str:
        """Determine problem solving approach."""
        if self.primary_trait == PersonalityTrait.ANALYTICAL:
            return "systematic"
        elif self.primary_trait == PersonalityTrait.CREATIVE:
            return "innovative"
        elif self.primary_trait == PersonalityTrait.PRAGMATIC:
            return "practical"
        elif self.primary_trait == PersonalityTrait.STRATEGIC:
            return "holistic"
        else:
            return "structured"

    def _calculate_influence_score(self) -> float:
        """Calculate influence score."""
        role_weight = {
            "architect": 0.9, "senior_developer": 0.8, "product_owner": 0.8,
            "scrum_master": 0.7, "developer": 0.6, "business_analyst": 0.6,
            "qa_engineer": 0.5, "ux_designer": 0.5, "devops_engineer": 0.5
        }

        base_score = role_weight.get(self.role.lower(), 0.5)
        experience_multiplier = min(1.5, 1.0 + (self.experience_years * 0.05))

        return min(1.0, base_score * experience_multiplier)

    def _calculate_expertise_score(self) -> float:
        """Calculate expertise score."""
        base_expertise = min(1.0, self.experience_years * 0.1)
        role_expertise = {
            "architect": 0.9, "senior_developer": 0.8, "devops_engineer": 0.7,
            "developer": 0.6, "qa_engineer": 0.6, "business_analyst": 0.6,
            "ux_designer": 0.5, "product_owner": 0.5, "scrum_master": 0.4
        }

        role_score = role_expertise.get(self.role.lower(), 0.5)
        return min(1.0, (base_expertise + role_score) / 2)

    def _calculate_communication_effectiveness(self) -> float:
        """Calculate communication effectiveness."""
        style_effectiveness = {
            CommunicationStyle.FORMAL: 0.8,
            CommunicationStyle.TECHNICAL: 0.9,
            CommunicationStyle.BUSINESS: 0.7,
            CommunicationStyle.CASUAL: 0.6,
            CommunicationStyle.CONCISE: 0.8,
            CommunicationStyle.DETAILED: 0.9
        }

        return style_effectiveness.get(self.communication_style, 0.7)

    def _build_content_preferences(self) -> Dict[str, Any]:
        """Build content generation preferences."""
        return {
            "preferred_sections": self._get_preferred_sections(),
            "writing_style": self.writing_tone,
            "detail_level": "high" if self.primary_trait == PersonalityTrait.DETAIL_ORIENTED else "medium",
            "structure_preference": "hierarchical" if self.primary_trait == PersonalityTrait.STRATEGIC else "logical",
            "emphasis_areas": self._get_emphasis_areas()
        }

    def _get_preferred_sections(self) -> List[str]:
        """Get preferred document sections."""
        preferences = {
            PersonalityTrait.STRATEGIC: ["objectives", "architecture", "roadmap"],
            PersonalityTrait.ANALYTICAL: ["requirements", "specifications", "analysis"],
            PersonalityTrait.DETAIL_ORIENTED: ["constraints", "validation", "testing"],
            PersonalityTrait.CREATIVE: ["user_experience", "innovation", "design"],
            PersonalityTrait.METHODICAL: ["process", "implementation", "standards"],
            PersonalityTrait.PRAGMATIC: ["timeline", "resources", "deliverables"],
            PersonalityTrait.COLLABORATIVE: ["team", "communication", "stakeholders"],
            PersonalityTrait.INNOVATIVE: ["future", "technology", "scalability"]
        }

        return preferences.get(self.primary_trait, ["overview", "details", "conclusion"])

    def _get_emphasis_areas(self) -> List[str]:
        """Get areas of emphasis."""
        emphasis = {
            PersonalityTrait.STRATEGIC: ["vision", "architecture", "scalability"],
            PersonalityTrait.ANALYTICAL: ["data", "logic", "optimization"],
            PersonalityTrait.DETAIL_ORIENTED: ["quality", "compliance", "validation"],
            PersonalityTrait.CREATIVE: ["user_experience", "innovation", "design"],
            PersonalityTrait.METHODICAL: ["process", "standards", "efficiency"],
            PersonalityTrait.PRAGMATIC: ["results", "timeline", "resources"],
            PersonalityTrait.COLLABORATIVE: ["team", "communication", "relationships"],
            PersonalityTrait.INNOVATIVE: ["future", "technology", "disruption"]
        }

        return emphasis.get(self.primary_trait, ["balance", "quality", "efficiency"])


class PersonalityDrivenGenerator:
    """Generator that incorporates team member personalities into content."""

    def __init__(self):
        """Initialize personality-driven generator."""
        self.logger = get_simulation_logger()
        self.context_generator = ContextAwareDocumentGenerator()

        # Personality profiles cache
        self.personality_profiles: Dict[str, PersonalityProfile] = {}

        # Team dynamics analyzer
        self.team_dynamics = {}

    def generate_with_personality_influence(self,
                                          document_type: str,
                                          project_config: Dict[str, Any],
                                          team_members: List[Dict[str, Any]],
                                          timeline: Dict[str, Any],
                                          primary_author_id: Optional[str] = None,
                                          **kwargs) -> Dict[str, Any]:
        """Generate content with personality-driven influence."""
        try:
            # Build personality profiles for all team members
            self._build_team_personality_profiles(team_members)

            # Analyze team dynamics
            team_dynamics = self._analyze_team_dynamics()

            # Select primary author or determine most influential
            primary_author = self._select_primary_author(primary_author_id, team_members)

            # Generate base content using context-aware generator
            base_content = self.context_generator.generate_context_aware_document(
                document_type, project_config, team_members, timeline, **kwargs
            )

            # Apply personality influence
            personality_influenced_content = self._apply_personality_influence(
                base_content, primary_author, team_dynamics
            )

            # Add personality metadata
            personality_influenced_content["personality_metadata"] = {
                "primary_author": primary_author.member_id if primary_author else None,
                "influencing_personalities": len(self.personality_profiles),
                "dominant_traits": self._get_dominant_team_traits(),
                "communication_styles": self._get_team_communication_styles(),
                "personality_influence_score": 0.9
            }

            return personality_influenced_content

        except Exception as e:
            self.logger.error("Personality-driven generation failed",
                            document_type=document_type, error=str(e))
            # Fallback to basic generation
            return self.context_generator.generate_context_aware_document(
                document_type, project_config, team_members, timeline, **kwargs
            )

    def _build_team_personality_profiles(self, team_members: List[Dict[str, Any]]):
        """Build personality profiles for all team members."""
        self.personality_profiles = {}

        for member in team_members:
            member_id = member.get("member_id", member.get("id", f"member_{len(self.personality_profiles)}"))
            self.personality_profiles[member_id] = PersonalityProfile(member_id, member)

    def _analyze_team_dynamics(self) -> Dict[str, Any]:
        """Analyze team dynamics based on personality profiles."""
        if not self.personality_profiles:
            return {}

        # Count personality traits
        trait_counts = {}
        for profile in self.personality_profiles.values():
            trait = profile.primary_trait.value
            trait_counts[trait] = trait_counts.get(trait, 0) + 1

        # Count communication styles
        style_counts = {}
        for profile in self.personality_profiles.values():
            style = profile.communication_style.value
            style_counts[style] = style_counts.get(style, 0) + 1

        # Calculate diversity scores
        trait_diversity = len(trait_counts) / max(1, len(self.personality_profiles))
        style_diversity = len(style_counts) / max(1, len(self.personality_profiles))

        # Identify dominant traits
        dominant_trait = max(trait_counts.items(), key=lambda x: x[1])[0] if trait_counts else None
        dominant_style = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else None

        return {
            "trait_distribution": trait_counts,
            "style_distribution": style_counts,
            "dominant_trait": dominant_trait,
            "dominant_style": dominant_style,
            "trait_diversity_score": trait_diversity,
            "style_diversity_score": style_diversity,
            "collaboration_effectiveness": self._calculate_collaboration_effectiveness(trait_counts, style_counts)
        }

    def _calculate_collaboration_effectiveness(self, trait_counts: Dict[str, int], style_counts: Dict[str, int]) -> float:
        """Calculate team collaboration effectiveness based on personality composition."""
        # High effectiveness with balanced traits and communication styles
        trait_balance = len(trait_counts) / 4.0  # Optimal: 4 different traits
        style_balance = len(style_counts) / 3.0  # Optimal: 3 different styles

        # Bonus for having strategic and collaborative traits
        has_strategic = "strategic" in trait_counts
        has_collaborative = "collaborative" in trait_counts

        balance_bonus = 0.2 if (has_strategic and has_collaborative) else 0.0

        effectiveness = min(1.0, (trait_balance + style_balance) / 2 + balance_bonus)
        return max(0.3, effectiveness)  # Minimum effectiveness

    def _select_primary_author(self, primary_author_id: Optional[str], team_members: List[Dict[str, Any]]) -> Optional[PersonalityProfile]:
        """Select primary author for content generation."""
        if primary_author_id and primary_author_id in self.personality_profiles:
            return self.personality_profiles[primary_author_id]

        # Select most influential team member
        if self.personality_profiles:
            return max(self.personality_profiles.values(),
                      key=lambda p: p.influence_score * p.expertise_score)

        return None

    def _apply_personality_influence(self,
                                   content: Dict[str, Any],
                                   primary_author: Optional[PersonalityProfile],
                                   team_dynamics: Dict[str, Any]) -> Dict[str, Any]:
        """Apply personality influence to generated content."""
        if not primary_author:
            return content

        influenced_content = content.copy()

        # Apply primary author influence to content sections
        if "content" in influenced_content:
            for section_name, section_content in influenced_content["content"].items():
                if isinstance(section_content, str):
                    influenced_section = self._apply_section_personality(
                        section_content, section_name, primary_author, team_dynamics
                    )
                    influenced_content["content"][section_name] = influenced_section

        # Apply team influence to overall document
        influenced_content = self._apply_team_influence(influenced_content, team_dynamics)

        return influenced_content

    def _apply_section_personality(self,
                                 content: str,
                                 section_name: str,
                                 author: PersonalityProfile,
                                 team_dynamics: Dict[str, Any]) -> str:
        """Apply personality influence to a specific content section."""
        # Get section-specific personality adjustments
        adjustments = self._get_section_adjustments(section_name, author)

        # Apply writing tone
        content = self._apply_writing_tone(content, author.writing_tone)

        # Apply detail level
        content = self._apply_detail_level(content, author.content_preferences["detail_level"])

        # Apply structure preference
        content = self._apply_structure_preference(content, author.content_preferences["structure_preference"])

        # Add personality-specific phrases and perspectives
        content = self._add_personality_phrases(content, author, section_name)

        # Apply section-specific adjustments
        for adjustment in adjustments:
            content = adjustment(content)

        return content

    def _get_section_adjustments(self, section_name: str, author: PersonalityProfile) -> List[callable]:
        """Get section-specific adjustments based on author personality."""
        adjustments = []

        # Strategic author adjustments
        if author.primary_trait == PersonalityTrait.STRATEGIC:
            if section_name in ["objectives", "conclusion"]:
                adjustments.append(self._add_strategic_emphasis)
            if section_name in ["architecture", "design"]:
                adjustments.append(self._add_visionary_perspective)

        # Analytical author adjustments
        elif author.primary_trait == PersonalityTrait.ANALYTICAL:
            if section_name in ["requirements", "analysis"]:
                adjustments.append(self._add_analytical_depth)
            if section_name in ["constraints", "risks"]:
                adjustments.append(self._add_data_driven_insights)

        # Detail-oriented author adjustments
        elif author.primary_trait == PersonalityTrait.DETAIL_ORIENTED:
            if section_name in ["implementation", "validation"]:
                adjustments.append(self._add_comprehensive_details)
            if section_name in ["testing", "quality"]:
                adjustments.append(self._add_quality_focus)

        # Creative author adjustments
        elif author.primary_trait == PersonalityTrait.CREATIVE:
            if section_name in ["design", "user_experience"]:
                adjustments.append(self._add_innovative_ideas)
            if section_name in ["challenges", "solutions"]:
                adjustments.append(self._add_creative_solutions)

        return adjustments

    def _apply_writing_tone(self, content: str, tone: str) -> str:
        """Apply writing tone to content."""
        tone_modifiers = {
            "authoritative": lambda c: f"Authoritatively: {c}",
            "precise": lambda c: f"Precisely stated: {c}",
            "logical": lambda c: f"Logically following: {c}",
            "comprehensive": lambda c: f"Comprehensively: {c}",
            "inclusive": lambda c: f"Inclusively considering: {c}",
            "engaging": lambda c: f"Engagingly: {c}",
            "direct": lambda c: f"Directly: {c}",
            "forward-thinking": lambda c: f"Forward-thinking: {c}"
        }

        modifier = tone_modifiers.get(tone, lambda c: c)
        return modifier(content)

    def _apply_detail_level(self, content: str, detail_level: str) -> str:
        """Apply detail level to content."""
        if detail_level == "high":
            return content + "\n\nDetailed specifications and comprehensive analysis have been documented separately."
        elif detail_level == "low":
            return content + "\n\nHigh-level overview provided; detailed specifications available upon request."
        else:
            return content

    def _apply_structure_preference(self, content: str, structure_preference: str) -> str:
        """Apply structure preference to content."""
        if structure_preference == "hierarchical":
            return f"Strategic Overview:\n{content}"
        elif structure_preference == "logical":
            return f"Logical Analysis:\n{content}"
        else:
            return content

    def _add_personality_phrases(self, content: str, author: PersonalityProfile, section_name: str) -> str:
        """Add personality-specific phrases to content."""
        phrases = self._get_personality_phrases(author.primary_trait, section_name)

        if phrases:
            selected_phrase = random.choice(phrases)
            return f"{selected_phrase}\n\n{content}"

        return content

    def _get_personality_phrases(self, trait: PersonalityTrait, section_name: str) -> List[str]:
        """Get personality-specific phrases for content."""
        phrase_library = {
            PersonalityTrait.STRATEGIC: {
                "objectives": [
                    "From a strategic perspective, the objectives align with our long-term vision.",
                    "Strategically positioned for maximum impact and scalability."
                ],
                "architecture": [
                    "Architecturally designed to support future growth and technological evolution.",
                    "Strategic foundation established for enterprise-level scalability."
                ]
            },
            PersonalityTrait.ANALYTICAL: {
                "requirements": [
                    "Analytical breakdown reveals the following key requirements.",
                    "Data-driven analysis identifies critical success factors."
                ],
                "constraints": [
                    "Analytical assessment of constraints and dependencies.",
                    "Systematic evaluation of limiting factors and mitigation strategies."
                ]
            },
            PersonalityTrait.DETAIL_ORIENTED: {
                "implementation": [
                    "Detailed implementation specifications ensure quality and consistency.",
                    "Comprehensive documentation supports thorough validation processes."
                ],
                "validation": [
                    "Rigorous validation procedures ensure compliance and quality standards.",
                    "Detailed verification checklist confirms all requirements are met."
                ]
            },
            PersonalityTrait.CREATIVE: {
                "design": [
                    "Innovative design approach brings fresh perspectives to user experience.",
                    "Creative solutions enable breakthrough functionality and engagement."
                ],
                "challenges": [
                    "Creative problem-solving transforms challenges into opportunities.",
                    "Innovative approaches generate novel solutions to complex problems."
                ]
            }
        }

        trait_phrases = phrase_library.get(trait, {})
        return trait_phrases.get(section_name, [])

    def _add_strategic_emphasis(self, content: str) -> str:
        """Add strategic emphasis to content."""
        return content + "\n\nThis approach positions the project for long-term success and competitive advantage."

    def _add_visionary_perspective(self, content: str) -> str:
        """Add visionary perspective to content."""
        return content + "\n\nVisionary architecture anticipates future technological trends and business needs."

    def _add_analytical_depth(self, content: str) -> str:
        """Add analytical depth to content."""
        return content + "\n\nAnalytical framework provides quantitative metrics for decision-making and optimization."

    def _add_data_driven_insights(self, content: str) -> str:
        """Add data-driven insights to content."""
        return content + "\n\nData-driven insights inform risk mitigation strategies and contingency planning."

    def _add_comprehensive_details(self, content: str) -> str:
        """Add comprehensive details to content."""
        return content + "\n\nComprehensive documentation ensures complete understanding and successful implementation."

    def _add_quality_focus(self, content: str) -> str:
        """Add quality focus to content."""
        return content + "\n\nQuality assurance processes guarantee reliability and user satisfaction."

    def _add_innovative_ideas(self, content: str) -> str:
        """Add innovative ideas to content."""
        return content + "\n\nInnovative concepts push boundaries and create unique value propositions."

    def _add_creative_solutions(self, content: str) -> str:
        """Add creative solutions to content."""
        return content + "\n\nCreative problem-solving generates breakthrough solutions and competitive advantages."

    def _apply_team_influence(self, content: Dict[str, Any], team_dynamics: Dict[str, Any]) -> Dict[str, Any]:
        """Apply team-level influence to the overall document."""
        influenced_content = content.copy()

        # Add team consensus indicators
        if team_dynamics.get("dominant_trait") == "collaborative":
            influenced_content["team_consensus"] = "Document reflects team consensus and collaborative decision-making."

        # Add diversity indicators
        diversity_score = team_dynamics.get("trait_diversity_score", 0)
        if diversity_score > 0.7:
            influenced_content["team_diversity"] = "Document benefits from diverse perspectives and comprehensive analysis."

        # Add communication style indicators
        dominant_style = team_dynamics.get("dominant_style")
        if dominant_style == "formal":
            influenced_content["communication_style"] = "Professional and formal communication standards maintained."
        elif dominant_style == "technical":
            influenced_content["communication_style"] = "Technical precision and accuracy emphasized throughout."

        return influenced_content

    def _get_dominant_team_traits(self) -> List[str]:
        """Get dominant personality traits in the team."""
        if not self.personality_profiles:
            return []

        trait_counts = {}
        for profile in self.personality_profiles.values():
            trait = profile.primary_trait.value
            trait_counts[trait] = trait_counts.get(trait, 0) + 1

        # Return traits with count > 1 (to avoid single-person dominance)
        dominant = [trait for trait, count in trait_counts.items() if count > 1]
        return dominant if dominant else list(trait_counts.keys())[:2]

    def _get_team_communication_styles(self) -> List[str]:
        """Get communication styles used in the team."""
        if not self.personality_profiles:
            return []

        style_counts = {}
        for profile in self.personality_profiles.values():
            style = profile.communication_style.value
            style_counts[style] = style_counts.get(style, 0) + 1

        return list(style_counts.keys())[:3]  # Top 3 styles


# Global personality-driven generator instance
_personality_generator: Optional[PersonalityDrivenGenerator] = None


def get_personality_driven_generator() -> PersonalityDrivenGenerator:
    """Get the global personality-driven content generator instance."""
    global _personality_generator
    if _personality_generator is None:
        _personality_generator = PersonalityDrivenGenerator()
    return _personality_generator


def create_team_interaction_content(team_members: List[Dict[str, Any]],
                                  interaction_type: str,
                                  context: Dict[str, Any]) -> Dict[str, Any]:
    """Create realistic team interaction content based on personalities."""
    generator = get_personality_driven_generator()

    # Build personality profiles
    generator._build_team_personality_profiles(team_members)

    # Generate interaction content
    if interaction_type == "meeting":
        return generator._generate_meeting_content(context)
    elif interaction_type == "code_review":
        return generator._generate_code_review_content(context)
    elif interaction_type == "planning_session":
        return generator._generate_planning_content(context)
    else:
        return generator._generate_general_interaction(context)


__all__ = [
    'PersonalityProfile',
    'PersonalityDrivenGenerator',
    'TeamRole',
    'get_personality_driven_generator',
    'create_team_interaction_content'
]
