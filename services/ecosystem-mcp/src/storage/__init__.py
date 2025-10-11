"""
Storage layer for Ecosystem MCP Service.

Provides database access through repository pattern.
"""

from .database import Database, get_database
from .chromadb_client import ChromaDBClient, get_chroma_client

# Placeholder functions for lifecycle management
async def init_database():
    """Initialize database connection and create tables."""
    from sqlalchemy import create_engine
    from .db_models import Base
    from ..config import settings
    
    # Create tables using sync engine (one-time operation)
    # Convert async URL to sync for table creation
    sync_url = str(settings.database_url).replace('postgresql+asyncpg://', 'postgresql://')
    engine = create_engine(sync_url, echo=False)
    Base.metadata.create_all(engine)
    engine.dispose()  # Clean up sync engine
    
    # Database is already initialized via get_database()
    # No need to call connect() - async engine handles connections automatically

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

