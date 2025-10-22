"""
Document Finder (Phase 6.1)

Finds relevant documents using semantic search based on extracted topics.
"""

import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RelevantDocument:
    """A document deemed relevant to the query."""
    document_id: str
    file_path: str
    content: str
    relevance_score: float
    commit_count: int
    last_modified: datetime
    ingestion_mode: str
    matched_topics: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'document_id': self.document_id,
            'file_path': self.file_path,
            'content_preview': self.content[:200] if self.content else '',
            'relevance_score': self.relevance_score,
            'commit_count': self.commit_count,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'ingestion_mode': self.ingestion_mode,
            'matched_topics': self.matched_topics
        }


class DocumentFinder:
    """
    Finds relevant documents using semantic search and filtering.
    
    Features:
    - Semantic search via embeddings
    - Relevance ranking
    - Deduplication
    - Git history awareness
    - Topic matching
    """
    
    def __init__(self):
        logger.info("DocumentFinder initialized")
    
    async def find_relevant_documents(
        self,
        search_terms: List[str],
        service_name: Optional[str] = None,
        limit: int = 50,
        min_relevance: float = 0.5
    ) -> List[RelevantDocument]:
        """
        Find documents relevant to the search terms.
        
        Args:
            search_terms: List of terms to search for
            service_name: Optional service filter
            limit: Maximum number of documents
            min_relevance: Minimum relevance score (0.0-1.0)
        
        Returns:
            List of relevant documents sorted by relevance
        """
        logger.info(f"Finding documents for {len(search_terms)} search terms")
        
        try:
            # Search using multiple strategies
            documents = []
            
            # Strategy 1: Semantic search via embeddings
            semantic_docs = await self._semantic_search(
                search_terms, service_name, limit * 2
            )
            documents.extend(semantic_docs)
            
            # Strategy 2: Keyword search for exact matches
            keyword_docs = await self._keyword_search(
                search_terms, service_name, limit
            )
            documents.extend(keyword_docs)
            
            # Strategy 3: File path matching
            path_docs = await self._path_search(
                search_terms, service_name, limit
            )
            documents.extend(path_docs)
            
            # Deduplicate by document_id
            unique_docs = self._deduplicate(documents)
            
            # Filter by minimum relevance
            filtered_docs = [
                doc for doc in unique_docs
                if doc.relevance_score >= min_relevance
            ]
            
            # Sort by relevance (highest first)
            sorted_docs = sorted(
                filtered_docs,
                key=lambda x: x.relevance_score,
                reverse=True
            )
            
            # Limit results
            result = sorted_docs[:limit]
            
            logger.info(f"✅ Found {len(result)} relevant documents")
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding documents: {e}")
            raise
    
    async def _semantic_search(
        self,
        search_terms: List[str],
        service_name: Optional[str],
        limit: int
    ) -> List[RelevantDocument]:
        """Perform semantic search using embeddings."""
        documents = []
        
        try:
            from ...storage.repositories import DocumentRepository
            from ...storage.database import get_db_session
            from ...storage.chromadb_client import get_chroma_client
            
            # Combine search terms into query
            query = ' '.join(search_terms)
            
            # Get embeddings client
            chroma_client = get_chroma_client()
            
            # TODO: Perform actual semantic search
            # For now, fallback to keyword search
            logger.debug(f"Semantic search for: {query[:100]}...")
            
            # Simulate semantic search with keyword for now
            async with get_db_session() as session:
                repo = DocumentRepository(session)
                
                # Search by content
                all_docs = await repo.find_by_metadata(
                    {'service': service_name} if service_name else {}
                )
                
                # Score by term matching
                for doc in all_docs[:limit]:
                    score = self._calculate_semantic_score(
                        doc.content, search_terms
                    )
                    
                    if score > 0:
                        documents.append(RelevantDocument(
                            document_id=str(doc.id),
                            file_path=doc.file_path,
                            content=doc.content,
                            relevance_score=score,
                            commit_count=getattr(doc, 'commit_count', 0),
                            last_modified=doc.updated_at,
                            ingestion_mode=doc.ingestion_mode,
                            matched_topics=self._get_matched_topics(
                                doc.content, search_terms
                            )
                        ))
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
        
        return documents
    
    async def _keyword_search(
        self,
        search_terms: List[str],
        service_name: Optional[str],
        limit: int
    ) -> List[RelevantDocument]:
        """Perform keyword-based search."""
        documents = []
        
        try:
            from ...storage.repositories import DocumentRepository
            from ...storage.database import get_db_session
            
            async with get_db_session() as session:
                repo = DocumentRepository(session)
                
                # Get documents
                all_docs = await repo.find_by_metadata(
                    {'service': service_name} if service_name else {}
                )
                
                # Score by keyword matching
                for doc in all_docs:
                    score = self._calculate_keyword_score(
                        doc.content, doc.file_path, search_terms
                    )
                    
                    if score > 0:
                        documents.append(RelevantDocument(
                            document_id=str(doc.id),
                            file_path=doc.file_path,
                            content=doc.content,
                            relevance_score=score * 0.8,  # Lower weight than semantic
                            commit_count=getattr(doc, 'commit_count', 0),
                            last_modified=doc.updated_at,
                            ingestion_mode=doc.ingestion_mode,
                            matched_topics=self._get_matched_topics(
                                doc.content, search_terms
                            )
                        ))
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
        
        return documents
    
    async def _path_search(
        self,
        search_terms: List[str],
        service_name: Optional[str],
        limit: int
    ) -> List[RelevantDocument]:
        """Search by file path matching."""
        documents = []
        
        try:
            from ...storage.repositories import DocumentRepository
            from ...storage.database import get_db_session
            
            async with get_db_session() as session:
                repo = DocumentRepository(session)
                
                # Get documents
                all_docs = await repo.find_by_metadata(
                    {'service': service_name} if service_name else {}
                )
                
                # Score by path matching
                for doc in all_docs:
                    score = self._calculate_path_score(
                        doc.file_path, search_terms
                    )
                    
                    if score > 0:
                        documents.append(RelevantDocument(
                            document_id=str(doc.id),
                            file_path=doc.file_path,
                            content=doc.content,
                            relevance_score=score * 0.9,  # High weight for path matches
                            commit_count=getattr(doc, 'commit_count', 0),
                            last_modified=doc.updated_at,
                            ingestion_mode=doc.ingestion_mode,
                            matched_topics=self._get_matched_topics(
                                doc.file_path, search_terms
                            )
                        ))
            
        except Exception as e:
            logger.error(f"Path search error: {e}")
        
        return documents
    
    def _calculate_semantic_score(
        self,
        content: str,
        search_terms: List[str]
    ) -> float:
        """Calculate semantic relevance score."""
        if not content or not search_terms:
            return 0.0
        
        content_lower = content.lower()
        
        # Count term matches
        matches = sum(1 for term in search_terms if term.lower() in content_lower)
        
        # Normalize by number of terms
        score = matches / len(search_terms) if search_terms else 0.0
        
        return min(score, 1.0)
    
    def _calculate_keyword_score(
        self,
        content: str,
        file_path: str,
        search_terms: List[str]
    ) -> float:
        """Calculate keyword relevance score."""
        if not content or not search_terms:
            return 0.0
        
        content_lower = content.lower()
        path_lower = file_path.lower()
        
        # Score content matches
        content_matches = sum(1 for term in search_terms if term.lower() in content_lower)
        
        # Score path matches (higher weight)
        path_matches = sum(1 for term in search_terms if term.lower() in path_lower)
        
        # Combined score
        total_matches = content_matches + (path_matches * 2)
        max_possible = len(search_terms) * 3
        
        score = total_matches / max_possible if max_possible > 0 else 0.0
        
        return min(score, 1.0)
    
    def _calculate_path_score(
        self,
        file_path: str,
        search_terms: List[str]
    ) -> float:
        """Calculate file path relevance score."""
        if not file_path or not search_terms:
            return 0.0
        
        path_lower = file_path.lower()
        
        # Exact path match gets highest score
        if any(term.lower() == path_lower for term in search_terms):
            return 1.0
        
        # Count partial matches
        matches = sum(1 for term in search_terms if term.lower() in path_lower)
        
        score = matches / len(search_terms) if search_terms else 0.0
        
        return min(score, 1.0)
    
    def _get_matched_topics(
        self,
        text: str,
        search_terms: List[str]
    ) -> List[str]:
        """Get list of matched topics in text."""
        if not text:
            return []
        
        text_lower = text.lower()
        
        matched = [
            term for term in search_terms
            if term.lower() in text_lower
        ]
        
        return matched
    
    def _deduplicate(
        self,
        documents: List[RelevantDocument]
    ) -> List[RelevantDocument]:
        """Remove duplicate documents, keeping highest relevance."""
        seen = {}
        
        for doc in documents:
            if doc.document_id not in seen:
                seen[doc.document_id] = doc
            else:
                # Keep document with higher relevance
                if doc.relevance_score > seen[doc.document_id].relevance_score:
                    seen[doc.document_id] = doc
        
        return list(seen.values())
    
    async def rank_by_git_history(
        self,
        documents: List[RelevantDocument]
    ) -> List[RelevantDocument]:
        """
        Re-rank documents considering git history.
        
        Documents with more commits get a boost in relevance.
        """
        for doc in documents:
            if doc.commit_count > 0:
                # Boost score based on commit activity
                commit_boost = min(doc.commit_count / 50.0, 0.2)
                doc.relevance_score = min(doc.relevance_score + commit_boost, 1.0)
        
        # Re-sort by updated relevance
        documents.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return documents

