"""Pytest configuration and shared fixtures for Prompt Store Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of prompt management, versioning, A/B testing, analytics, and AI-powered optimization.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta

from core.entities import Prompt, PromptVersion, PromptRelationship, PromptTag
from core.models import PromptContent, PromptMetadata, ABTest, ABTestResult


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
def sample_prompt():
    """Sample Prompt entity."""
    return Prompt(
        id=str(uuid.uuid4()),
        name="Document Analysis Prompt",
        description="A comprehensive prompt for analyzing technical documents",
        content="""Analyze the following document and provide:
1. Key insights and main topics
2. Technical complexity assessment
3. Potential applications or use cases
4. Recommendations for improvement

Document: {document_content}

Please structure your response clearly with sections.""",
        category="analysis",
        tags=["technical", "analysis", "documentation"],
        metadata=PromptMetadata(
            author="john.doe@company.com",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            language="en",
            model_compatibility=["gpt-4", "gpt-3.5-turbo", "claude-2"],
            token_count=150,
            estimated_cost_per_use=0.002,
            performance_metrics={
                "avg_response_quality": 0.87,
                "avg_response_time_ms": 2500,
                "usage_count": 1250,
                "success_rate": 0.94
            }
        ),
        version_id=str(uuid.uuid4()),
        relationships=[],
        status="published",
        access_control={
            "owner": "john.doe@company.com",
            "readers": ["team@company.com"],
            "writers": ["john.doe@company.com"],
            "public": False
        },
        ab_test_id=None,
        optimization_score=0.87
    )


@pytest.fixture
def sample_prompt_version():
    """Sample PromptVersion entity."""
    return PromptVersion(
        id=str(uuid.uuid4()),
        prompt_id=str(uuid.uuid4()),
        version_number=2,
        name="Enhanced Document Analysis v2",
        content="""Perform a comprehensive analysis of the provided document:

## Analysis Requirements:
1. **Key Insights**: Extract main topics and core concepts
2. **Technical Assessment**: Evaluate complexity and technical depth
3. **Applications**: Identify potential use cases and applications
4. **Recommendations**: Suggest improvements and optimizations

## Document Content:
{document_content}

## Response Format:
Please provide a structured analysis with clear headings and actionable insights.""",
        change_summary="Enhanced structure, added detailed requirements, improved formatting",
        change_type="enhancement",
        created_by="jane.smith@company.com",
        created_at=datetime.now(),
        token_count=180,
        model_used="gpt-4",
        performance_baseline={
            "quality_score": 0.89,
            "response_time_ms": 2800,
            "cost_per_use": 0.0025
        },
        is_current=False,
        parent_version_id=str(uuid.uuid4()),
        ab_test_variant=None
    )


@pytest.fixture
def sample_prompt_relationship():
    """Sample PromptRelationship entity."""
    return PromptRelationship(
        id=str(uuid.uuid4()),
        source_prompt_id=str(uuid.uuid4()),
        target_prompt_id=str(uuid.uuid4()),
        relationship_type="extends",
        strength=0.85,
        bidirectional=False,
        created_by="system",
        created_at=datetime.now(),
        metadata={
            "context": "analysis_enhancement",
            "compatibility_score": 0.85,
            "shared_variables": ["document_content", "analysis_depth"],
            "discovered_via": "content_analysis"
        }
    )


@pytest.fixture
def sample_prompt_tag():
    """Sample PromptTag entity."""
    return PromptTag(
        id=str(uuid.uuid4()),
        name="document-analysis",
        display_name="Document Analysis",
        category="functionality",
        color="#4A90E2",
        description="Prompts designed for analyzing documents and extracting insights",
        usage_count=89,
        created_by="admin",
        created_at=datetime.now(),
        is_system_tag=False,
        synonyms=["doc-analysis", "content-analysis", "document-insights"]
    )


@pytest.fixture
def sample_ab_test():
    """Sample ABTest entity."""
    return ABTest(
        id=str(uuid.uuid4()),
        name="Document Analysis Prompt Optimization",
        description="Testing different prompt structures for document analysis",
        prompt_id=str(uuid.uuid4()),
        variants=[
            {
                "variant_id": str(uuid.uuid4()),
                "name": "Structured Analysis",
                "content": "Analyze this document with structured sections...",
                "weight": 50,
                "is_control": True
            },
            {
                "variant_id": str(uuid.uuid4()),
                "name": "Free-form Analysis",
                "content": "Provide a comprehensive analysis of this document...",
                "weight": 50,
                "is_control": False
            }
        ],
        status="running",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now() + timedelta(days=7),
        target_sample_size=1000,
        current_sample_size=456,
        metrics=[
            "response_quality",
            "response_time",
            "user_satisfaction",
            "cost_efficiency"
        ],
        created_by="data.scientist@company.com",
        created_at=datetime.now(),
        significance_threshold=0.05,
        early_stopping_enabled=True
    )


@pytest.fixture
def sample_ab_test_result():
    """Sample ABTestResult entity."""
    return ABTestResult(
        id=str(uuid.uuid4()),
        ab_test_id=str(uuid.uuid4()),
        variant_id=str(uuid.uuid4()),
        metric_name="response_quality",
        metric_value=0.89,
        sample_size=456,
        confidence_interval=(0.85, 0.93),
        statistical_significance=0.02,
        measured_at=datetime.now(),
        metadata={
            "model_used": "gpt-4",
            "average_response_time_ms": 2450,
            "cost_per_response": 0.0023
        }
    )


@pytest.fixture
def sample_prompt_content():
    """Sample PromptContent for content processing."""
    return PromptContent(
        prompt_id=str(uuid.uuid4()),
        content="""You are an expert document analyst. Analyze the following document and provide structured insights.

