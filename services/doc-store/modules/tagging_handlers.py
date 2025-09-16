# ============================================================================
# TAGGING HANDLERS MODULE
# ============================================================================
"""
Semantic tagging handlers for Doc Store service.

Provides endpoints for automatic tagging, taxonomy management, and semantic search.
"""

from typing import Dict, Any, Optional, List
from .semantic_tagging import semantic_tagger, tag_taxonomy
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .caching import docstore_cache


class TaggingHandlers:
    """Handles semantic tagging operations."""

    @staticmethod
    async def handle_tag_document(document_id: str) -> Dict[str, Any]:
        """Automatically tag a document with semantic information."""
        try:
            # Get document data
            from .shared_utils import get_document_by_id
            doc_data = get_document_by_id(document_id)

            if not doc_data:
                return handle_doc_store_error("tag document", f"Document {document_id} not found")

            content = doc_data.get("content", "")
            metadata = doc_data.get("metadata", {})

            # Tag the document
            result = semantic_tagger.tag_document(document_id, content, metadata)

            # Invalidate caches
            docstore_cache.invalidate(tags=["tags", f"doc:{document_id}"])

            context = build_doc_store_context("document_tagging", document_id=document_id)
            return create_doc_store_success_response("document tagged successfully", result, **context)

        except Exception as e:
            context = build_doc_store_context("document_tagging", document_id=document_id)
            return handle_doc_store_error("tag document", e, **context)

    @staticmethod
    async def handle_get_document_tags(document_id: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Get tags for a document."""
        try:
            # Check cache first
            cache_key = f"document_tags:{document_id}:{category}"
            cached_result = await docstore_cache.get("tags", {"document_id": document_id, "category": category},
                                                    tags=["tags", f"doc:{document_id}"])

            if cached_result:
                context = build_doc_store_context("tag_retrieval", document_id=document_id, cached=True)
                return create_doc_store_success_response("document tags retrieved from cache", cached_result, **context)

            # Get tags
            tags = semantic_tagger.get_document_tags(document_id, category)

            result = {
                "document_id": document_id,
                "tags": tags,
                "total_tags": len(tags),
                "category_filter": category
            }

            # Cache for 30 minutes
            await docstore_cache.set("tags", {"document_id": document_id, "category": category},
                                   result, ttl=1800, tags=["tags", f"doc:{document_id}"])

            context = build_doc_store_context("tag_retrieval", document_id=document_id)
            return create_doc_store_success_response("document tags retrieved", result, **context)

        except Exception as e:
            context = build_doc_store_context("tag_retrieval", document_id=document_id)
            return handle_doc_store_error("get document tags", e, **context)

    @staticmethod
    async def handle_search_by_tags(tags: List[str], categories: Optional[List[str]] = None,
                                   min_confidence: float = 0.0, limit: int = 50) -> Dict[str, Any]:
        """Search documents by tags."""
        try:
            # Create cache key from search parameters
            search_params = {
                "tags": sorted(tags),
                "categories": sorted(categories) if categories else None,
                "min_confidence": min_confidence,
                "limit": limit
            }
            cache_key = f"tag_search:{hash(str(search_params))}"

            # Check cache
            cached_result = await docstore_cache.get("tag_search", search_params, tags=["tag_search"])

            if cached_result:
                context = build_doc_store_context("tag_search", cached=True)
                return create_doc_store_success_response("tag search results retrieved from cache", cached_result, **context)

            # Perform search
            results = semantic_tagger.search_by_tags(tags, categories, min_confidence, limit)

            result = {
                "query": {
                    "tags": tags,
                    "categories": categories,
                    "min_confidence": min_confidence,
                    "limit": limit
                },
                "results": results,
                "total_results": len(results)
            }

            # Cache for 10 minutes
            await docstore_cache.set("tag_search", search_params, result, ttl=600, tags=["tag_search"])

            context = build_doc_store_context("tag_search", result_count=len(results))
            return create_doc_store_success_response("tag search completed", result, **context)

        except Exception as e:
            context = build_doc_store_context("tag_search")
            return handle_doc_store_error("search by tags", e, **context)

    @staticmethod
    async def handle_get_tag_statistics() -> Dict[str, Any]:
        """Get comprehensive tag statistics."""
        try:
            # Check cache (stats change less frequently)
            cached_result = await docstore_cache.get("tag_stats", {}, tags=["tag_stats"])

            if cached_result:
                context = build_doc_store_context("tag_statistics", cached=True)
                return create_doc_store_success_response("tag statistics retrieved from cache", cached_result, **context)

            # Generate statistics
            stats = semantic_tagger.get_tag_statistics()

            # Cache for 30 minutes
            await docstore_cache.set("tag_stats", {}, stats, ttl=1800, tags=["tag_stats"])

            context = build_doc_store_context("tag_statistics")
            return create_doc_store_success_response("tag statistics generated", stats, **context)

        except Exception as e:
            context = build_doc_store_context("tag_statistics")
            return handle_doc_store_error("get tag statistics", e, **context)

    @staticmethod
    async def handle_create_taxonomy_node(tag: str, category: str, description: str = "",
                                         parent_tag: Optional[str] = None,
                                         synonyms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a taxonomy node."""
        try:
            success = tag_taxonomy.create_taxonomy_node(tag, category, description, parent_tag, synonyms)

            if success:
                # Invalidate taxonomy cache
                docstore_cache.invalidate(tags=["taxonomy"])

                context = build_doc_store_context("taxonomy_creation", tag=tag, category=category)
                return create_doc_store_success_response("taxonomy node created", {
                    "tag": tag,
                    "category": category,
                    "description": description,
                    "parent_tag": parent_tag,
                    "synonyms": synonyms
                }, **context)
            else:
                return handle_doc_store_error("create taxonomy node", "Failed to create taxonomy node")

        except Exception as e:
            context = build_doc_store_context("taxonomy_creation", tag=tag)
            return handle_doc_store_error("create taxonomy node", e, **context)

    @staticmethod
    async def handle_get_taxonomy_tree(root_category: Optional[str] = None) -> Dict[str, Any]:
        """Get taxonomy tree structure."""
        try:
            # Check cache
            cached_result = await docstore_cache.get("taxonomy", {"root_category": root_category}, tags=["taxonomy"])

            if cached_result:
                context = build_doc_store_context("taxonomy_retrieval", cached=True)
                return create_doc_store_success_response("taxonomy tree retrieved from cache", cached_result, **context)

            # Get taxonomy tree
            tree = tag_taxonomy.get_taxonomy_tree(root_category)

            result = {
                "root_category": root_category,
                "taxonomy_tree": tree
            }

            # Cache for 1 hour (taxonomy changes infrequently)
            await docstore_cache.set("taxonomy", {"root_category": root_category}, result, ttl=3600, tags=["taxonomy"])

            context = build_doc_store_context("taxonomy_retrieval")
            return create_doc_store_success_response("taxonomy tree retrieved", result, **context)

        except Exception as e:
            context = build_doc_store_context("taxonomy_retrieval")
            return handle_doc_store_error("get taxonomy tree", e, **context)
