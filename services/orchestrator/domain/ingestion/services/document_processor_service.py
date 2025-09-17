"""Document Processor Service Domain Service"""

from typing import Dict, Any, Optional, List
import hashlib
from datetime import datetime

from ..value_objects.document_metadata import DocumentMetadata
from ..value_objects.ingestion_source_type import IngestionSourceType


class DocumentProcessorService:
    """Domain service for processing ingested documents."""

    def __init__(self):
        """Initialize document processor service."""
        self._supported_formats = {
            'text/plain': ['.txt', '.rst'],
            'text/markdown': ['.md'],
            'text/html': ['.html', '.htm'],
            'application/json': ['.json'],
            'application/xml': ['.xml'],
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
        }

    def extract_metadata(
        self,
        document_id: str,
        source_url: str,
        raw_content: bytes,
        source_type: IngestionSourceType,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentMetadata:
        """
        Extract metadata from document content.

        Args:
            document_id: Unique document identifier
            source_url: Source URL of the document
            raw_content: Raw document content as bytes
            source_type: Type of ingestion source
            additional_metadata: Additional metadata from ingestion

        Returns:
            DocumentMetadata: Extracted document metadata
        """
        # Calculate checksum
        checksum = hashlib.sha256(raw_content).hexdigest()

        # Determine content type
        content_type = self._detect_content_type(source_url, raw_content)

        # Extract title if possible
        title = self._extract_title(raw_content, content_type, source_url)

        # Extract timestamps
        last_modified, created_at = self._extract_timestamps(additional_metadata or {})

        # Extract author
        author = self._extract_author(additional_metadata or {})

        # Generate tags
        tags = self._generate_tags(source_type, content_type, additional_metadata or {})

        return DocumentMetadata(
            document_id=document_id,
            source_url=source_url,
            title=title,
            content_type=content_type,
            file_size=len(raw_content),
            checksum=checksum,
            last_modified=last_modified,
            created_at=created_at,
            author=author,
            tags=tags,
            custom_metadata=additional_metadata or {}
        )

    def _detect_content_type(self, source_url: str, raw_content: bytes) -> str:
        """Detect the content type of the document."""
        # Check file extension first
        for content_type, extensions in self._supported_formats.items():
            for ext in extensions:
                if source_url.lower().endswith(ext):
                    return content_type

        # Try to detect from content
        try:
            content_str = raw_content[:100].decode('utf-8', errors='ignore').lower()

            if content_str.startswith('<?xml'):
                return 'application/xml'
            elif content_str.startswith('{') or content_str.startswith('['):
                return 'application/json'
            elif '<html' in content_str or '<!doctype html' in content_str:
                return 'text/html'
            elif content_str.startswith('%pdf'):
                return 'application/pdf'

        except UnicodeDecodeError:
            pass

        # Default to plain text
        return 'text/plain'

    def _extract_title(self, raw_content: bytes, content_type: str, source_url: str) -> Optional[str]:
        """Extract document title from content."""
        try:
            if content_type == 'text/html':
                content_str = raw_content.decode('utf-8', errors='ignore')
                # Look for title tag
                import re
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', content_str, re.IGNORECASE)
                if title_match:
                    return title_match.group(1).strip()

            elif content_type in ['text/plain', 'text/markdown']:
                content_str = raw_content.decode('utf-8', errors='ignore')
                lines = content_str.split('\n', 10)  # First 10 lines

                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10 and len(line) < 200:
                        # Look for lines that look like titles
                        if not line.startswith(('#', '-', '=', '1.', '*', '- ')):
                            return line

            # Fallback to filename from URL
            if '/' in source_url:
                filename = source_url.split('/')[-1]
                if '.' in filename:
                    return filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()

        except (UnicodeDecodeError, AttributeError):
            pass

        return None

    def _extract_timestamps(self, metadata: Dict[str, Any]) -> tuple[Optional[datetime], Optional[datetime]]:
        """Extract created and modified timestamps from metadata."""
        from datetime import datetime

        last_modified = None
        created_at = None

        # Look for common timestamp fields
        timestamp_fields = [
            'last_modified', 'modified_at', 'updated_at', 'last_updated',
            'created_at', 'created', 'date_created'
        ]

        for field in timestamp_fields:
            if field in metadata:
                value = metadata[field]
                if isinstance(value, str):
                    try:
                        # Try to parse ISO format
                        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        if 'modified' in field or 'updated' in field:
                            last_modified = parsed
                        else:
                            created_at = parsed
                    except ValueError:
                        pass
                elif isinstance(value, datetime):
                    if 'modified' in field or 'updated' in field:
                        last_modified = value
                    else:
                        created_at = value

        return last_modified, created_at

    def _extract_author(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract author information from metadata."""
        author_fields = ['author', 'creator', 'owner', 'user', 'submitted_by']

        for field in author_fields:
            if field in metadata:
                author = metadata[field]
                if isinstance(author, str) and author.strip():
                    return author.strip()

        return None

    def _generate_tags(self, source_type: IngestionSourceType, content_type: str, metadata: Dict[str, Any]) -> List[str]:
        """Generate tags for the document."""
        tags = []

        # Source type tags
        tags.append(f"source:{source_type.value}")

        # Content type tags
        if content_type.startswith('text/'):
            tags.append('content:text')
        elif content_type.startswith('application/'):
            tags.append('content:structured')

        # Size-based tags
        if 'size' in metadata:
            size = metadata['size']
            if isinstance(size, (int, float)):
                if size < 1024:
                    tags.append('size:small')
                elif size < 1024 * 1024:
                    tags.append('size:medium')
                else:
                    tags.append('size:large')

        # Custom tags from metadata
        if 'tags' in metadata and isinstance(metadata['tags'], list):
            tags.extend(metadata['tags'])

        return list(set(tags))  # Remove duplicates

    def validate_document(self, metadata: DocumentMetadata, content: bytes) -> Dict[str, Any]:
        """
        Validate a document and its metadata.

        Args:
            metadata: Document metadata
            content: Document content

        Returns:
            Dict: Validation results
        """
        issues = []

        # Check content integrity
        calculated_checksum = hashlib.sha256(content).hexdigest()
        if metadata.checksum and metadata.checksum != calculated_checksum:
            issues.append("Content checksum mismatch")

        # Check file size consistency
        if metadata.file_size and metadata.file_size != len(content):
            issues.append("File size mismatch")

        # Check content type validity
        if metadata.content_type not in self._supported_formats:
            issues.append(f"Unsupported content type: {metadata.content_type}")

        # Check required fields
        if not metadata.title and not metadata.document_id:
            issues.append("Missing title or document identifier")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': [],  # Could add warnings for non-critical issues
            'checksum_verified': metadata.checksum == calculated_checksum if metadata.checksum else None
        }

    def enrich_metadata(self, metadata: DocumentMetadata, additional_data: Dict[str, Any]) -> DocumentMetadata:
        """
        Enrich document metadata with additional information.

        Args:
            metadata: Existing document metadata
            additional_data: Additional data to enrich with

        Returns:
            DocumentMetadata: Enriched metadata
        """
        # Add enrichment timestamp
        metadata.set_custom_metadata('enriched_at', datetime.utcnow().isoformat())

        # Add any additional tags
        if 'tags' in additional_data:
            for tag in additional_data['tags']:
                metadata.add_tag(tag)

        # Add processing information
        if 'processing_info' in additional_data:
            metadata.set_custom_metadata('processing', additional_data['processing_info'])

        return metadata

    def categorize_document(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Categorize a document based on its metadata.

        Args:
            metadata: Document metadata

        Returns:
            Dict: Categorization information
        """
        categories = []

        # Content-based categorization
        if metadata.content_type == 'text/plain':
            categories.append('documentation')
        elif metadata.content_type == 'application/json':
            categories.append('data')
        elif metadata.content_type in ['application/pdf', 'application/msword']:
            categories.append('document')

        # Source-based categorization
        if 'github' in metadata.source_url.lower():
            categories.extend(['code', 'repository'])
        elif 'jira' in metadata.source_url.lower():
            categories.extend(['issue', 'tracking'])
        elif 'confluence' in metadata.source_url.lower():
            categories.extend(['wiki', 'knowledge'])

        # Size-based categorization
        if metadata.file_size:
            if metadata.file_size < 1024:
                categories.append('small')
            elif metadata.file_size > 1024 * 1024:
                categories.append('large')

        return {
            'primary_category': categories[0] if categories else 'unknown',
            'all_categories': categories,
            'confidence': min(0.9, 0.5 + len(categories) * 0.1)  # Higher confidence with more categories
        }
