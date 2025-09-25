"""Relationship Analyzer for Change Impact Analysis.

Manages relationship analysis, graph operations, and dependency mapping
between documents.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

try:
    import warnings

    import networkx as nx
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    warnings.filterwarnings("ignore")
    RELATIONSHIP_ANALYSIS_AVAILABLE = True
except ImportError:
    RELATIONSHIP_ANALYSIS_AVAILABLE = False
    nx = None
    np = None
    cosine_similarity = None
    TfidfVectorizer = None


logger = logging.getLogger(__name__)


class RelationshipAnalyzer:
    """Analyzes relationships between documents and builds dependency graphs."""

    def __init__(self):
        """Initialize the relationship analyzer."""
        self.initialized = RELATIONSHIP_ANALYSIS_AVAILABLE
        self.relationship_types = self._get_relationship_types()
        if not self.initialized:
            logger.warning("Relationship analysis dependencies not available")

    def _get_relationship_types(self) -> Dict[str, Dict[str, Any]]:
        """Get relationship type definitions."""
        return {
            "parent_child": {
                "description": "Hierarchical relationship (parent contains child)",
                "impact_weight": 0.9,
                "propagation_rules": ["direct", "transitive"],
            },
            "reference": {
                "description": "Document references another document",
                "impact_weight": 0.7,
                "propagation_rules": ["direct"],
            },
            "dependency": {
                "description": "Document depends on another for context/completeness",
                "impact_weight": 0.8,
                "propagation_rules": ["direct", "transitive"],
            },
            "similar": {
                "description": "Documents have similar content/themes",
                "impact_weight": 0.5,
                "propagation_rules": ["none"],
            },
            "contradictory": {
                "description": "Documents contain contradictory information",
                "impact_weight": 0.6,
                "propagation_rules": ["direct"],
            },
        }

    def analyze_relationships(
        self, documents: List[Dict[str, Any]], changed_document_id: str
    ) -> Dict[str, Any]:
        """Analyze relationships between documents."""
        if not self.initialized:
            return self._get_fallback_relationships(documents, changed_document_id)

        relationships = []
        relationship_graph = self._build_relationship_graph(documents)

        # Find relationships for the changed document
        for doc in documents:
            if doc["id"] == changed_document_id:
                continue

            relationship = self._determine_relationship_type(
                documents, changed_document_id, doc["id"]
            )

            if relationship:
                relationships.append(
                    {
                        "source_id": changed_document_id,
                        "target_id": doc["id"],
                        "relationship_type": relationship["type"],
                        "confidence": relationship["confidence"],
                        "impact_weight": relationship["impact_weight"],
                        "description": relationship["description"],
                    }
                )

        return {
            "relationships": relationships,
            "relationship_graph": relationship_graph,
            "total_relationships": len(relationships),
            "relationship_types": list(
                set(r["relationship_type"] for r in relationships)
            ),
        }

    def _build_relationship_graph(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build a graph of document relationships."""
        if not self.initialized or not nx:
            return {"nodes": [], "edges": []}

        try:
            G = nx.DiGraph()

            # Add nodes
            for doc in documents:
                G.add_node(doc["id"], **doc)

            # Add edges based on relationships (simplified for this example)
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents):
                    if i != j:
                        # Simple relationship detection based on content overlap
                        similarity = self._calculate_simple_similarity(doc1, doc2)
                        if similarity > 0.3:  # Threshold for relationship
                            G.add_edge(
                                doc1["id"],
                                doc2["id"],
                                weight=similarity,
                                type="similar",
                            )

            return {
                "nodes": list(G.nodes(data=True)),
                "edges": list(G.edges(data=True)),
                "density": nx.density(G),
                "connected_components": nx.number_connected_components(
                    G.to_undirected()
                ),
            }
        except Exception as e:
            logger.error(f"Error building relationship graph: {e}")
            return {"nodes": [], "edges": []}

    def _calculate_simple_similarity(
        self, doc1: Dict[str, Any], doc2: Dict[str, Any]
    ) -> float:
        """Calculate simple similarity between two documents."""
        if not self.initialized:
            return 0.0

        content1 = doc1.get("content", "").lower()
        content2 = doc2.get("content", "").lower()

        # Simple word overlap similarity
        words1 = set(content1.split())
        words2 = set(content2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _determine_relationship_type(
        self, documents: List[Dict[str, Any]], source_id: str, target_id: str
    ) -> Optional[Dict[str, Any]]:
        """Determine the relationship type between two documents."""
        source_doc = next((d for d in documents if d["id"] == source_id), None)
        target_doc = next((d for d in documents if d["id"] == target_id), None)

        if not source_doc or not target_doc:
            return None

        # Calculate various relationship indicators
        content_similarity = self._calculate_simple_similarity(source_doc, target_doc)
        reference_links = self._check_reference_links(source_doc, target_doc)
        shared_terms = self._find_shared_terms(source_doc, target_doc)

        # Determine relationship type based on indicators
        if reference_links:
            return {
                "type": "reference",
                "confidence": 0.8,
                "impact_weight": self.relationship_types["reference"]["impact_weight"],
                "description": f"Document references {target_id}",
            }
        elif content_similarity > 0.7:
            return {
                "type": "dependency",
                "confidence": content_similarity,
                "impact_weight": self.relationship_types["dependency"]["impact_weight"],
                "description": f"High content similarity ({content_similarity:.2f})",
            }
        elif content_similarity > 0.4:
            return {
                "type": "similar",
                "confidence": content_similarity,
                "impact_weight": self.relationship_types["similar"]["impact_weight"],
                "description": f"Moderate content similarity ({content_similarity:.2f})",
            }

        return None

    def _check_reference_links(
        self, source_doc: Dict[str, Any], target_doc: Dict[str, Any]
    ) -> bool:
        """Check if source document references target document."""
        source_content = source_doc.get("content", "").lower()
        target_title = target_doc.get("title", "").lower()
        target_id = target_doc.get("id", "").lower()

        return target_title in source_content or target_id in source_content

    def _find_shared_terms(
        self, doc1: Dict[str, Any], doc2: Dict[str, Any]
    ) -> List[str]:
        """Find shared technical terms between documents."""
        # This is a simplified implementation
        content1 = doc1.get("content", "").lower()
        content2 = doc2.get("content", "").lower()

        # Extract potential technical terms (simplified)
        words1 = set(content1.split())
        words2 = set(content2.split())

        shared = words1.intersection(words2)
        return [word for word in shared if len(word) > 3][
            :10
        ]  # Technical terms likely > 3 chars

    def _get_fallback_relationships(
        self, documents: List[Dict[str, Any]], changed_document_id: str
    ) -> Dict[str, Any]:
        """Get basic relationship analysis when advanced analysis is not available."""
        relationships = []

        # Simple fallback: assume all documents are somewhat related
        for doc in documents:
            if doc["id"] != changed_document_id:
                relationships.append(
                    {
                        "source_id": changed_document_id,
                        "target_id": doc["id"],
                        "relationship_type": "potential",
                        "confidence": 0.5,
                        "impact_weight": 0.5,
                        "description": "Basic relationship (advanced analysis not available)",
                    }
                )

        return {
            "relationships": relationships,
            "relationship_graph": {"nodes": [], "edges": []},
            "total_relationships": len(relationships),
            "relationship_types": ["potential"],
        }
