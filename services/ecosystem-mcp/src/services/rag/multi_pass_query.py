"""
Multi-Pass Query System - Complex Query Decomposition & Synthesis

Enables deep analysis of complex queries through:
1. Query decomposition into major concepts/sections
2. Secondary question generation for each section
3. Multi-pass RAG execution with progress tracking
4. Comprehensive synthesis of all results
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import hashlib

from .rag_service import get_rag_service
from .enhanced_rag_service import get_enhanced_rag_service
from ..models.ollama_router import get_ollama_router

logger = logging.getLogger(__name__)


@dataclass
class SecondaryQuestion:
    """A secondary question derived from a section."""
    question: str
    section_index: int
    section_name: str
    question_index: int


@dataclass
class QuestionResult:
    """Result from processing a single question."""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    duration_seconds: float
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class SectionResult:
    """Result from processing a complete section."""
    section_index: int
    section_name: str
    section_description: str
    questions: List[QuestionResult]
    synthesis: str
    duration_seconds: float
    timestamp: str


@dataclass
class MultiPassResult:
    """Complete result from multi-pass query processing."""
    original_query: str
    num_passes: int
    num_secondary_questions: int
    sections: List[SectionResult]
    final_synthesis: str
    total_duration_seconds: float
    total_questions_asked: int
    total_sources_used: int
    timestamp: str
    metadata: Dict[str, Any]


class MultiPassQueryService:
    """
    Multi-pass query processing service.
    
    Decomposes complex queries into sections, generates secondary questions,
    executes RAG for each question, and synthesizes comprehensive answers.
    """
    
    def __init__(self):
        """Initialize multi-pass query service."""
        self.rag_service = get_rag_service()
        self.ollama_router = get_ollama_router()
        logger.info("MultiPassQueryService initialized")
    
    async def process_query(
        self,
        query: str,
        num_passes: int = 3,
        num_secondary_questions: int = 3,
        n_results: int = 10,
        temperature: float = 0.7,
        response_length: int = 1000,
        use_enhancements: bool = False,
        progress_callback: Optional[callable] = None
    ) -> MultiPassResult:
        """
        Process a complex query using multi-pass decomposition.
        
        Args:
            query: Main query to process
            num_passes: Number of major concepts/sections (1-10)
            num_secondary_questions: Number of questions per section (1-10)
            n_results: Documents to retrieve per question
            temperature: LLM temperature
            response_length: Target response length in tokens (affects verbosity)
            use_enhancements: Use enhanced RAG with optional config (glossary, templates, priorities)
            progress_callback: Optional callback for progress updates
        
        Returns:
            MultiPassResult with complete analysis
        """
        start_time = datetime.now()
        
        # Select RAG service based on enhancements flag
        if use_enhancements:
            logger.info("🎨 Using EnhancedRAGService with optional config")
            rag_service = get_enhanced_rag_service()
        else:
            logger.info("📊 Using standard RAGService")
            rag_service = get_rag_service()
        
        logger.info(
            f"Starting multi-pass query: passes={num_passes}, "
            f"secondary_questions={num_secondary_questions}, "
            f"use_enhancements={use_enhancements}"
        )
        
        try:
            # Step 1: Decompose query into sections
            if progress_callback:
                await progress_callback("decomposing", 0, "Decomposing query into sections...")
            
            logger.info(f"📋 Step 1: Decomposing query into {num_passes} sections...")
            sections = await self._decompose_query(query, num_passes)
            logger.info(f"✅ Decomposed into {len(sections)} sections: {[s['name'] for s in sections]}")
            
            # Step 2: Generate secondary questions for each section
            if progress_callback:
                await progress_callback("generating_questions", 10, "Generating secondary questions...")
            
            # 🚀 OPTIMIZATION: Generate questions for all sections in parallel (3× speedup!)
            logger.info(f"❓ Step 2: Generating {num_secondary_questions} questions per section...")
            all_questions = await self._generate_secondary_questions(
                query, sections, num_secondary_questions
            )
            logger.info(f"✅ Generated {len(all_questions)} total questions across all sections")
            
            # 🚀 PHASE 2 OPTIMIZATION: Process ALL sections in PARALLEL (2-3× speedup!)
            logger.info(f"🔍 Step 3: Processing {len(sections)} sections in PARALLEL...")
            logger.info(f"  → All {len(all_questions)} RAG queries will execute simultaneously")
            logger.info(f"  → Using {'Enhanced' if use_enhancements else 'Standard'} RAG service")
            
            # Create tasks for all sections
            section_tasks = [
                self._process_section(
                    section_idx,
                    section,
                    all_questions,
                    n_results,
                    temperature,
                    response_length
                )
                for section_idx, section in enumerate(sections)
            ]
            
            # Execute all sections in parallel
            sections_start = time.time()
            logger.info(f"⏱️  Executing {len(section_tasks)} sections in parallel (this will take longest)...")
            section_results = await asyncio.gather(*section_tasks, return_exceptions=True)
            sections_time = time.time() - sections_start
            logger.info(f"✅ All sections completed in {sections_time:.2f}s")
            
            # Handle any exceptions
            valid_section_results = []
            for idx, result in enumerate(section_results):
                if isinstance(result, Exception):
                    logger.error(f"Section {idx} failed: {result}")
                    # Create error section result
                    from .multi_pass_query import SectionResult, QuestionResult
                    error_result = SectionResult(
                        section_index=idx,
                        section_name=sections[idx]['name'],
                        section_description=sections[idx]['description'],
                        questions=[],
                        synthesis=f"Error processing section: {str(result)}",
                        duration_seconds=0.0,
                        timestamp=datetime.now().isoformat()
                    )
                    valid_section_results.append(error_result)
                else:
                    valid_section_results.append(result)
            
            section_results = valid_section_results
            logger.info(f"✅ Completed {len(section_results)} sections in PARALLEL")
            
            # Calculate total questions
            total_questions = len(all_questions)
            
            # Step 4: Final synthesis
            if progress_callback:
                await progress_callback("synthesizing", 90, "Synthesizing final answer...")
            
            final_synthesis = await self._synthesize_final_answer(
                query, section_results, response_length
            )
            
            # Calculate totals
            total_duration = (datetime.now() - start_time).total_seconds()
            total_sources = sum(
                len(q.sources)
                for section in section_results
                for q in section.questions
            )
            
            if progress_callback:
                await progress_callback("complete", 100, "Query processing complete!")
            
            result = MultiPassResult(
                original_query=query,
                num_passes=num_passes,
                num_secondary_questions=num_secondary_questions,
                sections=section_results,
                final_synthesis=final_synthesis,
                total_duration_seconds=total_duration,
                total_questions_asked=total_questions,
                total_sources_used=total_sources,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "n_results": n_results,
                    "temperature": temperature,
                    "sections_count": len(sections)
                }
            )
            
            logger.info(
                f"Multi-pass query complete: {total_questions} questions, "
                f"{total_sources} sources, {total_duration:.2f}s"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Multi-pass query failed: {e}", exc_info=True)
            raise
    
    async def _decompose_query(
        self,
        query: str,
        num_passes: int
    ) -> List[Dict[str, str]]:
        """
        Decompose query into major concepts/sections.
        
        Args:
            query: Main query
            num_passes: Number of sections to create
        
        Returns:
            List of sections with name and description
        """
        prompt = f"""Decompose the following query into {num_passes} major concepts or sections for analysis.

