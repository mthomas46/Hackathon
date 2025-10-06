"""Base worker class for all extractors, normalizers, and embedders."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WorkerResult(BaseModel):
    """Standard result format for all workers."""
    
    success: bool
    worker_type: str
    documents_processed: int = 0
    documents_failed: int = 0
    documents_skipped: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


@dataclass
class Document:
    """Standard document format passed through pipeline."""
    
    doc_id: str
    source: str  # github, confluence, jira, etc.
    source_type: str  # repo, page, issue, etc.
    title: str
    content: str
    raw_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    embeddings: Optional[List[float]] = None
    tier: Optional[str] = None  # project, team, company, client
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "source": self.source,
            "source_type": self.source_type,
            "title": self.title,
            "content": self.content,
            "raw_content": self.raw_content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "url": self.url,
            "tags": self.tags,
            "entities": self.entities,
            "embeddings": self.embeddings,
            "tier": self.tier,
        }


class BaseWorker(ABC):
    """Base class for all workers."""
    
    def __init__(self, worker_type: str):
        self.worker_type = worker_type
        self.logger = logging.getLogger(f"worker.{worker_type}")
    
    @abstractmethod
    async def process(self, config: Dict[str, Any]) -> WorkerResult:
        """
        Process work based on configuration.
        
        Args:
            config: Worker-specific configuration
        
        Returns:
            WorkerResult with statistics and errors
        """
        pass
    
    def _create_result(
        self,
        success: bool,
        started_at: datetime,
        **kwargs
    ) -> WorkerResult:
        """Create a WorkerResult."""
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        return WorkerResult(
            success=success,
            worker_type=self.worker_type,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            **kwargs
        )


class BaseExtractor(BaseWorker):
    """Base class for extraction workers."""
    
    def __init__(self, worker_type: str):
        super().__init__(f"extractor.{worker_type}")
    
    @abstractmethod
    async def extract(self, config: Dict[str, Any]) -> List[Document]:
        """
        Extract documents from source.
        
        Args:
            config: Extraction configuration
        
        Returns:
            List of extracted documents
        """
        pass
    
    async def process(self, config: Dict[str, Any]) -> WorkerResult:
        """Process extraction job."""
        started_at = datetime.utcnow()
        errors = []
        warnings = []
        
        try:
            documents = await self.extract(config)
            
            return self._create_result(
                success=True,
                started_at=started_at,
                documents_processed=len(documents),
                metadata={"document_count": len(documents)}
            )
        
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}", exc_info=True)
            errors.append(str(e))
            
            return self._create_result(
                success=False,
                started_at=started_at,
                documents_failed=1,
                errors=errors
            )


class BaseNormalizer(BaseWorker):
    """Base class for normalization workers."""
    
    def __init__(self, worker_type: str):
        super().__init__(f"normalizer.{worker_type}")
    
    @abstractmethod
    async def normalize(self, documents: List[Document]) -> List[Document]:
        """
        Normalize documents.
        
        Args:
            documents: Documents to normalize
        
        Returns:
            Normalized documents
        """
        pass
    
    async def process(self, config: Dict[str, Any]) -> WorkerResult:
        """Process normalization job."""
        started_at = datetime.utcnow()
        errors = []
        
        try:
            documents = config.get("documents", [])
            normalized = await self.normalize(documents)
            
            return self._create_result(
                success=True,
                started_at=started_at,
                documents_processed=len(normalized),
            )
        
        except Exception as e:
            self.logger.error(f"Normalization failed: {e}", exc_info=True)
            errors.append(str(e))
            
            return self._create_result(
                success=False,
                started_at=started_at,
                documents_failed=len(documents),
                errors=errors
            )


class BaseEmbedder(BaseWorker):
    """Base class for embedding workers."""
    
    def __init__(self, worker_type: str):
        super().__init__(f"embedder.{worker_type}")
    
    @abstractmethod
    async def embed(self, documents: List[Document]) -> List[Document]:
        """
        Add embeddings to documents.
        
        Args:
            documents: Documents to embed
        
        Returns:
            Documents with embeddings
        """
        pass
    
    async def process(self, config: Dict[str, Any]) -> WorkerResult:
        """Process embedding job."""
        started_at = datetime.utcnow()
        errors = []
        
        try:
            documents = config.get("documents", [])
            embedded = await self.embed(documents)
            
            return self._create_result(
                success=True,
                started_at=started_at,
                documents_processed=len(embedded),
            )
        
        except Exception as e:
            self.logger.error(f"Embedding failed: {e}", exc_info=True)
            errors.append(str(e))
            
            return self._create_result(
                success=False,
                started_at=started_at,
                documents_failed=len(documents),
                errors=errors
            )

