"""Mock Data Generator Service - Simplified Version.

Generates realistic mock data for testing the LLM Documentation Ecosystem.
Integrates with LLM Gateway for intelligent content generation.
"""

import asyncio
import json
import uuid
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum
import httpx

# Service configuration
SERVICE_NAME = "mock-data-generator"
SERVICE_TITLE = "Mock Data Generator"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5065

# Environment configuration
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")
DOC_STORE_URL = os.getenv("DOC_STORE_URL", "http://doc_store:5010")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

class MockDataType(str, Enum):
    """Types of mock data that can be generated."""
    CONFLUENCE_PAGE = "confluence_page"
    GITHUB_REPO = "github_repo"
    GITHUB_PR = "github_pr"
    JIRA_ISSUE = "jira_issue"
    JIRA_EPIC = "jira_epic"
    API_DOCS = "api_docs"
    CODE_SAMPLE = "code_sample"
    WORKFLOW_DATA = "workflow_data"

class GenerationRequest(BaseModel):
    """Request model for mock data generation."""
    data_type: MockDataType
    count: int = Field(default=1, ge=1, le=100)
    context: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}
    store_in_doc_store: bool = False

class MockDataResponse(BaseModel):
    """Response model for generated mock data."""
    success: bool
    data_type: str
    count: int
    generated_data: List[Dict[str, Any]]
    generation_time: float
    stored_documents: Optional[List[str]] = None

# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_TITLE,
    description="Generates realistic mock data for LLM ecosystem testing",
    version=SERVICE_VERSION
)