Query: {query}

Provide exactly {num_passes} sections. For each section, provide:
1. A concise name (2-5 words)
2. A brief description of what this section covers

Format your response as a JSON array of objects with 'name' and 'description' fields.

Example:
[
  {{"name": "Core Concepts", "description": "Fundamental concepts and definitions"}},
  {{"name": "Implementation Details", "description": "Technical implementation and architecture"}},
  {{"name": "Best Practices", "description": "Usage patterns and recommendations"}}
]

Provide exactly {num_passes} sections:"""

        decompose_start = time.time()
        logger.info(f"⏱️  Calling LLM to decompose query into {num_passes} sections...")
        
        response = await self.ollama_router.generate(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for structured output
            workload_type='rag'  # Use 'rag' to get Desktop GPU routing
        )
        
        decompose_time = time.time() - decompose_start
        logger.info(f"✅ LLM decomposition completed in {decompose_time:.2f}s")
        
        # Extract JSON from response
        response_text = response.get("response", response.get("text", ""))
        
        # Try to parse JSON
        import json
        import re
        
        # Find JSON array in response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            try:
                sections = json.loads(json_match.group(0))
                
                # Validate structure
                if isinstance(sections, list) and len(sections) > 0:
                    # Ensure we have exactly num_passes sections
                    sections = sections[:num_passes]
                    
                    # Validate each section has required fields
                    validated_sections = []
                    for i, section in enumerate(sections):
                        if isinstance(section, dict) and 'name' in section and 'description' in section:
                            validated_sections.append(section)
                        else:
                            # Fallback section
                            validated_sections.append({
                                "name": f"Section {i+1}",
                                "description": f"Analysis section {i+1} for the query"
                            })
                    
                    # Pad if we got fewer than requested
                    while len(validated_sections) < num_passes:
                        i = len(validated_sections)
                        validated_sections.append({
                            "name": f"Section {i+1}",
                            "description": f"Additional analysis section {i+1}"
                        })
                    
                    logger.info(f"Decomposed query into {len(validated_sections)} sections")
                    return validated_sections
            
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from decomposition response")
        
        # Fallback: Create generic sections
        logger.warning("Using fallback section decomposition")
        return [
            {
                "name": f"Section {i+1}",
                "description": f"Analysis section {i+1} for: {query[:50]}..."
            }
            for i in range(num_passes)
        ]
    
    async def _generate_secondary_questions(
        self,
        main_query: str,
        sections: List[Dict[str, str]],
        num_questions: int
    ) -> List[SecondaryQuestion]:
        """
        Generate secondary questions for each section.
        
        🚀 OPTIMIZED: Generates questions for all sections in PARALLEL (3× speedup)
        
        Args:
            main_query: Original query
            sections: Decomposed sections
            num_questions: Questions per section
        
        Returns:
            List of secondary questions
        """
        logger.info(f"🚀 Generating questions for {len(sections)} sections in PARALLEL")
        
        async def generate_for_section(section_idx: int, section: Dict[str, str]) -> List[SecondaryQuestion]:
            """Generate questions for a single section."""
            section_start = time.time()
            logger.info(f"  ⏱️  Section {section_idx+1}: Generating {num_questions} questions for '{section['name']}'...")
            
            prompt = f"""Generate {num_questions} specific, focused questions to explore this section in depth.

