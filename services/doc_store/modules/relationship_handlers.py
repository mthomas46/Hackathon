# ============================================================================
# RELATIONSHIP HANDLERS MODULE
# ============================================================================
"""
Relationship handlers for Doc Store service.

Provides endpoints for relationship management, graph traversal, and analysis.
"""

from typing import Dict, Any, Optional, List
from .relationships import relationship_graph
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .caching import docstore_cache


class RelationshipHandlers:
    """Handles relationship operations."""

    @staticmethod
    async def handle_add_relationship(source_id: str, target_id: str, relationship_type: str,
                                    strength: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a relationship between documents."""
        try:
            success = relationship_graph.add_relationship(
                source_id, target_id, relationship_type, strength, metadata
            )

            if success:
                context = build_doc_store_context(
                    "relationship_creation",
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=relationship_type
                )
                return create_doc_store_success_response("relationship created", {
                    "source_id": source_id,
                    "target_id": target_id,
                    "relationship_type": relationship_type,
                    "strength": strength
                }, **context)
            else:
                return handle_doc_store_error("create relationship", "Failed to create relationship")

        except Exception as e:
            context = build_doc_store_context("relationship_creation")
            return handle_doc_store_error("create relationship", e, **context)

    @staticmethod
    async def handle_get_relationships(document_id: str, relationship_type: Optional[str] = None,
                                      direction: str = "both", limit: int = 50) -> Dict[str, Any]:
        """Get relationships for a document."""
        try:
            # Check cache first
            cache_key = f"relationships:{document_id}:{relationship_type}:{direction}:{limit}"
            cached_result = await docstore_cache.get("relationships", {
                "document_id": document_id,
                "relationship_type": relationship_type,
                "direction": direction,
                "limit": limit
            }, tags=["relationships", f"doc:{document_id}"])

            if cached_result:
                context = build_doc_store_context(
                    "relationship_retrieval",
                    document_id=document_id,
                    cached=True
                )
                return create_doc_store_success_response("relationships retrieved from cache", cached_result, **context)

            # Get relationships
            result = relationship_graph.get_relationships(
                document_id, relationship_type, direction, limit
            )

            # Cache for 10 minutes
            await docstore_cache.set("relationships", {
                "document_id": document_id,
                "relationship_type": relationship_type,
                "direction": direction,
                "limit": limit
            }, result, ttl=600, tags=["relationships", f"doc:{document_id}"])

            context = build_doc_store_context("relationship_retrieval", document_id=document_id)
            return create_doc_store_success_response("relationships retrieved", result, **context)

        except Exception as e:
            context = build_doc_store_context("relationship_retrieval", document_id=document_id)
            return handle_doc_store_error("retrieve relationships", e, **context)

    @staticmethod
    async def handle_find_paths(start_id: str, end_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Find paths between two documents."""
        try:
            paths = relationship_graph.find_paths(start_id, end_id, max_depth)

            result = {
                "start_document": start_id,
                "end_document": end_id,
                "max_depth": max_depth,
                "paths_found": len(paths),
                "paths": paths
            }

            context = build_doc_store_context(
                "path_finding",
                start_id=start_id,
                end_id=end_id,
                paths_found=len(paths)
            )
            return create_doc_store_success_response("paths found", result, **context)

        except Exception as e:
            context = build_doc_store_context("path_finding", start_id=start_id, end_id=end_id)
            return handle_doc_store_error("find paths", e, **context)

    @staticmethod
    async def handle_graph_statistics() -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        try:
            # Check cache first (cache for 30 minutes since stats change less frequently)
            cached_result = await docstore_cache.get("graph_stats", {}, tags=["graph_stats"])

            if cached_result:
                context = build_doc_store_context("graph_statistics", cached=True)
                return create_doc_store_success_response("graph statistics retrieved from cache", cached_result, **context)

            # Generate statistics
            stats = relationship_graph.get_graph_statistics()

            # Cache for 30 minutes
            await docstore_cache.set("graph_stats", {}, stats, ttl=1800, tags=["graph_stats"])

            context = build_doc_store_context("graph_statistics")
            return create_doc_store_success_response("graph statistics generated", stats, **context)

        except Exception as e:
            context = build_doc_store_context("graph_statistics")
            return handle_doc_store_error("generate graph statistics", e, **context)

    @staticmethod
    async def handle_extract_relationships(document_id: str) -> Dict[str, Any]:
        """Extract relationships for an existing document."""
        try:
            # Get document content
            document = relationship_graph.extractor._document_exists(document_id)
            if not document:
                return handle_doc_store_error("extract relationships", f"Document {document_id} not found")

            # Get document data
            from .shared_utils import get_document_by_id
            doc_data = get_document_by_id(document_id)
            if not doc_data:
                return handle_doc_store_error("extract relationships", f"Document {document_id} not found")

            # Extract relationships
            stored_count = relationship_graph.extract_and_store_relationships(
                document_id,
                doc_data.get("content", ""),
                doc_data.get("metadata", {})
            )

            context = build_doc_store_context(
                "relationship_extraction",
                document_id=document_id,
                relationships_stored=stored_count
            )
            return create_doc_store_success_response("relationships extracted", {
                "document_id": document_id,
                "relationships_stored": stored_count
            }, **context)

        except Exception as e:
            context = build_doc_store_context("relationship_extraction", document_id=document_id)
            return handle_doc_store_error("extract relationships", e, **context)
