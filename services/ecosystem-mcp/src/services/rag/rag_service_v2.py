"""
RAG Service for intelligent question answering - REFACTORED to use Enhancement Pipeline.

PHASE 3: Integrated with modular enhancement system.

Changes from original:
- Uses EnhancementPipeline for orchestration
- Hybrid search enabled by default (semantic + BM25)
- Query rewriting for better results
- Context optimization for relevant information
- Confidence scoring for answer quality
- Expected: 10x better document retrieval (1 → 10 sources)

Backward compatible with original API.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from ...storage.chromadb_client import get_chroma_client
from ...storage import get_database
from ...storage.repositories import DocumentRepository
from ..models.ollama_router import get_ollama_router
from ..embeddings.embedding_service import get_embedding_service
from ...config import settings
from ...utils.cache_decorator import cache

# ✨ PHASE 3: Import enhancement pipeline
from .enhancements import (
    EnhancementPipeline,
    EnhancementConfig,
    EnhancementHooks,
    QueryContext
)

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval Augmented Generation service - Enhanced with Pipeline.
    
    PHASE 3 Features:
    - ✅ Hybrid search (semantic + BM25) for better recall
    - ✅ Query rewriting for synonym expansion
    - ✅ Context optimization for relevance
    - ✅ Confidence scoring for quality assessment
    - ✅ Modular enhancement system
    
    Legacy Features (preserved):
    - Semantic search with version/recency-aware scoring
    - LLM-based answer synthesis
    - Source citation tracking
    - Conversational context support
    - Answer caching (PHASE 4R)
    """
    
    def __init__(self):
        """Initialize RAG service with enhancement pipeline."""
        self.chroma = get_chroma_client()
        self.ollama_router = get_ollama_router()
        self.embedding_service = get_embedding_service()
        
        # Legacy scoring parameters (preserved for backward compatibility)
        self.recency_weight = 0.15  # 15% weight for recency
        self.version_boost = 0.10   # 10% boost for version match
        
        # ✨ PHASE 3: Initialize enhancement pipeline with "default" preset
        try:
            self.enhancement_pipeline = EnhancementPipeline()
            self.use_enhancements = True
            logger.info("✅ RAGService initialized with EnhancementPipeline (Phase 3)")
        except Exception as e:
            logger.warning(f"⚠️  EnhancementPipeline initialization failed: {e}. Falling back to legacy mode.")
            self.enhancement_pipeline = None
            self.use_enhancements = False
        
        logger.info("RAGService initialized with Ollama router")
    
    @cache(ttl=1800, key_prefix="rag_answer_v2")  # ⚡ PHASE 4R: Cache answers for 30 min
    async def _get_cached_answer(
        self,
        question: str,
        n_results: int,
        prefer_recent: bool,
        temperature: float,
        response_length: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached answer for a question.
        
        PHASE 4R: Cache complete answer by question only (NOT context).
        """
        logger.debug(f"💾 Answer cache MISS for: {question[:60]}...")
        return None
    
    async def ask(
        self,
        question: str,
        n_results: int = 10,
        context: Optional[List[Dict[str, Any]]] = None,
        prefer_recent: bool = True,
        temperature: float = 0.7,
        response_length: int = 1000,
        # ✨ PHASE 3: New enhancement control parameters
        use_enhancements: Optional[bool] = None,
        enable_hybrid_search: Optional[bool] = None,
        enable_query_rewriting: Optional[bool] = None,
        enable_context_optimization: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG.
        
        PHASE 3 ENHANCEMENTS:
        - Hybrid search for better recall
        - Query rewriting for better understanding
        - Context optimization for relevance
        - Confidence scoring for quality
        
        Args:
            question: User's question
            n_results: Number of documents to retrieve
            context: Previous conversation context
            prefer_recent: Whether to boost recent documents
            temperature: LLM temperature (0.0-1.0)
            response_length: Maximum tokens in response
            use_enhancements: Whether to use enhancement pipeline (default: True)
            enable_hybrid_search: Enable hybrid search (default: True)
            enable_query_rewriting: Enable query rewriting (default: True)
            enable_context_optimization: Enable context optimization (default: True)
        
        Returns:
            Dict with answer, sources, and metadata
        """
        logger.info(f"📝 RAG query: {question[:100]}...")
        start_time = time.time()
        
        # ✨ PHASE 3: Determine whether to use enhancements
        should_use_enhancements = (
            self.use_enhancements and  # Pipeline available
            (use_enhancements is None or use_enhancements)  # Not explicitly disabled
        )
        
        try:
            # === PHASE 4R: Try cached answer first ===
            cached_start = time.time()
            cached_answer = await self._get_cached_answer(
                question=question,
                n_results=n_results,
                prefer_recent=prefer_recent,
                temperature=temperature,
                response_length=response_length
            )
            cache_check_time = time.time() - cached_start
            
            if cached_answer is not None:
                total_time = time.time() - start_time
                logger.info(
                    f"✅ RAG cache HIT: {question[:60]}... "
                    f"({total_time:.3f}s, ~{1.5/total_time:.0f}x faster)"
                )
                cached_answer["metadata"]["cached"] = True
                cached_answer["metadata"]["cache_time_ms"] = int(total_time * 1000)
                return cached_answer
            
            logger.debug(f"   Cache check: {cache_check_time:.3f}s")
            
            # === PHASE 3: Use enhancement pipeline or legacy flow ===
            if should_use_enhancements and self.enhancement_pipeline:
                logger.info("✨ Using EnhancementPipeline (Phase 3)")
                result = await self._ask_with_enhancements(
                    question=question,
                    n_results=n_results,
                    context=context,
                    prefer_recent=prefer_recent,
                    temperature=temperature,
                    response_length=response_length,
                    enable_hybrid_search=enable_hybrid_search,
                    enable_query_rewriting=enable_query_rewriting,
                    enable_context_optimization=enable_context_optimization,
                    start_time=start_time
                )
            else:
                logger.info("📋 Using legacy RAG flow")
                result = await self._ask_legacy(
                    question=question,
                    n_results=n_results,
                    context=context,
                    prefer_recent=prefer_recent,
                    temperature=temperature,
                    response_length=response_length,
                    start_time=start_time
                )
            
            # Cache the result
            try:
                from ...utils.cache_decorator import get_cache_client
                cache_client = get_cache_client()
                if cache_client:
                    cache_key = f"rag_answer_v2:{question}:{n_results}:{prefer_recent}:{temperature}:{response_length}"
                    await cache_client.set(cache_key, result, ttl=1800)
                    logger.debug(f"   💾 Answer cached for future queries")
            except Exception as cache_error:
                logger.warning(f"Failed to cache answer: {cache_error}")
            
            return result
        
        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            raise
    
    async def _ask_with_enhancements(
        self,
        question: str,
        n_results: int,
        context: Optional[List[Dict[str, Any]]],
        prefer_recent: bool,
        temperature: float,
        response_length: int,
        enable_hybrid_search: Optional[bool],
        enable_query_rewriting: Optional[bool],
        enable_context_optimization: Optional[bool],
        start_time: float
    ) -> Dict[str, Any]:
        """
        Answer using enhancement pipeline (PHASE 3).
        
        This is the new, enhanced flow that uses the modular pipeline.
        """
        # Build enhancement config
        config = EnhancementConfig.default()
        
        # Apply overrides
        if enable_hybrid_search is not None:
            config.enable_hybrid_search = enable_hybrid_search
        if enable_query_rewriting is not None:
            config.enable_query_rewriting = enable_query_rewriting
        if enable_context_optimization is not None:
            config.enable_context_optimization = enable_context_optimization
        
        # Always enable confidence scoring for standard RAG
        config.enable_confidence_scoring = True
        
        # Standard RAG doesn't need expensive reranking
        config.enable_reranking = False
        
        logger.info(f"   Config: hybrid={config.enable_hybrid_search}, "
                   f"rewriting={config.enable_query_rewriting}, "
                   f"context_opt={config.enable_context_optimization}")
        
        # Create query context
        query_context = QueryContext(
            original_query=question,
            adaptive_n_results=n_results
        )
        
        # Create hooks for standard RAG retrieval
        hooks = EnhancementHooks(
            # Custom generation to use our _generate_answer method
            generation_fn=lambda ctx, docs, conf: self._generate_answer(
                question=question,
                context=self._build_context(docs),
                conversation_history=context,
                temperature=temperature,
                retrieved_documents=docs,
                max_tokens=response_length
            )
        )
        
        # Execute pipeline
        pipeline_start = time.time()
        result = await self.enhancement_pipeline.execute(
            config=config,
            hooks=hooks,
            query_context=query_context
        )
        pipeline_time = time.time() - pipeline_start
        
        # Extract results
        answer = result.get("answer", "")
        documents = result.get("documents", [])
        confidence_data = result.get("confidence", {})
        
        # Format sources
        sources = self._format_sources(documents)
        
        # Calculate confidence (use pipeline confidence or fallback)
        confidence = confidence_data.get("overall_score", 0.0) if confidence_data else self._calculate_confidence(documents, answer)
        
        total_time = time.time() - start_time
        
        final_result = {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "metadata": {
                "documents_used": len(documents),
                "temperature": temperature,
                "prefer_recent": prefer_recent,
                "top_score": documents[0].get("adjusted_score", 0.0) if documents else 0.0,
                "cached": False,
                "total_time_ms": int(total_time * 1000),
                "pipeline_time_ms": int(pipeline_time * 1000),
                "enhancement_mode": "pipeline_v1",  # Phase 3 indicator
                "enhancements_used": {
                    "hybrid_search": config.enable_hybrid_search,
                    "query_rewriting": config.enable_query_rewriting,
                    "context_optimization": config.enable_context_optimization
                }
            }
        }
        
        logger.info(
            f"✅ RAG complete (enhanced): {question[:60]}... "
            f"({total_time:.3f}s, {len(sources)} sources, {confidence:.0%} confidence)"
        )
        
        return final_result
    
    async def _ask_legacy(
        self,
        question: str,
        n_results: int,
        context: Optional[List[Dict[str, Any]]],
        prefer_recent: bool,
        temperature: float,
        response_length: int,
        start_time: float
    ) -> Dict[str, Any]:
        """
        Answer using legacy flow (fallback).
        
        This is the original implementation, preserved for backward compatibility.
        """
        # Step 1: Retrieve relevant documents with enhanced scoring
        retrieval_start = time.time()
        documents = await self._retrieve_with_scoring(
            question,
            n_results=n_results,
            prefer_recent=prefer_recent
        )
        retrieval_time = time.time() - retrieval_start
        logger.debug(f"   Retrieval: {retrieval_time:.3f}s")
        
        if not documents:
            return {
                "answer": "I don't have enough information to answer that question.",
                "sources": [],
                "confidence": 0.0,
                "metadata": {"reason": "no_relevant_documents", "cached": False}
            }
        
        # Step 2: Build context
        context_build_start = time.time()
        context_text = self._build_context(documents)
        context_build_time = time.time() - context_build_start
        logger.debug(f"   Context build: {context_build_time:.3f}s")
        
        # Step 3: Generate answer
        generation_start = time.time()
        answer = await self._generate_answer(
            question=question,
            context=context_text,
            conversation_history=context,
            temperature=temperature,
            retrieved_documents=documents,
            max_tokens=response_length
        )
        generation_time = time.time() - generation_start
        logger.debug(f"   Generation: {generation_time:.3f}s")
        
        # Step 4: Format sources
        sources = self._format_sources(documents)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(documents, answer)
        
        total_time = time.time() - start_time
        
        result = {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "metadata": {
                "documents_used": len(documents),
                "temperature": temperature,
                "prefer_recent": prefer_recent,
                "top_score": documents[0]["adjusted_score"] if documents else 0.0,
                "cached": False,
                "total_time_ms": int(total_time * 1000),
                "retrieval_time_ms": int(retrieval_time * 1000),
                "generation_time_ms": int(generation_time * 1000),
                "enhancement_mode": "legacy"
            }
        }
        
        logger.info(
            f"✅ RAG complete (legacy): {question[:60]}... "
            f"({total_time:.3f}s: retrieve {retrieval_time:.2f}s + generate {generation_time:.2f}s)"
        )
        
        return result
    
    # ========================================================================
    # Legacy methods preserved for backward compatibility and fallback
    # ========================================================================
    
    @cache(ttl=1800, key_prefix="chroma_search")
    async def _retrieve_with_scoring(
        self,
        query: str,
        n_results: int = 10,
        prefer_recent: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with recency and version-aware scoring (CACHED).
        
        Legacy method preserved for fallback mode.
        """
        # Get embedding for query
        embedding_result = await self.embedding_service.generate_embedding(query)
        query_embedding = embedding_result["embedding"]
        
        # Search ChromaDB
        results = await self.chroma.query(
            query_embeddings=[query_embedding],
            n_results=n_results * 2
        )
        
        if not results or "ids" not in results or not results["ids"]:
            return []
        
        # Get document metadata from database
        async with get_database().session() as session:
            repo = DocumentRepository(session)
            
            # Bulk fetch documents
            doc_ids = results["ids"][0]
            bulk_fetch_start = time.time()
            documents = await repo.get_by_ids_bulk(doc_ids)
            bulk_fetch_time = (time.time() - bulk_fetch_start) * 1000
            
            logger.debug(
                f"   📦 Bulk fetch: {len(documents)} docs in {bulk_fetch_time:.1f}ms"
            )
            
            # Create document lookup map
            doc_map = {str(doc.id): doc for doc in documents}
            
            enhanced_docs = []
            for i, doc_id in enumerate(doc_ids):
                try:
                    doc = doc_map.get(str(doc_id))
                    if not doc:
                        continue
                    
                    base_score = results["distances"][0][i] if "distances" in results else 0.5
                    
                    adjusted_score = self._adjust_score(
                        base_score=base_score,
                        document=doc,
                        query=query,
                        prefer_recent=prefer_recent
                    )
                    
                    content = ""
                    if "documents" in results and results["documents"] and len(results["documents"]) > 0:
                        if results["documents"][0] and i < len(results["documents"][0]):
                            content = results["documents"][0][i]
                    
                    enhanced_docs.append({
                        "id": str(doc.id),
                        "file_path": doc.file_path,
                        "content": content,
                        "metadata": doc.doc_metadata or {},
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                        "base_score": base_score,
                        "adjusted_score": adjusted_score,
                        "recency_days": (datetime.utcnow() - doc.updated_at).days if doc.updated_at else 9999
                    })
                
                except Exception as e:
                    logger.warning(f"Failed to enhance document {doc_id}: {e}")
                    continue
            
            # Deduplicate
            seen_hashes = set()
            unique_docs = []
            for doc in enhanced_docs:
                content_preview = (doc.get('content') or "")[:100]
                doc_key = doc["metadata"].get("content_hash", f"{doc['file_path']}:{content_preview}")
                if doc_key not in seen_hashes:
                    seen_hashes.add(doc_key)
                    unique_docs.append(doc)
            
            # Sort and return top N
            unique_docs.sort(key=lambda x: x["adjusted_score"], reverse=True)
            return unique_docs[:n_results]
    
    def _adjust_score(self, base_score: float, document: Any, query: str, prefer_recent: bool) -> float:
        """Adjust similarity score based on recency and version."""
        import re
        
        score = base_score
        
        # Recency adjustment
        if prefer_recent and document.updated_at:
            days_old = (datetime.utcnow() - document.updated_at).days
            
            if days_old <= 7:
                recency_boost = self.recency_weight
            elif days_old <= 30:
                recency_boost = self.recency_weight * 0.67
            elif days_old <= 90:
                recency_boost = self.recency_weight * 0.33
            else:
                recency_boost = 0.0
            
            score += recency_boost
        
        # Version matching boost
        query_versions = self._extract_versions(query)
        doc_versions = self._extract_versions(document.file_path)
        
        if query_versions and doc_versions:
            if any(qv in doc_versions for qv in query_versions):
                score += self.version_boost
        
        return min(1.0, max(0.0, score))
    
    def _extract_versions(self, text: str) -> List[str]:
        """Extract version numbers from text."""
        import re
        
        patterns = [
            r'v(\d+\.\d+(?:\.\d+)?)',
            r'version[:\s]+(\d+\.\d+(?:\.\d+)?)',
            r'(\d+\.\d+\.\d+)',
        ]
        
        versions = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            versions.extend(matches)
        
        return list(set(versions))
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context text from documents."""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            recency_days = doc.get('recency_days', None)
            recency = f" (Updated: {recency_days} days ago)" if recency_days is not None and recency_days < 90 else ""
            
            content = doc.get('content', doc.get('content_snippet', doc.get('normalized_content', doc.get('original_content', ''))))
            if not content:
                content = "[Content not available]"
            
            context_parts.append(
                f"[Source {i}] {doc['file_path']}{recency}\n"
                f"{content}\n"
            )
        
        return "\n---\n\n".join(context_parts)
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        retrieved_documents: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1000
    ) -> str:
        """Generate answer using LLM."""
        # Build conversation history
        history_text = ""
        if conversation_history:
            for turn in conversation_history[-3:]:
                history_text += f"Q: {turn.get('question', '')}\nA: {turn.get('answer', '')}\n\n"
        
        # Build prompt
        prompt = self._build_prompt(
            question=question,
            context=context,
            history=history_text,
            max_tokens=max_tokens
        )
        
        # Generate response
        response = await self.ollama_router.generate(
            prompt=prompt,
            workload_type='rag',
            temperature=temperature,
            max_tokens=max_tokens,
            context=history_text,
            context_docs=retrieved_documents
        )
        
        return response.get("response", "").strip()
    
    def _build_prompt(self, question: str, context: str, history: str = "", max_tokens: int = 1000) -> str:
        """Build RAG prompt for LLM."""
        # Length instruction based on max_tokens
        if max_tokens <= 200:
            length_instruction = "Be VERY BRIEF and concise, limiting your answer to key points only (1-2 short paragraphs)."
        elif max_tokens <= 500:
            length_instruction = "Be concise but cover the main points (2-3 paragraphs)."
        elif max_tokens <= 1000:
            length_instruction = "Provide a balanced answer with moderate detail (3-5 paragraphs)."
        elif max_tokens <= 2000:
            length_instruction = "Provide a DETAILED and comprehensive answer (5-10 paragraphs minimum)."
        else:
            length_instruction = "Provide an EXTREMELY DETAILED and exhaustive answer (10+ paragraphs minimum)."
        
        prompt = f"""You are an intelligent assistant for the Ecosystem-MCP microservices documentation system.

Your role is to answer questions accurately based on the provided context from indexed documentation.

GUIDELINES:
1. Answer based ONLY on the provided context
2. If the context doesn't contain the answer, say "I don't have enough information"
3. Cite sources using [Source N] notation when referencing information
4. {length_instruction}
5. If information is outdated, mention the update date
6. Prioritize recent information when conflicting information exists
7. Structure your answer with clear sections and headings when appropriate

"""
        
        if history:
            prompt += f"CONVERSATION HISTORY:\n{history}\n"
        
        prompt += f"""CONTEXT FROM DOCUMENTATION:

{context}

QUESTION: {question}

ANSWER (based on the context above):"""
        
        return prompt
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for citation."""
        sources = []
        total_docs = len(documents)
        
        for i, doc in enumerate(documents, 1):
            percentile_rank = int(((total_docs - i + 1) / total_docs) * 100)
            
            actual_score = (
                doc.get("rerank_score") or
                doc.get("hybrid_score") or
                doc.get("adjusted_score") or
                doc.get("base_score") or
                doc.get("semantic_score") or
                0.0
            )
            
            # Normalize score for display
            if actual_score < 0.1 and doc.get("hybrid_score"):
                display_score = percentile_rank / 100
            elif actual_score > 1.0 or actual_score < 0:
                display_score = 1.0 / (1.0 + abs(actual_score)) if actual_score < 0 else min(actual_score / 10, 1.0)
            else:
                display_score = actual_score
            
            score_type = self._detect_score_type(doc)
            
            adjusted_score = (
                doc.get("adjusted_score") or 
                doc.get("hybrid_score") or 
                doc.get("base_score") or 
                0.0
            )
            
            quality_score = (
                doc.get("quality_score") or
                doc.get("metadata", {}).get("quality_score") or
                doc.get("full_metadata", {}).get("quality_score") or
                None
            )
            
            sources.append({
                "id": i,
                "file_path": doc["file_path"],
                "relevance_score": round(display_score, 3),
                "adjusted_score": round(adjusted_score, 3),
                "percentile_rank": percentile_rank,
                "actual_score": round(actual_score, 4),
                "score_type": score_type,
                "quality_score": quality_score,
                "quality_grade": doc.get("quality_grade"),
                "recency_days": doc.get("recency_days"),
                "updated_at": doc.get("updated_at")
            })
        
        return sources
    
    def _detect_score_type(self, doc: Dict[str, Any]) -> str:
        """Detect which scoring method was used."""
        if "rerank_score" in doc:
            return "reranked"
        elif "hybrid_score" in doc:
            return "hybrid"
        elif "semantic_score" in doc:
            return "semantic"
        else:
            return "standard"
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]], answer: str) -> float:
        """Calculate confidence in the answer."""
        if not documents:
            return 0.0
        
        top_score = documents[0].get("adjusted_score", 0.5)
        high_relevance_count = sum(1 for d in documents if d.get("adjusted_score", 0) > 0.7)
        support_score = min(1.0, high_relevance_count / 3)
        
        if len(answer) < 50 or "don't have enough information" in answer.lower():
            completeness = 0.3
        elif len(answer) < 150:
            completeness = 0.6
        else:
            completeness = 1.0
        
        confidence = (
            top_score * 0.5 +
            support_score * 0.3 +
            completeness * 0.2
        )
        
        return round(confidence, 3)


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get the global RAG service instance.
    
    Returns:
        RAGService instance
    """
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService()
    
    return _rag_service

