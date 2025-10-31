    async def query_with_context(
        self,
        query: str,
        repo_id: Optional[str] = None,
        context_id: Optional[str] = None,
        context_level: Optional[ContextLevel] = None,
        service_filter: Optional[str] = None,
        tech_filter: Optional[List[str]] = None,
        language_filter: Optional[str] = None,
        time_range: Optional[timedelta] = None,
        limit: int = 10,
        generate_answer: bool = True  # ✨ PHASE 5: NEW parameter for LLM answer
    ) -> Dict[str, Any]:
        """
        Query with context filtering and LLM answer generation.
        
        PHASE 5: Enhanced with EnhancementPipeline for better retrieval and answers.
        
        Args:
            query: Query text
            repo_id: Optional repository filter
            context_id: Optional hierarchical context ID
            context_level: Optional context level filter
            service_filter: Optional service name filter
            tech_filter: Optional technology stack filter
            language_filter: Optional programming language filter
            time_range: Optional time range for documents
            limit: Max results
            generate_answer: Whether to generate LLM answer (Phase 5 feature)
        
        Returns:
            Query results with context metadata and optional LLM answer
        """
        logger.info(f"🔍 Context-aware RAG query (Phase 5): {query[:100]}")
        logger.debug(f"   Enhancements: {self.use_enhancements}")
        logger.debug(f"   Generate answer: {generate_answer}")
        
        # Get hierarchical context if specified
        context = None
        if context_id:
            context = await self.context_manager.get_context(context_id)
            logger.info(f"   📍 Using context: {context.name if context else 'NOT FOUND'}")
        
        # Build context-aware where clause
        where_clause = self._build_where_clause(
            repo_id=repo_id,
            context=context,
            context_level=context_level,
            service_filter=service_filter,
            tech_filter=tech_filter,
            language_filter=language_filter,
            time_range=time_range
        )
        
        if where_clause:
            logger.info(f"   🎯 Filters: {list(where_clause.keys())}")
        
        # ===== USE ENHANCEMENT PIPELINE (if available) =====
        if self.use_enhancements and self.enhancement_pipeline and generate_answer:
            logger.info(f"✨ Using EnhancementPipeline with context filtering")
            
            # Use context_aware_default preset
            config = EnhancementConfig.context_aware_default()
            
            # Create pre-retrieval filter hook for context filtering
            async def context_filter(ctx):
                """Return context where clause for filtering."""
                return where_clause if where_clause else {}
            
            hooks = EnhancementHooks(
                pre_retrieval_filter=context_filter
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
                
                logger.info(
                    f"✅ Pipeline retrieved {len(documents)} documents"
                )
                
                if not documents:
                    return {
                        "query": query,
                        "answer": "No documents found matching the specified context filters.",
                        "sources": [],
                        "filters": self._format_filters(repo_id, context_id, context_level, service_filter, tech_filter, language_filter, time_range),
                        "context_info": self._format_context_info(context),
                        "metadata": {
                            "filters_applied": where_clause is not None,
                            "context_used": context is not None,
                            "enhancement_mode": "pipeline_v1",
                            "documents_found": 0
                        }
                    }
                
                # Generate context-aware answer
                answer = await self._generate_answer(documents, query, context, repo_id, service_filter)
                
                # Format sources
                sources = self._format_sources(documents)
                
                return {
                    "query": query,
                    "answer": answer,
                    "sources": sources,
                    "filters": self._format_filters(repo_id, context_id, context_level, service_filter, tech_filter, language_filter, time_range),
                    "context_info": self._format_context_info(context),
                    "total": len(sources),
                    "metadata": {
                        "filters_applied": where_clause is not None,
                        "context_used": context is not None,
                        "enhancement_mode": "pipeline_v1",
                        "enhancements_used": {
                            "hybrid_search": config.enable_hybrid_search,
                            "query_rewriting": config.enable_query_rewriting,
                            "context_optimization": config.enable_context_optimization
                        },
                        "documents_found": len(sources)
                    }
                }
                
            except Exception as pipeline_error:
                logger.error(
                    f"⚠️  Pipeline failed: {pipeline_error}. Falling back to legacy.",
                    exc_info=True
                )
                # Fall through to legacy mode
        
        # ===== LEGACY MODE (no enhancements or no answer generation) =====
        logger.info(f"📋 Using legacy context-aware query")
        
        # Generate query embedding
        embedding_result = await self.embedding_service.generate_embedding(query)
        query_embedding = embedding_result["embedding"] if isinstance(embedding_result, dict) else embedding_result
        
        # Query ChromaDB with context filters
        try:
            results = await self.chromadb.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None
            )
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB query with filters failed, retrying without filters: {e}")
            # Fallback: query without filters
            results = await self.chromadb.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
        
        # Enhance results with context info
        enhanced_results = await self._enhance_with_context(results, context)
        
        # Calculate relevance scores
        scored_results = self._calculate_relevance_scores(enhanced_results, query)
        
        # Generate answer if requested (legacy mode)
        answer = None
        if generate_answer and scored_results:
            try:
                # Extract documents for answer generation
                docs_for_answer = [
                    {
                        "content": r.get("content", r.get("document", "")),
                        "file_path": r.get("file_path", "Unknown"),
                        "metadata": r.get("metadata", {})
                    }
                    for r in scored_results
                ]
                answer = await self._generate_answer(docs_for_answer, query, context, repo_id, service_filter)
            except Exception as e:
                logger.error(f"Failed to generate answer: {e}")
                answer = None
        
        return {
            "query": query,
            "answer": answer,  # May be None if not generated
            "filters": self._format_filters(repo_id, context_id, context_level, service_filter, tech_filter, language_filter, time_range),
            "context_info": self._format_context_info(context),
            "results": scored_results,
            "total": len(scored_results),
            "metadata": {
                "filters_applied": where_clause is not None,
                "context_used": context is not None,
                "enhancement_mode": "legacy",
                "answer_generated": answer is not None
            }
        }
    
    def _format_filters(self, repo_id, context_id, context_level, service_filter, tech_filter, language_filter, time_range):
        """Format filters for response."""
        return {
            "repo_id": repo_id,
            "context_id": context_id,
            "context_level": context_level.name if context_level else None,
            "service": service_filter,
            "tech_stack": tech_filter,
            "language": language_filter,
            "time_range_hours": time_range.total_seconds() / 3600 if time_range else None
        }
    
    def _format_context_info(self, context):
        """Format context info for response."""
        if not context:
            return None
        
        return {
            "name": context.name,
            "level": context.level.name,
            "full_path": context.full_path,
            "file_count": context.level_files
        }
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format documents as sources."""
        sources = []
        for i, doc in enumerate(documents, 1):
            sources.append({
                "id": i,
                "file_path": doc.get("file_path", "Unknown"),
                "relevance_score": doc.get("adjusted_score", doc.get("relevance_score", 0)),
                "content_snippet": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                "metadata": doc.get("metadata", {})
            })
        return sources
    
    async def _generate_answer(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        context: Optional[HierarchicalContext],
        repo_id: Optional[str],
        service_filter: Optional[str]
    ) -> str:
        """
        Generate LLM answer from context-filtered documents.
        
        ✨ PHASE 5: NEW METHOD - adds LLM answer generation to Context-Aware RAG.
        
        Args:
            documents: Retrieved documents
            query: User's query
            context: Hierarchical context (if any)
            repo_id: Repository filter (if any)
            service_filter: Service filter (if any)
        
        Returns:
            Generated answer string
        """
        if not documents:
            return "No documents found matching the specified context filters."
        
        # Build context text from documents
        context_parts = []
        for i, doc in enumerate(documents, 1):
            file_path = doc.get("file_path", "Unknown")
            content = doc.get("content", doc.get("content_snippet", ""))
            relevance = doc.get("adjusted_score", doc.get("relevance_score", 0))
            
            context_parts.append(
                f"[Source {i}] {file_path} (relevance: {relevance:.3f})\n"
                f"{content}\n"
            )
        
        context_text = "\n---\n\n".join(context_parts)
        
        # Build context-aware prompt
        context_description = ""
        if context:
            context_description = f"\n**Context:** You are answering about {context.full_path} ({context.level.name} level)."
        elif repo_id:
            context_description = f"\n**Context:** You are answering about repository '{repo_id}'."
        elif service_filter:
            context_description = f"\n**Context:** You are answering about service '{service_filter}'."
        
        prompt = f"""You are an intelligent assistant analyzing code documentation.
{context_description}

**Important:** Only use information from the provided sources. If the sources don't contain enough information to answer the question, say so.

**Sources from filtered context:**
{context_text}

**Question:** {query}

**Instructions:**
- Answer the question using ONLY the information from the provided sources
- Provide a detailed, comprehensive answer (3-5 paragraphs minimum)
- Include specific details, examples, and context from the sources
- If listing items, provide descriptions and explanations for each
- Reference which sources support your answer
- Keep in mind the context filters that were applied

**Answer:**"""
        
        # Generate answer using Ollama router
        # Import here to avoid circular dependencies
        from ..models.ollama_router import get_ollama_router
        ollama_router = get_ollama_router()
        
        logger.info(f"🤖 Generating context-aware answer from {len(documents)} documents")
        response = await ollama_router.generate(
            prompt=prompt,
            workload_type='rag',
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.get("response", "").strip()
        
        if not answer:
            answer = f"Found {len(documents)} documents but failed to generate detailed answer."
        
        logger.info(f"✅ Answer generated: {len(answer)} characters")
        
        return answer

