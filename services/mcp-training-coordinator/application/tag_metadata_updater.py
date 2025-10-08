"""
Tag metadata updater for MCP instances.

This module updates MCP metadata with tag collection information
after documents are ingested and tagged.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TagMetadataUpdater:
    """Updates MCP metadata with tag collection information."""
    
    @staticmethod
    def create_tag_metadata(
        default_tags: list,
        contextual_tags: list,
        user_defined_tags: list
    ) -> Dict[str, Any]:
        """
        Create tag metadata dictionary for MCP storage.
        
        Args:
            default_tags: List of default tags
            contextual_tags: List of contextual (NLP-derived) tags
            user_defined_tags: List of user-defined tags
        
        Returns:
            Dictionary with complete tag collection metadata
        """
        total_count = len(set(default_tags + contextual_tags + user_defined_tags))
        
        return {
            "default_tags": list(set(default_tags)),
            "contextual_tags": list(set(contextual_tags)),
            "user_defined_tags": list(user_defined_tags),
            "total_count": total_count,
            "breakdown": {
                "default": len(set(default_tags)),
                "contextual": len(set(contextual_tags)),
                "user_defined": len(user_defined_tags),
                "total": total_count
            },
            "last_updated": datetime.utcnow().isoformat(),
            "statistics": {
                "unique_default": len(set(default_tags)),
                "unique_contextual": len(set(contextual_tags)),
                "unique_user_defined": len(user_defined_tags),
                "total_unique": total_count
            }
        }
    
    @staticmethod
    def merge_tag_metadata(
        existing_metadata: Dict[str, Any],
        new_tags: Dict[str, list]
    ) -> Dict[str, Any]:
        """
        Merge new tags into existing tag metadata.
        
        Args:
            existing_metadata: Existing tag collection metadata
            new_tags: New tags to merge (keys: default_tags, contextual_tags, user_defined_tags)
        
        Returns:
            Updated tag metadata
        """
        # Get existing tags
        default_tags = set(existing_metadata.get("default_tags", []))
        contextual_tags = set(existing_metadata.get("contextual_tags", []))
        user_defined_tags = set(existing_metadata.get("user_defined_tags", []))
        
        # Merge new tags
        default_tags.update(new_tags.get("default_tags", []))
        contextual_tags.update(new_tags.get("contextual_tags", []))
        user_defined_tags.update(new_tags.get("user_defined_tags", []))
        
        # Create updated metadata
        return TagMetadataUpdater.create_tag_metadata(
            list(default_tags),
            list(contextual_tags),
            list(user_defined_tags)
        )
    
    @staticmethod
    def extract_tag_collection(documents: list) -> Dict[str, list]:
        """
        Extract tag collection from a list of documents.
        
        Args:
            documents: List of documents with tags
        
        Returns:
            Dictionary with categorized tags
        """
        default_tags = []
        contextual_tags = []
        user_defined_tags = []
        
        # Define tag prefixes for categorization
        default_prefixes = ['source:', 'file_type:', 'has_', 'language:']
        contextual_prefixes = ['character:', 'faction:', 'location:', 'event:', 'topic:']
        
        for doc in documents:
            doc_tags = doc.get('tags', []) if isinstance(doc, dict) else getattr(doc, 'tags', [])
            
            for tag in doc_tags:
                # Categorize tag
                if any(tag.startswith(prefix) for prefix in default_prefixes):
                    default_tags.append(tag)
                elif any(tag.startswith(prefix) for prefix in contextual_prefixes):
                    contextual_tags.append(tag)
                elif ':' in tag and not tag.startswith(tuple(default_prefixes + contextual_prefixes)):
                    # Assume user-defined if it has a prefix we don't recognize
                    user_defined_tags.append(tag)
                else:
                    # Default to contextual for unrecognized tags
                    contextual_tags.append(tag)
        
        return {
            "default_tags": default_tags,
            "contextual_tags": contextual_tags,
            "user_defined_tags": user_defined_tags
        }
    
    @staticmethod
    def get_tag_summary(tag_metadata: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of tag metadata.
        
        Args:
            tag_metadata: Tag collection metadata
        
        Returns:
            Formatted summary string
        """
        breakdown = tag_metadata.get("breakdown", {})
        total = breakdown.get("total", 0)
        
        summary = f"""Tag Collection Summary:
- Total Unique Tags: {total}
- Default Tags: {breakdown.get('default', 0)}
- Contextual Tags: {breakdown.get('contextual', 0)}
- User-Defined Tags: {breakdown.get('user_defined', 0)}
- Last Updated: {tag_metadata.get('last_updated', 'Never')}
"""
        return summary
    
    @staticmethod
    def validate_tag_metadata(tag_metadata: Dict[str, Any]) -> bool:
        """
        Validate tag metadata structure.
        
        Args:
            tag_metadata: Tag metadata to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['default_tags', 'contextual_tags', 'user_defined_tags', 'breakdown']
        
        if not all(key in tag_metadata for key in required_keys):
            return False
        
        if not isinstance(tag_metadata['breakdown'], dict):
            return False
        
        breakdown_keys = ['default', 'contextual', 'user_defined', 'total']
        if not all(key in tag_metadata['breakdown'] for key in breakdown_keys):
            return False
        
        return True

