"""
Database connection and session management for Ecosystem MCP Service.

Provides async PostgreSQL connections using SQLAlchemy with connection pooling
and circuit breaker protection.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool

from ..config import settings
from .db_models import Base
from ..utils.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)

# Circuit breaker for database operations
_db_breaker = get_circuit_breaker(
    name="database",
    failure_threshold=5,
    timeout=30.0  # Try again after 30 seconds
)


class Database:
    """
    Database connection manager.
    
    Handles connection pooling, session management, and migrations.
    """
    
    def __init__(self, database_url: str | None = None):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection string (uses settings if None)
        """
        self.database_url = database_url or settings.database_url
        
        # Convert postgresql:// to postgresql+asyncpg://
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://",
                "postgresql+asyncpg://"
            )
        
        # Create async engine with connection pooling
        # Note: Don't specify poolclass for async engines - SQLAlchemy uses AsyncAdaptedQueuePool by default
        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            echo=settings.mcp_debug,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
        )
        
        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        logger.info(f"Database initialized: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """Return database URL with password redacted."""
        url = str(self.database_url)
        if "@" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                credentials, host = rest.split("@", 1)
                if ":" in credentials:
                    user, _ = credentials.split(":", 1)
                    return f"{protocol}://{user}:***@{host}"
        return url
    
    async def create_tables(self):
        """
        Create all tables.
        
        ⚠️ Use migrations in production!
        This is for development/testing only.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """
        Drop all tables.
        
        ⚠️ DANGER: This will delete all data!
        Only use in development/testing.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")
    
    async def close(self):
        """Close all database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.
        
        Usage:
            async with db.session() as session:
                result = await session.execute(query)
                await session.commit()
        """
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """
        Check if database is accessible with circuit breaker protection.
        
        Returns:
            True if database is healthy, False otherwise
        """
        from ..utils.retry import retry_database_operation
        
        @_db_breaker
        @retry_database_operation
        async def _check():
            from sqlalchemy import text
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
            return True
        
        try:
            return await _check()
        except CircuitBreakerOpenError as e:
            logger.warning(f"Database health check skipped - circuit breaker open: {e}")
            return False
        except Exception as e:
            logger.error(f"Database health check failed after retries: {e}")
            return False


# Global database instance
_database: Database | None = None


def get_database() -> Database:
    """
    Get global database instance.
    
    Creates instance on first call.
    """
    global _database
    if _database is None:
        _database = Database()
    return _database


async def init_database():
    """Initialize database on application startup."""
    from ..utils.exceptions import DatabaseError
    
    db = get_database()
    healthy = await db.health_check()
    if not healthy:
        raise DatabaseError("Database is not accessible")
    logger.info("Database initialized successfully")


async def close_database():
    """Close database on application shutdown."""
    global _database
    if _database is not None:
        await _database.close()
        _database = None
    logger.info("Database closed")

