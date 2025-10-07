"""Validation Application Service."""

from typing import Optional
import re

from ...domain.entities.documentation import Documentation
from ...domain.entities.validation_result import ValidationResult
from ...domain.repositories.validation_repository import ValidationRepository


class ValidationService:
    """
    Application service for documentation validation.
    
    Validates documentation content and structure.
    """
    
    def __init__(self, validation_repo: ValidationRepository):
        """
        Initialize validation service.
        
        Args:
            validation_repo: Validation repository
        """
        self.validation_repo = validation_repo
    
    async def validate_documentation(self, doc: Documentation) -> ValidationResult:
        """
        Validate documentation.
        
        Args:
            doc: Documentation to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult(doc_id=doc.doc_id)
        
        # Perform validation checks
        self._check_content_length(doc, result)
        self._check_structure(doc, result)
        self._check_links(doc, result)
        self._check_headings(doc, result)
        self._check_formatting(doc, result)
        
        # Calculate metrics
        result.content_length = len(doc.content)
        result.word_count = len(doc.content.split())
        
        # Calculate score
        result.calculate_score()
        
        # Save result
        await self.validation_repo.add(result)
        
        return result
    
    def _check_content_length(self, doc: Documentation, result: ValidationResult) -> None:
        """Check content length."""
        check_name = "content_length"
        
        if not doc.content:
            result.add_error("Documentation has no content", rule=check_name)
            result.mark_check_failed(check_name)
        elif len(doc.content) < 100:
            result.add_warning("Documentation is very short (< 100 chars)", rule=check_name)
            result.mark_check_passed(check_name)
        else:
            result.mark_check_passed(check_name)
    
    def _check_structure(self, doc: Documentation, result: ValidationResult) -> None:
        """Check document structure."""
        check_name = "structure"
        
        if doc.format == "markdown":
            # Check for at least one heading
            if not re.search(r'^#+\s+', doc.content, re.MULTILINE):
                result.add_warning("No headings found in markdown document", rule=check_name)
                result.mark_check_failed(check_name)
            else:
                result.mark_check_passed(check_name)
        else:
            result.mark_check_passed(check_name)
    
    def _check_links(self, doc: Documentation, result: ValidationResult) -> None:
        """Check links in documentation."""
        check_name = "links"
        
        if doc.format == "markdown":
            # Find all markdown links
            links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', doc.content)
            result.link_count = len(links)
            
            # Basic link validation (could be enhanced)
            for text, url in links:
                if not url:
                    result.add_error(f"Empty link URL for text: {text}", rule=check_name)
                    result.broken_links += 1
            
            if result.broken_links > 0:
                result.mark_check_failed(check_name)
            else:
                result.mark_check_passed(check_name)
        else:
            result.mark_check_passed(check_name)
    
    def _check_headings(self, doc: Documentation, result: ValidationResult) -> None:
        """Check heading structure."""
        check_name = "headings"
        
        if doc.format == "markdown":
            # Find all headings
            headings = re.findall(r'^(#+)\s+(.+)$', doc.content, re.MULTILINE)
            result.heading_count = len(headings)
            
            if headings:
                # Check for H1
                if not any(len(level) == 1 for level, _ in headings):
                    result.add_warning("No H1 heading found", rule=check_name)
                
                # Check heading hierarchy
                prev_level = 0
                for level, text in headings:
                    current_level = len(level)
                    if current_level > prev_level + 1:
                        result.add_warning(
                            f"Heading hierarchy skip: {prev_level} to {current_level}",
                            rule=check_name,
                        )
                    prev_level = current_level
            
            result.mark_check_passed(check_name)
        else:
            result.mark_check_passed(check_name)
    
    def _check_formatting(self, doc: Documentation, result: ValidationResult) -> None:
        """Check formatting issues."""
        check_name = "formatting"
        
        # Check for trailing whitespace
        lines_with_trailing = sum(
            1 for line in doc.content.split('\n') if line.rstrip() != line
        )
        if lines_with_trailing > 0:
            result.add_suggestion(
                f"{lines_with_trailing} lines have trailing whitespace",
                suggestion="Remove trailing whitespace",
            )
        
        # Check for multiple blank lines
        if '\n\n\n' in doc.content:
            result.add_suggestion(
                "Multiple consecutive blank lines found",
                suggestion="Use single blank lines for separation",
            )
        
        result.mark_check_passed(check_name)
    
    async def get_latest_validation(self, doc_id: str) -> Optional[ValidationResult]:
        """
        Get latest validation result for document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Latest validation result or None
        """
        return await self.validation_repo.get_latest_by_doc(doc_id)

