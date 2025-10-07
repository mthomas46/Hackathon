"""Tag Validation Rules Value Object."""

from dataclasses import dataclass
from typing import List, Set


@dataclass(frozen=True)
class TagValidationRules:
    """
    Tag validation rules value object.
    
    Defines validation rules for tags, keywords, and categories.
    """
    
    # Length constraints
    min_keyword_length: int = 3
    max_keyword_length: int = 50
    min_tag_length: int = 2
    max_tag_length: int = 30
    min_category_length: int = 3
    max_category_length: int = 50
    
    # Count constraints
    min_keywords: int = 3
    max_keywords: int = 20
    min_tags: int = 2
    max_tags: int = 15
    min_categories: int = 1
    max_categories: int = 5
    
    # Summary constraints
    min_summary_length: int = 50
    max_summary_length: int = 500
    
    # Allowed characters
    allowed_tag_chars: str = "abcdefghijklmnopqrstuvwxyz0-9-_"
    
    # Blocked words (common words to exclude)
    blocked_words: Set[str] = None
    
    def __post_init__(self):
        """Initialize blocked words."""
        if self.blocked_words is None:
            # Common stop words to exclude
            object.__setattr__(self, 'blocked_words', {
                "the", "a", "an", "and", "or", "but", "in", "on", "at",
                "to", "for", "of", "with", "by", "from", "this", "that",
            })
    
    def validate_keyword(self, keyword: str) -> tuple[bool, str]:
        """
        Validate a keyword.
        
        Args:
            keyword: Keyword to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        keyword = keyword.strip().lower()
        
        if not keyword:
            return False, "Keyword cannot be empty"
        
        if len(keyword) < self.min_keyword_length:
            return False, f"Keyword too short (min {self.min_keyword_length} chars)"
        
        if len(keyword) > self.max_keyword_length:
            return False, f"Keyword too long (max {self.max_keyword_length} chars)"
        
        if keyword in self.blocked_words:
            return False, f"Keyword '{keyword}' is a blocked word"
        
        return True, ""
    
    def validate_tag(self, tag: str) -> tuple[bool, str]:
        """
        Validate a tag.
        
        Args:
            tag: Tag to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        tag = tag.strip().lower()
        
        if not tag:
            return False, "Tag cannot be empty"
        
        if len(tag) < self.min_tag_length:
            return False, f"Tag too short (min {self.min_tag_length} chars)"
        
        if len(tag) > self.max_tag_length:
            return False, f"Tag too long (max {self.max_tag_length} chars)"
        
        # Check allowed characters
        if not all(c in self.allowed_tag_chars for c in tag):
            return False, "Tag contains invalid characters"
        
        return True, ""
    
    def validate_category(self, category: str) -> tuple[bool, str]:
        """
        Validate a category.
        
        Args:
            category: Category to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        category = category.strip().lower()
        
        if not category:
            return False, "Category cannot be empty"
        
        if len(category) < self.min_category_length:
            return False, f"Category too short (min {self.min_category_length} chars)"
        
        if len(category) > self.max_category_length:
            return False, f"Category too long (max {self.max_category_length} chars)"
        
        return True, ""
    
    def validate_summary(self, summary: str) -> tuple[bool, str]:
        """
        Validate a summary.
        
        Args:
            summary: Summary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        summary = summary.strip()
        
        if not summary:
            return False, "Summary cannot be empty"
        
        if len(summary) < self.min_summary_length:
            return False, f"Summary too short (min {self.min_summary_length} chars)"
        
        if len(summary) > self.max_summary_length:
            return False, f"Summary too long (max {self.max_summary_length} chars)"
        
        return True, ""
    
    def validate_keywords_list(self, keywords: List[str]) -> tuple[bool, str]:
        """
        Validate list of keywords.
        
        Args:
            keywords: List of keywords
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(keywords) < self.min_keywords:
            return False, f"Too few keywords (min {self.min_keywords})"
        
        if len(keywords) > self.max_keywords:
            return False, f"Too many keywords (max {self.max_keywords})"
        
        return True, ""
    
    def validate_tags_list(self, tags: List[str]) -> tuple[bool, str]:
        """
        Validate list of tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(tags) < self.min_tags:
            return False, f"Too few tags (min {self.min_tags})"
        
        if len(tags) > self.max_tags:
            return False, f"Too many tags (max {self.max_tags})"
        
        return True, ""

