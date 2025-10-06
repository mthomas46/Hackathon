"""Auto Tagger Worker - Generate tags using LLM."""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseEmbedder, Document, WorkerResult

logger = logging.getLogger(__name__)


class AutoTagger(BaseEmbedder):
    """Automatically generate tags using LLM."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        super().__init__("auto_tagger")
        self.ollama_url = ollama_url
        self.model = "llama2"  # Or whatever model is available
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed(self, documents: List[Document]) -> List[Document]:
        """
        Generate tags for documents using LLM.
        
        Analyzes content and generates relevant tags.
        """
        tagged_docs = []
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            for doc in documents:
                try:
                    # Generate tags
                    new_tags = await self._generate_tags(client, doc)
                    
                    if new_tags:
                        # Merge with existing tags
                        existing = set(doc.tags)
                        existing.update(new_tags)
                        doc.tags = list(existing)
                        
                        doc.metadata["auto_tagged"] = True
                        doc.metadata["generated_tags"] = new_tags
                    
                    tagged_docs.append(doc)
                    
                except Exception as e:
                    self.logger.error(f"Error generating tags for {doc.doc_id}: {e}")
                    tagged_docs.append(doc)
        
        return tagged_docs
    
    async def _generate_tags(
        self,
        client: httpx.AsyncClient,
        doc: Document
    ) -> List[str]:
        """Generate tags for a single document."""
        try:
            # Prepare prompt
            prompt = self._create_tagging_prompt(doc)
            
            # Call Ollama
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower for more consistent tagging
                        "num_predict": 100,
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                # Parse tags from response
                tags = self._parse_tags(response_text)
                return tags
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return []
        
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return []
    
    def _create_tagging_prompt(self, doc: Document) -> str:
        """Create prompt for tag generation."""
        # Truncate content
        content_preview = doc.content[:1000]
        
        prompt = f"""Analyze this document and generate 3-7 relevant tags.

Title: {doc.title}
Source: {doc.source} ({doc.source_type})
Tier: {doc.tier or 'unknown'}

Content:
{content_preview}

Generate tags that describe:
1. The main topics/subjects
2. The document type (e.g., documentation, code, issue, design)
3. Technical concepts mentioned
4. Relevant technologies/tools

Output ONLY the tags as a comma-separated list. No explanation.

Tags:"""
        
        return prompt
    
    def _parse_tags(self, response: str) -> List[str]:
        """Parse tags from LLM response."""
        # Clean response
        response = response.strip()
        
        # Try to extract comma-separated list
        if "," in response:
            tags = [t.strip().lower() for t in response.split(",")]
        else:
            # Try space-separated
            tags = [t.strip().lower() for t in response.split()]
        
        # Clean tags
        cleaned = []
        for tag in tags:
            # Remove special characters
            tag = "".join(c for c in tag if c.isalnum() or c in ["-", "_", " "])
            tag = tag.strip()
            
            # Remove common stopwords
            if tag and tag not in ["the", "a", "an", "and", "or", "but", "in", "on", "at"]:
                cleaned.append(tag)
        
        # Limit to 10 tags
        return cleaned[:10]


# Celery task
@app.task(name="auto_tag", bind=True)
def auto_tag_task(
    self,
    documents: List[Dict[str, Any]],
    ollama_url: str = "http://localhost:11434"
) -> Dict[str, Any]:
    """Celery task for auto-tagging."""
    import asyncio
    
    # Convert dicts back to Document objects
    from services.workers.shared.base_worker import Document
    
    doc_objects = []
    for d in documents:
        doc = Document(
            doc_id=d["doc_id"],
            source=d["source"],
            source_type=d["source_type"],
            title=d["title"],
            content=d["content"],
            raw_content=d.get("raw_content", ""),
            metadata=d.get("metadata", {}),
            tags=d.get("tags", []),
            tier=d.get("tier"),
        )
        doc_objects.append(doc)
    
    tagger = AutoTagger(ollama_url=ollama_url)
    
    # Run async tagging
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(tagger.process({"documents": doc_objects}))
    
    return result.dict()

