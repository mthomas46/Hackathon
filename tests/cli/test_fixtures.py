"""
CLI Test Fixtures and Mock Data

Comprehensive test data and fixtures for CLI testing including:
- Mock service responses
- Test data for various scenarios
- Helper functions for test setup
- Pre-configured test cases
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MockServiceResponse:
    """Mock HTTP response for testing"""
    status_code: int
    json_data: Optional[Dict[str, Any]] = None
    text_data: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {'Content-Type': 'application/json'}


class CLITestFixtures:
    """Comprehensive test fixtures for CLI testing"""

    @staticmethod
    def get_mock_health_response(service_name: str, status: str = "healthy") -> MockServiceResponse:
        """Generate mock health check response"""
        timestamp = datetime.now(timezone.utc).isoformat()

        health_data = {
            "service": service_name,
            "status": status,
            "timestamp": timestamp,
            "version": "1.0.0",
            "environment": "test",
            "uptime_seconds": 3600,
            "dependencies": {
                "redis": "healthy",
                "database": "healthy" if service_name != "doc_store" else "unhealthy"
            }
        }

        if status == "unhealthy":
            health_data["error"] = "Service experiencing issues"

        return MockServiceResponse(
            status_code=200 if status == "healthy" else 503,
            json_data=health_data
        )

    @staticmethod
    def get_mock_doc_store_response(operation: str) -> MockServiceResponse:
        """Generate mock doc_store responses"""
        timestamp = datetime.now(timezone.utc).isoformat()

        responses = {
            "list": {
                "status_code": 200,
                "json_data": {
                    "items": [
                        {
                            "id": "doc_001",
                            "content": "Sample document content",
                            "content_hash": "hash123",
                            "metadata": {"author": "test", "category": "test"},
                            "created_at": timestamp
                        },
                        {
                            "id": "doc_002",
                            "content": "Another document",
                            "content_hash": "hash456",
                            "metadata": {"author": "user", "category": "demo"},
                            "created_at": timestamp
                        }
                    ],
                    "total": 2,
                    "has_more": False
                }
            },
            "create": {
                "status_code": 201,
                "json_data": {
                    "id": "doc_003",
                    "content": "New document content",
                    "content_hash": "hash789",
                    "metadata": {"author": "test", "category": "new"},
                    "created_at": timestamp
                }
            },
            "search": {
                "status_code": 200,
                "json_data": {
                    "query": "sample",
                    "items": [
                        {
                            "id": "doc_001",
                            "content": "Sample document content",
                            "content_hash": "hash123",
                            "metadata": {"author": "test", "category": "test"},
                            "created_at": timestamp,
                            "relevance_score": 0.95
                        }
                    ],
                    "total": 1,
                    "has_more": False,
                    "search_time": 0.05
                }
            },
            "delete": {
                "status_code": 200,
                "json_data": {
                    "success": True,
                    "message": "Document deleted successfully",
                    "document_id": "doc_001"
                }
            },
            "error": {
                "status_code": 404,
                "json_data": {
                    "detail": "Document not found",
                    "error_code": "DOC_NOT_FOUND"
                }
            }
        }

        response_data = responses.get(operation, responses["error"])
        return MockServiceResponse(**response_data)

    @staticmethod
    def get_mock_prompt_store_response(operation: str) -> MockServiceResponse:
        """Generate mock prompt_store responses"""
        timestamp = datetime.now(timezone.utc).isoformat()

        responses = {
            "list": {
                "status_code": 200,
                "json_data": {
                    "items": [
                        {
                            "id": "prompt_001",
                            "name": "Code Review Prompt",
                            "content": "Review this code for best practices",
                            "category": "development",
                            "tags": ["code", "review"],
                            "created_at": timestamp,
                            "updated_at": timestamp
                        },
                        {
                            "id": "prompt_002",
                            "name": "Documentation Prompt",
                            "content": "Generate comprehensive documentation",
                            "category": "documentation",
                            "tags": ["docs", "api"],
                            "created_at": timestamp,
                            "updated_at": timestamp
                        }
                    ],
                    "total": 2,
                    "has_more": False
                }
            },
            "create": {
                "status_code": 201,
                "json_data": {
                    "id": "prompt_003",
                    "name": "New Test Prompt",
                    "content": "Test prompt content",
                    "category": "testing",
                    "tags": ["test", "automation"],
                    "created_at": timestamp,
                    "updated_at": timestamp
                }
            },
            "update": {
                "status_code": 200,
                "json_data": {
                    "success": True,
                    "message": "Prompt updated successfully",
                    "prompt_id": "prompt_001"
                }
            },
            "delete": {
                "status_code": 200,
                "json_data": {
                    "success": True,
                    "message": "Prompt deleted successfully",
                    "prompt_id": "prompt_001"
                }
            }
        }

        response_data = responses.get(operation, {"status_code": 404, "json_data": {"detail": "Prompt not found"}})
        return MockServiceResponse(**response_data)

    @staticmethod
    def get_mock_notification_response(operation: str) -> MockServiceResponse:
        """Generate mock notification service responses"""
        timestamp = datetime.now(timezone.utc).isoformat()

        responses = {
            "list": {
                "status_code": 200,
                "json_data": {
                    "items": [
                        {
                            "id": "notif_001",
                            "title": "System Alert",
                            "message": "High CPU usage detected",
                            "priority": "high",
                            "status": "sent",
                            "created_at": timestamp
                        },
                        {
                            "id": "notif_002",
                            "title": "Service Update",
                            "message": "New features available",
                            "priority": "normal",
                            "status": "read",
                            "created_at": timestamp
                        }
                    ],
                    "total": 2,
                    "has_more": False
                }
            },
            "send": {
                "status_code": 201,
                "json_data": {
                    "id": "notif_003",
                    "title": "Test Notification",
                    "message": "This is a test message",
                    "priority": "normal",
                    "status": "sent",
                    "created_at": timestamp
                }
            },
            "history": {
                "status_code": 200,
                "json_data": {
                    "items": [
                        {
                            "id": "notif_001",
                            "title": "System Alert",
                            "message": "High CPU usage detected",
                            "priority": "high",
                            "status": "sent",
                            "created_at": timestamp,
                            "sent_at": timestamp
                        }
                    ],
                    "total": 1,
                    "has_more": False
                }
            }
        }

        response_data = responses.get(operation, {"status_code": 404, "json_data": {"detail": "Notification not found"}})
        return MockServiceResponse(**response_data)

    @staticmethod
    def get_mock_workflow_response(operation: str) -> MockServiceResponse:
        """Generate mock workflow responses"""
        timestamp = datetime.now(timezone.utc).isoformat()

        responses = {
            "list": {
                "status_code": 200,
                "json_data": {
                    "workflows": [
                        {
                            "id": "wf_001",
                            "name": "Document Processing",
                            "description": "Process and analyze documents",
                            "status": "active",
                            "created_at": timestamp
                        },
                        {
                            "id": "wf_002",
                            "name": "Code Analysis",
                            "description": "Analyze code quality",
                            "status": "completed",
                            "created_at": timestamp
                        }
                    ],
                    "total": 2
                }
            },
            "execute": {
                "status_code": 202,
                "json_data": {
                    "workflow_id": "wf_exec_001",
                    "status": "running",
                    "message": "Workflow execution started",
                    "started_at": timestamp
                }
            },
            "status": {
                "status_code": 200,
                "json_data": {
                    "workflow_id": "wf_exec_001",
                    "status": "completed",
                    "progress": 100,
                    "started_at": timestamp,
                    "completed_at": timestamp,
                    "results": {
                        "documents_processed": 5,
                        "quality_score": 0.95
                    }
                }
            }
        }

        response_data = responses.get(operation, {"status_code": 404, "json_data": {"detail": "Workflow not found"}})
        return MockServiceResponse(**response_data)

    @staticmethod
    def get_mock_container_status(service_name: str = "test-service") -> str:
        """Generate mock docker-compose ps output"""
        return f"""NAME                                SERVICE             STATUS                      PORTS
