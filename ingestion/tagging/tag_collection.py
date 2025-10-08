"""
Tag collection with breakdown by type.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set
from enum import Enum


class TagType(Enum):
    """Type of tag."""
    DEFAULT = "default"         # Built-in tags (source, file_type, etc.)
    CONTEXTUAL = "contextual"   # From corpus analysis
    USER_DEFINED = "user_defined"  # Manually added
    HIERARCHICAL = "hierarchical"  # From AI topic extraction


@dataclass
class TagCollection:
    """
    Complete tag collection for a corpus.
    
    Tracks tags by their source/type to provide transparency about
    where tags come from and enable filtering.
    """
    
    default_tags: List[str] = field(default_factory=list)
    contextual_tags: List[str] = field(default_factory=list)
    user_defined_tags: List[str] = field(default_factory=list)
    hierarchical_tags: List[str] = field(default_factory=list)  # AI-generated topic hierarchy
    
    def all_tags(self) -> List[str]:
        """
        Get all tags combined.
        
        Returns:
            Combined list of all tags from all sources
        """
        return self.default_tags + self.contextual_tags + self.user_defined_tags + self.hierarchical_tags
    
    def unique_tags(self) -> Set[str]:
        """
        Get set of unique tags.
        
        Returns:
            Set of all unique tags
        """
        return set(self.all_tags())
    
    def total_count(self) -> int:
        """
        Total number of unique tags.
        
        Returns:
            Count of unique tags across all types
        """
        return len(self.unique_tags())
    
    def breakdown(self) -> Dict[str, int]:
        """
        Tag count by type.
        
        Returns:
            Dictionary with counts: {default: N, contextual: N, user_defined: N, total: N}
        """
        return {
            "default": len(set(self.default_tags)),
            "contextual": len(set(self.contextual_tags)),
            "user_defined": len(set(self.user_defined_tags)),
            "hierarchical": len(set(self.hierarchical_tags)),
            "total": self.total_count()
        }
    
    def tags_by_prefix(self) -> Dict[str, List[str]]:
        """
        Group tags by their prefix.
        
        Returns:
            Dictionary mapping prefix to list of tags
            Example: {"source": ["source:github", "source:jira"], ...}
        """
        prefix_map = {}
        
        for tag in self.unique_tags():
            if ':' in tag:
                prefix = tag.split(':', 1)[0]
                if prefix not in prefix_map:
                    prefix_map[prefix] = []
                prefix_map[prefix].append(tag)
            else:
                # Tags without prefix go to "other"
                if "other" not in prefix_map:
                    prefix_map["other"] = []
                prefix_map["other"].append(tag)
        
        return prefix_map
    
    def filter_by_type(self, tag_type: TagType) -> List[str]:
        """
        Get tags of a specific type.
        
        Args:
            tag_type: Type of tags to retrieve
        
        Returns:
            List of tags of the specified type
        """
        if tag_type == TagType.DEFAULT:
            return list(set(self.default_tags))
        elif tag_type == TagType.CONTEXTUAL:
            return list(set(self.contextual_tags))
        elif tag_type == TagType.USER_DEFINED:
            return list(set(self.user_defined_tags))
        elif tag_type == TagType.HIERARCHICAL:
            return list(set(self.hierarchical_tags))
        else:
            return []
    
    def filter_by_prefix(self, prefix: str) -> List[str]:
        """
        Get tags with a specific prefix.
        
        Args:
            prefix: Tag prefix to filter by (e.g., "source", "topic")
        
        Returns:
            List of tags with the specified prefix
        """
        return [tag for tag in self.unique_tags() if tag.startswith(f"{prefix}:")]
    
    def add_tags(self, tags: List[str], tag_type: TagType):
        """
        Add tags to collection.
        
        Args:
            tags: List of tags to add
            tag_type: Type of tags being added
        """
        if tag_type == TagType.DEFAULT:
            self.default_tags.extend(tags)
        elif tag_type == TagType.CONTEXTUAL:
            self.contextual_tags.extend(tags)
        elif tag_type == TagType.USER_DEFINED:
            self.user_defined_tags.extend(tags)
        elif tag_type == TagType.HIERARCHICAL:
            self.hierarchical_tags.extend(tags)
    
    def merge(self, other: 'TagCollection'):
        """
        Merge another TagCollection into this one.
        
        Args:
            other: TagCollection to merge
        """
        self.default_tags.extend(other.default_tags)
        self.contextual_tags.extend(other.contextual_tags)
        self.user_defined_tags.extend(other.user_defined_tags)
        self.hierarchical_tags.extend(other.hierarchical_tags)
    
    def deduplicate(self):
        """Remove duplicate tags within each type."""
        self.default_tags = list(set(self.default_tags))
        self.contextual_tags = list(set(self.contextual_tags))
        self.user_defined_tags = list(set(self.user_defined_tags))
        self.hierarchical_tags = list(set(self.hierarchical_tags))
    
    def to_dict(self) -> Dict:
        """
        Export to dictionary.
        
        Returns:
            Dictionary representation with breakdown and all tags
        """
        return {
            "default": list(set(self.default_tags)),
            "contextual": list(set(self.contextual_tags)),
            "user_defined": list(set(self.user_defined_tags)),
            "hierarchical": list(set(self.hierarchical_tags)),
            "breakdown": self.breakdown(),
            "by_prefix": self.tags_by_prefix()
        }
    
    def to_summary(self) -> str:
        """
        Create human-readable summary.
        
        Returns:
            Multi-line string summary of tag collection
        """
        breakdown = self.breakdown()
        lines = [
            f"Tag Collection Summary:",
            f"  Total unique tags: {breakdown['total']}",
            f"  Default tags: {breakdown['default']}",
            f"  Contextual tags: {breakdown['contextual']}",
            f"  User-defined tags: {breakdown['user_defined']}",
            f"  Hierarchical tags: {breakdown['hierarchical']}",
            f"",
            f"Tag prefixes:"
        ]
        
        for prefix, tags in sorted(self.tags_by_prefix().items()):
            lines.append(f"  {prefix}: {len(tags)} tags")
        
        return "\n".join(lines)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TagCollection':
        """
        Create TagCollection from dictionary.
        
        Args:
            data: Dictionary with default, contextual, user_defined keys
        
        Returns:
            New TagCollection instance
        """
        return cls(
            default_tags=data.get('default', []),
            contextual_tags=data.get('contextual', []),
            user_defined_tags=data.get('user_defined', []),
            hierarchical_tags=data.get('hierarchical', [])
        )
    
    @classmethod
    def empty(cls) -> 'TagCollection':
        """
        Create empty TagCollection.
        
        Returns:
            New empty TagCollection
        """
        return cls(
            default_tags=[],
            contextual_tags=[],
            user_defined_tags=[],
            hierarchical_tags=[]
        )

