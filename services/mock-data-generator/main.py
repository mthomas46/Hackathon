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
SERVICE_TITLE = "Enhanced Mock Data Generator"
SERVICE_VERSION = "2.0.0"
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
    # New ecosystem-specific types
    LLM_PROMPT = "llm_prompt"
    ANALYSIS_REPORT = "analysis_report"
    SOURCE_CODE = "source_code"
    DOCUMENT_COLLECTION = "document_collection"
    USER_PROFILE = "user_profile"
    NOTIFICATION = "notification"
    CONFIGURATION = "configuration"
    LOG_ENTRY = "log_entry"

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

class BulkCollectionRequest(BaseModel):
    """Request model for bulk data collection generation."""
    collection_name: str
    description: Optional[str] = None
    data_types: List[MockDataType]
    items_per_type: Dict[str, int] = Field(default_factory=dict)
    total_items: int = Field(default=100, ge=10, le=10000)
    context: Optional[str] = None
    store_in_doc_store: bool = True
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

class BulkCollectionResponse(BaseModel):
    """Response model for bulk collection generation."""
    success: bool
    collection_name: str
    collection_id: str
    total_items: int
    items_by_type: Dict[str, int]
    generation_time: float
    stored_documents: List[str]
    metadata: Dict[str, Any]
    created_at: str

class EcosystemScenarioRequest(BaseModel):
    """Request model for ecosystem scenario generation."""
    scenario_type: str = Field(..., description="Type of scenario (e.g., 'code_review', 'documentation', 'analysis')")
    complexity: str = Field(default="medium", description="Complexity level (simple, medium, complex)")
    scale: str = Field(default="small", description="Scale of data (small, medium, large)")
    include_relationships: bool = Field(default=True, description="Include data relationships")
    store_in_doc_store: bool = True

class EcosystemScenarioResponse(BaseModel):
    """Response model for ecosystem scenario generation."""
    success: bool
    scenario_type: str
    scenario_id: str
    complexity: str
    scale: str
    total_items: int
    data_breakdown: Dict[str, int]
    generation_time: float
    stored_collections: List[str]
    scenario_metadata: Dict[str, Any]
    created_at: str

# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_TITLE,
    description="Enhanced mock data generator for LLM ecosystem testing. Creates representative data collections, bulk datasets, and complete ecosystem scenarios for comprehensive testing and development.",
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
            },
            # New ecosystem-specific templates
            MockDataType.LLM_PROMPT: {
                "name": "Code Analysis Prompt",
                "content": "Analyze the following code for potential bugs, security issues, and best practices. Provide detailed feedback with specific recommendations.",
                "category": "development",
                "tags": ["code", "analysis", "security"],
                "model_preference": "gpt-4"
            },
            MockDataType.ANALYSIS_REPORT: {
                "title": "Code Quality Analysis Report",
                "summary": "Comprehensive analysis of codebase quality metrics and recommendations",
                "issues_found": 15,
                "recommendations": ["Improve error handling", "Add input validation", "Update dependencies"],
                "severity_breakdown": {"high": 3, "medium": 7, "low": 5}
            },
            MockDataType.SOURCE_CODE: {
                "filename": "api_handler.py",
                "language": "python",
                "content": "def handle_request(request):\n    try:\n        data = validate_input(request)\n        result = process_data(data)\n        return format_response(result)\n    except Exception as e:\n        logger.error(f'Error processing request: {e}')\n        return error_response(e)",
                "complexity_score": 3.2,
                "lines_of_code": 45
            },
            MockDataType.DOCUMENT_COLLECTION: {
                "name": "API Documentation Suite",
                "documents": ["overview.md", "authentication.md", "endpoints.md", "examples.md"],
                "total_pages": 25,
                "last_updated": "2024-01-15",
                "version": "2.1.0"
            },
            MockDataType.USER_PROFILE: {
                "username": "developer@example.com",
                "role": "Senior Developer",
                "permissions": ["read", "write", "admin"],
                "preferences": {"theme": "dark", "notifications": True},
                "last_login": "2024-01-20T10:30:00Z"
            },
            MockDataType.NOTIFICATION: {
                "title": "System Maintenance Scheduled",
                "message": "Scheduled maintenance will occur tonight from 2-4 AM EST",
                "priority": "medium",
                "type": "maintenance",
                "target_users": ["all"],
                "scheduled_time": "2024-01-21T02:00:00Z"
            },
            MockDataType.CONFIGURATION: {
                "service_name": "api-gateway",
                "version": "1.2.3",
                "environment": "production",
                "settings": {
                    "rate_limit": 1000,
                    "timeout": 30,
                    "retries": 3,
                    "features": ["authentication", "logging", "monitoring"]
                },
                "last_modified": "2024-01-15T14:20:00Z"
            },
            MockDataType.LOG_ENTRY: {
                "timestamp": "2024-01-20T10:15:30Z",
                "level": "INFO",
                "service": "user-service",
                "message": "User authentication successful",
                "user_id": "user_12345",
                "request_id": "req_abcdef",
                "duration_ms": 150
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
        elif data_type == MockDataType.LLM_PROMPT:
            template["prompt_id"] = f"prompt_{uuid.uuid4().hex[:8]}"
        elif data_type == MockDataType.SOURCE_CODE:
            template["file_hash"] = uuid.uuid4().hex[:16]
        elif data_type == MockDataType.USER_PROFILE:
            template["user_id"] = f"user_{uuid.uuid4().hex[:8]}"
        elif data_type == MockDataType.LOG_ENTRY:
            template["log_id"] = f"log_{uuid.uuid4().hex[:12]}"

        return template

    async def generate_bulk_collection(self, request: BulkCollectionRequest) -> BulkCollectionResponse:
        """Generate a bulk collection of mock data."""
        start_time = time.time()
        collection_id = str(uuid.uuid4())
        stored_documents = []
        items_by_type = {}

        try:
            # Distribute items across data types
            if request.items_per_type:
                # Use specified distribution
                total_items = sum(request.items_per_type.values())
            else:
                # Distribute evenly across data types
                total_items = request.total_items
                items_per_type = total_items // len(request.data_types)
                remainder = total_items % len(request.data_types)

                for i, data_type in enumerate(request.data_types):
                    count = items_per_type + (1 if i < remainder else 0)
                    request.items_per_type[data_type.value] = count

            # Generate data for each type
            for data_type_str, count in request.items_per_type.items():
                data_type = MockDataType(data_type_str)
                items_by_type[data_type_str] = count

                for i in range(count):
                    # Generate individual item
                    data = await self.generate_with_llm(data_type, request.context)

                    # Add collection metadata
                    data["collection_id"] = collection_id
                    data["collection_name"] = request.collection_name
                    data["item_index"] = i + 1
                    data["tags"] = request.tags

                    if request.metadata:
                        data["collection_metadata"] = request.metadata

                    # Store in doc store if requested
                    if request.store_in_doc_store:
                        doc_id = await self.store_in_doc_store(data, f"{request.collection_name}_{data_type_str}")
                        if doc_id:
                            stored_documents.append(doc_id)

            generation_time = time.time() - start_time

            return BulkCollectionResponse(
                success=True,
                collection_name=request.collection_name,
                collection_id=collection_id,
                total_items=sum(items_by_type.values()),
                items_by_type=items_by_type,
                generation_time=generation_time,
                stored_documents=stored_documents,
                metadata={
                    "description": request.description,
                    "context": request.context,
                    "tags": request.tags,
                    "created_by": "bulk_generator"
                },
                created_at=datetime.now().isoformat()
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate bulk collection: {str(e)}"
            )

    async def generate_ecosystem_scenario(self, request: EcosystemScenarioRequest) -> EcosystemScenarioResponse:
        """Generate a complete ecosystem scenario with related data."""
        start_time = time.time()
        scenario_id = str(uuid.uuid4())
        stored_collections = []

        try:
            # Define scenario templates
            scenarios = {
                "code_review": {
                    "description": "Complete code review workflow scenario",
                    "collections": {
                        "source_code": 50,
                        "llm_prompt": 10,
                        "analysis_report": 5,
                        "github_pr": 3,
                        "log_entry": 20
                    }
                },
                "documentation": {
                    "description": "Documentation generation and management scenario",
                    "collections": {
                        "confluence_page": 15,
                        "api_docs": 8,
                        "document_collection": 3,
                        "user_profile": 5,
                        "configuration": 2
                    }
                },
                "analysis": {
                    "description": "Data analysis and reporting scenario",
                    "collections": {
                        "analysis_report": 10,
                        "source_code": 30,
                        "log_entry": 15,
                        "configuration": 3,
                        "notification": 5
                    }
                }
            }

            scenario_config = scenarios.get(request.scenario_type, scenarios["documentation"])

            # Adjust scale
            scale_multiplier = {"small": 0.5, "medium": 1.0, "large": 2.0}.get(request.scale, 1.0)
            complexity_multiplier = {"simple": 0.6, "medium": 1.0, "complex": 1.5}.get(request.complexity, 1.0)
            multiplier = scale_multiplier * complexity_multiplier

            # Generate collections
            data_breakdown = {}
            for data_type_str, base_count in scenario_config["collections"].items():
                count = int(base_count * multiplier)
                if count > 0:
                    data_breakdown[data_type_str] = count

                    # Create collection request
                    collection_request = BulkCollectionRequest(
                        collection_name=f"{request.scenario_type}_{data_type_str}_{scenario_id[:8]}",
                        description=f"{scenario_config['description']} - {data_type_str}",
                        data_types=[MockDataType(data_type_str)],
                        items_per_type={data_type_str: count},
                        total_items=count,
                        context=f"Ecosystem scenario: {request.scenario_type}",
                        store_in_doc_store=request.store_in_doc_store,
                        tags=[request.scenario_type, request.complexity, request.scale],
                        metadata={
                            "scenario_id": scenario_id,
                            "scenario_type": request.scenario_type,
                            "complexity": request.complexity,
                            "scale": request.scale,
                            "include_relationships": request.include_relationships
                        }
                    )

                    # Generate collection
                    collection_response = await self.generate_bulk_collection(collection_request)
                    stored_collections.extend(collection_response.stored_documents)

            generation_time = time.time() - start_time
            total_items = sum(data_breakdown.values())

            return EcosystemScenarioResponse(
                success=True,
                scenario_type=request.scenario_type,
                scenario_id=scenario_id,
                complexity=request.complexity,
                scale=request.scale,
                total_items=total_items,
                data_breakdown=data_breakdown,
                generation_time=generation_time,
                stored_collections=stored_collections,
                scenario_metadata={
                    "description": scenario_config["description"],
                    "scale_multiplier": scale_multiplier,
                    "complexity_multiplier": complexity_multiplier,
                    "relationships_included": request.include_relationships
                },
                created_at=datetime.now().isoformat()
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate ecosystem scenario: {str(e)}"
            )

    def get_available_scenarios(self) -> Dict[str, Any]:
        """Get available ecosystem scenarios."""
        return {
            "scenarios": {
                "code_review": {
                    "description": "Complete code review workflow with source code, analysis, and PRs",
                    "typical_data_types": ["source_code", "llm_prompt", "analysis_report", "github_pr"],
                    "complexity_levels": ["simple", "medium", "complex"],
                    "scale_options": ["small", "medium", "large"]
                },
                "documentation": {
                    "description": "Documentation generation and management workflow",
                    "typical_data_types": ["confluence_page", "api_docs", "document_collection"],
                    "complexity_levels": ["simple", "medium", "complex"],
                    "scale_options": ["small", "medium", "large"]
                },
                "analysis": {
                    "description": "Data analysis and reporting workflow",
                    "typical_data_types": ["analysis_report", "source_code", "log_entry"],
                    "complexity_levels": ["simple", "medium", "complex"],
                    "scale_options": ["small", "medium", "large"]
                }
            },
            "customization_options": {
                "complexity": ["simple", "medium", "complex"],
                "scale": ["small", "medium", "large"],
                "relationships": [True, False]
            }
        }
    
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
            "batch": "/generate/batch",
            # New enhanced endpoints
            "collections_generate": "/collections/generate",
            "collections_templates": "/collections/templates",
            "collections_list": "/collections/list",
            "scenarios_generate": "/scenarios/generate",
            "scenarios_available": "/scenarios/available",
            "scenarios_quick_start": "/scenarios/quick-start/{scenario_type}",
            "data_overview": "/data/ecosystem-overview",
            "data_export": "/data/export/{collection_id}"
        },
        "supported_types": list(MockDataType),
        "features": {
            "llm_integration": True,
            "doc_store_integration": True,
            "batch_generation": True,
            # New enhanced features
            "bulk_collections": True,
            "ecosystem_scenarios": True,
            "collection_templates": True,
            "data_relationships": True,
            "export_formats": ["json", "csv", "xml", "yaml"],
            "scenario_types": ["code_review", "documentation", "analysis"]
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

# New enhanced endpoints for bulk collections and ecosystem scenarios

@app.post("/collections/generate", response_model=BulkCollectionResponse)
async def generate_bulk_collection(request: BulkCollectionRequest):
    """Generate a bulk collection of mock data."""
    return await generator.generate_bulk_collection(request)

@app.get("/collections/templates")
async def get_collection_templates():
    """Get available collection templates and examples."""
    return {
        "templates": {
            "code_review_workflow": {
                "description": "Complete code review scenario with source code, analysis, and PRs",
                "data_types": ["source_code", "llm_prompt", "analysis_report", "github_pr", "log_entry"],
                "suggested_distribution": {
                    "source_code": 50,
                    "llm_prompt": 10,
                    "analysis_report": 5,
                    "github_pr": 3,
                    "log_entry": 20
                },
                "tags": ["code_review", "development", "testing"]
            },
            "documentation_suite": {
                "description": "Comprehensive documentation collection",
                "data_types": ["confluence_page", "api_docs", "document_collection", "user_profile"],
                "suggested_distribution": {
                    "confluence_page": 15,
                    "api_docs": 8,
                    "document_collection": 3,
                    "user_profile": 5
                },
                "tags": ["documentation", "api", "user_management"]
            },
            "analysis_workbench": {
                "description": "Data analysis and reporting environment",
                "data_types": ["analysis_report", "source_code", "log_entry", "configuration", "notification"],
                "suggested_distribution": {
                    "analysis_report": 10,
                    "source_code": 30,
                    "log_entry": 15,
                    "configuration": 3,
                    "notification": 5
                },
                "tags": ["analysis", "reporting", "monitoring"]
            },
            "ecosystem_integration": {
                "description": "Full ecosystem integration test data",
                "data_types": ["llm_prompt", "analysis_report", "source_code", "user_profile", "configuration", "notification", "log_entry"],
                "suggested_distribution": {
                    "llm_prompt": 20,
                    "analysis_report": 15,
                    "source_code": 40,
                    "user_profile": 10,
                    "configuration": 5,
                    "notification": 8,
                    "log_entry": 25
                },
                "tags": ["integration", "full_stack", "comprehensive"]
            }
        },
        "customization_options": {
            "total_items_range": [10, 10000],
            "supported_tags": ["testing", "development", "documentation", "analysis", "integration", "production"],
            "storage_options": ["doc_store_only", "memory_only", "both"]
        }
    }

@app.post("/scenarios/generate", response_model=EcosystemScenarioResponse)
async def generate_ecosystem_scenario(request: EcosystemScenarioRequest):
    """Generate a complete ecosystem scenario."""
    return await generator.generate_ecosystem_scenario(request)

@app.get("/scenarios/available")
async def get_available_scenarios():
    """Get available ecosystem scenarios."""
    return generator.get_available_scenarios()

@app.post("/scenarios/quick-start/{scenario_type}")
async def quick_start_scenario(
    scenario_type: str,
    complexity: str = "medium",
    scale: str = "small"
):
    """Quick start a predefined scenario with default settings."""
    request = EcosystemScenarioRequest(
        scenario_type=scenario_type,
        complexity=complexity,
        scale=scale,
        include_relationships=True,
        store_in_doc_store=True
    )

    return await generator.generate_ecosystem_scenario(request)

@app.get("/collections/list")
async def list_collections(limit: int = 50, offset: int = 0):
    """List generated collections (metadata only)."""
    # This would typically query a database, but for now return mock data
    return {
        "collections": [
            {
                "id": "coll_001",
                "name": "test_collection_1",
                "created_at": "2024-01-20T10:00:00Z",
                "total_items": 25,
                "data_types": ["source_code", "llm_prompt"],
                "status": "completed"
            },
            {
                "id": "coll_002",
                "name": "documentation_suite",
                "created_at": "2024-01-19T15:30:00Z",
                "total_items": 50,
                "data_types": ["confluence_page", "api_docs"],
                "status": "completed"
            }
        ],
        "total": 2,
        "limit": limit,
        "offset": offset
    }

@app.get("/collections/{collection_id}")
async def get_collection_details(collection_id: str):
    """Get detailed information about a specific collection."""
    # Mock response - in real implementation, this would query the database
    return {
        "collection_id": collection_id,
        "name": f"collection_{collection_id}",
        "description": "Mock collection details",
        "created_at": "2024-01-20T10:00:00Z",
        "total_items": 25,
        "items_by_type": {
            "source_code": 15,
            "llm_prompt": 10
        },
        "stored_documents": [f"doc_{i}" for i in range(25)],
        "metadata": {
            "tags": ["testing", "development"],
            "context": "Mock data generation"
        }
    }

@app.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str):
    """Delete a collection and its associated documents."""
    # Mock response - in real implementation, this would delete from database and doc store
    return {
        "success": True,
        "message": f"Collection {collection_id} deleted successfully",
        "deleted_documents": 25
    }

