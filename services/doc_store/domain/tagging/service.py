"""Tagging service for business logic operations.

Handles semantic tagging, content analysis, and taxonomy management.
"""
import re
import uuid
from typing import Dict, Any, List, Optional
from ...core.service import BaseService
from ...core.entities import DocumentTag, TaxonomyNode, SemanticEntity
from .repository import TaggingRepository


class TaggingService(BaseService[DocumentTag]):
    """Service for tagging business logic."""

    def __init__(self):
        super().__init__(TaggingRepository())

    def _validate_entity(self, entity: DocumentTag) -> None:
        """Validate document tag."""
        if not entity.document_id:
            raise ValueError("Document ID is required")

        if not entity.tag:
            raise ValueError("Tag is required")

        if not (0 <= entity.confidence <= 1):
            raise ValueError("Confidence must be between 0 and 1")

    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> DocumentTag:
        """Create document tag from data."""
        return DocumentTag(
            id=entity_id,
            document_id=data['document_id'],
            tag=data['tag'],
            confidence=data.get('confidence', 1.0)
        )

    def tag_document(self, document_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentTag]:
        """Automatically tag a document based on content analysis."""
        entities = self._analyze_content(content, metadata or {})

        tags = []
        for entity in entities:
            tag = self._create_entity({
                'document_id': document_id,
                'tag': entity.entity_value.lower(),
                'confidence': entity.confidence
            })

            # Apply taxonomy categorization
            taxonomy_node = self.repository.get_taxonomy_node(tag.tag)
            if taxonomy_node:
                # Tag already exists in taxonomy
                pass
            else:
                # Auto-categorize based on entity type
                category = self._categorize_entity(entity)
                if category:
                    self.repository.save_taxonomy_node(TaxonomyNode(
                        tag=tag.tag,
                        category=category,
                        description=f"Auto-categorized {entity.entity_type}"
                    ))

            tags.append(tag)

        return tags

    def _analyze_content(self, content: str, metadata: Dict[str, Any]) -> List[SemanticEntity]:
        """Analyze content for semantic entities."""
        entities = []

        # Programming languages detection
        languages = {
            'python', 'javascript', 'typescript', 'java', 'csharp', 'cpp', 'c++', 'c',
            'ruby', 'php', 'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab'
        }

        for lang in languages:
            if re.search(r'\b' + re.escape(lang) + r'\b', content, re.IGNORECASE):
                entities.append(SemanticEntity(
                    entity_type="programming_language",
                    entity_value=lang,
                    confidence=0.9
                ))

        # Framework detection
        frameworks = {
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
            'express', 'laravel', 'rails', 'dotnet', 'tensorflow', 'pytorch'
        }

        for framework in frameworks:
            if re.search(r'\b' + re.escape(framework) + r'\b', content, re.IGNORECASE):
                entities.append(SemanticEntity(
                    entity_type="framework",
                    entity_value=framework,
                    confidence=0.8
                ))

        # Content type detection from metadata
        content_type = metadata.get('type', '')
        if content_type:
            entities.append(SemanticEntity(
                entity_type="content_type",
                entity_value=content_type,
                confidence=1.0
            ))

        # Source type detection
        source_type = metadata.get('source_type', '')
        if source_type:
            entities.append(SemanticEntity(
                entity_type="source_type",
                entity_value=source_type,
                confidence=1.0
            ))

        return entities

    def _categorize_entity(self, entity: SemanticEntity) -> Optional[str]:
        """Categorize an entity for taxonomy."""
        type_to_category = {
            "programming_language": "language",
            "framework": "framework",
            "content_type": "content",
            "source_type": "source"
        }
        return type_to_category.get(entity.entity_type)

    def get_document_tags(self, document_id: str, category: Optional[str] = None) -> List[DocumentTag]:
        """Get tags for a document with optional category filtering."""
        tags = self.repository.get_tags_for_document(document_id)

        if category:
            # Filter by category using taxonomy
            filtered_tags = []
            for tag in tags:
                taxonomy_node = self.repository.get_taxonomy_node(tag.tag)
                if taxonomy_node and taxonomy_node.category == category:
                    filtered_tags.append(tag)
            return filtered_tags

        return tags

    def search_by_tags(self, tags: List[str], categories: Optional[List[str]] = None,
                      min_confidence: float = 0.0, limit: int = 50) -> Dict[str, Any]:
        """Search documents by tags."""
        results = []

        for tag in tags:
            # Find documents with this tag
            document_ids = self.repository.get_documents_by_tag(tag, min_confidence)

            for doc_id in document_ids:
                # Get all tags for this document
                doc_tags = self.repository.get_tags_for_document(doc_id)

                # Filter by categories if specified
                if categories:
                    filtered_tags = []
                    for t in doc_tags:
                        taxonomy_node = self.repository.get_taxonomy_node(t.tag)
                        if taxonomy_node and taxonomy_node.category in categories:
                            filtered_tags.append(t)
                    doc_tags = filtered_tags

                if doc_tags:  # Only include if document has matching tags
                    results.append({
                        "document_id": doc_id,
                        "matching_tags": [t.to_dict() for t in doc_tags],
                        "tag_count": len(doc_tags)
                    })

                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

        return {
            "results": results[:limit],
            "total": len(results),
            "searched_tags": tags,
            "categories": categories
        }

    def create_taxonomy_node(self, tag: str, category: str, description: str = "",
                           parent_tag: Optional[str] = None, synonyms: Optional[List[str]] = None) -> TaxonomyNode:
        """Create a taxonomy node."""
        node = TaxonomyNode(
            tag=tag,
            category=category,
            description=description,
            parent_tag=parent_tag,
            synonyms=synonyms or []
        )

        self.repository.save_taxonomy_node(node)
        return node

    def get_taxonomy_tree(self, root_category: Optional[str] = None) -> Dict[str, Any]:
        """Get taxonomy tree structure."""
        return self.repository.get_taxonomy_tree(root_category)

    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tag statistics."""
        return self.repository.get_tag_statistics()

    def remove_document_tags(self, document_id: str, tags: Optional[List[str]] = None) -> int:
        """Remove tags from a document."""
        return self.repository.remove_tags_from_document(document_id, tags)

    def update_tag_confidence(self, document_id: str, tag: str, confidence: float) -> None:
        """Update confidence score for a document tag."""
        # Find the tag
        tags = self.repository.get_tags_for_document(document_id)
        for t in tags:
            if t.tag == tag:
                t.confidence = confidence
                self.repository.update(t)
                break
