"""
Temporal RAG Service

Provides time-travel RAG queries with temporal filtering:
- Query documents as they existed at a specific point in time
- Track how information evolved over time
- Compare information between different time periods
- Detect changes and drift in documentation

Integrates with Timeline system and ContextAwareRAG.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .context_aware_rag import ContextAwareRAG
from ..timeline import TimelineManager, TemporalConfidenceCalculator
from ...storage.repositories.timeline_repository import (
    TimelineRepository,
    TimePeriodRepository,
    DocumentPlacementRepository
)
from ...storage import get_database
from ...models.timeline import TemporalConfidence

logger = logging.getLogger(__name__)


class TemporalRAGService:
    """
    Temporal RAG service with time-travel capabilities.
    
    Features:
    - Query documents "as of" a specific date
    - Track information evolution over time
    - Compare information between periods
    - Detect documentation drift
    - Confidence-aware temporal queries
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize temporal RAG service.
        
        Args:
            db_session: Optional database session (creates new if not provided)
        """
        self.db = db_session
        self.context_rag = ContextAwareRAG()
        self.logger = logging.getLogger(__name__)
        
        # Import Ollama router for LLM answer synthesis
        from ..models.ollama_router import get_ollama_router
        self.ollama_router = get_ollama_router()
        
        self.logger.info("TemporalRAGService initialized")
    
    async def _query_with_temporal_filter(
        self,
        query: str,
        as_of_date: datetime,
        service_name: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query documents using temporal filtering in ChromaDB.
        
        ✅ PHASE 4: Uses git_date metadata to filter documents that existed at as_of_date.
        
        Args:
            query: Question to answer
            as_of_date: Point in time to query
            service_name: Optional service filter
            limit: Maximum results
        
        Returns:
            Query results with temporal context
        """
        try:
            from ...storage.chromadb_client import get_chroma_client
            from ...services.embeddings.embedding_service import EmbeddingService
            
            self.logger.info(f"🔍 [TEMPORAL_RAG] Starting temporal query")
            self.logger.debug(f"   Query: {query[:100]}")
            self.logger.debug(f"   As of date: {as_of_date}")
            self.logger.debug(f"   Service name: {service_name}")
            self.logger.debug(f"   Limit: {limit}")
            
            chroma = get_chroma_client()
            
            # ✅ FIX: Build where clause properly for ChromaDB
            # ChromaDB requires $and operator when there are multiple conditions
            self.logger.debug(f"🔍 [TEMPORAL_RAG] Building where clause")
            
            conditions = []
            
            # Always filter by git_date
            # ✅ FIX: Convert to timestamp (ChromaDB expects numeric values for comparison operators)
            as_of_timestamp = as_of_date.timestamp()
            git_date_condition = {"git_date": {"$lte": as_of_timestamp}}
            conditions.append(git_date_condition)
            self.logger.debug(f"   Adding git_date filter: <= {as_of_date.date()} (timestamp: {as_of_timestamp})")
            
            # Optionally filter by service_name
            if service_name:
                service_condition = {"service_name": service_name}
                conditions.append(service_condition)
                self.logger.debug(f"   Adding service_name filter: {service_name}")
            
            # Build final where clause
            if len(conditions) == 1:
                where_clause = conditions[0]
                self.logger.debug(f"   Single condition where clause: {where_clause}")
            else:
                where_clause = {"$and": conditions}
                self.logger.debug(f"   Multi-condition where clause using $and: {where_clause}")
            
            self.logger.info(
                f"✅ [TEMPORAL_RAG] Where clause built with {len(conditions)} condition(s)"
            )
            
            # Generate query embedding first (ChromaDB needs vectors, not text)
            self.logger.debug(f"🔍 [TEMPORAL_RAG] Generating query embedding")
            embedding_service = EmbeddingService()
            try:
                embedding_result = await embedding_service.generate_embedding(query)
                query_embedding = embedding_result.get("embedding") if isinstance(embedding_result, dict) else embedding_result
                
                if not query_embedding:
                    raise ValueError("Failed to generate query embedding")
                
                self.logger.debug(f"   ✅ Embedding generated (dimension: {len(query_embedding)})")
                    
            except Exception as embed_error:
                self.logger.error(f"   ❌ Failed to generate query embedding: {embed_error}", exc_info=True)
                raise
            
            # Query ChromaDB with temporal filter
            self.logger.debug(f"🔍 [TEMPORAL_RAG] Querying ChromaDB")
            self.logger.debug(f"   Where clause: {where_clause}")
            self.logger.debug(f"   n_results: {limit}")
            
            try:
                results = await chroma.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where_clause
                )
                self.logger.debug(f"   ✅ ChromaDB query successful")
            except Exception as chroma_error:
                self.logger.error(f"   ❌ ChromaDB query failed: {chroma_error}", exc_info=True)
                self.logger.error(f"   Where clause that failed: {where_clause}")
                raise
            
            if not results or not results.get("documents"):
                self.logger.warning(f"⚠️ [TEMPORAL_RAG] No documents found matching temporal filter")
                return {
                    "query": query,
                    "as_of_date": as_of_date.isoformat(),
                    "answer": "No documents found for the specified time period.",
                    "documents": [],
                    "sources": [],
                    "metadata": {
                        "temporal_filter_applied": True,
                        "filter": where_clause,
                        "documents_found": 0,
                        "query_type": "temporal_rag",
                        "as_of_date": as_of_date.isoformat()
                    }
                }
            
            # Format results
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []
            
            self.logger.info(f"✅ [TEMPORAL_RAG] Found {len(documents)} documents matching temporal filter")
            
            formatted_docs = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                formatted_docs.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": dist,
                    "relevance_score": 1.0 - dist  # Convert distance to score
                })
            
            # Generate answer using LLM synthesis
            # ✅ FIX: Use LLM to synthesize answer from temporal-filtered documents (like standard RAG)
            try:
                if not formatted_docs:
                    answer = f"No documents found as of {as_of_date.date()}. This information may not have existed at that time."
                else:
                    # Build context from temporal-filtered documents
                    context_parts = []
                    for i, doc in enumerate(formatted_docs, 1):
                        file_path = doc.get("file_path", "Unknown")
                        content = doc.get("content", "")
                        relevance = doc.get("relevance_score", 0)
                        
                        context_parts.append(
                            f"[Source {i}] {file_path} (relevance: {relevance:.3f})\n"
                            f"{content}\n"
                        )
                    
                    context_text = "\n".join(context_parts)
                    
                    # Build temporal-aware prompt
                    prompt = f"""You are an intelligent assistant analyzing historical documentation.

**Context:** You are answering based on documents that existed as of {as_of_date.date()}.

**Important:** Only use information from the provided sources. If the sources don't contain enough information to answer the question, say so.

**Sources:**
{context_text}

**Question:** {query}

**Instructions:**
- Answer the question using ONLY the information from the provided sources
- Provide a detailed, comprehensive answer (3-5 paragraphs minimum)
- Include specific details, examples, and context from the sources
- If listing items, provide descriptions and explanations for each
- Reference which sources support your answer
- Remember: This is information as of {as_of_date.date()}

**Answer:**"""
                    
                    # Generate answer using Ollama router (3-tier routing)
                    self.logger.info(f"🤖 [TEMPORAL_RAG] Generating LLM answer from {len(formatted_docs)} temporal-filtered documents")
                    response = await self.ollama_router.generate(
                        prompt=prompt,
                        workload_type='rag',
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    answer = response.get("response", "").strip()
                    
                    if not answer:
                        answer = f"Found {len(formatted_docs)} documents as of {as_of_date.date()}, but failed to generate detailed answer."
                    
                    self.logger.info(f"✅ [TEMPORAL_RAG] LLM answer generated: {len(answer)} characters")
                    
            except Exception as answer_error:
                self.logger.error(f"Failed to generate answer: {answer_error}", exc_info=True)
                answer = f"Found {len(formatted_docs)} documents but failed to generate answer: {str(answer_error)}"
            
            return {
                "query": query,
                "as_of_date": as_of_date.isoformat(),
                "answer": answer,
                "documents": formatted_docs,
                "metadata": {
                    "temporal_filter_applied": True,
                    "filter": where_clause,
                    "documents_found": len(formatted_docs),
                    "query_type": "temporal_rag"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Temporal filtering failed: {e}", exc_info=True)
            raise
    
    async def query_as_of(
        self,
        query: str,
        as_of_date: datetime,
        timeline_id: Optional[UUID] = None,
        service_name: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Time-travel query: Get information as it existed at a specific point in time.
        
        Example:
            "What did the API documentation say about authentication on Jan 15, 2025?"
        
        Args:
            query: The question to answer
            as_of_date: Point in time to query
            timeline_id: Optional specific timeline to use
            service_name: Optional service filter
            limit: Maximum results
        
        Returns:
            Query results with temporal context
        """
        try:
            self.logger.info(f"⏰ Time-travel query as of {as_of_date.date()}: {query[:100]}")
            
            # ✅ PHASE 4: Use temporal filtering instead of falling back
            return await self._query_with_temporal_filter(
                query=query,
                as_of_date=as_of_date,
                service_name=service_name,
                limit=limit
            )
                
        except Exception as e:
            self.logger.error(f"Failed to perform query_as_of: {e}", exc_info=True)
            raise
    
    async def query_what_changed(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime,
        timeline_id: Optional[UUID] = None,
        service_name: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Change detection query: Find what changed about a topic between two dates.
        
        Example:
            "What changed in the authentication docs between Jan 1 and Mar 31?"
        
        Args:
            query: The topic to track changes for
            start_date: Start of time range
            end_date: End of time range
            timeline_id: Optional specific timeline
            service_name: Optional service filter
            limit: Maximum results per period
        
        Returns:
            Comparison showing changes over time
        """
        try:
            from ...utils.datetime_utils import ensure_utc
            
            # ✅ FIX: Ensure dates are UTC-aware to prevent timezone comparison errors
            start_date = ensure_utc(start_date)
            end_date = ensure_utc(end_date)
            
            self.logger.info(
                f"🔄 Change detection query from {start_date.date()} to {end_date.date()}: "
                f"{query[:100]}"
            )
            
            async with get_database().session() as session:
                # Get timeline
                timeline = await self._get_or_find_timeline(
                    session, timeline_id, service_name, start_date
                )
                
                if not timeline:
                    return {
                        "query": query,
                        "error": "No timeline found for change detection",
                        "results": []
                    }
                
                # Find periods in range
                periods = await self._find_periods_in_range(
                    session, timeline["id"], start_date, end_date
                )
                
                if len(periods) < 2:
                    return {
                        "query": query,
                        "warning": "Not enough periods for change detection",
                        "results": []
                    }
                
                self.logger.info(f"   📊 Analyzing {len(periods)} periods for changes")
                
                # Query each period
                period_results = []
                for period in periods:
                    doc_ids = await self._get_documents_in_period(session, period["id"])
                    
                    # Query RAG for this period
                    rag_results = await self.context_rag.query_with_context(
                        query=query,
                        service_filter=service_name,
                        limit=limit
                    )
                    
                    # Filter to period documents
                    filtered = [
                        r for r in rag_results["results"]
                        if r.get("document_id") in doc_ids
                    ][:limit]
                    
                    period_results.append({
                        "period": {
                            "id": str(period["id"]),
                            "name": period["name"],
                            "start": period["start_date"].isoformat(),
                            "end": period["end_date"].isoformat()
                        },
                        "results": filtered,
                        "result_count": len(filtered)
                    })
                
                # Analyze changes between periods
                changes = self._analyze_changes_between_periods(period_results)
                
                return {
                    "query": query,
                    "time_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "temporal_context": {
                        "timeline_id": str(timeline["id"]),
                        "timeline_name": timeline["name"],
                        "periods_analyzed": len(periods)
                    },
                    "period_results": period_results,
                    "changes_detected": changes,
                    "metadata": {
                        "service": service_name,
                        "query_type": "change_detection"
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to detect changes: {e}", exc_info=True)
            raise
    
    async def query_evolution(
        self,
        topic: str,
        timeline_id: Optional[UUID] = None,
        service_name: Optional[str] = None,
        limit_per_period: int = 3
    ) -> Dict[str, Any]:
        """
        Evolution tracking: Show how a topic evolved across all periods.
        
        Example:
            "How did the API authentication approach evolve over time?"
        
        Args:
            topic: The topic to track
            timeline_id: Optional timeline to analyze (use this OR service_name)
            service_name: Optional service name to find timeline for
            limit_per_period: Max results per period
        
        Returns:
            Evolution timeline showing changes across all periods
        """
        try:
            self.logger.info(f"📈 Evolution tracking for: {topic[:100]}")
            
            async with get_database().session() as session:
                timeline_repo = TimelineRepository(session)
                period_repo = TimePeriodRepository(session)
                
                # ✅ FIX: Get timeline by ID or service name
                if timeline_id:
                    timeline_model = await timeline_repo.get_by_id(timeline_id)
                    if not timeline_model:
                        raise ValueError(f"Timeline not found: {timeline_id}")
                elif service_name:
                    # Find timeline by service name
                    from sqlalchemy import select
                    from ...storage.db_models import TimelineModel
                    
                    result = await session.execute(
                        select(TimelineModel)
                        .where(TimelineModel.service_name == service_name)
                        .limit(1)
                    )
                    timeline_model = result.scalar_one_or_none()
                    
                    if not timeline_model:
                        # ✅ Create timeline if it doesn't exist
                        self.logger.info(f"📝 Creating timeline for service: {service_name}")
                        now = datetime.utcnow()
                        timeline_model = TimelineModel(
                            name=f"{service_name} Timeline",  # ✅ REQUIRED FIELD
                            service_name=service_name,
                            repo_path=f"/repo/services/{service_name}",  # ✅ REQUIRED FIELD
                            description=f"Auto-generated timeline for {service_name}",
                            start_date=datetime(2020, 1, 1),  # ✅ REQUIRED: Default start
                            end_date=now,  # ✅ REQUIRED: Current time as end
                            confidence_level="MEDIUM",  # ✅ REQUIRED: Confidence level
                            confidence_metadata={},  # ✅ REQUIRED: Empty metadata
                            period_strategy="adaptive",  # Already set by default
                            created_at=now,
                            updated_at=now
                        )
                        session.add(timeline_model)
                        await session.flush()
                        self.logger.info(f"✅ Timeline created: {timeline_model.id}")
                else:
                    raise ValueError("Either timeline_id or service_name must be provided")
                
                # Get all periods (use timeline_model.id since we have the model now)
                periods = await period_repo.get_by_timeline(timeline_model.id, order_by_sequence=True)
                
                self.logger.info(f"   📊 Tracking evolution across {len(periods)} periods")
                
                # Query each period
                evolution_data = []
                for period in periods:
                    doc_ids = await self._get_documents_in_period(session, period.id)
                    
                    if not doc_ids:
                        evolution_data.append({
                            "period": {
                                "id": str(period.id),
                                "name": period.name,
                                "sequence": period.sequence_number,
                                "start": period.start_date.isoformat(),
                                "end": period.end_date.isoformat()
                            },
                            "results": [],
                            "status": "no_documents"
                        })
                        continue
                    
                    # Query RAG
                    rag_results = await self.context_rag.query_with_context(
                        query=topic,
                        service_filter=timeline_model.service_name,
                        limit=limit_per_period * 2
                    )
                    
                    # Filter and rank
                    filtered = [
                        r for r in rag_results["results"]
                        if r.get("document_id") in doc_ids
                    ][:limit_per_period]
                    
                    evolution_data.append({
                        "period": {
                            "id": str(period.id),
                            "name": period.name,
                            "sequence": period.sequence_number,
                            "start": period.start_date.isoformat(),
                            "end": period.end_date.isoformat()
                        },
                        "results": filtered,
                        "result_count": len(filtered),
                        "document_count": len(doc_ids)
                    })
                
                # Identify major changes
                major_changes = self._identify_major_changes(evolution_data)
                
                return {
                    "topic": topic,
                    "timeline": {
                        "id": str(timeline_id),
                        "name": timeline_model.name,
                        "service": timeline_model.service_name,
                        "total_periods": len(periods)
                    },
                    "evolution": evolution_data,
                    "major_changes": major_changes,
                    "metadata": {
                        "query_type": "evolution_tracking"
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to track evolution: {e}", exc_info=True)
            raise
    
    # Helper methods
    
    async def _get_or_find_timeline(
        self,
        session: AsyncSession,
        timeline_id: Optional[UUID],
        service_name: Optional[str],
        reference_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Find or get timeline for query."""
        timeline_repo = TimelineRepository(session)
        
        if timeline_id:
            timeline_model = await timeline_repo.get_by_id(timeline_id)
            if timeline_model:
                return {
                    "id": timeline_model.id,
                    "name": timeline_model.name,
                    "service_name": timeline_model.service_name,
                    "confidence_level": timeline_model.confidence_level
                }
        
        if service_name:
            from ...utils.datetime_utils import ensure_utc_naive
            
            timelines = await timeline_repo.get_by_service(service_name, limit=10)
            # Find timeline that contains reference_date
            # ✅ FIX: Convert reference_date to naive for safe comparison with DB dates
            reference_naive = ensure_utc_naive(reference_date)
            for timeline in timelines:
                if timeline.start_date <= reference_naive <= timeline.end_date:
                    return {
                        "id": timeline.id,
                        "name": timeline.name,
                        "service_name": timeline.service_name,
                        "confidence_level": timeline.confidence_level
                    }
        
        return None
    
    async def _check_temporal_confidence(
        self,
        session: AsyncSession,
        timeline_id: UUID
    ) -> Dict[str, Any]:
        """Check if timeline has sufficient confidence for temporal queries."""
        timeline_repo = TimelineRepository(session)
        timeline = await timeline_repo.get_by_id(timeline_id)
        
        if not timeline:
            return {
                "can_use_temporal": False,
                "reason": "Timeline not found"
            }
        
        confidence_level = timeline.confidence_level
        
        # HIGH and MEDIUM confidence can use temporal features
        if confidence_level in ["HIGH", "MEDIUM"]:
            return {
                "can_use_temporal": True,
                "confidence_level": confidence_level,
                "reason": None
            }
        else:
            return {
                "can_use_temporal": False,
                "confidence_level": confidence_level,
                "reason": f"{confidence_level} confidence insufficient for temporal queries"
            }
    
    async def _find_period_for_date(
        self,
        session: AsyncSession,
        timeline_id: UUID,
        target_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Find period that contains the target date."""
        period_repo = TimePeriodRepository(session)
        periods = await period_repo.get_by_date_range(
            timeline_id, target_date, target_date
        )
        
        if periods:
            period = periods[0]
            return {
                "id": period.id,
                "name": period.name,
                "start_date": period.start_date,
                "end_date": period.end_date,
                "sequence_number": period.sequence_number
            }
        
        return None
    
    async def _find_closest_period(
        self,
        session: AsyncSession,
        timeline_id: UUID,
        target_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Find closest period to target date."""
        period_repo = TimePeriodRepository(session)
        periods = await period_repo.get_by_timeline(timeline_id, order_by_sequence=True)
        
        if not periods:
            return None
        
        # Find closest period
        closest = min(
            periods,
            key=lambda p: min(
                abs((p.start_date - target_date).total_seconds()),
                abs((p.end_date - target_date).total_seconds())
            )
        )
        
        return {
            "id": closest.id,
            "name": closest.name,
            "start_date": closest.start_date,
            "end_date": closest.end_date,
            "sequence_number": closest.sequence_number
        }
    
    async def _find_periods_in_range(
        self,
        session: AsyncSession,
        timeline_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Find all periods in date range.
        
        ✅ UTC STANDARDIZATION: Converts UTC-aware dates to naive for comparison with DB dates.
        """
        from ...utils.datetime_utils import ensure_utc_naive
        
        period_repo = TimePeriodRepository(session)
        # ✅ FIX: Convert input dates to naive for safe comparison with DB dates
        periods = await period_repo.get_by_date_range(
            timeline_id,
            ensure_utc_naive(start_date),
            ensure_utc_naive(end_date)
        )
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "sequence_number": p.sequence_number
            }
            for p in periods
        ]
    
    async def _get_documents_in_period(
        self,
        session: AsyncSession,
        period_id: UUID
    ) -> List[str]:
        """Get list of document IDs in a period."""
        placement_repo = DocumentPlacementRepository(session)
        placements = await placement_repo.get_by_period(period_id, limit=10000)
        
        return [str(p.document_id) for p in placements]
    
    async def _fallback_to_standard_rag(
        self,
        query: str,
        service_name: Optional[str],
        limit: int,
        confidence_warning: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback to standard RAG when temporal features unavailable."""
        self.logger.info("📄 Falling back to standard RAG (no temporal filtering)")
        
        results = await self.context_rag.query_with_context(
            query=query,
            service_filter=service_name,
            limit=limit
        )
        
        results["temporal_context"] = None
        results["metadata"]["query_type"] = "standard_rag_fallback"
        
        if confidence_warning:
            results["metadata"]["confidence_warning"] = confidence_warning
        
        return results
    
    def _analyze_changes_between_periods(
        self,
        period_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze changes between consecutive periods."""
        changes = []
        
        for i in range(len(period_results) - 1):
            current = period_results[i]
            next_period = period_results[i + 1]
            
            # Compare result counts
            count_change = next_period["result_count"] - current["result_count"]
            
            if count_change != 0:
                changes.append({
                    "from_period": current["period"]["name"],
                    "to_period": next_period["period"]["name"],
                    "change_type": "result_count",
                    "change": count_change,
                    "direction": "increase" if count_change > 0 else "decrease"
                })
            
            # TODO: Add content-based change detection (semantic similarity)
        
        return changes
    
    def _identify_major_changes(
        self,
        evolution_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify major changes in evolution timeline.
        
        ✅ FIX: Handle periods with status='no_documents' that don't have result_count.
        """
        major_changes = []
        
        for i in range(len(evolution_data) - 1):
            current = evolution_data[i]
            next_item = evolution_data[i + 1]
            
            # ✅ FIX: Safely get result_count, default to 0 if missing or if status is 'no_documents'
            current_count = current.get("result_count", 0) if current.get("status") != "no_documents" else 0
            next_count = next_item.get("result_count", 0) if next_item.get("status") != "no_documents" else 0
            
            # Detect significant changes (e.g., new documents, removed topics)
            if current_count == 0 and next_count > 0:
                major_changes.append({
                    "period": next_item["period"]["name"],
                    "type": "new_content",
                    "description": f"New content appeared in {next_item['period']['name']}"
                })
            elif current_count > 0 and next_count == 0:
                major_changes.append({
                    "period": next_item["period"]["name"],
                    "type": "content_removed",
                    "description": f"Content disappeared in {next_item['period']['name']}"
                })
        
        return major_changes

