"""Feature Extractor for Change Impact Analysis.

Handles document feature extraction including technical terms, stakeholder groups,
and semantic features.
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional

try:
    import warnings
    from difflib import SequenceMatcher

    warnings.filterwarnings("ignore")
    FEATURE_EXTRACTION_AVAILABLE = True
except ImportError:
    FEATURE_EXTRACTION_AVAILABLE = False
    SequenceMatcher = None


logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extracts features from documents for change impact analysis."""

    def __init__(self):
        """Initialize the feature extractor."""
        self.initialized = FEATURE_EXTRACTION_AVAILABLE
        if not self.initialized:
            logger.warning("Feature extraction dependencies not available")

    def extract_document_features(
        self, document_data: Dict[str, Any], content: str
    ) -> Dict[str, Any]:
        """Extract features from a document."""
        if not self.initialized:
            return self._get_fallback_features(document_data, content)

        features = {
            "technical_terms": self._extract_technical_terms(content),
            "stakeholder_groups": self._identify_stakeholder_groups(document_data),
            "content_length": len(content),
            "code_blocks": len(re.findall(r"```[\s\S]*?```", content)),
            "headings": len(re.findall(r"^#{1,6}\s+", content, re.MULTILINE)),
            "links": len(re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)),
        }

        return features

    def _extract_technical_terms(self, content: str) -> List[str]:
        """Extract technical terms from document content."""
        if not self.initialized:
            return []

        # Common technical patterns
        patterns = [
            r'\b[A-Z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b',  # CamelCase
            r'\b[A-Z]{2,}\b',  # UPPERCASE acronyms
            r'`[^`]+`',  # Code snippets
            r'\b\d+\.\d+\.\d+\b',  # Version numbers
            r'\bAPI\b|\bREST\b|\bHTTP\b|\bJSON\b|\bXML\b',  # Tech terms
        ]

        technical_terms = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            technical_terms.extend(matches)

        # Remove duplicates and filter
        unique_terms = list(set(technical_terms))
        return [term for term in unique_terms if len(term) > 2][:50]  # Limit to 50 terms

    def _identify_stakeholder_groups(self, document_data: Dict[str, Any]) -> List[str]:
        """Identify stakeholder groups affected by the document."""
        stakeholders = []

        # Extract from document metadata
        doc_type = document_data.get("type", "").lower()
        audience = document_data.get("audience", "").lower()
        department = document_data.get("department", "").lower()

        # Map document types to stakeholder groups
        type_mapping = {
            "api": ["developers", "architects", "testers"],
            "user_guide": ["end_users", "support", "training"],
            "technical": ["developers", "architects", "devops"],
            "business": ["business_analysts", "product_managers", "executives"],
            "compliance": ["legal", "compliance", "auditors"],
        }

        # Add stakeholders based on document type
        if doc_type in type_mapping:
            stakeholders.extend(type_mapping[doc_type])

        # Add stakeholders based on audience
        if "developer" in audience:
            stakeholders.extend(["developers", "architects"])
        if "business" in audience or "executive" in audience:
            stakeholders.extend(["business_analysts", "executives"])
        if "operation" in audience or "devops" in audience:
            stakeholders.extend(["devops", "system_administrators"])

        # Add department-specific stakeholders
        if department:
            stakeholders.append(f"{department}_team")

        return list(set(stakeholders))  # Remove duplicates

    def _get_fallback_features(self, document_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Get basic features when advanced extraction is not available."""
        return {
            "technical_terms": [],
            "stakeholder_groups": ["general"],
            "content_length": len(content),
            "code_blocks": 0,
            "headings": 0,
            "links": 0,
        }
