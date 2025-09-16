"""MongoDB client for storing and retrieving Confluence pages."""

import logging
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