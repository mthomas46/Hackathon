"""Pytest configuration and shared fixtures for Discovery Agent Service tests.

This module provides comprehensive test fixtures for enterprise-grade testing
of service discovery, API specification management, tool discovery, and integration
coordination within the Discovery Agent service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta
import json

from modules.discovery_handler import DiscoveryHandler
from modules.tool_registry import ToolRegistry
from modules.semantic_analyzer import SemanticAnalyzer


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
def sample_service_spec():
    """Sample service specification."""
    return {
        "service_id": "interpreter",
        "service_name": "Document Interpreter",
        "version": "1.2.0",
        "description": "Natural language document processing and interpretation service",
        "base_url": "http://interpreter:5005",
        "health_endpoint": "/health",
        "api_spec_url": "http://interpreter:5005/openapi.json",
        "capabilities": [
            "document_processing",
            "natural_language_understanding",
            "content_extraction",
            "semantic_analysis"
        ],
        "dependencies": ["llm_gateway", "doc_store"],
        "environment": "production",
        "tags": ["nlp", "documents", "processing"],
        "metadata": {
            "owner": "platform_team",
            "sla_tier": "gold",
            "data_classification": "internal",
            "last_updated": datetime.now()
        }
    }


@pytest.fixture
def sample_api_specification():
    """Sample OpenAPI specification."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Document Interpreter API",
            "version": "1.2.0",
            "description": "API for document interpretation and processing",
            "contact": {
                "name": "Platform Team",
                "email": "platform@company.com"
            }
        },
        "servers": [
            {
                "url": "http://interpreter:5005",
                "description": "Production server"
            }
        ],
        "paths": {
            "/documents/process": {
                "post": {
                    "summary": "Process a document",
                    "operationId": "processDocument",
                    "tags": ["documents"],
                    "parameters": [
                        {
                            "name": "Content-Type",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DocumentRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Document processed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DocumentResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "DocumentRequest": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {"type": "string"},
                        "metadata": {"type": "object"}
                    }
                },
                "DocumentResponse": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string"},
                        "processed_content": {"type": "string"},
                        "extracted_entities": {"type": "array"},
                        "confidence_score": {"type": "number"}
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_tool_specification():
    """Sample tool specification."""
    return {
        "tool_id": "code_analyzer_tool",
        "tool_name": "Code Analysis Tool",
        "version": "2.1.0",
        "description": "Advanced code analysis and quality assessment tool",
        "provider": "code_analyzer_service",
        "capabilities": [
            {
                "capability_id": "syntax_analysis",
                "name": "Syntax Analysis",
                "description": "Parse and analyze code syntax",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"}
                    }
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "syntax_valid": {"type": "boolean"},
                        "parse_tree": {"type": "object"},
                        "errors": {"type": "array"}
                    }
                }
            },
            {
                "capability_id": "quality_metrics",
                "name": "Quality Metrics",
                "description": "Calculate code quality metrics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "metrics": {"type": "array"}
                    }
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "cyclomatic_complexity": {"type": "number"},
                        "maintainability_index": {"type": "number"},
                        "duplication_percentage": {"type": "number"}
                    }
                }
            }
        ],
        "authentication": {
            "type": "bearer_token",
            "token_endpoint": "/auth/token"
        },
        "rate_limits": {
            "requests_per_minute": 100,
            "burst_limit": 20
        },
        "tags": ["code", "analysis", "quality"],
        "metadata": {
            "maturity_level": "stable",
            "last_tested": datetime.now(),
            "performance_score": 0.92
        }
    }


@pytest.fixture
def sample_discovery_result():
    """Sample service discovery result."""
    return {
        "discovery_id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "scan_type": "network_scan",
        "target_network": "10.0.0.0/24",
        "discovered_services": [
            {
                "ip_address": "10.0.0.15",
                "port": 5005,
                "service_type": "http",
                "detected_service": "interpreter",
                "confidence": 0.95,
                "metadata": {
                    "server_header": "FastAPI/0.100.0",
                    "endpoints_found": ["/health", "/docs", "/openapi.json"],
                    "response_time_ms": 145
                }
            },
            {
                "ip_address": "10.0.0.20",
                "port": 5010,
                "service_type": "http",
                "detected_service": "doc_store",
                "confidence": 0.88,
                "metadata": {
                    "server_header": "FastAPI/0.100.0",
                    "endpoints_found": ["/health", "/documents"],
                    "response_time_ms": 98
                }
            }
        ],
        "scan_duration_seconds": 45.2,
        "total_hosts_scanned": 254,
        "services_identified": 12,
        "errors_encountered": 3
    }


