"""Tag Extractor Domain Service."""

from typing import List, Dict, Any
import re

from ..entities.llm_metadata import LLMMetadata
from ..value_objects.tag_validation_rules import TagValidationRules


class TagExtractorService:
    """
    Domain service for extracting and validating tags.
    
    Provides business logic for tag extraction, cleaning, and validation.
    """
    
    def __init__(self, validation_rules: TagValidationRules = None):
        """
        Initialize service.
        
        Args:
            validation_rules: Tag validation rules (uses defaults if None)
        """
        self.validation_rules = validation_rules or TagValidationRules()
    
    def extract_keywords_from_text(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        Extract keywords from text using simple heuristics.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords
            
        Returns:
            List of extracted keywords
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and split
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Count word frequency
        word_freq: Dict[str, int] = {}
        for word in words:
            if word not in self.validation_rules.blocked_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and take top N
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in keywords[:max_keywords]]
        
        # Validate and filter
        validated_keywords = []
        for keyword in keywords:
            is_valid, _ = self.validation_rules.validate_keyword(keyword)
            if is_valid:
                validated_keywords.append(keyword)
        
        return validated_keywords
    
    def clean_tags(self, tags: List[str]) -> List[str]:
        """
        Clean and normalize tags.
        
        Args:
            tags: Raw tags
            
        Returns:
            Cleaned tags
        """
        cleaned = []
        seen = set()
        
        for tag in tags:
            # Clean tag
            tag = tag.strip().lower()
            tag = re.sub(r'[^a-z0-9-_]', '-', tag)
            tag = re.sub(r'-+', '-', tag)
            tag = tag.strip('-')
            
            # Validate and deduplicate
            if tag and tag not in seen:
                is_valid, _ = self.validation_rules.validate_tag(tag)
                if is_valid:
                    cleaned.append(tag)
                    seen.add(tag)
        
        return cleaned
    
    def clean_keywords(self, keywords: List[str]) -> List[str]:
        """
        Clean and normalize keywords.
        
        Args:
            keywords: Raw keywords
            
        Returns:
            Cleaned keywords
        """
        cleaned = []
        seen = set()
        
        for keyword in keywords:
            # Clean keyword
            keyword = keyword.strip().lower()
            keyword = re.sub(r'\s+', ' ', keyword)
            
            # Validate and deduplicate
            if keyword and keyword not in seen:
                is_valid, _ = self.validation_rules.validate_keyword(keyword)
                if is_valid:
                    cleaned.append(keyword)
                    seen.add(keyword)
        
        return cleaned
    
    def clean_categories(self, categories: List[str]) -> List[str]:
        """
        Clean and normalize categories.
        
        Args:
            categories: Raw categories
            
        Returns:
            Cleaned categories
        """
        cleaned = []
        seen = set()
        
        for category in categories:
            # Clean category
            category = category.strip().lower()
            category = ' '.join(category.split())
            
            # Validate and deduplicate
            if category and category not in seen:
                is_valid, _ = self.validation_rules.validate_category(category)
                if is_valid:
                    cleaned.append(category)
                    seen.add(category)
        
        return cleaned
    
    def validate_metadata(self, metadata: LLMMetadata) -> tuple[bool, List[str]]:
        """
        Validate LLM metadata.
        
        Args:
            metadata: Metadata to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate summary
        if metadata.summary:
            is_valid, error = self.validation_rules.validate_summary(metadata.summary)
            if not is_valid:
                errors.append(f"Summary: {error}")
        else:
            errors.append("Summary is required")
        
        # Validate keywords
        if metadata.keywords:
            is_valid, error = self.validation_rules.validate_keywords_list(metadata.keywords)
            if not is_valid:
                errors.append(f"Keywords: {error}")
        else:
            errors.append("Keywords are required")
        
        # Validate tags
        if metadata.tags:
            is_valid, error = self.validation_rules.validate_tags_list(metadata.tags)
            if not is_valid:
                errors.append(f"Tags: {error}")
        
        # Check confidence scores
        if metadata.get_overall_confidence() < 0.5:
            errors.append(f"Overall confidence too low: {metadata.get_overall_confidence():.2f}")
        
        return len(errors) == 0, errors
    
    def merge_metadata(
        self,
        metadata1: LLMMetadata,
        metadata2: LLMMetadata
    ) -> LLMMetadata:
        """
        Merge two metadata objects.
        
        Args:
            metadata1: First metadata
            metadata2: Second metadata
            
        Returns:
            Merged metadata
        """
        # Use the metadata with higher confidence for summary
        summary = (
            metadata1.summary
            if metadata1.summary_confidence >= metadata2.summary_confidence
            else metadata2.summary
        )
        
        # Merge and deduplicate lists
        keywords = list(set(metadata1.keywords + metadata2.keywords))
        tags = list(set(metadata1.tags + metadata2.tags))
        categories = list(set(metadata1.categories + metadata2.categories))
        topics = list(set(metadata1.topics + metadata2.topics))
        entities = metadata1.entities + metadata2.entities
        
        # Average confidence scores
        summary_confidence = (metadata1.summary_confidence + metadata2.summary_confidence) / 2
        keywords_confidence = (metadata1.keywords_confidence + metadata2.keywords_confidence) / 2
        tags_confidence = (metadata1.tags_confidence + metadata2.tags_confidence) / 2
        categories_confidence = (metadata1.categories_confidence + metadata2.categories_confidence) / 2
        
        return LLMMetadata(
            summary=summary,
            keywords=keywords[:20],  # Limit to top 20
            tags=tags[:15],  # Limit to top 15
            categories=categories[:5],  # Limit to top 5
            topics=topics,
            entities=entities,
            sentiment=metadata1.sentiment or metadata2.sentiment,
            complexity_score=metadata1.complexity_score or metadata2.complexity_score,
            summary_confidence=summary_confidence,
            keywords_confidence=keywords_confidence,
            tags_confidence=tags_confidence,
            categories_confidence=categories_confidence,
            model_name=f"{metadata1.model_name}+{metadata2.model_name}",
            tokens_used=metadata1.tokens_used + metadata2.tokens_used,
            processing_time_seconds=metadata1.processing_time_seconds + metadata2.processing_time_seconds,
        )

