"""Parent Document Retriever pattern implementation."""

from typing import Any, Dict, List, Optional, Tuple
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings
import asyncio
import httpx
import json


class ParentDocumentRetrieverPattern(BasePattern):
    """
    Implements the Parent Document Retriever pattern.
    
    This pattern improves context quality by:
    1. Retrieving small, specific chunks that match the query
    2. Returning the larger parent documents these chunks belong to
    3. Providing richer context while maintaining retrieval precision
    
    This solves the problem of retrieving semantically relevant chunks
    that lack sufficient surrounding context for comprehensive answers.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.logger.info("ParentDocumentRetrieverPattern initialized.")
        self.mcp_gateway_url = settings.mcp_gateway_url
        self.vector_store_url = getattr(settings, 'vector_store_url', 'http://chromadb:8000')
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Executes the Parent Document Retriever pattern.
        
        Args:
            query (str): The user query or question.
            context (Dict[str, Any]): The current operational context.
            **kwargs: Additional parameters:
                - model (str): LLM model to use
                - collection (str): Vector store collection name
                - top_k (int): Number of child chunks to retrieve
                - expansion_strategy (str): 'full_parent', 'paragraph', 'section'
                - temperature (float): Sampling temperature
        
        Returns:
            Dict[str, Any]: Results including child chunks, parent documents, and final answer.
        """
        self.logger.info(f"Executing Parent Document Retriever for query: {query[:100]}...")
        await self._log_event("ParentRetriever_Start", f"Starting retrieval for query: {query}", {"query": query})
        
        model = kwargs.get("model", self.settings.default_llm_model)
        collection = kwargs.get("collection", "default_mcp_knowledge")
        top_k = kwargs.get("top_k", 5)
        expansion_strategy = kwargs.get("expansion_strategy", "full_parent")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 800)
        
        try:
            # Step 1: Embed the query
            self.logger.info("Step 1: Embedding query...")
            query_embedding = await self._embed_query(query)
            
            # Step 2: Retrieve child chunks
            self.logger.info("Step 2: Retrieving child chunks...")
            child_chunks = await self._retrieve_child_chunks(
                query_embedding, collection, top_k
            )
            
            await self._log_event("ParentRetriever_Children_Retrieved", 
                                f"Retrieved {len(child_chunks)} child chunks", {
                "query": query,
                "num_chunks": len(child_chunks),
                "chunk_ids": [chunk.get('id', 'unknown') for chunk in child_chunks]
            })
            
            # Step 3: Expand to parent documents
            self.logger.info("Step 3: Expanding to parent documents...")
            parent_documents = await self._expand_to_parents(
                child_chunks, expansion_strategy
            )
            
            await self._log_event("ParentRetriever_Parents_Retrieved",
                                f"Expanded to {len(parent_documents)} parent documents", {
                "query": query,
                "num_parents": len(parent_documents),
                "expansion_strategy": expansion_strategy
            })
            
            # Step 4: Generate answer with enriched context
            self.logger.info("Step 4: Generating answer with parent context...")
            final_answer = await self._generate_answer_with_context(
                query, child_chunks, parent_documents, model, temperature, max_tokens
            )
            
            await self._log_event("ParentRetriever_End", "Parent retrieval completed", {
                "query": query,
                "final_answer": final_answer[:200]
            })
            
            return {
                "child_chunks": child_chunks,
                "parent_documents": parent_documents,
                "final_answer": final_answer,
                "retrieval_method": "parent_document_retriever",
                "expansion_strategy": expansion_strategy,
                "num_child_chunks": len(child_chunks),
                "num_parent_documents": len(parent_documents)
            }
            
        except Exception as e:
            self.logger.error(f"Error during Parent Document Retriever execution: {e}")
            await self._log_event("ParentRetriever_Error", f"Retrieval failed: {e}", {
                "query": query,
                "error": str(e)
            })
            raise
    
    async def _embed_query(self, query: str) -> List[float]:
        """Generate embeddings for the query."""
        try:
            # Try LLM Gateway first
            response = await self.http_client.post(
                f"{self.llm_gateway_url}/api/v1/embeddings",
                json={"text": query, "model": "ollama"}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            self.logger.warning(f"LLM Gateway embedding failed, trying Ollama: {e}")
            
            # Fallback to Ollama
            try:
                response = await self.http_client.post(
                    "http://ollama:11434/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": query}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("embedding", [])
            except Exception as e2:
                self.logger.error(f"Ollama embedding failed: {e2}")
                raise
    
    async def _retrieve_child_chunks(
        self,
        embedding: List[float],
        collection: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve small child chunks that match the query."""
        try:
            response = await self.http_client.post(
                f"{self.vector_store_url}/api/v1/collections/{collection}/query",
                json={
                    "query_embeddings": [embedding],
                    "n_results": top_k
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Format child chunks
            chunks = []
            if result.get("documents") and len(result["documents"]) > 0:
                for i, doc in enumerate(result["documents"][0]):
                    metadata = result.get("metadatas", [[]])[0][i] if result.get("metadatas") else {}
                    chunks.append({
                        "id": result.get("ids", [[]])[0][i] if result.get("ids") else f"chunk_{i}",
                        "content": doc,
                        "distance": result.get("distances", [[]])[0][i] if result.get("distances") else 0.0,
                        "metadata": metadata,
                        "parent_id": metadata.get("parent_id", None),
                        "chunk_index": metadata.get("chunk_index", i)
                    })
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error retrieving child chunks: {e}")
            return []
    
    async def _expand_to_parents(
        self,
        child_chunks: List[Dict[str, Any]],
        expansion_strategy: str
    ) -> List[Dict[str, Any]]:
        """
        Expand child chunks to their parent documents.
        
        Expansion strategies:
        - 'full_parent': Return entire parent document
        - 'paragraph': Return surrounding paragraph
        - 'section': Return surrounding section
        """
        parent_documents = []
        seen_parent_ids = set()
        
        for chunk in child_chunks:
            parent_id = chunk.get("parent_id")
            
            if not parent_id:
                # If no parent ID, treat chunk as its own parent
                parent_documents.append({
                    "id": chunk["id"],
                    "content": chunk["content"],
                    "source": "child_as_parent",
                    "child_chunks": [chunk["id"]],
                    "metadata": chunk.get("metadata", {})
                })
                continue
            
            # Avoid duplicate parents
            if parent_id in seen_parent_ids:
                continue
            
            seen_parent_ids.add(parent_id)
            
            # Retrieve parent document
            parent_doc = await self._retrieve_parent_by_id(parent_id, expansion_strategy, chunk)
            if parent_doc:
                parent_documents.append(parent_doc)
        
        return parent_documents
    
    async def _retrieve_parent_by_id(
        self,
        parent_id: str,
        expansion_strategy: str,
        child_chunk: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a parent document by ID."""
        try:
            # In a real implementation, this would query a document store
            # For now, simulate parent document retrieval
            
            # Mock parent document construction
            if expansion_strategy == "full_parent":
                # Return full parent (simulated as multiple chunks)
                parent_content = self._simulate_full_parent(child_chunk)
            elif expansion_strategy == "paragraph":
                parent_content = self._simulate_paragraph_context(child_chunk)
            elif expansion_strategy == "section":
                parent_content = self._simulate_section_context(child_chunk)
            else:
                parent_content = child_chunk["content"]
            
            return {
                "id": parent_id,
                "content": parent_content,
                "source": f"parent_via_{expansion_strategy}",
                "child_chunks": [child_chunk["id"]],
                "metadata": child_chunk.get("metadata", {})
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving parent {parent_id}: {e}")
            return None
    
    def _simulate_full_parent(self, child_chunk: Dict[str, Any]) -> str:
        """Simulate retrieving the full parent document."""
        # In production, this would fetch from document store
        chunk_content = child_chunk["content"]
        return (
            f"[START OF PARENT DOCUMENT]\n\n"
            f"...context before...\n\n"
            f"{chunk_content}\n\n"
            f"...context after...\n\n"
            f"[END OF PARENT DOCUMENT]"
        )
    
    def _simulate_paragraph_context(self, child_chunk: Dict[str, Any]) -> str:
        """Simulate retrieving surrounding paragraph context."""
        chunk_content = child_chunk["content"]
        return (
            f"...previous sentence. {chunk_content} Following sentence..."
        )
    
    def _simulate_section_context(self, child_chunk: Dict[str, Any]) -> str:
        """Simulate retrieving surrounding section context."""
        chunk_content = child_chunk["content"]
        return (
            f"## Section Title\n\n"
            f"Section introduction...\n\n"
            f"{chunk_content}\n\n"
            f"Section conclusion..."
        )
    
    async def _generate_answer_with_context(
        self,
        query: str,
        child_chunks: List[Dict[str, Any]],
        parent_documents: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate the final answer using parent document context."""
        if not parent_documents:
            return "No relevant information found to answer the query."
        
        # Prepare context from parent documents
        context_parts = []
        for i, parent in enumerate(parent_documents):
            context_parts.append(
                f"Document {i+1} (ID: {parent['id']}):\n{parent['content'][:800]}..."
            )
        
        combined_context = "\n\n".join(context_parts)
        
        prompt = (
            f"You are an expert assistant. Answer the following question based on the provided documents. "
            f"These documents provide rich context around the relevant information.\n\n"
            f"Question: {query}\n\n"
            f"Documents with Full Context:\n{combined_context}\n\n"
            f"Provide a comprehensive answer. Cite document IDs when referencing information:"
        )
        
        answer = await self._call_llm_gateway(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return answer.strip()
    
    def get_pattern_info(self) -> Dict[str, Any]:
        """Returns metadata about the Parent Document Retriever pattern."""
        return {
            "name": "Parent Document Retriever",
            "description": "Retrieves small, precise chunks then returns larger parent documents for richer context.",
            "category": "Advanced RAG",
            "latency_impact": "Medium (15-30s per query)",
            "complexity": "Medium",
            "use_cases": [
                "Questions requiring surrounding context",
                "Nuanced information needs",
                "Multi-step reasoning over documents",
                "Understanding context-dependent information",
                "Avoiding chunking artifacts"
            ],
            "pros": [
                "Better context than chunk-only retrieval",
                "Maintains retrieval precision",
                "Avoids losing important surrounding information",
                "Flexible expansion strategies",
                "Works well with hierarchical documents"
            ],
            "cons": [
                "Increased token usage for parent docs",
                "Potential for irrelevant context",
                "Requires parent-child relationships in storage",
                "More complex document management"
            ],
            "parameters": {
                "model": "LLM model to use (default: ollama)",
                "collection": "Vector store collection name",
                "top_k": "Number of child chunks to retrieve (default: 5)",
                "expansion_strategy": "How to expand: 'full_parent', 'paragraph', 'section'",
                "temperature": "Sampling temperature for LLM (default: 0.7)"
            },
            "when_to_use": {
                "ideal_for": [
                    "Complex questions needing context",
                    "Multi-paragraph reasoning",
                    "Understanding relationships between concepts",
                    "Avoiding chunk boundary issues"
                ],
                "avoid_for": [
                    "Simple fact lookups",
                    "Token-constrained applications",
                    "Real-time requirements",
                    "Flat document structures"
                ]
            }
        }