Document: {document_content}

Your analysis should include:
1. Main topics and themes
2. Key insights and findings
3. Technical complexity level
4. Potential applications
5. Recommendations for improvement

Please format your response with clear headings and be comprehensive yet concise.""",
        content_type="text/plain",
        encoding="utf-8",
        processed_content={
            "tokens": 120,
            "sentences": 8,
            "paragraphs": 4,
            "variables": ["document_content"],
            "instructions": ["analyze", "structure", "comprehensive", "concise"]
        },
        extracted_metadata={
            "title": "Expert Document Analysis",
            "purpose": "Document analysis and insights extraction",
            "complexity_level": "intermediate",
            "target_models": ["gpt-4", "claude-2"],
            "estimated_tokens": 120
        },
        quality_metrics={
            "clarity_score": 0.92,
            "completeness_score": 0.88,
            "instruction_clarity": 0.95,
            "variable_usage": 0.90,
            "overall_quality": 0.91
        }
    )


@pytest.fixture
def sample_bulk_operation():
    """Sample bulk operation data for prompts."""
    return {
        "operation_id": str(uuid.uuid4()),
        "operation_type": "bulk_prompt_update",
        "prompts": [
            {
                "id": str(uuid.uuid4()),
                "name": f"Analysis Prompt {i}",
                "category": "analysis",
                "tags": ["bulk", f"batch_{i//10}"]
            }
            for i in range(50)
        ],
        "configuration": {
            "validate_prompts": True,
            "update_metadata": True,
            "create_versions": True,
            "batch_size": 10,
            "concurrent_batches": 5
        },
        "status": "processing",
        "progress": {
            "total_prompts": 50,
            "processed_prompts": 35,
            "successful_updates": 32,
            "failed_updates": 3,
            "estimated_completion_time": datetime.now() + timedelta(minutes=8)
        },
        "errors": [
            {"prompt_index": 15, "error": "Invalid prompt syntax"},
            {"prompt_index": 27, "error": "Missing required variables"},
            {"prompt_index": 42, "error": "Content too long"}
        ]
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_repository():
    """Mock prompt repository for data persistence."""
    mock_repo = AsyncMock()
    mock_repo.save_prompt = AsyncMock(return_value=str(uuid.uuid4()))
    mock_repo.get_prompt_by_id = AsyncMock(return_value=None)
    mock_repo.list_prompts = AsyncMock(return_value=[])
    mock_repo.update_prompt = AsyncMock(return_value=True)
    mock_repo.delete_prompt = AsyncMock(return_value=True)
    mock_repo.search_prompts = AsyncMock(return_value=[])
    mock_repo.get_prompt_versions = AsyncMock(return_value=[])
    mock_repo.save_version = AsyncMock(return_value=str(uuid.uuid4()))
    return mock_repo


@pytest.fixture
def mock_cache():
    """Mock caching service for performance optimization."""
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=True)
    mock_cache.delete = AsyncMock(return_value=1)
    mock_cache.exists = AsyncMock(return_value=False)
    mock_cache.clear = AsyncMock(return_value=True)
    return mock_cache


@pytest.fixture
def mock_event_bus():
    """Mock event bus for domain events."""
    mock_bus = AsyncMock()
    mock_bus.publish = AsyncMock(return_value=True)
    mock_bus.subscribe = AsyncMock(return_value=True)
    mock_bus.unsubscribe = AsyncMock(return_value=True)
    return mock_bus


@pytest.fixture
def mock_ai_service():
    """Mock AI service for prompt optimization and analysis."""
    mock_ai = AsyncMock()
    mock_ai.optimize_prompt = AsyncMock(return_value={
        "optimized_content": "Enhanced prompt content...",
        "improvement_score": 0.15,
        "optimization_suggestions": ["Add more structure", "Include examples"]
    })
    mock_ai.analyze_prompt_quality = AsyncMock(return_value={
        "clarity_score": 0.88,
        "completeness_score": 0.92,
        "effectiveness_score": 0.85,
        "overall_quality": 0.88
    })
    mock_ai.generate_prompt_variants = AsyncMock(return_value=[
        {"content": "Variant 1 content", "expected_improvement": 0.1},
        {"content": "Variant 2 content", "expected_improvement": 0.08}
    ])
    mock_ai.predict_prompt_performance = AsyncMock(return_value={
        "estimated_quality": 0.87,
        "estimated_cost": 0.0025,
        "estimated_time": 2400
    })
    return mock_ai


@pytest.fixture
def mock_ab_testing_service():
    """Mock A/B testing service."""
    mock_ab = AsyncMock()
    mock_ab.create_ab_test = AsyncMock(return_value=str(uuid.uuid4()))
    mock_ab.get_ab_test_status = AsyncMock(return_value={
        "status": "running",
        "current_sample_size": 456,
        "target_sample_size": 1000,
        "leader_variant": "variant_a",
        "confidence_level": 0.89
    })
    mock_ab.record_test_result = AsyncMock(return_value=True)
    mock_ab.calculate_test_statistics = AsyncMock(return_value={
        "winner": "variant_a",
        "confidence": 0.95,
        "improvement_percentage": 12.5,
        "statistical_significance": 0.01
    })
    return mock_ab


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service for prompt performance tracking."""
    mock_analytics = AsyncMock()
    mock_analytics.record_usage = AsyncMock(return_value=True)
    mock_analytics.get_prompt_metrics = AsyncMock(return_value={
        "usage_count": 1250,
        "avg_response_time": 2450,
        "avg_cost_per_use": 0.0023,
        "success_rate": 0.94,
        "quality_score_trend": [0.85, 0.87, 0.89, 0.88]
    })
    mock_analytics.generate_performance_report = AsyncMock(return_value={
        "period": "last_30_days",
        "total_usage": 1250,
        "performance_trends": {"quality": "improving", "cost": "stable"},
        "recommendations": ["Consider A/B testing", "Optimize for cost"]
    })
    return mock_analytics


