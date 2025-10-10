"""
Embedding repository for Ecosystem MCP Service.

Provides embedding-specific database operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import EmbeddingModel
from .base import BaseRepository


class EmbeddingRepository(BaseRepository[EmbeddingModel]):
    """
    Embedding repository with domain-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize embedding repository."""
        super().__init__(EmbeddingModel, session)
    
    async def get_by_document_id(
        self,
        document_id: UUID
    ) -> Optional[EmbeddingModel]:
        """
        Get embedding for a document.
        
        Args:
            document_id: Document UUID
        
        Returns:
            Embedding model or None
        """
        result = await self.session.execute(
            select(self.model).where(self.model.document_id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_chroma_id(
        self,
        chroma_id: str
    ) -> Optional[EmbeddingModel]:
        """
        Get embedding by ChromaDB ID.
        
        Args:
            chroma_id: ChromaDB identifier
        
        Returns:
            Embedding model or None
        """
        result = await self.session.execute(
            select(self.model).where(self.model.chroma_id == chroma_id)
        )
        return result.scalar_one_or_none()
    
    async def get_recent_embeddings(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[EmbeddingModel]:
        """
        Get embeddings created in the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum embeddings
        
        Returns:
            List of embeddings
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(self.model)
            .where(self.model.created_at >= since)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_total_cost(
        self,
        since: Optional[datetime] = None
    ) -> float:
        """
        Calculate total embedding cost.
        
        Args:
            since: Optional start date (None = all time)
        
        Returns:
            Total cost in USD
        """
        query = select(func.sum(self.model.cost_usd))
        
        if since:
            query = query.where(self.model.created_at >= since)
        
        result = await self.session.execute(query)
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0
    
    async def get_total_tokens(
        self,
        since: Optional[datetime] = None
    ) -> int:
        """
        Calculate total tokens embedded.
        
        Args:
            since: Optional start date (None = all time)
        
        Returns:
            Total token count
        """
        query = select(func.sum(self.model.token_count))
        
        if since:
            query = query.where(self.model.created_at >= since)
        
        result = await self.session.execute(query)
        total = result.scalar_one_or_none()
        return int(total) if total else 0
    
    async def get_cost_by_model(self) -> dict[str, float]:
        """
        Get total cost grouped by model.
        
        Returns:
            Dictionary of {model_name: total_cost}
        """
        result = await self.session.execute(
            select(
                self.model.model,
                func.sum(self.model.cost_usd).label("total_cost")
            )
            .group_by(self.model.model)
        )
        
        return {row.model: float(row.total_cost) for row in result}

