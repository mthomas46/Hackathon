"""Tests for base repository classes.

Comprehensive test coverage for:
- SqlRepository CRUD operations
- InMemoryRepository functionality
- BaseRepository abstract interface
- Error handling and validation
"""

import pytest
import asyncio
import sqlite3
from abc import ABC
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List, Optional

from services.shared.domain.repositories.base_repository import (
    BaseRepository,
    SqlRepository,
    InMemoryRepository,
    RepositoryError,
    EntityNotFoundError,
)
from services.shared.domain.exceptions import DomainError


# Test Entity for repository testing
class TestEntity:
    """Simple test entity for repository testing."""

    def __init__(self, id: str, name: str, value: int = 0):
        self.id = id
        self.name = name
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestEntity":
        """Create entity from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            value=data.get("value", 0),
        )

    def __eq__(self, other):
        if not isinstance(other, TestEntity):
            return False
        return (
            self.id == other.id
            and self.name == other.name
            and self.value == other.value
        )


class TestBaseRepository:
    """Test BaseRepository abstract interface."""

    def test_base_repository_is_abstract(self):
        """Test that BaseRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseRepository(TestEntity)

    def test_base_repository_initialization(self):
        """Test BaseRepository initialization with entity class."""
        repo = BaseRepository(TestEntity)
        assert repo.entity_class == TestEntity

    def test_base_repository_abstract_methods(self):
        """Test that abstract methods are properly defined."""
        repo = BaseRepository(TestEntity)

        # These should raise NotImplementedError
        with pytest.raises(NotImplementedError):
            asyncio.run(repo.find_by_id("test"))

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.find_all())

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.save(TestEntity("1", "test")))

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.update("1", {"name": "updated"}))

        with pytest.raises(NotImplementedError):
            asyncio.run(repo.delete("1"))


