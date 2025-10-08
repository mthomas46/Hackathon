"""
Hierarchical Topic Extraction using Summarizer-Hub

Leverages the summarizer-hub service for AI-powered topic extraction:
- Main topics
- Sub-topics  
- Tangential (related) topics
- Confidence scoring

This dramatically improves contextual tagging accuracy.
"""
import httpx
import asyncio
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TopicType(Enum):
    """Type of topic relationship."""
    MAIN = "main"  # Primary topic
    SUB = "sub"  # Sub-topic (child of main topic)
    TANGENTIAL = "tangential"  # Related/adjacent topic


@dataclass
class Topic:
    """Represents a topic with hierarchical relationships."""
    name: str
    type: TopicType
    confidence: float
    parent: Optional[str] = None  # For sub-topics
    related: List[str] = field(default_factory=list)  # Tangential topics
    keywords: List[str] = field(default_factory=list)
    

@dataclass
class DocumentTopics:
    """Complete topic analysis for a document."""
    main_topics: List[Topic]
    sub_topics: List[Topic]
    tangential_topics: List[Topic]
    all_keywords: Set[str]
    confidence_score: float
    

class HierarchicalTopicExtractor:
    """
    Extract hierarchical topics using summarizer-hub AI service.
    
    Workflow:
    1. Send document content to summarizer-hub
    2. Use AI to identify main topics
    3. Extract sub-topics under each main topic
    4. Identify tangential/related topics
    5. Generate confidence scores
    """
    
    def __init__(
        self,
        summarizer_url: str = "http://localhost:5160",
        timeout: float = 30.0,
        batch_size: int = 10
    ):
        """
        Initialize topic extractor.
        
        Args:
            summarizer_url: URL of summarizer-hub service
            timeout: Request timeout in seconds
            batch_size: Number of documents to process in parallel
        """
        self.summarizer_url = summarizer_url.rstrip('/')
        self.timeout = timeout
        self.batch_size = batch_size
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def check_service_health(self) -> bool:
        """
        Check if summarizer-hub is available.
        
        Returns:
            True if service is healthy
        """
        try:
            if not self.client:
                self.client = httpx.AsyncClient(timeout=self.timeout)
            
            response = await self.client.get(f"{self.summarizer_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Summarizer-hub health check failed: {e}")
            return False
    
    async def extract_topics_single(
        self,
        text: str,
        title: str = "",
        taxonomy: str = "technical_documents"
    ) -> Optional[DocumentTopics]:
        """
        Extract hierarchical topics from a single document.
        
        Args:
            text: Document content
            title: Document title (optional, helps with context)
            taxonomy: Category taxonomy to use
        
        Returns:
            DocumentTopics or None if extraction fails
        """
        try:
            if not self.client:
                self.client = httpx.AsyncClient(timeout=self.timeout)
            
            # Step 1: Categorize document to get main topics
            categorize_payload = {
                "text": text,
                "title": title,
                "taxonomy": taxonomy,
                "confidence_threshold": 0.5,
                "include_scores": True,
                "extract_keywords": True
            }
            
            response = await self.client.post(
                f"{self.summarizer_url}/categorize",
                json=categorize_payload
            )
            
            if response.status_code != 200:
                logger.warning(f"Categorization failed: {response.status_code}")
                return None
            
            categorization = response.json()
            
            # Step 2: Use AI summarization to extract hierarchical topics
            summarize_payload = {
                "text": text,
                "prompt": (
                    "Analyze this document and extract:\n"
                    "1. Main topics (primary subjects)\n"
                    "2. Sub-topics (specific aspects under each main topic)\n"
                    "3. Tangential topics (related but not primary)\n\n"
                    "Format your response as:\n"
                    "MAIN: <topic1>, <topic2>, ...\n"
                    "SUB(<parent>): <sub1>, <sub2>, ...\n"
                    "TANGENTIAL: <related1>, <related2>, ..."
                ),
                "options": {
                    "max_length": 300,
                    "format": "text",
                    "include_confidence": True
                }
            }
            
            response = await self.client.post(
                f"{self.summarizer_url}/summarize",
                json=summarize_payload
            )
            
            if response.status_code != 200:
                logger.warning(f"Summarization failed: {response.status_code}")
                # Fallback to categorization only
                return self._parse_categorization_only(categorization)
            
            summary_data = response.json()
            
            # Step 3: Parse AI response into structured topics
            topics = self._parse_ai_response(
                summary_data.get('summary', ''),
                categorization
            )
            
            return topics
        
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}", exc_info=True)
            return None
    
    async def extract_topics_batch(
        self,
        documents: List[Tuple[str, str]],  # (text, title) pairs
        taxonomy: str = "technical_documents"
    ) -> List[Optional[DocumentTopics]]:
        """
        Extract topics from multiple documents in batch.
        
        Args:
            documents: List of (text, title) tuples
            taxonomy: Category taxonomy to use
        
        Returns:
            List of DocumentTopics (or None for failed extractions)
        """
        # Process in batches
        results = []
        
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            
            # Create tasks for parallel processing
            tasks = [
                self.extract_topics_single(text, title, taxonomy)
                for text, title in batch
            ]
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch extraction failed: {result}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results
    
    def _parse_ai_response(
        self,
        summary: str,
        categorization: Dict[str, Any]
    ) -> DocumentTopics:
        """
        Parse AI summary response into structured topics.
        
        Args:
            summary: AI-generated summary with topic structure
            categorization: Categorization response from API
        
        Returns:
            Structured DocumentTopics
        """
        main_topics: List[Topic] = []
        sub_topics: List[Topic] = []
        tangential_topics: List[Topic] = []
        all_keywords: Set[str] = set()
        
        # Parse AI response
        lines = summary.split('\n')
        current_parent = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('MAIN:'):
                # Extract main topics
                topics_str = line.replace('MAIN:', '').strip()
                for topic_name in topics_str.split(','):
                    topic_name = topic_name.strip()
                    if topic_name:
                        main_topics.append(Topic(
                            name=topic_name,
                            type=TopicType.MAIN,
                            confidence=categorization.get('confidence', 0.8)
                        ))
                        all_keywords.add(topic_name.lower())
            
            elif line.startswith('SUB('):
                # Extract sub-topics with parent
                parent_match = line.split('):')[0].replace('SUB(', '').strip()
                topics_str = line.split('):')[1].strip() if '):' in line else ''
                
                for topic_name in topics_str.split(','):
                    topic_name = topic_name.strip()
                    if topic_name:
                        sub_topics.append(Topic(
                            name=topic_name,
                            type=TopicType.SUB,
                            confidence=categorization.get('confidence', 0.7) * 0.9,
                            parent=parent_match
                        ))
                        all_keywords.add(topic_name.lower())
            
            elif line.startswith('TANGENTIAL:'):
                # Extract tangential topics
                topics_str = line.replace('TANGENTIAL:', '').strip()
                for topic_name in topics_str.split(','):
                    topic_name = topic_name.strip()
                    if topic_name:
                        tangential_topics.append(Topic(
                            name=topic_name,
                            type=TopicType.TANGENTIAL,
                            confidence=categorization.get('confidence', 0.6)
                        ))
                        all_keywords.add(topic_name.lower())
        
        # Add keywords from categorization
        if 'keywords' in categorization:
            for kw in categorization['keywords']:
                all_keywords.add(kw.lower())
        
        return DocumentTopics(
            main_topics=main_topics,
            sub_topics=sub_topics,
            tangential_topics=tangential_topics,
            all_keywords=all_keywords,
            confidence_score=categorization.get('confidence', 0.7)
        )
    
    def _parse_categorization_only(
        self,
        categorization: Dict[str, Any]
    ) -> DocumentTopics:
        """
        Fallback: Create topics from categorization only (no AI summary).
        
        Args:
            categorization: Categorization API response
        
        Returns:
            Basic DocumentTopics from categories
        """
        main_topics = []
        all_keywords = set()
        
        # Use categories as main topics
        if 'categories' in categorization:
            for cat in categorization['categories'][:3]:  # Top 3
                main_topics.append(Topic(
                    name=cat.get('name', 'Unknown'),
                    type=TopicType.MAIN,
                    confidence=cat.get('confidence', 0.5)
                ))
                all_keywords.add(cat.get('name', '').lower())
        
        # Add keywords
        if 'keywords' in categorization:
            for kw in categorization['keywords']:
                all_keywords.add(kw.lower())
        
        return DocumentTopics(
            main_topics=main_topics,
            sub_topics=[],
            tangential_topics=[],
            all_keywords=all_keywords,
            confidence_score=categorization.get('confidence', 0.5)
        )
    
    def generate_hierarchical_tags(
        self,
        topics: DocumentTopics
    ) -> List[str]:
        """
        Generate hierarchical tags from extracted topics.
        
        Format:
        - Main topics: "topic:<name>"
        - Sub-topics: "topic:<parent>:<sub>"
        - Tangential: "related:<name>"
        
        Args:
            topics: Extracted document topics
        
        Returns:
            List of hierarchical tags
        """
        tags = []
        
        # Main topics
        for topic in topics.main_topics:
            tags.append(f"topic:{topic.name.lower().replace(' ', '-')}")
        
        # Sub-topics
        for topic in topics.sub_topics:
            parent = topic.parent or 'unknown'
            tags.append(
                f"topic:{parent.lower().replace(' ', '-')}:"
                f"{topic.name.lower().replace(' ', '-')}"
            )
        
        # Tangential topics
        for topic in topics.tangential_topics:
            tags.append(f"related:{topic.name.lower().replace(' ', '-')}")
        
        return tags