hackathon-{service_name}-1          {service_name}        Up 2 hours (healthy)         0.0.0.0:8080->8080/tcp
hackathon-another-service-1         another-service      Up 2 hours (healthy)         0.0.0.0:8081->8081/tcp"""

    @staticmethod
    def get_mock_container_stats() -> str:
        """Generate mock docker stats output"""
        return """CONTAINER      CPU %     MEM USAGE / LIMIT     NET I/O           BLOCK I/O
abc123def     0.15%     45.2MiB / 8GiB      1.2MB / 800KB     0B / 1.2MB
def456ghi     0.08%     32.1MiB / 8GiB      800KB / 400KB     0B / 800KB"""

    @staticmethod
    def get_mock_container_logs(service_name: str) -> str:
        """Generate mock container logs"""
        return f"""{service_name}-1  | INFO:     Application startup complete
{service_name}-1  | INFO:     127.0.0.1:12345 - "GET /health HTTP/1.1" 200 OK
{service_name}-1  | INFO:     127.0.0.1:12346 - "POST /api/test HTTP/1.1" 201 OK
{service_name}-1  | WARNING:  High memory usage detected
{service_name}-1  | INFO:     127.0.0.1:12347 - "GET /status HTTP/1.1" 200 OK"""

    @staticmethod
    def get_test_service_urls() -> Dict[str, str]:
        """Get test service URL mappings"""
        return {
            "analysis-service": "http://localhost:5080",
            "orchestrator": "http://localhost:5099",
            "source-agent": "http://localhost:5085",
            "doc_store": "http://localhost:5087",
            "prompt_store": "http://localhost:5110",
            "notification-service": "http://localhost:5130",
            "llm-gateway": "http://localhost:5055",
            "frontend": "http://localhost:3000",
            "code-analyzer": "http://localhost:5025",
            "summarizer-hub": "http://localhost:5160"
        }

    @staticmethod
    def get_docker_service_urls() -> Dict[str, str]:
        """Get Docker container service URL mappings"""
        return {
            "analysis-service": "http://hackathon-analysis-service-1:5020",
            "orchestrator": "http://hackathon-orchestrator-1:5099",
            "source-agent": "http://hackathon-source-agent-1:5000",
            "doc_store": "http://hackathon-doc_store-1:5010",
            "prompt_store": "http://hackathon-prompt_store-1:5110",
            "notification-service": "http://hackathon-notification-service-1:5095",
            "llm-gateway": "http://hackathon-llm-gateway-1:5055",
            "frontend": "http://hackathon-frontend-1:5090",
            "code-analyzer": "http://hackathon-code-analyzer-1:5025",
            "summarizer-hub": "http://hackathon-summarizer-hub-1:5160"
        }

    @staticmethod
    def get_error_responses() -> Dict[str, MockServiceResponse]:
        """Get common error response fixtures"""
        return {
            "connection_error": MockServiceResponse(
                status_code=0,
                text_data="Connection refused"
            ),
            "timeout_error": MockServiceResponse(
                status_code=0,
                text_data="Request timeout"
            ),
            "server_error": MockServiceResponse(
                status_code=500,
                json_data={
                    "detail": "Internal server error",
                    "error_code": "INTERNAL_ERROR"
                }
            ),
            "not_found": MockServiceResponse(
                status_code=404,
                json_data={
                    "detail": "Resource not found",
                    "error_code": "NOT_FOUND"
                }
            ),
            "unauthorized": MockServiceResponse(
                status_code=401,
                json_data={
                    "detail": "Unauthorized access",
                    "error_code": "UNAUTHORIZED"
                }
            ),
            "bad_request": MockServiceResponse(
                status_code=400,
                json_data={
                    "detail": "Invalid request parameters",
                    "error_code": "BAD_REQUEST"
                }
            )
        }

    @staticmethod
    def get_performance_test_data() -> Dict[str, Any]:
        """Get performance testing data"""
        return {
            "small_payload": {"data": "x" * 100},
            "medium_payload": {"data": "x" * 1000},
            "large_payload": {"data": "x" * 10000},
            "concurrent_requests": 10,
            "timeout_seconds": 30,
            "expected_response_time": 2.0,  # seconds
            "max_response_time": 5.0       # seconds
        }

    @staticmethod
    def get_test_workflow_definitions() -> List[Dict[str, Any]]:
        """Get test workflow definitions"""
        return [
            {
                "name": "document_analysis",
                "description": "Analyze document content and extract insights",
                "steps": [
                    {"service": "doc_store", "action": "retrieve"},
                    {"service": "analysis-service", "action": "analyze"},
                    {"service": "summarizer-hub", "action": "summarize"}
                ]
            },
            {
                "name": "code_review",
                "description": "Review code for quality and best practices",
                "steps": [
                    {"service": "source-agent", "action": "extract"},
                    {"service": "code-analyzer", "action": "analyze"},
                    {"service": "notification-service", "action": "notify"}
                ]
            }
        ]

    @staticmethod
    def get_integration_test_scenarios() -> List[Dict[str, Any]]:
        """Get comprehensive integration test scenarios"""
        return [
            {
                "name": "health_check_all_services",
                "description": "Verify all services respond to health checks",
                "services": ["analysis-service", "orchestrator", "doc_store", "llm-gateway"],
                "expected_status": "healthy"
            },
            {
                "name": "document_lifecycle",
                "description": "Test complete document CRUD operations",
                "steps": [
                    {"action": "create", "service": "doc_store"},
                    {"action": "read", "service": "doc_store"},
                    {"action": "search", "service": "doc_store"},
                    {"action": "update", "service": "doc_store"},
                    {"action": "delete", "service": "doc_store"}
                ]
            },
            {
                "name": "workflow_execution",
                "description": "Test end-to-end workflow execution",
                "workflow": "document_analysis",
                "expected_result": "completed"
            },
            {
                "name": "container_management",
                "description": "Test container lifecycle operations",
                "operations": ["list", "restart", "logs", "stats"],
                "services": ["frontend", "doc_store"]
            }
        ]
