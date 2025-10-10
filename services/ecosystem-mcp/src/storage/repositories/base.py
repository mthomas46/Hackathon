"""
Base repository for common database operations.

Provides generic CRUD operations that can be extended by specific repositories.
"""

from typing import Generic, TypeVar, Type, Optional, List
from uuid import UUID

from sqlalchemy import select, update as sql_update, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.
    
    All specific repositories should extend this class.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Model fields
        
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: UUID | int | str) -> Optional[ModelType]:
        """
        Get record by ID.
        
        Args:
            id: Record ID
        
        Returns:
            Model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """
        Get all records with pagination.
        
        Args:
            limit: Maximum number of records
            offset: Number of records to skip
        
        Returns:
            List of model instances
        """
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def update(self, id: UUID | int | str, **kwargs) -> Optional[ModelType]:
        """
        Update record by ID.
        
        Args:
            id: Record ID
            **kwargs: Fields to update
        
        Returns:
            Updated model instance or None if not found
        """
        await self.session.execute(
            sql_update(self.model).where(self.model.id == id).values(**kwargs)
        )
        await self.session.flush()
        return await self.get_by_id(id)
    
    async def delete(self, id: UUID | int | str) -> bool:
        """
        Delete record by ID.
        
        Args:
            id: Record ID
        
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            sql_delete(self.model).where(self.model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def count(self) -> int:
        """
        Count total records.
        
        Returns:
            Total number of records
        """
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()
    
    async def exists(self, id: UUID | int | str) -> bool:
        """
        Check if record exists.
        
        Args:
            id: Record ID
        
        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None

