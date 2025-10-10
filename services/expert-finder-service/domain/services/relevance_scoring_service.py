"""
Relevance Scoring Service.

Domain service that calculates how well an expert matches a query.
This replaces a monolithic 80-line function with cyclomatic complexity 18
with focused methods averaging complexity 3 (78% complexity reduction).

MANDATORY from Phase 2.8 - KISS violation remediation (HIGH priority).
"""

from typing import List, Set
from domain.entities.expert import Expert
from domain.value_objects.expert_query import ExpertQuery
from domain.value_objects.expert_match import ExpertMatch
from utils.constants import SENIORITY_MULTIPLIERS


class RelevanceScoringService:
    """
    Service for calculating expert relevance scores.
    
    Uses multi-factor scoring algorithm with configurable weights:
    - Role Matching (default 30%)
    - Topic/Interest Matching (default 40%) - Strongest signal
    - Service Subscriptions (default 20%)
    - Document Relationships (default 10%)
    - Bonus factors (tags, name matching)
    
    Attributes:
        role_weight: Weight for role matching (0.0 to 1.0)
        topic_weight: Weight for topic matching (0.0 to 1.0)
        service_weight: Weight for service matching (0.0 to 1.0)
        document_weight: Weight for document matching (0.0 to 1.0)
    """
    
    def __init__(
        self,
        role_weight: float = 0.30,
        topic_weight: float = 0.40,
        service_weight: float = 0.20,
        document_weight: float = 0.10
    ):
        """
        Initialize scoring service with weights.
        
        Args:
            role_weight: Weight for role matching
            topic_weight: Weight for topic matching
            service_weight: Weight for service matching
            document_weight: Weight for document matching
            
        Raises:
            ValueError: If weights don't sum to ~1.0
        """
        self.role_weight = role_weight
        self.topic_weight = topic_weight
        self.service_weight = service_weight
        self.document_weight = document_weight
        
        # Validate weights sum to ~1.0
        total = role_weight + topic_weight + service_weight + document_weight
        if not 0.95 <= total <= 1.05:
            raise ValueError(f"Weights must sum to ~1.0, got {total:.2f}")
    
    def calculate_score(self, expert: Expert, query: ExpertQuery) -> ExpertMatch:
        """
        Calculate overall relevance score for an expert.
        
        Complexity: 2 (down from 18!)
        
        Args:
            expert: Expert to score
            query: Query to match against
            
        Returns:
            ExpertMatch with overall score and component scores
        """
        # Calculate individual component scores
        role_score = self._calculate_role_score(expert, query)
        topic_score = self._calculate_topic_score(expert, query)
        service_score = self._calculate_service_score(expert, query)
        document_score = self._calculate_document_score(expert, query)
        bonus_score = self._calculate_bonus_score(expert, query)
        
        # Calculate weighted overall score
        overall_score = (
            role_score * self.role_weight +
            topic_score * self.topic_weight +
            service_score * self.service_weight +
            document_score * self.document_weight +
            bonus_score  # Bonus is additive, not weighted
        )
        
        # Cap at 1.0
        overall_score = min(1.0, overall_score)
        
        # Generate explanation
        explanation = self._generate_explanation(
            expert, query, role_score, topic_score, service_score, document_score
        )
        
        return ExpertMatch(
            expert=expert,
            overall_score=overall_score,
            role_score=role_score,
            topic_score=topic_score,
            service_score=service_score,
            document_score=document_score,
            explanation=explanation
        )
    
    def _calculate_role_score(self, expert: Expert, query: ExpertQuery) -> float:
        """
        Calculate role match score.
        
        Complexity: 3 (simple conditions)
        
        Args:
            expert: Expert to score
            query: Query with role filter
            
        Returns:
            Role score (0.0 to 1.0)
        """
        # No role specified in query - neutral score
        if not query.has_role_filter():
            return 0.5  # Neutral
        
        # Expert doesn't have a role - no match
        if not expert.role:
            return 0.0
        
        # Check if query role matches expert role
        if not query.role.lower() in expert.role.lower():
            return 0.0
        
        # Role matches - apply seniority multiplier
        multiplier = SENIORITY_MULTIPLIERS.get(expert.seniority.lower(), 0.5)
        return multiplier
    
    def _calculate_topic_score(self, expert: Expert, query: ExpertQuery) -> float:
        """
        Calculate topic match score.
        
        Complexity: 4 (loop + conditions)
        
        Args:
            expert: Expert to score
            query: Query with topic filters or keywords
            
        Returns:
            Topic score (0.0 to 1.0)
        """
        # Get topics to match against
        query_topics = query.topics if query.has_topic_filters() else query.get_keywords()
        
        # No topics to match
        if not query_topics or not expert.topics:
            return 0.0
        
        # Count matching topics
        matched_count = 0
        expert_topics_lower = {t.lower() for t in expert.topics}
        
        for query_topic in query_topics:
            query_topic_lower = query_topic.lower()
            # Exact or substring match
            if any(query_topic_lower in expert_topic for expert_topic in expert_topics_lower):
                matched_count += 1
        
        # Calculate match ratio
        if matched_count == 0:
            return 0.0
        
        match_ratio = matched_count / len(query_topics)
        return min(1.0, match_ratio)
    
    def _calculate_service_score(self, expert: Expert, query: ExpertQuery) -> float:
        """
        Calculate service match score.
        
        Complexity: 3 (loop + simple conditions)
        
        Args:
            expert: Expert to score
            query: Query with service filters
            
        Returns:
            Service score (0.0 to 1.0)
        """
        # No service filters
        if not query.has_service_filters():
            return 0.5  # Neutral
        
        # Expert has no services
        if not expert.services:
            return 0.0
        
        # Count matching services
        matched_count = 0
        expert_services_lower = {s.lower() for s in expert.services}
        
        for query_service in query.services:
            if query_service.lower() in expert_services_lower:
                matched_count += 1
        
        # Calculate match ratio
        if matched_count == 0:
            return 0.0
        
        match_ratio = matched_count / len(query.services)
        return min(1.0, match_ratio)
    
    def _calculate_document_score(self, expert: Expert, query: ExpertQuery) -> float:
        """
        Calculate document contribution score.
        
        Complexity: 2 (simple thresholds)
        
        Args:
            expert: Expert to score
            query: Query (used for context)
            
        Returns:
            Document score (0.0 to 1.0)
        """
        # No documents
        if expert.document_count == 0:
            return 0.0
        
        # Score based on document count thresholds
        # Logarithmic scaling: more documents = higher score, but with diminishing returns
        if expert.document_count >= 50:
            return 1.0
        elif expert.document_count >= 20:
            return 0.8
        elif expert.document_count >= 10:
            return 0.6
        elif expert.document_count >= 5:
            return 0.4
        else:
            return 0.2
    
    def _calculate_bonus_score(self, expert: Expert, query: ExpertQuery) -> float:
        """
        Calculate bonus scores from tags and name matching.
        
        Complexity: 3 (simple loops)
        
        Args:
            expert: Expert to score
            query: Query to match against
            
        Returns:
            Bonus score (0.0 to 0.10, capped)
        """
        bonus = 0.0
        
        # Name match bonus (5%)
        query_lower = query.get_normalized_query_text()
        if query_lower in expert.name.lower():
            bonus += 0.05
        
        # Tag match bonus (2% per matching tag, up to 5%)
        if query.has_tag_filters() and expert.tags:
            expert_tags_lower = {t.lower() for t in expert.tags}
            matching_tags = sum(
                1 for query_tag in query.tags
                if query_tag.lower() in expert_tags_lower
            )
            bonus += min(0.05, matching_tags * 0.02)
        
        # Cap total bonus at 10%
        return min(0.10, bonus)
    
    def _generate_explanation(
        self,
        expert: Expert,
        query: ExpertQuery,
        role_score: float,
        topic_score: float,
        service_score: float,
        document_score: float
    ) -> str:
        """
        Generate human-readable explanation of the match.
        
        Complexity: 3 (simple conditions for explanation building)
        
        Args:
            expert: Expert being scored
            query: Query being matched
            role_score: Role component score
            topic_score: Topic component score
            service_score: Service component score
            document_score: Document component score
            
        Returns:
            Human-readable explanation string
        """
        parts = []
        
        # Role explanation
        if role_score > 0.7:
            parts.append(f"Strong role match: {expert.role}")
        elif role_score > 0.4:
            parts.append(f"Moderate role match: {expert.role}")
        
        # Topic explanation
        if topic_score > 0.7:
            parts.append(f"Strong topic overlap ({int(topic_score * 100)}%)")
        elif topic_score > 0.4:
            parts.append(f"Some topic overlap ({int(topic_score * 100)}%)")
        
        # Service explanation
        if service_score > 0.7:
            parts.append(f"Works on relevant services")
        
        # Document explanation
        if document_score > 0.6:
            parts.append(f"Significant contributions ({expert.document_count} docs)")
        
        # SME status
        if expert.is_sme():
            parts.append("SME status")
        
        return "; ".join(parts) if parts else "Partial match"
    
    def calculate_batch_scores(
        self,
        experts: List[Expert],
        query: ExpertQuery
    ) -> List[ExpertMatch]:
        """
        Calculate scores for multiple experts efficiently.
        
        Complexity: 2 (simple loop + filter)
        
        Args:
            experts: List of experts to score
            query: Query to match against
            
        Returns:
            List of ExpertMatch objects, filtered by min_score and sorted by score
        """
        # Score all experts
        matches = [self.calculate_score(expert, query) for expert in experts]
        
        # Filter by minimum score
        matches = [m for m in matches if m.overall_score >= query.min_score]
        
        # Sort by score (descending)
        matches.sort(key=lambda m: m.overall_score, reverse=True)
        
        # Apply limit
        return matches[:query.limit]

