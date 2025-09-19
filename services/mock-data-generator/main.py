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
    # NEW: Simulation-specific document types
    PROJECT_REQUIREMENTS = "project_requirements"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    USER_STORY = "user_story"
    TECHNICAL_DESIGN = "technical_design"
    CODE_REVIEW_COMMENTS = "code_review_comments"
    TEST_SCENARIOS = "test_scenarios"
    DEPLOYMENT_GUIDE = "deployment_guide"
    MAINTENANCE_DOCS = "maintenance_docs"
    CHANGE_LOG = "change_log"
    TEAM_RETROSPECTIVE = "team_retrospective"

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

# NEW: Simulation-specific request/response models
class SimulationProjectDocsRequest(BaseModel):
    """Request model for generating project-specific documents."""
    project_name: str = Field(..., description="Name of the project")
    project_type: str = Field(default="web_application", description="Type of project (web_application, api_service, mobile_application)")
    team_size: int = Field(default=5, ge=1, le=20, description="Number of team members")
    complexity: str = Field(default="medium", description="Project complexity (simple, medium, complex)")
    duration_weeks: int = Field(default=8, ge=1, le=52, description="Project duration in weeks")
    team_members: Optional[List[Dict[str, Any]]] = Field(None, description="Team member profiles")
    document_types: List[str] = Field(default_factory=lambda: ["project_requirements", "architecture_diagram", "user_story"], description="Types of documents to generate")
    store_in_doc_store: bool = Field(default=True, description="Store generated documents in doc_store")

class SimulationTimelineEventsRequest(BaseModel):
    """Request model for generating timeline-based content."""
    project_name: str = Field(..., description="Name of the project")
    timeline_phases: List[Dict[str, Any]] = Field(..., description="Project timeline phases")
    current_phase: Optional[str] = Field(None, description="Current active phase")
    include_past_events: bool = Field(default=True, description="Include past phase events")
    include_future_events: bool = Field(default=False, description="Include future phase events")
    event_types: List[str] = Field(default_factory=lambda: ["document_creation", "team_activity", "milestone"], description="Types of events to generate")
    store_in_doc_store: bool = Field(default=True, description="Store generated content in doc_store")

class SimulationTeamActivitiesRequest(BaseModel):
    """Request model for generating team activity data."""
    project_name: str = Field(..., description="Name of the project")
    team_members: List[Dict[str, Any]] = Field(..., description="Team member profiles")
    activity_types: List[str] = Field(default_factory=lambda: ["code_commit", "document_update", "meeting_notes", "design_decision"], description="Types of activities to generate")
    time_range_days: int = Field(default=30, ge=1, le=365, description="Time range for activities in days")
    activity_count: int = Field(default=50, ge=1, le=500, description="Number of activities to generate")
    store_in_doc_store: bool = Field(default=True, description="Store generated activities in doc_store")

class SimulationPhaseDocumentsRequest(BaseModel):
    """Request model for generating phase-specific documents."""
    project_name: str = Field(..., description="Name of the project")
    phase_name: str = Field(..., description="Name of the project phase")
    phase_details: Dict[str, Any] = Field(..., description="Details about the phase")
    document_types: List[str] = Field(default_factory=lambda: ["technical_design", "test_scenarios", "deployment_guide"], description="Types of documents to generate for this phase")
    team_members: Optional[List[Dict[str, Any]]] = Field(None, description="Team members involved in this phase")
    store_in_doc_store: bool = Field(default=True, description="Store generated documents in doc_store")

class SimulationEcosystemScenarioRequest(BaseModel):
    """Request model for generating complete ecosystem scenarios."""
    scenario_name: str = Field(..., description="Name of the scenario")
    project_config: Dict[str, Any] = Field(..., description="Complete project configuration")
    include_full_ecosystem: bool = Field(default=True, description="Include all ecosystem services")
    generate_relationships: bool = Field(default=True, description="Generate document relationships and cross-references")
    store_in_doc_store: bool = Field(default=True, description="Store all generated content in doc_store")

