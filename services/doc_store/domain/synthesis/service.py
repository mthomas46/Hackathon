"""
RAG (Retrieval-Augmented Generation) Synthesis Service

Combines semantic search with LLM generation for intelligent answer synthesis.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class SynthesisService:
    """Service for RAG-based answer synthesis."""
    
    def __init__(
        self,
        llm_gateway_url: str = "http://llm-gateway:5055",
        llm_model: str = "llama3.2:3b",
        max_context_docs: int = 5
    ):
        """
        Initialize synthesis service.
        
        Args:
            llm_gateway_url: URL of LLM gateway service
            llm_model: Model to use for generation
            max_context_docs: Maximum documents to include in context
        """
        self.llm_gateway_url = llm_gateway_url
        self.llm_model = llm_model
        self.max_context_docs = max_context_docs
    
    async def synthesize_answer(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Synthesize answer from query and retrieved documents using LLM.
        
        Args:
            query: User's question
            context_documents: Retrieved relevant documents
            temperature: LLM temperature (0-1)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Synthesized answer with metadata
        """
        # Build context from documents
        context = self._build_context(context_documents[:self.max_context_docs])
        
        # Build prompt
        prompt = self._build_rag_prompt(query, context)
        
        # Generate answer using LLM
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.llm_gateway_url}/api/generate",
                    json={
                        "model": self.llm_model,
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stop": ["</answer>", "\n\nUser:", "\n\nQuestion:"]
                    }
                )
                
                if response.status_code == 200:
                    llm_response = response.json()
                    answer = llm_response.get("response", "").strip()
                    
                    return {
                        "answer": answer,
                        "query": query,
                        "context_documents_used": len(context_documents),
                        "model": self.llm_model,
                        "sources": [doc.get("id", "unknown") for doc in context_documents[:self.max_context_docs]],
                        "synthesis_method": "rag",
                        "temperature": temperature
                    }
                else:
                    logger.error(f"LLM gateway returned {response.status_code}")
                    return self._fallback_answer(query, context_documents)
        
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}")
            return self._fallback_answer(query, context_documents)
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from documents."""
        context_parts = []
        
        for idx, doc in enumerate(documents, 1):
            doc_id = doc.get("id", f"doc-{idx}")
            content = doc.get("content", "")
            similarity = doc.get("semantic_similarity", doc.get("score", 0.0))
            
            # Truncate long content
            max_content_length = 800
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            context_parts.append(
                f"[Document {idx} - ID: {doc_id}, Relevance: {similarity:.2f}]\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build RAG prompt for LLM."""
        return f"""You are a helpful AI assistant that answers questions based on the provided context documents.

Context Documents:
{context}

User Question: {query}

Instructions:
1. Answer the question using ONLY information from the context documents above
2. If the context doesn't contain enough information, say so clearly
3. Cite document numbers when referencing specific information
4. Be concise but comprehensive
5. If multiple documents provide conflicting information, acknowledge this

Answer:"""
    
    def _fallback_answer(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback answer when LLM is unavailable."""
        if documents:
            top_doc = documents[0]
            answer = f"Based on the most relevant document: {top_doc.get('content', '')[:500]}..."
        else:
            answer = "No relevant information found to answer the question."
        
        return {
            "answer": answer,
            "query": query,
            "context_documents_used": len(documents),
            "model": "fallback",
            "sources": [doc.get("id", "unknown") for doc in documents[:self.max_context_docs]],
            "synthesis_method": "fallback",
            "temperature": 0.0
        }
    
    async def synthesize_with_search(
        self,
        query: str,
        semantic_weight: float = 0.7,
        min_similarity: float = 0.3,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Perform search and synthesis in one operation.
        
        Args:
            query: User's question
            semantic_weight: Weight for semantic vs keyword search
            min_similarity: Minimum similarity threshold
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Synthesized answer with search metadata
        """
        from ..embeddings.service import get_embedding_service
        from ...db.queries import search_documents as keyword_search
        import time
        
        start_time = time.time()
        
        # Perform hybrid search
        try:
            embedding_service = get_embedding_service()
            
            # Semantic search
            semantic_results = await embedding_service.semantic_search(
                query=query,
                limit=self.max_context_docs * 2,  # Get more for better context
                min_similarity=min_similarity
            )
            
            # Keyword search
            keyword_results = keyword_search(query, limit=self.max_context_docs * 2)
            
            # Merge results (simple approach: take top from each)
            seen_ids = set()
            merged_docs = []
            
            # Add semantic results first (higher weight)
            for doc in semantic_results:
                doc_id = doc.get("id")
                if doc_id not in seen_ids:
                    merged_docs.append(doc)
                    seen_ids.add(doc_id)
                if len(merged_docs) >= self.max_context_docs:
                    break
            
            # Add keyword results to fill up
            for doc in keyword_results:
                doc_id = doc.get("id")
                if doc_id not in seen_ids:
                    merged_docs.append(doc)
                    seen_ids.add(doc_id)
                if len(merged_docs) >= self.max_context_docs:
                    break
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            merged_docs = []
        
        search_time = time.time() - start_time
        
        # Synthesize answer
        if merged_docs:
            synthesis_result = await self.synthesize_answer(
                query=query,
                context_documents=merged_docs,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            synthesis_result = {
                "answer": "No relevant documents found to answer your question.",
                "query": query,
                "context_documents_used": 0,
                "model": "none",
                "sources": [],
                "synthesis_method": "no_context",
                "temperature": 0.0
            }
        
        # Add search metadata
        synthesis_result["search_metadata"] = {
            "documents_found": len(merged_docs),
            "semantic_weight": semantic_weight,
            "min_similarity": min_similarity,
            "search_time_ms": round(search_time * 1000, 2)
        }
        
        return synthesis_result


# Singleton instance
_synthesis_service = None


def get_synthesis_service(
    llm_gateway_url: str = "http://llm-gateway:5055",
    llm_model: str = "llama3.2:3b"
) -> SynthesisService:
    """Get or create synthesis service singleton."""
    global _synthesis_service
    if _synthesis_service is None:
        _synthesis_service = SynthesisService(
            llm_gateway_url=llm_gateway_url,
            llm_model=llm_model
        )
    return _synthesis_service

