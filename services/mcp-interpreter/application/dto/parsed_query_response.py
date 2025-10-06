"""Parsed Query Response DTO."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ParsedQueryResponse:
    """
    DTO for parsed query response.
    """
    
    # Query identification
    query_id: str
    original_query: str
    normalized_query: str
    
    # Interpretation
    intent: str
    intent_confidence: float
    
    # Entities
    entities: List[Dict[str, Any]]
    
    # MCP targeting
    required_tiers: List[int]
    primary_tier: Optional[int]
    requires_multiple_mcps: bool
    
    # Quality
    overall_confidence: float
    confidence_level: str
    estimated_complexity: int
    
    # Context
    keywords: List[str]
    topics: List[str]
    temporal_scope: Optional[str]
    
    # Metadata
    parsed_at: str
    processing_time_ms: float
    cached: bool = False
    
    @classmethod
    def from_entity(cls, parsed_query, cached: bool = False) -> "ParsedQueryResponse":
        """Create response from ParsedQuery entity."""
        query_dict = parsed_query.to_dict()
        return cls(
            query_id=query_dict["id"],
            original_query=query_dict["original_query"],
            normalized_query=query_dict["normalized_query"],
            intent=query_dict["intent"],
            intent_confidence=query_dict["intent_confidence"],
            entities=query_dict["entities"],
            required_tiers=query_dict["required_tiers"],
            primary_tier=query_dict["primary_tier"],
            requires_multiple_mcps=query_dict["requires_multiple_mcps"],
            overall_confidence=query_dict["overall_confidence"],
            confidence_level=query_dict["confidence_level"],
            estimated_complexity=query_dict["estimated_complexity"],
            keywords=query_dict["keywords"],
            topics=query_dict["topics"],
            temporal_scope=query_dict["temporal_scope"],
            parsed_at=query_dict["parsed_at"],
            processing_time_ms=query_dict["processing_time_ms"],
            cached=cached,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "entities": self.entities,
            "required_tiers": self.required_tiers,
            "primary_tier": self.primary_tier,
            "requires_multiple_mcps": self.requires_multiple_mcps,
            "overall_confidence": self.overall_confidence,
            "confidence_level": self.confidence_level,
            "estimated_complexity": self.estimated_complexity,
            "keywords": self.keywords,
            "topics": self.topics,
            "temporal_scope": self.temporal_scope,
            "parsed_at": self.parsed_at,
            "processing_time_ms": self.processing_time_ms,
            "cached": self.cached,
        }