Main Query: {main_query}

Section: {section['name']}
Description: {section['description']}

Generate exactly {num_questions} questions that:
1. Are specific and answerable
2. Build on each other progressively
3. Help understand this section thoroughly
4. Are relevant to the main query

Format as a JSON array of strings:
["Question 1?", "Question 2?", "Question 3?"]

Provide exactly {num_questions} questions:"""

            try:
                llm_start = time.time()
                response = await self.ollama_router.generate(
                    prompt=prompt,
                    temperature=0.4,
                    workload_type='rag'  # Use 'rag' to get Desktop GPU routing
                )
                llm_time = time.time() - llm_start
                logger.info(f"    ✅ LLM call for section {section_idx+1} completed in {llm_time:.2f}s")
                
                response_text = response.get("response", response.get("text", ""))
                
                # Extract questions
                import json
                import re
                
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                questions = []
                
                if json_match:
                    try:
                        questions = json.loads(json_match.group(0))
                        if isinstance(questions, list):
                            questions = questions[:num_questions]
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON for section {section['name']}")
                
                # Fallback: Generate generic questions
                if not questions or len(questions) < num_questions:
                    questions = [
                        f"What are the key aspects of {section['name'].lower()}?",
                        f"How does {section['name'].lower()} work?",
                        f"What are best practices for {section['name'].lower()}?"
                    ][:num_questions]
                
                # Pad if needed
                while len(questions) < num_questions:
                    questions.append(f"Additional question about {section['name']}")
                
                # Create SecondaryQuestion objects
                section_questions = []
                for q_idx, question in enumerate(questions):
                    section_questions.append(SecondaryQuestion(
                        question=question,
                        section_index=section_idx,
                        section_name=section['name'],
                        question_index=q_idx
                    ))
                
                return section_questions
            
            except Exception as e:
                logger.error(f"Failed to generate questions for section {section['name']}: {e}")
                # Return fallback question
                return [SecondaryQuestion(
                    question=f"What are the key aspects of {section['name']}?",
                    section_index=section_idx,
                    section_name=section['name'],
                    question_index=0
                )]
        
        # 🚀 Execute question generation for all sections in parallel
        question_tasks = [
            generate_for_section(section_idx, section)
            for section_idx, section in enumerate(sections)
        ]
        
        questions_start = time.time()
        logger.info(f"⏱️  Executing {len(question_tasks)} LLM calls in parallel...")
        section_question_lists = await asyncio.gather(*question_tasks, return_exceptions=True)
        questions_time = time.time() - questions_start
        logger.info(f"✅ All question generation completed in {questions_time:.2f}s")
        
        # Flatten results and handle exceptions
        all_questions = []
        for result in section_question_lists:
            if isinstance(result, Exception):
                logger.error(f"Question generation failed: {result}")
                # Skip this section's questions
                continue
            all_questions.extend(result)
        
        logger.info(f"✅ Generated {len(all_questions)} secondary questions in parallel")
        return all_questions
    
    async def _process_section(
        self,
        section_idx: int,
        section: Dict[str, str],
        all_questions: List[SecondaryQuestion],
        n_results: int,
        temperature: float,
        response_length: int
    ) -> SectionResult:
        """
        Process a single section by answering all its questions.
        
        Args:
            section_idx: Section index
            section: Section info
            all_questions: All secondary questions
            n_results: Documents per query
            temperature: LLM temperature
        
        Returns:
            SectionResult with all answers
        """
        start_time = datetime.now()
        
        # Get questions for this section
        section_questions = [
            q for q in all_questions
            if q.section_index == section_idx
        ]
        
        logger.info(f"🚀 Processing {len(section_questions)} questions in PARALLEL for section {section_idx}")
        
        # 🚀 PHASE 3 OPTIMIZATION: Adaptive n_results (later questions need fewer docs)
        def calculate_adaptive_n_results(question_index: int, total_questions: int, base_n_results: int) -> int:
            """
            Reduce documents for later questions since they have context from earlier ones.
            
            First question: 100% of docs (no context)
            Last question: 70% of docs (has context from all previous)
            """
            if question_index == 0 or total_questions == 1:
                return base_n_results
            
            # Gradual reduction: 0% → 30% reduction
            reduction_factor = 0.3 * (question_index / (total_questions - 1))
            adaptive_n = int(base_n_results * (1 - reduction_factor))
            
            logger.debug(f"   Q{question_index + 1}/{total_questions}: {adaptive_n} docs (base={base_n_results}, reduction={reduction_factor:.1%})")
            return max(adaptive_n, 5)  # Minimum 5 docs
        
        # 🚀 OPTIMIZATION: Execute ALL RAG queries in parallel (6-9× speedup!)
        async def execute_rag_query(question: SecondaryQuestion, question_index: int):
            """Execute single RAG query with timing, error handling, and adaptive docs."""
            q_start = datetime.now()
            try:
                # Calculate adaptive n_results for this question
                adaptive_n = calculate_adaptive_n_results(
                    question_index,
                    len(section_questions),
                    n_results
                )
                
                logger.debug(
                    f"  Executing RAG for question {question_index + 1}/{len(section_questions)}: "
                    f"{question.question[:60]}..."
                )
                
                rag_result = await rag_service.ask(
                    question=question.question,
                    n_results=adaptive_n,  # ✅ Adaptive!
                    temperature=temperature,
                    response_length=response_length
                )
                
                logger.debug(
                    f"  ✅ RAG completed: {len(rag_result.get('answer', ''))} chars, "
                    f"confidence: {rag_result.get('confidence', 0):.3f}"
                )
                
                q_duration = (datetime.now() - q_start).total_seconds()
                
                return QuestionResult(
                    question=question.question,
                    answer=rag_result.get("answer", ""),
                    sources=rag_result.get("sources", []),
                    confidence=rag_result.get("confidence", 0.0),
                    duration_seconds=q_duration,
                    timestamp=datetime.now().isoformat(),
                    metadata=rag_result.get("metadata", {})
                )
            
            except Exception as e:
                logger.error(f"Failed to process question '{question.question[:50]}...': {e}")
                return QuestionResult(
                    question=question.question,
                    answer=f"Error: {str(e)}",
                    sources=[],
                    confidence=0.0,
                    duration_seconds=(datetime.now() - q_start).total_seconds(),
                    timestamp=datetime.now().isoformat(),
                    metadata={"error": str(e)}
                )
        
        # Execute all questions in parallel with semaphore to limit concurrency
        # Desktop Ollama can handle ~8-10 parallel requests
        semaphore = asyncio.Semaphore(8)
        
        async def limited_rag_query(question: SecondaryQuestion, question_index: int):
            """Execute RAG query with concurrency limit."""
            async with semaphore:
                return await execute_rag_query(question, question_index)
        
        # Create tasks for all questions (with indices for adaptive n_results)
        rag_tasks = [limited_rag_query(q, idx) for idx, q in enumerate(section_questions)]
        
        # Wait for all to complete (return_exceptions=True handles errors gracefully)
        question_results = await asyncio.gather(*rag_tasks, return_exceptions=True)
        
        # Convert any exceptions to error results
        question_results = [
            result if not isinstance(result, Exception) else QuestionResult(
                question=section_questions[i].question,
                answer=f"Error: {str(result)}",
                sources=[],
                confidence=0.0,
                duration_seconds=0.0,
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(result), "exception_type": type(result).__name__}
            )
            for i, result in enumerate(question_results)
        ]
        
        logger.info(f"✅ Completed {len(question_results)} parallel RAG queries for section {section_idx}")
        
        # Synthesize section answer with verbosity control
        synthesis = await self._synthesize_section(
            section['name'],
            section['description'],
            question_results,
            response_length
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return SectionResult(
            section_index=section_idx,
            section_name=section['name'],
            section_description=section['description'],
            questions=question_results,
            synthesis=synthesis,
            duration_seconds=duration,
            timestamp=datetime.now().isoformat()
        )
    
    async def _synthesize_section(
        self,
        section_name: str,
        section_description: str,
        question_results: List[QuestionResult],
        response_length: int = 1000
    ) -> str:
        """Synthesize section-level answer from question results."""
        
        # Build context from all question answers
        context_parts = []
        for q_result in question_results:
            context_parts.append(f"Q: {q_result.question}\nA: {q_result.answer}\n")
        
        context = "\n".join(context_parts)
        
        # Determine verbosity for section synthesis (same logic as RAG service)
        if response_length <= 500:
            verbosity = "Provide a concise synthesis (2-3 paragraphs) covering key points."
        elif response_length <= 1000:
            verbosity = "Provide a balanced synthesis (3-5 paragraphs) with moderate detail."
        elif response_length <= 2000:
            verbosity = "Provide a DETAILED synthesis (5-8 paragraphs) with thorough explanations, examples, and technical context."
        else:
            verbosity = "Provide an EXTREMELY DETAILED synthesis (8-12 paragraphs) with comprehensive explanations, multiple examples, technical specifications, and thorough coverage."
        
        prompt = f"""Synthesize a comprehensive answer for this section based on the questions and answers below.