class TestInMemoryRepository:
    """Test InMemoryRepository implementation."""

    def setup_method(self):
        """Setup for each test."""
        self.repo = InMemoryRepository(TestEntity)

    def test_initialization(self):
        """Test InMemoryRepository initialization."""
        assert self.repo.entity_class == TestEntity
        assert self.repo._storage == {}

    @pytest.mark.asyncio
    async def test_save_new_entity(self):
        """Test saving a new entity."""
        entity = TestEntity("1", "test", 42)
        result = await self.repo.save(entity)

        assert result == entity
        assert "1" in self.repo._storage
        assert self.repo._storage["1"] == entity

    @pytest.mark.asyncio
    async def test_save_update_existing(self):
        """Test saving updates existing entity."""
        entity1 = TestEntity("1", "test", 42)
        await self.repo.save(entity1)

        entity2 = TestEntity("1", "updated", 100)
        result = await self.repo.save(entity2)

        assert result == entity2
        assert self.repo._storage["1"] == entity2

    @pytest.mark.asyncio
    async def test_find_by_id_existing(self):
        """Test finding existing entity by ID."""
        entity = TestEntity("1", "test", 42)
        await self.repo.save(entity)

        result = await self.repo.find_by_id("1")
        assert result == entity

    @pytest.mark.asyncio
    async def test_find_by_id_nonexistent(self):
        """Test finding nonexistent entity by ID."""
        result = await self.repo.find_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_all_empty(self):
        """Test finding all entities when repository is empty."""
        result = await self.repo.find_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_find_all_with_entities(self):
        """Test finding all entities."""
        entity1 = TestEntity("1", "test1", 10)
        entity2 = TestEntity("2", "test2", 20)
        await self.repo.save(entity1)
        await self.repo.save(entity2)

        result = await self.repo.find_all()
        assert len(result) == 2
        assert entity1 in result
        assert entity2 in result

    @pytest.mark.asyncio
    async def test_update_existing(self):
        """Test updating existing entity."""
        entity = TestEntity("1", "original", 10)
        await self.repo.save(entity)

        update_data = {"name": "updated", "value": 20}
        result = await self.repo.update("1", update_data)

        assert result is True
        updated = await self.repo.find_by_id("1")
        assert updated.name == "updated"
        assert updated.value == 20

    @pytest.mark.asyncio
    async def test_update_nonexistent(self):
        """Test updating nonexistent entity."""
        result = await self.repo.update("nonexistent", {"name": "test"})
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_existing(self):
        """Test deleting existing entity."""
        entity = TestEntity("1", "test", 42)
        await self.repo.save(entity)

        result = await self.repo.delete("1")
        assert result is True
        assert "1" not in self.repo._storage

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        """Test deleting nonexistent entity."""
        result = await self.repo.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """Test exists returns True for existing entity."""
        entity = TestEntity("1", "test", 42)
        await self.repo.save(entity)

        result = await self.repo.exists("1")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        """Test exists returns False for nonexistent entity."""
        result = await self.repo.exists("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_count_empty(self):
        """Test count returns 0 for empty repository."""
        result = await self.repo.count()
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_with_entities(self):
        """Test count returns correct number of entities."""
        entity1 = TestEntity("1", "test1", 10)
        entity2 = TestEntity("2", "test2", 20)
        await self.repo.save(entity1)
        await self.repo.save(entity2)

        result = await self.repo.count()
        assert result == 2


class TestSqlRepository:
    """Test SqlRepository implementation."""

    def setup_method(self):
        """Setup for each test."""
        self.connection_string = "sqlite:///:memory:"
        self.repo = SqlRepository(TestEntity, self.connection_string)

        # Create test table
        asyncio.run(self._create_test_table())

    async def _create_test_table(self):
        """Create test table for SQL repository."""
        async with self.repo._get_connection() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS test_entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    value INTEGER DEFAULT 0
                )
            """
            )
            await conn.commit()

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test SqlRepository initialization."""
        assert self.repo.entity_class == TestEntity
        assert self.repo.connection_string == self.connection_string

    @pytest.mark.asyncio
    async def test_save_new_entity(self):
        """Test saving a new entity to SQL database."""
        entity = TestEntity("1", "test", 42)
        result = await self.repo.save(entity)

        assert result == entity

        # Verify it was saved
        found = await self.repo.find_by_id("1")
        assert found == entity

    @pytest.mark.asyncio
    async def test_save_update_existing(self):
        """Test saving updates existing entity in SQL."""
        entity1 = TestEntity("1", "original", 10)
        await self.repo.save(entity1)

        entity2 = TestEntity("1", "updated", 20)
        result = await self.repo.save(entity2)

        assert result == entity2

        # Verify update
        found = await self.repo.find_by_id("1")
        assert found.name == "updated"
        assert found.value == 20

    @pytest.mark.asyncio
    async def test_find_by_id_existing(self):
        """Test finding existing entity by ID in SQL."""
        entity = TestEntity("1", "test", 42)
        await self.repo.save(entity)

        result = await self.repo.find_by_id("1")
        assert result == entity

    @pytest.mark.asyncio
    async def test_find_by_id_nonexistent(self):
        """Test finding nonexistent entity by ID in SQL."""
        result = await self.repo.find_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_all_sql(self):
        """Test finding all entities in SQL."""
        entity1 = TestEntity("1", "test1", 10)
        entity2 = TestEntity("2", "test2", 20)
        await self.repo.save(entity1)
        await self.repo.save(entity2)

        result = await self.repo.find_all()
        assert len(result) == 2

        # Results should contain both entities (order may vary)
        entity_ids = {e.id for e in result}
        assert entity_ids == {"1", "2"}

    @pytest.mark.asyncio
    async def test_update_sql(self):
        """Test updating entity in SQL."""
        entity = TestEntity("1", "original", 10)
        await self.repo.save(entity)

        update_data = {"name": "updated", "value": 20}
        result = await self.repo.update("1", update_data)

        assert result is True

        # Verify update
        found = await self.repo.find_by_id("1")
        assert found.name == "updated"
        assert found.value == 20

    @pytest.mark.asyncio
    async def test_delete_sql(self):
        """Test deleting entity from SQL."""
        entity = TestEntity("1", "test", 42)
        await self.repo.save(entity)

        result = await self.repo.delete("1")
        assert result is True

        # Verify deletion
        found = await self.repo.find_by_id("1")
        assert found is None

    @pytest.mark.asyncio
    async def test_exists_sql(self):
        """Test exists method with SQL."""
        entity = TestEntity("1", "test", 42)
        await self.repo.save(entity)

        assert await self.repo.exists("1") is True
        assert await self.repo.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_count_sql(self):
        """Test count method with SQL."""
        # Initially empty
        assert await self.repo.count() == 0

        # Add entities
        entity1 = TestEntity("1", "test1", 10)
        entity2 = TestEntity("2", "test2", 20)
        await self.repo.save(entity1)
        await self.repo.save(entity2)

        assert await self.repo.count() == 2

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent repository operations."""
        # Create multiple entities concurrently
        entities = [TestEntity(f"{i}", f"test{i}", i * 10) for i in range(10)]

        # Save concurrently
        tasks = [self.repo.save(entity) for entity in entities]
        await asyncio.gather(*tasks)

        # Verify all were saved
        count = await self.repo.count()
        assert count == 10

        # Verify all can be found
        found_entities = await self.repo.find_all()
        assert len(found_entities) == 10


class TestRepositoryErrorHandling:
    """Test error handling in repositories."""

    @pytest.mark.asyncio
    async def test_sql_repository_connection_error(self):
        """Test SQL repository handles connection errors gracefully."""
        # Use invalid connection string
        repo = SqlRepository(TestEntity, "invalid://connection")

        with pytest.raises(Exception):  # Should raise some connection error
            await repo.find_all()

    @pytest.mark.asyncio
    async def test_repository_validation(self):
        """Test repository input validation."""
        repo = InMemoryRepository(TestEntity)

        # Test with invalid entity
        with pytest.raises(AttributeError):
            await repo.save("not an entity")

        # Test with None entity
        with pytest.raises(AttributeError):
            await repo.save(None)


if __name__ == "__main__":
    pytest.main([__file__])
