"""
Dynamic Temporal RAG Orchestrator (Phase 6.4)

Coordinates the entire dynamic temporal RAG flow.
"""

import logging
from typing import Dict, Optional, AsyncGenerator
import asyncio
from datetime import datetime

from .topic_extractor import TopicExtractor, ExtractedTopics
from .document_finder import DocumentFinder, RelevantDocument
from .dynamic_timeline_constructor import DynamicTimelineConstructor, DynamicTimeline
from .answer_synthesizer import TemporalAnswerSynthesizer, TemporalAnswer
from .citation_formatter import CitationFormatter, FormattedCitation

logger = logging.getLogger(__name__)


class DynamicTemporalRAGOrchestrator:
    """
    Orchestrates the complete dynamic temporal RAG flow.
    
    Flow:
    1. Extract topics from query
    2. Find relevant documents
    3. Construct dynamic timeline
    4. Synthesize answer with temporal context
    5. Format citations
    6. Return complete response
    
    Features:
    - End-to-end coordination
    - Caching support
    - Streaming support
    - Error handling
    - Performance monitoring
    """
    
    def __init__(self):
        self.topic_extractor = TopicExtractor()
        self.document_finder = DocumentFinder()
        self.timeline_constructor = DynamicTimelineConstructor()
        self.answer_synthesizer = TemporalAnswerSynthesizer()
        self.citation_formatter = CitationFormatter()
        
        logger.info("DynamicTemporalRAGOrchestrator initialized")
    
    async def execute(
        self,
        query: str,
        service_name: Optional[str] = None,
        citation_format: str = "markdown",
        use_cache: bool = True
    ) -> Dict:
        """
        Execute the complete dynamic temporal RAG flow.
        
        Args:
            query: User's natural language query
            service_name: Optional service filter
            citation_format: Citation format (markdown/html/plain)
            use_cache: Whether to use cached timelines
        
        Returns:
            Complete response with answer, timeline, and citations
        """
        logger.info(f"🚀 Executing Dynamic Temporal RAG for query: {query[:100]}...")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Extract topics
            logger.info("📊 Step 1: Extracting topics...")
            topics = self.topic_extractor.extract(query)
            
            if not topics.all_topics:
                return self._generate_no_topics_response(query)
            
            # Step 2: Find relevant documents
            logger.info("🔍 Step 2: Finding relevant documents...")
            search_terms = self.topic_extractor.get_search_terms(topics)
            documents = await self.document_finder.find_relevant_documents(
                search_terms=search_terms,
                service_name=service_name,
                limit=50
            )
            
            if not documents:
                return self._generate_no_documents_response(query, topics)
            
            # Step 3: Construct dynamic timeline
            logger.info("📅 Step 3: Constructing dynamic timeline...")
            timeline = await self.timeline_constructor.construct_timeline(
                documents=documents,
                timeline_name=f"Timeline for: {query[:50]}..."
            )
            
            # Step 4: Synthesize answer
            logger.info("🤖 Step 4: Synthesizing answer...")
            answer = await self.answer_synthesizer.synthesize_answer(
                query=query,
                timeline=timeline,
                documents=documents
            )
            
            # Step 5: Format citations
            logger.info("📝 Step 5: Formatting citations...")
            citations = self.citation_formatter.format_citations(
                answer=answer,
                format_type=citation_format
            )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Dynamic Temporal RAG completed in {execution_time:.2f}s")
            
            return {
                'success': True,
                'query': query,
                'answer': answer.answer,
                'citations': citations.citation_text,
                'timeline': timeline.to_dict(),
                'topics': topics.to_dict(),
                'metadata': {
                    'execution_time_seconds': execution_time,
                    'document_count': len(documents),
                    'confidence': answer.confidence,
                    'timeline_id': timeline.timeline_id,
                    'period_count': len(timeline.periods),
                    'sources': citations.sources,
                    'see_also': citations.see_also
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Dynamic Temporal RAG: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    async def execute_streaming(
        self,
        query: str,
        service_name: Optional[str] = None,
        citation_format: str = "markdown"
    ) -> AsyncGenerator[Dict, None]:
        """
        Execute with streaming updates (for real-time UI feedback).
        
        Yields progress updates at each step.
        """
        logger.info(f"🚀 Streaming Dynamic Temporal RAG for query: {query[:100]}...")
        
        try:
            # Step 1: Extract topics
            yield {'step': 1, 'status': 'extracting_topics', 'message': 'Analyzing query...'}
            topics = self.topic_extractor.extract(query)
            yield {'step': 1, 'status': 'topics_extracted', 'data': topics.to_dict()}
            
            if not topics.all_topics:
                yield {'step': 'complete', 'status': 'no_topics', 'message': 'No topics extracted'}
                return
            
            # Step 2: Find documents
            yield {'step': 2, 'status': 'finding_documents', 'message': 'Searching for relevant documents...'}
            search_terms = self.topic_extractor.get_search_terms(topics)
            documents = await self.document_finder.find_relevant_documents(
                search_terms=search_terms,
                service_name=service_name,
                limit=50
            )
            yield {'step': 2, 'status': 'documents_found', 'data': {'count': len(documents)}}
            
            if not documents:
                yield {'step': 'complete', 'status': 'no_documents', 'message': 'No relevant documents found'}
                return
            
            # Step 3: Construct timeline
            yield {'step': 3, 'status': 'constructing_timeline', 'message': 'Building temporal timeline...'}
            timeline = await self.timeline_constructor.construct_timeline(
                documents=documents,
                timeline_name=f"Timeline for: {query[:50]}..."
            )
            yield {'step': 3, 'status': 'timeline_constructed', 'data': timeline.to_dict()}
            
            # Step 4: Synthesize answer
            yield {'step': 4, 'status': 'synthesizing_answer', 'message': 'Generating answer...'}
            answer = await self.answer_synthesizer.synthesize_answer(
                query=query,
                timeline=timeline,
                documents=documents
            )
            yield {'step': 4, 'status': 'answer_synthesized', 'data': answer.to_dict()}
            
            # Step 5: Format citations
            yield {'step': 5, 'status': 'formatting_citations', 'message': 'Formatting citations...'}
            citations = self.citation_formatter.format_citations(
                answer=answer,
                format_type=citation_format
            )
            yield {'step': 5, 'status': 'citations_formatted'}
            
            # Complete
            yield {
                'step': 'complete',
                'status': 'success',
                'answer': answer.answer,
                'citations': citations.citation_text,
                'timeline': timeline.to_dict(),
                'metadata': {
                    'document_count': len(documents),
                    'confidence': answer.confidence,
                    'timeline_id': timeline.timeline_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error in streaming Dynamic Temporal RAG: {e}")
            yield {
                'step': 'complete',
                'status': 'error',
                'error': str(e)
            }
    
    def _generate_no_topics_response(self, query: str) -> Dict:
        """Generate response when no topics are extracted."""
        return {
            'success': False,
            'query': query,
            'error': 'No topics could be extracted from the query',
            'suggestion': 'Try rephrasing your question with more specific terms or examples'
        }
    
    def _generate_no_documents_response(
        self,
        query: str,
        topics: ExtractedTopics
    ) -> Dict:
        """Generate response when no documents are found."""
        return {
            'success': False,
            'query': query,
            'topics': topics.to_dict(),
            'error': 'No relevant documents found',
            'suggestion': 'The system could not find documents matching your query. '
                         'Try broader terms or check if the documentation exists.'
        }
    
    def cleanup_expired_caches(self):
        """Clean up expired cached timelines."""
        self.timeline_constructor.cleanup_expired()
        logger.info("Cleaned up expired timeline caches")


# Singleton instance
_orchestrator_instance = None

def get_orchestrator() -> DynamicTemporalRAGOrchestrator:
    """Get singleton orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DynamicTemporalRAGOrchestrator()
    return _orchestrator_instance