Section: {section_name}
Description: {section_description}

Questions and Answers:
{context}

Provide a well-structured, coherent synthesis that:
1. Integrates information from all answers
2. Eliminates redundancy
3. Maintains logical flow
4. Highlights key insights
5. {verbosity}

Synthesis:"""

        response = await self.ollama_router.generate(
            prompt=prompt,
            temperature=0.7,
            workload_type='rag',  # Use 'rag' to get Desktop GPU routing
            max_tokens=response_length  # Pass max_tokens for synthesis
        )
        
        return response.get("response", response.get("text", ""))
    
    async def _synthesize_final_answer(
        self,
        original_query: str,
        section_results: List[SectionResult],
        response_length: int = 1000
    ) -> str:
        """Synthesize final comprehensive answer from all sections."""
        synthesis_start = time.time()
        logger.info(f"⏱️  Synthesizing final answer from {len(section_results)} sections...")
        
        # Build context from all section syntheses
        context_parts = []
        for section in section_results:
            context_parts.append(
                f"## {section.section_name}\n"
                f"{section.synthesis}\n"
            )
        
        context = "\n".join(context_parts)
        
        # Determine verbosity for final synthesis (more aggressive for multi-pass)
        if response_length <= 500:
            verbosity = "Provide a concise final answer (3-5 paragraphs) highlighting the most important points."
        elif response_length <= 1000:
            verbosity = "Provide a comprehensive final answer (5-8 paragraphs) with clear structure and detailed coverage."
        elif response_length <= 2000:
            verbosity = """Provide a DETAILED and COMPREHENSIVE final answer (10-15 paragraphs minimum).
            
            IMPORTANT: Multi-pass analysis deserves thorough synthesis. Include:
            - Comprehensive overview of all findings
            - Detailed explanations for each major concept
            - Integration of insights across sections
            - Examples and technical details
            - Clear section headings and structure"""
        else:
            verbosity = """Provide an EXTREMELY DETAILED and EXHAUSTIVE final answer (15-25 paragraphs minimum).
            
            CRITICAL: This is a deep multi-pass analysis - the final document should be authoritative and thorough:
            - Comprehensive introduction and executive summary
            - Detailed exploration of each major concept
            - Multiple examples and real-world scenarios
            - Technical specifications and implementation details
            - Cross-section integration and relationships
            - Best practices and recommendations
            - Clear hierarchical structure with headings"""
        
        prompt = f"""Create a comprehensive, final answer to the original query by synthesizing all section analyses.

