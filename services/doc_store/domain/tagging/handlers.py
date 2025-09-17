"""Tagging handlers for API endpoints.

Handles tagging and taxonomy-related HTTP requests.
"""
from typing import Dict, Any, Optional, List
from ...core.handler import BaseHandler
from .service import TaggingService


class TaggingHandlers(BaseHandler):
    """Handlers for tagging API endpoints."""

    def __init__(self):
        super().__init__(TaggingService())

    async def handle_tag_document(self, document_id: str) -> Dict[str, Any]:
        """Handle document tagging."""
        # Get document content for analysis
        from ...domain.documents.service import DocumentService
        doc_service = DocumentService()
        document = doc_service.get_entity(document_id)

        if not document:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Document not found")))

        # Tag the document
        tags = self.service.tag_document(document_id, document.content, document.metadata)

        return await self._handle_request(
            lambda: {"tags": [tag.to_dict() for tag in tags], "count": len(tags)},
            operation="tag_document",
            document_id=document_id,
            tags_created=len(tags)
        )

    async def handle_get_document_tags(self, document_id: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Handle document tags retrieval."""
        tags = self.service.get_document_tags(document_id, category)

        return await self._handle_request(
            lambda: {"tags": [tag.to_dict() for tag in tags], "count": len(tags)},
            operation="get_document_tags",
            document_id=document_id,
            category=category
        )

    async def handle_search_by_tags(self, tags: List[str], categories: Optional[List[str]] = None,
                                   min_confidence: float = 0.0, limit: int = 50) -> Dict[str, Any]:
        """Handle tag-based search."""
        if not tags:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Tags list cannot be empty")))

        result = self.service.search_by_tags(tags, categories, min_confidence, limit)

        return await self._handle_request(
            lambda: result,
            operation="search_by_tags",
            searched_tags=tags,
            results_count=result["total"]
        )

    async def handle_create_taxonomy_node(self, tag: str, category: str, description: str = "",
                                         parent_tag: Optional[str] = None, synonyms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Handle taxonomy node creation."""
        self._validate_request_data({
            'tag': tag,
            'category': category
        }, ['tag', 'category'])

        node = self.service.create_taxonomy_node(tag, category, description, parent_tag, synonyms)

        return await self._handle_request(
            lambda: node.to_dict(),
            operation="create_taxonomy_node",
            tag=tag,
            category=category
        )

    async def handle_get_taxonomy_tree(self, root_category: Optional[str] = None) -> Dict[str, Any]:
        """Handle taxonomy tree retrieval."""
        tree = self.service.get_taxonomy_tree(root_category)

        return await self._handle_request(
            lambda: tree,
            operation="get_taxonomy_tree",
            root_category=root_category
        )

    async def handle_get_tag_statistics(self) -> Dict[str, Any]:
        """Handle tag statistics request."""
        stats = self.service.get_tag_statistics()

        return await self._handle_request(
            lambda: stats,
            operation="get_tag_statistics"
        )

    async def handle_remove_document_tags(self, document_id: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Handle tag removal from document."""
        removed_count = self.service.remove_document_tags(document_id, tags)

        return await self._handle_request(
            lambda: {"removed_count": removed_count},
            operation="remove_document_tags",
            document_id=document_id,
            tags_removed=removed_count
        )

    async def handle_update_tag_confidence(self, document_id: str, tag: str, confidence: float) -> Dict[str, Any]:
        """Handle tag confidence update."""
        if not (0 <= confidence <= 1):
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Confidence must be between 0 and 1")))

        self.service.update_tag_confidence(document_id, tag, confidence)

        return await self._handle_request(
            lambda: {"document_id": document_id, "tag": tag, "confidence": confidence},
            operation="update_tag_confidence",
            document_id=document_id,
            tag=tag,
            confidence=confidence
        )
