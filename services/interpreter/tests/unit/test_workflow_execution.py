"""Unit Tests for Workflow Execution in Interpreter Service.

This module tests workflow execution capabilities including:
- Workflow step orchestration and sequencing
- Document processing pipelines
- Error handling and recovery in workflows
- Performance monitoring and optimization
- Workflow state management and persistence
- Real-time execution tracking

Tests cover the complete workflow execution engine.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from modules.workflow_execution_engine import WorkflowExecutionEngine
from modules.workflow_builder import WorkflowBuilder
from modules.workflow_dispatcher import WorkflowDispatcher
from modules.models import WorkflowExecution, WorkflowContext


class TestWorkflowExecutionEngine:
    """Test Workflow Execution Engine functionality."""

    @pytest.fixture
    def execution_engine(self, mock_repository, mock_event_bus):
        """Create workflow execution engine instance."""
        return WorkflowExecutionEngine(mock_repository, mock_event_bus)

    def test_workflow_execution_initialization(self, execution_engine, sample_workflow_execution):
        """Test workflow execution initialization."""
        execution = sample_workflow_execution

        assert execution.execution_id is not None
        assert execution.workflow_id is not None
        assert execution.status == "running"
        assert execution.started_at <= datetime.now()
        assert execution.progress_percentage >= 0

    def test_step_execution_sequencing(self, execution_engine):
        """Test workflow step execution sequencing."""
        workflow_steps = [
            {"id": "step_1", "name": "Init", "depends_on": []},
            {"id": "step_2", "name": "Process", "depends_on": ["step_1"]},
            {"id": "step_3", "name": "Finalize", "depends_on": ["step_2"]}
        ]

        execution_order = execution_engine.calculate_execution_order(workflow_steps)

        # Verify dependency ordering
        assert execution_order[0]["id"] == "step_1"  # No dependencies first
        assert execution_order[1]["id"] == "step_2"  # Depends on step_1
        assert execution_order[2]["id"] == "step_3"  # Depends on step_2

    def test_parallel_step_execution(self, execution_engine):
        """Test parallel execution of independent steps."""
        workflow_steps = [
            {"id": "step_1", "name": "Init", "depends_on": []},
            {"id": "step_2a", "name": "Process A", "depends_on": ["step_1"]},
            {"id": "step_2b", "name": "Process B", "depends_on": ["step_1"]},
            {"id": "step_3", "name": "Finalize", "depends_on": ["step_2a", "step_2b"]}
        ]

        parallel_groups = execution_engine.identify_parallel_groups(workflow_steps)

        # Should identify parallel execution opportunities
        assert len(parallel_groups) >= 2

        # Step 1 should be in first group
        assert "step_1" in parallel_groups[0]

        # Steps 2a and 2b should be in same parallel group
        step_2_group = next(group for group in parallel_groups if "step_2a" in group)
        assert "step_2b" in step_2_group

        # Step 3 should be in later group
        step_3_group = next(group for group in parallel_groups if "step_3" in group)
        assert step_3_group != parallel_groups[0]

    def test_workflow_error_handling_and_recovery(self, execution_engine):
        """Test error handling and recovery in workflow execution."""
        workflow_steps = [
            {"id": "step_1", "name": "Success Step", "depends_on": []},
            {"id": "step_2", "name": "Failing Step", "depends_on": ["step_1"]},
            {"id": "step_3", "name": "Recovery Step", "depends_on": ["step_2"]},
            {"id": "step_4", "name": "Final Step", "depends_on": ["step_3"]}
        ]

        # Simulate step failure and recovery
        execution_context = {
            "step_failures": {"step_2": "Connection timeout"},
            "recovery_actions": {"step_2": "retry_with_backoff"}
        }

        recovery_plan = execution_engine.generate_error_recovery_plan(
            workflow_steps, execution_context
        )

        assert "recovery_strategy" in recovery_plan
        assert "affected_steps" in recovery_plan
        assert "estimated_recovery_time" in recovery_plan

        # Should identify failing step
        assert "step_2" in recovery_plan["affected_steps"]

        # Should suggest retry strategy
        assert recovery_plan["recovery_strategy"] == "retry_with_backoff"

    def test_workflow_performance_monitoring(self, execution_engine, sample_workflow_execution):
        """Test workflow performance monitoring."""
        execution = sample_workflow_execution

        performance_metrics = execution_engine.collect_performance_metrics(execution)

        assert "execution_time" in performance_metrics
        assert "step_performance" in performance_metrics
        assert "resource_utilization" in performance_metrics
        assert "bottlenecks" in performance_metrics

        # Should calculate execution time
        assert performance_metrics["execution_time"] > 0

        # Should identify step performance
        step_perf = performance_metrics["step_performance"]
        assert len(step_perf) == len(execution.step_results)

    def test_workflow_state_persistence(self, execution_engine, sample_workflow_execution):
        """Test workflow state persistence."""
        execution = sample_workflow_execution

        # Persist execution state
        persistence_result = execution_engine.persist_execution_state(execution)

        assert persistence_result["persisted"] is True
        assert "state_id" in persistence_result
        assert persistence_result["timestamp"] is not None

        # Retrieve execution state
        retrieved_state = execution_engine.retrieve_execution_state(execution.execution_id)

        assert retrieved_state is not None
        assert retrieved_state.execution_id == execution.execution_id
        assert retrieved_state.status == execution.status

    def test_real_time_execution_tracking(self, execution_engine, sample_workflow_execution):
        """Test real-time execution tracking and updates."""
        execution = sample_workflow_execution

        # Subscribe to execution updates
        update_callback = MagicMock()
        execution_engine.subscribe_to_updates(execution.execution_id, update_callback)

        # Simulate execution progress
        progress_updates = [
            {"step": "step_1", "status": "completed", "progress": 33.3},
            {"step": "step_2", "status": "running", "progress": 66.7},
            {"step": "step_3", "status": "pending", "progress": 100.0}
        ]

        for update in progress_updates:
            execution_engine.publish_execution_update(execution.execution_id, update)

            # Verify callback was called
            update_callback.assert_called()

        # Verify final state
        final_status = execution_engine.get_execution_status(execution.execution_id)
        assert final_status["progress_percentage"] == 100.0


class TestWorkflowBuilder:
    """Test Workflow Builder functionality."""

    @pytest.fixture
    def workflow_builder(self):
        """Create workflow builder instance."""
        return WorkflowBuilder()

    def test_dynamic_workflow_construction(self, workflow_builder):
        """Test dynamic workflow construction from requirements."""
        requirements = {
            "task_type": "document_analysis",
            "input_type": "pdf_document",
            "analysis_depth": "comprehensive",
            "output_format": "structured_report",
            "performance_requirements": {
                "max_execution_time": 300,
                "quality_threshold": 0.85
            }
        }

        constructed_workflow = workflow_builder.construct_workflow_from_requirements(requirements)

        assert "workflow_id" in constructed_workflow
        assert "steps" in constructed_workflow
        assert "estimated_complexity" in constructed_workflow
        assert "performance_characteristics" in constructed_workflow

        # Should include appropriate steps for document analysis
        steps = constructed_workflow["steps"]
        step_names = [step["name"] for step in steps]

        assert any("extract" in name.lower() for name in step_names)  # Text extraction
        assert any("analyze" in name.lower() for name in step_names)  # Content analysis
        assert any("generate" in name.lower() for name in step_names)  # Report generation

    def test_workflow_validation_and_optimization(self, workflow_builder):
        """Test workflow validation and optimization."""
        workflow_definition = {
            "name": "Test Workflow",
            "steps": [
                {"id": "step_1", "name": "Start", "type": "init", "config": {}},
                {"id": "step_2", "name": "Process", "type": "processing", "config": {}, "depends_on": ["step_1"]},
                {"id": "step_3", "name": "End", "type": "final", "config": {}, "depends_on": ["step_2"]},
                {"id": "step_4", "name": "Unused Step", "type": "utility", "config": {}}  # No dependencies
            ]
        }

        validation_result = workflow_builder.validate_and_optimize_workflow(workflow_definition)

        assert validation_result["is_valid"] is True
        assert "optimized_workflow" in validation_result
        assert "optimization_suggestions" in validation_result

        # Should identify unused step
        suggestions = validation_result["optimization_suggestions"]
        unused_suggestions = [s for s in suggestions if "unused" in s.lower()]
        assert len(unused_suggestions) > 0

        # Optimized workflow should be more efficient
        optimized = validation_result["optimized_workflow"]
        assert len(optimized["steps"]) <= len(workflow_definition["steps"])  # May remove unused steps

    def test_workflow_template_application(self, workflow_builder):
        """Test workflow template application and customization."""
        base_template = "document_processing_pipeline"
        customizations = {
            "add_steps": [
                {"name": "Custom Analysis", "type": "analysis", "config": {"method": "custom"}}
            ],
            "modify_steps": {
                "text_extraction": {"config": {"ocr_engine": "advanced"}}
            },
            "remove_steps": ["basic_validation"],
            "parameter_overrides": {
                "quality_threshold": 0.9,
                "timeout_seconds": 600
            }
        }

        customized_workflow = workflow_builder.apply_template_with_customizations(
            base_template, customizations
        )

        assert "template_applied" in customized_workflow
        assert "customizations_applied" in customized_workflow
        assert "final_workflow" in customized_workflow

        final_workflow = customized_workflow["final_workflow"]

        # Should include custom step
        step_names = [step["name"] for step in final_workflow["steps"]]
        assert "Custom Analysis" in step_names

        # Should not include removed step
        assert "Basic Validation" not in step_names

        # Should have overridden parameters
        assert final_workflow["parameters"]["quality_threshold"] == 0.9

    def test_workflow_cost_and_performance_estimation(self, workflow_builder):
        """Test workflow cost and performance estimation."""
        workflow_definition = {
            "name": "Cost Estimation Test",
            "steps": [
                {"type": "extraction", "config": {"method": "ocr"}},
                {"type": "analysis", "config": {"model": "gpt-4"}},
                {"type": "generation", "config": {"format": "pdf"}}
            ]
        }

        execution_context = {
            "input_size": "large",  # 100MB document
            "priority": "high",
            "infrastructure": "premium"
        }

        estimation = workflow_builder.estimate_workflow_cost_and_performance(
            workflow_definition, execution_context
        )

        assert "estimated_cost" in estimation
        assert "estimated_duration" in estimation
        assert "resource_requirements" in estimation
        assert "performance_characteristics" in estimation

        # Should estimate realistic costs
        cost = estimation["estimated_cost"]
        assert cost["total_dollars"] > 0
        assert "breakdown" in cost

        # Should estimate duration
        duration = estimation["estimated_duration"]
        assert duration["total_seconds"] > 0
        assert "step_breakdown" in duration


class TestWorkflowDispatcher:
    """Test Workflow Dispatcher functionality."""

    @pytest.fixture
    def workflow_dispatcher(self, mock_repository, mock_event_bus):
        """Create workflow dispatcher instance."""
        return WorkflowDispatcher(mock_repository, mock_event_bus)

    def test_workflow_routing_and_assignment(self, workflow_dispatcher):
        """Test workflow routing and assignment to execution engines."""
        workflow_request = {
            "workflow_type": "document_analysis",
            "priority": "high",
            "resource_requirements": {
                "cpu": "high",
                "memory": "4GB",
                "gpu": False
            },
            "execution_constraints": {
                "max_duration": 300,
                "cost_limit": 50.0
            }
        }

        routing_decision = workflow_dispatcher.route_workflow(workflow_request)

        assert "assigned_engine" in routing_decision
        assert "routing_reason" in routing_decision
        assert "estimated_performance" in routing_decision
        assert "resource_allocation" in routing_decision

        # High priority should get premium resources
        assert routing_decision["resource_allocation"]["priority"] == "high"

    def test_load_balancing_across_engines(self, workflow_dispatcher):
        """Test load balancing across multiple execution engines."""
        engine_status = {
            "engine_1": {"current_load": 30, "capacity": 100, "performance_score": 0.9},
            "engine_2": {"current_load": 80, "capacity": 100, "performance_score": 0.85},
            "engine_3": {"current_load": 10, "capacity": 100, "performance_score": 0.95}
        }

        workflow_queue = [
            {"id": "wf_1", "priority": "high", "complexity": "medium"},
            {"id": "wf_2", "priority": "normal", "complexity": "low"},
            {"id": "wf_3", "priority": "low", "complexity": "high"}
        ]

        load_distribution = workflow_dispatcher.balance_load_across_engines(
            engine_status, workflow_queue
        )

        assert "assignments" in load_distribution
        assert "load_balance_score" in load_distribution
        assert "performance_optimization" in load_distribution

        assignments = load_distribution["assignments"]

        # High priority should go to best available engine
        high_priority_assignment = next(a for a in assignments if a["workflow_id"] == "wf_1")
        assert high_priority_assignment["assigned_engine"] in ["engine_1", "engine_3"]  # Lower load

        # Should achieve good load balance
        assert load_distribution["load_balance_score"] > 0.7

    def test_workflow_queue_management(self, workflow_dispatcher):
        """Test workflow queue management and prioritization."""
        queued_workflows = [
            {"id": "wf_1", "priority": "low", "submitted_at": datetime.now() - timedelta(minutes=30)},
            {"id": "wf_2", "priority": "high", "submitted_at": datetime.now() - timedelta(minutes=5)},
            {"id": "wf_3", "priority": "normal", "submitted_at": datetime.now() - timedelta(minutes=15)},
            {"id": "wf_4", "priority": "high", "submitted_at": datetime.now() - timedelta(minutes=10)}
        ]

        prioritized_queue = workflow_dispatcher.prioritize_workflow_queue(queued_workflows)

        # High priority workflows should be first
        high_priority_workflows = [wf for wf in prioritized_queue if wf["priority"] == "high"]
        assert len(high_priority_workflows) == 2

        # Within same priority, earlier submission should come first
        high_priority_sorted = sorted(high_priority_workflows, key=lambda x: prioritized_queue.index(x))
        assert high_priority_sorted[0]["id"] == "wf_2"  # Submitted 5 min ago
        assert high_priority_sorted[1]["id"] == "wf_4"  # Submitted 10 min ago

    def test_workflow_timeout_and_deadline_management(self, workflow_dispatcher):
        """Test workflow timeout and deadline management."""
        active_workflows = [
            {
                "id": "wf_1",
                "started_at": datetime.now() - timedelta(minutes=10),
                "timeout_minutes": 15,
                "progress": 60.0
            },
            {
                "id": "wf_2",
                "started_at": datetime.now() - timedelta(minutes=25),
                "timeout_minutes": 20,
                "progress": 80.0
            },
            {
                "id": "wf_3",
                "started_at": datetime.now() - timedelta(minutes=5),
                "timeout_minutes": 30,
                "progress": 20.0
            }
        ]

        timeout_analysis = workflow_dispatcher.analyze_workflow_timeouts(active_workflows)

        assert "timeout_risks" in timeout_analysis
        assert "deadline_projections" in timeout_analysis
        assert "timeout_prevention_actions" in timeout_analysis

        timeout_risks = timeout_analysis["timeout_risks"]

        # wf_2 should be at risk (25 min > 20 min timeout)
        wf_2_risk = next(risk for risk in timeout_risks if risk["workflow_id"] == "wf_2")
        assert wf_2_risk["risk_level"] == "high"

        # wf_1 should be low risk (10 min < 15 min timeout)
        wf_1_risk = next(risk for risk in timeout_risks if risk["workflow_id"] == "wf_1")
        assert wf_1_risk["risk_level"] == "low"

    def test_workflow_resource_optimization(self, workflow_dispatcher):
        """Test workflow resource optimization and allocation."""
        workflow_requirements = {
            "cpu_cores": 4,
            "memory_gb": 8,
            "gpu_required": False,
            "network_bandwidth": "high",
            "storage_gb": 50
        }

        available_resources = {
            "total_cpu_cores": 32,
            "total_memory_gb": 128,
            "gpu_instances": 2,
            "network_capacity_gbps": 10,
            "storage_tb": 2
        }

        resource_allocation = workflow_dispatcher.optimize_resource_allocation(
            workflow_requirements, available_resources
        )

        assert "allocated_resources" in resource_allocation
        assert "optimization_score" in resource_allocation
        assert "efficiency_metrics" in resource_allocation

        allocated = resource_allocation["allocated_resources"]

        # Should allocate requested resources
        assert allocated["cpu_cores"] >= workflow_requirements["cpu_cores"]
        assert allocated["memory_gb"] >= workflow_requirements["memory_gb"]

        # Should achieve good optimization score
        assert resource_allocation["optimization_score"] > 0.8

    def test_workflow_failure_analysis_and_learning(self, workflow_dispatcher):
        """Test workflow failure analysis and learning."""
        failure_history = [
            {
                "workflow_id": "wf_1",
                "failure_reason": "resource_exhaustion",
                "failure_point": "step_3",
                "resource_usage": {"cpu": 95, "memory": 90},
                "error_pattern": "memory_limit_exceeded"
            },
            {
                "workflow_id": "wf_2",
                "failure_reason": "timeout",
                "failure_point": "step_2",
                "resource_usage": {"cpu": 30, "memory": 40},
                "error_pattern": "processing_timeout"
            },
            {
                "workflow_id": "wf_3",
                "failure_reason": "resource_exhaustion",
                "failure_point": "step_4",
                "resource_usage": {"cpu": 92, "memory": 88},
                "error_pattern": "memory_limit_exceeded"
            }
        ]

        failure_analysis = workflow_dispatcher.analyze_workflow_failures(failure_history)

        assert "failure_patterns" in failure_analysis
        assert "root_cause_analysis" in failure_analysis
        assert "preventive_measures" in failure_analysis
        assert "improvement_recommendations" in failure_analysis

        failure_patterns = failure_analysis["failure_patterns"]

        # Should identify resource exhaustion as common pattern
        resource_failures = [p for p in failure_patterns if "resource" in p["pattern"].lower()]
        assert len(resource_failures) > 0

        # Should recommend preventive measures
        preventive_measures = failure_analysis["preventive_measures"]
        assert len(preventive_measures) > 0

        # Should include resource monitoring recommendations
        resource_monitoring = [m for m in preventive_measures if "resource" in m.lower()]
        assert len(resource_monitoring) > 0


class TestDocumentProcessingWorkflows:
    """Test document processing specific workflows."""

    @pytest.fixture
    def document_processor(self, mock_llm_gateway, mock_document_store):
        """Create document processing workflow instance."""
        return WorkflowExecutionEngine(
            repository=MagicMock(),
            event_bus=MagicMock(),
            llm_gateway=mock_llm_gateway,
            document_store=mock_document_store
        )

    def test_pdf_document_processing_pipeline(self, document_processor):
        """Test complete PDF document processing pipeline."""
        document_input = {
            "document_url": "https://example.com/document.pdf",
            "processing_options": {
                "extract_text": True,
                "perform_ocr": False,
                "analyze_content": True,
                "generate_summary": True,
                "extract_metadata": True
            }
        }

        processing_result = document_processor.execute_document_processing_pipeline(document_input)

        assert "processing_id" in processing_result
        assert "stages_completed" in processing_result
        assert "extracted_content" in processing_result
        assert "analysis_results" in processing_result
        assert "generated_summary" in processing_result

        stages = processing_result["stages_completed"]
        assert "text_extraction" in stages
        assert "content_analysis" in stages
        assert "summary_generation" in stages

        # Should have extracted meaningful content
        content = processing_result["extracted_content"]
        assert len(content["text"]) > 0
        assert "pages" in content

        # Should have analysis results
        analysis = processing_result["analysis_results"]
        assert "sentiment" in analysis
        assert "topics" in analysis
        assert "complexity_score" in analysis

    def test_multi_format_document_processing(self, document_processor):
        """Test processing documents in multiple formats."""
        test_documents = [
            {"url": "doc1.pdf", "format": "pdf", "expected_stages": ["ocr", "text_extraction", "analysis"]},
            {"url": "doc2.docx", "format": "docx", "expected_stages": ["text_extraction", "analysis"]},
            {"url": "doc3.txt", "format": "txt", "expected_stages": ["text_extraction", "analysis"]},
            {"url": "doc4.html", "format": "html", "expected_stages": ["parsing", "text_extraction", "analysis"]}
        ]

        for doc in test_documents:
            result = document_processor.process_document_by_format(doc["url"], doc["format"])

            assert result["format"] == doc["format"]
            assert result["processing_success"] is True

            completed_stages = result["completed_stages"]
            for expected_stage in doc["expected_stages"]:
                assert expected_stage in completed_stages

    def test_document_quality_assessment(self, document_processor):
        """Test document quality assessment during processing."""
        quality_test_cases = [
            {
                "document": "high_quality_doc.pdf",
                "expected_quality": "high",
                "characteristics": {
                    "text_clarity": 0.9,
                    "structure_score": 0.85,
                    "content_completeness": 0.95
                }
            },
            {
                "document": "medium_quality_doc.pdf",
                "expected_quality": "medium",
                "characteristics": {
                    "text_clarity": 0.7,
                    "structure_score": 0.6,
                    "content_completeness": 0.75
                }
            },
            {
                "document": "low_quality_doc.pdf",
                "expected_quality": "low",
                "characteristics": {
                    "text_clarity": 0.4,
                    "structure_score": 0.3,
                    "content_completeness": 0.5
                }
            }
        ]

        for test_case in quality_test_cases:
            quality_assessment = document_processor.assess_document_quality(test_case["document"])

            assert quality_assessment["overall_quality"] == test_case["expected_quality"]

            quality_scores = quality_assessment["quality_scores"]
            for characteristic, expected_score in test_case["characteristics"].items():
                actual_score = quality_scores[characteristic]
                assert abs(actual_score - expected_score) < 0.1  # Close match

    def test_document_processing_error_recovery(self, document_processor):
        """Test error recovery in document processing workflows."""
        problematic_documents = [
            {
                "url": "corrupted.pdf",
                "issue": "corruption",
                "recovery_strategy": "alternative_extraction"
            },
            {
                "url": "large_document.pdf",
                "issue": "size_limit",
                "recovery_strategy": "chunking_processing"
            },
            {
                "url": "unsupported_format.xyz",
                "issue": "unsupported_format",
                "recovery_strategy": "format_conversion"
            }
        ]

        for doc in problematic_documents:
            processing_result = document_processor.process_with_error_recovery(
                doc["url"], error_context={"issue_type": doc["issue"]}
            )

            assert processing_result["recovery_attempted"] is True
            assert processing_result["recovery_strategy"] == doc["recovery_strategy"]
            assert processing_result["final_status"] in ["recovered", "failed_after_recovery"]

            if processing_result["final_status"] == "recovered":
                assert "recovered_content" in processing_result

    def test_document_processing_performance_optimization(self, document_processor):
        """Test performance optimization in document processing."""
        performance_scenarios = [
            {
                "document_size": "small",
                "complexity": "low",
                "expected_duration": "< 30s",
                "optimization_focus": "speed"
            },
            {
                "document_size": "medium",
                "complexity": "medium",
                "expected_duration": "30-120s",
                "optimization_focus": "balance"
            },
            {
                "document_size": "large",
                "complexity": "high",
                "expected_duration": "> 120s",
                "optimization_focus": "quality"
            }
        ]

        for scenario in performance_scenarios:
            optimization_result = document_processor.optimize_processing_performance(scenario)

            assert "performance_config" in optimization_result
            assert "estimated_duration_seconds" in optimization_result
            assert "resource_allocation" in optimization_result

            # Verify optimization focus
            config = optimization_result["performance_config"]
            if scenario["optimization_focus"] == "speed":
                assert config["parallel_processing"] is True
                assert config["caching_enabled"] is True
            elif scenario["optimization_focus"] == "quality":
                assert config["detailed_analysis"] is True
                assert config["multiple_models"] is True
