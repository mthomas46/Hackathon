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
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import hashlib

from .rag_service import get_rag_service
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
            progress_callback: Optional callback for progress updates
        
        Returns:
            MultiPassResult with complete analysis
        """
        start_time = datetime.now()
        logger.info(
            f"Starting multi-pass query: passes={num_passes}, "
            f"secondary_questions={num_secondary_questions}"
        )
        
        try:
            # Step 1: Decompose query into sections
            if progress_callback:
                await progress_callback("decomposing", 0, "Decomposing query into sections...")
            
            sections = await self._decompose_query(query, num_passes)
            
            # Step 2: Generate secondary questions for each section
            if progress_callback:
                await progress_callback("generating_questions", 10, "Generating secondary questions...")
            
            all_questions = await self._generate_secondary_questions(
                query, sections, num_secondary_questions
            )
            
            # Step 3: Execute RAG for all questions
            section_results = []
            total_questions = len(all_questions)
            
            for section_idx, section in enumerate(sections):
                if progress_callback:
                    progress = 10 + ((section_idx / len(sections)) * 70)
                    await progress_callback(
                        "processing_sections",
                        int(progress),
                        f"Processing section {section_idx + 1}/{len(sections)}: {section['name']}"
                    )
                
                section_result = await self._process_section(
                    section_idx,
                    section,
                    all_questions,
                    n_results,
                    temperature
                )
                section_results.append(section_result)
            
            # Step 4: Final synthesis
            if progress_callback:
                await progress_callback("synthesizing", 90, "Synthesizing final answer...")
            
            final_synthesis = await self._synthesize_final_answer(
                query, section_results
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

        response = await self.ollama_router.generate(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for structured output
            workload_type='generation'
        )
        
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
        
        Args:
            main_query: Original query
            sections: Decomposed sections
            num_questions: Questions per section
        
        Returns:
            List of secondary questions
        """
        all_questions = []
        
        for section_idx, section in enumerate(sections):
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

            response = await self.ollama_router.generate(
                prompt=prompt,
                temperature=0.4,
                workload_type='generation'
            )
            
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
                    pass
            
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
            for q_idx, question in enumerate(questions):
                all_questions.append(SecondaryQuestion(
                    question=question,
                    section_index=section_idx,
                    section_name=section['name'],
                    question_index=q_idx
                ))
        
        logger.info(f"Generated {len(all_questions)} secondary questions")
        return all_questions
    
    async def _process_section(
        self,
        section_idx: int,
        section: Dict[str, str],
        all_questions: List[SecondaryQuestion],
        n_results: int,
        temperature: float
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
        
        # Execute RAG for each question
        question_results = []
        
        for question in section_questions:
            q_start = datetime.now()
            
            try:
                # Execute RAG
                rag_result = await self.rag_service.ask(
                    question=question.question,
                    n_results=n_results,
                    temperature=temperature
                )
                
                q_duration = (datetime.now() - q_start).total_seconds()
                
                question_results.append(QuestionResult(
                    question=question.question,
                    answer=rag_result.get("answer", ""),
                    sources=rag_result.get("sources", []),
                    confidence=rag_result.get("confidence", 0.0),
                    duration_seconds=q_duration,
                    timestamp=datetime.now().isoformat(),
                    metadata=rag_result.get("metadata", {})
                ))
            
            except Exception as e:
                logger.error(f"Failed to process question: {e}")
                question_results.append(QuestionResult(
                    question=question.question,
                    answer=f"Error: {str(e)}",
                    sources=[],
                    confidence=0.0,
                    duration_seconds=0.0,
                    timestamp=datetime.now().isoformat(),
                    metadata={"error": str(e)}
                ))
        
        # Synthesize section answer
        synthesis = await self._synthesize_section(
            section['name'],
            section['description'],
            question_results
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
        question_results: List[QuestionResult]
    ) -> str:
        """Synthesize section-level answer from question results."""
        
        # Build context from all question answers
        context_parts = []
        for q_result in question_results:
            context_parts.append(f"Q: {q_result.question}\nA: {q_result.answer}\n")
        
        context = "\n".join(context_parts)
        
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
5. Is comprehensive yet concise

Synthesis:"""

        response = await self.ollama_router.generate(
            prompt=prompt,
            temperature=0.7,
            workload_type='generation'
        )
        
        return response.get("response", response.get("text", ""))
    
    async def _synthesize_final_answer(
        self,
        original_query: str,
        section_results: List[SectionResult]
    ) -> str:
        """Synthesize final comprehensive answer from all sections."""
        
        # Build context from all section syntheses
        context_parts = []
        for section in section_results:
            context_parts.append(
                f"## {section.section_name}\n"
                f"{section.synthesis}\n"
            )
        
        context = "\n".join(context_parts)
        
        prompt = f"""Create a comprehensive, final answer to the original query by synthesizing all section analyses.

Original Query: {original_query}

Section Analyses:
{context}

Provide a complete, well-structured answer that:
1. Directly addresses the original query
2. Integrates insights from all sections
3. Maintains coherent narrative flow
4. Highlights key takeaways
5. Is authoritative and comprehensive

Final Answer:"""

        response = await self.ollama_router.generate(
            prompt=prompt,
            temperature=0.7,
            workload_type='generation'
        )
        
        return response.get("response", response.get("text", ""))


# Singleton instance
_multi_pass_service: Optional[MultiPassQueryService] = None


def get_multi_pass_service() -> MultiPassQueryService:
    """Get the global multi-pass query service instance."""
    global _multi_pass_service
    
    if _multi_pass_service is None:
        _multi_pass_service = MultiPassQueryService()
    
    return _multi_pass_service

