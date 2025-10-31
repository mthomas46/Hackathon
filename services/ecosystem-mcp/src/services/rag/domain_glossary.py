"""
Domain Glossary for MCP (Model Context Protocol)

Provides domain-specific term expansions and synonyms for query rewriting.

PHASE 6R: Added for improved query expansion (+2-3% accuracy)
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class DomainGlossary:
    """
    Domain-specific glossary for MCP ecosystem.
    
    Features:
    - Technical term synonyms
    - Acronym expansions
    - Related concepts
    - Component mappings
    
    Philosophy:
    - Keep it focused (MCP domain only)
    - Frequently updated based on usage
    - Balance precision vs coverage
    
    PHASE 6R: Improves query expansion beyond generic WordNet
    """
    
    def __init__(self):
        """Initialize domain glossary with MCP-specific terms."""
        
        # === Core MCP Concepts ===
        self.glossary: Dict[str, List[str]] = {
            # MCP Core
            "mcp": ["model context protocol", "context protocol", "mcp protocol"],
            "model context protocol": ["mcp", "context protocol"],
            
            # Architecture Components
            "server": ["mcp server", "service", "backend", "api"],
            "client": ["mcp client", "frontend", "consumer"],
            "resource": ["mcp resource", "asset", "file", "document"],
            "tool": ["mcp tool", "function", "capability", "method"],
            "prompt": ["mcp prompt", "template", "query template"],
            
            # Vector/Embedding Terms
            "embedding": ["vector", "embedding vector", "semantic vector", "text embedding"],
            "vector": ["embedding", "embedding vector", "semantic representation"],
            "chromadb": ["chroma", "vector database", "vector db", "embedding store"],
            "chroma": ["chromadb", "vector database"],
            
            # Search & Retrieval
            "semantic search": ["vector search", "similarity search", "embedding search"],
            "keyword search": ["bm25", "lexical search", "text search", "full-text search"],
            "hybrid search": ["combined search", "semantic + keyword", "multi-modal search"],
            "bm25": ["keyword search", "okapi bm25", "best match 25", "ranking algorithm"],
            "rag": ["retrieval augmented generation", "retrieval-augmented generation"],
            "retrieval": ["search", "lookup", "query", "fetch"],
            
            # Document Processing
            "ingestion": ["document ingestion", "data ingestion", "indexing", "processing"],
            "normalization": ["text normalization", "preprocessing", "cleaning"],
            "chunking": ["splitting", "segmentation", "partitioning"],
            "tokenization": ["tokenizing", "word splitting", "text parsing"],
            
            # Quality & Scoring
            "quality score": ["document quality", "content score", "quality metric"],
            "confidence": ["confidence score", "certainty", "reliability"],
            "relevance": ["relevance score", "similarity", "match quality"],
            "reranking": ["re-ranking", "reorder", "rescoring"],
            
            # Infrastructure
            "redis": ["redis cache", "caching layer", "in-memory store"],
            "postgres": ["postgresql", "database", "relational db", "sql database"],
            "docker": ["container", "containerization", "docker compose"],
            "ollama": ["llm router", "language model", "model server"],
            
            # Operations
            "deploy": ["deployment", "release", "ship", "publish"],
            "monitor": ["monitoring", "observability", "logging", "tracking"],
            "optimize": ["optimization", "performance tuning", "improve"],
            "debug": ["debugging", "troubleshoot", "diagnose", "fix"],
            
            # API & Integration
            "api": ["rest api", "endpoint", "interface", "service"],
            "endpoint": ["api endpoint", "route", "url", "path"],
            "webhook": ["callback", "notification", "event handler"],
            
            # Error Handling
            "error": ["exception", "failure", "issue", "problem"],
            "timeout": ["time out", "timeout error", "request timeout"],
            "retry": ["retry logic", "retry attempt", "backoff"],
            
            # Performance
            "latency": ["response time", "delay", "speed"],
            "throughput": ["requests per second", "rps", "capacity"],
            "cache": ["caching", "cached", "cache layer"],
            "bottleneck": ["performance issue", "slow point", "constraint"],
            
            # Data & Schema
            "schema": ["database schema", "data model", "structure"],
            "migration": ["database migration", "schema migration", "upgrade"],
            "model": ["data model", "schema", "entity"],
            
            # Testing
            "test": ["testing", "unit test", "integration test", "e2e test"],
            "benchmark": ["benchmarking", "performance test", "load test"],
            "validation": ["validate", "verify", "check"],
        }
        
        logger.info(f"DomainGlossary initialized with {len(self.glossary)} terms")
    
    def expand_term(self, term: str, max_expansions: int = 3) -> List[str]:
        """
        Expand a term with domain-specific synonyms.
        
        Args:
            term: Term to expand (case-insensitive)
            max_expansions: Maximum number of expansions to return
        
        Returns:
            List of synonyms/related terms (empty if not found)
        
        Performance: O(1) lookup, < 0.1ms
        """
        term_lower = term.lower().strip()
        
        # Direct lookup
        expansions = self.glossary.get(term_lower, [])
        
        if expansions:
            logger.debug(f"   🔍 Domain expansion: '{term}' → {expansions[:max_expansions]}")
            return expansions[:max_expansions]
        
        return []
    
    def has_term(self, term: str) -> bool:
        """
        Check if term exists in glossary.
        
        Args:
            term: Term to check
        
        Returns:
            True if term is in glossary
        """
        return term.lower().strip() in self.glossary
    
    def get_all_terms(self) -> List[str]:
        """
        Get all terms in glossary.
        
        Returns:
            List of all glossary terms
        """
        return list(self.glossary.keys())
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get glossary statistics.
        
        Returns:
            Dict with term counts
        """
        total_expansions = sum(len(v) for v in self.glossary.values())
        return {
            "total_terms": len(self.glossary),
            "total_expansions": total_expansions,
            "avg_expansions_per_term": total_expansions / len(self.glossary) if self.glossary else 0
        }


# Singleton instance
_glossary_instance = None


def get_domain_glossary() -> DomainGlossary:
    """Get or create singleton domain glossary."""
    global _glossary_instance
    if _glossary_instance is None:
        _glossary_instance = DomainGlossary()
    return _glossary_instance

