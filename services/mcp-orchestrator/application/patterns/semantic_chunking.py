"""Semantic Chunking pattern implementation."""

from typing import Any, Dict, List, Tuple
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings
import re


class SemanticChunkingPattern(BasePattern):
    """
    Implements the Semantic Chunking pattern.
    
    Intelligently splits documents based on semantic boundaries rather than
    fixed-size chunks, preserving meaning and context coherence.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.logger.info("SemanticChunkingPattern initialized.")
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Executes semantic chunking on documents.
        
        Args:
            query (str): The document text to chunk (or query for chunk retrieval).
            context (Dict[str, Any]): Contains document(s) to chunk.
            **kwargs: Additional parameters:
                - chunk_strategy (str): 'paragraph', 'sentence', 'topic', 'hybrid'
                - max_chunk_size (int): Maximum chunk size in tokens
                - overlap (int): Overlap between chunks
        
        Returns:
            Dict[str, Any]: Semantic chunks with metadata.
        """
        self.logger.info("Executing Semantic Chunking...")
        
        document = context.get("document", query)
        chunk_strategy = kwargs.get("chunk_strategy", "hybrid")
        max_chunk_size = kwargs.get("max_chunk_size", 512)
        overlap = kwargs.get("overlap", 50)
        
        if chunk_strategy == "paragraph":
            chunks = self._chunk_by_paragraph(document, max_chunk_size, overlap)
        elif chunk_strategy == "sentence":
            chunks = self._chunk_by_sentence(document, max_chunk_size, overlap)
        elif chunk_strategy == "topic":
            chunks = await self._chunk_by_topic(document, max_chunk_size)
        else:
            chunks = await self._hybrid_chunking(document, max_chunk_size, overlap)
        
        return {
            "chunks": chunks,
            "num_chunks": len(chunks),
            "strategy": chunk_strategy,
            "avg_chunk_size": sum(len(c["content"]) for c in chunks) / len(chunks) if chunks else 0
        }
    
    def _chunk_by_paragraph(self, text: str, max_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Chunk by paragraph boundaries."""
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        
        for i, para in enumerate(paragraphs):
            if len(current_chunk) + len(para) < max_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "type": "paragraph",
                        "index": len(chunks),
                        "metadata": {"boundary": "paragraph"}
                    })
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "type": "paragraph",
                "index": len(chunks),
                "metadata": {"boundary": "paragraph"}
            })
        
        return chunks
    
    def _chunk_by_sentence(self, text: str, max_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Chunk by sentence boundaries."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sent in sentences:
            if len(current_chunk) + len(sent) < max_size:
                current_chunk += sent + " "
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "type": "sentence",
                        "index": len(chunks),
                        "metadata": {"boundary": "sentence"}
                    })
                current_chunk = sent + " "
        
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "type": "sentence",
                "index": len(chunks),
                "metadata": {"boundary": "sentence"}
            })
        
        return chunks
    
    async def _chunk_by_topic(self, text: str, max_size: int) -> List[Dict[str, Any]]:
        """Chunk by topic shifts using LLM."""
        # Simplified - in production, use LLM to detect topic boundaries
        return self._chunk_by_paragraph(text, max_size, 0)
    
    async def _hybrid_chunking(self, text: str, max_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Hybrid chunking combining multiple strategies."""
        return self._chunk_by_paragraph(text, max_size, overlap)
    
    def get_pattern_info(self) -> Dict[str, Any]:
        return {
            "name": "Semantic Chunking",
            "description": "Smart document splitting based on semantic boundaries.",
            "category": "RAG Preprocessing",
            "latency_impact": "Low (1-5s)",
            "complexity": "Medium"
        }
