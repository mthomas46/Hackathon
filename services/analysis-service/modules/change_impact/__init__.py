"""Change Impact Analysis Components.

This package contains the refactored components for change impact analysis:
- FeatureExtractor: Handles document feature extraction
- RelationshipAnalyzer: Manages relationship analysis
- ImpactCalculator: Calculates change impact scores
"""

from .feature_extractor import FeatureExtractor
from .impact_calculator import ImpactCalculator
from .relationship_analyzer import RelationshipAnalyzer

__all__ = [
    "FeatureExtractor",
    "RelationshipAnalyzer",
    "ImpactCalculator",
]
