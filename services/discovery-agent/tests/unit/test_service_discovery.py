"""Unit Tests for Service Discovery in Discovery Agent.

This module tests service discovery capabilities including:
- Network scanning and service detection
- Service health monitoring and validation
- Service registration and metadata management
- Discovery performance optimization

Tests cover the complete service discovery infrastructure within the Discovery Agent.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from modules.discovery_handler import DiscoveryHandler
from modules.monitoring_service import MonitoringService


class TestNetworkScanning:
    """Test Network Scanning functionality."""

    @pytest.fixture
    def discovery_handler(self, mock_network_scanner):
        """Create discovery handler instance."""
        return DiscoveryHandler(network_scanner=mock_network_scanner)

    def test_network_scan_initialization(self, discovery_handler):
        """Test network scan initialization."""
        scan_config = {
            "scan_id": "network_scan_001",
            "target_network": "10.0.0.0/24",
            "scan_type": "comprehensive",
            "ports": [80, 443, 5000, 5005, 5010, 8080],
            "timeout_seconds": 30,
            "max_concurrent_scans": 10,
            "service_detection": {
                "enabled": True,
                "fingerprinting": True,
                "api_spec_detection": True
            }
        }

        scan_result = discovery_handler.initialize_network_scan(scan_config)

        assert scan_result["success"] is True
        assert "scan_id" in scan_result
        assert scan_result["status"] == "initialized"
        assert "estimated_duration_seconds" in scan_result
        assert "target_hosts_count" in scan_result

        # Should calculate network size correctly
        assert scan_result["target_hosts_count"] == 254  # /24 network has 254 usable hosts

    def test_service_type_detection(self, discovery_handler):
        """Test service type detection during scanning."""
        service_probes = [
            {
                "ip_address": "10.0.0.15",
                "port": 5005,
                "response_headers": {
                    "server": "FastAPI/0.100.0",
                    "content-type": "application/json"
                },
                "response_body": '{"message": "Document Interpreter API"}',
                "response_time_ms": 145
            },
            {
                "ip_address": "10.0.0.20",
                "port": 5010,
                "response_headers": {
                    "server": "FastAPI/0.100.0",
                    "content-type": "application/json"
                },
                "response_body": '{"status": "healthy", "service": "doc_store"}',
                "response_time_ms": 98
            },
            {
                "ip_address": "10.0.0.25",
                "port": 6379,
                "response_headers": {},
                "response_body": "+PONG\r\n",
                "response_time_ms": 12
            }
        ]

        for probe in service_probes:
            detection_result = discovery_handler.detect_service_type(probe)

            assert detection_result["detection_success"] is True
            assert "service_type" in detection_result
            assert "confidence_score" in detection_result

            if probe["port"] in [5005, 5010]:
                assert detection_result["service_type"] == "fastapi_service"
                assert detection_result["confidence_score"] >= 0.8
            elif probe["port"] == 6379:
                assert detection_result["service_type"] == "redis"
                assert detection_result["confidence_score"] >= 0.9

    def test_api_specification_discovery(self, discovery_handler):
        """Test API specification discovery during scanning."""
        service_endpoints = [
            {
                "base_url": "http://10.0.0.15:5005",
                "detected_endpoints": ["/health", "/docs", "/openapi.json", "/redoc"],
                "api_spec_url": "http://10.0.0.15:5005/openapi.json"
            },
            {
                "base_url": "http://10.0.0.20:5010",
                "detected_endpoints": ["/health", "/documents", "/api/v1/docs"],
                "api_spec_url": None  # No OpenAPI spec found
            }
        ]

        for service in service_endpoints:
            spec_result = discovery_handler.discover_api_specification(service)

            assert spec_result["discovery_attempted"] is True

            if service["api_spec_url"]:
                assert spec_result["spec_found"] is True
                assert "spec_url" in spec_result
                assert "spec_format" in spec_result  # Should detect OpenAPI/Swagger
                assert spec_result["spec_format"] in ["openapi_3", "swagger_2"]
            else:
                assert spec_result["spec_found"] is False
                assert "fallback_detection" in spec_result

    def test_scan_result_aggregation(self, discovery_handler):
        """Test scan result aggregation and deduplication."""
        raw_scan_results = [
            {
                "ip_address": "10.0.0.15",
                "port": 5005,
                "service_type": "fastapi_service",
                "service_name": "interpreter",
                "confidence": 0.95
            },
            {
                "ip_address": "10.0.0.15",
                "port": 5005,
                "service_type": "fastapi_service",
                "service_name": "interpreter",  # Duplicate detection
                "confidence": 0.92
            },
            {
                "ip_address": "10.0.0.20",
                "port": 5010,
                "service_type": "fastapi_service",
                "service_name": "doc_store",
                "confidence": 0.88
            },
            {
                "ip_address": "10.0.0.15",
                "port": 22,
                "service_type": "ssh",
                "service_name": None,  # Non-HTTP service
                "confidence": 0.99
            }
        ]

        aggregation_result = discovery_handler.aggregate_scan_results(raw_scan_results)

        assert aggregation_result["success"] is True
        assert "aggregated_services" in aggregation_result
        assert "duplicates_removed" in aggregation_result
        assert "scan_summary" in aggregation_result

        aggregated = aggregation_result["aggregated_services"]

        # Should deduplicate identical services
        interpreter_services = [s for s in aggregated if s["service_name"] == "interpreter"]
        assert len(interpreter_services) == 1

        # Should keep non-HTTP services
        ssh_services = [s for s in aggregated if s["service_type"] == "ssh"]
        assert len(ssh_services) == 1

        # Should calculate deduplication stats
        assert aggregation_result["duplicates_removed"] >= 1

        summary = aggregation_result["scan_summary"]
        assert "total_unique_services" in summary
        assert "services_by_type" in summary
        assert "high_confidence_services" in summary

    def test_scan_performance_optimization(self, discovery_handler):
        """Test scan performance optimization techniques."""
        performance_config = {
            "optimization_enabled": True,
            "parallel_scanning": True,
            "smart_port_selection": True,
            "adaptive_timeouts": True,
            "result_caching": True,
            "early_termination": True
        }

        optimization_result = discovery_handler.optimize_scan_performance(performance_config)

        assert optimization_result["success"] is True
        assert "optimizations_applied" in optimization_result
        assert "performance_projections" in optimization_result

        optimizations = optimization_result["optimizations_applied"]
        assert optimizations["parallel_scanning"] is True
        assert optimizations["smart_port_selection"] is True

        projections = optimization_result["performance_projections"]
        assert "estimated_scan_time_seconds" in projections
        assert "resource_usage_estimate" in projections
        assert "success_rate_projection" in projections

        # Should show performance improvements
        assert projections["estimated_scan_time_seconds"] < 300  # Under 5 minutes for /24 network
        assert projections["success_rate_projection"] > 0.7


class TestServiceHealthMonitoring:
    """Test Service Health Monitoring functionality."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance."""
        return MonitoringService()

    def test_service_health_check(self, monitoring_service):
        """Test service health check execution."""
        service_config = {
            "service_id": "interpreter",
            "health_endpoint": "/health",
            "base_url": "http://interpreter:5005",
            "expected_status_codes": [200, 201],
            "timeout_seconds": 10,
            "headers": {"Authorization": "Bearer token123"}
        }

        health_result = monitoring_service.check_service_health(service_config)

        assert "check_performed" in health_result
        assert health_result["check_performed"] is True
        assert "healthy" in health_result
        assert "response_time_ms" in health_result
        assert "status_code" in health_result

        if health_result["healthy"]:
            assert health_result["status_code"] in service_config["expected_status_codes"]
            assert health_result["response_time_ms"] < service_config["timeout_seconds"] * 1000
        else:
            assert "error_details" in health_result

    def test_comprehensive_health_assessment(self, monitoring_service):
        """Test comprehensive health assessment with multiple checks."""
        comprehensive_checks = {
            "service_id": "interpreter",
            "base_url": "http://interpreter:5005",
            "health_checks": [
                {
                    "check_type": "http_endpoint",
                    "endpoint": "/health",
                    "expected_status": 200
                },
                {
                    "check_type": "api_spec_accessible",
                    "endpoint": "/openapi.json",
                    "expected_content_type": "application/json"
                },
                {
                    "check_type": "service_dependencies",
                    "dependencies": ["llm_gateway", "doc_store"],
                    "check_type": "health_proxy"
                },
                {
                    "check_type": "performance_metrics",
                    "endpoint": "/metrics",
                    "expected_metrics": ["response_time", "throughput"]
                }
            ],
            "assessment_criteria": {
                "min_checks_passed": 3,
                "max_response_time_ms": 1000,
                "acceptable_error_rate": 0.05
            }
        }

        assessment_result = monitoring_service.perform_comprehensive_health_assessment(comprehensive_checks)

        assert assessment_result["success"] is True
        assert "overall_health_score" in assessment_result
        assert "checks_results" in assessment_result
        assert "assessment_summary" in assessment_result

        checks_results = assessment_result["checks_results"]
        assert len(checks_results) == len(comprehensive_checks["health_checks"])

        for check_result in checks_results:
            assert "check_type" in check_result
            assert "passed" in check_result
            assert "execution_time_ms" in check_result

        summary = assessment_result["assessment_summary"]
        assert "checks_passed" in summary
        assert "checks_failed" in summary
        assert "average_response_time_ms" in summary

        # Should calculate overall health score
        health_score = assessment_result["overall_health_score"]
        assert 0.0 <= health_score <= 1.0

    def test_health_monitoring_scheduling(self, monitoring_service):
        """Test health monitoring scheduling and execution."""
        monitoring_schedule = {
            "service_id": "interpreter",
            "monitoring_config": {
                "interval_seconds": 60,
                "timeout_seconds": 30,
                "max_consecutive_failures": 3,
                "backoff_multiplier": 2.0,
                "alerting_enabled": True
            },
            "escalation_policy": {
                "first_failure": "log_warning",
                "consecutive_failures_2": "send_notification",
                "consecutive_failures_3": "page_on_call",
                "recovery": "send_recovery_notification"
            }
        }

        schedule_result = monitoring_service.schedule_health_monitoring(monitoring_schedule)

        assert schedule_result["success"] is True
        assert "schedule_id" in schedule_result
        assert "next_check_time" in schedule_result
        assert "monitoring_status" in schedule_result

        # Should calculate next check time
        next_check = schedule_result["next_check_time"]
        expected_next = datetime.now() + timedelta(seconds=monitoring_schedule["monitoring_config"]["interval_seconds"])
        time_diff = abs((next_check - expected_next).total_seconds())
        assert time_diff < 5  # Within 5 seconds

        status = schedule_result["monitoring_status"]
        assert status["active"] is True
        assert status["consecutive_failures"] == 0
        assert status["last_check_result"] is None

    def test_health_trend_analysis(self, monitoring_service):
        """Test health trend analysis and predictive monitoring."""
        health_history = [
            {
                "timestamp": datetime.now() - timedelta(hours=24),
                "healthy": True,
                "response_time_ms": 145,
                "status_code": 200
            },
            {
                "timestamp": datetime.now() - timedelta(hours=18),
                "healthy": True,
                "response_time_ms": 156,
                "status_code": 200
            },
            {
                "timestamp": datetime.now() - timedelta(hours=12),
                "healthy": False,
                "response_time_ms": 5000,  # Timeout
                "status_code": None,
                "error": "Connection timeout"
            },
            {
                "timestamp": datetime.now() - timedelta(hours=6),
                "healthy": True,
                "response_time_ms": 178,
                "status_code": 200
            },
            {
                "timestamp": datetime.now() - timedelta(hours=1),
                "healthy": True,
                "response_time_ms": 234,
                "status_code": 200
            }
        ]

        trend_result = monitoring_service.analyze_health_trends(health_history)

        assert trend_result["success"] is True
        assert "trend_analysis" in trend_result
        assert "predictive_insights" in trend_result
        assert "anomaly_detection" in trend_result

        trend_analysis = trend_result["trend_analysis"]
        assert "overall_trend" in trend_analysis
        assert "response_time_trend" in trend_analysis
        assert "availability_trend" in trend_analysis

        # Should detect the availability dip
        availability = trend_analysis["availability_trend"]
        assert availability["total_checks"] == len(health_history)
        assert availability["successful_checks"] == 4  # 4 out of 5 were healthy
        assert availability["availability_percentage"] == 80.0

        predictive = trend_result["predictive_insights"]
        assert "predicted_next_failure_probability" in predictive
        assert "recommended_monitoring_adjustments" in predictive

        anomalies = trend_result["anomaly_detection"]
        assert "anomalies_detected" in anomalies
        assert len(anomalies["anomalies_detected"]) >= 1  # Should detect the timeout

        # Should identify the timeout as an anomaly
        timeout_anomalies = [a for a in anomalies["anomalies_detected"] if "timeout" in str(a.get("description", "")).lower()]
        assert len(timeout_anomalies) >= 1

    def test_health_alert_management(self, monitoring_service):
        """Test health alert generation and management."""
        alert_config = {
            "service_id": "interpreter",
            "alert_rules": [
                {
                    "rule_id": "high_response_time",
                    "condition": "response_time_ms > 1000",
                    "severity": "warning",
                    "cooldown_minutes": 15,
                    "notification_channels": ["email", "slack"]
                },
                {
                    "rule_id": "service_unhealthy",
                    "condition": "healthy == false",
                    "severity": "error",
                    "cooldown_minutes": 5,
                    "notification_channels": ["email", "slack", "pagerduty"]
                },
                {
                    "rule_id": "consecutive_failures",
                    "condition": "consecutive_failures >= 3",
                    "severity": "critical",
                    "cooldown_minutes": 1,
                    "notification_channels": ["pagerduty", "sms"]
                }
            ],
            "alert_history": [
                {
                    "timestamp": datetime.now() - timedelta(minutes=30),
                    "rule_id": "high_response_time",
                    "triggered": True,
                    "resolved": True
                }
            ]
        }

        # Simulate health check results that should trigger alerts
        health_results = [
            {
                "healthy": False,
                "response_time_ms": None,
                "error": "Connection refused",
                "consecutive_failures": 1
            },
            {
                "healthy": False,
                "response_time_ms": None,
                "error": "Connection timeout",
                "consecutive_failures": 2
            },
            {
                "healthy": False,
                "response_time_ms": None,
                "error": "Service unavailable",
                "consecutive_failures": 3  # Should trigger critical alert
            }
        ]

        alert_results = []
        for i, health_result in enumerate(health_results):
            alert_result = monitoring_service.process_health_alerts(
                alert_config,
                health_result,
                check_timestamp=datetime.now() + timedelta(minutes=i)
            )
            alert_results.append(alert_result)

        # Third check should trigger critical alert
        critical_alert = alert_results[2]
        assert critical_alert["alerts_triggered"] > 0

        critical_alerts = [a for a in critical_alert["triggered_alerts"] if a["severity"] == "critical"]
        assert len(critical_alerts) >= 1

        # Should include escalation information
        for alert in critical_alerts:
            assert "notification_channels" in alert
            assert "pagerduty" in alert["notification_channels"]
            assert "sms" in alert["notification_channels"]