@pytest.fixture
def sample_integration_spec():
    """Sample service integration specification."""
    return {
        "integration_id": "interpreter_llm_gateway",
        "source_service": "interpreter",
        "target_service": "llm_gateway",
        "integration_type": "api_call",
        "description": "Interpreter service calls LLM Gateway for text processing",
        "communication_pattern": "synchronous_request_response",
        "data_flow": {
            "request_mapping": {
                "source_field": "document.content",
                "target_field": "text",
                "transformation": "extract_text_content"
            },
            "response_mapping": {
                "source_field": "processed_text",
                "target_field": "document.processed_content",
                "transformation": "inject_processed_content"
            }
        },
        "error_handling": {
            "timeout_seconds": 30,
            "retry_policy": {
                "max_attempts": 3,
                "backoff_strategy": "exponential",
                "base_delay_seconds": 1
            },
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout_seconds": 60
            }
        },
        "monitoring": {
            "metrics_to_track": [
                "request_count",
                "response_time",
                "error_rate",
                "data_transfer_volume"
            ],
            "alerts": {
                "high_error_rate": {"threshold": 0.05, "severity": "warning"},
                "slow_response": {"threshold_ms": 5000, "severity": "error"}
            }
        },
        "version_compatibility": {
            "source_version_range": ">=1.0.0",
            "target_version_range": ">=2.0.0",
            "breaking_changes_handled": True
        }
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_discovery_handler():
    """Mock discovery handler."""
    mock_handler = AsyncMock()
    mock_handler.discover_services = AsyncMock(return_value={
        "services_found": 8,
        "services_registered": 6,
        "errors": 2,
        "scan_duration_seconds": 42.5
    })
    mock_handler.validate_service_health = AsyncMock(return_value={
        "service_id": "interpreter",
        "healthy": True,
        "response_time_ms": 145,
        "checks_passed": 4,
        "last_checked": datetime.now()
    })
    mock_handler.update_service_spec = AsyncMock(return_value={
        "service_id": "interpreter",
        "spec_updated": True,
        "changes_detected": 3,
        "validation_passed": True
    })
    return mock_handler


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    mock_registry = AsyncMock()
    mock_registry.register_tool = AsyncMock(return_value={
        "tool_id": "code_analyzer_tool",
        "registration_status": "success",
        "version": "2.1.0"
    })
    mock_registry.discover_tools = AsyncMock(return_value={
        "tools_discovered": 15,
        "tools_registered": 12,
        "categories": ["code_analysis", "documentation", "testing"]
    })
    mock_registry.get_tool_capabilities = AsyncMock(return_value=[
        {
            "capability_id": "syntax_analysis",
            "name": "Syntax Analysis",
            "description": "Parse and analyze code syntax"
        }
    ])
    mock_registry.validate_tool_spec = AsyncMock(return_value={
        "valid": True,
        "warnings": [],
        "capability_count": 8
    })
    return mock_registry


@pytest.fixture
def mock_semantic_analyzer():
    """Mock semantic analyzer."""
    mock_analyzer = AsyncMock()
    mock_analyzer.analyze_service_semantics = AsyncMock(return_value={
        "service_id": "interpreter",
        "semantic_score": 0.87,
        "capabilities_identified": 12,
        "relationships_detected": 5,
        "confidence_level": "high"
    })
    mock_analyzer.extract_api_patterns = AsyncMock(return_value={
        "patterns_found": 8,
        "pattern_categories": ["restful", "resource_based", "action_based"],
        "complexity_score": 0.72
    })
    mock_analyzer.validate_api_consistency = AsyncMock(return_value={
        "consistent": True,
        "consistency_score": 0.94,
        "violations": [],
        "recommendations": []
    })
    return mock_analyzer


@pytest.fixture
def mock_api_spec_parser():
    """Mock API specification parser."""
    mock_parser = AsyncMock()
    mock_parser.parse_openapi_spec = AsyncMock(return_value={
        "parsing_success": True,
        "api_version": "3.0.3",
        "endpoints_count": 15,
        "schemas_count": 8,
        "validation_errors": 0
    })
    mock_parser.extract_api_metadata = AsyncMock(return_value={
        "title": "Document Interpreter API",
        "version": "1.2.0",
        "description": "API for document interpretation",
        "contact": {"email": "platform@company.com"},
        "license": {"name": "MIT"}
    })
    mock_parser.validate_api_spec = AsyncMock(return_value={
        "valid": True,
        "validation_level": "strict",
        "errors": [],
        "warnings": []
    })
    return mock_parser


