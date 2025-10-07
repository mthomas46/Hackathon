"""
Database connection management for TimescaleDB/PostgreSQL.
"""
import asyncpg
import logging
from typing import Optional

from services.mcp_performance_store.infrastructure.config import Settings


class DatabaseConnection:
    """
    Manages database connection pool for TimescaleDB/PostgreSQL.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize database connection manager.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.settings.timescale_url,
                min_size=5,
                max_size=self.settings.timescale_pool_size,
                command_timeout=60,
                server_settings={
                    'application_name': 'mcp-performance-store'
                }
            )
            self.logger.info("Database connection pool created")
            
            # Run initial migrations/schema
            await self._initialize_schema()
    
    async def disconnect(self):
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self.logger.info("Database connection pool closed")
    
    @property
    def pool(self) -> asyncpg.Pool:
        """Get database connection pool."""
        if self._pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._pool
    
    async def _initialize_schema(self):
        """
        Initialize database schema.
        
        Note: In production, use proper migration tools like Alembic.
        """
        try:
            # Read schema file
            import os
            schema_path = os.path.join(
                os.path.dirname(__file__),
                'schema.sql'
            )
            
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema
                async with self._pool.acquire() as conn:
                    await conn.execute(schema_sql)
                    self.logger.info("Database schema initialized")
            else:
                self.logger.warning(f"Schema file not found: {schema_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize schema: {e}")
            # Don't raise - allow service to start even if schema init fails
    
    async def execute(self, query: str, *args):
        """
        Execute a query.
        
        Args:
            query: SQL query
            *args: Query parameters
        
        Returns:
            Query result
        """
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """
        Fetch multiple rows.
        
        Args:
            query: SQL query
            *args: Query parameters
        
        Returns:
            List of rows
        """
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """
        Fetch a single row.
        
        Args:
            query: SQL query
            *args: Query parameters
        
        Returns:
            Single row or None
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """
        Fetch a single value.
        
        Args:
            query: SQL query
            *args: Query parameters
        
        Returns:
            Single value or None
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)
