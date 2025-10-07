"""Documentation Application Service."""

from typing import List, Optional

from ...domain.entities.documentation import Documentation
from ...domain.repositories.documentation_repository import DocumentationRepository


class DocumentationService:
    """
    Application service for documentation management.
    
    Handles CRUD operations and business logic for documentation.
    """
    
    def __init__(self, doc_repo: DocumentationRepository):
        """
        Initialize documentation service.
        
        Args:
            doc_repo: Documentation repository
        """
        self.doc_repo = doc_repo
    
    async def create_documentation(
        self,
        title: str,
        file_path: str,
        content: str,
        format: str = "markdown",
        source_type: str = "manual",
        **kwargs,
    ) -> Documentation:
        """
        Create new documentation.
        
        Args:
            title: Document title
            file_path: File path
            content: Document content
            format: Content format
            source_type: Source type
            **kwargs: Additional attributes
            
        Returns:
            Created documentation
        """
        doc = Documentation(
            title=title,
            file_path=file_path,
            content=content,
            format=format,
            source_type=source_type,
            **kwargs,
        )
        
        # Calculate checksum
        doc.calculate_checksum()
        
        # Validate
        doc.validate()
        
        await self.doc_repo.add(doc)
        return doc
    
    async def get_documentation(self, doc_id: str) -> Optional[Documentation]:
        """
        Get documentation by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Documentation or None
        """
        return await self.doc_repo.get_by_id(doc_id)
    
    async def update_documentation(
        self,
        doc_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Documentation:
        """
        Update documentation.
        
        Args:
            doc_id: Document ID
            content: New content
            title: New title
            tags: New tags
            
        Returns:
            Updated documentation
            
        Raises:
            ValueError: If document not found
        """
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc:
            raise ValueError(f"Documentation not found: {doc_id}")
        
        # Update fields
        if content is not None:
            doc.content = content
            doc.calculate_checksum()
            doc.increment_version()
        
        if title is not None:
            doc.title = title
        
        if tags is not None:
            doc.tags = tags
        
        # Validate
        doc.validate()
        
        await self.doc_repo.update(doc)
        return doc
    
    async def delete_documentation(self, doc_id: str) -> None:
        """
        Delete documentation.
        
        Args:
            doc_id: Document ID
        """
        await self.doc_repo.delete(doc_id)
    
    async def list_documentation(self) -> List[Documentation]:
        """
        List all documentation.
        
        Returns:
            List of documentation
        """
        return await self.doc_repo.list_all()
    
    async def find_by_tags(self, tags: List[str]) -> List[Documentation]:
        """
        Find documentation by tags.
        
        Args:
            tags: Tags to search for
            
        Returns:
            List of matching documentation
        """
        return await self.doc_repo.find_by_tags(tags)
    
    async def find_outdated(self) -> List[Documentation]:
        """
        Find outdated documentation.
        
        Returns:
            List of outdated documentation
        """
        return await self.doc_repo.find_outdated()

