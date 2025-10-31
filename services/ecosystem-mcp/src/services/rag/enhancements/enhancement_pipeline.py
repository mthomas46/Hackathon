"""
Enhancement Pipeline

Main orchestrator for RAG enhancements.
Extracted from AccuracyEnhancedRAG to be reusable by all RAG types.
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional

from .enhancement_config import EnhancementConfig
from .enhancement_hooks import EnhancementHooks
from .query_context import QueryContext

logger = logging.getLogger(__name__)


class EnhancementPipeline:
    """
    Modular enhancement pipeline for RAG queries.
    
    Orchestrates all enhancement phases:
    1. Query Preprocessing (difficulty, intent, rewriting)
    2. Filter Construction (metadata + custom filters)
    3. Retrieval (hybrid search or custom)
    4. Post-Retrieval Processing (reranking, quality filtering)
    5. Context Optimization (token budgeting, redundancy removal)
    6. Answer Generation (standard or custom)
    7. Post-Processing (confidence scoring, formatting)
    
    Supports hooks for customization by different RAG types.
    """
    
    def __init__(self):
        """Initialize enhancement pipeline with component services."""
        # Import enhancement components
        from ..hybrid_search import get_hybrid_search_service
        from ..query_rewriter import get_query_rewriter
        from ..confidence_scorer import get_confidence_scorer
        from ..bm25_search import get_bm25_service
        from ..reranker import get_reranker_service
        from ..context_optimizer import get_context_optimizer
        from ..metadata_filter import get_metadata_filter
        from ..query_intent_classifier import get_query_intent_classifier
        from ..contradiction_detector import get_contradiction_detector
        from ..query_difficulty_estimator import get_query_difficulty_estimator
        from ..unified_query_analyzer import get_unified_query_analyzer
        
        # Phase 1 components
        self.hybrid_search = get_hybrid_search_service()
        self.query_rewriter = get_query_rewriter()
        self.confidence_scorer = get_confidence_scorer()
        self.bm25_service = get_bm25_service()
        
        # Phase 2 components
        self.reranker = get_reranker_service()
        self.context_optimizer = get_context_optimizer()
        self.metadata_filter = get_metadata_filter()
        
        # Phase 5R component
        self.intent_classifier = get_query_intent_classifier()
        
        # Phase 7R components
        self.contradiction_detector = get_contradiction_detector()
        self.difficulty_estimator = get_query_difficulty_estimator()
        
        # Audit Phase 2A component
        self.unified_analyzer = get_unified_query_analyzer()
        
        logger.info("EnhancementPipeline initialized")
    
    async def execute(
        self,
        query: str,
        n_results: int,
        config: EnhancementConfig,
        hooks: Optional[EnhancementHooks] = None,
        generation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute enhancement pipeline.
        
        Args:
            query: User's query
            n_results: Number of documents to retrieve
            config: Enhancement configuration
            hooks: Optional hooks for customization
            generation_context: Optional context for answer generation
        
        Returns:
            Dict with documents, query_context, and metadata
        """
        start_time = time.time()
        hooks = hooks or EnhancementHooks()
        
        logger.info(f"🚀 Enhancement pipeline starting for query: {query[:80]}...")
        logger.info(
            f"   Config: hybrid={config.enable_hybrid_search}, "
            f"rewriting={config.enable_query_rewriting}, "
            f"reranking={config.enable_reranking}"
        )
        
        try:
            # ===== PHASE 1: Query Preprocessing =====
            query_context = await self._preprocess_query(query, config)
            
            # ===== PHASE 2: Filter Construction =====
            where_filters = await self._build_filters(query_context, config, hooks)
            
            # ===== PHASE 3: Retrieval =====
            documents = await self._retrieve_documents(
                query_context, where_filters, n_results, config, hooks
            )
            
            if not documents:
                logger.warning(f"   ⚠️  No documents retrieved")
                return {
                    "documents": [],
                    "query_context": query_context,
                    "metadata": {
                        "reason": "no_documents",
                        "elapsed_ms": int((time.time() - start_time) * 1000)
                    }
                }
            
            # ===== PHASE 4: Post-Retrieval Processing =====
            documents = await self._post_retrieval_process(
                documents, query_context, n_results, config, hooks
            )
            
            # ===== PHASE 5: Context Optimization =====
            if config.enable_context_optimization:
                documents = await self._optimize_context(documents, config)
            
            # ===== PHASE 6: Contradiction Detection =====
            contradiction_result = None
            if config.enable_contradiction_detection:
                contradiction_result = self.contradiction_detector.detect(
                    documents=documents,
                    question=query
                )
                if contradiction_result.get("has_contradictions"):
                    logger.warning(
                        f"   ⚠️  {contradiction_result['contradiction_count']} "
                        f"contradiction(s) detected"
                    )
            
            elapsed_total = time.time() - start_time
            logger.info(f"✅ Enhancement pipeline complete ({elapsed_total:.3f}s)")
            
            return {
                "documents": documents,
                "query_context": query_context,
                "contradiction_result": contradiction_result,
                "metadata": {
                    "elapsed_ms": int(elapsed_total * 1000),
                    "documents_count": len(documents),
                    "enhancements_applied": self._get_applied_enhancements(config)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Enhancement pipeline failed: {e}", exc_info=True)
            raise
    
    async def _preprocess_query(
        self,
        query: str,
        config: EnhancementConfig
    ) -> QueryContext:
        """
        Phase 1: Query preprocessing.
        
        Performs:
        - Difficulty estimation (early exit if impossible)
        - Intent classification (adaptive parameters)
        - Query rewriting (generate variants)
        """
        logger.info(f"   📝 Phase 1: Query preprocessing")
        
        # Create query context
        context = QueryContext(original_query=query)
        
        # ===== Unified Query Analysis (if enabled) =====
        if config.use_unified_analyzer and config.enable_difficulty_estimation and config.enable_intent_classification:
            logger.debug(f"      Using unified query analyzer")
            unified_result = self.unified_analyzer.analyze(query)
            
            context.difficulty = unified_result["difficulty"]
            context.intent = unified_result["intent"]
            
            logger.info(
                f"      Unified: difficulty={context.difficulty['difficulty_level']}, "
                f"intent={context.intent['type']}/{context.intent['complexity']}"
            )
        else:
            # ===== Separate Difficulty Estimation =====
            if config.enable_difficulty_estimation:
                context.difficulty = self.difficulty_estimator.estimate(query)
                logger.info(
                    f"      Difficulty: {context.difficulty['difficulty_level']} "
                    f"(score: {context.difficulty['difficulty_score']})"
                )
            
            # ===== Separate Intent Classification =====
            if config.enable_intent_classification:
                context.intent = self.intent_classifier.classify_heuristic(query)
                logger.info(
                    f"      Intent: {context.intent['type']}/{context.intent['complexity']} "
                    f"(confidence: {context.intent['confidence']:.2f})"
                )
                
                # Optional: LLM classification for low-confidence
                if config.enable_llm_intent and context.intent["confidence"] < 0.6:
                    context.intent = await self.intent_classifier.classify_llm(query)
                    logger.info(f"      LLM intent: {context.intent['type']}")
        
        # ===== Apply Adaptive Parameters =====
        if context.intent:
            context.adaptive_n_results = context.intent.get("n_results")
            context.adaptive_strategy = context.intent.get("strategy")
            context.adaptive_enable_reranking = context.intent.get("enable_reranking")
            
            if context.adaptive_n_results:
                logger.info(f"      Adaptive n_results: {context.adaptive_n_results}")
        
        # ===== Query Rewriting =====
        if config.enable_query_rewriting:
            logger.debug(f"      Rewriting query")
            rewrite_result = await self.query_rewriter.rewrite(
                query,
                enable_expansion=True,
                enable_clarification=True,
                enable_decomposition=True
            )
            context.query_variants = rewrite_result["search_queries"]
            context.rewritten_query = context.query_variants[0] if context.query_variants else None
            logger.info(f"      Generated {len(context.query_variants)} query variants")
        else:
            context.query_variants = [query]
        
        return context
    
    async def _build_filters(
        self,
        query_context: QueryContext,
        config: EnhancementConfig,
        hooks: EnhancementHooks
    ) -> Dict[str, Any]:
        """
        Phase 2: Filter construction.
        
        Builds metadata filters and applies custom filters from hooks.
        """
        logger.info(f"   🎯 Phase 2: Filter construction")
        
        where_filters = {}
        
        # ===== Metadata Filtering =====
        if config.enable_metadata_filtering:
            metadata_filters = self.metadata_filter.build_filters(
                query=query_context.original_query,
                quality_threshold=config.quality_threshold
            )
            if metadata_filters:
                where_filters.update(metadata_filters)
                logger.info(f"      Metadata filters: {len(metadata_filters)} conditions")
        
        # ===== Custom Pre-Retrieval Filters (Hook) =====
        if hooks.has_pre_retrieval_filter():
            logger.debug(f"      Applying custom pre-retrieval filter")
            custom_filters = await hooks.pre_retrieval_filter(query_context)
            if custom_filters:
                where_filters.update(custom_filters)
                logger.info(f"      Custom filters: {len(custom_filters)} conditions")
        
        query_context.metadata_filters = where_filters
        return where_filters
    
    async def _retrieve_documents(
        self,
        query_context: QueryContext,
        where_filters: Dict[str, Any],
        n_results: int,
        config: EnhancementConfig,
        hooks: EnhancementHooks
    ) -> List[Dict[str, Any]]:
        """
        Phase 3: Retrieval.
        
        Uses custom retrieval if provided, else hybrid search.
        """
        logger.info(f"   🔍 Phase 3: Retrieval")
        
        # Use adaptive n_results if available
        effective_n_results = query_context.get_n_results(n_results)
        
        # Increase initial retrieval if reranking enabled
        initial_n_results = effective_n_results * 10 if config.enable_reranking else effective_n_results
        
        # ===== Custom Retrieval (Hook) =====
        if hooks.has_custom_retrieval():
            logger.info(f"      Using custom retrieval function")
            documents = await hooks.retrieval_fn(
                query_context, where_filters, initial_n_results
            )
            logger.info(f"      Custom retrieval: {len(documents)} documents")
            return documents
        
        # ===== Hybrid Search (Default) =====
        if config.enable_hybrid_search:
            logger.info(f"      Using hybrid search")
            all_documents = []
            
            # Optimize: Use fewer variants for simple queries
            query_is_simple = len(query_context.query_variants) == 1 or len(query_context.original_query.split()) <= 5
            max_variants = 1 if query_is_simple else 2
            
            # Search all variants in parallel
            variant_tasks = []
            for query_variant in query_context.query_variants[:max_variants]:
                task = self.hybrid_search.search(
                    query=query_variant,
                    n_results=initial_n_results,
                    semantic_weight=config.semantic_weight,
                    keyword_weight=config.keyword_weight,
                    where=where_filters if where_filters else None,
                    quality_boost=True,
                    query_intent=query_context.intent
                )
                variant_tasks.append(task)
            
            if variant_tasks:
                logger.debug(f"      Running {len(variant_tasks)} variant searches in parallel")
                variant_results = await asyncio.gather(*variant_tasks)
                
                for docs in variant_results:
                    all_documents.extend(docs)
            
            # Deduplicate and sort
            seen_ids = set()
            unique_docs = []
            for doc in all_documents:
                if doc["id"] not in seen_ids:
                    seen_ids.add(doc["id"])
                    unique_docs.append(doc)
            
            unique_docs.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
            documents = unique_docs[:initial_n_results]
            
            logger.info(f"      Hybrid search: {len(all_documents)} total → {len(documents)} unique")
            return documents
        
        # ===== Fallback: Should not reach here =====
        logger.warning(f"      No retrieval method available!")
        return []
    
    async def _post_retrieval_process(
        self,
        documents: List[Dict[str, Any]],
        query_context: QueryContext,
        n_results: int,
        config: EnhancementConfig,
        hooks: EnhancementHooks
    ) -> List[Dict[str, Any]]:
        """
        Phase 4: Post-retrieval processing.
        
        Performs:
        - Custom post-retrieval processing (hook)
        - Smart reranking decision
        - Cross-encoder reranking (if enabled)
        - Quality filtering
        """
        logger.info(f"   ⚙️  Phase 4: Post-retrieval processing")
        
        # ===== Custom Post-Retrieval Processing (Hook) =====
        if hooks.has_post_retrieval_processor():
            logger.debug(f"      Applying custom post-retrieval processor")
            documents = await hooks.post_retrieval_processor(documents, query_context)
            logger.info(f"      Post-processing: {len(documents)} documents")
        
        # ===== Smart Reranking Decision =====
        should_rerank = False
        rerank_reason = ""
        
        # Get effective n_results
        effective_n_results = query_context.get_n_results(n_results)
        
        if config.enable_reranking:
            should_rerank = True
            rerank_reason = "explicitly enabled"
        elif query_context.difficulty and query_context.difficulty["difficulty_level"] == "hard":
            should_rerank = True
            rerank_reason = "hard query detected"
        elif query_context.intent and query_context.intent.get("enable_reranking"):
            should_rerank = True
            rerank_reason = "intent suggests reranking"
        
        # Skip reranking for simple queries
        if should_rerank and query_context.intent and query_context.intent["complexity"] == "simple":
            should_rerank = False
            rerank_reason = "simple query, skipping for speed"
        
        # Skip reranking for comparative queries (timeout prevention)
        comparative_keywords = ["compare", "vs", "versus", "difference between", "differences between"]
        is_comparative = any(kw in query_context.original_query.lower() for kw in comparative_keywords)
        if should_rerank and is_comparative:
            should_rerank = False
            rerank_reason = "comparative query, skipping to prevent timeout"
        
        # ===== Cross-Encoder Reranking =====
        if should_rerank and documents:
            logger.info(f"      Reranking: {rerank_reason}")
            
            # Quality-based early pruning
            high_quality_docs = [d for d in documents if d.get("quality_score", 0) >= 50]
            
            if len(high_quality_docs) >= effective_n_results:
                logger.info(
                    f"      Quality pruning: {len(high_quality_docs)} high-quality docs "
                    f"(pruned {len(documents) - len(high_quality_docs)})"
                )
                docs_to_rerank = high_quality_docs[:40]
            else:
                logger.info(f"      Not enough high-quality docs, reranking all")
                docs_to_rerank = documents[:40]
            
            # Rerank with timeout protection
            try:
                documents = await asyncio.wait_for(
                    self.reranker.rerank(
                        query=query_context.original_query,
                        documents=docs_to_rerank,
                        top_k=effective_n_results
                    ),
                    timeout=30.0
                )
                logger.info(f"      Reranked to top {len(documents)} documents")
            except asyncio.TimeoutError:
                logger.warning(f"      Reranking timed out, using original ranking")
                documents = docs_to_rerank[:effective_n_results]
            except Exception as e:
                logger.error(f"      Reranking failed: {e}, using original ranking")
                documents = docs_to_rerank[:effective_n_results]
        else:
            logger.info(f"      Reranking disabled: {rerank_reason or 'not enabled'}")
            documents = documents[:effective_n_results]
        
        # ===== Relative Quality Filtering =====
        logger.debug(f"      Applying relative quality filter")
        documents = self.context_optimizer.filter_by_relative_quality(
            documents=documents,
            min_ratio=0.5,
            min_documents=5
        )
        logger.info(f"      Quality filtered to {len(documents)} documents")
        
        return documents
    
    async def _optimize_context(
        self,
        documents: List[Dict[str, Any]],
        config: EnhancementConfig
    ) -> List[Dict[str, Any]]:
        """
        Phase 5: Context optimization.
        
        Performs token budgeting and redundancy removal.
        """
        logger.info(f"   🎨 Phase 5: Context optimization")
        logger.info(f"      Strategy: {config.context_strategy}")
        
        documents = self.context_optimizer.optimize(
            documents=documents,
            max_tokens=4000,
            strategy=config.context_strategy
        )
        
        logger.info(f"      Optimized to {len(documents)} documents")
        return documents
    
    def _get_applied_enhancements(self, config: EnhancementConfig) -> List[str]:
        """Get list of applied enhancements."""
        enhancements = []
        
        if config.enable_hybrid_search:
            enhancements.append("hybrid_search")
        if config.enable_query_rewriting:
            enhancements.append("query_rewriting")
        if config.enable_confidence_scoring:
            enhancements.append("confidence_scoring")
        if config.enable_reranking:
            enhancements.append("reranking")
        if config.enable_context_optimization:
            enhancements.append("context_optimization")
        if config.enable_metadata_filtering:
            enhancements.append("metadata_filtering")
        if config.enable_intent_classification:
            enhancements.append("intent_classification")
        if config.enable_contradiction_detection:
            enhancements.append("contradiction_detection")
        if config.enable_difficulty_estimation:
            enhancements.append("difficulty_estimation")
        
        return enhancements

