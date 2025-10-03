"""
Historical Context Workflow - Phase 2 Day 3
Part of Enhanced Roadmap v2.0 - Workflow B: Historical Context Retrieval

This workflow retrieves and aggregates historical context from multiple sources:
- Memory Agent (recent context)
- Doc Store (historical documents)
- Source Agent (Jira/Confluence)
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import httpx


@dataclass
class ContextSource:
    """Represents a source of historical context."""
    source_type: str  # memory, document, jira, confluence
    source_id: str
    content: str
    relevance_score: float  # 0.0 - 1.0
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HistoricalContext:
    """Complete historical context result from Workflow B."""
    workflow_id: str
    query_context: Dict[str, Any]
    sources: List[ContextSource]
    total_sources: int
    unique_source_types: int
    average_relevance: float
    memory_context: List[ContextSource]
    document_context: List[ContextSource]
    jira_context: List[ContextSource]
    confluence_context: List[ContextSource]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def top_sources(self, limit: int = 5) -> List[ContextSource]:
        """Get top N most relevant sources."""
        return sorted(self.sources, key=lambda s: s.relevance_score, reverse=True)[:limit]


class HistoricalContextWorkflow:
    """
    Workflow B: Historical Context Retrieval
    
    Retrieves and aggregates historical context from multiple sources:
    - Memory Agent: Recent workflow context and artifacts
    - Doc Store: Historical documents and analysis reports
    - Source Agent: Jira tickets and Confluence pages
    
    Features:
    - Multi-source integration
    - Relevance scoring
    - Deduplication
    - Ranking and filtering
    
    Part of Enhanced Roadmap v2.0 Phase 2 implementation.
    """
    
    def __init__(
        self,
        memory_agent_url: str = "http://memory-agent:5090",
        doc_store_url: str = "http://doc-store:5140",
        source_agent_url: str = "http://source-agent:8001",
        workflow_logger = None,
        relevance_threshold: float = 0.3  # Minimum relevance to include
    ):
        """
        Initialize Workflow B with service URLs.
        
        Args:
            memory_agent_url: URL for Memory Agent service
            doc_store_url: URL for Doc Store service
            source_agent_url: URL for Source Agent service
            workflow_logger: WorkflowLogger instance for logging
            relevance_threshold: Minimum relevance score to include (0.0-1.0)
        """
        self.memory_agent_url = memory_agent_url
        self.doc_store_url = doc_store_url
        self.source_agent_url = source_agent_url
        self.workflow_logger = workflow_logger
        self.relevance_threshold = relevance_threshold
        self.timeout = 30.0
        
    async def execute(
        self,
        query_context: Dict[str, Any],
        parent_workflow_id: Optional[str] = None,
        max_sources: int = 50
    ) -> HistoricalContext:
        """
        Execute Workflow B: Historical Context Retrieval.
        
        Args:
            query_context: Context about the query (feature_type, platform, etc.)
            parent_workflow_id: Parent workflow ID for tracing
            max_sources: Maximum number of sources to retrieve
            
        Returns:
            HistoricalContext with aggregated multi-source context
        """
        # Generate workflow ID
        workflow_id = f"workflow_b_{str(uuid.uuid4())[:8]}"
        
        # Log workflow start
        if self.workflow_logger:
            await self.workflow_logger.log_workflow_start(
                workflow_id=workflow_id,
                operation="historical_context_workflow_b",
                context={
                    "query_context": query_context,
                    "parent_workflow": parent_workflow_id,
                    "max_sources": max_sources
                }
            )
        
        try:
            # Step 1: Retrieve from Memory Agent (recent context)
            memory_sources = await self._retrieve_from_memory_agent(
                query_context=query_context,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="memory_agent_retrieval",
                    step_data={
                        "sources_retrieved": len(memory_sources),
                        "source_type": "memory"
                    }
                )
            
            # Step 2: Retrieve from Doc Store (historical documents)
            document_sources = await self._retrieve_from_doc_store(
                query_context=query_context,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="doc_store_retrieval",
                    step_data={
                        "sources_retrieved": len(document_sources),
                        "source_type": "documents"
                    }
                )
            
            # Step 3: Retrieve from Source Agent (Jira)
            jira_sources = await self._retrieve_from_jira(
                query_context=query_context,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="jira_retrieval",
                    step_data={
                        "sources_retrieved": len(jira_sources),
                        "source_type": "jira"
                    }
                )
            
            # Step 4: Retrieve from Source Agent (Confluence)
            confluence_sources = await self._retrieve_from_confluence(
                query_context=query_context,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="confluence_retrieval",
                    step_data={
                        "sources_retrieved": len(confluence_sources),
                        "source_type": "confluence"
                    }
                )
            
            # Step 5: Aggregate all sources
            all_sources = memory_sources + document_sources + jira_sources + confluence_sources
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="sources_aggregated",
                    step_data={
                        "total_sources": len(all_sources),
                        "memory": len(memory_sources),
                        "documents": len(document_sources),
                        "jira": len(jira_sources),
                        "confluence": len(confluence_sources)
                    }
                )
            
            # Step 6: Deduplicate sources
            deduplicated_sources = self._deduplicate_sources(all_sources)
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="deduplication_complete",
                    step_data={
                        "original_count": len(all_sources),
                        "deduplicated_count": len(deduplicated_sources),
                        "duplicates_removed": len(all_sources) - len(deduplicated_sources)
                    }
                )
            
            # Step 7: Filter by relevance and rank
            filtered_sources = self._filter_and_rank(
                sources=deduplicated_sources,
                max_sources=max_sources
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="filtering_and_ranking_complete",
                    step_data={
                        "input_count": len(deduplicated_sources),
                        "output_count": len(filtered_sources),
                        "filtered_out": len(deduplicated_sources) - len(filtered_sources)
                    }
                )
            
            # Step 8: Create result
            result = HistoricalContext(
                workflow_id=workflow_id,
                query_context=query_context,
                sources=filtered_sources,
                total_sources=len(filtered_sources),
                unique_source_types=len(set(s.source_type for s in filtered_sources)),
                average_relevance=sum(s.relevance_score for s in filtered_sources) / len(filtered_sources) if filtered_sources else 0.0,
                memory_context=[s for s in filtered_sources if s.source_type == "memory"],
                document_context=[s for s in filtered_sources if s.source_type == "document"],
                jira_context=[s for s in filtered_sources if s.source_type == "jira"],
                confluence_context=[s for s in filtered_sources if s.source_type == "confluence"]
            )
            
            # Log workflow completion
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_complete(
                    workflow_id=workflow_id,
                    duration_ms=0,  # Calculate if needed
                    success=True,
                    result_summary={
                        "total_sources": result.total_sources,
                        "unique_types": result.unique_source_types,
                        "average_relevance": result.average_relevance,
                        "memory_sources": len(result.memory_context),
                        "document_sources": len(result.document_context),
                        "jira_sources": len(result.jira_context),
                        "confluence_sources": len(result.confluence_context)
                    }
                )
            
            return result
            
        except Exception as e:
            # Log error
            if self.workflow_logger:
                await self.workflow_logger.log_error(
                    workflow_id=workflow_id,
                    error=e,
                    context={"stage": "historical_context_workflow_b"}
                )
            raise
    
    async def _retrieve_from_memory_agent(
        self,
        query_context: Dict[str, Any],
        workflow_id: str
    ) -> List[ContextSource]:
        """Retrieve recent context from Memory Agent."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Build search query from context
                search_terms = self._extract_search_terms(query_context)
                
                # Search Memory Agent
                response = await client.post(
                    f"{self.memory_agent_url}/api/v1/context/search",
                    json={
                        "query": " ".join(search_terms),
                        "limit": 10,
                        "include_artifacts": True
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    # Convert to ContextSource objects
                    sources = []
                    for result in results:
                        sources.append(ContextSource(
                            source_type="memory",
                            source_id=result.get("context_id", str(uuid.uuid4())),
                            content=json.dumps(result.get("data", {})),
                            relevance_score=result.get("score", 0.5),
                            timestamp=datetime.fromisoformat(result.get("timestamp", datetime.utcnow().isoformat())),
                            metadata=result.get("metadata", {})
                        ))
                    
                    return sources
                else:
                    return []
                    
        except Exception as e:
            # Return empty list on error
            return []
    
    async def _retrieve_from_doc_store(
        self,
        query_context: Dict[str, Any],
        workflow_id: str
    ) -> List[ContextSource]:
        """Retrieve historical documents from Doc Store."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Build search query
                search_terms = self._extract_search_terms(query_context)
                
                # Search Doc Store
                response = await client.post(
                    f"{self.doc_store_url}/api/v1/documents/search",
                    json={
                        "query": " ".join(search_terms),
                        "limit": 15,
                        "include_content": True
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    documents = data.get("documents", [])
                    
                    # Convert to ContextSource objects
                    sources = []
                    for doc in documents:
                        # Calculate relevance based on search score
                        relevance = self._calculate_document_relevance(
                            doc, query_context
                        )
                        
                        sources.append(ContextSource(
                            source_type="document",
                            source_id=doc.get("document_id", str(uuid.uuid4())),
                            content=doc.get("content", "")[:1000],  # Limit content
                            relevance_score=relevance,
                            timestamp=datetime.fromisoformat(doc.get("created_at", datetime.utcnow().isoformat())),
                            metadata={
                                "title": doc.get("title", ""),
                                "type": doc.get("document_type", ""),
                                "tags": doc.get("tags", [])
                            }
                        ))
                    
                    return sources
                else:
                    return []
                    
        except Exception as e:
            return []
    
    async def _retrieve_from_jira(
        self,
        query_context: Dict[str, Any],
        workflow_id: str
    ) -> List[ContextSource]:
        """Retrieve Jira tickets via Source Agent."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Build Jira search query
                feature_type = query_context.get("feature_type", "")
                platform = query_context.get("platform", "")
                
                jql_query = f"text ~ \"{feature_type}\" AND text ~ \"{platform}\""
                
                # Search via Source Agent
                response = await client.post(
                    f"{self.source_agent_url}/api/v1/jira/search",
                    json={
                        "jql": jql_query,
                        "max_results": 10,
                        "fields": ["summary", "description", "status", "created"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get("issues", [])
                    
                    # Convert to ContextSource objects
                    sources = []
                    for issue in issues:
                        fields = issue.get("fields", {})
                        
                        # Calculate relevance
                        relevance = self._calculate_jira_relevance(
                            issue, query_context
                        )
                        
                        sources.append(ContextSource(
                            source_type="jira",
                            source_id=issue.get("key", str(uuid.uuid4())),
                            content=f"{fields.get('summary', '')}\n{fields.get('description', '')}"[:1000],
                            relevance_score=relevance,
                            timestamp=datetime.fromisoformat(fields.get("created", datetime.utcnow().isoformat())),
                            metadata={
                                "key": issue.get("key"),
                                "status": fields.get("status", {}).get("name"),
                                "type": fields.get("issuetype", {}).get("name")
                            }
                        ))
                    
                    return sources
                else:
                    return []
                    
        except Exception as e:
            return []
    
    async def _retrieve_from_confluence(
        self,
        query_context: Dict[str, Any],
        workflow_id: str
    ) -> List[ContextSource]:
        """Retrieve Confluence pages via Source Agent."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Build Confluence search query
                search_terms = self._extract_search_terms(query_context)
                
                # Search via Source Agent
                response = await client.post(
                    f"{self.source_agent_url}/api/v1/confluence/search",
                    json={
                        "cql": f"text ~ \"{' '.join(search_terms)}\"",
                        "limit": 10
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pages = data.get("results", [])
                    
                    # Convert to ContextSource objects
                    sources = []
                    for page in pages:
                        # Calculate relevance
                        relevance = self._calculate_confluence_relevance(
                            page, query_context
                        )
                        
                        sources.append(ContextSource(
                            source_type="confluence",
                            source_id=page.get("id", str(uuid.uuid4())),
                            content=page.get("excerpt", page.get("body", ""))[:1000],
                            relevance_score=relevance,
                            timestamp=datetime.fromisoformat(page.get("lastModified", datetime.utcnow().isoformat())),
                            metadata={
                                "title": page.get("title"),
                                "space": page.get("space", {}).get("key"),
                                "url": page.get("_links", {}).get("webui")
                            }
                        ))
                    
                    return sources
                else:
                    return []
                    
        except Exception as e:
            return []
    
    def _extract_search_terms(self, query_context: Dict[str, Any]) -> List[str]:
        """Extract relevant search terms from query context."""
        terms = []
        
        if "feature_type" in query_context:
            terms.append(query_context["feature_type"])
        
        if "platform" in query_context:
            terms.append(query_context["platform"])
        
        if "feature_title" in query_context:
            terms.extend(query_context["feature_title"].split())
        
        if "feature_description" in query_context:
            # Extract key words from description
            words = query_context["feature_description"].split()
            # Take first 5 meaningful words (> 3 chars)
            meaningful_words = [w for w in words if len(w) > 3][:5]
            terms.extend(meaningful_words)
        
        return list(set(terms))  # Deduplicate
    
    def _calculate_document_relevance(
        self,
        document: Dict[str, Any],
        query_context: Dict[str, Any]
    ) -> float:
        """Calculate relevance score for a document."""
        score = 0.5  # Base score
        
        # Boost for matching feature type
        if query_context.get("feature_type") in document.get("content", "").lower():
            score += 0.2
        
        # Boost for matching platform
        if query_context.get("platform") in document.get("content", "").lower():
            score += 0.15
        
        # Boost for recent documents
        created_at = datetime.fromisoformat(document.get("created_at", datetime.utcnow().isoformat()))
        days_old = (datetime.utcnow() - created_at).days
        if days_old < 30:
            score += 0.15
        elif days_old < 90:
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_jira_relevance(
        self,
        issue: Dict[str, Any],
        query_context: Dict[str, Any]
    ) -> float:
        """Calculate relevance score for a Jira issue."""
        score = 0.5  # Base score
        
        fields = issue.get("fields", {})
        content = f"{fields.get('summary', '')} {fields.get('description', '')}".lower()
        
        # Boost for matching feature type
        if query_context.get("feature_type") in content:
            score += 0.25
        
        # Boost for matching platform
        if query_context.get("platform") in content:
            score += 0.15
        
        # Boost for similar issues (same type)
        if fields.get("issuetype", {}).get("name") in ["Story", "Epic"]:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_confluence_relevance(
        self,
        page: Dict[str, Any],
        query_context: Dict[str, Any]
    ) -> float:
        """Calculate relevance score for a Confluence page."""
        score = 0.5  # Base score
        
        content = f"{page.get('title', '')} {page.get('excerpt', '')}".lower()
        
        # Boost for matching feature type
        if query_context.get("feature_type") in content:
            score += 0.2
        
        # Boost for matching platform
        if query_context.get("platform") in content:
            score += 0.15
        
        # Boost for documentation pages
        if "documentation" in content or "guide" in content:
            score += 0.15
        
        return min(score, 1.0)
    
    def _deduplicate_sources(self, sources: List[ContextSource]) -> List[ContextSource]:
        """Remove duplicate sources based on content similarity."""
        if not sources:
            return []
        
        deduplicated = []
        seen_contents = set()
        
        for source in sources:
            # Create a hash of the first 200 chars for deduplication
            content_hash = hash(source.content[:200].lower().strip())
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                deduplicated.append(source)
        
        return deduplicated
    
    def _filter_and_rank(
        self,
        sources: List[ContextSource],
        max_sources: int
    ) -> List[ContextSource]:
        """Filter by relevance threshold and rank by score."""
        # Filter by threshold
        filtered = [s for s in sources if s.relevance_score >= self.relevance_threshold]
        
        # Sort by relevance (descending)
        ranked = sorted(filtered, key=lambda s: s.relevance_score, reverse=True)
        
        # Limit to max_sources
        return ranked[:max_sources]

