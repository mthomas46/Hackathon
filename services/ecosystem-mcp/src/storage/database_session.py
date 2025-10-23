"""
Database Session Wrapper

Provides a high-level interface for database operations with
automatic retry logic, connection pooling, and error handling.
"""

import logging
from typing import Optional, Any, Callable
from contextlib import asynccontextmanager
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, DBAPIError

from .database import get_database

logger = logging.getLogger(__name__)


class DatabaseSession:
    """
    Database session wrapper with retry logic and error handling.
    
    Provides:
    - Automatic retry on connection failures
    - Connection pool management
    - Transaction management
    - Error recovery
    
    Wraps existing database infrastructure.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """
        Initialize database session wrapper.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            backoff_factor: Exponential backoff multiplier
        """
        self.db = get_database()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        logger.info(f"DatabaseSession initialized (max_retries={max_retries})")
    
    @asynccontextmanager
    async def session(self):
        """
        Get database session with automatic retry.
        
        Yields:
            AsyncSession
        
        Usage:
            async with db_session.session() as session:
                # Use session
                await session.commit()
        """
        retries = 0
        delay = self.retry_delay
        
        while retries <= self.max_retries:
            try:
                async with self.db.session() as session:
                    yield session
                    return
            except (OperationalError, DBAPIError) as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"❌ Database connection failed after {self.max_retries} retries: {e}")
                    raise
                
                logger.warning(f"⚠️ Database connection error (attempt {retries}/{self.max_retries}): {e}")
                logger.info(f"   Retrying in {delay}s...")
                
                await asyncio.sleep(delay)
                delay *= self.backoff_factor
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute database operation with automatic retry.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Operation result
        """
        retries = 0
        delay = self.retry_delay
        
        while retries <= self.max_retries:
            try:
                return await operation(*args, **kwargs)
            except (OperationalError, DBAPIError) as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"❌ Operation failed after {self.max_retries} retries: {e}")
                    raise
                
                logger.warning(f"⚠️ Operation error (attempt {retries}/{self.max_retries}): {e}")
                logger.info(f"   Retrying in {delay}s...")
                
                await asyncio.sleep(delay)
                delay *= self.backoff_factor
    
    async def health_check(self) -> bool:
        """
        Check database health.
        
        Returns:
            True if database is healthy
        """
        try:
            async with self.session() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                logger.info("✅ Database health check passed")
                return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """
        Get database connection information.
        
        Returns:
            Connection info dictionary
        """
        try:
            async with self.session() as session:
                from sqlalchemy import text
                
                # Get database version
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                
                # Get connection count
                result = await session.execute(
                    text("SELECT count(*) FROM pg_stat_activity")
                )
                connections = result.scalar()
                
                return {
                    "healthy": True,
                    "version": version,
                    "active_connections": connections,
                    "max_retries": self.max_retries
                }
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "max_retries": self.max_retries
            }


# Singleton instance
_database_session: Optional[DatabaseSession] = None


def get_database_session(
    max_retries: int = 3,
    **kwargs
) -> DatabaseSession:
    """
    Get singleton database session wrapper.
    
    Args:
        max_retries: Maximum retry attempts
        **kwargs: Additional configuration
    
    Returns:
        DatabaseSession instance
    """
    global _database_session
    if _database_session is None:
        _database_session = DatabaseSession(max_retries=max_retries, **kwargs)
    return _database_session

