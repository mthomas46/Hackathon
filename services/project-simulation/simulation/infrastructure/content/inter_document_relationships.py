"""Inter-Document Relationships - Intelligent Cross-Reference System.

This module implements sophisticated inter-document relationship management that creates
intelligent connections between project documents, establishing dependencies, references,
and contextual relationships that reflect real-world document ecosystems.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime
from enum import Enum
import networkx as nx
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.content.context_aware_generation import ContentContext
from simulation.infrastructure.content.timeline_based_generation import TimelineAwareContentGenerator
from simulation.infrastructure.content.personality_driven_generation import PersonalityDrivenGenerator


class RelationshipType(Enum):
    """Types of relationships between documents."""
    PREREQUISITE = "prerequisite"
    REFERENCE = "reference"
    UPDATE = "update"
    SUPERSEDE = "supersede"
    COMPLEMENT = "complement"
    IMPLEMENT = "implement"
    VALIDATE = "validate"
    DEPENDENCY = "dependency"
    DERIVE_FROM = "derive_from"
    CONFLICT_WITH = "conflict_with"


class DocumentReference:
    """Represents a reference between documents."""

    def __init__(self,
                 source_doc_id: str,
                 target_doc_id: str,
                 relationship_type: RelationshipType,
                 strength: float = 1.0,
                 context: Optional[str] = None,
                 bidirectional: bool = False):
        """Initialize document reference."""
        self.source_doc_id = source_doc_id
        self.target_doc_id = target_doc_id
        self.relationship_type = relationship_type
        self.strength = strength
        self.context = context
        self.bidirectional = bidirectional
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "source_doc_id": self.source_doc_id,
            "target_doc_id": self.target_doc_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "context": self.context,
            "bidirectional": self.bidirectional,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


class DocumentNode:
    """Represents a document node in the relationship graph."""

    def __init__(self,
                 doc_id: str,
                 doc_type: str,
                 title: str,
                 created_at: datetime,
                 author_id: Optional[str] = None,
                 version: str = "1.0"):
        """Initialize document node."""
        self.doc_id = doc_id
        self.doc_type = doc_type
        self.title = title
        self.created_at = created_at
        self.author_id = author_id
        self.version = version
        self.tags: Set[str] = set()
        self.metadata: Dict[str, Any] = {}

    def add_tag(self, tag: str):
        """Add a tag to the document."""
        self.tags.add(tag)

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the document."""
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "author_id": self.author_id,
            "version": self.version,
            "tags": list(self.tags),
            "metadata": self.metadata
        }