class TestServiceRegistration:
    """Test Service Registration functionality."""

    @pytest.fixture
    def discovery_handler(self):
        """Create discovery handler instance."""
        return DiscoveryHandler()

    def test_service_registration_process(self, discovery_handler):
        """Test complete service registration process."""
        service_data = {
            "service_id": "interpreter",
            "service_name": "Document Interpreter",
            "version": "1.2.0",
            "base_url": "http://interpreter:5005",
            "health_endpoint": "/health",
            "api_spec_url": "http://interpreter:5005/openapi.json",
            "capabilities": ["document_processing", "nlp_analysis"],
            "dependencies": ["llm_gateway", "doc_store"],
            "environment": "production",
            "tags": ["nlp", "documents", "processing"]
        }

        registration_config = {
            "validation_required": True,
            "health_check_required": True,
            "api_spec_validation": True,
            "dependency_verification": True,
            "registration_timeout_seconds": 30
        }

        registration_result = discovery_handler.register_service(service_data, registration_config)

        assert registration_result["success"] is True
        assert "registration_id" in registration_result
        assert "service_registered" in registration_result
        assert "validation_results" in registration_result

        validation = registration_result["validation_results"]
        assert "health_check_passed" in validation
        assert "api_spec_valid" in validation
        assert "dependencies_verified" in validation

        # Should generate registration metadata
        assert "registration_timestamp" in registration_result
        assert "registered_by" in registration_result
        assert registration_result["registered_by"] == "discovery_agent"

    def test_service_metadata_enrichment(self, discovery_handler):
        """Test service metadata enrichment during registration."""
        base_service_data = {
            "service_id": "interpreter",
            "base_url": "http://interpreter:5005",
            "capabilities": ["document_processing"]
        }

        enrichment_result = discovery_handler.enrich_service_metadata(base_service_data)

        assert enrichment_result["success"] is True
        assert "enriched_metadata" in enrichment_result
        assert "enrichment_sources" in enrichment_result

        enriched = enrichment_result["enriched_metadata"]

        # Should add discovered metadata
        assert "service_name" in enriched
        assert "version" in enriched
        assert "health_endpoint" in enriched
        assert "api_spec_url" in enriched

        # Should add computed metadata
        assert "tags" in enriched
        assert "category" in enriched
        assert "capability_count" in enriched

        # Should add discovery metadata
        assert "discovered_at" in enriched
        assert "discovery_method" in enriched
        assert "confidence_score" in enriched

        sources = enrichment_result["enrichment_sources"]
        assert len(sources) > 0
        source_types = [s["source_type"] for s in sources]
        assert "api_spec_analysis" in source_types
        assert "health_check" in source_types

    def test_service_update_and_versioning(self, discovery_handler):
        """Test service update detection and versioning."""
        existing_service = {
            "service_id": "interpreter",
            "version": "1.1.0",
            "capabilities": ["document_processing", "text_extraction"],
            "last_updated": datetime.now() - timedelta(days=7)
        }

        discovered_service = {
            "service_id": "interpreter",
            "version": "1.2.0",
            "capabilities": ["document_processing", "text_extraction", "sentiment_analysis"],
            "api_spec_changes": {
                "new_endpoints": ["/sentiment"],
                "modified_endpoints": ["/process"],
                "deprecated_endpoints": []
            }
        }

        update_result = discovery_handler.detect_service_updates(existing_service, discovered_service)

        assert update_result["success"] is True
        assert "update_detected" in update_result
        assert "update_type" in update_result
        assert "change_details" in update_result

        # Should detect version change
        assert update_result["update_detected"] is True
        assert update_result["update_type"] in ["minor_update", "major_update", "patch_update"]

        changes = update_result["change_details"]
        assert "version_change" in changes
        assert "capability_changes" in changes
        assert "api_changes" in changes

        # Should identify new capabilities
        capability_changes = changes["capability_changes"]
        assert "sentiment_analysis" in capability_changes["added"]

        # Should identify API changes
        api_changes = changes["api_changes"]
        assert "/sentiment" in api_changes["new_endpoints"]

    def test_service_dependency_resolution(self, discovery_handler):
        """Test service dependency resolution and validation."""
        service_with_deps = {
            "service_id": "interpreter",
            "dependencies": [
                {
                    "service_id": "llm_gateway",
                    "version_requirement": ">=2.0.0",
                    "required_capabilities": ["text_generation", "model_management"]
                },
                {
                    "service_id": "doc_store",
                    "version_requirement": ">=1.0.0",
                    "required_capabilities": ["document_storage", "search"]
                }
            ]
        }

        available_services = {
            "llm_gateway": {
                "version": "2.1.0",
                "capabilities": ["text_generation", "model_management", "fine_tuning"],
                "status": "healthy"
            },
            "doc_store": {
                "version": "1.2.0",
                "capabilities": ["document_storage", "search", "versioning"],
                "status": "healthy"
            },
            "redis": {
                "version": "6.2.0",
                "capabilities": ["caching", "pubsub"],
                "status": "healthy"
            }
        }

        resolution_result = discovery_handler.resolve_service_dependencies(service_with_deps, available_services)

        assert resolution_result["success"] is True
        assert "dependency_resolution" in resolution_result
        assert "compatibility_check" in resolution_result

        resolution = resolution_result["dependency_resolution"]

        # Should resolve all dependencies
        for dep in service_with_deps["dependencies"]:
            dep_id = dep["service_id"]
            assert dep_id in resolution
            assert resolution[dep_id]["resolved"] is True
            assert resolution[dep_id]["available_version"] == available_services[dep_id]["version"]

        compatibility = resolution_result["compatibility_check"]
        assert compatibility["all_dependencies_satisfied"] is True
        assert len(compatibility["compatibility_issues"]) == 0

        # Should validate capability requirements
        for dep in service_with_deps["dependencies"]:
            dep_id = dep["service_id"]
            dep_resolution = resolution[dep_id]
            assert "capability_match" in dep_resolution
            assert dep_resolution["capability_match"]["satisfied"] is True

    def test_registration_conflict_resolution(self, discovery_handler):
        """Test registration conflict resolution."""
        existing_registration = {
            "service_id": "interpreter",
            "base_url": "http://interpreter:5005",
            "version": "1.1.0",
            "registered_at": datetime.now() - timedelta(days=7),
            "registration_source": "manual_registration"
        }

        conflicting_discovery = {
            "service_id": "interpreter",
            "base_url": "http://interpreter:5005",
            "version": "1.2.0",
            "discovered_at": datetime.now(),
            "discovery_source": "network_scan",
            "confidence_score": 0.95
        }

        conflict_resolution = discovery_handler.resolve_registration_conflict(existing_registration, conflicting_discovery)

        assert conflict_resolution["success"] is True
        assert "conflict_detected" in conflict_resolution
        assert "resolution_strategy" in conflict_resolution
        assert "resolution_action" in conflict_resolution

        # Should detect version conflict
        assert conflict_resolution["conflict_detected"] is True

        # Should choose appropriate resolution strategy
        strategy = conflict_resolution["resolution_strategy"]
        assert strategy in ["update_existing", "create_new_version", "reject_discovery", "merge_metadata"]

        # Should provide resolution details
        action = conflict_resolution["resolution_action"]
        assert "action_type" in action
        assert "reasoning" in action

        if strategy == "update_existing":
            assert "update_metadata" in action
            assert conflicting_discovery["version"] in str(action["update_metadata"])