@pytest.fixture
def mock_integration_manager():
    """Mock integration manager."""
    mock_manager = AsyncMock()
    mock_manager.create_integration = AsyncMock(return_value={
        "integration_id": "interpreter_llm_gateway",
        "creation_status": "success",
        "validation_passed": True
    })
    mock_manager.validate_integration = AsyncMock(return_value={
        "integration_id": "interpreter_llm_gateway",
        "valid": True,
        "compatibility_score": 0.91,
        "issues": []
    })
    mock_manager.test_integration = AsyncMock(return_value={
        "integration_id": "interpreter_llm_gateway",
        "test_passed": True,
        "performance_score": 0.88,
        "error_rate": 0.02
    })
    return mock_manager


@pytest.fixture
def mock_network_scanner():
    """Mock network scanner."""
    mock_scanner = AsyncMock()
    mock_scanner.scan_network = AsyncMock(return_value={
        "scan_id": str(uuid.uuid4()),
        "hosts_scanned": 254,
        "services_found": 12,
        "scan_duration_seconds": 45.2,
        "success_rate": 0.98
    })
    mock_scanner.detect_service_type = AsyncMock(return_value={
        "ip_address": "10.0.0.15",
        "port": 5005,
        "service_type": "http",
        "confidence": 0.95,
        "fingerprint": "FastAPI/0.100.0"
    })
    mock_scanner.probe_service_endpoints = AsyncMock(return_value={
        "service_url": "http://10.0.0.15:5005",
        "endpoints_found": ["/health", "/docs", "/openapi.json"],
        "response_times": {"health": 145, "docs": 234, "openapi": 567}
    })
    return mock_scanner


@pytest.fixture
def mock_performance_optimizer():
    """Mock performance optimizer."""
    mock_optimizer = AsyncMock()
    mock_optimizer.optimize_discovery_performance = AsyncMock(return_value={
        "optimization_applied": True,
        "performance_improvement": 0.35,  # 35% faster
        "resource_usage_reduction": 0.22,  # 22% less resources
        "optimizations": ["parallel_scanning", "caching", "smart_filtering"]
    })
    mock_optimizer.analyze_discovery_bottlenecks = AsyncMock(return_value={
        "bottlenecks_identified": 3,
        "primary_bottleneck": "network_latency",
        "recommendations": [
            "Implement connection pooling",
            "Add result caching",
            "Use parallel scanning"
        ]
    })
    return mock_optimizer


@pytest.fixture
def mock_security_scanner():
    """Mock security scanner."""
    mock_scanner = AsyncMock()
    mock_scanner.scan_service_security = AsyncMock(return_value={
        "service_id": "interpreter",
        "security_score": 0.87,
        "vulnerabilities_found": 2,
        "severity_breakdown": {"critical": 0, "high": 1, "medium": 1, "low": 3},
        "recommendations": [
            "Enable HTTPS",
            "Implement rate limiting",
            "Add input validation"
        ]
    })
    mock_scanner.validate_api_security = AsyncMock(return_value={
        "api_spec_id": "interpreter_api",
        "security_compliant": True,
        "authentication_required": True,
        "authorization_implemented": True,
        "encryption_enabled": False  # This would be a finding
    })
    return mock_scanner


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        "test_services": ["interpreter", "doc_store", "prompt_store"],
        "network_range": "10.0.0.0/24",
        "api_endpoints": {
            "interpreter": "http://interpreter:5005",
            "doc_store": "http://doc_store:5010",
            "prompt_store": "http://prompt_store:5110"
        },
        "test_duration_seconds": 120,
        "concurrent_discovery_processes": 3,
        "expected_service_count": 8,
        "validation_timeout_seconds": 30
    }


@pytest.fixture
def mock_ecosystem_services():
    """Mock external ecosystem services for integration testing."""
    return {
        "interpreter": AsyncMock(),
        "doc_store": AsyncMock(),
        "prompt_store": AsyncMock(),
        "llm_gateway": AsyncMock(),
        "orchestrator": AsyncMock(),
        "frontend": AsyncMock()
    }


# =============================================================================
# PERFORMANCE TEST FIXTURES
# =============================================================================

@pytest.fixture
def performance_test_scenarios():
    """Performance testing scenarios for discovery operations."""
    return {
        "small_network": {
            "name": "Small Network Scan",
            "network_size": "10.0.0.0/28",  # 16 hosts
            "expected_services": 4,
            "max_duration_seconds": 30,
            "expected_discovery_rate": 0.8  # 80% success rate
        },
        "medium_network": {
            "name": "Medium Network Scan",
            "network_size": "10.0.0.0/24",  # 256 hosts
            "expected_services": 12,
            "max_duration_seconds": 120,
            "expected_discovery_rate": 0.75
        },
        "large_network": {
            "name": "Large Network Scan",
            "network_size": "10.0.0.0/22",  # 1024 hosts
            "expected_services": 25,
            "max_duration_seconds": 300,
            "expected_discovery_rate": 0.7
        },
        "concurrent_discovery": {
            "name": "Concurrent Discovery",
            "concurrent_scans": 5,
            "services_per_scan": 20,
            "max_duration_seconds": 180,
            "expected_efficiency": 0.85  # 85% of sequential performance
        },
        "api_spec_processing": {
            "name": "API Specification Processing",
            "specs_count": 50,
            "avg_spec_size_kb": 25,
            "max_duration_seconds": 60,
            "expected_processing_rate": 100  # specs per minute
        }
    }


