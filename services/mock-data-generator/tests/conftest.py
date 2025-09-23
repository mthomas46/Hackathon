"""Pytest configuration and shared fixtures for Mock Data Generator tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of data generation, schema validation, bulk operations, and ecosystem scenarios
within the Mock Data Generator service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta
import json

from main import (
    MockDataType, GenerationRequest, BulkCollectionRequest,
    EcosystemScenarioRequest, SimulationProjectDocsRequest,
    SimulationTimelineEventsRequest, SimulationTeamActivitiesRequest,
    SimulationPhaseDocumentsRequest, SimulationEcosystemScenarioRequest
)


# =============================================================================
# SHARED TEST FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def request_id():
    """Generate a unique request ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def correlation_id():
    """Generate a unique correlation ID for each test."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def test_timestamp():
    """Provide a consistent timestamp for testing."""
    return datetime(2024, 1, 1, 12, 0, 0)


# =============================================================================
# DOMAIN ENTITY FIXTURES
# =============================================================================

@pytest.fixture
def sample_generation_request():
    """Sample generation request."""
    return GenerationRequest(
        data_type=MockDataType.CONFLUENCE_PAGE,
        count=5,
        context="API documentation for user management service",
        parameters={
            "complexity": "medium",
            "include_code_examples": True,
            "tags": ["api", "documentation", "user-management"]
        },
        store_in_doc_store=True
    )


@pytest.fixture
def sample_bulk_collection_request():
    """Sample bulk collection request."""
    return BulkCollectionRequest(
        collection_name="ecommerce_platform_docs",
        description="Complete documentation suite for an e-commerce platform",
        data_types=[
            MockDataType.API_DOCS,
            MockDataType.USER_STORY,
            MockDataType.TECHNICAL_DESIGN,
            MockDataType.TEST_SCENARIOS
        ],
        items_per_type={
            "api_docs": 15,
            "user_story": 25,
            "technical_design": 8,
            "test_scenarios": 12
        },
        total_items=60,
        context="Modern e-commerce platform with microservices architecture",
        store_in_doc_store=True,
        tags=["ecommerce", "platform", "microservices"],
        metadata={
            "domain": "ecommerce",
            "architecture": "microservices",
            "team_size": 12,
            "timeline_months": 8
        }
    )


@pytest.fixture
def sample_ecosystem_scenario_request():
    """Sample ecosystem scenario request."""
    return EcosystemScenarioRequest(
        scenario_type="code_review",
        complexity="complex",
        scale="large",
        include_relationships=True,
        store_in_doc_store=True
    )


@pytest.fixture
def sample_simulation_project_request():
    """Sample simulation project documents request."""
    return SimulationProjectDocsRequest(
        project_name="SmartInventory",
        project_type="web_application",
        team_size=8,
        complexity="complex",
        duration_weeks=16,
        team_members=[
            {
                "name": "Alice Johnson",
                "role": "Senior Full-Stack Developer",
                "expertise": ["React", "Node.js", "PostgreSQL"]
            },
            {
                "name": "Bob Chen",
                "role": "DevOps Engineer",
                "expertise": ["Kubernetes", "AWS", "CI/CD"]
            },
            {
                "name": "Carol Williams",
                "role": "Product Manager",
                "expertise": ["Agile", "User Research", "Analytics"]
            }
        ],
        document_types=[
            "project_requirements",
            "architecture_diagram",
            "user_story",
            "technical_design",
            "test_scenarios",
            "deployment_guide"
        ],
        store_in_doc_store=True
    )


@pytest.fixture
def sample_timeline_events_request():
    """Sample timeline events request."""
    return SimulationTimelineEventsRequest(
        project_name="SmartInventory",
        timeline_phases=[
            {
                "name": "Planning",
                "duration_weeks": 2,
                "start_date": "2024-01-01",
                "deliverables": ["Project Charter", "Requirements Document"]
            },
            {
                "name": "Design",
                "duration_weeks": 4,
                "start_date": "2024-01-15",
                "deliverables": ["Architecture Diagram", "UI Mockups", "Database Schema"]
            },
            {
                "name": "Development",
                "duration_weeks": 8,
                "start_date": "2024-02-12",
                "deliverables": ["Working Software", "Unit Tests", "Integration Tests"]
            }
        ],
        current_phase="Development",
        include_past_events=True,
        include_future_events=False,
        event_types=["document_creation", "team_activity", "milestone", "decision"],
        store_in_doc_store=True
    )


@pytest.fixture
def sample_team_activities_request():
    """Sample team activities request."""
    return SimulationTeamActivitiesRequest(
        project_name="SmartInventory",
        team_members=[
            {
                "name": "Alice Johnson",
                "role": "Senior Developer",
                "productivity_score": 0.9,
                "focus_areas": ["backend", "api_design"]
            },
            {
                "name": "Bob Chen",
                "role": "DevOps Engineer",
                "productivity_score": 0.85,
                "focus_areas": ["infrastructure", "deployment"]
            },
            {
                "name": "Carol Williams",
                "role": "QA Engineer",
                "productivity_score": 0.95,
                "focus_areas": ["testing", "quality_assurance"]
            }
        ],
        activity_types=[
            "code_commit",
            "document_update",
            "meeting_notes",
            "design_decision",
            "code_review",
            "bug_report",
            "feature_request"
        ],
        time_range_days=30,
        activity_count=100,
        store_in_doc_store=True
    )


@pytest.fixture
def sample_phase_documents_request():
    """Sample phase documents request."""
    return SimulationPhaseDocumentsRequest(
        project_name="SmartInventory",
        phase_name="Development",
        phase_details={
            "phase_number": 3,
            "total_phases": 5,
            "phase_goal": "Implement core features and establish CI/CD pipeline",
            "key_deliverables": [
                "User authentication system",
                "Inventory management API",
                "Basic UI components",
                "Database integration",
                "Unit test coverage > 80%"
            ],
            "challenges": [
                "Complex business logic for inventory tracking",
                "Real-time data synchronization",
                "Scalable architecture design"
            ]
        },
        document_types=[
            "technical_design",
            "test_scenarios",
            "deployment_guide",
            "code_review_comments",
            "architecture_diagram"
        ],
        team_members=[
            {
                "name": "Alice Johnson",
                "role": "Tech Lead",
                "responsibilities": ["Architecture", "Code Review"]
            },
            {
                "name": "Bob Chen",
                "role": "DevOps Engineer",
                "responsibilities": ["CI/CD", "Infrastructure"]
            }
        ],
        store_in_doc_store=True
    )


@pytest.fixture
def sample_ecosystem_scenario_request():
    """Sample ecosystem scenario request."""
    return SimulationEcosystemScenarioRequest(
        scenario_name="complete_product_launch",
        project_config={
            "name": "SmartInventory",
            "type": "SaaS Platform",
            "team_size": 15,
            "duration_months": 6,
            "budget": 500000,
            "technology_stack": {
                "frontend": ["React", "TypeScript", "Tailwind CSS"],
                "backend": ["Node.js", "Python", "PostgreSQL"],
                "infrastructure": ["AWS", "Kubernetes", "Docker"],
                "monitoring": ["DataDog", "New Relic"]
            },
            "compliance_requirements": ["SOC2", "GDPR", "ISO27001"]
        },
        include_full_ecosystem=True,
        generate_relationships=True,
        store_in_doc_store=True
    )


@pytest.fixture
def mock_generated_document():
    """Mock generated document."""
    return {
        "id": str(uuid.uuid4()),
        "type": "api_docs",
        "title": "User Management API Documentation",
        "content": """
