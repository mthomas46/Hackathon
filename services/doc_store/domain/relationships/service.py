"""Relationships service for business logic operations.

Handles relationship processing and graph analysis business rules.
"""
import uuid
from typing import Dict, Any, List, Optional
from ...core.service import BaseService
from ...core.entities import DocumentRelationship, GraphNode, GraphEdge
from .repository import RelationshipsRepository


class RelationshipsService(BaseService[DocumentRelationship]):
    """Service for relationship business logic."""

    def __init__(self):
        super().__init__(RelationshipsRepository())

    def _validate_entity(self, entity: DocumentRelationship) -> None:
        """Validate relationship before saving."""
        if not entity.source_document_id or not entity.target_document_id:
            raise ValueError("Source and target document IDs are required")

        if entity.source_document_id == entity.target_document_id:
            raise ValueError("Cannot create relationship to self")

        if entity.strength < 0 or entity.strength > 1:
            raise ValueError("Relationship strength must be between 0 and 1")

        if not entity.relationship_type:
            raise ValueError("Relationship type is required")

    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> DocumentRelationship:
        """Create relationship from data."""
        return DocumentRelationship(
            id=entity_id,
            source_document_id=data['source_document_id'],
            target_document_id=data['target_document_id'],
            relationship_type=data['relationship_type'],
            strength=data.get('strength', 1.0),
            metadata=data.get('metadata', {})
        )

    def create_relationship(self, source_id: str, target_id: str, relationship_type: str,
                           strength: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> DocumentRelationship:
        """Create a new relationship."""
        data = {
            'source_document_id': source_id,
            'target_document_id': target_id,
            'relationship_type': relationship_type,
            'strength': strength,
            'metadata': metadata or {}
        }
        return self.create_entity(data)

    def get_relationships_for_document(self, document_id: str, relationship_type: Optional[str] = None,
                                     direction: str = "both", limit: int = 50) -> Dict[str, Any]:
        """Get relationships for a document with pagination."""
        relationships = self.repository.get_relationships_for_document(
            document_id, relationship_type, direction, limit
        )

        return {
            "document_id": document_id,
            "relationships": [rel.to_dict() for rel in relationships],
            "total": len(relationships),
            "relationship_type": relationship_type,
            "direction": direction,
            "limit": limit
        }

    def find_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Find paths between documents."""
        if max_depth < 1 or max_depth > 5:
            raise ValueError("Max depth must be between 1 and 5")

        paths = self.repository.find_paths(start_id, end_id, max_depth)

        return {
            "start_document": start_id,
            "end_document": end_id,
            "paths": paths,
            "total_paths": len(paths),
            "max_depth": max_depth
        }

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        stats = self.repository.get_graph_statistics()

        # Add computed metrics
        if stats['unique_documents'] > 0:
            # Network density (actual connections / possible connections)
            possible_connections = stats['unique_documents'] * (stats['unique_documents'] - 1) / 2
            stats['density'] = stats['total_relationships'] / possible_connections if possible_connections > 0 else 0

            # Clustering coefficient approximation
            stats['avg_clustering'] = min(stats['avg_degree'] / stats['unique_documents'], 1.0)

        return stats

    def extract_relationships_from_content(self, document_id: str, content: str,
                                         metadata: Optional[Dict[str, Any]] = None) -> List[DocumentRelationship]:
        """Extract relationships from document content."""
        relationships = []
        metadata = metadata or {}

        # Simple pattern-based extraction (can be enhanced with ML)
        import re

        # Extract document references
        doc_patterns = [
            r'doc:([a-zA-Z0-9_-]+)',
            r'#([a-zA-Z0-9_-]+)',
            r'@([a-zA-Z0-9_-]+)',
        ]

        for pattern in doc_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match != document_id:  # Avoid self-references
                    relationships.append(DocumentRelationship(
                        id=str(uuid.uuid4()),
                        source_document_id=document_id,
                        target_document_id=match,
                        relationship_type="references",
                        strength=0.8,
                        metadata={"extracted_from": "content", "pattern": pattern}
                    ))

        # Extract URL relationships
        url_pattern = r'https?://[^\s<>"]+'
        urls = re.findall(url_pattern, content)
        for url in urls:
            # Create relationship to external resource
            relationships.append(DocumentRelationship(
                id=str(uuid.uuid4()),
                source_document_id=document_id,
                target_document_id=f"external:{url}",
                relationship_type="links_to",
                strength=0.6,
                metadata={"url": url, "extracted_from": "content"}
            ))

        return relationships

    def build_graph(self, document_ids: Optional[List[str]] = None, max_depth: int = 2) -> Dict[str, Any]:
        """Build a relationship graph for visualization."""
        if document_ids:
            # Start with specified documents
            nodes = []
            edges = []

            for doc_id in document_ids:
                # Add node
                nodes.append(GraphNode(document_id=doc_id).to_dict())

                # Get relationships
                relationships = self.repository.get_relationships_for_document(doc_id, limit=100)
                for rel in relationships:
                    edges.append(GraphEdge(
                        source_id=rel.source_document_id,
                        target_id=rel.target_document_id,
                        relationship_type=rel.relationship_type,
                        strength=rel.strength,
                        metadata=rel.metadata
                    ).to_dict())

                    # Add target node if not already added
                    if not any(n['document_id'] == rel.target_document_id for n in nodes):
                        nodes.append(GraphNode(document_id=rel.target_document_id).to_dict())
        else:
            # Build graph from all relationships (limited for performance)
            relationships = self.repository.get_all(limit=500)
            nodes = []
            edges = []

            doc_ids = set()
            for rel in relationships:
                doc_ids.add(rel.source_document_id)
                doc_ids.add(rel.target_document_id)
                edges.append(GraphEdge(
                    source_id=rel.source_document_id,
                    target_id=rel.target_document_id,
                    relationship_type=rel.relationship_type,
                    strength=rel.strength,
                    metadata=rel.metadata
                ).to_dict())

            nodes = [GraphNode(document_id=doc_id).to_dict() for doc_id in doc_ids]

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