class MockDataGenerator:
    """Core mock data generation logic."""
    
    def __init__(self):
        self.templates = {
            MockDataType.CONFLUENCE_PAGE: {
                "title": "System Architecture Documentation",
                "content": "This document outlines the architecture of our microservices system...",
                "space": "Engineering",
                "labels": ["architecture", "microservices", "documentation"]
            },
            MockDataType.GITHUB_REPO: {
                "name": "awesome-project",
                "description": "A comprehensive solution for modern web applications",
                "language": "Python",
                "stars": 145,
                "forks": 23
            },
            MockDataType.GITHUB_PR: {
                "title": "Add new feature for user authentication",
                "description": "Implements OAuth 2.0 authentication flow with JWT tokens",
                "status": "open",
                "files_changed": 8
            },
            MockDataType.JIRA_ISSUE: {
                "summary": "Implement user dashboard functionality",
                "description": "Create a comprehensive user dashboard with analytics",
                "issue_type": "Story",
                "priority": "High"
            },
            MockDataType.API_DOCS: {
                "endpoint": "/api/v1/users",
                "method": "GET",
                "description": "Retrieve user information",
                "parameters": ["user_id", "include_profile"]
            }
        }
    
    async def generate_with_llm(self, data_type: MockDataType, context: str = None) -> Dict[str, Any]:
        """Generate content using LLM Gateway."""
        try:
            template = self.templates.get(data_type, {})
            prompt = f"Generate realistic {data_type.value} data. Context: {context or 'General purpose'}. Base template: {template}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_GATEWAY_URL}/query",
                    json={
                        "prompt": prompt,
                        "provider": "ollama",
                        "model": "llama2",
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract generated content and merge with template
                    generated_content = result.get("data", {}).get("response", "")
                    enhanced_data = template.copy()
                    enhanced_data["generated_content"] = generated_content
                    enhanced_data["generation_timestamp"] = datetime.now().isoformat()
                    enhanced_data["id"] = str(uuid.uuid4())
                    return enhanced_data
                else:
                    # Fallback to template with variations
                    return self.generate_fallback(data_type, context)
                    
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return self.generate_fallback(data_type, context)
    
    def generate_fallback(self, data_type: MockDataType, context: str = None) -> Dict[str, Any]:
        """Fallback generation without LLM."""
        template = self.templates.get(data_type, {}).copy()
        template["id"] = str(uuid.uuid4())
        template["generation_timestamp"] = datetime.now().isoformat()
        template["context"] = context
        template["generated_content"] = f"Mock {data_type.value} generated at {datetime.now()}"
        
        # Add some variation based on data type
        if data_type == MockDataType.CONFLUENCE_PAGE:
            template["page_id"] = f"page_{uuid.uuid4().hex[:8]}"
        elif data_type == MockDataType.GITHUB_REPO:
            template["repo_id"] = f"repo_{uuid.uuid4().hex[:8]}"
        elif data_type == MockDataType.JIRA_ISSUE:
            template["issue_key"] = f"PROJ-{uuid.uuid4().int % 9999}"
        
        return template
    
    async def store_in_doc_store(self, data: Dict[str, Any], data_type: str) -> Optional[str]:
        """Store generated data in doc store."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{DOC_STORE_URL}/documents",
                    json={
                        "title": f"Mock {data_type}: {data.get('title', data.get('name', data.get('summary', 'Generated Data')))}",
                        "content": json.dumps(data, indent=2),
                        "metadata": {
                            "data_type": data_type,
                            "generated": True,
                            "service": SERVICE_NAME
                        }
                    }
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return result.get("document_id")
                    
        except Exception as e:
            print(f"Doc store storage failed: {e}")
        return None

# Initialize generator
generator = MockDataGenerator()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": time.time(),
        "environment": ENVIRONMENT,
        "llm_gateway_url": LLM_GATEWAY_URL,
        "doc_store_url": DOC_STORE_URL
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": SERVICE_NAME,
        "title": SERVICE_TITLE,
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
            "types": "/data-types",
            "batch": "/generate/batch"
        },
        "supported_types": list(MockDataType),
        "features": {
            "llm_integration": True,
            "doc_store_integration": True,
            "batch_generation": True
        }
    }

@app.get("/data-types")
async def get_data_types():
    """Get available mock data types."""
    return {
        "data_types": [
            {
                "type": data_type.value,
                "description": f"Generate mock {data_type.value.replace('_', ' ')} data"
            }
            for data_type in MockDataType
        ]
    }

@app.post("/generate", response_model=MockDataResponse)
async def generate_mock_data(request: GenerationRequest):
    """Generate mock data based on the request."""
    start_time = time.time()
    
    try:
        generated_data = []
        stored_documents = []
        
        for i in range(request.count):
            # Generate data with optional LLM enhancement
            data = await generator.generate_with_llm(
                request.data_type, 
                request.context
            )
            
            # Add request parameters
            if request.parameters:
                data.update(request.parameters)
            
            generated_data.append(data)
            
            # Store in doc store if requested
            if request.store_in_doc_store:
                doc_id = await generator.store_in_doc_store(data, request.data_type.value)
                if doc_id:
                    stored_documents.append(doc_id)
        
        generation_time = time.time() - start_time
        
        return MockDataResponse(
            success=True,
            data_type=request.data_type.value,
            count=len(generated_data),
            generated_data=generated_data,
            generation_time=generation_time,
            stored_documents=stored_documents if stored_documents else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate mock data: {str(e)}"
        )

@app.post("/generate/batch")
async def generate_batch_data(requests: List[GenerationRequest]):
    """Generate multiple types of mock data in batch."""
    start_time = time.time()
    
    try:
        results = []
        
        for request in requests:
            result = await generate_mock_data(request)
            results.append(result)
        
        total_time = time.time() - start_time
        total_count = sum(result.count for result in results)
        
        return {
            "success": True,
            "batch_results": results,
            "total_items": total_count,
            "total_time": total_time,
            "average_time_per_item": total_time / total_count if total_count > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate batch data: {str(e)}"
        )

@app.get("/test/llm-connection")
async def test_llm_connection():
    """Test connection to LLM Gateway."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LLM_GATEWAY_URL}/health")
            if response.status_code == 200:
                return {
                    "llm_gateway_status": "connected",
                    "response": response.json()
                }
            else:
                return {
                    "llm_gateway_status": "error",
                    "status_code": response.status_code
                }
    except Exception as e:
        return {
            "llm_gateway_status": "unreachable",
            "error": str(e)
        }

@app.get("/test/doc-store-connection")
async def test_doc_store_connection():
    """Test connection to Doc Store."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DOC_STORE_URL}/health")
            if response.status_code == 200:
                return {
                    "doc_store_status": "connected",
                    "response": response.json()
                }
            else:
                return {
                    "doc_store_status": "error",
                    "status_code": response.status_code
                }
    except Exception as e:
        return {
            "doc_store_status": "unreachable",
            "error": str(e)
        }

if __name__ == "__main__":
    """Run the Mock Data Generator service directly."""
    import uvicorn
    print(f"🚀 Starting {SERVICE_TITLE} Service...")
    print(f"🔗 LLM Gateway: {LLM_GATEWAY_URL}")
    print(f"📄 Doc Store: {DOC_STORE_URL}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
