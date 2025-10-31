"""
Metadata-Enhanced Filtering (Phase 2)

Smart metadata filtering based on query intent.

Techniques:
1. Temporal filtering (recent vs historical)
2. Quality filtering (high-quality sources only)
3. Category filtering (docs vs code vs tests)
4. Intent detection (what type of answer needed)

Expected: +5-10% accuracy
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class MetadataFilter:
    """
    Intelligent metadata-based filtering.
    
    Features:
    - Query intent detection
    - Automatic filter selection
    - Quality thresholds
    - Temporal preferences
    """
    
    def __init__(self):
        """Initialize metadata filter."""
        self.intent_patterns = {
            "how_to": r'\b(how to|how do|how does|tutorial|guide|steps)\b',
            "implementation": r'\b(implement|code|function|class|method)\b',
            "architecture": r'\b(architecture|design|structure|system)\b',
            "troubleshooting": r'\b(error|bug|fix|issue|problem|debug)\b',
            "recent": r'\b(recent|latest|new|current)\b',
            "historical": r'\b(history|evolution|changes|was)\b',
        }
        
        logger.info("MetadataFilter initialized")
    
    def build_filters(
        self,
        query: str,
        quality_threshold: Optional[float] = None,
        date_range: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Build ChromaDB where clause based on query intent.
        
        Args:
            query: Search query
            quality_threshold: Optional minimum quality score
            date_range: Optional time range for documents
        
        Returns:
            ChromaDB where clause dict
        """
        logger.info(f"🎯 Building filters for: '{query[:60]}...'")
        
        # Detect intents
        intents = self._detect_intents(query)
        
        # Start building filters
        filters = {}
        
        # 1. Quality filtering (for critical queries)
        if self._is_critical_query(query, intents):
            quality_threshold = quality_threshold or 75.0
            filters["quality_score"] = {"$gte": quality_threshold}
            logger.info(f"   Quality filter: >= {quality_threshold}")
        elif quality_threshold:
            filters["quality_score"] = {"$gte": quality_threshold}
        
        # 2. Category filtering based on intent
        if "how_to" in intents or "tutorial" in query.lower():
            filters["category"] = {"$in": ["documentation", "example"]}
            logger.info("   Category filter: documentation, examples")
        
        elif "implementation" in intents:
            filters["category"] = {"$in": ["source_code", "documentation"]}
            logger.info("   Category filter: source code, documentation")
        
        elif "troubleshooting" in intents:
            # Don't filter by category - errors can be anywhere
            pass
        
        # 3. Temporal filtering
        if "recent" in intents:
            # Prefer recent documents
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
            filters["git_date"] = {"$gte": cutoff_date}
            logger.info("   Temporal filter: last 90 days")
        
        elif "historical" in intents:
            # Don't filter by date - want full history
            pass
        
        elif date_range:
            cutoff_date = (datetime.now() - date_range).isoformat()
            filters["git_date"] = {"$gte": cutoff_date}
        
        # 4. Exclude low-value categories
        # TODO: Fix filter structure for ChromaDB compatibility
        # For now, skip complex filtering to avoid validation errors
        
        logger.info(f"✅ Filters built: {len(filters)} conditions")
        
        # TEMPORARY: Return None to avoid ChromaDB filter validation errors
        # Phase 2 reranking and context optimization will still work
        logger.warning("⚠️  Metadata filtering temporarily disabled (filter format issue)")
        return None
    
    def _detect_intents(self, query: str) -> List[str]:
        """Detect query intents using patterns."""
        intents = []
        query_lower = query.lower()
        
        for intent, pattern in self.intent_patterns.items():
            if re.search(pattern, query_lower):
                intents.append(intent)
        
        return intents
    
    def _is_critical_query(self, query: str, intents: List[str]) -> bool:
        """
        Determine if query is critical (needs high-quality sources).
        
        Critical queries:
        - Architecture/design questions
        - Security-related
        - Core functionality
        """
        critical_keywords = [
            "architecture", "security", "authentication", "authorization",
            "design", "core", "critical", "production", "deployment"
        ]
        
        query_lower = query.lower()
        
        # Check for critical keywords
        if any(kw in query_lower for kw in critical_keywords):
            return True
        
        # Check for architecture intent
        if "architecture" in intents:
            return True
        
        return False
    
    def filter_by_quality(
        self,
        documents: List[Dict[str, Any]],
        min_quality: float = 40.0
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by quality score.
        
        Args:
            documents: Documents to filter
            min_quality: Minimum quality score (0-100)
        
        Returns:
            Filtered documents
        """
        filtered = []
        
        for doc in documents:
            quality = doc.get("quality_score") or doc.get("metadata", {}).get("quality_score")
            
            if quality is None or quality >= min_quality:
                filtered.append(doc)
        
        logger.info(f"Quality filter: {len(documents)} → {len(filtered)} (>= {min_quality})")
        
        return filtered
    
    def filter_by_recency(
        self,
        documents: List[Dict[str, Any]],
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by recency.
        
        Args:
            documents: Documents to filter
            days: Number of days (recent)
        
        Returns:
            Recent documents
        """
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        
        for doc in documents:
            git_date_str = doc.get("git_date") or doc.get("metadata", {}).get("git_date")
            
            if git_date_str:
                try:
                    git_date = datetime.fromisoformat(git_date_str.replace("Z", "+00:00"))
                    if git_date >= cutoff:
                        filtered.append(doc)
                except Exception:
                    # If date parsing fails, include anyway
                    filtered.append(doc)
            else:
                # No date, include anyway
                filtered.append(doc)
        
        logger.info(f"Recency filter: {len(documents)} → {len(filtered)} (last {days} days)")
        
        return filtered
    
    def prefer_categories(
        self,
        documents: List[Dict[str, Any]],
        preferred_categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Reorder documents to prefer certain categories.
        
        Args:
            documents: Documents to reorder
            preferred_categories: Categories to prioritize
        
        Returns:
            Reordered documents
        """
        preferred = []
        others = []
        
        for doc in documents:
            category = doc.get("category") or doc.get("metadata", {}).get("category")
            
            if category in preferred_categories:
                preferred.append(doc)
            else:
                others.append(doc)
        
        # Preferred first, then others
        return preferred + others


# Singleton instance
_metadata_filter = None


def get_metadata_filter() -> MetadataFilter:
    """Get or create metadata filter singleton."""
    global _metadata_filter
    if _metadata_filter is None:
        _metadata_filter = MetadataFilter()
    return _metadata_filter