@pytest.fixture
def mock_notification_service():
    """Mock notification service for prompt events."""
    mock_notification = AsyncMock()
    mock_notification.send_notification = AsyncMock(return_value=True)
    mock_notification.subscribe_to_events = AsyncMock(return_value=True)
    return mock_notification


@pytest.fixture
def mock_validation_service():
    """Mock validation service for prompt quality checks."""
    mock_validation = AsyncMock()
    mock_validation.validate_prompt = AsyncMock(return_value={
        "is_valid": True,
        "warnings": [],
        "suggestions": ["Consider adding more examples"]
    })
    mock_validation.validate_prompt_syntax = AsyncMock(return_value={
        "syntax_valid": True,
        "issues": []
    })
    return mock_validation


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "database_url": "sqlite:///test_prompt_store.db",
        "redis_url": "redis://localhost:6379/2",
        "ai_service_url": "http://localhost:5020",
        "analytics_service_url": "http://localhost:5100",
        "test_timeout": 30,
        "cleanup_after_tests": True,
        "test_data": {
            "prompts": 100,
            "versions": 50,
            "ab_tests": 10,
            "analytics_events": 1000
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "ai_service": AsyncMock(),
        "analytics_service": AsyncMock(),
        "notification_service": AsyncMock(),
        "validation_service": AsyncMock(),
        "cache_service": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_data():
    """Test data for performance benchmarking."""
    return {
        "prompts": [
            {
                "name": f"Performance Test Prompt {i}",
                "content": f"You are an AI assistant. Analyze this text: {{input_text}}. Provide insights about {'technology' if i % 3 == 0 else 'business' if i % 3 == 1 else 'science'}.",
                "category": "analysis",
                "tags": ["performance", f"batch_{i//20}"],
                "token_count": 50 + (i * 2)
            }
            for i in range(500)  # 500 prompts for performance testing
        ],
        "ab_tests": [
            {
                "name": f"A/B Test {i}",
                "variants": [
                    {"name": "Control", "content": "Basic analysis prompt"},
                    {"name": "Variant A", "content": "Enhanced analysis prompt A"},
                    {"name": "Variant B", "content": "Enhanced analysis prompt B"}
                ],
                "target_sample_size": 1000
            }
            for i in range(20)
        ],
        "usage_scenarios": [
            {
                "scenario": "high_frequency_analysis",
                "requests_per_second": 50,
                "duration_seconds": 300,
                "prompt_ids": [f"prompt_{i}" for i in range(10)]
            },
            {
                "scenario": "bulk_operations",
                "concurrent_operations": 20,
                "operation_types": ["create", "update", "search", "analytics"],
                "duration_seconds": 180
            },
            {
                "scenario": "ab_testing_load",
                "active_tests": 50,
                "requests_per_second": 100,
                "duration_seconds": 240
            }
        ]
    }


@pytest.fixture
def load_test_scenario():
    """Load testing scenario configuration."""
    return {
        "duration_seconds": 300,
        "concurrent_users": 100,
        "ramp_up_seconds": 60,
        "scenarios": {
            "prompt_operations": {
                "weight": 40,
                "steps": ["create_prompt", "read_prompt", "update_prompt", "search_prompts"]
            },
            "ab_testing": {
                "weight": 25,
                "steps": ["start_ab_test", "record_usage", "get_test_results", "end_test"]
            },
            "analytics_operations": {
                "weight": 20,
                "steps": ["record_usage", "get_metrics", "generate_report", "get_recommendations"]
            },
            "version_operations": {
                "weight": 15,
                "steps": ["create_version", "list_versions", "compare_versions", "revert_version"]
            }
        },
        "thresholds": {
            "avg_response_time_ms": 500,
            "error_rate_percent": 1.0,
            "throughput_requests_per_sec": 100,
            "p95_response_time_ms": 1000
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "prompt_store_resilience_test",
        "duration_minutes": 15,
        "failure_scenarios": [
            {
                "type": "ai_service_failure",
                "target": "ai_optimization_service",
                "duration_seconds": 120,
                "impact": "medium",
                "fallback_test": True
            },
            {
                "type": "analytics_service_degradation",
                "target": "analytics_service",
                "latency_increase_ms": 2000,
                "duration_seconds": 180,
                "impact": "low"
            },
            {
                "type": "cache_failure",
                "target": "redis_cache",
                "duration_seconds": 90,
                "impact": "medium",
                "performance_impact_test": True
            },
            {
                "type": "database_connection_loss",
                "target": "postgresql",
                "duration_seconds": 60,
                "impact": "high",
                "data_consistency_check": True
            }
        ],
        "monitoring": {
            "metrics": ["prompt_create_success_rate", "ab_test_completion_rate", "analytics_query_time", "cache_hit_rate"],
            "alerts": ["error_rate > 10%", "response_time > 2000ms", "ab_test_failures > 5"],
            "recovery_time_sla": 300
        },
        "data_integrity_checks": [
            "prompt_content_preservation",
            "version_history_integrity",
            "ab_test_result_accuracy",
            "analytics_data_consistency"
        ]
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_ai_service_failure = MagicMock(return_value=True)
    mock_injector.inject_analytics_degradation = MagicMock(return_value=True)
    mock_injector.inject_cache_failure = MagicMock(return_value=True)
    mock_injector.inject_database_failure = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["ai_service_down", "cache_failure"],
        "recovery_eta_seconds": 75,
        "data_integrity_score": 0.98
    })
    return mock_injector
