"""
Multi-Hop RAG Service

Enables answering complex questions that require information from multiple documents
through iterative reasoning.

Example Use Cases:
- "How did the authentication refactor affect API performance?"
- "What is the relationship between caching and response times?"
- "Trace the evolution of the ingestion pipeline"
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from . import get_rag_service
from ..ollama import get_ollama_service

logger = logging.getLogger(__name__)


@dataclass
class ReasoningStep:
    """A single step in the multi-hop reasoning chain."""
    question: str
    answer: str
    sources: List[Dict]
    confidence: float


class MultiHopRAGService:
    """Multi-hop reasoning for complex queries."""
    
    def __init__(self, max_hops: int = 3):
        """
        Initialize multi-hop RAG service.
        
        Args:
            max_hops: Maximum number of reasoning hops (sub-questions)
        """
        self.rag_service = get_rag_service()
        self.ollama = get_ollama_service()
        self.max_hops = max_hops
        
        logger.info(f"✅ Multi-hop RAG service initialized (max_hops={max_hops})")
    
    async def answer_multi_hop(
        self,
        question: str,
        max_hops: Optional[int] = None,
        n_results_per_hop: int = 5
    ) -> Dict:
        """
        Answer complex question using multi-hop reasoning.
        
        Process:
        1. Decompose question into sub-questions
        2. Answer each sub-question independently
        3. Synthesize final answer from sub-answers
        
        Args:
            question: Complex question requiring multiple sources
            max_hops: Maximum reasoning hops (defaults to self.max_hops)
            n_results_per_hop: Documents to retrieve per sub-question
        
        Returns:
            Dict with:
                - answer: Final synthesized answer
                - reasoning_chain: List of ReasoningStep objects
                - hops: Number of reasoning hops used
                - metadata: Additional metrics
        """
        max_hops = max_hops or self.max_hops
        
        logger.info(f"🔗 Starting multi-hop reasoning: {question[:60]}...")
        
        # Step 1: Decompose question into sub-questions
        sub_questions = await self._decompose_question(question, max_hops)
        logger.info(f"   Decomposed into {len(sub_questions)} sub-questions")
        
        # Step 2: Answer each sub-question
        reasoning_chain: List[ReasoningStep] = []
        
        for i, sq in enumerate(sub_questions, 1):
            logger.info(f"   Hop {i}/{len(sub_questions)}: {sq[:50]}...")
            
            # Get answer for sub-question
            result = await self.rag_service.ask(
                question=sq,
                n_results=n_results_per_hop,
                use_enhancements=True
            )
            
            # Store reasoning step
            reasoning_chain.append(ReasoningStep(
                question=sq,
                answer=result["answer"],
                sources=result["sources"],
                confidence=result["confidence"]
            ))
        
        # Step 3: Synthesize final answer
        logger.info(f"   Synthesizing final answer from {len(reasoning_chain)} hops...")
        final_answer = await self._synthesize_answer(question, reasoning_chain)
        
        # Calculate overall confidence (average of sub-question confidences)
        overall_confidence = sum(step.confidence for step in reasoning_chain) / len(reasoning_chain)
        
        # Collect all unique sources
        all_sources = []
        seen_ids = set()
        for step in reasoning_chain:
            for source in step.sources:
                if source["id"] not in seen_ids:
                    all_sources.append(source)
                    seen_ids.add(source["id"])
        
        logger.info(
            f"✅ Multi-hop complete: {len(reasoning_chain)} hops, "
            f"{len(all_sources)} unique sources, confidence={overall_confidence:.2f}"
        )
        
        return {
            "answer": final_answer,
            "reasoning_chain": [
                {
                    "hop": i + 1,
                    "question": step.question,
                    "answer": step.answer,
                    "confidence": step.confidence,
                    "n_sources": len(step.sources)
                }
                for i, step in enumerate(reasoning_chain)
            ],
            "sources": all_sources,
            "confidence": overall_confidence,
            "metadata": {
                "method": "multi_hop",
                "hops": len(reasoning_chain),
                "total_sources": len(all_sources),
                "sub_questions": [step.question for step in reasoning_chain]
            }
        }
    
    async def _decompose_question(
        self,
        question: str,
        max_sub_questions: int
    ) -> List[str]:
        """
        Decompose complex question into sub-questions.
        
        Uses LLM to break down the question into simpler, more focused questions.
        
        Args:
            question: Complex question
            max_sub_questions: Maximum number of sub-questions
        
        Returns:
            List of sub-questions
        """
        prompt = f"""Decompose this complex question into {max_sub_questions} simpler sub-questions.
Each sub-question should focus on a specific aspect and be answerable independently.

Complex Question: {question}

Sub-questions (one per line, numbered):
1."""
        
        try:
            response = await self.ollama.generate(
                prompt=prompt,
                temperature=0.3  # Lower temperature for more focused decomposition
            )
            
            # Parse sub-questions from response
            lines = response.strip().split("\n")
            sub_questions = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract question after number/bullet
                if line[0].isdigit() or line.startswith("-"):
                    # Remove number/bullet prefix
                    sq = line.split(".", 1)[-1].split(")", 1)[-1].strip()
                    if sq and len(sq) > 10:  # Reasonable question length
                        sub_questions.append(sq)
            
            # Limit to max_sub_questions
            sub_questions = sub_questions[:max_sub_questions]
            
            # Fallback: if no sub-questions extracted, use original question
            if not sub_questions:
                logger.warning("Failed to decompose question, using original")
                sub_questions = [question]
            
            return sub_questions
        
        except Exception as e:
            logger.error(f"Question decomposition failed: {e}")
            # Fallback: use original question
            return [question]
    
    async def _synthesize_answer(
        self,
        original_question: str,
        reasoning_chain: List[ReasoningStep]
    ) -> str:
        """
        Synthesize final answer from sub-answers.
        
        Uses LLM to combine insights from multiple sub-question answers.
        
        Args:
            original_question: Original complex question
            reasoning_chain: List of reasoning steps with sub-answers
        
        Returns:
            Synthesized final answer
        """
        # Build context from reasoning chain
        context_parts = []
        for i, step in enumerate(reasoning_chain, 1):
            context_parts.append(f"**Sub-question {i}:** {step.question}")
            context_parts.append(f"**Answer {i}:** {step.answer}")
            context_parts.append("")  # Blank line
        
        context = "\n".join(context_parts)
        
        prompt = f"""Based on the following sub-questions and their answers, synthesize a comprehensive answer to the original question.

{context}

**Original Question:** {original_question}

**Synthesized Answer (combine insights from all sub-answers):**"""
        
        try:
            final_answer = await self.ollama.generate(
                prompt=prompt,
                temperature=0.5  # Balanced temperature for synthesis
            )
            
            return final_answer.strip()
        
        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            # Fallback: concatenate sub-answers
            return " ".join(step.answer for step in reasoning_chain)


# Singleton instance
_multi_hop_service: Optional[MultiHopRAGService] = None


def get_multi_hop_service(max_hops: int = 3) -> MultiHopRAGService:
    """
    Get or create singleton multi-hop RAG service.
    
    Args:
        max_hops: Maximum reasoning hops
    
    Returns:
        MultiHopRAGService instance
    """
    global _multi_hop_service
    
    if _multi_hop_service is None:
        _multi_hop_service = MultiHopRAGService(max_hops=max_hops)
    
    return _multi_hop_service

