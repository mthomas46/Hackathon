    async def _query_with_temporal_filter(
        self,
        query: str,
        as_of_date: datetime,
        service_name: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query documents using temporal filtering with EnhancementPipeline.
        
        PHASE 4: Refactored to use Enhancement Pipeline for better retrieval.
        - Temporal filtering via pre-retrieval hook
        - Hybrid search (semantic + BM25)
        - Query rewriting for better understanding
        - Context optimization for relevance
        
        Args:
            query: Question to answer
            as_of_date: Point in time to query
            service_name: Optional service filter
            limit: Maximum results
        
        Returns:
            Query results with temporal context and enhancements
        """
        try:
            self.logger.info(f"🔍 [TEMPORAL_RAG] Starting temporal query (Phase 4)")
            self.logger.debug(f"   Query: {query[:100]}")
            self.logger.debug(f"   As of date: {as_of_date}")
            self.logger.debug(f"   Service name: {service_name}")
            self.logger.debug(f"   Limit: {limit}")
            self.logger.debug(f"   Enhancements: {self.use_enhancements}")
            
            # ===== BUILD TEMPORAL FILTER =====
            self.logger.debug(f"🔍 [TEMPORAL_RAG] Building temporal where clause")
            
            conditions = []
            
            # Always filter by git_date
            as_of_timestamp = as_of_date.timestamp()
            git_date_condition = {"git_date": {"$lte": as_of_timestamp}}
            conditions.append(git_date_condition)
            self.logger.debug(f"   Adding git_date filter: <= {as_of_date.date()} (timestamp: {as_of_timestamp})")
            
            # Optionally filter by service_name
            if service_name:
                service_condition = {"service_name": service_name}
                conditions.append(service_condition)
                self.logger.debug(f"   Adding service_name filter: {service_name}")
            
            # Build final where clause
            if len(conditions) == 1:
                where_clause = conditions[0]
            else:
                where_clause = {"$and": conditions}
            
            self.logger.info(
                f"✅ [TEMPORAL_RAG] Temporal filter built with {len(conditions)} condition(s)"
            )
            
            # ===== USE ENHANCEMENT PIPELINE (if available) =====
            if self.use_enhancements and self.enhancement_pipeline:
                self.logger.info(f"✨ [TEMPORAL_RAG] Using EnhancementPipeline")
                
                # Use temporal_default preset (optimized for temporal queries)
                config = EnhancementConfig.temporal_default()
                
                # Create pre-retrieval filter hook for temporal filtering
                hooks = EnhancementHooks(
                    pre_retrieval_filter=lambda ctx: where_clause
                )
                
                # Execute pipeline
                try:
                    result = await self.enhancement_pipeline.execute(
                        query=query,
                        n_results=limit,
                        config=config,
                        hooks=hooks
                    )
                    
                    # Extract enhanced documents
                    documents = result.get("documents", [])
                    
                    self.logger.info(
                        f"✅ [TEMPORAL_RAG] Pipeline retrieved {len(documents)} documents"
                    )
                    
                except Exception as pipeline_error:
                    self.logger.error(
                        f"⚠️  Pipeline failed: {pipeline_error}. Falling back to legacy.",
                        exc_info=True
                    )
                    # Fall through to legacy mode
                    return await self._query_with_temporal_filter_legacy(
                        query, as_of_date, service_name, limit
                    )
            
            else:
                # Legacy mode (no enhancements)
                self.logger.info(f"📋 [TEMPORAL_RAG] Using legacy temporal query")
                return await self._query_with_temporal_filter_legacy(
                    query, as_of_date, service_name, limit
                )
            
            # ===== CHECK RESULTS =====
            if not documents:
                self.logger.warning(f"⚠️  [TEMPORAL_RAG] No documents found matching temporal filter")
                return {
                    "query": query,
                    "as_of_date": as_of_date.isoformat(),
                    "answer": f"No documents found for the specified time period (as of {as_of_date.date()}).",
                    "documents": [],
                    "sources": [],
                    "metadata": {
                        "temporal_filter_applied": True,
                        "filter": where_clause,
                        "documents_found": 0,
                        "query_type": "temporal_rag_enhanced",
                        "as_of_date": as_of_date.isoformat(),
                        "enhancements_used": True
                    }
                }
            
            # ===== GENERATE TEMPORAL-AWARE ANSWER =====
            self.logger.info(f"🤖 [TEMPORAL_RAG] Generating temporal-aware answer")
            
            # Build context from enhanced documents
            context_parts = []
            for i, doc in enumerate(documents, 1):
                file_path = doc.get("file_path", "Unknown")
                content = doc.get("content", doc.get("content_snippet", ""))
                relevance = doc.get("adjusted_score", doc.get("relevance_score", 0))
                
                context_parts.append(
                    f"[Source {i}] {file_path} (relevance: {relevance:.3f})\n"
                    f"{content}\n"
                )
            
            context_text = "\n".join(context_parts)
            
            # Build temporal-aware prompt
            prompt = f"""You are an intelligent assistant analyzing historical documentation.

**Context:** You are answering based on documents that existed as of {as_of_date.date()}.

**Important:** Only use information from the provided sources. If the sources don't contain enough information to answer the question, say so.

**Sources:**
{context_text}

**Question:** {query}

**Instructions:**
- Answer the question using ONLY the information from the provided sources
- Provide a detailed, comprehensive answer (3-5 paragraphs minimum)
- Include specific details, examples, and context from the sources
- If listing items, provide descriptions and explanations for each
- Reference which sources support your answer
- Remember: This is information as of {as_of_date.date()}

**Answer:**"""
            
            # Generate answer using Ollama router
            self.logger.info(f"🤖 [TEMPORAL_RAG] Generating LLM answer from {len(documents)} documents")
            response = await self.ollama_router.generate(
                prompt=prompt,
                workload_type='rag',
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.get("response", "").strip()
            
            if not answer:
                answer = f"Found {len(documents)} documents as of {as_of_date.date()}, but failed to generate detailed answer."
            
            self.logger.info(f"✅ [TEMPORAL_RAG] Answer generated: {len(answer)} characters")
            
            # Format sources for response
            sources = []
            for i, doc in enumerate(documents, 1):
                sources.append({
                    "id": i,
                    "file_path": doc.get("file_path", "Unknown"),
                    "relevance_score": doc.get("adjusted_score", doc.get("relevance_score", 0)),
                    "git_date": doc.get("metadata", {}).get("git_date"),
                    "service_name": doc.get("metadata", {}).get("service_name")
                })
            
            return {
                "query": query,
                "as_of_date": as_of_date.isoformat(),
                "answer": answer,
                "documents": documents,
                "sources": sources,
                "metadata": {
                    "temporal_filter_applied": True,
                    "filter": where_clause,
                    "documents_found": len(documents),
                    "query_type": "temporal_rag_enhanced",
                    "as_of_date": as_of_date.isoformat(),
                    "enhancements_used": True,
                    "config": {
                        "hybrid_search": True,
                        "query_rewriting": True,
                        "context_optimization": True
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Temporal filtering failed: {e}", exc_info=True)
            raise
    
    async def _query_with_temporal_filter_legacy(
        self,
        query: str,
        as_of_date: datetime,
        service_name: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Legacy temporal query without enhancements (fallback).
        
        This is the original implementation, preserved for fallback.
        """
        try:
            from ...storage.chromadb_client import get_chroma_client
            from ...services.embeddings.embedding_service import EmbeddingService
            
            self.logger.info(f"📋 [TEMPORAL_RAG] Legacy temporal query")
            
            chroma = get_chroma_client()
            
            # Build where clause
            conditions = []
            as_of_timestamp = as_of_date.timestamp()
            git_date_condition = {"git_date": {"$lte": as_of_timestamp}}
            conditions.append(git_date_condition)
            
            if service_name:
                service_condition = {"service_name": service_name}
                conditions.append(service_condition)
            
            if len(conditions) == 1:
                where_clause = conditions[0]
            else:
                where_clause = {"$and": conditions}
            
            # Generate embedding
            embedding_service = EmbeddingService()
            embedding_result = await embedding_service.generate_embedding(query)
            query_embedding = embedding_result.get("embedding") if isinstance(embedding_result, dict) else embedding_result
            
            if not query_embedding:
                raise ValueError("Failed to generate query embedding")
            
            # Query ChromaDB
            results = await chroma.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            if not results or not results.get("documents"):
                return {
                    "query": query,
                    "as_of_date": as_of_date.isoformat(),
                    "answer": "No documents found for the specified time period.",
                    "documents": [],
                    "sources": [],
                    "metadata": {
                        "temporal_filter_applied": True,
                        "filter": where_clause,
                        "documents_found": 0,
                        "query_type": "temporal_rag_legacy",
                        "as_of_date": as_of_date.isoformat()
                    }
                }
            
            # Format results
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []
            
            formatted_docs = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                formatted_docs.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": dist,
                    "relevance_score": 1.0 - dist,
                    "file_path": meta.get("file_path", "Unknown")
                })
            
            # Generate answer
            context_parts = []
            for i, doc in enumerate(formatted_docs, 1):
                file_path = doc.get("file_path", "Unknown")
                content = doc.get("content", "")
                relevance = doc.get("relevance_score", 0)
                
                context_parts.append(
                    f"[Source {i}] {file_path} (relevance: {relevance:.3f})\n"
                    f"{content}\n"
                )
            
            context_text = "\n".join(context_parts)
            
            prompt = f"""You are an intelligent assistant analyzing historical documentation.

**Context:** You are answering based on documents that existed as of {as_of_date.date()}.

**Sources:**
{context_text}

**Question:** {query}

**Answer (based on sources above, as of {as_of_date.date()}):"""
            
            response = await self.ollama_router.generate(
                prompt=prompt,
                workload_type='rag',
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.get("response", "").strip()
            
            sources = []
            for i, doc in enumerate(formatted_docs, 1):
                sources.append({
                    "id": i,
                    "file_path": doc.get("file_path", "Unknown"),
                    "relevance_score": doc.get("relevance_score", 0)
                })
            
            return {
                "query": query,
                "as_of_date": as_of_date.isoformat(),
                "answer": answer,
                "documents": formatted_docs,
                "sources": sources,
                "metadata": {
                    "temporal_filter_applied": True,
                    "filter": where_clause,
                    "documents_found": len(formatted_docs),
                    "query_type": "temporal_rag_legacy"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Legacy temporal query failed: {e}", exc_info=True)
            raise

