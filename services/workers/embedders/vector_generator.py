"""Vector Generator Worker - Generate embeddings using Ollama."""

import hashlib
import logging
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseEmbedder, Document, WorkerResult

logger = logging.getLogger(__name__)


class VectorGenerator(BaseEmbedder):
    """Generate vector embeddings using Ollama."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        super().__init__("vector_generator")
        self.ollama_url = ollama_url
        self.model = "nomic-embed-text"  # Good for embeddings
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed(self, documents: List[Document]) -> List[Document]:
        """
        Generate embeddings for documents.
        
        Uses Ollama's embedding API to create vector representations.
        """
        embedded_docs = []
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            for doc in documents:
                try:
                    # Generate embedding
                    embedding = await self._generate_embedding(client, doc)
                    
                    if embedding:
                        doc.embeddings = embedding
                        doc.metadata["embedding_model"] = self.model
                        doc.metadata["embedding_dim"] = len(embedding)
                        doc.metadata["has_embeddings"] = True
                    
                    embedded_docs.append(doc)
                    
                except Exception as e:
                    self.logger.error(f"Error generating embedding for {doc.doc_id}: {e}")
                    # Keep document without embedding
                    embedded_docs.append(doc)
        
        return embedded_docs
    
    async def _generate_embedding(
        self,
        client: httpx.AsyncClient,
        doc: Document
    ) -> Optional[List[float]]:
        """Generate embedding for a single document."""
        try:
            # Prepare text for embedding
            text = self._prepare_text(doc)
            
            if not text.strip():
                return None
            
            # Call Ollama API
            response = await client.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding")
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return None
    
    def _prepare_text(self, doc: Document) -> str:
        """Prepare document text for embedding."""
        # Combine title and content with more weight on title
        parts = [
            doc.title,
            doc.title,  # Repeat title for emphasis
            doc.content[:2000],  # Limit content to first 2000 chars
        ]
        
        # Add important metadata
        if doc.metadata.get("tier"):
            parts.append(f"Tier: {doc.metadata['tier']}")
        
        if doc.tags:
            parts.append(f"Tags: {', '.join(doc.tags[:5])}")
        
        text = " ".join(parts)
        
        # Clean text
        text = text.replace("\n", " ")
        text = " ".join(text.split())  # Normalize whitespace
        
        # Limit to reasonable length (Ollama handles truncation)
        return text[:4000]


# Celery task
@app.task(name="generate_vectors", bind=True)
def generate_vectors_task(
    self,
    documents: List[Dict[str, Any]],
    ollama_url: str = "http://localhost:11434"
) -> Dict[str, Any]:
    """Celery task for vector generation."""
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
    
    generator = VectorGenerator(ollama_url=ollama_url)
    
    # Run async embedding
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(generator.process({"documents": doc_objects}))
    
    return result.dict()

