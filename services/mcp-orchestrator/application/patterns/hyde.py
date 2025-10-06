"""Hypothetical Document Embeddings (HyDE) pattern implementation."""

from typing import Any, Dict, List, Optional
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings
import asyncio
import httpx
import json


class HyDEPattern(BasePattern):
    """
    Implements the Hypothetical Document Embeddings (HyDE) pattern.
    
    This pattern improves retrieval by:
    1. Generating a hypothetical answer to the query
    2. Embedding the hypothetical answer
    3. Using this embedding to retrieve actual relevant documents
    4. Generating a final answer based on retrieved documents
    
    This approach works better than direct query embedding for abstract or
    conceptual queries where the query and relevant documents may use different terminology.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.logger.info("HyDEPattern initialized.")
        self.mcp_gateway_url = settings.mcp_gateway_url
        self.vector_store_url = getattr(settings, 'vector_store_url', 'http://chromadb:8000')
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Executes the HyDE pattern.
        
        Args:
            query (str): The user query or question.
            context (Dict[str, Any]): The current operational context, including MCP info.
            **kwargs: Additional parameters:
                - model (str): LLM model to use
                - collection (str): Vector store collection name
                - top_k (int): Number of documents to retrieve
                - temperature (float): Sampling temperature
        
        Returns:
            Dict[str, Any]: Results including hypothetical answer, retrieved docs, and final answer.
        """
        self.logger.info(f"Executing HyDE for query: {query[:100]}...")
        await self._log_event("HyDE_Execution_Start", f"Starting HyDE for query: {query}", {"query": query})
        
        model = kwargs.get("model", self.settings.default_llm_model)
        collection = kwargs.get("collection", "default_mcp_knowledge")
        top_k = kwargs.get("top_k", 5)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 500)
        
        try:
            # Step 1: Generate hypothetical answer
            self.logger.info("Step 1: Generating hypothetical answer...")
            hypothetical_answer = await self._generate_hypothetical_answer(
                query, context, model, temperature, max_tokens
            )
            
            await self._log_event("HyDE_Hypothetical_Generated", "Generated hypothetical answer", {
                "query": query,
                "hypothetical_answer": hypothetical_answer[:200]
            })
            
            # Step 2: Embed the hypothetical answer
            self.logger.info("Step 2: Embedding hypothetical answer...")
            embedding = await self._embed_text(hypothetical_answer)
            
            # Step 3: Retrieve documents using the embedding
            self.logger.info("Step 3: Retrieving documents using hypothetical embedding...")
            retrieved_docs = await self._retrieve_documents(
                embedding, collection, top_k
            )
            
            await self._log_event("HyDE_Documents_Retrieved", f"Retrieved {len(retrieved_docs)} documents", {
                "query": query,
                "num_docs": len(retrieved_docs),
                "doc_ids": [doc.get('id', 'unknown') for doc in retrieved_docs]
            })
            
            # Step 4: Generate final answer based on retrieved documents
            self.logger.info("Step 4: Generating final answer from retrieved documents...")
            final_answer = await self._generate_final_answer(
                query, hypothetical_answer, retrieved_docs, model, temperature, max_tokens
            )
            
            await self._log_event("HyDE_Execution_End", "HyDE completed successfully", {
                "query": query,
                "final_answer": final_answer[:200]
            })
            
            return {
                "hypothetical_answer": hypothetical_answer,
                "retrieved_documents": retrieved_docs,
                "final_answer": final_answer,
                "retrieval_method": "hyde",
                "num_documents_retrieved": len(retrieved_docs)
            }
            
        except Exception as e:
            self.logger.error(f"Error during HyDE execution: {e}")
            await self._log_event("HyDE_Execution_Error", f"HyDE failed: {e}", {
                "query": query,
                "error": str(e)
            })
            raise
    
    async def _generate_hypothetical_answer(
        self, 
        query: str, 
        context: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Generate a hypothetical answer to the query.
        This answer may not be entirely accurate, but should use terminology
        similar to what would appear in relevant documents.
        """
        prompt = self._create_hypothetical_prompt(query, context)
        
        response = await self._call_llm_gateway(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.strip()
    
    def _create_hypothetical_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Creates the prompt for generating a hypothetical answer."""
        return (
            f"You are an expert who will provide a detailed, informative answer to the following question. "
            f"Write as if you are explaining this in a document or article. Use technical terminology and "
            f"specific details that would typically appear in documentation about this topic.\n\n"
            f"Question: {query}\n\n"
            f"Context: {json.dumps(context, indent=2) if context else 'No additional context.'}\n\n"
            f"Provide a comprehensive hypothetical answer:"
        )
    
    async def _embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.
        Uses the LLM Gateway's embedding endpoint or Ollama directly.
        """
        try:
            # Try LLM Gateway first
            response = await self.http_client.post(
                f"{self.llm_gateway_url}/api/v1/embeddings",
                json={"text": text, "model": "ollama"}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            self.logger.warning(f"LLM Gateway embedding failed, trying Ollama directly: {e}")
            
            # Fallback to Ollama directly
            try:
                response = await self.http_client.post(
                    "http://ollama:11434/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("embedding", [])
            except Exception as e2:
                self.logger.error(f"Ollama embedding also failed: {e2}")
                raise
    
    async def _retrieve_documents(
        self, 
        embedding: List[float], 
        collection: str, 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents from the vector store using the embedding.
        """
        try:
            # Query ChromaDB
            response = await self.http_client.post(
                f"{self.vector_store_url}/api/v1/collections/{collection}/query",
                json={
                    "query_embeddings": [embedding],
                    "n_results": top_k
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Format results
            documents = []
            if result.get("documents") and len(result["documents"]) > 0:
                for i, doc in enumerate(result["documents"][0]):
                    documents.append({
                        "id": result.get("ids", [[]])[0][i] if result.get("ids") else f"doc_{i}",
                        "content": doc,
                        "distance": result.get("distances", [[]])[0][i] if result.get("distances") else 0.0,
                        "metadata": result.get("metadatas", [[]])[0][i] if result.get("metadatas") else {}
                    })
            
            return documents
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Vector store HTTP error: {e.response.status_code} - {e.response.text}")
            # Return empty list instead of failing
            return []
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []
    
    async def _generate_final_answer(
        self,
        query: str,
        hypothetical_answer: str,
        retrieved_docs: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Generate the final answer based on the query and retrieved documents.
        """
        if not retrieved_docs:
            self.logger.warning("No documents retrieved, returning hypothetical answer")
            return f"{hypothetical_answer}\n\n[Note: This answer is based on general knowledge as no specific documents were retrieved.]"
        
        # Prepare document context
        doc_context = "\n\n".join([
            f"Document {i+1} (ID: {doc['id']}):\n{doc['content'][:500]}..."
            for i, doc in enumerate(retrieved_docs)
        ])
        
        prompt = (
            f"You are an expert assistant. Answer the following question based on the provided documents.\n\n"
            f"Question: {query}\n\n"
            f"Retrieved Documents:\n{doc_context}\n\n"
            f"Initial Hypothesis (for reference):\n{hypothetical_answer}\n\n"
            f"Provide a comprehensive answer grounded in the retrieved documents. "
            f"Cite document IDs when referencing specific information:"
        )
        
        final_answer = await self._call_llm_gateway(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return final_answer.strip()
    
    def get_pattern_info(self) -> Dict[str, Any]:
        """Returns metadata about the HyDE pattern."""
        return {
            "name": "Hypothetical Document Embeddings (HyDE)",
            "description": "Improves retrieval by generating a hypothetical answer, embedding it, and using it for semantic search.",
            "category": "Advanced RAG",
            "latency_impact": "Medium (20-40s per query)",
            "complexity": "Medium",
            "use_cases": [
                "Abstract or conceptual queries",
                "Queries where terminology differs from documents",
                "Exploratory information seeking",
                "Cross-domain knowledge retrieval",
                "Technical documentation search"
            ],
            "pros": [
                "Better retrieval for abstract queries",
                "Bridges terminology gap between query and documents",
                "Improves semantic understanding",
                "Works well with sparse or diverse document sets"
            ],
            "cons": [
                "Additional LLM call increases latency",
                "Hypothetical answer may introduce bias",
                "Requires good embedding model",
                "May not work well for fact-checking queries"
            ],
            "parameters": {
                "model": "LLM model to use (default: ollama)",
                "collection": "Vector store collection name",
                "top_k": "Number of documents to retrieve (default: 5)",
                "temperature": "Sampling temperature for LLM (default: 0.7)"
            },
            "when_to_use": {
                "ideal_for": [
                    "Conceptual or abstract questions",
                    "Multi-domain knowledge queries",
                    "Exploratory research",
                    "Terminology mismatch scenarios"
                ],
                "avoid_for": [
                    "Simple fact lookups",
                    "Known document retrieval",
                    "Real-time applications (due to latency)",
                    "Queries requiring exact matches"
                ]
            }
        }