@pytest.fixture
def load_test_configuration():
    """Load testing configuration for discovery agent."""
    return {
        "duration_minutes": 10,
        "concurrent_users": 50,
        "operations_per_second": 20,
        "scenarios": {
            "service_discovery_heavy": {
                "weight": 40,
                "operations": ["network_scan", "service_probe", "health_check"]
            },
            "api_spec_processing_heavy": {
                "weight": 30,
                "operations": ["spec_download", "spec_parse", "spec_validate", "capability_extract"]
            },
            "tool_discovery_heavy": {
                "weight": 20,
                "operations": ["tool_scan", "capability_analysis", "tool_registration"]
            },
            "integration_management_heavy": {
                "weight": 10,
                "operations": ["integration_create", "integration_validate", "integration_test"]
            }
        },
        "thresholds": {
            "max_response_time_ms": 2000,
            "max_error_rate_percent": 5.0,
            "min_throughput_ops_per_second": 15,
            "max_memory_usage_mb": 512,
            "max_cpu_usage_percent": 80
        }
    }


# =============================================================================
# CHAOS ENGINEERING FIXTURES
# =============================================================================

@pytest.fixture
def chaos_experiment_config():
    """Configuration for chaos engineering experiments."""
    return {
        "experiment_name": "discovery_agent_resilience_test",
        "duration_minutes": 15,
        "failure_scenarios": [
            {
                "type": "network_partition",
                "target": "service_discovery",
                "description": "Simulate network connectivity issues during discovery",
                "duration_seconds": 120,
                "impact": "high",
                "mitigation_test": True
            },
            {
                "type": "api_service_unavailable",
                "target": "external_services",
                "description": "Services become temporarily unreachable",
                "duration_seconds": 180,
                "impact": "medium",
                "recovery_test": True
            },
            {
                "type": "high_concurrency",
                "target": "discovery_operations",
                "description": "Overwhelm discovery agent with concurrent requests",
                "concurrent_requests": 200,
                "duration_seconds": 300,
                "impact": "high",
                "scaling_test": True
            },
            {
                "type": "corrupted_api_specs",
                "target": "specification_processing",
                "description": "API specifications become malformed or corrupted",
                "corruption_rate": 0.15,
                "duration_seconds": 240,
                "impact": "medium",
                "error_handling_test": True
            },
            {
                "type": "resource_exhaustion",
                "target": "system_resources",
                "description": "Simulate memory and CPU pressure",
                "memory_limit_mb": 256,
                "cpu_limit_percent": 50,
                "duration_seconds": 360,
                "impact": "high",
                "optimization_test": True
            }
        ],
        "monitoring": {
            "metrics": [
                "discovery_success_rate",
                "average_response_time",
                "error_rate",
                "memory_usage",
                "cpu_usage",
                "network_connectivity"
            ],
            "alerts": [
                "discovery_success_rate < 70%",
                "average_response_time > 5000ms",
                "error_rate > 10%",
                "memory_usage > 80%"
            ],
            "recovery_sla_seconds": 300
        },
        "data_integrity_checks": [
            "service_registry_consistency",
            "api_spec_cache_validity",
            "tool_capability_integrity",
            "integration_mapping_accuracy"
        ]
    }


@pytest.fixture
def mock_failure_injector():
    """Mock failure injector for chaos testing."""
    mock_injector = MagicMock()
    mock_injector.inject_network_failure = MagicMock(return_value=True)
    mock_injector.inject_service_unavailable = MagicMock(return_value=True)
    mock_injector.inject_high_load = MagicMock(return_value=True)
    mock_injector.inject_data_corruption = MagicMock(return_value=True)
    mock_injector.inject_resource_pressure = MagicMock(return_value=True)
    mock_injector.restore_normal_operation = MagicMock(return_value=True)
    mock_injector.get_system_health = MagicMock(return_value={
        "status": "degraded",
        "active_failures": ["network_down", "service_unavailable", "high_load"],
        "recovery_eta_seconds": 120,
        "discovery_success_rate": 0.65,
        "error_rate": 0.08,
        "average_response_time_ms": 3500
    })
    return mock_injector
