"""
Metadata extractor for enriching documents with searchable metadata.

Extracts topics, tags, references, and other metadata from documents.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any

from ..models.document import DocumentMetadata

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts rich metadata from documents.
    
    Analyzes content to determine:
    - Service name
    - Phase information
    - Topics and tags
    - Code snippets count
    - Diagrams presence
    - Word count
    - References to other services/files
    """
    
    # Common topics to detect
    TOPICS = [
        "api", "endpoints", "testing", "documentation", "deployment",
        "configuration", "database", "redis", "docker", "kubernetes",
        "authentication", "authorization", "logging", "monitoring",
        "performance", "security", "architecture", "refactoring",
        "migration", "integration", "validation", "error-handling"
    ]
    
    def extract(
        self,
        file_path: Path,
        content: str,
        normalized_content: str,
        parsed_metadata: Dict[str, Any],
        service_name: str
    ) -> DocumentMetadata:
        """
        Extract comprehensive metadata from document.
        
        Args:
            file_path: Path to file
            content: Original content
            normalized_content: Normalized markdown content
            parsed_metadata: Metadata from parser
            service_name: Service name
        
        Returns:
            DocumentMetadata instance
        """
        # Extract phase from file path or content
        phase = self._extract_phase(file_path, content)
        
        # Extract topics
        topics = self._extract_topics(normalized_content)
        
        # Count code snippets
        code_snippets = normalized_content.count("```")
        
        # Detect diagrams
        has_diagrams = self._has_diagrams(normalized_content)
        
        # Word count (approximate)
        word_count = len(normalized_content.split())
        
        # Determine language for code files
        language = self._determine_language(file_path)
        
        # Extract references to other services/files
        references = self._extract_references(content)
        
        # Generate tags
        tags = self._generate_tags(file_path, topics, phase)
        
        return DocumentMetadata(
            service_name=service_name,
            phase=phase,
            topics=topics,
            code_snippets=code_snippets,
            has_diagrams=has_diagrams,
            word_count=word_count,
            language=language,
            file_type=file_path.suffix.lstrip("."),
            tags=tags,
            references=references,
            extra=parsed_metadata
        )
    
    def _extract_phase(self, file_path: Path, content: str) -> str | None:
        """Extract phase information."""
        # Check filename for phase pattern
        filename = file_path.name.lower()
        phase_pattern = r"phase[_\s-]?(\d+)"
        match = re.search(phase_pattern, filename)
        if match:
            return f"Phase {match.group(1)}"
        
        # Check content for phase markers
        content_lower = content.lower()
        for i in range(1, 12):  # Phases 1-11
            if f"phase {i}" in content_lower or f"phase_{i}" in content_lower:
                return f"Phase {i}"
        
        return None
    
    def _extract_topics(self, content: str) -> list[str]:
        """Extract relevant topics from content."""
        content_lower = content.lower()
        found_topics = []
        
        for topic in self.TOPICS:
            # Look for topic as whole word
            pattern = r"\b" + re.escape(topic) + r"\b"
            if re.search(pattern, content_lower):
                found_topics.append(topic)
        
        return found_topics[:10]  # Limit to 10 topics
    
    def _has_diagrams(self, content: str) -> bool:
        """Detect if document contains diagrams."""
        diagram_indicators = [
            "```mermaid",
            "```diagram",
            "┌─", "└─", "├─", "│",  # ASCII art boxes
            "flowchart",
            "graph TD",
            "graph LR"
        ]
        
        for indicator in diagram_indicators:
            if indicator in content:
                return True
        
        return False
    
    def _determine_language(self, file_path: Path) -> str | None:
        """Determine programming language."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php"
        }
        
        return extension_map.get(file_path.suffix.lower())
    
    def _extract_references(self, content: str) -> list[str]:
        """Extract references to other services/files."""
        references = []
        
        # Look for service references
        service_pattern = r"services/([a-z0-9-]+)"
        matches = re.findall(service_pattern, content)
        references.extend(matches)
        
        # Look for file references
        file_pattern = r"`([a-zA-Z0-9_/-]+\.[a-z]+)`"
        matches = re.findall(file_pattern, content)
        references.extend(matches)
        
        # Deduplicate and limit
        unique_refs = list(set(references))
        return unique_refs[:20]
    
    def _generate_tags(
        self,
        file_path: Path,
        topics: list[str],
        phase: str | None
    ) -> list[str]:
        """Generate tags for the document."""
        tags = []
        
        # Add file type tag
        file_type = file_path.suffix.lstrip(".")
        if file_type:
            tags.append(file_type)
        
        # Add phase tag
        if phase:
            tags.append(phase.lower().replace(" ", "-"))
        
        # Add top topics as tags
        tags.extend(topics[:5])
        
        # Add document type tags
        filename_lower = file_path.name.lower()
        if "readme" in filename_lower:
            tags.append("readme")
        if "test" in filename_lower:
            tags.append("test")
        if "config" in filename_lower:
            tags.append("config")
        
        return list(set(tags))  # Deduplicate

