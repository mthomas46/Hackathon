"""
Storage layer for Ecosystem MCP Service.

Provides database access through repository pattern.
"""

from .database import Database, get_database
from .chromadb_client import ChromaDBClient, get_chroma_client

# Placeholder functions for lifecycle management
async def init_database():
    """Initialize database connection and create tables.
    
    Raises:
        RuntimeError: If database connection fails during initialization
    """
    import logging
    from sqlalchemy import create_engine
    from .db_models import Base
    from ..config import settings
    
    logger = logging.getLogger(__name__)
    
    # Create tables using sync engine (one-time operation)
    # Convert async URL to sync for table creation
    sync_url = str(settings.database_url).replace('postgresql+asyncpg://', 'postgresql://')
    
    logger.info("Creating database tables...")
    engine = create_engine(sync_url, echo=False)
    try:
        Base.metadata.create_all(engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise RuntimeError(f"Database table creation failed: {e}") from e
    finally:
        engine.dispose()  # Clean up sync engine
    
    # Validate async connection
    logger.info("Validating database connection...")
    db = get_database()
    try:
        is_healthy = await db.health_check()
        if not is_healthy:
            raise RuntimeError("Database health check failed - connection unreachable")
        logger.info("✅ Database connection validated successfully")
    except Exception as e:
        logger.error(f"❌ Database connection validation failed: {e}")
        raise RuntimeError(f"Database connection failed during initialization: {e}") from e

async def close_database():
    """Close database connection."""
    db = get_database()
    # Dispose of the engine to close all connections
    await db.engine.dispose()

async def init_chroma():
    """Initialize ChromaDB."""
    pass  # ChromaDB initializes on first use

async def close_chroma():
    """Close ChromaDB."""
    pass  # ChromaDB closes automatically

__all__ = [
    "Database",
    "get_database",
    "ChromaDBClient",
    "get_chroma_client",
    "init_database",
    "close_database",
]

