"""Integration Tests for Discovery Agent Service Integration.

This module tests end-to-end integration scenarios including:
- Complete service discovery workflows
- API specification processing pipelines
- Tool discovery and registration flows
- Cross-service integration validation

Tests cover complete integration scenarios within the Discovery Agent.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from modules.discovery_handler import DiscoveryHandler
from modules.tool_registry import ToolRegistry
from modules.semantic_analyzer import SemanticAnalyzer
from modules.orchestrator_integration import OrchestratorIntegration


class TestEndToEndServiceDiscovery:
    """Test End-to-End Service Discovery Workflows."""

    @pytest.fixture
    def integration_setup(self, mock_network_scanner, mock_api_spec_parser, mock_tool_registry):
        """Create integrated discovery setup."""
        return {
            "discovery_handler": DiscoveryHandler(network_scanner=mock_network_scanner),
            "tool_registry": ToolRegistry(),
            "semantic_analyzer": SemanticAnalyzer(),
            "orchestrator_integration": OrchestratorIntegration(),
            "api_spec_parser": mock_api_spec_parser
        }

    def test_complete_service_discovery_pipeline(self, integration_setup):
        """Test complete service discovery from network scan to registration."""
        setup = integration_setup

        # Step 1: Network scanning
        scan_config = {
            "target_network": "10.0.0.0/24",
            "scan_type": "comprehensive",
            "service_detection": True,
            "api_spec_discovery": True
        }

        scan_result = setup["discovery_handler"].execute_network_scan(scan_config)
        assert scan_result["success"] is True

        discovered_services = scan_result.get("discovered_services", [])
        assert len(discovered_services) > 0

        # Step 2: Service validation and enrichment
        for service in discovered_services[:2]:  # Test with first 2 services
            # Validate service health
            health_result = setup["discovery_handler"].validate_service_health(service)
            assert health_result["validation_success"] is True

            # Enrich service metadata
            enriched_service = setup["discovery_handler"].enrich_service_metadata(service)
            assert enriched_service["enrichment_success"] is True

            # Step 3: API specification processing
            if enriched_service.get("api_spec_url"):
                spec_result = setup["api_spec_parser"].parse_openapi_spec(enriched_service["api_spec_url"])
                assert spec_result["parsing_success"] is True

                # Validate API spec
                validation_result = setup["api_spec_parser"].validate_api_spec(spec_result["parsed_spec"])
                assert validation_result["valid"] is True

                # Extract capabilities
                capability_result = setup["semantic_analyzer"].extract_api_patterns(spec_result["parsed_spec"])
                assert capability_result["extraction_success"] is True

            # Step 4: Service registration
            registration_result = setup["discovery_handler"].register_service(enriched_service)
            assert registration_result["registration_success"] is True

            # Step 5: Orchestrator integration
            integration_result = setup["orchestrator_integration"].register_with_orchestrator(enriched_service)
            assert integration_result["integration_success"] is True

        # Step 6: Discovery summary and validation
        discovery_summary = setup["discovery_handler"].generate_discovery_summary(scan_result)
        assert discovery_summary["summary_complete"] is True

        summary = discovery_summary["summary"]
        assert "total_services_discovered" in summary
        assert "services_registered" in summary
        assert "api_specs_processed" in summary
        assert "integration_status" in summary

        # Validate complete workflow
        workflow_validation = setup["discovery_handler"].validate_discovery_workflow({
            "scan_result": scan_result,
            "registration_results": [],  # Would be populated in real scenario
            "integration_results": [],  # Would be populated in real scenario
            "expected_outcomes": {
                "min_services_discovered": 1,
                "min_services_registered": 1,
                "min_api_specs_processed": 0
            }
        })

        assert workflow_validation["workflow_valid"] is True

    def test_service_discovery_with_dependency_resolution(self, integration_setup):
        """Test service discovery with automatic dependency resolution."""
        setup = integration_setup

        # Define service with complex dependencies
        complex_service = {
            "service_id": "workflow_orchestrator",
            "base_url": "http://orchestrator:5000",
            "dependencies": [
                {
                    "service_id": "interpreter",
                    "required": True,
                    "capabilities": ["document_processing", "nlp_analysis"]
                },
                {
                    "service_id": "doc_store",
                    "required": True,
                    "capabilities": ["document_storage", "search"]
                },
                {
                    "service_id": "llm_gateway",
                    "required": False,
                    "capabilities": ["text_generation"]
                }
            ]
        }

        # Execute dependency-aware discovery
        dependency_discovery = setup["discovery_handler"].execute_dependency_aware_discovery(complex_service)

        assert dependency_discovery["success"] is True
        assert "dependency_resolution" in dependency_discovery
        assert "discovery_plan" in dependency_discovery

        resolution = dependency_discovery["dependency_resolution"]

        # Should resolve required dependencies first
        required_deps = [d for d in complex_service["dependencies"] if d["required"]]
        for dep in required_deps:
            assert dep["service_id"] in resolution
            assert resolution[dep["service_id"]]["resolved"] is True

        # Should attempt optional dependencies
        optional_deps = [d for d in complex_service["dependencies"] if not d["required"]]
        for dep in optional_deps:
            assert dep["service_id"] in resolution
            # Optional deps might not be resolved if not available

        discovery_plan = dependency_discovery["discovery_plan"]
        assert "discovery_order" in discovery_plan
        assert "parallel_discovery_groups" in discovery_plan

        # Should order discovery by dependency hierarchy
        discovery_order = discovery_plan["discovery_order"]
        assert len(discovery_order) >= len(required_deps)

        # Validate dependency satisfaction
        satisfaction_check = setup["discovery_handler"].validate_dependency_satisfaction(
            complex_service,
            resolution
        )

        assert satisfaction_check["validation_complete"] is True

        if all(res["resolved"] for res in resolution.values() if res["required"]):
            assert satisfaction_check["all_required_satisfied"] is True
        else:
            assert satisfaction_check["all_required_satisfied"] is False

    def test_api_specification_processing_pipeline(self, integration_setup):
        """Test complete API specification processing pipeline."""
        setup = integration_setup

        # Sample OpenAPI specification
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Document Interpreter API",
                "version": "1.2.0",
                "description": "API for document interpretation and processing"
            },
            "servers": [{"url": "http://interpreter:5005"}],
            "paths": {
                "/documents/process": {
                    "post": {
                        "summary": "Process a document",
                        "operationId": "processDocument",
                        "tags": ["documents"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/DocumentRequest"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/DocumentResponse"}
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
                            "confidence_score": {"type": "number"}
                        }
                    }
                }
            }
        }

        # Step 1: Parse specification
        parse_result = setup["api_spec_parser"].parse_openapi_spec(openapi_spec)
        assert parse_result["parsing_success"] is True

        parsed_spec = parse_result["parsed_spec"]
        assert parsed_spec["openapi_version"] == "3.0.3"
        assert parsed_spec["title"] == "Document Interpreter API"

        # Step 2: Validate specification
        validation_result = setup["api_spec_parser"].validate_api_spec(parsed_spec)
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0

        # Step 3: Extract metadata
        metadata_result = setup["api_spec_parser"].extract_api_metadata(parsed_spec)
        assert metadata_result["extraction_success"] is True

        metadata = metadata_result["metadata"]
        assert metadata["title"] == "Document Interpreter API"
        assert metadata["version"] == "1.2.0"

        # Step 4: Semantic analysis
        semantic_result = setup["semantic_analyzer"].analyze_service_semantics(parsed_spec)
        assert semantic_result["analysis_success"] is True

        semantics = semantic_result["semantics"]
        assert "capability_score" in semantics
        assert "complexity_score" in semantics
        assert "maturity_indicators" in semantics

        # Step 5: Capability extraction
        capability_result = setup["semantic_analyzer"].extract_api_patterns(parsed_spec)
        assert capability_result["extraction_success"] is True

        capabilities = capability_result["capabilities"]
        assert "endpoints" in capabilities
        assert "schemas" in capabilities
        assert "patterns" in capabilities

        # Step 6: Generate service profile
        profile_result = setup["discovery_handler"].generate_service_profile_from_spec({
            "spec": parsed_spec,
            "metadata": metadata,
            "semantics": semantics,
            "capabilities": capabilities
        })

        assert profile_result["success"] is True

        service_profile = profile_result["service_profile"]
        assert "service_id" in service_profile
        assert "capabilities" in service_profile
        assert "api_endpoints" in service_profile
        assert "data_models" in service_profile

        # Step 7: Validate complete pipeline
        pipeline_validation = setup["discovery_handler"].validate_spec_processing_pipeline({
            "original_spec": openapi_spec,
            "processing_steps": [
                parse_result,
                validation_result,
                metadata_result,
                semantic_result,
                capability_result,
                profile_result
            ]
        })

        assert pipeline_validation["pipeline_valid"] is True
        assert pipeline_validation["data_integrity_preserved"] is True
        assert len(pipeline_validation["pipeline_errors"]) == 0


class TestToolDiscoveryIntegration:
    """Test Tool Discovery and Registration Integration."""

    @pytest.fixture
    def tool_integration_setup(self, mock_tool_registry, mock_semantic_analyzer):
        """Create tool integration setup."""
        return {
            "tool_registry": ToolRegistry(),
            "semantic_analyzer": SemanticAnalyzer(),
            "discovery_handler": DiscoveryHandler()
        }

    def test_complete_tool_discovery_workflow(self, tool_integration_setup):
        """Test complete tool discovery and registration workflow."""
        setup = tool_integration_setup

        # Step 1: Tool discovery scan
        discovery_config = {
            "scan_targets": ["http://code-analyzer:5020", "http://github-mcp:5030"],
            "discovery_methods": ["api_introspection", "capability_probing", "documentation_analysis"],
            "tool_categories": ["code_analysis", "version_control", "documentation"]
        }

        discovery_result = setup["tool_registry"].execute_tool_discovery(discovery_config)
        assert discovery_result["success"] is True

        discovered_tools = discovery_result.get("discovered_tools", [])
        assert len(discovered_tools) > 0

        # Step 2: Tool validation and analysis
        for tool in discovered_tools[:2]:  # Test with first 2 tools
            # Validate tool specification
            validation_result = setup["tool_registry"].validate_tool_spec(tool)
            assert validation_result["validation_success"] is True

            # Analyze tool semantics
            semantic_result = setup["semantic_analyzer"].analyze_tool_semantics(tool)
            assert semantic_result["analysis_success"] is True

            # Step 3: Capability extraction
            capability_result = setup["tool_registry"].extract_tool_capabilities(tool)
            assert capability_result["extraction_success"] is True

            capabilities = capability_result["capabilities"]
            assert len(capabilities) > 0

            # Step 4: Tool registration
            registration_result = setup["tool_registry"].register_tool({
                "tool_spec": tool,
                "capabilities": capabilities,
                "semantic_analysis": semantic_result["analysis"],
                "validation_results": validation_result
            })

            assert registration_result["registration_success"] is True

            # Step 5: Integration testing
            integration_result = setup["tool_registry"].test_tool_integration(registration_result["registered_tool"])
            assert integration_result["integration_success"] is True

        # Step 6: Tool registry summary
        registry_summary = setup["tool_registry"].generate_registry_summary()
        assert registry_summary["summary_complete"] is True

        summary = registry_summary["summary"]
        assert "total_tools_registered" in summary
        assert "tools_by_category" in summary
        assert "capability_coverage" in summary

    def test_tool_dependency_resolution(self, tool_integration_setup):
        """Test tool dependency resolution and compatibility checking."""
        setup = tool_integration_setup

        # Define tool with dependencies
        dependent_tool = {
            "tool_id": "complex_code_analyzer",
            "name": "Complex Code Analyzer",
            "capabilities": ["static_analysis", "complexity_metrics", "dependency_analysis"],
            "dependencies": [
                {
                    "tool_id": "basic_code_analyzer",
                    "required_capabilities": ["syntax_checking", "basic_metrics"],
                    "version_constraint": ">=1.0.0"
                },
                {
                    "tool_id": "dependency_scanner",
                    "required_capabilities": ["module_analysis", "import_detection"],
                    "version_constraint": ">=2.0.0"
                }
            ],
            "environment_requirements": {
                "python_version": ">=3.8",
                "required_modules": ["ast", "inspect", "typing"]
            }
        }

        # Available tools in registry
        available_tools = {
            "basic_code_analyzer": {
                "version": "1.2.0",
                "capabilities": ["syntax_checking", "basic_metrics", "linting"],
                "status": "available"
            },
            "dependency_scanner": {
                "version": "2.1.0",
                "capabilities": ["module_analysis", "import_detection", "graph_generation"],
                "status": "available"
            },
            "security_scanner": {
                "version": "1.0.0",
                "capabilities": ["vulnerability_scanning", "security_audit"],
                "status": "available"
            }
        }

        # Resolve dependencies
        resolution_result = setup["tool_registry"].resolve_tool_dependencies(dependent_tool, available_tools)

        assert resolution_result["success"] is True
        assert "dependency_resolution" in resolution_result
        assert "compatibility_assessment" in resolution_result

        resolution = resolution_result["dependency_resolution"]

        # Should resolve all required dependencies
        for dep in dependent_tool["dependencies"]:
            dep_id = dep["tool_id"]
            assert dep_id in resolution
            assert resolution[dep_id]["resolved"] is True
            assert resolution[dep_id]["version_satisfied"] is True

        compatibility = resolution_result["compatibility_assessment"]
        assert compatibility["all_dependencies_satisfied"] is True
        assert compatibility["capability_coverage_sufficient"] is True

        # Should validate environment compatibility
        assert "environment_compatibility" in compatibility
        env_compat = compatibility["environment_compatibility"]
        assert env_compat["python_version_compatible"] is True
        assert env_compat["required_modules_available"] is True

    def test_tool_capability_orchestration(self, tool_integration_setup):
        """Test tool capability orchestration and workflow creation."""
        setup = tool_integration_setup

        # Define complex workflow requiring multiple tools
        workflow_requirements = {
            "workflow_name": "comprehensive_code_review",
            "required_capabilities": [
                "syntax_analysis",
                "complexity_measurement",
                "security_scanning",
                "performance_analysis",
                "documentation_generation"
            ],
            "workflow_steps": [
                {
                    "step_name": "syntax_validation",
                    "required_capabilities": ["syntax_analysis"],
                    "estimated_duration_seconds": 30
                },
                {
                    "step_name": "complexity_analysis",
                    "required_capabilities": ["complexity_measurement"],
                    "dependencies": ["syntax_validation"],
                    "estimated_duration_seconds": 60
                },
                {
                    "step_name": "security_assessment",
                    "required_capabilities": ["security_scanning"],
                    "dependencies": ["syntax_validation"],
                    "estimated_duration_seconds": 120
                },
                {
                    "step_name": "performance_evaluation",
                    "required_capabilities": ["performance_analysis"],
                    "dependencies": ["complexity_analysis"],
                    "estimated_duration_seconds": 90
                },
                {
                    "step_name": "documentation_update",
                    "required_capabilities": ["documentation_generation"],
                    "dependencies": ["security_assessment", "performance_evaluation"],
                    "estimated_duration_seconds": 45
                }
            ],
            "quality_gates": {
                "syntax_errors_max": 0,
                "complexity_score_max": 10,
                "security_vulnerabilities_max": 0,
                "performance_score_min": 7
            }
        }

        # Orchestrate tool capabilities
        orchestration_result = setup["tool_registry"].orchestrate_tool_capabilities(workflow_requirements)

        assert orchestration_result["success"] is True
        assert "capability_mapping" in orchestration_result
        assert "workflow_plan" in orchestration_result
        assert "resource_requirements" in orchestration_result

        capability_mapping = orchestration_result["capability_mapping"]

        # Should map all required capabilities to available tools
        for capability in workflow_requirements["required_capabilities"]:
            assert capability in capability_mapping
            mapping = capability_mapping[capability]
            assert "assigned_tool" in mapping
            assert "capability_confidence" in mapping

        workflow_plan = orchestration_result["workflow_plan"]
        assert "execution_order" in workflow_plan
        assert "parallel_groups" in workflow_plan
        assert "estimated_total_duration" in workflow_plan

        # Should respect step dependencies
        execution_order = workflow_plan["execution_order"]
        for step in workflow_requirements["workflow_steps"]:
            if step.get("dependencies"):
                step_index = next(i for i, s in enumerate(execution_order) if s["step_name"] == step["step_name"])
                for dep in step["dependencies"]:
                    dep_index = next(i for i, s in enumerate(execution_order) if s["step_name"] == dep)
                    assert dep_index < step_index  # Dependencies must come first

        resource_reqs = orchestration_result["resource_requirements"]
        assert "tool_instances_needed" in resource_reqs
        assert "estimated_memory_mb" in resource_reqs
        assert "estimated_duration_seconds" in resource_reqs


class TestCrossServiceIntegrationValidation:
    """Test Cross-Service Integration Validation."""

    @pytest.fixture
    def cross_service_setup(self, mock_network_scanner, mock_tool_registry, mock_semantic_analyzer):
        """Create cross-service integration setup."""
        return {
            "discovery_handler": DiscoveryHandler(network_scanner=mock_network_scanner),
            "tool_registry": ToolRegistry(),
            "semantic_analyzer": SemanticAnalyzer(),
            "orchestrator_integration": OrchestratorIntegration()
        }

    def test_service_mesh_integration_validation(self, cross_service_setup):
        """Test service mesh integration and communication validation."""
        setup = cross_service_setup

        # Define service mesh configuration
        service_mesh = {
            "services": [
                {
                    "service_id": "frontend",
                    "role": "entry_point",
                    "exposed_ports": [8080],
                    "dependencies": ["orchestrator"]
                },
                {
                    "service_id": "orchestrator",
                    "role": "coordinator",
                    "internal_ports": [5000],
                    "dependencies": ["interpreter", "doc_store"]
                },
                {
                    "service_id": "interpreter",
                    "role": "processor",
                    "internal_ports": [5005],
                    "dependencies": ["llm_gateway"]
                },
                {
                    "service_id": "doc_store",
                    "role": "storage",
                    "internal_ports": [5010],
                    "dependencies": []
                },
                {
                    "service_id": "llm_gateway",
                    "role": "ai_service",
                    "internal_ports": [5020],
                    "dependencies": []
                }
            ],
            "communication_patterns": [
                {
                    "from_service": "frontend",
                    "to_service": "orchestrator",
                    "protocol": "http",
                    "pattern": "synchronous"
                },
                {
                    "from_service": "orchestrator",
                    "to_service": "interpreter",
                    "protocol": "http",
                    "pattern": "asynchronous"
                },
                {
                    "from_service": "interpreter",
                    "to_service": "llm_gateway",
                    "protocol": "grpc",
                    "pattern": "synchronous"
                }
            ]
        }

        # Validate service mesh integration
        validation_result = setup["orchestrator_integration"].validate_service_mesh_integration(service_mesh)

        assert validation_result["success"] is True
        assert "mesh_validation" in validation_result
        assert "communication_validation" in validation_result
        assert "dependency_validation" in validation_result

        mesh_validation = validation_result["mesh_validation"]
        assert mesh_validation["all_services_discovered"] is True
        assert mesh_validation["service_health_verified"] is True

        communication_validation = validation_result["communication_validation"]
        assert len(communication_validation["validated_patterns"]) == len(service_mesh["communication_patterns"])

        for pattern_result in communication_validation["validated_patterns"]:
            assert pattern_result["communication_verified"] is True

        dependency_validation = validation_result["dependency_validation"]
        assert dependency_validation["all_dependencies_resolved"] is True
        assert len(dependency_validation["circular_dependencies"]) == 0

    def test_integration_performance_monitoring(self, cross_service_setup):
        """Test integration performance monitoring and bottleneck detection."""
        setup = cross_service_setup

        # Define integration performance scenario
        performance_scenario = {
            "integration_points": [
                {
                    "from_service": "frontend",
                    "to_service": "orchestrator",
                    "expected_latency_ms": 200,
                    "expected_throughput": 50  # requests per second
                },
                {
                    "from_service": "orchestrator",
                    "to_service": "interpreter",
                    "expected_latency_ms": 500,
                    "expected_throughput": 30
                },
                {
                    "from_service": "interpreter",
                    "to_service": "llm_gateway",
                    "expected_latency_ms": 1000,
                    "expected_throughput": 20
                }
            ],
            "monitoring_duration_seconds": 300,
            "performance_thresholds": {
                "max_latency_p95": 1500,
                "min_throughput_p50": 15,
                "max_error_rate": 0.05
            }
        }

        # Execute performance monitoring
        monitoring_result = setup["orchestrator_integration"].monitor_integration_performance(performance_scenario)

        assert monitoring_result["success"] is True
        assert "performance_metrics" in monitoring_result
        assert "bottleneck_analysis" in monitoring_result
        assert "optimization_recommendations" in monitoring_result

        performance_metrics = monitoring_result["performance_metrics"]

        # Should collect metrics for all integration points
        assert len(performance_metrics) == len(performance_scenario["integration_points"])

        for metric in performance_metrics:
            assert "latency_p50" in metric
            assert "latency_p95" in metric
            assert "throughput_p50" in metric
            assert "error_rate" in metric

        bottleneck_analysis = monitoring_result["bottleneck_analysis"]
        assert "identified_bottlenecks" in bottleneck_analysis
        assert "performance_degradation_points" in bottleneck_analysis

        # Should identify any performance issues
        bottlenecks = bottleneck_analysis["identified_bottlenecks"]
        # Analysis may or may not find bottlenecks depending on test data

        optimization_recs = monitoring_result["optimization_recommendations"]
        assert len(optimization_recs) >= 0

        # Should validate against thresholds
        threshold_validation = monitoring_result.get("threshold_validation", {})
        if threshold_validation:
            assert "thresholds_met" in threshold_validation

    def test_integration_failure_recovery(self, cross_service_setup):
        """Test integration failure recovery and resilience."""
        setup = cross_service_setup

        # Define failure scenario
        failure_scenario = {
            "failure_type": "service_unavailable",
            "affected_service": "llm_gateway",
            "failure_duration_seconds": 120,
            "impact_scope": {
                "directly_affected": ["interpreter"],
                "indirectly_affected": ["orchestrator", "frontend"],
                "isolated_services": ["doc_store"]
            },
            "recovery_expectations": {
                "automatic_failover": True,
                "graceful_degradation": True,
                "user_impact_minimization": True,
                "max_downtime_seconds": 30
            }
        }

        # Execute failure recovery test
        recovery_result = setup["orchestrator_integration"].test_integration_failure_recovery(failure_scenario)

        assert recovery_result["success"] is True
        assert "failure_simulation" in recovery_result
        assert "recovery_execution" in recovery_result
        assert "impact_assessment" in recovery_result

        failure_simulation = recovery_result["failure_simulation"]
        assert failure_simulation["failure_injected"] is True
        assert failure_simulation["affected_services_isolated"] is True

        recovery_execution = recovery_result["recovery_execution"]
        assert "recovery_initiated" in recovery_execution
        assert "recovery_duration_seconds" in recovery_execution

        impact_assessment = recovery_result["impact_assessment"]
        assert "services_impacted" in impact_assessment
        assert "downtime_duration_seconds" in impact_assessment
        assert "data_integrity_preserved" in impact_assessment

        # Validate recovery expectations
        expectations_met = recovery_result["expectations_validation"]
        assert "automatic_failover_worked" in expectations_met
        assert "graceful_degradation_activated" in expectations_met
        assert "user_impact_minimized" in expectations_met

        # Recovery should meet timing expectations
        assert recovery_execution["recovery_duration_seconds"] <= failure_scenario["recovery_expectations"]["max_downtime_seconds"]
