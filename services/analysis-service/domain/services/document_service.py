"""Document domain service."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities import Document, DocumentId, Content, Metadata


class DocumentService:
    """Domain service for document operations."""

    def __init__(self, max_document_size: int = 10 * 1024 * 1024):  # 10MB default
        """Initialize document service."""
        self.max_document_size = max_document_size

    def create_document(self, title: str, content_text: str,
                       content_format: str = "markdown",
                       author: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       repository_id: Optional[str] = None) -> Document:
        """Create a new document."""
        # Validate content size
        if len(content_text.encode('utf-8')) > self.max_document_size:
            raise ValueError(f"Document content exceeds maximum size of {self.max_document_size} bytes")

        # Generate document ID
        document_id = DocumentId(f"doc_{datetime.now().timestamp()}_{hash(title) % 10000}")

        # Create content value object
        content = Content(text=content_text, format=content_format)

        # Create metadata
        now = datetime.now()
        metadata = Metadata(
            created_at=now,
            updated_at=now,
            author=author,
            tags=tags or []
        )

        # Create document entity
        document = Document(
            id=document_id,
            title=title,
            content=content,
            metadata=metadata,
            repository_id=repository_id
        )

        return document

    def update_document_content(self, document: Document,
                               new_content: str,
                               new_format: Optional[str] = None) -> Document:
        """Update document content."""
        # Validate content size
        if len(new_content.encode('utf-8')) > self.max_document_size:
            raise ValueError(f"Document content exceeds maximum size of {self.max_document_size} bytes")

        # Create new content
        content_format = new_format or document.content.format
        new_content_obj = Content(text=new_content, format=content_format)

        # Update document
        document.update_content(new_content_obj)

        # Update metadata
        new_metadata = Metadata(
            created_at=document.metadata.created_at,
            updated_at=datetime.now(),
            author=document.metadata.author,
            tags=document.metadata.tags,
            properties=document.metadata.properties
        )
        document.update_metadata(new_metadata)

        return document

    def validate_document(self, document: Document) -> List[str]:
        """Validate document and return list of issues."""
        issues = []

        # Check title
        if len(document.title.strip()) == 0:
            issues.append("Document title cannot be empty")
        elif len(document.title) > 200:
            issues.append("Document title too long (max 200 characters)")

        # Check content
        if len(document.content.text.strip()) == 0:
            issues.append("Document content cannot be empty")

        # Check word count
        word_count = document.word_count
        if word_count < 10:
            issues.append("Document too short (minimum 10 words)")
        elif word_count > 50000:
            issues.append("Document too long (maximum 50,000 words)")

        # Check age
        age_days = (datetime.now() - document.metadata.updated_at).days
        if age_days > 365:
            issues.append(f"Document not updated for {age_days} days")

        return issues

    def search_documents(self, documents: List[Document],
                        query: str,
                        filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search documents by content and metadata."""
        results = []

        for document in documents:
            # Check content match
            content_match = query.lower() in document.content.text.lower()

            # Check title match
            title_match = query.lower() in document.title.lower()

            # Check metadata matches
            metadata_match = False
            if filters:
                if 'author' in filters and document.metadata.author:
                    metadata_match = filters['author'].lower() in document.metadata.author.lower()
                if 'tags' in filters:
                    metadata_match = any(tag in document.metadata.tags for tag in filters['tags'])

            if content_match or title_match or metadata_match:
                results.append(document)

        return results

    def get_document_statistics(self, documents: List[Document]) -> Dict[str, Any]:
        """Get statistics about a collection of documents."""
        if not documents:
            return {
                'total_documents': 0,
                'total_words': 0,
                'avg_words_per_doc': 0,
                'oldest_document_days': 0,
                'newest_document_days': 0
            }

        total_words = sum(doc.word_count for doc in documents)
        created_dates = [doc.metadata.created_at for doc in documents]
        updated_dates = [doc.metadata.updated_at for doc in documents]

        oldest_created = min(created_dates)
        newest_updated = max(updated_dates)

        return {
            'total_documents': len(documents),
            'total_words': total_words,
            'avg_words_per_doc': total_words / len(documents),
            'oldest_document_days': (datetime.now() - oldest_created).days,
            'newest_document_days': (datetime.now() - newest_updated).days,
            'documents_by_format': self._count_by_format(documents),
            'documents_by_author': self._count_by_author(documents)
        }

    def _count_by_format(self, documents: List[Document]) -> Dict[str, int]:
        """Count documents by format."""
        format_counts = {}
        for doc in documents:
            format_name = doc.content.format
            format_counts[format_name] = format_counts.get(format_name, 0) + 1
        return format_counts

    def _count_by_author(self, documents: List[Document]) -> Dict[str, int]:
        """Count documents by author."""
        author_counts = {}
        for doc in documents:
            author = doc.metadata.author or 'Unknown'
            author_counts[author] = author_counts.get(author, 0) + 1
        return author_counts
