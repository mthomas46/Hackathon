"""Database setup and session management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from services.mcp_store.infrastructure.database.models import Base
from services.mcp_store.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection and session management."""
    
    def __init__(self, settings: Settings):
        """
        Initialize database.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Create async engine
        # For SQLite, use StaticPool to allow concurrent access
        self.engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
        )
        
        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info(f"Database initialized: {settings.database_url}")
    
    async def create_tables(self):
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")
    
    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.
        
        Yields:
            AsyncSession: Database session
        """
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database instance (will be initialized in main.py)
_db: Database = None


def init_database(settings: Settings) -> Database:
    """
    Initialize global database instance.
    
    Args:
        settings: Application settings
        
    Returns:
        Database instance
    """
    global _db
    _db = Database(settings)
    return _db


def get_database() -> Database:
    """
    Get the global database instance.
    
    Returns:
        Database instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db
