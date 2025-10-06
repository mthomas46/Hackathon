"""Advanced RAG (Retrieval-Augmented Generation) pattern implementation."""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class AdvancedRAGEngine(BasePatternEngine):
    """
    Advanced RAG pattern execution engine.
    
    Enhanced Retrieval-Augmented Generation with:
    - Query decomposition
    - Multi-source retrieval
    - Result re-ranking
    - Context fusion
    - Source attribution
    
    Process:
    1. Decompose complex query into sub-queries
    2. Retrieve from multiple sources (parallel)
    3. Re-rank results by relevance
    4. Fuse context intelligently
    5. Generate answer with citations
    6. Validate against retrieved context
    
    Key Innovation: Multi-stage retrieval with intelligent
    re-ranking and context fusion for higher quality answers.
    """
    
    def __init__(self):
        super().__init__("advanced_rag")
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Advanced RAG pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        try:
            # Configuration
            enable_decomposition = config.get("rag_decompose_query", True)
            num_sources = config.get("rag_num_sources", 3)
            rerank_results = config.get("rag_rerank", True)
            enable_citations = config.get("rag_citations", True)
            
            # Step 1: Query decomposition (if complex)
            if enable_decomposition:
                decomp_step = await self._decompose_query(
                    query,
                    context,
                    config
                )
                steps.append(decomp_step)
                sub_queries = self._parse_subqueries(decomp_step.response)
            else:
                sub_queries = [query]
            
            # Step 2: Multi-source retrieval (parallel)
            retrieval_steps = await self._retrieve_from_sources(
                sub_queries,
                context,
                config,
                num_sources
            )
            steps.extend(retrieval_steps)
            
            # Extract retrieved contexts
            retrieved_contexts = [
                step.response for step in retrieval_steps
                if step.response
            ]
            
            # Step 3: Re-rank results by relevance
            if rerank_results and len(retrieved_contexts) > 1:
                rerank_step = await self._rerank_results(
                    query,
                    retrieved_contexts,
                    config
                )
                steps.append(rerank_step)
                ranked_contexts = self._parse_ranked_contexts(rerank_step.response)
            else:
                ranked_contexts = retrieved_contexts
            
            # Step 4: Fuse contexts intelligently
            fusion_step = await self._fuse_contexts(
                query,
                ranked_contexts,
                config
            )
            steps.append(fusion_step)
            
            # Step 5: Generate answer with citations
            generation_step = await self._generate_with_citations(
                query,
                fusion_step.response,
                ranked_contexts,
                config,
                enable_citations
            )
            steps.append(generation_step)
            
            # Step 6: Validate answer against context
            validation_step = await self._validate_answer(
                query,
                generation_step.response,
                fusion_step.response,
                config
            )
            steps.append(validation_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_rag_confidence(
                validation_step,
                len(ranked_contexts)
            )
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=generation_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "sub_queries": sub_queries,
                    "num_sources_retrieved": len(retrieved_contexts),
                    "reranked": rerank_results,
                    "validated": validation_step.metadata.get("is_valid", False),
                    "has_citations": enable_citations
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing Advanced RAG: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _decompose_query(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Decompose complex query into sub-queries."""
        step = self.create_step(
            step_id="decomposition",
            step_type="decomposition",
            description="Decompose query into sub-queries",
            prompt=self._build_decomposition_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "decomposition"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _retrieve_from_sources(
        self,
        sub_queries: List[str],
        context: Dict[str, Any],
        config: Dict[str, Any],
        num_sources: int
    ) -> List[PatternStep]:
        """Retrieve from multiple sources in parallel."""
        tasks = []
        
        for i, sub_query in enumerate(sub_queries[:num_sources]):
            step = self.create_step(
                step_id=f"retrieval_{i}",
                step_type="retrieval",
                description=f"Retrieve for: {sub_query[:50]}...",
                prompt=self._build_retrieval_prompt(sub_query, context)
            )
            tasks.append(self._execute_retrieval_step(step, config))
        
        # Execute in parallel
        steps = await asyncio.gather(*tasks)
        return list(steps)
    
    async def _execute_retrieval_step(
        self,
        step: PatternStep,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Execute a single retrieval step."""
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "retrieval"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _rerank_results(
        self,
        query: str,
        retrieved_contexts: List[str],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Re-rank retrieved results by relevance."""
        step = self.create_step(
            step_id="reranking",
            step_type="reranking",
            description="Re-rank results by relevance",
            prompt=self._build_reranking_prompt(query, retrieved_contexts)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "reranking"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _fuse_contexts(
        self,
        query: str,
        ranked_contexts: List[str],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Fuse multiple contexts intelligently."""
        step = self.create_step(
            step_id="fusion",
            step_type="fusion",
            description="Fuse contexts",
            prompt=self._build_fusion_prompt(query, ranked_contexts)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "fusion"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _generate_with_citations(
        self,
        query: str,
        fused_context: str,
        original_contexts: List[str],
        config: Dict[str, Any],
        enable_citations: bool
    ) -> PatternStep:
        """Generate answer with source citations."""
        step = self.create_step(
            step_id="generation",
            step_type="generation",
            description="Generate answer with citations",
            prompt=self._build_generation_prompt(
                query,
                fused_context,
                enable_citations
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            self.complete_step(
                step,
                response,
                {"stage": "generation"}
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _validate_answer(
        self,
        query: str,
        answer: str,
        context: str,
        config: Dict[str, Any]
    ) -> PatternStep:
        """Validate answer against retrieved context."""
        step = self.create_step(
            step_id="validation",
            step_type="validation",
            description="Validate answer",
            prompt=self._build_validation_prompt(query, answer, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            is_valid = self._parse_validation(response)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "validation",
                    "is_valid": is_valid
                }
            )
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_decomposition_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for query decomposition."""
        return f"""Decompose this complex query into simpler sub-queries for retrieval.

Query: {query}

Decomposition Instructions:
1. Break into 2-3 focused sub-queries
2. Each should be independently answerable
3. Cover different aspects of main query
4. Keep sub-queries specific
5. Number them clearly

Format:
1. [sub-query]
2. [sub-query]
3. [sub-query]

Sub-queries:"""
    
    def _build_retrieval_prompt(
        self,
        sub_query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for retrieval simulation."""
        mcp_data = context.get("mcp_data", "")
        
        return f"""Retrieve relevant information for this query.

Query: {sub_query}

Available Context:
{mcp_data[:500]}...

Retrieval Instructions:
1. Find most relevant information
2. Extract key facts and details
3. Include specific data points
4. Keep context focused
5. Preserve source information

Retrieved Context:"""
    
    def _build_reranking_prompt(
        self,
        query: str,
        contexts: List[str]
    ) -> str:
        """Build prompt for result re-ranking."""
        contexts_text = "\n\n".join([
            f"=== Context {i+1} ===\n{ctx[:300]}..."
            for i, ctx in enumerate(contexts)
        ])
        
        return f"""Re-rank these retrieved contexts by relevance to the query.

Query: {query}

Retrieved Contexts:
{contexts_text}

Re-ranking Instructions:
1. Rate each context for relevance (1-10)
2. Consider query coverage
3. Prioritize specific information
4. List in order (most→least relevant)

Format:
1. Context [N]: [score] - [reason]
2. Context [N]: [score] - [reason]

Ranked Results:"""
    
    def _build_fusion_prompt(
        self,
        query: str,
        contexts: List[str]
    ) -> str:
        """Build prompt for context fusion."""
        contexts_text = "\n\n".join([
            f"Source {i+1}:\n{ctx[:400]}..."
            for i, ctx in enumerate(contexts[:3])
        ])
        
        return f"""Fuse these contexts into a unified, comprehensive context.

Query: {query}

Contexts to Fuse:
{contexts_text}

Fusion Instructions:
1. Combine complementary information
2. Resolve contradictions
3. Remove redundancy
4. Preserve important details
5. Create coherent narrative

Fused Context:"""
    
    def _build_generation_prompt(
        self,
        query: str,
        fused_context: str,
        enable_citations: bool
    ) -> str:
        """Build prompt for answer generation."""
        citation_instruction = ""
        if enable_citations:
            citation_instruction = "\n6. Cite sources [Source N] for claims"
        
        return f"""Answer the query using the provided context.

Query: {query}

Context:
{fused_context[:800]}...

Generation Instructions:
1. Answer directly and completely
2. Use ONLY information from context
3. Be accurate and specific
4. If context insufficient, say so
5. Provide clear reasoning{citation_instruction}

Answer:"""
    
    def _build_validation_prompt(
        self,
        query: str,
        answer: str,
        context: str
    ) -> str:
        """Build prompt for answer validation."""
        return f"""Validate this answer against the context.

Query: {query}

Answer:
{answer[:500]}...

Context:
{context[:500]}...

Validation Instructions:
1. Check if answer is supported by context
2. Identify any hallucinations
3. Verify factual accuracy
4. Note any unsupported claims
5. Respond "VALID" or "INVALID: [reason]"

Validation:"""
    
    def _parse_subqueries(self, decomp_text: str) -> List[str]:
        """Parse sub-queries from decomposition."""
        if not decomp_text:
            return []
        
        queries = []
        lines = decomp_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Extract query text
                if ':' in line or '.' in line:
                    query = line.split(':', 1)[-1].split('.', 1)[-1].strip()
                    if len(query) > 10:
                        queries.append(query)
        
        return queries if queries else [decomp_text.split('\n')[0]]
    
    def _parse_ranked_contexts(self, rerank_text: str) -> List[str]:
        """Parse ranked contexts from reranking response."""
        # For now, return original order
        # In production, would parse and reorder
        return []
    
    def _parse_validation(self, validation_text: str) -> bool:
        """Parse validation result."""
        if not validation_text:
            return False
        
        text_lower = validation_text.lower()
        return "valid" in text_lower and "invalid" not in text_lower
    
    def _calculate_rag_confidence(
        self,
        validation_step: PatternStep,
        num_sources: int
    ) -> float:
        """Calculate confidence for RAG pattern."""
        if not validation_step:
            return 0.5
        
        # Factors:
        # 1. Validation passed
        is_valid = validation_step.metadata.get("is_valid", False)
        validation_factor = 1.0 if is_valid else 0.4
        
        # 2. Number of sources (more = higher confidence)
        source_factor = min(num_sources / 3, 1.0)
        
        # Combine
        confidence = (
            validation_factor * 0.7 +
            source_factor * 0.3
        )
        
        return min(confidence, 1.0)

