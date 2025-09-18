"""Mock Data Generator Service - LLM-Integrated Data Generation.

This service generates realistic mock data for testing the LLM Documentation Ecosystem.
Uses LLM capabilities to create contextually appropriate mock documents for:
- Confluence pages and documentation
- GitHub repositories and pull requests
- Jira issues and epics
- API documentation and code samples

The service integrates with the LLM Gateway for intelligent content generation
and with the Doc Store for persistence during workflow execution.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum

# Shared service imports
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ValidationException, ServiceException
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, generate_id, clean_string
from services.shared.logging import fire_and_forget
from services.shared.clients import ServiceClients

# Service configuration
SERVICE_NAME = "mock-data-generator"
SERVICE_TITLE = "Mock Data Generator"
SERVICE_VERSION = "1.0.0"


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
    data_type: MockDataType = Field(..., description="Type of mock data to generate")
    count: int = Field(1, ge=1, le=50, description="Number of items to generate")
    topic: str = Field(..., description="Topic/theme for the generated data")
    complexity: str = Field("medium", description="Complexity level: simple, medium, complex")
    include_metadata: bool = Field(True, description="Include metadata in response")
    workflow_id: Optional[str] = Field(None, description="Workflow ID for tracking")
    persist_to_doc_store: bool = Field(False, description="Save generated data to doc store")


class MockDataGenerator:
    """LLM-integrated mock data generation service."""

    def __init__(self):
        self.clients = ServiceClients()
        self.llm_gateway_url = "http://llm-gateway:5055"
        self.doc_store_url = "http://doc_store:5087"

        # Templates for different data types
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load generation templates for different data types."""
        return {
            "confluence_page": {
                "title_template": "Documentation: {topic} - {aspect}",
                "content_structure": [
                    "# {topic} Documentation",
                    "## Overview",
                    "## Implementation Details",
                    "## Best Practices",
                    "## Examples",
                    "## Related Links"
                ]
            },
            "github_repo": {
                "name_template": "{topic}-{aspect}-service",
                "description_template": "A comprehensive {topic} service for {aspect} management",
                "readme_sections": ["Overview", "Features", "Installation", "Usage", "API", "Contributing"]
            },
            "jira_issue": {
                "summary_template": "{action} {topic} {component} - {issue_type}",
                "description_template": "As a {user_type}, I need to {action} {topic} {component} so that {benefit}",
                "priority_levels": ["Lowest", "Low", "Medium", "High", "Highest"]
            }
        }

    async def generate_mock_data(self, request: GenerationRequest) -> Dict[str, Any]:
        """Generate mock data using LLM integration."""
        try:
            generated_items = []

            for i in range(request.count):
                item = await self._generate_single_item(request, i)
                generated_items.append(item)

                # Persist to doc store if requested
                if request.persist_to_doc_store:
                    await self._persist_to_doc_store(item, request.workflow_id)

            # Log generation completion
            fire_and_forget(
                "info",
                f"Generated {len(generated_items)} mock {request.data_type.value} items",
                SERVICE_NAME,
                {"workflow_id": request.workflow_id, "topic": request.topic}
            )

            return {
                "success": True,
                "data_type": request.data_type.value,
                "count": len(generated_items),
                "items": generated_items,
                "metadata": {
                    "topic": request.topic,
                    "complexity": request.complexity,
                    "generated_at": utc_now().isoformat(),
                    "workflow_id": request.workflow_id
                }
            }

        except Exception as e:
            fire_and_forget(
                "error",
                f"Failed to generate mock data: {str(e)}",
                SERVICE_NAME,
                {"data_type": request.data_type.value, "topic": request.topic}
            )
            raise ServiceException(
                f"Failed to generate mock data: {str(e)}",
                error_code=ErrorCodes.INTERNAL_ERROR
            )

    async def _generate_single_item(self, request: GenerationRequest, index: int) -> Dict[str, Any]:
        """Generate a single mock data item using LLM."""
        try:
            # Create LLM prompt for generation
            prompt = self._create_generation_prompt(request, index)

            # Call LLM Gateway for content generation
            llm_response = await self.clients.post_json(
                f"{self.llm_gateway_url}/query",
                {
                    "prompt": prompt,
                    "provider": "ollama",  # Use Ollama for cost-effective generation
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )

            if not llm_response.get("success"):
                raise ServiceException("LLM generation failed")

            # Parse and structure the generated content
            generated_content = llm_response["response"]
            structured_item = await self._structure_generated_content(
                request.data_type, generated_content, request.topic, index
            )

            return structured_item

        except Exception as e:
            fire_and_forget(
                "error",
                f"Failed to generate single item: {str(e)}",
                SERVICE_NAME
            )
            raise

    def _create_generation_prompt(self, request: GenerationRequest, index: int) -> str:
        """Create LLM prompt for data generation."""
        base_prompts = {
            MockDataType.CONFLUENCE_PAGE: f"""
            Generate a realistic Confluence documentation page about: {request.topic}
            Include:
            - Professional title
            - Comprehensive overview section
            - Implementation details
            - Best practices
            - Code examples
            - Links to related documentation
            Make it sound like real enterprise documentation.
            """,

            MockDataType.GITHUB_REPO: f"""
            Generate a realistic GitHub repository description and README for: {request.topic}
            Include:
            - Repository name
            - Description
            - Features list
            - Installation instructions
            - Usage examples
            - API documentation
            Make it sound like a real open-source project.
            """,

            MockDataType.JIRA_ISSUE: f"""
            Generate a realistic Jira issue/ticket for: {request.topic}
            Include:
            - Issue summary
            - Detailed description
            - Acceptance criteria
            - Priority level
            - Assignee information
            Make it sound like a real software development task.
            """,

            MockDataType.API_DOCS: f"""
            Generate realistic API documentation for: {request.topic}
            Include:
            - Endpoint specifications
            - Request/response examples
            - Authentication details
            - Error handling
            - Rate limiting information
            Make it look like real API documentation.
            """
        }

        complexity_modifier = {
            "simple": "Keep it straightforward and basic.",
            "medium": "Include moderate detail and examples.",
            "complex": "Make it comprehensive with advanced features and edge cases."
        }

        prompt = base_prompts.get(request.data_type, f"Generate realistic content about: {request.topic}")
        prompt += f"\n\nComplexity level: {complexity_modifier[request.complexity]}"
        prompt += f"\n\nFormat the response as structured data that can be easily parsed."

        return prompt

    async def _structure_generated_content(
        self,
        data_type: MockDataType,
        raw_content: str,
        topic: str,
        index: int
    ) -> Dict[str, Any]:
        """Structure the LLM-generated content into appropriate format."""
        base_structure = {
            "id": generate_id(),
            "data_type": data_type.value,
            "topic": topic,
            "generated_at": utc_now().isoformat(),
            "index": index,
            "content": raw_content
        }

        # Add type-specific structure
        if data_type == MockDataType.CONFLUENCE_PAGE:
            base_structure.update({
                "title": f"{topic} Documentation - Page {index + 1}",
                "space": "Engineering",
                "author": f"user{index + 1}@company.com",
                "last_modified": utc_now().isoformat(),
                "labels": ["documentation", topic.lower(), "api"]
            })

        elif data_type == MockDataType.GITHUB_REPO:
            base_structure.update({
                "name": f"{topic.lower()}-service-{index + 1}",
                "full_name": f"company/{topic.lower()}-service-{index + 1}",
                "description": raw_content[:200] + "...",
                "language": "Python",
                "stars": 45 + index * 5,
                "forks": 12 + index * 2,
                "created_at": (utc_now() - timedelta(days=index * 7)).isoformat()
            })

        elif data_type == MockDataType.JIRA_ISSUE:
            base_structure.update({
                "key": f"PROJ-{1000 + index}",
                "summary": f"{topic} Implementation - Task {index + 1}",
                "status": "In Progress",
                "priority": "Medium",
                "assignee": f"developer{index + 1}@company.com",
                "reporter": f"product.manager@company.com"
            })

        return base_structure

    async def _persist_to_doc_store(self, item: Dict[str, Any], workflow_id: Optional[str]):
        """Persist generated item to document store."""
        try:
            doc_data = {
                "title": item.get("title", f"Mock {item['data_type']} - {item['topic']}"),
                "content": json.dumps(item, indent=2),
                "content_type": "application/json",
                "tags": [item["data_type"], item["topic"], "mock-data"],
                "metadata": {
                    "generated_by": SERVICE_NAME,
                    "workflow_id": workflow_id,
                    "generation_time": utc_now().isoformat(),
                    "data_type": item["data_type"]
                }
            }

            response = await self.clients.post_json(
                f"{self.doc_store_url}/documents",
                doc_data
            )

            if response.get("success"):
                item["doc_store_id"] = response.get("document_id")

        except Exception as e:
            fire_and_forget(
                "warning",
                f"Failed to persist to doc store: {str(e)}",
                SERVICE_NAME,
                {"item_id": item.get("id")}
            )

    async def get_generation_history(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get generation history for tracking and analytics."""
        try:
            # This would typically query a database, but for now return mock data
            return {
                "success": True,
                "history": [],
                "stats": {
                    "total_generated": 0,
                    "by_type": {},
                    "recent_workflows": []
                }
            }
        except Exception as e:
            raise ServiceException(
                f"Failed to get generation history: {str(e)}",
                error_code=ErrorCodes.INTERNAL_ERROR
            )


# FastAPI Application
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="LLM-integrated mock data generation for ecosystem testing"
)

# Initialize service
generator = MockDataGenerator()


@app.post("/generate")
async def generate_mock_data(request: GenerationRequest) -> Dict[str, Any]:
    """Generate mock data for testing purposes."""
    try:
        result = await generator.generate_mock_data(request)
        return create_success_response(
            data=result,
            message=f"Generated {result['count']} mock {request.data_type.value} items"
        )
    except Exception as e:
        return create_error_response(
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.post("/generate/workflow-data")
async def generate_workflow_test_data() -> Dict[str, Any]:
    """Generate a complete set of mock data for workflow testing."""
    try:
        # Generate comprehensive test data set
        workflow_data = {
            "confluence_pages": [],
            "github_repos": [],
            "jira_issues": [],
            "api_docs": []
        }

        # Generate sample data for each type
        test_topic = "Authentication Service"

        for data_type in [MockDataType.CONFLUENCE_PAGE, MockDataType.GITHUB_REPO,
                         MockDataType.JIRA_ISSUE, MockDataType.API_DOCS]:
            request = GenerationRequest(
                data_type=data_type,
                count=2,
                topic=test_topic,
                complexity="medium",
                workflow_id=generate_id(),
                persist_to_doc_store=True
            )

            result = await generator.generate_mock_data(request)
            workflow_data[f"{data_type.value}s"] = result["items"]

        return create_success_response(
            data=workflow_data,
            message="Generated complete workflow test dataset"
        )
    except Exception as e:
        return create_error_response(
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.get("/history")
async def get_generation_history(workflow_id: Optional[str] = None) -> Dict[str, Any]:
    """Get generation history and statistics."""
    try:
        result = await generator.get_generation_history(workflow_id)
        return create_success_response(
            data=result,
            message="Retrieved generation history"
        )
    except Exception as e:
        return create_error_response(
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get service capabilities and supported data types."""
    capabilities = {
        "supported_data_types": [dt.value for dt in MockDataType],
        "complexity_levels": ["simple", "medium", "complex"],
        "max_items_per_request": 50,
        "llm_integration": True,
        "doc_store_integration": True,
        "workflow_tracking": True
    }

    return create_success_response(
        data=capabilities,
        message="Retrieved service capabilities"
    )


# Register health endpoints
register_health_endpoints(app, SERVICE_NAME)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5065,
        reload=True,
        log_level="info"
    )