# User Management API

This API provides comprehensive user management functionality for the platform.

## Endpoints

### GET /users
Retrieves a list of users with optional filtering and pagination.

**Parameters:**
- `page` (integer, optional): Page number for pagination
- `limit` (integer, optional): Number of items per page (max 100)
- `status` (string, optional): Filter by user status

**Response:**
```json
{
  "users": [
    {
      "id": "123",
      "email": "user@example.com",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 5,
    "total_count": 250
  }
}
```

### POST /users
Creates a new user account.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "secure_password_123",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "timezone": "America/New_York"
  }
}
```
        """,
        "metadata": {
            "data_type": "api_docs",
            "complexity": "medium",
            "word_count": 450,
            "reading_time_minutes": 3,
            "tags": ["api", "documentation", "user-management"],
            "generated_at": datetime.now(),
            "quality_score": 0.92
        },
        "relationships": {
            "related_documents": [],
            "parent_collections": [],
            "cross_references": []
        }
    }


@pytest.fixture
def mock_bulk_collection():
    """Mock bulk collection."""
    return {
        "collection_id": str(uuid.uuid4()),
        "collection_name": "ecommerce_platform_docs",
        "description": "Complete documentation suite for an e-commerce platform",
        "total_documents": 60,
        "documents_by_type": {
            "api_docs": 15,
            "user_story": 25,
            "technical_design": 8,
            "test_scenarios": 12
        },
        "documents": [],  # Would contain the actual document objects
        "metadata": {
            "domain": "ecommerce",
            "architecture": "microservices",
            "team_size": 12,
            "timeline_months": 8,
            "generation_time_seconds": 45.2,
            "quality_score": 0.88,
            "tags": ["ecommerce", "platform", "microservices"]
        },
        "created_at": datetime.now(),
        "stored_in_doc_store": True,
        "doc_store_ids": [str(uuid.uuid4()) for _ in range(60)]
    }


@pytest.fixture
def mock_simulation_scenario():
    """Mock simulation scenario."""
    return {
        "scenario_id": str(uuid.uuid4()),
        "scenario_name": "complete_product_launch",
        "project_name": "SmartInventory",
        "total_documents": 150,
        "documents_by_category": {
            "requirements": 15,
            "architecture": 12,
            "user_stories": 35,
            "technical_designs": 25,
            "test_scenarios": 20,
            "deployment_guides": 8,
            "maintenance_docs": 10,
            "meeting_notes": 25
        },
        "timeline_events": 75,
        "team_activities": 120,
        "document_relationships": 200,
        "cross_references": 85,
        "metadata": {
            "complexity": "complex",
            "scale": "enterprise",
            "generation_time_seconds": 120.5,
            "quality_score": 0.91,
            "realism_score": 0.87
        },
        "phases": [
            {
                "name": "Planning",
                "duration_weeks": 3,
                "document_count": 20,
                "key_deliverables": ["Requirements", "Architecture Overview"]
            },
            {
                "name": "Development",
                "duration_weeks": 12,
                "document_count": 85,
                "key_deliverables": ["Working Software", "Tests", "Documentation"]
            },
            {
                "name": "Launch",
                "duration_weeks": 2,
                "document_count": 15,
                "key_deliverables": ["Deployment Guide", "User Manual"]
            }
        ],
        "created_at": datetime.now(),
        "stored_in_doc_store": True
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway for content generation."""
    mock_llm = AsyncMock()
    mock_llm.generate_content = AsyncMock(return_value={
        "content": "Generated realistic content based on the provided context and requirements.",
        "tokens_used": 150,
        "generation_time_seconds": 2.3,
        "quality_score": 0.89
    })
    mock_llm.validate_content = AsyncMock(return_value={
        "is_valid": True,
        "validation_score": 0.94,
        "issues": []
    })
    mock_llm.enhance_content = AsyncMock(return_value={
        "enhanced_content": "Enhanced and more realistic content with better structure and details.",
        "enhancement_score": 0.15,
        "enhancement_time_seconds": 1.2
    })
    return mock_llm


@pytest.fixture
def mock_doc_store():
    """Mock Document Store for persistence."""
    mock_store = AsyncMock()
    mock_store.store_document = AsyncMock(return_value={
        "document_id": str(uuid.uuid4()),
        "stored_at": datetime.now(),
        "storage_success": True
    })
    mock_store.store_documents_batch = AsyncMock(return_value={
        "document_ids": [str(uuid.uuid4()) for _ in range(10)],
        "batch_id": str(uuid.uuid4()),
        "stored_count": 10,
        "storage_success": True,
        "storage_time_seconds": 3.2
    })
    mock_store.validate_document = AsyncMock(return_value={
        "is_valid": True,
        "validation_errors": []
    })
    mock_store.get_document = AsyncMock(return_value={
        "document_id": "doc_123",
        "content": "Mock document content",
        "metadata": {"type": "api_docs"}
    })
    return mock_store


@pytest.fixture
def mock_schema_validator():
    """Mock schema validator for data structure validation."""
    mock_validator = MagicMock()
    mock_validator.validate_data_structure = MagicMock(return_value={
        "is_valid": True,
        "validation_errors": [],
        "structure_score": 0.96,
        "completeness_score": 0.92
    })
    mock_validator.validate_relationships = MagicMock(return_value={
        "relationships_valid": True,
        "relationship_errors": [],
        "relationship_score": 0.88
    })
    mock_validator.generate_schema = MagicMock(return_value={
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["id", "title", "content"]
        },
        "schema_generation_time": 0.5
    })
    return mock_validator


@pytest.fixture
def mock_content_generator():
    """Mock content generator for realistic data creation."""
    mock_generator = AsyncMock()
    mock_generator.generate_realistic_content = AsyncMock(return_value={
        "content": "Realistic and contextually appropriate content generated for testing.",
        "content_type": "documentation",
        "complexity_level": "medium",
        "word_count": 250,
        "generation_metadata": {
            "technique_used": "llm_enhanced",
            "confidence_score": 0.91,
            "processing_time_seconds": 1.8
        }
    })
    mock_generator.generate_structured_data = AsyncMock(return_value={
        "structured_data": {
            "title": "API Documentation",
            "sections": ["Overview", "Endpoints", "Examples"],
            "metadata": {"type": "api_docs", "complexity": "medium"}
        },
        "structure_score": 0.94,
        "generation_time_seconds": 1.2
    })
    mock_generator.validate_content_quality = AsyncMock(return_value={
        "quality_score": 0.87,
        "readability_score": 0.82,
        "technical_accuracy_score": 0.91,
        "completeness_score": 0.89,
        "issues": []
    })
    return mock_generator


@pytest.fixture
def mock_relationship_engine():
    """Mock relationship engine for document interconnections."""
    mock_engine = MagicMock()
    mock_engine.generate_relationships = MagicMock(return_value={
        "relationships": [
            {
                "source_document": "doc_1",
                "target_document": "doc_2",
                "relationship_type": "references",
                "strength": 0.85
            }
        ],
        "relationship_count": 5,
        "relationship_generation_time": 1.2
    })
    mock_engine.validate_relationships = MagicMock(return_value={
        "relationships_valid": True,
        "consistency_score": 0.92,
        "issues": []
    })
    mock_engine.optimize_relationships = MagicMock(return_value={
        "optimized_relationships": [],
        "optimization_score": 0.15,
        "optimization_time": 0.8
    })
    return mock_engine


@pytest.fixture
def mock_quality_assessor():
    """Mock quality assessor for generated content."""
    mock_assessor = MagicMock()
    mock_assessor.assess_content_quality = MagicMock(return_value={
        "overall_quality_score": 0.88,
        "quality_dimensions": {
            "relevance": 0.92,
            "accuracy": 0.89,
            "completeness": 0.85,
            "readability": 0.87,
            "technical_correctness": 0.90
        },
        "quality_issues": [],
        "assessment_time_seconds": 0.5
    })
    mock_assessor.generate_quality_report = MagicMock(return_value={
        "quality_report": {
            "document_id": "doc_123",
            "quality_metrics": {},
            "recommendations": ["Improve technical depth", "Add more examples"],
            "quality_score_trend": "improving"
        },
        "report_generation_time": 0.3
    })
    return mock_assessor


@pytest.fixture
def mock_simulation_engine():
    """Mock simulation engine for project simulation data."""
    mock_engine = AsyncMock()
    mock_engine.generate_project_timeline = AsyncMock(return_value={
        "timeline": [
            {
                "phase": "Planning",
                "duration_weeks": 2,
                "start_date": "2024-01-01",
                "milestones": ["Requirements Complete", "Architecture Approved"]
            }
        ],
        "timeline_complexity": "medium",
        "generation_time_seconds": 1.5
    })
    mock_engine.generate_team_dynamics = AsyncMock(return_value={
        "team_dynamics": {
            "communication_patterns": "collaborative",
            "productivity_score": 0.85,
            "conflict_resolution_effectiveness": 0.78
        },
        "dynamics_generation_time": 0.8
    })
    mock_engine.simulate_project_evolution = AsyncMock(return_value={
        "project_evolution": {
            "initial_scope": "MVP features",
            "final_scope": "Full product launch",
            "scope_changes": 3,
            "quality_improvements": 5
        },
        "evolution_simulation_time": 2.1
    })
    return mock_engine


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        "test_services": ["mock_data_generator", "llm_gateway", "doc_store"],
        "test_scenarios": [
            {"type": "single_document", "count": 50},
            {"type": "bulk_collection", "count": 10},
            {"type": "ecosystem_scenario", "count": 5},
            {"type": "simulation_project", "count": 3}
        ],
        "performance_thresholds": {
            "max_generation_time_seconds": 30,
            "min_quality_score": 0.8,
            "max_error_rate": 0.05,
            "min_throughput_docs_per_minute": 10
        },
        "data_validation_rules": {
            "required_fields_present": True,
            "data_structure_valid": True,
            "relationships_consistent": True,
            "content_realistic": True
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "llm_gateway": AsyncMock(),
        "doc_store": AsyncMock(),
        "log_collector": AsyncMock(),
        "orchestrator": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_scenarios():
    """Performance testing scenarios for data generation operations."""
    return {
        "high_volume_generation": {
            "name": "High Volume Document Generation",
            "description": "Generate large volumes of documents under time constraints",
            "target_documents": 1000,
            "time_limit_minutes": 10,
            "document_types": ["api_docs", "user_story", "technical_design"],
            "expected_throughput": 100,  # docs per minute
            "expected_quality_threshold": 0.8
        },
        "complex_ecosystem_generation": {
            "name": "Complex Ecosystem Scenario Generation",
            "description": "Generate complete project ecosystems with relationships",
            "scenarios_count": 10,
            "max_scenario_complexity": "complex",
            "include_relationships": True,
            "expected_generation_time_minutes": 5,
            "expected_relationship_accuracy": 0.9
        },
        "concurrent_bulk_operations": {
            "name": "Concurrent Bulk Operations",
            "description": "Handle multiple bulk generation requests simultaneously",
            "concurrent_requests": 5,
            "documents_per_request": 100,
            "expected_max_response_time_seconds": 60,
            "expected_success_rate": 0.95
        },
        "llm_enhanced_generation": {
            "name": "LLM-Enhanced Content Generation",
            "description": "Generate content using LLM gateway with quality validation",
            "documents_count": 50,
            "use_llm_enhancement": True,
            "expected_quality_improvement": 0.1,
            "expected_generation_time_seconds": 120
        }
    }


@pytest.fixture
def load_test_configuration():
    """Load testing configuration for mock data generator."""
    return {
        "duration_minutes": 15,
        "concurrent_users": 20,
        "requests_per_minute": 200,
        "document_generation_mix": {
            "single_documents": 0.6,
            "bulk_collections": 0.25,
            "ecosystem_scenarios": 0.1,
            "simulation_projects": 0.05
        },
        "data_type_distribution": {
            "api_docs": 0.2,
            "user_story": 0.25,
            "technical_design": 0.15,
            "test_scenarios": 0.1,
            "confluence_page": 0.1,
            "github_repo": 0.05,
            "jira_issue": 0.05,
            "code_sample": 0.05,
            "workflow_data": 0.05
        },
        "thresholds": {
            "min_success_rate": 0.9,
            "max_average_response_time_seconds": 30,
            "max_p95_response_time_seconds": 60,
            "min_quality_score": 0.75,
            "max_error_rate": 0.1
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "mock_data_generator_resilience_test",
        "duration_minutes": 20,
        "failure_injection": {
            "llm_gateway_failure": {
                "failure_mode": "intermittent",
                "failure_rate": 0.3,
                "duration_seconds": 300,
                "fallback_mode": "template_based"
            },
            "doc_store_unavailable": {
                "failure_mode": "complete_outage",
                "duration_seconds": 180,
                "impact": "storage_disabled"
            },
            "high_memory_pressure": {
                "memory_limit_mb": 256,
                "duration_seconds": 240,
                "cleanup_strategy": "aggressive"
            },
            "network_latency_spike": {
                "latency_increase_ms": 5000,
                "duration_seconds": 200,
                "affected_services": ["llm_gateway", "doc_store"]
            },
            "concurrent_request_storm": {
                "concurrent_requests": 100,
                "duration_seconds": 120,
                "request_pattern": "burst"
            }
        },
        "monitoring": {
            "metrics": [
                "generation_success_rate",
                "average_generation_time",
                "memory_usage",
                "error_rate",
                "quality_score_degradation"
            ],
            "alerts": [
                "generation_success_rate < 80%",
                "average_generation_time > 60s",
                "memory_usage > 90%",
                "error_rate > 15%"
            ],
            "data_integrity_checks": [
                "generated_content_validity",
                "document_structure_integrity",
                "relationship_consistency",
                "metadata_completeness"
            ]
        },
        "recovery_validation": {
            "services_recovery_time_seconds": 60,
            "data_integrity_restoration": True,
            "quality_score_recovery": True,
            "full_functionality_restoration": True
        }
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_llm_gateway_failure = MagicMock(return_value=True)
    mock_injector.inject_doc_store_failure = MagicMock(return_value=True)
    mock_injector.inject_memory_pressure = MagicMock(return_value=True)
    mock_injector.inject_network_latency = MagicMock(return_value=True)
    mock_injector.inject_concurrent_storm = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["llm_gateway_intermittent", "high_memory_pressure"],
        "recovery_eta_seconds": 120,
        "generation_success_rate": 0.75,
        "average_generation_time_seconds": 45,
        "memory_usage_percent": 85,
        "error_rate": 0.12
    })
    return mock_injector
