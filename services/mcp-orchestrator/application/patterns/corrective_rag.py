"""Corrective RAG (CRAG) pattern implementation."""

from typing import Any, Dict, List, Optional, Tuple
from services.mcp_orchestrator.application.patterns.base import BasePattern
from services.mcp_orchestrator.infrastructure.config.settings import Settings
import asyncio
import httpx
import json
from enum import Enum


class RetrievalQuality(Enum):
    """Enum for retrieval quality assessment."""
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    FAILED = "failed"


class CorrectiveRAGPattern(BasePattern):
    """
    Implements the Corrective RAG (CRAG) pattern.
    
    This pattern improves retrieval robustness by:
    1. Performing initial retrieval from local knowledge base
    2. Evaluating the quality and relevance of retrieved documents
    3. If quality is insufficient, falling back to web search
    4. Fusing results from multiple sources
    5. Generating a comprehensive answer
    
    This pattern is especially useful for critical applications where
    retrieval failures must be gracefully handled.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.logger.info("CorrectiveRAGPattern initialized.")
        self.mcp_gateway_url = settings.mcp_gateway_url
        self.vector_store_url = getattr(settings, 'vector_store_url', 'http://chromadb:8000')
        self.web_search_enabled = getattr(settings, 'web_search_enabled', True)
        self.quality_threshold = getattr(settings, 'crag_quality_threshold', 0.6)
        
    async def execute(self, query: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Executes the Corrective RAG pattern.
        
        Args:
            query (str): The user query or question.
            context (Dict[str, Any]): The current operational context.
            **kwargs: Additional parameters:
                - model (str): LLM model to use
                - collection (str): Vector store collection name
                - top_k (int): Number of documents to retrieve
                - quality_threshold (float): Minimum quality score (0-1)
                - enable_web_fallback (bool): Whether to use web search fallback
                - temperature (float): Sampling temperature
        
        Returns:
            Dict[str, Any]: Results including retrieval assessment, sources used, and final answer.
        """
        self.logger.info(f"Executing Corrective RAG for query: {query[:100]}...")
        await self._log_event("CRAG_Start", f"Starting CRAG for query: {query}", {"query": query})
        
        model = kwargs.get("model", self.settings.default_llm_model)
        collection = kwargs.get("collection", "default_mcp_knowledge")
        top_k = kwargs.get("top_k", 5)
        quality_threshold = kwargs.get("quality_threshold", self.quality_threshold)
        enable_web_fallback = kwargs.get("enable_web_fallback", self.web_search_enabled)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 800)
        
        retrieval_history = []
        
        try:
            # Step 1: Initial retrieval from knowledge base
            self.logger.info("Step 1: Initial retrieval from knowledge base...")
            query_embedding = await self._embed_query(query)
            initial_docs = await self._retrieve_documents(query_embedding, collection, top_k)
            
            retrieval_history.append({
                "source": "knowledge_base",
                "num_docs": len(initial_docs),
                "timestamp": self._get_timestamp()
            })
            
            await self._log_event("CRAG_Initial_Retrieval", 
                                f"Retrieved {len(initial_docs)} documents from KB", {
                "query": query,
                "num_docs": len(initial_docs)
            })
            
            # Step 2: Evaluate retrieval quality
            self.logger.info("Step 2: Evaluating retrieval quality...")
            quality_assessment = await self._evaluate_retrieval_quality(
                query, initial_docs, model, temperature
            )
            
            await self._log_event("CRAG_Quality_Assessment",
                                f"Quality: {quality_assessment['quality']}, Score: {quality_assessment['score']:.2f}", {
                "query": query,
                "quality": quality_assessment["quality"].value,
                "score": quality_assessment["score"],
                "reasoning": quality_assessment["reasoning"][:200]
            })
            
            # Step 3: Decide on corrective action
            final_docs = initial_docs
            sources_used = ["knowledge_base"]
            
            if quality_assessment["score"] < quality_threshold:
                self.logger.warning(f"Quality score {quality_assessment['score']:.2f} below threshold {quality_threshold}")
                
                if enable_web_fallback:
                    # Step 4: Web search fallback
                    self.logger.info("Step 4: Performing web search fallback...")
                    web_docs = await self._web_search_fallback(query)
                    
                    retrieval_history.append({
                        "source": "web_search",
                        "num_docs": len(web_docs),
                        "timestamp": self._get_timestamp()
                    })
                    
                    await self._log_event("CRAG_Web_Fallback",
                                        f"Retrieved {len(web_docs)} documents from web", {
                        "query": query,
                        "num_docs": len(web_docs)
                    })
                    
                    # Step 5: Fuse results
                    final_docs = await self._fuse_results(initial_docs, web_docs)
                    sources_used.append("web_search")
                else:
                    self.logger.warning("Web fallback disabled, using low-quality KB results")
                    await self._log_event("CRAG_No_Fallback",
                                        "Quality low but fallback disabled", {
                        "query": query,
                        "quality_score": quality_assessment["score"]
                    })
            
            # Step 6: Generate final answer
            self.logger.info("Step 6: Generating final answer...")
            final_answer = await self._generate_corrective_answer(
                query, final_docs, sources_used, quality_assessment, model, temperature, max_tokens
            )
            
            await self._log_event("CRAG_Complete", "CRAG completed successfully", {
                "query": query,
                "sources_used": sources_used,
                "final_quality": quality_assessment["quality"].value,
                "final_answer": final_answer[:200]
            })
            
            return {
                "query": query,
                "initial_documents": initial_docs,
                "final_documents": final_docs,
                "quality_assessment": {
                    "quality": quality_assessment["quality"].value,
                    "score": quality_assessment["score"],
                    "reasoning": quality_assessment["reasoning"]
                },
                "sources_used": sources_used,
                "retrieval_history": retrieval_history,
                "corrective_action_taken": len(sources_used) > 1,
                "final_answer": final_answer,
                "num_documents_used": len(final_docs)
            }
            
        except Exception as e:
            self.logger.error(f"Error during CRAG execution: {e}")
            await self._log_event("CRAG_Error", f"CRAG failed: {e}", {
                "query": query,
                "error": str(e)
            })
            raise
    
    async def _embed_query(self, query: str) -> List[float]:
        """Generate embeddings for the query."""
        try:
            response = await self.http_client.post(
                f"{self.llm_gateway_url}/api/v1/embeddings",
                json={"text": query, "model": "ollama"}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            self.logger.warning(f"LLM Gateway embedding failed, trying Ollama: {e}")
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
    
    async def _retrieve_documents(
        self,
        embedding: List[float],
        collection: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve documents from the knowledge base."""
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
            
            documents = []
            if result.get("documents") and len(result["documents"]) > 0:
                for i, doc in enumerate(result["documents"][0]):
                    documents.append({
                        "id": result.get("ids", [[]])[0][i] if result.get("ids") else f"doc_{i}",
                        "content": doc,
                        "distance": result.get("distances", [[]])[0][i] if result.get("distances") else 0.0,
                        "metadata": result.get("metadatas", [[]])[0][i] if result.get("metadatas") else {},
                        "source": "knowledge_base"
                    })
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []
    
    async def _evaluate_retrieval_quality(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        model: str,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Evaluate the quality and relevance of retrieved documents.
        Returns a quality assessment with score, quality level, and reasoning.
        """
        if not documents:
            return {
                "quality": RetrievalQuality.FAILED,
                "score": 0.0,
                "reasoning": "No documents retrieved"
            }
        
        # Prepare document summaries for evaluation
        doc_summaries = "\n\n".join([
            f"Doc {i+1}: {doc['content'][:200]}..."
            for i, doc in enumerate(documents[:3])  # Evaluate top 3
        ])
        
        eval_prompt = (
            f"You are an expert evaluator. Assess the relevance of the following retrieved documents "
            f"to the given query. Rate the overall retrieval quality.\n\n"
            f"Query: {query}\n\n"
            f"Retrieved Documents:\n{doc_summaries}\n\n"
            f"Provide:\n"
            f"1. A relevance score from 0.0 to 1.0\n"
            f"2. A quality rating: EXCELLENT, GOOD, POOR, or FAILED\n"
            f"3. Brief reasoning\n\n"
            f"Format your response as:\n"
            f"SCORE: <number>\n"
            f"QUALITY: <rating>\n"
            f"REASONING: <explanation>"
        )
        
        try:
            evaluation = await self._call_llm_gateway(
                prompt=eval_prompt,
                model=model,
                temperature=0.2,  # Low temperature for consistent evaluation
                max_tokens=200
            )
            
            # Parse evaluation
            score = 0.5  # Default
            quality = RetrievalQuality.GOOD
            reasoning = evaluation
            
            if "SCORE:" in evaluation:
                try:
                    score_str = evaluation.split("SCORE:")[1].split("\n")[0].strip()
                    score = float(score_str)
                except:
                    pass
            
            if "QUALITY:" in evaluation:
                quality_str = evaluation.split("QUALITY:")[1].split("\n")[0].strip().upper()
                if "EXCELLENT" in quality_str:
                    quality = RetrievalQuality.EXCELLENT
                elif "GOOD" in quality_str:
                    quality = RetrievalQuality.GOOD
                elif "POOR" in quality_str:
                    quality = RetrievalQuality.POOR
                elif "FAILED" in quality_str:
                    quality = RetrievalQuality.FAILED
            
            if "REASONING:" in evaluation:
                reasoning = evaluation.split("REASONING:")[1].strip()
            
            return {
                "quality": quality,
                "score": score,
                "reasoning": reasoning
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating retrieval quality: {e}")
            return {
                "quality": RetrievalQuality.GOOD,
                "score": 0.5,
                "reasoning": f"Evaluation error: {e}"
            }
    
    async def _web_search_fallback(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform web search as a fallback.
        In production, this would integrate with a real web search API.
        """
        self.logger.info(f"Performing web search for: {query}")
        
        # Mock web search results
        # In production, integrate with APIs like Google Search, Bing, DuckDuckGo, etc.
        mock_results = [
            {
                "id": "web_1",
                "content": f"Web search result for '{query}'. This would contain actual web content...",
                "distance": 0.3,
                "metadata": {
                    "url": "https://example.com/page1",
                    "title": f"Information about {query}",
                    "snippet": "Relevant web content snippet..."
                },
                "source": "web_search"
            },
            {
                "id": "web_2",
                "content": f"Another web result related to '{query}' with additional information...",
                "distance": 0.4,
                "metadata": {
                    "url": "https://example.com/page2",
                    "title": f"More on {query}",
                    "snippet": "Additional relevant content..."
                },
                "source": "web_search"
            }
        ]
        
        await self._log_event("CRAG_Web_Search", f"Mock web search for: {query}", {
            "query": query,
            "num_results": len(mock_results),
            "note": "Using mock results - integrate real search API in production"
        })
        
        return mock_results
    
    async def _fuse_results(
        self,
        kb_docs: List[Dict[str, Any]],
        web_docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fuse results from knowledge base and web search.
        Implements a simple fusion strategy - can be enhanced with reranking.
        """
        # Simple concatenation with deduplication
        fused = []
        seen_contents = set()
        
        # Prioritize KB docs (they're from trusted source)
        for doc in kb_docs:
            content_hash = hash(doc["content"][:100])
            if content_hash not in seen_contents:
                fused.append(doc)
                seen_contents.add(content_hash)
        
        # Add web docs
        for doc in web_docs:
            content_hash = hash(doc["content"][:100])
            if content_hash not in seen_contents:
                fused.append(doc)
                seen_contents.add(content_hash)
        
        self.logger.info(f"Fused {len(kb_docs)} KB docs + {len(web_docs)} web docs = {len(fused)} total")
        
        return fused
    
    async def _generate_corrective_answer(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        sources_used: List[str],
        quality_assessment: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate the final answer with corrective context."""
        if not documents:
            return "I apologize, but I couldn't find sufficient information to answer your question."
        
        # Prepare context
        context_parts = []
        for i, doc in enumerate(documents):
            source_label = doc.get("source", "unknown")
            url = doc.get("metadata", {}).get("url", "")
            url_info = f" ({url})" if url else ""
            
            context_parts.append(
                f"[{source_label.upper()}{url_info}]\n{doc['content'][:600]}..."
            )
        
        combined_context = "\n\n".join(context_parts)
        
        sources_note = (
            f"\n\nNote: This answer is based on information from {', '.join(sources_used)}. "
            if "web_search" in sources_used else ""
        )
        
        prompt = (
            f"You are an expert assistant. Answer the following question based on the provided documents. "
            f"The documents come from multiple sources and have been vetted for quality.\n\n"
            f"Question: {query}\n\n"
            f"Sources: {', '.join(sources_used)}\n"
            f"Retrieval Quality: {quality_assessment['quality'].value} (score: {quality_assessment['score']:.2f})\n\n"
            f"Documents:\n{combined_context}\n\n"
            f"Provide a comprehensive answer. Cite sources when appropriate.{sources_note}"
        )
        
        answer = await self._call_llm_gateway(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return answer.strip()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_pattern_info(self) -> Dict[str, Any]:
        """Returns metadata about the Corrective RAG pattern."""
        return {
            "name": "Corrective RAG (CRAG)",
            "description": "Self-correcting retrieval with quality assessment and web search fallback.",
            "category": "Advanced RAG",
            "latency_impact": "Medium-High (20-60s, depending on fallback)",
            "complexity": "High",
            "use_cases": [
                "Critical applications requiring reliable answers",
                "Questions that may not be in knowledge base",
                "Fact-checking and verification",
                "Time-sensitive information needs",
                "Hybrid knowledge base + web scenarios"
            ],
            "pros": [
                "Self-correcting and robust",
                "Handles knowledge base gaps",
                "Quality assessment built-in",
                "Multi-source information fusion",
                "Graceful degradation"
            ],
            "cons": [
                "Increased latency (evaluation + potential fallback)",
                "Requires web search API integration",
                "More complex error handling",
                "Higher API costs",
                "Quality assessment may be imperfect"
            ],
            "parameters": {
                "model": "LLM model to use (default: ollama)",
                "collection": "Vector store collection name",
                "top_k": "Number of documents to retrieve (default: 5)",
                "quality_threshold": "Minimum quality score 0-1 (default: 0.6)",
                "enable_web_fallback": "Whether to use web search (default: True)",
                "temperature": "Sampling temperature for LLM (default: 0.7)"
            },
            "when_to_use": {
                "ideal_for": [
                    "Mission-critical queries",
                    "Incomplete knowledge bases",
                    "Real-world fact checking",
                    "Current events and news",
                    "Production systems requiring reliability"
                ],
                "avoid_for": [
                    "Latency-sensitive applications",
                    "Private/confidential queries (web leakage)",
                    "Complete knowledge bases",
                    "Cost-constrained scenarios"
                ]
            }
        }
