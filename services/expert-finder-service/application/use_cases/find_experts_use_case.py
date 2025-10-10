"""
Find Experts Use Case.

Orchestrates the process of finding experts matching a query,
including scoring, filtering, and enrichment.
"""

import logging
from typing import List

from domain.entities.expert import Expert
from domain.value_objects.expert_query import ExpertQuery
from domain.value_objects.expert_match import ExpertMatch
from domain.services.relevance_scoring_service import RelevanceScoringService
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.document_repository import DocumentRepository
from infrastructure.repositories.service_repository import ServiceRepository
from utils.transformers import enrich_with_documents, enrich_with_services

logger = logging.getLogger(__name__)


class FindExpertsUseCase:
    """
    Use case for finding experts matching a query.
    
    This orchestrates the entire expert finding process:
    1. Fetch users from user-store
    2. Enrich with document data from doc-store
    3. Enrich with service data from external-service-store
    4. Score each expert against the query
    5. Filter by minimum score
    6. Sort by relevance
    7. Return top matches
    
    Attributes:
        user_repo: Repository for user data
        doc_repo: Repository for document data
        service_repo: Repository for service data
        scoring_service: Service for calculating relevance scores
    """
    
    def __init__(
        self,
        user_repo: UserRepository,
        doc_repo: DocumentRepository,
        service_repo: ServiceRepository,
        scoring_service: RelevanceScoringService
    ):
        """
        Initialize use case with dependencies.
        
        Args:
            user_repo: User repository
            doc_repo: Document repository
            service_repo: Service repository
            scoring_service: Relevance scoring service
        """
        self.user_repo = user_repo
        self.doc_repo = doc_repo
        self.service_repo = service_repo
        self.scoring_service = scoring_service
    
    async def execute(self, query: ExpertQuery) -> List[ExpertMatch]:
        """
        Execute the find experts use case.
        
        Args:
            query: Expert query with search criteria
            
        Returns:
            List of expert matches, sorted by relevance
        """
        logger.info(f"Finding experts for query: {query}")
        
        # Step 1: Fetch candidate users
        candidates = await self._fetch_candidates(query)
        logger.info(f"Found {len(candidates)} candidate experts")
        
        if not candidates:
            return []
        
        # Step 2: Enrich candidates with additional data
        enriched_candidates = await self._enrich_candidates(candidates)
        logger.info(f"Enriched {len(enriched_candidates)} experts")
        
        # Step 3: Filter by SME status if required
        if query.is_sme_query():
            enriched_candidates = [
                expert for expert in enriched_candidates
                if expert.is_sme(query.min_documents)
            ]
            logger.info(f"Filtered to {len(enriched_candidates)} SMEs")
        
        # Step 4: Score and rank experts
        matches = self.scoring_service.calculate_batch_scores(
            enriched_candidates,
            query
        )
        
        top_score_msg = f"(top score: {matches[0].overall_score:.2f})" if matches else "(top score: N/A)"
        logger.info(
            f"Returning {len(matches)} matches {top_score_msg}"
        )
        
        return matches
    
    async def _fetch_candidates(self, query: ExpertQuery) -> List[Expert]:
        """
        Fetch candidate experts from user-store.
        
        Args:
            query: Expert query
            
        Returns:
            List of candidate experts
        """
        # If role filter specified, use role-based search
        if query.has_role_filter():
            return await self.user_repo.get_users_by_role(
                query.role,
                limit=query.limit * 3  # Fetch more for filtering
            )
        
        # If topic filters specified, use topic-based search
        if query.has_topic_filters():
            # Get users for each topic and combine
            all_candidates = []
            for topic in query.topics:
                candidates = await self.user_repo.get_users_by_topic(
                    topic,
                    limit=query.limit * 2
                )
                all_candidates.extend(candidates)
            
            # Deduplicate by user_id
            seen = set()
            unique_candidates = []
            for candidate in all_candidates:
                if candidate.user_id not in seen:
                    seen.add(candidate.user_id)
                    unique_candidates.append(candidate)
            
            return unique_candidates
        
        # Otherwise, use general search
        return await self.user_repo.search_users(
            query.query_text,
            limit=query.limit * 3
        )
    
    async def _enrich_candidates(self, candidates: List[Expert]) -> List[Expert]:
        """
        Enrich candidates with document and service data.
        
        Args:
            candidates: List of candidate experts
            
        Returns:
            List of enriched experts
        """
        enriched = []
        
        for expert in candidates:
            try:
                # Fetch document count
                document_count = await self.doc_repo.get_document_count_by_author(
                    expert.user_id
                )
                
                # Fetch service count
                service_count = await self.service_repo.get_service_count_by_user(
                    expert.user_id
                )
                
                # Create enriched expert (immutable, so create new instance)
                from dataclasses import replace
                enriched_expert = replace(
                    expert,
                    document_count=document_count,
                    service_count=service_count
                )
                
                enriched.append(enriched_expert)
                
            except Exception as e:
                logger.error(
                    f"Error enriching expert {expert.user_id}: {str(e)}. "
                    f"Using unenriched data."
                )
                enriched.append(expert)
        
        return enriched

