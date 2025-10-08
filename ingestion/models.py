"""
Data models for ingestion system.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class NormalizedDocument:
    """Normalized document model for ingestion pipeline."""
    
    document_id: str
    title: str
    content_md: str
    original_format: str  # 'code', 'document', 'wikipedia', 'jira', etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'document_id': self.document_id,
            'title': self.title,
            'content_md': self.content_md,
            'original_format': self.original_format,
            'metadata': self.metadata,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""
    
    success: bool
    document_id: str
    message: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'document_id': self.document_id,
            'message': self.message,
            'error': self.error,
            'metadata': self.metadata,
        }


@dataclass
class CrawlReport:
    """Report from a crawling operation."""
    
    total_pages: int
    crawl_graph: Dict[str, Dict[str, Any]]
    depth_distribution: Dict[int, int]
    link_statistics: Dict[str, Any]
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_pages': self.total_pages,
            'crawl_graph': self.crawl_graph,
            'depth_distribution': self.depth_distribution,
            'link_statistics': self.link_statistics,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration_seconds,
        }

