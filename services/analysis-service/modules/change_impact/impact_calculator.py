"""Impact Calculator for Change Impact Analysis.

Calculates change impact scores, risk assessments, and provides
recommendations for change management.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ImpactCalculator:
    """Calculates change impact scores and provides recommendations."""

    def __init__(self):
        """Initialize the impact calculator."""
        self.impact_thresholds = self._get_default_impact_thresholds()

    def _get_default_impact_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Get default impact threshold definitions."""
        return {
            "critical": {
                "min_score": 0.8,
                "description": "Critical impact - requires immediate attention",
                "recommendations": [
                    "Schedule change management meeting",
                    "Conduct detailed impact analysis",
                    "Prepare rollback plan",
                    "Notify all stakeholders immediately",
                ],
            },
            "high": {
                "min_score": 0.6,
                "description": "High impact - requires careful planning",
                "recommendations": [
                    "Conduct impact assessment",
                    "Update dependent documentation",
                    "Test changes thoroughly",
                    "Communicate changes to stakeholders",
                ],
            },
            "medium": {
                "min_score": 0.4,
                "description": "Medium impact - monitor and plan",
                "recommendations": [
                    "Review change implications",
                    "Update relevant sections",
                    "Monitor for side effects",
                    "Document change rationale",
                ],
            },
            "low": {
                "min_score": 0.2,
                "description": "Low impact - standard change process",
                "recommendations": [
                    "Follow standard change procedures",
                    "Update version information",
                    "Test basic functionality",
                ],
            },
        }

    def calculate_change_impact(
        self,
        change_data: Dict[str, Any],
        relationships: List[Dict[str, Any]],
        stakeholder_groups: List[str],
    ) -> Dict[str, Any]:
        """Calculate the overall impact of a document change."""
        # Calculate base impact scores
        content_impact = self._calculate_content_impact(change_data)
        relationship_impact = self._calculate_relationship_impact(relationships)
        stakeholder_impact = self._calculate_stakeholder_impact(stakeholder_groups)

        # Combine impact scores
        overall_impact_score = (
            content_impact["score"] * 0.4 + relationship_impact["score"] * 0.4 + stakeholder_impact["score"] * 0.2
        )

        # Determine impact level
        impact_level = self._determine_impact_level(overall_impact_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(impact_level, content_impact, relationship_impact, stakeholder_impact)

        # Calculate risk assessment
        risk_assessment = self._assess_risks(change_data, relationships, overall_impact_score)

        return {
            "overall_impact_score": round(overall_impact_score, 3),
            "impact_level": impact_level,
            "content_impact": content_impact,
            "relationship_impact": relationship_impact,
            "stakeholder_impact": stakeholder_impact,
            "recommendations": recommendations,
            "risk_assessment": risk_assessment,
            "affected_stakeholders": stakeholder_groups,
            "affected_documents": len(relationships),
        }

    def _calculate_content_impact(self, change_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact based on content changes."""
        change_type = change_data.get("change_type", "unknown")
        content_diff = change_data.get("content_diff", {})
        breaking_changes = change_data.get("breaking_changes", [])

        # Base scores by change type
        type_scores = {
            "addition": 0.3,
            "modification": 0.6,
            "deletion": 0.8,
            "restructure": 0.9,
            "breaking": 1.0,
        }

        base_score = type_scores.get(change_type, 0.5)

        # Adjust for content diff size
        lines_changed = content_diff.get("lines_changed", 0)
        size_factor = min(1.0, lines_changed / 100)  # Cap at 100 lines

        # Adjust for breaking changes
        breaking_factor = min(1.0, len(breaking_changes) * 0.2)

        final_score = base_score * (1 + size_factor) * (1 + breaking_factor)
        final_score = min(1.0, final_score)

        return {
            "score": round(final_score, 3),
            "change_type": change_type,
            "lines_changed": lines_changed,
            "breaking_changes": len(breaking_changes),
            "factors": {
                "base_type_score": base_score,
                "size_factor": size_factor,
                "breaking_factor": breaking_factor,
            },
        }

    def _calculate_relationship_impact(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate impact based on document relationships."""
        if not relationships:
            return {
                "score": 0.0,
                "total_relationships": 0,
                "high_impact_relationships": 0,
                "relationship_types": [],
            }

        total_weight = sum(rel.get("impact_weight", 0.5) for rel in relationships)
        avg_weight = total_weight / len(relationships)

        # Count high-impact relationships
        high_impact_count = sum(1 for rel in relationships if rel.get("impact_weight", 0) > 0.7)

        # Relationship type distribution
        relationship_types = {}
        for rel in relationships:
            rel_type = rel.get("relationship_type", "unknown")
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

        # Calculate score based on relationship strength and count
        relationship_factor = min(1.0, len(relationships) / 10)  # Cap at 10 relationships
        strength_factor = avg_weight

        score = (relationship_factor * 0.6) + (strength_factor * 0.4)

        return {
            "score": round(score, 3),
            "total_relationships": len(relationships),
            "high_impact_relationships": high_impact_count,
            "relationship_types": relationship_types,
            "average_weight": round(avg_weight, 3),
        }

    def _calculate_stakeholder_impact(self, stakeholder_groups: List[str]) -> Dict[str, Any]:
        """Calculate impact based on affected stakeholder groups."""
        if not stakeholder_groups:
            return {
                "score": 0.0,
                "stakeholder_count": 0,
                "critical_stakeholders": [],
            }

        # Define stakeholder impact weights
        stakeholder_weights = {
            "executives": 1.0,
            "developers": 0.8,
            "architects": 0.9,
            "business_analysts": 0.7,
            "product_managers": 0.8,
            "end_users": 0.6,
            "support": 0.5,
            "training": 0.4,
            "legal": 1.0,
            "compliance": 0.9,
            "auditors": 0.8,
            "devops": 0.7,
            "system_administrators": 0.6,
        }

        total_weight = 0
        critical_stakeholders = []

        for stakeholder in stakeholder_groups:
            weight = stakeholder_weights.get(stakeholder, 0.5)
            total_weight += weight
            if weight >= 0.8:
                critical_stakeholders.append(stakeholder)

        avg_weight = total_weight / len(stakeholder_groups) if stakeholder_groups else 0

        # Calculate score based on stakeholder count and criticality
        count_factor = min(1.0, len(stakeholder_groups) / 5)  # Cap at 5 stakeholders
        criticality_factor = avg_weight

        score = (count_factor * 0.4) + (criticality_factor * 0.6)

        return {
            "score": round(score, 3),
            "stakeholder_count": len(stakeholder_groups),
            "critical_stakeholders": critical_stakeholders,
            "average_weight": round(avg_weight, 3),
        }

    def _determine_impact_level(self, impact_score: float) -> str:
        """Determine the impact level based on the score."""
        for level, config in self.impact_thresholds.items():
            if impact_score >= config["min_score"]:
                return level
        return "low"

    def _generate_recommendations(
        self,
        impact_level: str,
        content_impact: Dict[str, Any],
        relationship_impact: Dict[str, Any],
        stakeholder_impact: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []

        # Add level-specific recommendations
        level_config = self.impact_thresholds.get(impact_level, {})
        recommendations.extend(level_config.get("recommendations", []))

        # Add specific recommendations based on impact factors
        if content_impact["score"] > 0.7:
            recommendations.append("Content changes are significant - consider phased rollout")

        if relationship_impact["total_relationships"] > 5:
            recommendations.append("Many documents are affected - create comprehensive test plan")

        if stakeholder_impact["stakeholder_count"] > 3:
            recommendations.append("Multiple stakeholder groups affected - schedule stakeholder meeting")

        if relationship_impact.get("high_impact_relationships", 0) > 0:
            recommendations.append("High-impact relationships detected - conduct detailed dependency analysis")

        return list(set(recommendations))  # Remove duplicates

    def _assess_risks(
        self,
        change_data: Dict[str, Any],
        relationships: List[Dict[str, Any]],
        overall_impact_score: float,
    ) -> Dict[str, Any]:
        """Assess risks associated with the change."""
        risk_factors = []

        # Content-based risks
        if change_data.get("breaking_changes"):
            risk_factors.append(
                {
                    "type": "breaking_changes",
                    "severity": "high",
                    "description": f"{len(change_data['breaking_changes'])} breaking changes detected",
                }
            )

        # Relationship-based risks
        high_impact_rels = [rel for rel in relationships if rel.get("impact_weight", 0) > 0.8]
        if high_impact_rels:
            risk_factors.append(
                {
                    "type": "high_impact_relationships",
                    "severity": "high",
                    "description": f"{len(high_impact_rels)} high-impact relationships",
                }
            )

        # Stakeholder-based risks
        if overall_impact_score > 0.8:
            risk_factors.append(
                {
                    "type": "broad_impact",
                    "severity": "critical",
                    "description": "Change has broad impact across the organization",
                }
            )

        # Calculate overall risk level
        if any(r["severity"] == "critical" for r in risk_factors):
            risk_level = "critical"
        elif any(r["severity"] == "high" for r in risk_factors):
            risk_level = "high"
        elif risk_factors:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "mitigation_required": risk_level in ["high", "critical"],
        }
