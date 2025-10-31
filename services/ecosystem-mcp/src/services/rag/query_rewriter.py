"""
Query Rewriting Service

Improves vague/incomplete queries before search.

Techniques:
1. Synonym Expansion: Add related terms
2. Query Clarification: Use LLM to make queries more specific
3. Query Decomposition: Break complex queries into sub-queries

Expected: +20-30% accuracy for vague queries
"""

import logging
from typing import List, Dict, Any, Optional
import re
from nltk.corpus import wordnet
import nltk

from ..models.ollama_router import get_ollama_router
from ...utils.cache_decorator import cache
from .domain_glossary import get_domain_glossary  # ⚡ PHASE 6R

logger = logging.getLogger(__name__)


# Download NLTK data on first import (only if not already downloaded)
try:
    wordnet.ensure_loaded()
except LookupError:
    logger.info("Downloading NLTK wordnet data...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
except Exception:
    pass  # Already downloaded


class QueryRewriter:
    """
    Query rewriting service.
    
    Features:
    - Synonym expansion (WordNet)
    - LLM-based clarification
    - Query decomposition
    - Domain-specific term mapping
    
    PERFORMANCE OPTIMIZED:
    - WordNet synset caching
    - Smart simple query detection
    - Reduced variant generation
    """
    
    def __init__(self):
        """Initialize query rewriter."""
        self.ollama_router = get_ollama_router()
        
        # ⚡ PHASE 6R: Domain glossary for MCP-specific terms
        self.domain_glossary = get_domain_glossary()
        
        # 🚀 OPTIMIZATION: Cache WordNet synsets to avoid repeated lookups
        self._synset_cache = {}
        self._simple_query_cache = set()
        
        # Domain-specific synonym map for technical terms
        # Maps vague terms → specific technical terms
        self.technical_synonyms = {
            # Vague actions
            "start": ["initialize", "begin", "trigger", "launch", "execute"],
            "stop": ["terminate", "halt", "shutdown", "kill"],
            "run": ["execute", "process", "perform", "operate"],
            "fix": ["repair", "resolve", "correct", "debug"],
            "break": ["fail", "crash", "error", "malfunction"],
            
            # System components
            "database": ["db", "postgresql", "postgres", "sql", "storage"],
            "cache": ["redis", "memory", "cached"],
            "queue": ["redis stream", "message queue", "job queue"],
            "api": ["endpoint", "route", "rest api", "http"],
            "worker": ["background job", "celery worker", "task processor"],
            
            # Document processing
            "ingestion": ["document processing", "file indexing", "data ingestion"],
            "embedding": ["vector", "vectorization", "semantic encoding"],
            "search": ["query", "retrieval", "lookup", "find"],
            
            # Quality/status
            "slow": ["performance issue", "latency", "bottleneck"],
            "fast": ["optimized", "performant", "efficient"],
            "broken": ["failing", "erroring", "not working"],
        }
        
        logger.info("QueryRewriter initialized with domain-specific synonyms + caching")
    
    @cache(ttl=3600, key_prefix="query_rewrite")  # ⚡ Cache for 1 hour
    async def rewrite(
        self,
        query: str,
        enable_expansion: bool = True,
        enable_clarification: bool = True,
        enable_decomposition: bool = True
    ) -> Dict[str, Any]:
        """
        Rewrite query to improve search results (CACHED).
        
        Args:
            query: Original query
            enable_expansion: Enable synonym expansion
            enable_clarification: Enable LLM clarification
            enable_decomposition: Enable query decomposition
        
        Returns:
            Dict with:
            - original: Original query
            - expanded: Synonym-expanded query
            - clarified: LLM-clarified query
            - sub_queries: Decomposed sub-queries
            - search_queries: All variants to search with
        """
        logger.info(f"🔄 Rewriting query: '{query[:60]}...'")
        
        result = {
            "original": query,
            "expanded": None,
            "clarified": None,
            "sub_queries": [],
            "search_queries": [query]  # Always include original
        }
        
        try:
            # 🚀 OPTIMIZATION: Skip expensive operations for simple/direct queries
            is_simple = self._is_simple_query(query)
            if is_simple:
                logger.info("   ⚡ Simple query detected - skipping expensive rewriting")
                return result
            
            # 1. Synonym Expansion
            if enable_expansion:
                expanded = self._expand_with_synonyms(query)
                if expanded != query:
                    result["expanded"] = expanded
                    result["search_queries"].append(expanded)
            
            # 2. LLM Clarification (skip for short queries)
            if enable_clarification and len(query.split()) > 4:
                clarified = await self._clarify_with_llm(query)
                if clarified and clarified != query:
                    result["clarified"] = clarified
                    result["search_queries"].append(clarified)
            
            # 3. Query Decomposition
            if enable_decomposition and self._is_complex_query(query):
                sub_queries = await self._decompose_query(query)
                if sub_queries:
                    result["sub_queries"] = sub_queries
                    result["search_queries"].extend(sub_queries)
            
            # Deduplicate search queries
            result["search_queries"] = list(dict.fromkeys(result["search_queries"]))
            
            logger.info(f"✅ Query rewritten: {len(result['search_queries'])} variants generated")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Query rewriting failed: {e}", exc_info=True)
            # Return original query on error
            return result
    
    def _expand_with_synonyms(self, query: str) -> str:
        """
        Expand query with synonyms.
        
        Strategy:
        - Identify key terms
        - Add technical synonyms (domain-specific)
        - Add WordNet synonyms (general)
        - Create OR-expanded query
        
        Example:
            "start ingestion" → "start OR begin OR trigger ingestion OR document processing"
        """
        # Tokenize (simple)
        words = query.lower().split()
        
        expanded_terms = []
        
        for word in words:
            alternatives = [word]
            
            # 1. Domain glossary (HIGHEST PRIORITY) - PHASE 6R
            domain_expansions = self.domain_glossary.expand_term(word, max_expansions=2)
            if domain_expansions:
                alternatives.extend(domain_expansions)
                logger.debug(f"   📖 Domain glossary: '{word}' → {domain_expansions}")
            
            # 2. Technical synonyms (fallback for legacy terms)
            elif word in self.technical_synonyms:
                alternatives.extend(self.technical_synonyms[word][:3])  # Max 3 synonyms
            
            # 3. WordNet synonyms (general terms) - CACHED
            else:
                try:
                    # 🚀 OPTIMIZATION: Use cache to avoid repeated WordNet lookups
                    if word not in self._synset_cache:
                        synsets = wordnet.synsets(word)
                        if synsets:
                            # Get lemmas from first synset only (most common meaning)
                            lemmas = synsets[0].lemma_names()
                            # Cache up to 2 synonyms
                            self._synset_cache[word] = [
                                l.replace('_', ' ')
                                for l in lemmas
                                if l.lower() != word
                            ][:2]
                        else:
                            self._synset_cache[word] = []
                    
                    # Use cached synonyms
                    alternatives.extend(self._synset_cache[word])
                except Exception:
                    pass  # Skip on error
            
            # Create OR clause if we have alternatives
            if len(alternatives) > 1:
                # Remove duplicates, keep order
                alternatives = list(dict.fromkeys(alternatives))
                expanded_terms.append(" OR ".join(alternatives[:4]))  # Max 4 total
            else:
                expanded_terms.append(word)
        
        expanded_query = " ".join(expanded_terms)
        
        # If too long, truncate
        if len(expanded_query) > 500:
            expanded_query = expanded_query[:500]
        
        return expanded_query
    
    async def _clarify_with_llm(self, query: str) -> Optional[str]:
        """
        Use LLM to clarify vague query.
        
        Example:
            "Why is it slow?" → "Why is document ingestion slow? What causes performance issues?"
        """
        if len(query) > 200:
            # Query already detailed enough
            return None
        
        # Check if query is vague (contains pronouns, lacks specificity)
        vague_indicators = ["it", "this", "that", "they", "them", "why", "how", "what"]
        if not any(indicator in query.lower().split() for indicator in vague_indicators):
            return None  # Not vague
        
        try:
            prompt = f"""Rewrite this vague query to be more specific and technical, based on a document ingestion system context (RAG, embeddings, ChromaDB, workers, etc.).

Original query: "{query}"

Rewritten query (more specific, technical):"""
            
            response = await self.ollama_router.generate(
                prompt=prompt,
                max_tokens=100,
                temperature=0.3  # Low temperature for consistency
            )
            
            clarified = response.strip()
            
            # Sanity check: shouldn't be too different or too similar
            if clarified and 10 < len(clarified) < 300 and clarified != query:
                logger.info(f"   📝 Clarified: '{query}' → '{clarified}'")
                return clarified
            
        except Exception as e:
            logger.warning(f"LLM clarification failed: {e}")
        
        return None
    
    def _is_simple_query(self, query: str) -> bool:
        """
        Detect simple/direct queries that don't need expensive rewriting.
        
        🚀 OPTIMIZATION: Skip rewriting for:
        - Short queries (< 5 words)
        - Queries with specific technical terms
        - Direct "What is X" questions
        """
        # Cache check
        if query in self._simple_query_cache:
            return True
        
        words = query.lower().split()
        word_count = len(words)
        
        # Simple patterns
        is_simple = False
        
        # Pattern 1: Very short queries
        if word_count <= 3:
            is_simple = True
        
        # Pattern 2: Direct "What is X" questions
        elif query.lower().startswith(("what is", "what are")):
            is_simple = True
        
        # Pattern 3: Contains specific technical terms (no expansion needed)
        elif any(term in query.lower() for term in ["chromadb", "bm25", "postgresql", "redis", "docker"]):
            is_simple = True
        
        # Pattern 4: "How to" questions (simple enough)
        elif query.lower().startswith("how to") and word_count < 8:
            is_simple = True
        
        # Cache the result
        if is_simple and len(self._simple_query_cache) < 1000:  # Limit cache size
            self._simple_query_cache.add(query)
        
        return is_simple
    
    def _is_complex_query(self, query: str) -> bool:
        """
        Check if query is complex (should be decomposed).
        
        Indicators:
        - Contains "and" joining different questions
        - Multiple question marks
        - Multiple clauses
        """
        # Multiple questions
        if query.count('?') > 1:
            return True
        
        # Contains "and" with verbs (suggests multiple questions)
        if ' and ' in query.lower():
            # Simple heuristic: if "and" and multiple verbs, likely complex
            verbs = ['is', 'are', 'does', 'do', 'how', 'what', 'where', 'when', 'why']
            verb_count = sum(1 for v in verbs if v in query.lower().split())
            if verb_count >= 2:
                return True
        
        return False
    
    async def _decompose_query(self, query: str) -> List[str]:
        """
        Decompose complex query into sub-queries.
        
        Example:
            "How does authentication work and what database does it use?"
            →
            ["How does authentication work?", "What database does authentication use?"]
        """
        try:
            prompt = f"""Break this complex query into 2-3 simple, independent sub-questions.

Complex query: "{query}"

Sub-questions (one per line):
1."""
            
            response = await self.ollama_router.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.3
            )
            
            # Parse sub-questions
            lines = response.strip().split('\n')
            sub_queries = []
            
            for line in lines:
                # Remove numbering (1., 2., etc.)
                line = re.sub(r'^\d+\.\s*', '', line.strip())
                if line and len(line) > 10:
                    sub_queries.append(line)
            
            if sub_queries:
                logger.info(f"   🔀 Decomposed into {len(sub_queries)} sub-queries")
                return sub_queries[:3]  # Max 3 sub-queries
            
        except Exception as e:
            logger.warning(f"Query decomposition failed: {e}")
        
        return []


# Singleton instance
_query_rewriter = None


def get_query_rewriter() -> QueryRewriter:
    """Get or create query rewriter singleton."""
    global _query_rewriter
    if _query_rewriter is None:
        _query_rewriter = QueryRewriter()
    return _query_rewriter

