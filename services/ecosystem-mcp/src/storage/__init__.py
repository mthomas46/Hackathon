"""
Storage layer for Ecosystem MCP Service.

Provides database access through repository pattern.
"""

from .database import Database, get_database
from .chromadb_client import ChromaDBClient, get_chroma_client

# Placeholder functions for lifecycle management
async def init_database():
    """Initialize database connection."""
    db = get_database()
    await db.connect()

async def close_database():
    """Close database connection."""
    db = get_database()
    await db.disconnect()

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

