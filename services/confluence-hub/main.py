"""Service: Confluence Hub

Endpoints:
- POST /convert-page: Convert a Confluence page and all subpages to markdown and store in MongoDB
- GET /health: Health check endpoint that validates MongoDB and Confluence connectivity
- GET /pages: Retrieve stored pages with optional filtering
- DELETE /pages/{page_id}: Delete a specific page from the database
- GET /pages/{page_id}: Get a specific page by its Confluence page ID

Responsibilities:
- Retrieve Confluence pages and their hierarchies
- Convert Confluence content to markdown format
- Store converted pages in MongoDB with metadata
- Provide health checks for external dependencies
- Manage document storage and retrieval

Dependencies: MongoDB, Confluence API.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import os
import logging
from urllib.parse import urljoin

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from bson import ObjectId

# Shared modules
from services.shared.health import register_health_endpoints, DependencyHealth
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ServiceException, install_error_handlers
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, generate_id, setup_common_middleware
from services.shared.config import get_config_value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MODELS
# ============================================================================

class ConvertPageRequest(BaseModel):
    """Request model for converting Confluence pages."""
    page_id: Optional[str] = Field(None, description="Confluence page ID to convert")
    page_title: Optional[str] = Field(None, description="Confluence page title to search for")
    space_key: Optional[str] = Field(None, description="Confluence space key (required when using page_title)")
    session_id: str = Field(..., description="Session ID for tracking this conversion batch")
    max_depth: int = Field(default=10, description="Maximum depth for recursive page retrieval")
    include_content: bool = Field(default=True, description="Whether to include page content")

class ConfluencePageMetadata(BaseModel):
    """Metadata for a Confluence page."""
    original_url: str
    space_key: str
    parent_page_id: Optional[str] = None
    last_modified: datetime
    author: str
    version: int

class ConfluencePage(BaseModel):
    """Model for stored Confluence page."""
    id: Optional[str] = Field(None, alias="_id")
    session_id: str
    confluence_page_id: str
    title: str
    content: str
    metadata: ConfluencePageMetadata
    file_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class PageListResponse(BaseModel):
    """Response model for page listing."""
    pages: List[ConfluencePage]
    total: int
    session_id: Optional[str] = None

# Import modularized components
from .modules import ConfluenceClient, MongoDBClient, process_confluence_page

# ============================================================================
# APPLICATION SETUP
# ============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Confluence Hub Service",
    description="Service for converting Confluence pages to markdown and storing in MongoDB",
    version="1.0.0"
)

# Setup middleware and error handling
setup_common_middleware(app)
install_error_handlers(app)

# Global clients
confluence_client: Optional[ConfluenceClient] = None
mongodb_client: Optional[MongoDBClient] = None

@app.on_event("startup")
async def startup():
    """Initialize clients and database on startup."""
    global confluence_client, mongodb_client
    
    # Get configuration
    confluence_base_url = get_config_value("CONFLUENCE_BASE_URL", env_key="ConfluenceBaseUrl")
    confluence_username = get_config_value("CONFLUENCE_USERNAME", env_key="ConfluenceUsername")
    confluence_api_token = get_config_value("CONFLUENCE_API_TOKEN", env_key="ConfluenceApiToken")
    mongo_connection_string = get_config_value("MONGO_CONNECTION_STRING", env_key="MongoConnectionString")
    
    if not all([confluence_base_url, confluence_username, confluence_api_token, mongo_connection_string]):
        missing = []
        if not confluence_base_url: missing.append("ConfluenceBaseUrl")
        if not confluence_username: missing.append("ConfluenceUsername") 
        if not confluence_api_token: missing.append("ConfluenceApiToken")
        if not mongo_connection_string: missing.append("MongoConnectionString")
        
        logger.error(f"Missing required environment variables: {missing}")
        raise ValueError(f"Missing required environment variables: {missing}")
    
    # Initialize clients
    confluence_client = ConfluenceClient(confluence_base_url, confluence_username, confluence_api_token)
    mongodb_client = MongoDBClient(mongo_connection_string)
    
    # Test connections and create indexes
    try:
        await mongodb_client.test_connectivity()
        await mongodb_client.create_indexes()
        await confluence_client.test_connectivity()
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

async def check_confluence_health() -> DependencyHealth:
    """Check Confluence connectivity."""
    try:
        if not confluence_client:
            return DependencyHealth(
                name="confluence",
                status="unhealthy",
                error="Confluence client not initialized"
            )
        
        start_time = datetime.now()
        is_healthy = await confluence_client.test_connectivity()
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return DependencyHealth(
            name="confluence",
            status="healthy" if is_healthy else "unhealthy",
            response_time_ms=response_time,
            error=None if is_healthy else "Connection test failed"
        )
    except Exception as e:
        return DependencyHealth(
            name="confluence",
            status="unhealthy",
            error=str(e)
        )

async def check_mongodb_health() -> DependencyHealth:
    """Check MongoDB connectivity."""
    try:
        if not mongodb_client:
            return DependencyHealth(
                name="mongodb",
                status="unhealthy",
                error="MongoDB client not initialized"
            )
        
        start_time = datetime.now()
        is_healthy = await mongodb_client.test_connectivity()
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return DependencyHealth(
            name="mongodb",
            status="healthy" if is_healthy else "unhealthy",
            response_time_ms=response_time,
            error=None if is_healthy else "Connection test failed"
        )
    except Exception as e:
        return DependencyHealth(
            name="mongodb",
            status="unhealthy",
            error=str(e)
        )

# Register health endpoints
register_health_endpoints(
    app,
    service_name=ServiceNames.CONFLUENCE_HUB,
    dependency_checks=[check_confluence_health, check_mongodb_health]
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/convert-page")
async def convert_page(request: ConvertPageRequest):
    """Convert a Confluence page and all its subpages to markdown and store in MongoDB."""
    try:
        if not confluence_client or not mongodb_client:
            raise HTTPException(status_code=500, detail="Services not properly initialized")
        
        # Determine which page to process
        root_page = None
        if request.page_id:
            logger.info(f"Fetching page by ID: {request.page_id}")
            root_page = await confluence_client.get_page_by_id(request.page_id)
        elif request.page_title:
            if not request.space_key:
                raise HTTPException(status_code=400, detail="space_key is required when using page_title")
            
            logger.info(f"Searching for page: {request.page_title} in space: {request.space_key}")
            search_results = await confluence_client.search_pages_by_title(request.page_title, request.space_key)
            
            if not search_results:
                raise HTTPException(status_code=404, detail=f"Page '{request.page_title}' not found in space '{request.space_key}'")
            
            if len(search_results) > 1:
                logger.warning(f"Multiple pages found with title '{request.page_title}'. Using the first one.")
            
            # Get full page details
            root_page = await confluence_client.get_page_by_id(search_results[0]['id'])
        else:
            raise HTTPException(status_code=400, detail="Either page_id or page_title must be provided")
        
        logger.info(f"Processing page: {root_page['title']} (ID: {root_page['id']})")
        
        # Get all descendant pages if requested
        all_pages = [root_page]
        if request.max_depth > 0:
            descendants = await confluence_client.get_all_descendant_pages(root_page['id'], request.max_depth)
            all_pages.extend(descendants)
        
        logger.info(f"Found {len(all_pages)} pages to process")
        
        # Process and store all pages
        stored_pages = []
        for page in all_pages:
            try:
                # Get page content if not already included and requested
                if request.include_content and not page.get('body', {}).get('storage'):
                    page = await confluence_client.get_page_by_id(page['id'])
                
                # Process the page
                processed_page = await process_confluence_page(page, request.session_id, confluence_client.base_url)
                
                # Store in MongoDB
                page_id = await mongodb_client.insert_page(processed_page)
                processed_page['_id'] = page_id
                stored_pages.append(processed_page)
                
                logger.info(f"Stored page: {page['title']} (ID: {page['id']})")
                
            except Exception as e:
                logger.error(f"Error processing page {page.get('title', 'Unknown')} ({page['id']}): {str(e)}")
                # Continue with other pages
        
        return create_success_response(
            data={
                "session_id": request.session_id,
                "pages_processed": len(stored_pages),
                "total_pages_found": len(all_pages),
                "pages": stored_pages
            },
            message=f"Successfully processed {len(stored_pages)} pages"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in convert_page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pages", response_model=PageListResponse)
async def get_pages(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of pages to return"),
    skip: int = Query(0, ge=0, description="Number of pages to skip")
):
    """Retrieve stored pages with optional filtering."""
    try:
        if not mongodb_client:
            raise HTTPException(status_code=500, detail="MongoDB client not initialized")
        
        pages = await mongodb_client.get_pages(session_id, limit, skip)
        total = await mongodb_client.count_pages(session_id)
        
        # Convert to response model
        confluence_pages = []
        for page_data in pages:
            page = ConfluencePage(**page_data)
            confluence_pages.append(page)
        
        return PageListResponse(
            pages=confluence_pages,
            total=total,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in get_pages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pages/{page_id}")
async def get_page(page_id: str):
    """Get a specific page by its Confluence page ID."""
    try:
        if not mongodb_client:
            raise HTTPException(status_code=500, detail="MongoDB client not initialized")
        
        page = await mongodb_client.get_page_by_confluence_id(page_id)
        if not page:
            raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
        
        return create_success_response(data=page)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/pages/{page_id}")
async def delete_page(page_id: str):
    """Delete a specific page from the database."""
    try:
        if not mongodb_client:
            raise HTTPException(status_code=500, detail="MongoDB client not initialized")
        
        deleted = await mongodb_client.delete_page(page_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
        
        return create_success_response(
            message=f"Page {page_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=5070)
    except ImportError:
        logger.error("uvicorn is required to run the service directly. Install with: pip install uvicorn")
        print("To run this service, use: uvicorn main:app --host 0.0.0.0 --port 5070")