class DocumentRelationshipManager:
    """Manages relationships between documents in a project."""

    def __init__(self):
        """Initialize relationship manager."""
        self.logger = get_simulation_logger()

        # Core data structures
        self.documents: Dict[str, DocumentNode] = {}
        self.relationships: List[DocumentReference] = []
        self.relationship_graph = nx.DiGraph()

        # Relationship patterns by document type
        self.relationship_patterns = self._load_relationship_patterns()

        # Context-aware generators
        self.context_generator = None
        self.timeline_generator = TimelineAwareContentGenerator()
        self.personality_generator = PersonalityDrivenGenerator()

    def _load_relationship_patterns(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Load predefined relationship patterns for different document types."""
        return {
            "project_requirements": {
                "outgoing": [
                    {"type": RelationshipType.IMPLEMENT.value, "target_types": ["technical_design", "architecture_diagram"], "strength": 0.9},
                    {"type": RelationshipType.REFERENCE.value, "target_types": ["user_story"], "strength": 0.7},
                    {"type": RelationshipType.PREREQUISITE.value, "target_types": ["project_requirements"], "strength": 1.0}
                ],
                "incoming": [
                    {"type": RelationshipType.DERIVE_FROM.value, "source_types": ["user_story", "business_analysis"], "strength": 0.8},
                    {"type": RelationshipType.UPDATE.value, "source_types": ["change_request"], "strength": 0.6}
                ]
            },
            "architecture_diagram": {
                "outgoing": [
                    {"type": RelationshipType.IMPLEMENT.value, "target_types": ["technical_design"], "strength": 0.8},
                    {"type": RelationshipType.REFERENCE.value, "target_types": ["deployment_guide"], "strength": 0.6}
                ],
                "incoming": [
                    {"type": RelationshipType.DERIVE_FROM.value, "source_types": ["project_requirements"], "strength": 0.7},
                    {"type": RelationshipType.REFERENCE.value, "source_types": ["technical_design"], "strength": 0.5}
                ]
            },
            "user_story": {
                "outgoing": [
                    {"type": RelationshipType.IMPLEMENT.value, "target_types": ["technical_design"], "strength": 0.7},
                    {"type": RelationshipType.VALIDATE.value, "target_types": ["test_scenarios"], "strength": 0.8}
                ],
                "incoming": [
                    {"type": RelationshipType.DERIVE_FROM.value, "source_types": ["project_requirements"], "strength": 0.9}
                ]
            },
            "technical_design": {
                "outgoing": [
                    {"type": RelationshipType.IMPLEMENT.value, "target_types": ["code_implementation"], "strength": 0.9},
                    {"type": RelationshipType.REFERENCE.value, "target_types": ["test_scenarios"], "strength": 0.7}
                ],
                "incoming": [
                    {"type": RelationshipType.DERIVE_FROM.value, "source_types": ["project_requirements", "architecture_diagram"], "strength": 0.8},
                    {"type": RelationshipType.REFERENCE.value, "source_types": ["user_story"], "strength": 0.6}
                ]
            },
            "test_scenarios": {
                "outgoing": [
                    {"type": RelationshipType.VALIDATE.value, "target_types": ["user_story", "technical_design"], "strength": 0.8}
                ],
                "incoming": [
                    {"type": RelationshipType.DERIVE_FROM.value, "source_types": ["user_story", "technical_design"], "strength": 0.7},
                    {"type": RelationshipType.REFERENCE.value, "source_types": ["test_plan"], "strength": 0.6}
                ]
            },
            "deployment_guide": {
                "outgoing": [
                    {"type": RelationshipType.REFERENCE.value, "target_types": ["maintenance_docs"], "strength": 0.5}
                ],
                "incoming": [
                    {"type": RelationshipType.DERIVE_FROM.value, "source_types": ["architecture_diagram", "technical_design"], "strength": 0.6}
                ]
            }
        }

    def add_document(self, doc_id: str, doc_type: str, title: str,
                    author_id: Optional[str] = None, **metadata) -> DocumentNode:
        """Add a document to the relationship graph."""
        if doc_id in self.documents:
            raise ValueError(f"Document {doc_id} already exists")

        node = DocumentNode(
            doc_id=doc_id,
            doc_type=doc_type,
            title=title,
            created_at=datetime.now(),
            author_id=author_id
        )

        # Add metadata
        for key, value in metadata.items():
            node.add_metadata(key, value)

        # Add tags based on document type and metadata
        self._add_document_tags(node)

        self.documents[doc_id] = node
        self.relationship_graph.add_node(doc_id, **node.to_dict())

        self.logger.info("Added document to relationship graph",
                        doc_id=doc_id, doc_type=doc_type)

        return node

    def _add_document_tags(self, node: DocumentNode):
        """Add relevant tags to a document based on its type and metadata."""
        # Type-based tags
        type_tags = {
            "project_requirements": ["requirements", "planning", "business"],
            "architecture_diagram": ["architecture", "design", "technical"],
            "user_story": ["requirements", "user", "agile"],
            "technical_design": ["design", "technical", "implementation"],
            "test_scenarios": ["testing", "quality", "validation"],
            "deployment_guide": ["deployment", "operations", "infrastructure"],
            "maintenance_docs": ["maintenance", "operations", "support"]
        }

        if node.doc_type in type_tags:
            for tag in type_tags[node.doc_type]:
                node.add_tag(tag)

        # Metadata-based tags
        if "phase" in node.metadata:
            node.add_tag(f"phase_{node.metadata['phase']}")

        if "priority" in node.metadata:
            node.add_tag(f"priority_{node.metadata['priority']}")

        if "complexity" in node.metadata:
            node.add_tag(f"complexity_{node.metadata['complexity']}")

    def create_relationship(self, source_doc_id: str, target_doc_id: str,
                          relationship_type: RelationshipType,
                          strength: float = 1.0,
                          context: Optional[str] = None,
                          bidirectional: bool = False) -> DocumentReference:
        """Create a relationship between two documents."""
        if source_doc_id not in self.documents:
            raise ValueError(f"Source document {source_doc_id} not found")
        if target_doc_id not in self.documents:
            raise ValueError(f"Target document {target_doc_id} not found")

        reference = DocumentReference(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            relationship_type=relationship_type,
            strength=strength,
            context=context,
            bidirectional=bidirectional
        )

        self.relationships.append(reference)

        # Add to graph
        self.relationship_graph.add_edge(
            source_doc_id,
            target_doc_id,
            relationship_type=relationship_type.value,
            strength=strength,
            context=context
        )

        # Add reverse relationship if bidirectional
        if bidirectional:
            reverse_ref = DocumentReference(
                source_doc_id=target_doc_id,
                target_doc_id=source_doc_id,
                relationship_type=relationship_type,
                strength=strength,
                context=f"Reverse of: {context}" if context else None,
                bidirectional=True
            )
            self.relationships.append(reverse_ref)
            self.relationship_graph.add_edge(
                target_doc_id,
                source_doc_id,
                relationship_type=relationship_type.value,
                strength=strength,
                context=f"Reverse of: {context}" if context else None
            )

        self.logger.info("Created document relationship",
                        source=source_doc_id, target=target_doc_id,
                        type=relationship_type.value)

        return reference

    def generate_automatic_relationships(self, new_doc_id: str) -> List[DocumentReference]:
        """Generate automatic relationships for a newly added document."""
        if new_doc_id not in self.documents:
            raise ValueError(f"Document {new_doc_id} not found")

        new_doc = self.documents[new_doc_id]
        relationships_created = []

        # Get relationship patterns for this document type
        patterns = self.relationship_patterns.get(new_doc.doc_type, {})

        # Create outgoing relationships
        for pattern in patterns.get("outgoing", []):
            for target_doc_id, target_doc in self.documents.items():
                if target_doc_id != new_doc_id and target_doc.doc_type in pattern["target_types"]:
                    # Check if relationship already exists
                    if not self._relationship_exists(new_doc_id, target_doc_id, pattern["type"]):
                        relationship = self.create_relationship(
                            source_doc_id=new_doc_id,
                            target_doc_id=target_doc_id,
                            relationship_type=RelationshipType(pattern["type"]),
                            strength=pattern["strength"],
                            context=f"Automatically generated based on document type patterns"
                        )
                        relationships_created.append(relationship)

        # Create incoming relationships (relationships from other docs to this one)
        for pattern in patterns.get("incoming", []):
            for source_doc_id, source_doc in self.documents.items():
                if source_doc_id != new_doc_id and source_doc.doc_type in pattern["source_types"]:
                    # Check if relationship already exists
                    if not self._relationship_exists(source_doc_id, new_doc_id, pattern["type"]):
                        relationship = self.create_relationship(
                            source_doc_id=source_doc_id,
                            target_doc_id=new_doc_id,
                            relationship_type=RelationshipType(pattern["type"]),
                            strength=pattern["strength"],
                            context=f"Automatically generated based on document type patterns"
                        )
                        relationships_created.append(relationship)

        return relationships_created

    def _relationship_exists(self, source_id: str, target_id: str, rel_type: str) -> bool:
        """Check if a relationship already exists between two documents."""
        return any(
            rel.source_doc_id == source_id and
            rel.target_doc_id == target_id and
            rel.relationship_type.value == rel_type
            for rel in self.relationships
        )

    def get_document_relationships(self, doc_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all relationships for a specific document."""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")

        incoming = []
        outgoing = []

        for rel in self.relationships:
            if rel.source_doc_id == doc_id:
                outgoing.append({
                    "target_doc_id": rel.target_doc_id,
                    "relationship_type": rel.relationship_type.value,
                    "strength": rel.strength,
                    "context": rel.context,
                    "target_doc_type": self.documents[rel.target_doc_id].doc_type,
                    "target_doc_title": self.documents[rel.target_doc_id].title
                })
            elif rel.target_doc_id == doc_id:
                incoming.append({
                    "source_doc_id": rel.source_doc_id,
                    "relationship_type": rel.relationship_type.value,
                    "strength": rel.strength,
                    "context": rel.context,
                    "source_doc_type": self.documents[rel.source_doc_id].doc_type,
                    "source_doc_title": self.documents[rel.source_doc_id].title
                })

        return {
            "incoming_relationships": incoming,
            "outgoing_relationships": outgoing,
            "total_relationships": len(incoming) + len(outgoing)
        }

    def find_related_documents(self, doc_id: str, max_depth: int = 2,
                             relationship_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find documents related to a given document within specified depth."""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")

        # Use NetworkX for graph traversal
        related_docs = {}

        # Find paths within max_depth
        for target_doc_id in self.documents:
            if target_doc_id != doc_id:
                try:
                    # Find shortest path
                    path = nx.shortest_path(self.relationship_graph, doc_id, target_doc_id)
                    if len(path) <= max_depth + 1:  # +1 because path includes start node
                        path_length = len(path) - 1
                        relationship_chain = self._build_relationship_chain(path)

                        # Filter by relationship types if specified
                        if relationship_types:
                            if any(rel["type"] in relationship_types for rel in relationship_chain):
                                related_docs[target_doc_id] = {
                                    "doc_info": self.documents[target_doc_id].to_dict(),
                                    "distance": path_length,
                                    "relationship_chain": relationship_chain,
                                    "relevance_score": self._calculate_relevance_score(relationship_chain)
                                }
                        else:
                            related_docs[target_doc_id] = {
                                "doc_info": self.documents[target_doc_id].to_dict(),
                                "distance": path_length,
                                "relationship_chain": relationship_chain,
                                "relevance_score": self._calculate_relevance_score(relationship_chain)
                            }
                except nx.NetworkXNoPath:
                    continue

        # Sort by relevance score
        sorted_related = sorted(
            related_docs.items(),
            key=lambda x: x[1]["relevance_score"],
            reverse=True
        )

        return {
            "source_document": self.documents[doc_id].to_dict(),
            "related_documents": dict(sorted_related),
            "total_related": len(related_docs),
            "max_depth_searched": max_depth
        }

    def _build_relationship_chain(self, path: List[str]) -> List[Dict[str, Any]]:
        """Build relationship chain for a path."""
        chain = []

        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]

            # Find the relationship
            relationship = None
            for rel in self.relationships:
                if rel.source_doc_id == source_id and rel.target_doc_id == target_id:
                    relationship = rel
                    break

            if relationship:
                chain.append({
                    "from_doc": source_id,
                    "to_doc": target_id,
                    "type": relationship.relationship_type.value,
                    "strength": relationship.strength,
                    "context": relationship.context
                })

        return chain

    def _calculate_relevance_score(self, relationship_chain: List[Dict[str, Any]]) -> float:
        """Calculate relevance score for a relationship chain."""
        if not relationship_chain:
            return 0.0

        # Base score from relationship strengths
        strength_score = sum(rel["strength"] for rel in relationship_chain) / len(relationship_chain)

        # Bonus for shorter chains
        length_penalty = 1.0 / len(relationship_chain)

        # Bonus for certain relationship types
        type_bonus = 0.0
        high_value_types = [RelationshipType.PREREQUISITE.value, RelationshipType.IMPLEMENT.value]
        for rel in relationship_chain:
            if rel["type"] in high_value_types:
                type_bonus += 0.2

        return min(1.0, strength_score * length_penalty + type_bonus)

    def generate_cross_references_content(self, doc_id: str) -> Dict[str, Any]:
        """Generate cross-reference content for a document."""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")

        relationships = self.get_document_relationships(doc_id)
        related_docs = self.find_related_documents(doc_id, max_depth=3)

        # Generate cross-reference text
        cross_references = self._generate_cross_reference_text(
            self.documents[doc_id],
            relationships,
            related_docs
        )

        # Generate navigation suggestions
        navigation_suggestions = self._generate_navigation_suggestions(
            doc_id, relationships, related_docs
        )

        return {
            "document_id": doc_id,
            "cross_references": cross_references,
            "navigation_suggestions": navigation_suggestions,
            "relationship_summary": {
                "total_relationships": relationships["total_relationships"],
                "incoming_count": len(relationships["incoming_relationships"]),
                "outgoing_count": len(relationships["outgoing_relationships"]),
                "related_documents_count": len(related_docs["related_documents"])
            }
        }

    def _generate_cross_reference_text(self, document: DocumentNode,
                                     relationships: Dict[str, List[Dict[str, Any]]],
                                     related_docs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate human-readable cross-reference text."""
        cross_refs = {
            "prerequisites": [],
            "implements": [],
            "references": [],
            "updates": [],
            "complements": []
        }

        # Process outgoing relationships
        for rel in relationships["outgoing_relationships"]:
            rel_type = rel["relationship_type"]
            target_title = rel["target_doc_title"]
            target_type = rel["target_doc_type"]

            if rel_type == RelationshipType.PREREQUISITE.value:
                cross_refs["prerequisites"].append(f"Prerequisites: {target_title}")
            elif rel_type == RelationshipType.IMPLEMENT.value:
                cross_refs["implements"].append(f"Implements requirements from: {target_title}")
            elif rel_type == RelationshipType.REFERENCE.value:
                cross_refs["references"].append(f"See also: {target_title}")
            elif rel_type == RelationshipType.UPDATE.value:
                cross_refs["updates"].append(f"Updates: {target_title}")
            elif rel_type == RelationshipType.COMPLEMENT.value:
                cross_refs["complements"].append(f"Complements: {target_title}")

        # Process incoming relationships
        for rel in relationships["incoming_relationships"]:
            rel_type = rel["relationship_type"]
            source_title = rel["source_doc_title"]

            if rel_type == RelationshipType.IMPLEMENT.value:
                cross_refs["implements"].append(f"Implemented by: {source_title}")
            elif rel_type == RelationshipType.REFERENCE.value:
                cross_refs["references"].append(f"Referenced in: {source_title}")

        # Generate summary text
        summary_parts = []

        if cross_refs["prerequisites"]:
            summary_parts.append(f"This document depends on: {', '.join(cross_refs['prerequisites'])}")

        if cross_refs["implements"]:
            summary_parts.append(f"This document: {', '.join(cross_refs['implements'])}")

        if cross_refs["references"]:
            summary_parts.append(f"Related documents: {', '.join(cross_refs['references'])}")

        return {
            "sections": cross_refs,
            "summary": " ".join(summary_parts) if summary_parts else "No significant cross-references identified.",
            "detailed_relationships": relationships
        }

    def _generate_navigation_suggestions(self, doc_id: str,
                                       relationships: Dict[str, List[Dict[str, Any]]],
                                       related_docs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate navigation suggestions for document users."""
        suggestions = []

        # Suggest prerequisites first
        prerequisites = [
            rel for rel in relationships["outgoing_relationships"]
            if rel["relationship_type"] == RelationshipType.PREREQUISITE.value
        ]
        if prerequisites:
            suggestions.append({
                "type": "prerequisites",
                "priority": "high",
                "message": "Review prerequisite documents before proceeding",
                "documents": [rel["target_doc_id"] for rel in prerequisites]
            })

        # Suggest related implementation documents
        implementations = [
            rel for rel in relationships["incoming_relationships"]
            if rel["relationship_type"] == RelationshipType.IMPLEMENT.value
        ]
        if implementations:
            suggestions.append({
                "type": "implementations",
                "priority": "medium",
                "message": "Check implementation documents for current status",
                "documents": [rel["source_doc_id"] for rel in implementations]
            })

        # Suggest validation documents
        validations = [
            rel for rel in relationships["incoming_relationships"]
            if rel["relationship_type"] == RelationshipType.VALIDATE.value
        ]
        if validations:
            suggestions.append({
                "type": "validation",
                "priority": "medium",
                "message": "Review validation results and test coverage",
                "documents": [rel["source_doc_id"] for rel in validations]
            })

        # Suggest highly relevant related documents
        highly_relevant = [
            doc_id for doc_id, info in related_docs["related_documents"].items()
            if info["relevance_score"] > 0.7
        ][:3]  # Top 3

        if highly_relevant:
            suggestions.append({
                "type": "related_reading",
                "priority": "low",
                "message": "Consider reviewing these highly related documents",
                "documents": highly_relevant
            })

        return suggestions

    def export_relationship_graph(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """Export the relationship graph in specified format."""
        graph_data = {
            "documents": {doc_id: doc.to_dict() for doc_id, doc in self.documents.items()},
            "relationships": [rel.to_dict() for rel in self.relationships],
            "metadata": {
                "total_documents": len(self.documents),
                "total_relationships": len(self.relationships),
                "exported_at": datetime.now().isoformat(),
                "graph_density": self._calculate_graph_density()
            }
        }

        if format == "json":
            return json.dumps(graph_data, indent=2, default=str)
        else:
            return graph_data

    def _calculate_graph_density(self) -> float:
        """Calculate the density of the relationship graph."""
        if len(self.documents) <= 1:
            return 0.0

        max_possible_edges = len(self.documents) * (len(self.documents) - 1)
        actual_edges = len(self.relationships)

        return actual_edges / max_possible_edges if max_possible_edges > 0 else 0.0

    def get_relationship_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about document relationships."""
        if not self.relationships:
            return {"message": "No relationships found"}

        # Count relationship types
        type_counts = {}
        for rel in self.relationships:
            rel_type = rel.relationship_type.value
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

        # Calculate average strength
        total_strength = sum(rel.strength for rel in self.relationships)
        avg_strength = total_strength / len(self.relationships)

        # Document connectivity
        doc_connectivity = {}
        for doc_id in self.documents:
            relationships = self.get_document_relationships(doc_id)
            doc_connectivity[doc_id] = relationships["total_relationships"]

        most_connected = max(doc_connectivity.items(), key=lambda x: x[1]) if doc_connectivity else None

        return {
            "total_documents": len(self.documents),
            "total_relationships": len(self.relationships),
            "relationship_types": type_counts,
            "average_relationship_strength": avg_strength,
            "graph_density": self._calculate_graph_density(),
            "most_connected_document": most_connected[0] if most_connected else None,
            "connectivity_distribution": doc_connectivity,
            "bidirectional_relationships": len([r for r in self.relationships if r.bidirectional])
        }


# Global relationship manager instance
_relationship_manager: Optional[DocumentRelationshipManager] = None


def get_relationship_manager() -> DocumentRelationshipManager:
    """Get the global document relationship manager instance."""
    global _relationship_manager
    if _relationship_manager is None:
        _relationship_manager = DocumentRelationshipManager()
    return _relationship_manager


__all__ = [
    'RelationshipType',
    'DocumentReference',
    'DocumentNode',
    'DocumentRelationshipManager',
    'get_relationship_manager'
]