Original Query: {original_query}

Section Analyses:
{context}

Provide a complete, well-structured answer that:
1. Directly addresses the original query
2. Integrates insights from all sections
3. Maintains coherent narrative flow
4. Highlights key takeaways
5. {verbosity}

Final Answer:"""

        llm_start = time.time()
        logger.info(f"⏱️  Calling LLM for final synthesis (may take 30-60s for long responses)...")
        response = await self.ollama_router.generate(
            prompt=prompt,
            temperature=0.7,
            workload_type='rag',  # Use 'rag' to get Desktop GPU routing (critical for speed)
            max_tokens=response_length * 2  # 2x tokens for final synthesis (it's synthesizing multiple sections)
        )
        llm_time = time.time() - llm_start
        synthesis_total = time.time() - synthesis_start
        logger.info(f"✅ Final synthesis completed: LLM={llm_time:.2f}s, Total={synthesis_total:.2f}s")
        
        return response.get("response", response.get("text", ""))


# Singleton instance
_multi_pass_service: Optional[MultiPassQueryService] = None


def get_multi_pass_service() -> MultiPassQueryService:
    """Get the global multi-pass query service instance."""
    global _multi_pass_service
    
    if _multi_pass_service is None:
        _multi_pass_service = MultiPassQueryService()
    
    return _multi_pass_service

