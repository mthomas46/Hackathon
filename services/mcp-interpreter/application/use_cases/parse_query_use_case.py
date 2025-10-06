"""Parse Query Use Case."""

import logging
import time
from typing import Optional

from services.mcp_interpreter.application.dto.parse_query_request import ParseQueryRequest
from services.mcp_interpreter.application.dto.parsed_query_response import ParsedQueryResponse
from services.mcp_interpreter.domain.entities.parsed_query import ParsedQuery
from services.mcp_interpreter.domain.entities.extracted_entity import ExtractedEntity
from services.mcp_interpreter.domain.repositories.query_cache_repository import QueryCacheRepository
from services.mcp_interpreter.domain.value_objects.query_intent import QueryIntent
from services.mcp_interpreter.domain.value_objects.entity_type import EntityType

logger = logging.getLogger(__name__)


class ParseQueryUseCase:
    """
    Use case for parsing natural language queries.
    
    This is the main entry point for query interpretation.
    Orchestrates NLP processing, caching, and result assembly.
    """
    
    def __init__(
        self,
        cache_repository: Optional[QueryCacheRepository] = None,
        nlp_service=None,  # Will be NLPService from infrastructure
        intent_classifier=None,  # Will be IntentClassifier from infrastructure
    ):
        """
        Initialize the use case.
        
        Args:
            cache_repository: Optional repository for caching parsed queries
            nlp_service: Service for NLP processing (entity extraction)
            intent_classifier: Service for intent classification
        """
        self.cache_repository = cache_repository
        self.nlp_service = nlp_service
        self.intent_classifier = intent_classifier
    
    async def execute(self, request: ParseQueryRequest) -> ParsedQueryResponse:
        """
        Parse a natural language query.
        
        Args:
            request: Parse query request
        
        Returns:
            Parsed query response with interpretation results
        """
        start_time = time.time()
        
        try:
            # Check cache first (if enabled)
            if request.use_cache and not request.force_reparse and self.cache_repository:
                cached_query = await self._check_cache(request.query)
                if cached_query:
                    logger.info(f"Cache hit for query: {request.query[:50]}...")
                    return ParsedQueryResponse.from_entity(cached_query, cached=True)
            
            # Parse the query
            parsed_query = await self._parse_query(request)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            parsed_query.processing_time_ms = processing_time_ms
            
            # Cache the result (if enabled)
            if request.use_cache and self.cache_repository:
                await self._cache_result(parsed_query)
            
            logger.info(
                f"Parsed query: intent={parsed_query.intent.value}, "
                f"entities={len(parsed_query.entities)}, "
                f"confidence={parsed_query.overall_confidence:.2f}, "
                f"time={processing_time_ms:.1f}ms"
            )
            
            return ParsedQueryResponse.from_entity(parsed_query, cached=False)
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}", exc_info=True)
            raise
    
    async def _check_cache(self, query_text: str) -> Optional[ParsedQuery]:
        """
        Check if query is in cache.
        
        Args:
            query_text: Original query text
        
        Returns:
            Cached ParsedQuery if found, None otherwise
        """
        try:
            # Normalize query for cache lookup
            normalized_query = query_text.strip().lower()
            return await self.cache_repository.find_by_query_text(normalized_query)
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
            return None
    
    async def _parse_query(self, request: ParseQueryRequest) -> ParsedQuery:
        """
        Parse the query using NLP and classification.
        
        Args:
            request: Parse request
        
        Returns:
            Parsed query entity
        """
        # Create parsed query entity
        parsed_query = ParsedQuery(
            original_query=request.query,
            normalized_query=request.query.strip().lower(),
        )
        
        # Extract entities (if NLP service available)
        if self.nlp_service:
            entities = await self._extract_entities(request.query)
            for entity in entities:
                parsed_query.add_entity(entity)
        else:
            # Fallback: simple keyword extraction
            entities = self._extract_entities_fallback(request.query)
            for entity in entities:
                parsed_query.add_entity(entity)
        
        # Classify intent (if classifier available)
        if self.intent_classifier:
            intent, confidence = await self._classify_intent(request.query, parsed_query)
            parsed_query.intent = intent
            parsed_query.intent_confidence = confidence
        else:
            # Fallback: simple intent inference
            intent, confidence = self._classify_intent_fallback(request.query)
            parsed_query.intent = intent
            parsed_query.intent_confidence = confidence
        
        # Extract keywords
        parsed_query.keywords = self._extract_keywords(request.query)
        
        # Calculate overall confidence
        parsed_query.overall_confidence = self._calculate_overall_confidence(parsed_query)
        
        return parsed_query
    
    async def _extract_entities(self, query: str) -> list[ExtractedEntity]:
        """
        Extract entities using NLP service.
        
        Args:
            query: Query text
        
        Returns:
            List of extracted entities
        """
        # This will be implemented in infrastructure layer with spaCy
        # For now, return empty list
        return []
    
    def _extract_entities_fallback(self, query: str) -> list[ExtractedEntity]:
        """
        Fallback entity extraction using keywords.
        
        Args:
            query: Query text
        
        Returns:
            List of extracted entities
        """
        entities = []
        query_lower = query.lower()
        
        # Simple pattern matching for common entities
        patterns = {
            "team": EntityType.TEAM,
            "project": EntityType.PROJECT,
            "client": EntityType.CLIENT,
            "sprint": EntityType.SPRINT,
            "feature": EntityType.FEATURE,
            "last sprint": EntityType.TIME_PERIOD,
            "this quarter": EntityType.TIME_PERIOD,
        }
        
        for pattern, entity_type in patterns.items():
            if pattern in query_lower:
                entities.append(
                    ExtractedEntity(
                        text=pattern,
                        entity_type=entity_type,
                        normalized_value=pattern,
                        confidence=0.7,
                    )
                )
        
        return entities
    
    async def _classify_intent(
        self, query: str, parsed_query: ParsedQuery
    ) -> tuple[QueryIntent, float]:
        """
        Classify query intent using intent classifier.
        
        Args:
            query: Query text
            parsed_query: Partially parsed query
        
        Returns:
            Tuple of (intent, confidence)
        """
        # This will be implemented in infrastructure layer with LLM
        # For now, use fallback
        return self._classify_intent_fallback(query)
    
    def _classify_intent_fallback(self, query: str) -> tuple[QueryIntent, float]:
        """
        Fallback intent classification using keywords.
        
        Args:
            query: Query text
        
        Returns:
            Tuple of (intent, confidence)
        """
        query_lower = query.lower()
        
        # Simple keyword-based intent classification
        if any(word in query_lower for word in ["what", "which", "show", "list"]):
            return (QueryIntent.SEARCH, 0.6)
        elif any(word in query_lower for word in ["analyze", "analysis", "understand"]):
            return (QueryIntent.ANALYZE, 0.6)
        elif any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            return (QueryIntent.COMPARE, 0.6)
        elif any(word in query_lower for word in ["recommend", "suggest", "should"]):
            return (QueryIntent.RECOMMEND, 0.6)
        elif any(word in query_lower for word in ["how many", "count"]):
            return (QueryIntent.COUNT, 0.6)
        elif any(word in query_lower for word in ["plan", "strategy"]):
            return (QueryIntent.PLAN, 0.6)
        else:
            return (QueryIntent.UNKNOWN, 0.3)
    
    def _extract_keywords(self, query: str) -> list[str]:
        """
        Extract keywords from query.
        
        Args:
            query: Query text
        
        Returns:
            List of keywords
        """
        # Simple keyword extraction (remove stop words)
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "what", "which", "who", "when", "where", "how", "why",
            "in", "on", "at", "to", "for", "of", "with", "by", "from",
            "does", "do", "did", "have", "has", "had",
        }
        
        words = query.lower().split()
        keywords = [w.strip(".,!?;:") for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:10]  # Limit to top 10 keywords
    
    def _calculate_overall_confidence(self, parsed_query: ParsedQuery) -> float:
        """
        Calculate overall confidence score.
        
        Args:
            parsed_query: Parsed query
        
        Returns:
            Overall confidence score (0.0-1.0)
        """
        # Weight different components
        intent_weight = 0.4
        entity_weight = 0.4
        complexity_weight = 0.2
        
        # Intent confidence
        intent_score = parsed_query.intent_confidence
        
        # Entity confidence (average of entity confidences)
        if parsed_query.entities:
            entity_score = sum(e.confidence for e in parsed_query.entities) / len(parsed_query.entities)
        else:
            entity_score = 0.5  # Neutral if no entities
        
        # Complexity score (lower complexity = higher confidence)
        complexity_score = 1.0 - (parsed_query.estimated_complexity / 10.0)
        
        overall = (
            intent_score * intent_weight +
            entity_score * entity_weight +
            complexity_score * complexity_weight
        )
        
        return min(1.0, max(0.0, overall))
    
    async def _cache_result(self, parsed_query: ParsedQuery) -> None:
        """
        Cache the parsed query result.
        
        Args:
            parsed_query: Parsed query to cache
        """
        try:
            await self.cache_repository.save(parsed_query, ttl_seconds=3600)
            logger.debug(f"Cached query: {parsed_query.id}")
        except Exception as e:
            logger.warning(f"Failed to cache query: {e}")

