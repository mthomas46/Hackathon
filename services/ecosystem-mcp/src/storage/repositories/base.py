"""
Base repository with enhanced patterns for bulk operations,
transactions, streaming, and complex filtering.

Provides common database operations with performance optimizations.
Includes Layer 5 data isolation: automatic test data filtering in production.
"""

import logging
from typing import Generic, TypeVar, Optional, List, Dict, Any, AsyncIterator
from uuid import UUID
from contextlib import asynccontextmanager

from sqlalchemy import select, update, delete, func, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.utils.environment_config import get_database_config
from src.utils.test_data_marker import TestDataMarker

logger = logging.getLogger(__name__)

# Type variable for model class
ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with enhanced operations.
    
    Features:
    - CRUD operations
    - Bulk insert/update/delete
    - Query streaming
    - Complex filtering
    - Transaction support
    - Performance optimizations
    - Layer 5 Data Isolation: Auto-filter test data in production
    """
    
    def __init__(self, session: AsyncSession, model_class: type[ModelType]):
        """
        Initialize repository.
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class
        self.config = get_database_config()
    
    # ========================================================================
    # Layer 5: Test Data Isolation (NEW)
    # ========================================================================
    
    def _should_filter_test_data(self) -> bool:
        """
        Check if test data should be filtered from queries.
        
        Test data is filtered in all non-test environments to ensure
        production users never see test data, even if it accidentally
        exists in the database.
        
        Returns:
            True if test data should be filtered (production/staging)
            False if test data is allowed (test/development)
        """
        return not self.config.get("allow_test_data", False)
    
    def _filter_test_data(self, query: Select) -> Select:
        """
        Apply test data filtering to query (Layer 5 protection).
        
        In production/staging environments, automatically filters out
        any records marked as test data. This acts as a safety net
        if test data accidentally ends up in production database.
        
        Args:
            query: SQLAlchemy query to filter
        
        Returns:
            Query with test data filter applied (if needed)
        
        Example:
            # In production: filters out test data automatically
            # In test: includes test data
            query = select(DocumentModel)
            query = self._filter_test_data(query)
            # Now safe for production use
        """
        if not self._should_filter_test_data():
            # Test/dev environment: allow test data
            return query
        
        # Production/staging: filter out test data
        # Check if model has metadata field (JSONB)
        if hasattr(self.model_class, 'metadata'):
            # Filter out records where metadata contains test marker
            query = query.where(
                ~self.model_class.metadata.contains({
                    TestDataMarker.TEST_MARKER_KEY: True
                })
            )
            logger.debug(f"Applied test data filter to {self.model_class.__name__} query")
        
        return query
    
    # ========================================================================
    # Basic CRUD Operations
    # ========================================================================
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get entity by ID.
        
        Args:
            id: Entity ID
        
        Returns:
            Entity if found, None otherwise
        """
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """
        Get all entities.
        
        Automatically filters test data in production (Layer 5 protection).
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of entities (excluding test data in production)
        """
        query = select(self.model_class)
        query = self._filter_test_data(query)  # Layer 5 protection
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, entity: ModelType) -> ModelType:
        """
        Create entity.
        
        Args:
            entity: Entity to create
        
        Returns:
            Created entity with ID
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: ModelType) -> ModelType:
        """
        Update entity.
        
        Args:
            entity: Entity to update
        
        Returns:
            Updated entity
        """
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, entity: ModelType) -> None:
        """
        Delete entity.
        
        Args:
            entity: Entity to delete
        """
        await self.session.delete(entity)
        await self.session.flush()
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities.
        
        Automatically filters test data in production (Layer 5 protection).
        
        Args:
            filters: Optional filters
        
        Returns:
            Entity count (excluding test data in production)
        """
        query = select(func.count()).select_from(self.model_class)
        
        # Apply test data filter first
        if hasattr(self.model_class, 'metadata') and self._should_filter_test_data():
            query = query.where(
                ~self.model_class.metadata.contains({
                    TestDataMarker.TEST_MARKER_KEY: True
                })
            )
        
        if filters:
            query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    # ========================================================================
    # Bulk Operations (NEW)
    # ========================================================================
    
    async def bulk_create(
        self,
        entities: List[ModelType],
        batch_size: int = 1000
    ) -> List[ModelType]:
        """
        Create multiple entities efficiently.
        
        Uses batching to avoid memory issues with large datasets.
        
        Args:
            entities: List of entities to create
            batch_size: Number of entities per batch
        
        Returns:
            List of created entities with IDs
        
        Performance:
            - 10-50x faster than individual creates
            - Batching prevents memory exhaustion
        
        Example:
            entities = [Document(...), Document(...), ...]
            created = await repo.bulk_create(entities)
        """
        created = []
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            self.session.add_all(batch)
            await self.session.flush()
            
            # Refresh to get IDs
            for entity in batch:
                await self.session.refresh(entity)
            
            created.extend(batch)
            logger.debug(f"Bulk created batch of {len(batch)} {self.model_class.__name__}")
        
        logger.info(f"Bulk created {len(created)} {self.model_class.__name__} entities")
        return created
    
    async def bulk_update(
        self,
        updates: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        Update multiple entities efficiently.
        
        Args:
            updates: List of update dicts with 'id' and field values
            batch_size: Number of updates per batch
        
        Returns:
            Number of updated entities
        
        Example:
            updates = [
                {"id": uuid1, "status": "completed"},
                {"id": uuid2, "status": "completed"},
            ]
            count = await repo.bulk_update(updates)
        """
        total_updated = 0
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            for update_data in batch:
                entity_id = update_data.pop("id")
                
                stmt = (
                    update(self.model_class)
                    .where(self.model_class.id == entity_id)
                    .values(**update_data)
                )
                
                result = await self.session.execute(stmt)
                total_updated += result.rowcount
            
            await self.session.flush()
            logger.debug(f"Bulk updated batch of {len(batch)} {self.model_class.__name__}")
        
        logger.info(f"Bulk updated {total_updated} {self.model_class.__name__} entities")
        return total_updated
    
    async def bulk_delete(
        self,
        ids: List[UUID],
        batch_size: int = 1000
    ) -> int:
        """
        Delete multiple entities efficiently.
        
        Args:
            ids: List of entity IDs to delete
            batch_size: Number of deletes per batch
        
        Returns:
            Number of deleted entities
        """
        total_deleted = 0
        
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            
            stmt = delete(self.model_class).where(self.model_class.id.in_(batch))
            result = await self.session.execute(stmt)
            total_deleted += result.rowcount
            
            await self.session.flush()
            logger.debug(f"Bulk deleted batch of {len(batch)} {self.model_class.__name__}")
        
        logger.info(f"Bulk deleted {total_deleted} {self.model_class.__name__} entities")
        return total_deleted
    
    # ========================================================================
    # Query Streaming (NEW)
    # ========================================================================
    
    async def stream_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        batch_size: int = 100
    ) -> AsyncIterator[ModelType]:
        """
        Stream entities without loading all into memory.
        
        Automatically filters test data in production (Layer 5 protection).
        Useful for processing large datasets.
        
        Args:
            filters: Optional filters
            batch_size: Number of entities per fetch
        
        Yields:
            Entity instances one at a time (excluding test data in production)
        
        Example:
            async for document in repo.stream_all():
                await process(document)
        """
        offset = 0
        
        while True:
            query = select(self.model_class)
            query = self._filter_test_data(query)  # Layer 5 protection
            
            if filters:
                query = self._apply_filters(query, filters)
            
            query = query.offset(offset).limit(batch_size)
            
            result = await self.session.execute(query)
            entities = list(result.scalars().all())
            
            if not entities:
                break
            
            for entity in entities:
                yield entity
            
            offset += batch_size
    
    async def stream_filtered(
        self,
        filters: Dict[str, Any],
        order_by: Optional[str] = None,
        batch_size: int = 100
    ) -> AsyncIterator[ModelType]:
        """
        Stream filtered entities.
        
        Automatically filters test data in production (Layer 5 protection).
        
        Args:
            filters: Filters to apply
            order_by: Field to order by
            batch_size: Number of entities per fetch
        
        Yields:
            Filtered entity instances (excluding test data in production)
        """
        offset = 0
        
        while True:
            query = select(self.model_class)
            query = self._filter_test_data(query)  # Layer 5 protection
            query = self._apply_filters(query, filters)
            
            if order_by:
                query = query.order_by(getattr(self.model_class, order_by))
            
            query = query.offset(offset).limit(batch_size)
            
            result = await self.session.execute(query)
            entities = list(result.scalars().all())
            
            if not entities:
                break
            
            for entity in entities:
                yield entity
            
            offset += batch_size
    
    # ========================================================================
    # Complex Filtering (NEW)
    # ========================================================================
    
    def _apply_filters(
        self,
        query: Select,
        filters: Dict[str, Any]
    ) -> Select:
        """
        Apply complex filters to query.
        
        Supports:
        - Exact match: {"field": value}
        - Range: {"field": {"gte": val1, "lte": val2}}
        - In: {"field": [val1, val2, val3]}
        - Like: {"field": {"like": "%pattern%"}}
        - Not equal: {"field": {"ne": value}}
        - Is null: {"field": None}
        - Is not null: {"field": {"not_null": True}}
        
        Args:
            query: SQLAlchemy query
            filters: Filter dict
        
        Returns:
            Query with filters applied
        """
        for field_name, value in filters.items():
            if not hasattr(self.model_class, field_name):
                logger.warning(f"Field '{field_name}' not found on {self.model_class.__name__}")
                continue
            
            field = getattr(self.model_class, field_name)
            
            if value is None:
                # IS NULL
                query = query.where(field.is_(None))
            
            elif isinstance(value, dict):
                # Complex operators
                for op, op_value in value.items():
                    if op == "gte":
                        query = query.where(field >= op_value)
                    elif op == "gt":
                        query = query.where(field > op_value)
                    elif op == "lte":
                        query = query.where(field <= op_value)
                    elif op == "lt":
                        query = query.where(field < op_value)
                    elif op == "ne":
                        query = query.where(field != op_value)
                    elif op == "like":
                        query = query.where(field.like(op_value))
                    elif op == "ilike":
                        query = query.where(field.ilike(op_value))
                    elif op == "not_null":
                        if op_value:
                            query = query.where(field.is_not(None))
                    else:
                        logger.warning(f"Unknown operator: {op}")
            
            elif isinstance(value, list):
                # IN clause
                query = query.where(field.in_(value))
            
            else:
                # Exact match
                query = query.where(field == value)
        
        return query
    
    async def find(
        self,
        filters: Dict[str, Any],
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """
        Find entities with complex filters.
        
        Automatically filters test data in production (Layer 5 protection).
        
        Args:
            filters: Filter dict
            order_by: Field to order by
            limit: Maximum results
            offset: Results to skip
        
        Returns:
            List of matching entities (excluding test data in production)
        
        Example:
            # Find documents created in last 7 days
            documents = await repo.find({
                "created_at": {"gte": seven_days_ago},
                "is_latest": True
            }, order_by="created_at", limit=100)
        """
        query = select(self.model_class)
        query = self._filter_test_data(query)  # Layer 5 protection
        query = self._apply_filters(query, filters)
        
        if order_by:
            query = query.order_by(getattr(self.model_class, order_by))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_one(self, filters: Dict[str, Any]) -> Optional[ModelType]:
        """
        Find single entity with filters.
        
        Args:
            filters: Filter dict
        
        Returns:
            Entity if found, None otherwise
        """
        results = await self.find(filters, limit=1)
        return results[0] if results else None
    
    # ========================================================================
    # Existence Checks
    # ========================================================================
    
    async def exists(self, filters: Dict[str, Any]) -> bool:
        """
        Check if entity exists with filters.
        
        Automatically filters test data in production (Layer 5 protection).
        
        Args:
            filters: Filter dict
        
        Returns:
            True if entity exists (excluding test data in production)
        """
        query = select(func.count()).select_from(self.model_class)
        
        # Apply test data filter first
        if hasattr(self.model_class, 'metadata') and self._should_filter_test_data():
            query = query.where(
                ~self.model_class.metadata.contains({
                    TestDataMarker.TEST_MARKER_KEY: True
                })
            )
        
        query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count > 0


# ============================================================================
# Transaction Helpers (NEW)
# ============================================================================

@asynccontextmanager
async def transaction(session: AsyncSession):
    """
    Transaction context manager.
    
    Usage:
        async with transaction(session):
            await repo1.create(entity1)
            await repo2.update(entity2)
            # Auto-commits on success, rolls back on error
    """
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise


@asynccontextmanager
async def savepoint(session: AsyncSession, name: str = "savepoint"):
    """
    Savepoint context manager for nested transactions.
    
    Usage:
        async with transaction(session):
            await repo1.create(entity1)
            
            try:
                async with savepoint(session):
                    await repo2.create(entity2)  # May fail
            except:
                pass  # Rollback to savepoint
            
            await repo3.create(entity3)  # Still works
    """
    await session.execute(f"SAVEPOINT {name}")
    try:
        yield session
        await session.execute(f"RELEASE SAVEPOINT {name}")
    except Exception:
        await session.execute(f"ROLLBACK TO SAVEPOINT {name}")
        raise