class SimulationResponse(BaseModel):
    """Response model for simulation-specific endpoints."""
    success: bool
    simulation_type: str
    project_name: str
    generated_items: int
    document_types: List[str]
    documents_created: List[Dict[str, Any]]
    stored_documents: Optional[List[str]] = None
    generation_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

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

    # NEW: Simulation-specific generation methods

    async def generate_project_requirements(self, request: SimulationProjectDocsRequest) -> Dict[str, Any]:
        """Generate project requirements document."""
        complexity_multiplier = {"simple": 0.7, "medium": 1.0, "complex": 1.4}[request.complexity]

        requirements = {
            "title": f"{request.project_name} - Project Requirements",
            "project_name": request.project_name,
            "project_type": request.project_type,
            "version": "1.0",
            "created_date": datetime.now().isoformat(),
            "author": "Project Manager",
            "stakeholders": ["Product Owner", "Development Team", "QA Team", "DevOps Team"],
            "overview": {
                "description": f"Requirements for {request.project_name}, a {request.project_type} project",
                "objectives": [
                    "Deliver high-quality software solution",
                    "Meet business requirements and user needs",
                    "Ensure scalability and maintainability",
                    "Implement security best practices"
                ],
                "scope": {
                    "in_scope": ["Core functionality", "User interface", "API development", "Testing"],
                    "out_of_scope": ["Legacy system migration", "Third-party integrations", "Mobile applications"]
                }
            },
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "description": "User authentication and authorization system",
                    "priority": "High",
                    "acceptance_criteria": ["Users can login/logout", "Role-based access control", "Session management"]
                },
                {
                    "id": "FR-002",
                    "description": "Data management and CRUD operations",
                    "priority": "High",
                    "acceptance_criteria": ["Create, read, update, delete data", "Data validation", "Error handling"]
                },
                {
                    "id": "FR-003",
                    "description": "User interface and user experience",
                    "priority": "Medium",
                    "acceptance_criteria": ["Responsive design", "Intuitive navigation", "Accessibility compliance"]
                }
            ],
            "non_functional_requirements": {
                "performance": {
                    "response_time": "< 2 seconds for 95% of requests",
                    "throughput": f"{int(100 * complexity_multiplier)} requests per second",
                    "availability": "99.9% uptime"
                },
                "security": {
                    "authentication": "OAuth 2.0 / JWT",
                    "data_encryption": "AES-256 encryption at rest and in transit",
                    "audit_logging": "Comprehensive security event logging"
                },
                "scalability": {
                    "concurrent_users": f"{int(1000 * complexity_multiplier)} concurrent users",
                    "data_growth": "Support for 10x data growth over 2 years",
                    "elastic_scaling": "Auto-scaling based on demand"
                }
            },
            "constraints": {
                "technical": ["Must use Python/FastAPI backend", "PostgreSQL database", "Docker containerization"],
                "business": [f"Project timeline: {request.duration_weeks} weeks", f"Team size: {request.team_size} members"],
                "regulatory": ["GDPR compliance", "Data privacy requirements"]
            },
            "assumptions": [
                "Development team has required technical skills",
                "Infrastructure resources are available",
                "Stakeholder availability for requirements validation",
                "Third-party services will be available and stable"
            ],
            "risks": [
                {
                    "description": "Technical complexity might impact timeline",
                    "probability": "Medium",
                    "impact": "High",
                    "mitigation": "Regular technical reviews and prototyping"
                },
                {
                    "description": "Requirements changes during development",
                    "probability": "High",
                    "impact": "Medium",
                    "mitigation": "Agile development with change management process"
                }
            ],
            "acceptance_criteria": [
                "All functional requirements implemented and tested",
                "Performance requirements met",
                "Security requirements validated",
                "Documentation completed and reviewed",
                "User acceptance testing passed"
            ]
        }

        return requirements

    async def generate_architecture_diagram(self, request: SimulationProjectDocsRequest) -> Dict[str, Any]:
        """Generate architecture diagram document."""
        architecture = {
            "title": f"{request.project_name} - System Architecture",
            "project_name": request.project_name,
            "version": "1.0",
            "created_date": datetime.now().isoformat(),
            "author": "System Architect",
            "architecture_type": "Microservices Architecture",
            "overview": {
                "description": f"System architecture for {request.project_name} {request.project_type} project",
                "principles": [
                    "Microservices architecture for scalability",
                    "API-first design approach",
                    "Event-driven communication",
                    "Container-based deployment"
                ]
            },
            "components": {
                "frontend": {
                    "technology": "React/TypeScript",
                    "responsibility": "User interface and user experience",
                    "scaling": "Horizontal scaling with load balancer"
                },
                "api_gateway": {
                    "technology": "FastAPI/Python",
                    "responsibility": "Request routing, authentication, rate limiting",
                    "scaling": "Multiple instances with load balancer"
                },
                "user_service": {
                    "technology": "FastAPI/Python + PostgreSQL",
                    "responsibility": "User management, authentication, profiles",
                    "scaling": "Database read replicas, service instances"
                },
                "business_service": {
                    "technology": "FastAPI/Python + PostgreSQL",
                    "responsibility": "Core business logic and workflows",
                    "scaling": "Database sharding, service instances"
                },
                "notification_service": {
                    "technology": "FastAPI/Python + Redis",
                    "responsibility": "Email, SMS, push notifications",
                    "scaling": "Message queue-based processing"
                }
            },
            "data_flow": [
                {
                    "step": 1,
                    "description": "User request comes through load balancer",
                    "components": ["Load Balancer", "API Gateway"]
                },
                {
                    "step": 2,
                    "description": "API Gateway authenticates and routes request",
                    "components": ["API Gateway", "Target Service"]
                },
                {
                    "step": 3,
                    "description": "Service processes request and accesses database",
                    "components": ["Target Service", "PostgreSQL Database"]
                },
                {
                    "step": 4,
                    "description": "Response returned through API Gateway",
                    "components": ["Target Service", "API Gateway", "Frontend"]
                }
            ],
            "infrastructure": {
                "deployment": "Docker containers orchestrated with Kubernetes",
                "monitoring": "Prometheus + Grafana for metrics and alerting",
                "logging": "Centralized logging with ELK stack",
                "ci_cd": "GitHub Actions for automated testing and deployment",
                "security": "OAuth 2.0, JWT tokens, encrypted communications"
            },
            "scalability_considerations": {
                "horizontal_scaling": "All services designed for horizontal scaling",
                "database_scaling": "Read replicas, connection pooling, query optimization",
                "caching_strategy": "Redis for session and application caching",
                "cdn_integration": "Static asset delivery and API response caching"
            },
            "security_architecture": {
                "authentication": "OAuth 2.0 with JWT tokens",
                "authorization": "Role-based access control (RBAC)",
                "data_protection": "AES-256 encryption at rest and in transit",
                "network_security": "VPC isolation, security groups, WAF",
                "monitoring": "Security event logging and alerting"
            },
            "performance_requirements": {
                "response_time": "< 500ms for API calls, < 2s for page loads",
                "throughput": "1000+ requests per second",
                "availability": "99.9% uptime SLA",
                "concurrent_users": "10,000+ simultaneous users"
            },
            "disaster_recovery": {
                "backup_strategy": "Daily database backups with point-in-time recovery",
                "failover": "Multi-region deployment with automatic failover",
                "data_retention": "7-year audit trail, configurable data retention",
                "recovery_time_objective": "4 hours for critical systems",
                "recovery_point_objective": "1 hour data loss tolerance"
            }
        }

        return architecture

    async def generate_user_story(self, request: SimulationProjectDocsRequest, story_index: int) -> Dict[str, Any]:
        """Generate a user story document."""
        story_templates = [
            {
                "title": "User Registration and Login",
                "role": "As a new user",
                "goal": "I want to create an account and log in",
                "benefit": "So that I can access the system securely",
                "acceptance_criteria": [
                    "User can register with email and password",
                    "Email verification is required",
                    "User can login with valid credentials",
                    "Password reset functionality works",
                    "Session management is secure"
                ]
            },
            {
                "title": "Dashboard Overview",
                "role": "As a registered user",
                "goal": "I want to see my personalized dashboard",
                "benefit": "So that I can quickly access important information",
                "acceptance_criteria": [
                    "Dashboard shows recent activities",
                    "Key metrics are prominently displayed",
                    "Quick actions are easily accessible",
                    "Dashboard is responsive on mobile devices",
                    "Data refreshes automatically"
                ]
            },
            {
                "title": "Data Management",
                "role": "As a content creator",
                "goal": "I want to create and manage my data",
                "benefit": "So that I can organize and maintain my information",
                "acceptance_criteria": [
                    "User can create new data entries",
                    "Data validation prevents invalid entries",
                    "User can edit existing data",
                    "Bulk operations are supported",
                    "Data export functionality works"
                ]
            }
        ]

        template = story_templates[story_index % len(story_templates)]

        user_story = {
            "title": template["title"],
            "id": "04d",
            "story_type": "User Story",
            "created_date": datetime.now().isoformat(),
            "author": "Product Owner",
            "status": "Ready for Development",
            "priority": "High",
            "estimate": "5 story points",
            "epic": f"{request.project_name} Core Features",
            "description": f"{template['role']}, {template['goal']}, {template['benefit']}",
            "acceptance_criteria": template["acceptance_criteria"],
            "business_value": "High",
            "risk_level": "Low",
            "dependencies": [],
            "attachments": ["wireframes.png", "user_research.pdf"],
            "comments": [
                {
                    "author": "Product Owner",
                    "date": datetime.now().isoformat(),
                    "comment": "This is a critical user journey that needs to be implemented first."
                },
                {
                    "author": "UX Designer",
                    "date": (datetime.now()).isoformat(),
                    "comment": "Wireframes attached. Please review the user flow."
                }
            ]
        }

        return user_story

    async def generate_phase_events(self, request: SimulationTimelineEventsRequest, phase: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate timeline events for a specific phase."""
        events = []

        # Generate document creation events
        if phase.get("documents_created", 0) > 0:
            for i in range(min(phase["documents_created"], 5)):
                event = {
                    "type": "document_created",
                    "title": f"Document Created: {phase['name']} Documentation {i+1}",
                    "description": f"Created documentation for {phase['name']} phase",
                    "phase": phase["name"],
                    "timestamp": (datetime.now()).isoformat(),
                    "category": "documentation",
                    "importance": "medium"
                }
                events.append(event)

        # Generate team activity events
        if phase.get("team_activities", 0) > 0:
            activity_types = ["code_commit", "design_review", "meeting", "testing", "deployment"]
            for i in range(min(phase["team_activities"], 10)):
                activity_type = activity_types[i % len(activity_types)]
                event = {
                    "type": "team_activity",
                    "title": f"Team Activity: {activity_type.title()} Session",
                    "description": f"Team conducted {activity_type} activities in {phase['name']} phase",
                    "phase": phase["name"],
                    "timestamp": (datetime.now()).isoformat(),
                    "category": "team",
                    "activity_type": activity_type,
                    "importance": "low"
                }
                events.append(event)

        # Generate milestone events
        if phase.get("milestones", 0) > 0:
            for i in range(min(phase["milestones"], 3)):
                event = {
                    "type": "milestone",
                    "title": f"Milestone Achieved: {phase['name']} Phase {i+1}",
                    "description": f"Important milestone completed in {phase['name']} phase",
                    "phase": phase["name"],
                    "timestamp": (datetime.now()).isoformat(),
                    "category": "milestone",
                    "importance": "high"
                }
                events.append(event)

        return events

    async def generate_team_activity(self, request: SimulationTeamActivitiesRequest, activity_index: int) -> Dict[str, Any]:
        """Generate a team activity record."""
        activity_types = {
            "code_commit": {
                "title": "Code Changes Committed",
                "description": "Team member committed code changes to repository",
                "details": ["Fixed bug in authentication logic", "Added input validation", "Updated documentation"]
            },
            "document_update": {
                "title": "Documentation Updated",
                "description": "Technical documentation was reviewed and updated",
                "details": ["Updated API documentation", "Added code examples", "Fixed typos and formatting"]
            },
            "meeting_notes": {
                "title": "Team Meeting Held",
                "description": "Sprint planning meeting with development team",
                "details": ["Discussed sprint goals", "Assigned user stories", "Identified blockers"]
            },
            "design_decision": {
                "title": "Architecture Decision Made",
                "description": "Team decided on technology stack and architecture approach",
                "details": ["Selected PostgreSQL for database", "Chose FastAPI for backend", "Decided on microservices approach"]
            }
        }

        activity_keys = list(activity_types.keys())
        activity_key = activity_keys[activity_index % len(activity_keys)]
        activity_template = activity_types[activity_key]

        # Select random team member
        team_member = request.team_members[activity_index % len(request.team_members)] if request.team_members else {"name": "Team Member", "role": "Developer"}

        activity = {
            "title": activity_template["title"],
            "description": activity_template["description"],
            "type": activity_key,
            "timestamp": (datetime.now()).isoformat(),
            "author": team_member.get("name", "Team Member"),
            "role": team_member.get("role", "Developer"),
            "project": request.project_name,
            "details": activity_template["details"],
            "impact": "Medium",
            "category": "development",
            "tags": [activity_key, "team", request.project_name.lower().replace(" ", "_")],
            "metadata": {
                "activity_index": activity_index,
                "team_size": len(request.team_members),
                "project_phase": "development"
            }
        }

        return activity

    async def generate_technical_design(self, request: SimulationPhaseDocumentsRequest) -> Dict[str, Any]:
        """Generate technical design document for a phase."""
        design_doc = {
            "title": f"Technical Design: {request.phase_name} Phase",
            "phase": request.phase_name,
            "version": "1.0",
            "created_date": datetime.now().isoformat(),
            "author": "Technical Lead",
            "reviewers": ["System Architect", "Senior Developer", "DevOps Engineer"],
            "overview": {
                "purpose": f"Technical design for implementing {request.phase_name} phase functionality",
                "scope": f"Complete technical implementation of {request.phase_name} requirements",
                "assumptions": [
                    "Development team has required technical skills",
                    "Infrastructure components are available",
                    "Third-party services are accessible"
                ]
            },
            "architecture_decisions": [
                {
                    "decision": "Database Schema Design",
                    "rationale": "Normalized schema for data integrity and performance",
                    "alternatives_considered": ["Denormalized schema", "Document database"],
                    "consequences": "Better data consistency, slightly more complex queries"
                },
                {
                    "decision": "API Design Patterns",
                    "rationale": "RESTful APIs with proper HTTP methods and status codes",
                    "alternatives_considered": ["GraphQL", "RPC"],
                    "consequences": "Standardized interfaces, easier integration"
                },
                {
                    "decision": "Authentication Mechanism",
                    "rationale": "JWT tokens with refresh token rotation",
                    "alternatives_considered": ["Session-based auth", "API keys"],
                    "consequences": "Stateless authentication, better scalability"
                }
            ],
            "component_design": {
                "api_layer": {
                    "technology": "FastAPI with Pydantic models",
                    "responsibilities": ["Request validation", "Response formatting", "Error handling"],
                    "design_patterns": ["Dependency injection", "Middleware pipeline"]
                },
                "business_logic": {
                    "technology": "Python service classes",
                    "responsibilities": ["Business rules", "Data processing", "Workflow orchestration"],
                    "design_patterns": ["Strategy pattern", "Factory pattern"]
                },
                "data_layer": {
                    "technology": "SQLAlchemy ORM with PostgreSQL",
                    "responsibilities": ["Data persistence", "Query optimization", "Transaction management"],
                    "design_patterns": ["Repository pattern", "Unit of Work"]
                }
            },
            "data_model": {
                "entities": [
                    {
                        "name": "User",
                        "attributes": ["id", "email", "name", "role", "created_at", "updated_at"],
                        "relationships": ["has_many: sessions", "has_many: activities"]
                    },
                    {
                        "name": "Project",
                        "attributes": ["id", "name", "description", "status", "created_at"],
                        "relationships": ["belongs_to: owner", "has_many: tasks"]
                    }
                ],
                "constraints": [
                    "Email addresses must be unique",
                    "Project names must be unique per user",
                    "Soft delete for audit trail preservation"
                ]
            },
            "api_endpoints": [
                {
                    "path": "/api/v1/projects",
                    "method": "GET",
                    "description": "List user projects",
                    "response_format": "ProjectList",
                    "authentication": "Required"
                },
                {
                    "path": "/api/v1/projects",
                    "method": "POST",
                    "description": "Create new project",
                    "request_format": "ProjectCreate",
                    "response_format": "Project",
                    "authentication": "Required"
                }
            ],
            "security_considerations": {
                "authentication": "JWT-based authentication with role-based access",
                "authorization": "Permission-based access control",
                "input_validation": "Comprehensive input sanitization and validation",
                "rate_limiting": "API rate limiting to prevent abuse",
                "logging": "Security event logging for audit trail"
            },
            "performance_considerations": {
                "caching_strategy": "Redis caching for frequently accessed data",
                "database_optimization": "Proper indexing and query optimization",
                "async_processing": "Background job processing for heavy operations",
                "monitoring": "Performance metrics and alerting"
            },
            "testing_strategy": {
                "unit_tests": "Individual component testing with mocks",
                "integration_tests": "API endpoint testing with test database",
                "performance_tests": "Load testing and bottleneck identification",
                "security_tests": "Vulnerability scanning and penetration testing"
            },
            "deployment_plan": {
                "environment_setup": "Docker containers with environment-specific configuration",
                "database_migration": "Automated schema migrations with rollback capability",
                "rollback_strategy": "Blue-green deployment with instant rollback",
                "monitoring_setup": "Application and infrastructure monitoring"
            }
        }

        return design_doc

    async def generate_test_scenarios(self, request: SimulationPhaseDocumentsRequest) -> Dict[str, Any]:
        """Generate test scenarios document for a phase."""
        test_scenarios = {
            "title": f"Test Scenarios: {request.phase_name} Phase",
            "phase": request.phase_name,
            "version": "1.0",
            "created_date": datetime.now().isoformat(),
            "author": "QA Lead",
            "reviewers": ["Product Owner", "Development Team", "DevOps Team"],
            "overview": {
                "purpose": f"Comprehensive test scenarios for {request.phase_name} phase validation",
                "scope": "Functional, integration, and performance testing",
                "testing_levels": ["Unit", "Integration", "System", "Acceptance"]
            },
            "test_categories": {
                "functional_tests": [
                    {
                        "scenario_id": "FT-001",
                        "title": "User Registration Flow",
                        "description": "Test complete user registration process",
                        "preconditions": ["User is on registration page"],
                        "test_steps": [
                            "Enter valid email and password",
                            "Click register button",
                            "Verify email confirmation sent",
                            "Confirm email address",
                            "Verify account activation"
                        ],
                        "expected_result": "User account created and activated",
                        "test_data": "valid_email@example.com, password123",
                        "priority": "High"
                    },
                    {
                        "scenario_id": "FT-002",
                        "title": "Data CRUD Operations",
                        "description": "Test create, read, update, delete operations",
                        "preconditions": ["User is logged in", "Has create permissions"],
                        "test_steps": [
                            "Navigate to data management page",
                            "Create new data entry",
                            "Verify data appears in list",
                            "Edit existing data entry",
                            "Delete data entry",
                            "Verify data removed from list"
                        ],
                        "expected_result": "All CRUD operations work correctly",
                        "test_data": "Sample data entries with various field types",
                        "priority": "High"
                    }
                ],
                "integration_tests": [
                    {
                        "scenario_id": "IT-001",
                        "title": "API-Service Integration",
                        "description": "Test API communication with backend services",
                        "preconditions": ["API service is running", "Database is available"],
                        "test_steps": [
                            "Send API request to create resource",
                            "Verify backend service processes request",
                            "Check database for new record",
                            "Verify API response format",
                            "Test error handling for invalid requests"
                        ],
                        "expected_result": "Seamless API-service integration",
                        "test_data": "Valid and invalid API payloads",
                        "priority": "High"
                    }
                ],
                "performance_tests": [
                    {
                        "scenario_id": "PT-001",
                        "title": "Concurrent User Load",
                        "description": "Test system performance under concurrent user load",
                        "preconditions": ["Load testing tools configured", "Monitoring enabled"],
                        "test_steps": [
                            "Set up load testing scenario (100 concurrent users)",
                            "Execute test for 5 minutes",
                            "Monitor response times and error rates",
                            "Check resource utilization (CPU, memory)",
                            "Analyze performance bottlenecks"
                        ],
                        "expected_result": "System handles load within performance requirements",
                        "test_data": "100 concurrent user simulation",
                        "priority": "Medium"
                    }
                ],
                "security_tests": [
                    {
                        "scenario_id": "ST-001",
                        "title": "Authentication Bypass",
                        "description": "Test for authentication bypass vulnerabilities",
                        "preconditions": ["Security testing tools available"],
                        "test_steps": [
                            "Attempt login with invalid credentials",
                            "Try to access protected resources without authentication",
                            "Test session timeout handling",
                            "Attempt SQL injection in login form",
                            "Test cross-site scripting (XSS) vulnerabilities"
                        ],
                        "expected_result": "All authentication bypass attempts fail",
                        "test_data": "Various attack payloads and invalid credentials",
                        "priority": "High"
                    }
                ]
            },
            "test_environment": {
                "development": {
                    "purpose": "Unit and integration testing",
                    "data_setup": "Minimal test data set",
                    "automation_level": "Fully automated"
                },
                "staging": {
                    "purpose": "System and acceptance testing",
                    "data_setup": "Production-like data set",
                    "automation_level": "Semi-automated"
                },
                "production": {
                    "purpose": "Smoke and regression testing",
                    "data_setup": "Anonymized production data",
                    "automation_level": "Automated smoke tests"
                }
            },
            "test_data_management": {
                "data_generation": "Automated test data generation scripts",
                "data_cleanup": "Automated cleanup after test execution",
                "data_privacy": "PII masking and anonymization",
                "data_versioning": "Version control for test data sets"
            },
            "automation_framework": {
                "unit_testing": "pytest with coverage reporting",
                "api_testing": "HTTP client with response validation",
                "ui_testing": "Selenium with page object model",
                "performance_testing": "Locust for load testing",
                "ci_cd_integration": "Automated test execution in pipeline"
            },
            "success_criteria": [
                "All high-priority test scenarios pass",
                "Test automation coverage > 80%",
                "Performance requirements met",
                "Zero critical security vulnerabilities",
                "Test execution time < 30 minutes"
            ]
        }

        return test_scenarios

    async def generate_deployment_guide(self, request: SimulationPhaseDocumentsRequest) -> Dict[str, Any]:
        """Generate deployment guide document for a phase."""
        deployment_guide = {
            "title": f"Deployment Guide: {request.phase_name} Phase",
            "phase": request.phase_name,
            "version": "1.0",
            "created_date": datetime.now().isoformat(),
            "author": "DevOps Engineer",
            "reviewers": ["Development Team", "System Administrator", "Security Team"],
            "overview": {
                "purpose": f"Complete deployment instructions for {request.phase_name} phase",
                "scope": "Development, staging, and production environments",
                "target_audience": ["Developers", "DevOps engineers", "System administrators"]
            },
            "prerequisites": {
                "system_requirements": {
                    "operating_system": "Ubuntu 20.04 LTS or CentOS 8+",
                    "memory": "4GB RAM minimum, 8GB recommended",
                    "disk_space": "20GB free space",
                    "network": "Stable internet connection"
                },
                "software_dependencies": [
                    "Docker 20.10+",
                    "Docker Compose 2.0+",
                    "Git 2.25+",
                    "Python 3.9+",
                    "PostgreSQL 13+"
                ],
                "access_requirements": [
                    "SSH access to deployment server",
                    "Database admin privileges",
                    "Docker registry access",
                    "Cloud platform credentials (AWS/GCP/Azure)"
                ]
            },
            "environment_setup": {
                "development": {
                    "setup_commands": [
                        "git clone <repository-url>",
                        "cd <project-directory>",
                        "cp .env.example .env",
                        "docker-compose -f docker-compose.dev.yml up -d"
                    ],
                    "verification_steps": [
                        "Check container status: docker ps",
                        "Verify API health: curl http://localhost:8000/health",
                        "Check logs: docker-compose logs -f"
                    ]
                },
                "staging": {
                    "deployment_method": "Blue-green deployment",
                    "rollback_strategy": "Instant rollback to previous version",
                    "monitoring_setup": "Prometheus + Grafana dashboards"
                },
                "production": {
                    "deployment_method": "Rolling deployment with zero downtime",
                    "scaling_strategy": "Horizontal pod autoscaling",
                    "backup_strategy": "Automated daily backups with retention"
                }
            },
            "configuration_management": {
                "environment_variables": {
                    "DATABASE_URL": "postgresql://user:password@localhost:5432/dbname",
                    "SECRET_KEY": "your-secret-key-here",
                    "DEBUG": "false",
                    "ALLOWED_HOSTS": "yourdomain.com,api.yourdomain.com"
                },
                "configuration_files": [
                    ".env - Environment variables",
                    "config.yaml - Application configuration",
                    "docker-compose.yml - Container orchestration",
                    "nginx.conf - Web server configuration"
                ],
                "secrets_management": {
                    "method": "Docker secrets or external vault (HashiCorp Vault)",
                    "rotation_policy": "Automatic rotation every 30 days",
                    "access_control": "Role-based access to secrets"
                }
            },
            "database_setup": {
                "schema_migration": {
                    "tool": "Alembic for SQLAlchemy",
                    "commands": [
                        "alembic upgrade head",
                        "alembic revision --autogenerate -m 'Initial schema'",
                        "alembic downgrade -1 (for rollback)"
                    ]
                },
                "initial_data": {
                    "seed_data": "Automated data seeding scripts",
                    "admin_user": "Default admin user creation",
                    "lookup_tables": "Reference data population"
                },
                "backup_recovery": {
                    "backup_schedule": "Daily at 2 AM",
                    "retention_policy": "30 days for daily, 1 year for monthly",
                    "recovery_procedure": "Point-in-time recovery available"
                }
            },
            "deployment_procedures": {
                "pre_deployment": [
                    "Run automated tests: pytest",
                    "Build Docker images: docker build -t myapp:latest .",
                    "Run security scan: docker scan myapp:latest",
                    "Update documentation and change logs"
                ],
                "deployment_execution": [
                    "Create deployment branch: git checkout -b deployment/v1.2.3",
                    "Update version numbers in configuration",
                    "Push deployment branch to trigger CI/CD",
                    "Monitor deployment progress in dashboard",
                    "Verify deployment success with health checks"
                ],
                "post_deployment": [
                    "Run smoke tests against deployed environment",
                    "Update monitoring dashboards",
                    "Notify stakeholders of successful deployment",
                    "Schedule post-deployment review meeting",
                    "Archive deployment artifacts"
                ]
            },
            "monitoring_setup": {
                "application_monitoring": {
                    "health_endpoints": "/health, /metrics, /status",
                    "log_aggregation": "ELK stack (Elasticsearch, Logstash, Kibana)",
                    "performance_monitoring": "Response times, error rates, throughput"
                },
                "infrastructure_monitoring": {
                    "system_metrics": "CPU, memory, disk, network utilization",
                    "container_monitoring": "Docker container health and resource usage",
                    "database_monitoring": "Connection pools, query performance, backup status"
                },
                "alerting": {
                    "critical_alerts": "Service down, database unavailable, security breach",
                    "warning_alerts": "High CPU usage, slow response times, disk space low",
                    "notification_channels": "Email, Slack, SMS for critical alerts"
                }
            },
            "troubleshooting": {
                "common_issues": [
                    {
                        "issue": "Container fails to start",
                        "symptoms": "docker ps shows container in 'Exited' state",
                        "diagnosis": "Check logs: docker logs <container-id>",
                        "solution": "Fix configuration errors, check resource limits"
                    },
                    {
                        "issue": "Database connection fails",
                        "symptoms": "Application logs show connection timeout errors",
                        "diagnosis": "Verify DATABASE_URL, check network connectivity",
                        "solution": "Update connection string, check firewall rules"
                    },
                    {
                        "issue": "High memory usage",
                        "symptoms": "Container restarts due to OOM killer",
                        "diagnosis": "Monitor memory usage with docker stats",
                        "solution": "Increase memory limits, optimize application code"
                    }
                ],
                "debug_mode": {
                    "enable_debug": "Set DEBUG=true in environment variables",
                    "debug_logging": "Set LOG_LEVEL=DEBUG for verbose logging",
                    "remote_debugging": "Attach debugger to running container"
                },
                "support_contacts": {
                    "development_team": "dev-team@company.com",
                    "devops_team": "devops@company.com",
                    "infrastructure_team": "infra@company.com"
                }
            },
            "rollback_procedures": {
                "immediate_rollback": {
                    "trigger_conditions": "Critical functionality broken, security vulnerability",
                    "procedure": "Deploy previous version immediately",
                    "notification": "Alert all stakeholders of rollback"
                },
                "graceful_rollback": {
                    "trigger_conditions": "Performance degradation, minor bugs",
                    "procedure": "Gradual traffic shift to previous version",
                    "monitoring": "Monitor error rates and performance during rollback"
                },
                "data_rollback": {
                    "database_changes": "Use migration rollback scripts",
                    "file_changes": "Git revert for configuration changes",
                    "cache_invalidation": "Clear application and CDN caches"
                }
            }
        }

        return deployment_guide

    async def generate_ecosystem_scenario(self, request: SimulationEcosystemScenarioRequest) -> List[Dict[str, Any]]:
        """Generate a complete ecosystem scenario with multiple interconnected documents."""
        scenario_documents = []

        # Generate core project documents
        project_config = request.project_config

        # 1. Project Requirements Document
        requirements_doc = {
            "type": "project_requirements",
            "title": f"{request.scenario_name} - Project Requirements",
            "content": {
                "project_name": request.scenario_name,
                "objectives": project_config.get("objectives", []),
                "stakeholders": project_config.get("stakeholders", []),
                "success_criteria": project_config.get("success_criteria", [])
            },
            "metadata": {
                "scenario_id": request.scenario_name,
                "document_type": "requirements",
                "complexity": project_config.get("complexity", "medium")
            }
        }
        scenario_documents.append(requirements_doc)

        # 2. Architecture Document
        architecture_doc = {
            "type": "architecture_diagram",
            "title": f"{request.scenario_name} - System Architecture",
            "content": {
                "architecture_type": "Microservices",
                "components": project_config.get("components", []),
                "data_flow": project_config.get("data_flow", []),
                "technologies": project_config.get("technologies", [])
            },
            "metadata": {
                "scenario_id": request.scenario_name,
                "document_type": "architecture",
                "complexity": project_config.get("complexity", "medium")
            }
        }
        scenario_documents.append(architecture_doc)

        # 3. Generate multiple user stories
        for i in range(min(5, len(project_config.get("user_stories", [1, 2, 3, 4, 5])))):
            user_story_doc = {
                "type": "user_story",
                "title": f"User Story {i+1}: {request.scenario_name}",
                "content": {
                    "story_id": "04d",
                    "role": "As a user",
                    "goal": f"I want to {project_config.get('user_stories', ['login', 'manage data', 'view reports', 'export data', 'collaborate'])[i]}",
                    "benefit": "So that I can achieve my objectives efficiently",
                    "acceptance_criteria": [
                        f"Feature {i+1} is implemented",
                        f"Feature {i+1} meets requirements",
                        f"Feature {i+1} is tested"
                    ]
                },
                "metadata": {
                    "scenario_id": request.scenario_name,
                    "document_type": "user_story",
                    "story_number": i + 1
                }
            }
            scenario_documents.append(user_story_doc)

        # 4. Technical Design Document
        design_doc = {
            "type": "technical_design",
            "title": f"{request.scenario_name} - Technical Design",
            "content": {
                "architecture_decisions": project_config.get("decisions", []),
                "component_design": project_config.get("components", []),
                "data_model": project_config.get("data_model", {}),
                "api_endpoints": project_config.get("api_endpoints", [])
            },
            "metadata": {
                "scenario_id": request.scenario_name,
                "document_type": "technical_design",
                "complexity": project_config.get("complexity", "medium")
            }
        }
        scenario_documents.append(design_doc)

        # 5. Test Scenarios Document
        test_doc = {
            "type": "test_scenarios",
            "title": f"{request.scenario_name} - Test Scenarios",
            "content": {
                "test_categories": {
                    "functional_tests": project_config.get("functional_tests", []),
                    "integration_tests": project_config.get("integration_tests", []),
                    "performance_tests": project_config.get("performance_tests", [])
                },
                "test_environment": project_config.get("test_environment", {}),
                "automation_framework": project_config.get("automation_framework", {})
            },
            "metadata": {
                "scenario_id": request.scenario_name,
                "document_type": "test_scenarios",
                "complexity": project_config.get("complexity", "medium")
            }
        }
        scenario_documents.append(test_doc)

        # 6. Deployment Guide
        deployment_doc = {
            "type": "deployment_guide",
            "title": f"{request.scenario_name} - Deployment Guide",
            "content": {
                "environment_setup": project_config.get("environments", {}),
                "configuration_management": project_config.get("configuration", {}),
                "deployment_procedures": project_config.get("deployment", []),
                "monitoring_setup": project_config.get("monitoring", {})
            },
            "metadata": {
                "scenario_id": request.scenario_name,
                "document_type": "deployment_guide",
                "complexity": project_config.get("complexity", "medium")
            }
        }
        scenario_documents.append(deployment_doc)

        # Add cross-references if requested
        if request.generate_relationships:
            for doc in scenario_documents:
                doc["relationships"] = self._generate_document_relationships(doc, scenario_documents)

        return scenario_documents

    def _generate_document_relationships(self, document: Dict[str, Any], all_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate cross-document relationships and references."""
        relationships = []

        doc_type = document["type"]
        doc_title = document["title"]

        # Define relationship patterns based on document type
        relationship_patterns = {
            "project_requirements": [
                {"type": "references", "target_type": "architecture_diagram", "description": "Defines system requirements"},
                {"type": "references", "target_type": "user_story", "description": "Basis for user stories"},
                {"type": "validated_by", "target_type": "test_scenarios", "description": "Requirements validation"}
            ],
            "architecture_diagram": [
                {"type": "implements", "target_type": "technical_design", "description": "Technical implementation"},
                {"type": "references", "target_type": "project_requirements", "description": "Architecture requirements"},
                {"type": "deployed_via", "target_type": "deployment_guide", "description": "Deployment architecture"}
            ],
            "user_story": [
                {"type": "derived_from", "target_type": "project_requirements", "description": "Requirements basis"},
                {"type": "implemented_in", "target_type": "technical_design", "description": "Technical implementation"},
                {"type": "validated_by", "target_type": "test_scenarios", "description": "Acceptance testing"}
            ],
            "technical_design": [
                {"type": "implements", "target_type": "architecture_diagram", "description": "Architecture implementation"},
                {"type": "references", "target_type": "user_story", "description": "Feature implementation"},
                {"type": "deployed_via", "target_type": "deployment_guide", "description": "Deployment configuration"}
            ],
            "test_scenarios": [
                {"type": "validates", "target_type": "project_requirements", "description": "Requirements validation"},
                {"type": "tests", "target_type": "technical_design", "description": "Implementation testing"},
                {"type": "references", "target_type": "user_story", "description": "Acceptance criteria testing"}
            ],
            "deployment_guide": [
                {"type": "deploys", "target_type": "architecture_diagram", "description": "Architecture deployment"},
                {"type": "configures", "target_type": "technical_design", "description": "Technical configuration"},
                {"type": "references", "target_type": "test_scenarios", "description": "Deployment testing"}
            ]
        }

        # Generate relationships based on patterns
        if doc_type in relationship_patterns:
            for pattern in relationship_patterns[doc_type]:
                # Find matching target documents
                for target_doc in all_documents:
                    if target_doc["type"] == pattern["target_type"] and target_doc != document:
                        relationship = {
                            "type": pattern["type"],
                            "target_document": target_doc["title"],
                            "target_type": target_doc["type"],
                            "description": pattern["description"],
                            "strength": "strong"
                        }
                        relationships.append(relationship)

        return relationships

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
            "scenario_types": ["code_review", "documentation", "analysis"],
            # NEW: Simulation-specific features
            "simulation_document_generation": True,
            "project_context_awareness": True,
            "timeline_based_content": True,
            "team_activity_simulation": True,
            "phase_specific_documents": True,
            "ecosystem_scenario_generation": True
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

# NEW: Simulation-specific endpoints

@app.post("/simulation/project-docs", response_model=SimulationResponse)
async def generate_project_documents(request: SimulationProjectDocsRequest):
    """Generate project-specific documents with context awareness."""
    start_time = time.time()

    try:
        documents_created = []
        stored_documents = []

        # Generate project requirements document
        if "project_requirements" in request.document_types:
            req_doc = await generator.generate_project_requirements(request)
            documents_created.append(req_doc)
            if request.store_in_doc_store:
                doc_id = await generator.store_in_doc_store(req_doc, "project_requirements")
                if doc_id:
                    stored_documents.append(doc_id)

        # Generate architecture diagram
        if "architecture_diagram" in request.document_types:
            arch_doc = await generator.generate_architecture_diagram(request)
            documents_created.append(arch_doc)
            if request.store_in_doc_store:
                doc_id = await generator.store_in_doc_store(arch_doc, "architecture_diagram")
                if doc_id:
                    stored_documents.append(doc_id)

        # Generate user stories
        if "user_story" in request.document_types:
            for i in range(min(10, request.team_size * 3)):  # Generate multiple user stories
                story_doc = await generator.generate_user_story(request, i)
                documents_created.append(story_doc)
                if request.store_in_doc_store:
                    doc_id = await generator.store_in_doc_store(story_doc, "user_story")
                    if doc_id:
                        stored_documents.append(doc_id)

        generation_time = time.time() - start_time

        return SimulationResponse(
            success=True,
            simulation_type="project_docs",
            project_name=request.project_name,
            generated_items=len(documents_created),
            document_types=request.document_types,
            documents_created=documents_created,
            stored_documents=stored_documents if stored_documents else None,
            generation_time=generation_time,
            metadata={
                "project_type": request.project_type,
                "team_size": request.team_size,
                "complexity": request.complexity,
                "duration_weeks": request.duration_weeks
            }
        )

    except Exception as e:
        return SimulationResponse(
            success=False,
            simulation_type="project_docs",
            project_name=request.project_name,
            generated_items=0,
            document_types=request.document_types,
            documents_created=[],
            generation_time=time.time() - start_time,
            metadata={"error": str(e)}
        )

@app.post("/simulation/timeline-events", response_model=SimulationResponse)
async def generate_timeline_events(request: SimulationTimelineEventsRequest):
    """Generate timeline-based content and events."""
    start_time = time.time()

    try:
        documents_created = []
        stored_documents = []

        # Generate timeline events based on phases
        for phase in request.timeline_phases:
            if request.include_past_events or phase.get("status") == "current":
                # Generate phase-specific events
                phase_events = await generator.generate_phase_events(request, phase)
                documents_created.extend(phase_events)

                if request.store_in_doc_store:
                    for event in phase_events:
                        doc_id = await generator.store_in_doc_store(event, "timeline_event")
                        if doc_id:
                            stored_documents.append(doc_id)

        generation_time = time.time() - start_time

        return SimulationResponse(
            success=True,
            simulation_type="timeline_events",
            project_name=request.project_name,
            generated_items=len(documents_created),
            document_types=["timeline_event"],
            documents_created=documents_created,
            stored_documents=stored_documents if stored_documents else None,
            generation_time=generation_time,
            metadata={
                "phase_count": len(request.timeline_phases),
                "include_past": request.include_past_events,
                "include_future": request.include_future_events,
                "current_phase": request.current_phase
            }
        )

    except Exception as e:
        return SimulationResponse(
            success=False,
            simulation_type="timeline_events",
            project_name=request.project_name,
            generated_items=0,
            document_types=["timeline_event"],
            documents_created=[],
            generation_time=time.time() - start_time,
            metadata={"error": str(e)}
        )

@app.post("/simulation/team-activities", response_model=SimulationResponse)
async def generate_team_activities(request: SimulationTeamActivitiesRequest):
    """Generate team activity data and interactions."""
    start_time = time.time()

    try:
        documents_created = []
        stored_documents = []

        # Generate team activities
        for i in range(request.activity_count):
            activity = await generator.generate_team_activity(request, i)
            documents_created.append(activity)

            if request.store_in_doc_store:
                doc_id = await generator.store_in_doc_store(activity, "team_activity")
                if doc_id:
                    stored_documents.append(doc_id)

        generation_time = time.time() - start_time

        return SimulationResponse(
            success=True,
            simulation_type="team_activities",
            project_name=request.project_name,
            generated_items=len(documents_created),
            document_types=["team_activity"],
            documents_created=documents_created,
            stored_documents=stored_documents if stored_documents else None,
            generation_time=generation_time,
            metadata={
                "team_size": len(request.team_members),
                "activity_types": request.activity_types,
                "time_range_days": request.time_range_days,
                "activities_generated": request.activity_count
            }
        )

    except Exception as e:
        return SimulationResponse(
            success=False,
            simulation_type="team_activities",
            project_name=request.project_name,
            generated_items=0,
            document_types=["team_activity"],
            documents_created=[],
            generation_time=time.time() - start_time,
            metadata={"error": str(e)}
        )

@app.post("/simulation/phase-documents", response_model=SimulationResponse)
async def generate_phase_documents(request: SimulationPhaseDocumentsRequest):
    """Generate documents specific to a project phase."""
    start_time = time.time()

    try:
        documents_created = []
        stored_documents = []

        # Generate phase-specific documents
        for doc_type in request.document_types:
            if doc_type == "technical_design":
                doc = await generator.generate_technical_design(request)
                documents_created.append(doc)
            elif doc_type == "test_scenarios":
                doc = await generator.generate_test_scenarios(request)
                documents_created.append(doc)
            elif doc_type == "deployment_guide":
                doc = await generator.generate_deployment_guide(request)
                documents_created.append(doc)

            if request.store_in_doc_store:
                doc_id = await generator.store_in_doc_store(doc, doc_type)
                if doc_id:
                    stored_documents.append(doc_id)

        generation_time = time.time() - start_time

        return SimulationResponse(
            success=True,
            simulation_type="phase_documents",
            project_name=request.project_name,
            generated_items=len(documents_created),
            document_types=request.document_types,
            documents_created=documents_created,
            stored_documents=stored_documents if stored_documents else None,
            generation_time=generation_time,
            metadata={
                "phase_name": request.phase_name,
                "team_members_involved": len(request.team_members) if request.team_members else 0
            }
        )

    except Exception as e:
        return SimulationResponse(
            success=False,
            simulation_type="phase_documents",
            project_name=request.project_name,
            generated_items=0,
            document_types=request.document_types,
            documents_created=[],
            generation_time=time.time() - start_time,
            metadata={"error": str(e)}
        )

@app.post("/simulation/ecosystem-scenario", response_model=SimulationResponse)
async def generate_ecosystem_scenario(request: SimulationEcosystemScenarioRequest):
    """Generate a complete ecosystem scenario with all services."""
    start_time = time.time()

    try:
        documents_created = []
        stored_documents = []

        # Generate comprehensive ecosystem scenario
        scenario_docs = await generator.generate_ecosystem_scenario(request)
        documents_created.extend(scenario_docs)

        if request.store_in_doc_store:
            for doc in scenario_docs:
                doc_id = await generator.store_in_doc_store(doc, doc.get("type", "ecosystem_scenario"))
                if doc_id:
                    stored_documents.append(doc_id)

        generation_time = time.time() - start_time

        return SimulationResponse(
            success=True,
            simulation_type="ecosystem_scenario",
            project_name=request.scenario_name,
            generated_items=len(documents_created),
            document_types=["ecosystem_scenario"],
            documents_created=documents_created,
            stored_documents=stored_documents if stored_documents else None,
            generation_time=generation_time,
            metadata={
                "include_full_ecosystem": request.include_full_ecosystem,
                "generate_relationships": request.generate_relationships,
                "scenario_documents": len(scenario_docs)
            }
        )

    except Exception as e:
        return SimulationResponse(
            success=False,
            simulation_type="ecosystem_scenario",
            project_name=request.scenario_name,
            generated_items=0,
            document_types=["ecosystem_scenario"],
            documents_created=[],
            generation_time=time.time() - start_time,
            metadata={"error": str(e)}
        )

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
