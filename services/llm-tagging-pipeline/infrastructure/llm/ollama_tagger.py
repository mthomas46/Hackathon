"""Ollama LLM Tagger Implementation."""

import json
import logging
import time
from typing import Dict, List, Optional, Any
import httpx

from ...domain.entities.document import Document
from ...domain.entities.llm_metadata import LLMMetadata
from ...domain.value_objects.extraction_config import ExtractionConfig

logger = logging.getLogger(__name__)


class OllamaTagger:
    """
    Ollama LLM tagger implementation.
    
    Integrates with local Ollama service for LLM-based metadata extraction.
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        config: ExtractionConfig = None
    ):
        """
        Initialize tagger.
        
        Args:
            ollama_url: Ollama service URL
            config: Extraction configuration
        """
        self.ollama_url = ollama_url
        self.config = config or ExtractionConfig()
        self.client = httpx.AsyncClient(timeout=self.config.timeout_seconds)
    
    async def tag_document(self, document: Document) -> LLMMetadata:
        """
        Tag document using Ollama LLM.
        
        Args:
            document: Document to tag
            
        Returns:
            Extracted LLM metadata
            
        Raises:
            RuntimeError: If tagging fails after retries
        """
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_extraction_prompt(document)
        
        # Call Ollama with retries
        for attempt in range(self.config.max_retries):
            try:
                response = await self._call_ollama(prompt)
                
                # Parse response
                metadata = self._parse_response(response, document)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                metadata.processing_time_seconds = processing_time
                
                logger.info(
                    f"Tagged document {document.document_id} in {processing_time:.2f}s "
                    f"(attempt {attempt + 1})"
                )
                
                return metadata
                
            except Exception as e:
                logger.warning(
                    f"Tagging attempt {attempt + 1} failed for document {document.document_id}: {e}"
                )
                
                if attempt < self.config.max_retries - 1:
                    await self._delay_retry()
                else:
                    raise RuntimeError(f"Failed to tag document after {self.config.max_retries} attempts: {e}")
    
    def _build_extraction_prompt(self, document: Document) -> str:
        """
        Build extraction prompt for LLM.
        
        Args:
            document: Document to extract metadata from
            
        Returns:
            Extraction prompt
        """
        # Chunk document if needed
        content = document.content
        if self.config.chunk_large_documents and len(content) > self.config.max_chunk_size:
            content = content[:self.config.max_chunk_size]
        
        prompt = f"""Extract metadata from the following document:

Title: {document.title}

Content:
{content}

Please extract and provide the following in JSON format:
- summary: A concise 2-3 sentence summary
- keywords: List of 5-10 important keywords
- tags: List of 3-7 descriptive tags (lowercase, hyphenated)
- categories: List of 1-3 high-level categories
- topics: List of 2-5 main topics discussed
- sentiment: Overall sentiment (positive, negative, or neutral)
- entities: List of named entities (person, organization, location) as {{"type": "TYPE", "value": "VALUE"}}

Respond ONLY with valid JSON, no additional text:"""
        
        return prompt
    
    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """
        Call Ollama API.
        
        Args:
            prompt: Prompt to send
            
        Returns:
            Ollama response
            
        Raises:
            RuntimeError: If API call fails
        """
        payload = {
            "model": self.config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama API call failed: {e}")
    
    def _parse_response(self, response: Dict[str, Any], document: Document) -> LLMMetadata:
        """
        Parse Ollama response into LLMMetadata.
        
        Args:
            response: Ollama API response
            document: Original document
            
        Returns:
            Parsed LLM metadata
        """
        # Extract response text
        response_text = response.get("response", "")
        
        # Try to parse as JSON
        try:
            # Find JSON in response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Extract metadata fields
            summary = data.get("summary", "")
            keywords = data.get("keywords", [])
            tags = data.get("tags", [])
            categories = data.get("categories", [])
            topics = data.get("topics", [])
            entities = data.get("entities", [])
            sentiment = data.get("sentiment")
            
            # Calculate confidence scores (simplified - would use more sophisticated method in production)
            summary_confidence = 0.8 if summary else 0.0
            keywords_confidence = 0.8 if keywords else 0.0
            tags_confidence = 0.8 if tags else 0.0
            categories_confidence = 0.8 if categories else 0.0
            
            # Get token usage
            tokens_used = response.get("eval_count", 0)
            
            return LLMMetadata(
                summary=summary,
                keywords=keywords,
                tags=tags,
                categories=categories,
                topics=topics,
                entities=entities,
                sentiment=sentiment,
                complexity_score=None,  # Would calculate based on readability metrics
                summary_confidence=summary_confidence,
                keywords_confidence=keywords_confidence,
                tags_confidence=tags_confidence,
                categories_confidence=categories_confidence,
                model_name=self.config.model_name,
                tokens_used=tokens_used,
            )
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            # Fallback: return minimal metadata
            return LLMMetadata(
                summary="Failed to extract summary",
                keywords=[],
                tags=[],
                categories=[],
                summary_confidence=0.0,
                keywords_confidence=0.0,
                tags_confidence=0.0,
                categories_confidence=0.0,
                model_name=self.config.model_name,
                tokens_used=response.get("eval_count", 0),
            )
    
    async def _delay_retry(self) -> None:
        """Delay before retry."""
        import asyncio
        await asyncio.sleep(self.config.retry_delay_seconds)
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

