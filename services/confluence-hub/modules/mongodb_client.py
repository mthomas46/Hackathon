"""MongoDB client for storing and retrieving Confluence pages."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Client for interacting with MongoDB."""
    
    def __init__(self, connection_string: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client.confluence_hub
        self.collection = self.db.confluence_pages
        
    async def test_connectivity(self) -> bool:
        """Test MongoDB connectivity."""
        try:
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            return True
        except Exception as e:
            logger.error(f"MongoDB connectivity test failed: {str(e)}")
            return False
    
    async def create_indexes(self):
        """Create necessary indexes for the collection."""
        try:
            # Create indexes for performance
            await self.collection.create_index([("session_id", 1)])
            await self.collection.create_index([("confluence_page_id", 1)], unique=True)
            await self.collection.create_index([("metadata.space_key", 1)])
            await self.collection.create_index([("title", "text"), ("content", "text")])
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {str(e)}")
    
    async def insert_page(self, page_data: Dict[str, Any]) -> str:
        """Insert a page into the collection."""
        try:
            # Remove any existing page with the same confluence_page_id
            await self.collection.delete_many({"confluence_page_id": page_data["confluence_page_id"]})
            
            result = await self.collection.insert_one(page_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting page: {str(e)}")
            raise
    
    async def get_pages(
        self, 
        session_id: Optional[str] = None, 
        limit: int = 100, 
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get pages from the collection."""
        try:
            query = {}
            if session_id:
                query["session_id"] = session_id
            
            cursor = self.collection.find(query).skip(skip).limit(limit)
            pages = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for page in pages:
                page["_id"] = str(page["_id"])
            
            return pages
        except Exception as e:
            logger.error(f"Error retrieving pages: {str(e)}")
            raise
    
    async def get_page_by_confluence_id(self, confluence_page_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific page by its Confluence ID."""
        try:
            page = await self.collection.find_one({"confluence_page_id": confluence_page_id})
            if page:
                page["_id"] = str(page["_id"])
            return page
        except Exception as e:
            logger.error(f"Error retrieving page {confluence_page_id}: {str(e)}")
            raise
    
    async def delete_page(self, confluence_page_id: str) -> bool:
        """Delete a page by its Confluence ID."""
        try:
            result = await self.collection.delete_one({"confluence_page_id": confluence_page_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting page {confluence_page_id}: {str(e)}")
            raise
    
    async def count_pages(self, session_id: Optional[str] = None) -> int:
        """Count pages in the collection."""
        try:
            query = {}
            if session_id:
                query["session_id"] = session_id
            return await self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting pages: {str(e)}")
            raise
    
    # ============================================================================
    # EMBEDDING METHODS
    # ============================================================================
    
    async def update_page_embedding(self, page_id: str, embedding: List[float]) -> bool:
        """Update a page with its embedding vector.
        
        Args:
            page_id: MongoDB document ID
            embedding: Embedding vector
            
        Returns:
            True if update was successful
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(page_id)},
                {"$set": {"embedding": embedding, "embedding_updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating embedding for page {page_id}: {str(e)}")
            raise
    
    async def get_pages_with_embeddings(self) -> List[Dict[str, Any]]:
        """Get all pages that have embeddings.
        
        Returns:
            List of pages with embeddings
        """
        try:
            cursor = self.collection.find(
                {"embedding": {"$exists": True, "$ne": []}},
                {"_id": 1, "embedding": 1, "title": 1, "confluence_page_id": 1}
            )
            pages = await cursor.to_list(length=None)
            
            # Convert ObjectId to string
            for page in pages:
                page["_id"] = str(page["_id"])
            
            return pages
        except Exception as e:
            logger.error(f"Error retrieving pages with embeddings: {str(e)}")
            raise
    
    async def get_pages_without_embeddings(self) -> List[Dict[str, Any]]:
        """Get all pages that don't have embeddings.
        
        Returns:
            List of pages without embeddings
        """
        try:
            cursor = self.collection.find(
                {"$or": [
                    {"embedding": {"$exists": False}},
                    {"embedding": {"$size": 0}}
                ]},
                {"_id": 1, "title": 1, "content": 1, "confluence_page_id": 1}
            )
            pages = await cursor.to_list(length=None)
            
            # Convert ObjectId to string
            for page in pages:
                page["_id"] = str(page["_id"])
            
            return pages
        except Exception as e:
            logger.error(f"Error retrieving pages without embeddings: {str(e)}")
            raise
    
    async def count_pages_with_embeddings(self) -> int:
        """Count pages that have embeddings.
        
        Returns:
            Number of pages with embeddings
        """
        try:
            return await self.collection.count_documents({
                "embedding": {"$exists": True, "$ne": []}
            })
        except Exception as e:
            logger.error(f"Error counting pages with embeddings: {str(e)}")
            raise
    
    async def get_all_pages(self) -> List[Dict[str, Any]]:
        """Get all pages from the collection.
        
        Returns:
            List of all pages
        """
        try:
            cursor = self.collection.find(
                {},
                {"_id": 1, "title": 1, "content": 1, "confluence_page_id": 1}
            )
            pages = await cursor.to_list(length=None)
            
            # Convert ObjectId to string
            for page in pages:
                page["_id"] = str(page["_id"])
            
            return pages
        except Exception as e:
            logger.error(f"Error retrieving all pages: {str(e)}")
            raise
    
    async def get_page_by_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific page by its MongoDB ID.
        
        Args:
            page_id: MongoDB document ID
            
        Returns:
            Page document or None if not found
        """
        try:
            page = await self.collection.find_one({"_id": ObjectId(page_id)})
            if page:
                page["_id"] = str(page["_id"])
            return page
        except Exception as e:
            logger.error(f"Error retrieving page by ID {page_id}: {str(e)}")
            raise