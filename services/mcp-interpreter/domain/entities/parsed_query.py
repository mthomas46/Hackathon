"""Parsed Query Entity - Domain Layer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Set, Optional
import uuid

from services.mcp_interpreter.domain.entities.extracted_entity import ExtractedEntity
from services.mcp_interpreter.domain.value_objects.query_intent import QueryIntent
from services.mcp_interpreter.domain.value_objects.mcp_tier import MCPTier
from services.mcp_interpreter.domain.value_objects.confidence_level import ConfidenceLevel


@dataclass
class ParsedQuery:
    """
    Represents a parsed and interpreted natural language query.
    
    This is the core aggregate root for the query interpretation domain.
    Contains all extracted information and interpretation results.
    """
    
    # Identity and original query
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_query: str = ""
    normalized_query: str = ""  # Cleaned/normalized version
    
    # Interpretation results
    intent: QueryIntent = QueryIntent.UNKNOWN
    intent_confidence: float = 0.0
    
    # Extracted entities
    entities: List[ExtractedEntity] = field(default_factory=list)
    
    # MCP targeting
    required_tiers: List[MCPTier] = field(default_factory=list)
    primary_tier: Optional[MCPTier] = None
    
    # Query planning
    requires_multiple_mcps: bool = False
    estimated_complexity: int = 5  # 1-10 scale
    
    # Confidence and quality
    overall_confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    
    # Additional context
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    temporal_scope: Optional[str] = None  # e.g., "last_sprint", "Q1_2025"
    
    # Metadata
    parsed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and initialize the parsed query."""
        if not self.original_query:
            raise ValueError("ParsedQuery must have an original_query")
        
        # Set normalized query if not provided
        if not self.normalized_query:
            self.normalized_query = self.original_query.strip().lower()
        
        # Infer required tiers from entities if not set
        if not self.required_tiers and self.entities:
            self._infer_required_tiers()
        
        # Set primary tier if not set
        if not self.primary_tier and self.required_tiers:
            self.primary_tier = self.required_tiers[0]
        
        # Update confidence level from score
        if self.overall_confidence > 0:
            self.confidence_level = ConfidenceLevel.from_score(self.overall_confidence)
        
        # Set complexity from intent if not customized
        if self.estimated_complexity == 5:
            self.estimated_complexity = self.intent.complexity_score
        
        # Check if multiple MCPs needed
        if not self.requires_multiple_mcps:
            self.requires_multiple_mcps = (
                self.intent.requires_multiple_mcps or 
                len(self.required_tiers) > 1
            )
    
    def _infer_required_tiers(self) -> None:
        """Infer required MCP tiers from extracted entities."""
        entity_types = {entity.entity_type for entity in self.entities}
        
        # Get primary tier
        primary_tier = MCPTier.from_entity_types(entity_types)
        self.required_tiers = [primary_tier]
        
        # Add additional tiers based on intent
        if self.intent.requires_multiple_mcps:
            # For complex queries, add adjacent tiers
            if primary_tier == MCPTier.CLIENT:
                self.required_tiers.extend([MCPTier.PROJECT, MCPTier.COMPANY])
            elif primary_tier == MCPTier.PROJECT:
                self.required_tiers.extend([MCPTier.TEAM, MCPTier.COMPANY])
            elif primary_tier == MCPTier.TEAM:
                self.required_tiers.extend([MCPTier.COMPANY, MCPTier.ECOSYSTEM])
    
    def add_entity(self, entity: ExtractedEntity) -> None:
        """Add an extracted entity."""
        if not isinstance(entity, ExtractedEntity):
            raise TypeError("entity must be an ExtractedEntity")
        self.entities.append(entity)
    
    def get_entities_by_type(self, entity_type: Any) -> List[ExtractedEntity]:
        """Get all entities of a specific type."""
        from services.mcp_interpreter.domain.value_objects.entity_type import EntityType
        
        if not isinstance(entity_type, EntityType):
            entity_type = EntityType(entity_type)
        
        return [e for e in self.entities if e.entity_type == entity_type]
    
    def get_organizational_entities(self) -> List[ExtractedEntity]:
        """Get all organizational entities."""
        return [e for e in self.entities if e.is_organizational]
    
    def get_technical_entities(self) -> List[ExtractedEntity]:
        """Get all technical entities."""
        return [e for e in self.entities if e.is_technical]
    
    def get_temporal_entities(self) -> List[ExtractedEntity]:
        """Get all temporal entities."""
        return [e for e in self.entities if e.is_temporal]
    
    def requires_human_review(self) -> bool:
        """Check if query requires human review based on confidence."""
        return self.confidence_level.requires_human_review
    
    def can_auto_execute(self) -> bool:
        """Check if query can be auto-executed."""
        return self.confidence_level.can_auto_execute
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "intent": self.intent.value,
            "intent_confidence": self.intent_confidence,
            "entities": [e.to_dict() for e in self.entities],
            "required_tiers": [tier.value for tier in self.required_tiers],
            "primary_tier": self.primary_tier.value if self.primary_tier else None,
            "requires_multiple_mcps": self.requires_multiple_mcps,
            "estimated_complexity": self.estimated_complexity,
            "overall_confidence": self.overall_confidence,
            "confidence_level": self.confidence_level.value,
            "keywords": self.keywords,
            "topics": self.topics,
            "temporal_scope": self.temporal_scope,
            "parsed_at": self.parsed_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParsedQuery":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            original_query=data["original_query"],
            normalized_query=data["normalized_query"],
            intent=QueryIntent(data["intent"]),
            intent_confidence=data["intent_confidence"],
            entities=[ExtractedEntity.from_dict(e) for e in data.get("entities", [])],
            required_tiers=[MCPTier(t) for t in data.get("required_tiers", [])],
            primary_tier=MCPTier(data["primary_tier"]) if data.get("primary_tier") is not None else None,
            requires_multiple_mcps=data.get("requires_multiple_mcps", False),
            estimated_complexity=data.get("estimated_complexity", 5),
            overall_confidence=data.get("overall_confidence", 0.0),
            confidence_level=ConfidenceLevel(data.get("confidence_level", "medium")),
            keywords=data.get("keywords", []),
            topics=data.get("topics", []),
            temporal_scope=data.get("temporal_scope"),
            parsed_at=datetime.fromisoformat(data["parsed_at"]),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            metadata=data.get("metadata", {}),
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ParsedQuery(id={self.id}, "
            f"intent={self.intent.value}, "
            f"entities={len(self.entities)}, "
            f"confidence={self.confidence_level.value})"
        )

