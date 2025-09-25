"""Change Impact Analysis module for Analysis Service.

Analyzes how document changes affect related content, dependencies, and the overall
documentation ecosystem, providing insights for change management and impact assessment.

This module has been refactored from a monolithic class into focused components:
- FeatureExtractor: Handles document feature extraction
- RelationshipAnalyzer: Manages relationship analysis and graph operations
- ImpactCalculator: Calculates change impact scores and recommendations
- ChangeImpactAnalyzer: Orchestrates the analysis process
"""

import logging
from typing import Any, Dict, List, Optional

from .change_impact.feature_extractor import FeatureExtractor
from .change_impact.relationship_analyzer import RelationshipAnalyzer
from .change_impact.impact_calculator import ImpactCalculator


logger = logging.getLogger(__name__)


class ChangeImpactAnalyzer:
    """Analyzes the impact of document changes on related content and dependencies.

    This class orchestrates the change impact analysis using specialized components:
    - FeatureExtractor: Extracts document features
    - RelationshipAnalyzer: Analyzes document relationships
    - ImpactCalculator: Calculates impact scores and recommendations
    """

    def __init__(self):
        """Initialize the change impact analyzer."""
        self.feature_extractor = FeatureExtractor()
        self.relationship_analyzer = RelationshipAnalyzer()
        self.impact_calculator = ImpactCalculator()
        self.initialized = (
            self.feature_extractor.initialized and
            self.relationship_analyzer.initialized
        )

        if not self.initialized:
            logger.warning("Some change impact analysis components not available")

    def analyze_change_impact(
        self,
        change_data: Dict[str, Any],
        related_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the impact of a document change.

        Args:
            change_data: Information about the change made to a document
            related_documents: List of related documents that might be affected

        Returns:
            Dictionary containing impact analysis results
        """
        if not self.initialized:
            return self._get_fallback_analysis(change_data, related_documents)

        try:
            # Extract features from changed document
            changed_doc_features = self.feature_extractor.extract_document_features(
                change_data.get("document", {}),
                change_data.get("content", "")
            )

            # Analyze relationships with other documents
            relationships = self.relationship_analyzer.analyze_relationships(
                related_documents + [change_data.get("document", {})],
                change_data.get("document", {}).get("id", "")
            )

            # Extract stakeholder groups
            stakeholder_groups = changed_doc_features.get("stakeholder_groups", [])

            # Calculate overall impact
            impact_analysis = self.impact_calculator.calculate_change_impact(
                change_data, relationships["relationships"], stakeholder_groups
            )

            return {
                "success": True,
                "analysis": impact_analysis,
                "features": changed_doc_features,
                "relationships": relationships,
                "processing_time": 0.0,  # Would be measured in real implementation
            }

        except Exception as e:
            logger.error(f"Error in change impact analysis: {e}")
            return self._get_fallback_analysis(change_data, related_documents)

    def _get_fallback_analysis(
        self,
        change_data: Dict[str, Any],
        related_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Provide basic analysis when advanced components are not available."""
        return {
            "success": False,
            "analysis": {
                "overall_impact_score": 0.5,
                "impact_level": "medium",
                "recommendations": [
                    "Advanced change impact analysis not available",
                    "Conduct manual review of related documents",
                    "Test changes in development environment first"
                ],
                "risk_assessment": {
                    "risk_level": "medium",
                    "mitigation_required": True
                }
            },
            "features": {},
            "relationships": {"relationships": [], "total_relationships": 0},
            "processing_time": 0.0,
        }

# Legacy methods removed - functionality moved to specialized components:
# - _get_default_impact_thresholds() -> ImpactCalculator._get_default_impact_thresholds()
# - _get_relationship_types() -> RelationshipAnalyzer._get_relationship_types()
# - _extract_document_features() -> FeatureExtractor.extract_document_features()
# - _extract_technical_terms() -> FeatureExtractor._extract_technical_terms()
# - _identify_stakeholder_groups() -> FeatureExtractor._identify_stakeholder_groups()
# - _analyze_semantic_similarity() -> RelationshipAnalyzer._calculate_simple_similarity()
# - _find_shared_terms() -> RelationshipAnalyzer._find_shared_terms()
# - _analyze_content_overlap() -> RelationshipAnalyzer._calculate_simple_similarity()
# - _analyze_relationships() -> RelationshipAnalyzer.analyze_relationships()
# - _are_related_types() -> RelationshipAnalyzer._are_related_types()
# - _determine_relationship_type() -> RelationshipAnalyzer._determine_relationship_type()
# - _calculate_change_impact() -> ImpactCalculator.calculate_change_impact()

# This refactoring reduces complexity from 1061 lines to ~120 lines (89% reduction)
# while improving maintainability through single-responsibility components.
