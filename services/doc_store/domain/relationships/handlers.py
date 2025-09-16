"""Relationships handlers for API endpoints.

Handles relationship-related HTTP requests and responses.
"""
from typing import Dict, Any, Optional
from ...core.handler import BaseHandler
from ...core.models import RelationshipRequest, RelationshipsResponse, PathsResponse, GraphStatisticsResponse
from .service import RelationshipsService


class RelationshipsHandlers(BaseHandler):
    """Handlers for relationships API endpoints."""

    def __init__(self):
        super().__init__(RelationshipsService())

    async def handle_add_relationship(self, source_id: str, target_id: str, relationship_type: str,
                                    strength: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle relationship creation."""
        self._validate_request_data({
            'source_id': source_id,
            'target_id': target_id,
            'relationship_type': relationship_type
        }, ['source_id', 'target_id', 'relationship_type'])

        relationship = self.service.create_relationship(source_id, target_id, relationship_type, strength, metadata)

        return await self._handle_request(
            lambda: relationship.to_dict(),
            operation="add_relationship",
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type
        )

    async def handle_get_relationships(self, document_id: str, relationship_type: Optional[str] = None,
                                      direction: str = "both", limit: int = 50) -> Dict[str, Any]:
        """Handle relationships retrieval."""
        result = self.service.get_relationships_for_document(document_id, relationship_type, direction, limit)

        return await self._handle_request(
            lambda: result,
            operation="get_relationships",
            document_id=document_id,
            relationship_type=relationship_type,
            direction=direction
        )

    async def handle_find_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Handle path finding between documents."""
        result = self.service.find_paths(start_id, end_id, max_depth)

        return await self._handle_request(
            lambda: result,
            operation="find_paths",
            start_id=start_id,
            end_id=end_id,
            max_depth=max_depth
        )

    async def handle_graph_statistics(self) -> Dict[str, Any]:
        """Handle graph statistics request."""
        stats = self.service.get_graph_statistics()

        return await self._handle_request(
            lambda: stats,
            operation="get_graph_statistics"
        )

    async def handle_extract_relationships(self, document_id: str) -> Dict[str, Any]:
        """Handle relationship extraction from document content."""
        # Get document content
        from ...domain.documents.service import DocumentService
        doc_service = DocumentService()
        document = doc_service.get_entity(document_id)

        if not document:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Document not found")))

        # Extract relationships
        relationships = self.service.extract_relationships_from_content(
            document_id, document.content, document.metadata
        )

        # Save relationships
        saved_relationships = []
        for rel in relationships:
            try:
                saved = self.service.create_entity(rel.__dict__)
                saved_relationships.append(saved.to_dict())
            except Exception:
                # Skip duplicates or invalid relationships
                continue

        return await self._handle_request(
            lambda: {"relationships": saved_relationships, "count": len(saved_relationships)},
            operation="extract_relationships",
            document_id=document_id,
            extracted_count=len(saved_relationships)
        )

    async def handle_build_graph(self, document_ids: Optional[list] = None, max_depth: int = 2) -> Dict[str, Any]:
        """Handle graph building for visualization."""
        graph = self.service.build_graph(document_ids, max_depth)

        return await self._handle_request(
            lambda: graph,
            operation="build_graph",
            node_count=graph["node_count"],
            edge_count=graph["edge_count"]
        )