@app.get("/data/ecosystem-overview")
async def get_ecosystem_data_overview():
    """Get an overview of all generated ecosystem data."""
    return {
        "total_collections": 5,
        "total_documents": 250,
        "data_breakdown": {
            "source_code": 80,
            "llm_prompt": 45,
            "analysis_report": 30,
            "confluence_page": 25,
            "api_docs": 20,
            "github_pr": 15,
            "user_profile": 10,
            "configuration": 8,
            "notification": 12,
            "log_entry": 35
        },
        "recent_activity": [
            {
                "type": "collection_created",
                "name": "code_review_workflow",
                "timestamp": "2024-01-20T10:30:00Z",
                "items_count": 25
            },
            {
                "type": "scenario_generated",
                "name": "documentation",
                "timestamp": "2024-01-20T09:15:00Z",
                "items_count": 50
            }
        ],
        "storage_usage": {
            "doc_store_documents": 200,
            "memory_cache": 50,
            "total_size_mb": 45.2
        }
    }

@app.post("/data/export/{collection_id}")
async def export_collection_data(collection_id: str, format: str = "json"):
    """Export collection data in various formats."""
    supported_formats = ["json", "csv", "xml", "yaml"]

    if format not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: {supported_formats}"
        )

    # Mock export response
    return {
        "success": True,
        "collection_id": collection_id,
        "export_format": format,
        "export_url": f"/exports/{collection_id}.{format}",
        "file_size_mb": 12.5,
        "item_count": 25,
        "exported_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    """Run the Enhanced Mock Data Generator service directly."""
    import uvicorn
    print(f"🚀 Starting {SERVICE_TITLE} Service (v{SERVICE_VERSION})...")
    print(f"🔗 LLM Gateway: {LLM_GATEWAY_URL}")
    print(f"📄 Doc Store: {DOC_STORE_URL}")
    print("
✨ Enhanced Features Available:"    print("  🏗️  Bulk Collections - Generate large datasets with custom distributions")
    print("  🎭 Ecosystem Scenarios - Complete testing environments (code_review, documentation, analysis)")
    print("  📋 Collection Templates - Pre-configured data generation templates")
    print("  🔗 Data Relationships - Interconnected data with realistic dependencies")
    print("  📤 Export Formats - JSON, CSV, XML, YAML export capabilities")
    print("  📊 Data Overview - Comprehensive ecosystem data analytics")
    print(f"  🎯 New Data Types: {len([t for t in MockDataType if t.value not in ['confluence_page', 'github_repo', 'github_pr', 'jira_issue', 'jira_epic', 'api_docs', 'code_sample', 'workflow_data']])} additional types")
    print("
🌐 Service Endpoints:"    print(f"  📡 Health: http://localhost:{DEFAULT_PORT}/health")
    print(f"  🏗️  Collections: http://localhost:{DEFAULT_PORT}/collections/generate")
    print(f"  🎭 Scenarios: http://localhost:{DEFAULT_PORT}/scenarios/generate")
    print(f"  📊 Overview: http://localhost:{DEFAULT_PORT}/data/ecosystem-overview")
    print("
📖 API Documentation: http://localhost:{DEFAULT_PORT}/docs
"
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
