#!/usr/bin/env python3
"""
Integration Test Scenarios for Orchestrator Service

Tests complete end-to-end scenarios involving multiple services and complex workflows.
"""

import asyncio
import pytest
import json
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add services to path
sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services')

from orchestrator.modules.workflow_management.service import WorkflowManagementService
from orchestrator.modules.workflow_management.models import WorkflowStatus, WorkflowExecutionStatus
from shared.event_streaming import EventStreamProcessor, StreamEvent, EventType, EventPriority
from shared.enterprise_service_mesh import EnterpriseServiceMesh, ServiceIdentity


class TestDocumentAnalysisWorkflow:
    """Test complete document analysis workflow scenario."""

    @pytest.fixture
    async def orchestrator_setup(self):
        """Set up orchestrator with mocked services."""
        workflow_service = WorkflowManagementService()
        event_stream = EventStreamProcessor()
        service_mesh = EnterpriseServiceMesh()

        return {
            "workflow_service": workflow_service,
            "event_stream": event_stream,
            "service_mesh": service_mesh
        }

    @pytest.mark.asyncio
    async def test_document_analysis_workflow_execution(self, orchestrator_setup):
        """Test complete document analysis workflow from ingestion to reporting."""
        components = orchestrator_setup
        workflow_service = components["workflow_service"]

        # Create comprehensive document analysis workflow
        workflow_data = {
            "name": "Complete Document Analysis Workflow",
            "description": "End-to-end document analysis with multiple service integrations",
            "parameters": [
                {
                    "name": "document_url",
                    "type": "string",
                    "description": "URL of document to analyze",
                    "required": True
                },
                {
                    "name": "analysis_depth",
                    "type": "string",
                    "description": "Depth of analysis to perform",
                    "required": False,
                    "default_value": "comprehensive",
                    "allowed_values": ["basic", "standard", "comprehensive"]
                },
                {
                    "name": "generate_report",
                    "type": "boolean",
                    "description": "Whether to generate final report",
                    "required": False,
                    "default_value": True
                }
            ],
            "actions": [
                {
                    "action_id": "fetch_document",
                    "action_type": "service_call",
                    "name": "Fetch Document",
                    "description": "Fetch document from provided URL",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/fetch",
                        "method": "POST",
                        "parameters": {
                            "url": "{{document_url}}",
                            "type": "document"
                        }
                    }
                },
                {
                    "action_id": "store_document",
                    "action_type": "service_call",
                    "name": "Store Document",
                    "description": "Store document in document store",
                    "config": {
                        "service": "doc_store",
                        "endpoint": "/documents",
                        "method": "POST",
                        "parameters": {
                            "content": "{{fetch_document.response.content}}",
                            "metadata": {
                                "source_url": "{{document_url}}",
                                "analysis_depth": "{{analysis_depth}}"
                            }
                        }
                    },
                    "depends_on": ["fetch_document"]
                },
                {
                    "action_id": "analyze_quality",
                    "action_type": "service_call",
                    "name": "Analyze Quality",
                    "description": "Analyze document quality and consistency",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/analyze",
                        "method": "POST",
                        "parameters": {
                            "document_id": "{{store_document.response.document_id}}",
                            "analysis_types": ["quality", "consistency"]
                        }
                    },
                    "depends_on": ["store_document"]
                },
                {
                    "action_id": "generate_summary",
                    "action_type": "service_call",
                    "name": "Generate Summary",
                    "description": "Generate summary of analysis results",
                    "config": {
                        "service": "summarizer_hub",
                        "endpoint": "/summarize",
                        "method": "POST",
                        "parameters": {
                            "content": "{{analyze_quality.response.findings}}",
                            "max_length": 500
                        }
                    },
                    "depends_on": ["analyze_quality"]
                },
                {
                    "action_id": "create_report",
                    "action_type": "service_call",
                    "name": "Create Report",
                    "description": "Create comprehensive analysis report",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/generate_report",
                        "method": "POST",
                        "parameters": {
                            "document_id": "{{store_document.response.document_id}}",
                            "analysis_results": "{{analyze_quality.response}}",
                            "summary": "{{generate_summary.response.summary}}",
                            "report_format": "comprehensive"
                        }
                    },
                    "depends_on": ["analyze_quality", "generate_summary"],
                    "condition": "generate_report == true"
                },
                {
                    "action_id": "send_notification",
                    "action_type": "notification",
                    "name": "Send Completion Notification",
                    "description": "Notify stakeholders of completion",
                    "config": {
                        "message": "Document analysis completed for {{document_url}}. Report available: {{create_report.response.report_url}}",
                        "channels": ["log", "notification_service"],
                        "priority": "normal"
                    },
                    "depends_on": ["create_report"]
                }
            ]
        }

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "document_analysis_test"
        )
        assert success == True
        assert len(workflow.actions) == 6

        # Verify execution plan
        execution_plan = workflow.get_execution_plan()
        assert len(execution_plan) >= 4  # Should have multiple dependency levels

        print(f"Document analysis workflow created with {len(execution_plan)} execution levels")

        # Activate workflow
        workflow.status = WorkflowStatus.ACTIVE
        await workflow_service.repository.save_workflow_definition(workflow)

        # Execute workflow with test parameters
        execution_params = {
            "document_url": "https://example.com/test-document.pdf",
            "analysis_depth": "comprehensive",
            "generate_report": True
        }

        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id, execution_params, "integration_test"
        )
        assert success == True

        # Verify execution started
        assert execution.status == WorkflowExecutionStatus.RUNNING
        assert execution.input_parameters == execution_params

        print(f"Document analysis workflow execution started: {execution.execution_id}")


class TestPRConfidenceAnalysisWorkflow:
    """Test PR confidence analysis workflow scenario."""

    @pytest.fixture
    async def pr_workflow_setup(self):
        """Set up PR confidence analysis workflow."""
        workflow_service = WorkflowManagementService()

        # Create PR confidence analysis workflow
        workflow_data = {
            "name": "PR Confidence Analysis Workflow",
            "description": "Analyze PR confidence against Jira requirements",
            "parameters": [
                {
                    "name": "pr_number",
                    "type": "integer",
                    "description": "Pull request number",
                    "required": True
                },
                {
                    "name": "repository",
                    "type": "string",
                    "description": "Repository name (owner/repo)",
                    "required": True
                },
                {
                    "name": "jira_ticket",
                    "type": "string",
                    "description": "Associated Jira ticket ID",
                    "required": False
                }
            ],
            "actions": [
                {
                    "action_id": "fetch_pr_data",
                    "action_type": "service_call",
                    "name": "Fetch PR Data",
                    "description": "Fetch pull request data from GitHub",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/github/pr",
                        "method": "GET",
                        "parameters": {
                            "pr_number": "{{pr_number}}",
                            "repository": "{{repository}}"
                        }
                    }
                },
                {
                    "action_id": "fetch_jira_data",
                    "action_type": "service_call",
                    "name": "Fetch Jira Data",
                    "description": "Fetch Jira ticket data if provided",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/jira/issue",
                        "method": "GET",
                        "parameters": {
                            "issue_id": "{{jira_ticket}}"
                        }
                    },
                    "condition": "jira_ticket is not None and jira_ticket != ''"
                },
                {
                    "action_id": "analyze_pr_changes",
                    "action_type": "service_call",
                    "name": "Analyze PR Changes",
                    "description": "Analyze the code changes in the PR",
                    "config": {
                        "service": "code_analyzer",
                        "endpoint": "/analyze_changes",
                        "method": "POST",
                        "parameters": {
                            "pr_data": "{{fetch_pr_data.response}}",
                            "repository": "{{repository}}"
                        }
                    },
                    "depends_on": ["fetch_pr_data"]
                },
                {
                    "action_id": "cross_reference_analysis",
                    "action_type": "service_call",
                    "name": "Cross-Reference Analysis",
                    "description": "Cross-reference PR with Jira requirements",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/cross_reference",
                        "method": "POST",
                        "parameters": {
                            "pr_data": "{{fetch_pr_data.response}}",
                            "jira_data": "{{fetch_jira_data.response}}",
                            "code_analysis": "{{analyze_pr_changes.response}}"
                        }
                    },
                    "depends_on": ["fetch_pr_data", "analyze_pr_changes"]
                },
                {
                    "action_id": "calculate_confidence",
                    "action_type": "service_call",
                    "name": "Calculate Confidence Score",
                    "description": "Calculate confidence score for PR completion",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/calculate_confidence",
                        "method": "POST",
                        "parameters": {
                            "cross_reference_results": "{{cross_reference_analysis.response}}",
                            "code_quality_score": "{{analyze_pr_changes.response.quality_score}}"
                        }
                    },
                    "depends_on": ["cross_reference_analysis"]
                },
                {
                    "action_id": "generate_confidence_report",
                    "action_type": "service_call",
                    "name": "Generate Confidence Report",
                    "description": "Generate detailed confidence report",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/generate_confidence_report",
                        "method": "POST",
                        "parameters": {
                            "confidence_score": "{{calculate_confidence.response.score}}",
                            "analysis_details": "{{calculate_confidence.response.details}}",
                            "recommendations": "{{calculate_confidence.response.recommendations}}",
                            "pr_number": "{{pr_number}}",
                            "repository": "{{repository}}"
                        }
                    },
                    "depends_on": ["calculate_confidence"]
                },
                {
                    "action_id": "notify_stakeholders",
                    "action_type": "notification",
                    "name": "Notify Stakeholders",
                    "description": "Notify relevant stakeholders of confidence analysis",
                    "config": {
                        "message": "PR #{{pr_number}} confidence analysis complete. Score: {{calculate_confidence.response.score}}/100. Report: {{generate_confidence_report.response.report_url}}",
                        "channels": ["notification_service", "log"],
                        "priority": "high",
                        "recipients": ["pr_author", "reviewers", "product_manager"]
                    },
                    "depends_on": ["generate_confidence_report"]
                }
            ]
        }

        return {
            "workflow_service": workflow_service,
            "workflow_data": workflow_data
        }

    @pytest.mark.asyncio
    async def test_pr_confidence_workflow_creation(self, pr_workflow_setup):
        """Test PR confidence workflow creation and validation."""
        components = pr_workflow_setup
        workflow_service = components["workflow_service"]
        workflow_data = components["workflow_data"]

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "pr_confidence_test"
        )
        assert success == True
        assert len(workflow.actions) == 7

        # Verify complex dependency structure
        execution_plan = workflow.get_execution_plan()
        assert len(execution_plan) >= 5  # Complex dependency chain

        # Verify conditional actions
        conditional_actions = [a for a in workflow.actions if a.condition]
        assert len(conditional_actions) >= 1  # Should have conditional Jira fetching

        print(f"PR confidence workflow created with {len(execution_plan)} execution levels")

    @pytest.mark.asyncio
    async def test_pr_confidence_workflow_execution(self, pr_workflow_setup):
        """Test PR confidence workflow execution with different scenarios."""
        components = pr_workflow_setup
        workflow_service = components["workflow_service"]
        workflow_data = components["workflow_data"]

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "pr_confidence_exec_test"
        )
        assert success == True

        # Activate workflow
        workflow.status = WorkflowStatus.ACTIVE
        await workflow_service.repository.save_workflow_definition(workflow)

        # Test execution with Jira ticket
        execution_params = {
            "pr_number": 123,
            "repository": "myorg/myrepo",
            "jira_ticket": "PROJ-456"
        }

        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id, execution_params, "pr_test"
        )
        assert success == True
        assert execution.input_parameters == execution_params

        # Test execution without Jira ticket
        execution_params_no_jira = {
            "pr_number": 124,
            "repository": "myorg/myrepo"
        }

        success, message, execution2 = await workflow_service.execute_workflow(
            workflow.workflow_id, execution_params_no_jira, "pr_test_no_jira"
        )
        assert success == True

        print(f"PR confidence workflow executions started: {execution.execution_id}, {execution2.execution_id}")


class TestMultiServiceOrchestration:
    """Test complex multi-service orchestration scenarios."""

    @pytest.fixture
    async def multi_service_setup(self):
        """Set up multi-service orchestration test environment."""
        workflow_service = WorkflowManagementService()
        event_stream = EventStreamProcessor()

        return {
            "workflow_service": workflow_service,
            "event_stream": event_stream
        }

    @pytest.mark.asyncio
    async def test_github_jira_integration_workflow(self, multi_service_setup):
        """Test workflow that integrates GitHub, Jira, and documentation systems."""
        components = multi_service_setup
        workflow_service = components["workflow_service"]

        # Create complex integration workflow
        workflow_data = {
            "name": "GitHub-Jira Integration Workflow",
            "description": "Complete integration between GitHub PRs, Jira tickets, and documentation",
            "parameters": [
                {
                    "name": "github_pr_url",
                    "type": "string",
                    "description": "GitHub pull request URL",
                    "required": True
                },
                {
                    "name": "jira_ticket_key",
                    "type": "string",
                    "description": "Jira ticket key",
                    "required": True
                },
                {
                    "name": "documentation_paths",
                    "type": "array",
                    "description": "Paths to relevant documentation",
                    "required": False,
                    "default_value": []
                }
            ],
            "actions": [
                {
                    "action_id": "parse_github_url",
                    "action_type": "transform_data",
                    "name": "Parse GitHub URL",
                    "description": "Extract repository and PR number from GitHub URL",
                    "config": {
                        "transformation_type": "parse_github_url",
                        "input_field": "github_pr_url"
                    }
                },
                {
                    "action_id": "fetch_github_pr",
                    "action_type": "service_call",
                    "name": "Fetch GitHub PR",
                    "description": "Fetch pull request data from GitHub",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/github/pr",
                        "method": "GET",
                        "parameters": {
                            "repository": "{{parse_github_url.repository}}",
                            "pr_number": "{{parse_github_url.pr_number}}"
                        }
                    },
                    "depends_on": ["parse_github_url"]
                },
                {
                    "action_id": "fetch_jira_ticket",
                    "action_type": "service_call",
                    "name": "Fetch Jira Ticket",
                    "description": "Fetch Jira ticket data",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/jira/issue",
                        "method": "GET",
                        "parameters": {
                            "issue_key": "{{jira_ticket_key}}"
                        }
                    }
                },
                {
                    "action_id": "fetch_documentation",
                    "action_type": "service_call",
                    "name": "Fetch Documentation",
                    "description": "Fetch relevant documentation",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/confluence/search",
                        "method": "POST",
                        "parameters": {
                            "query": "{{jira_ticket_key}}",
                            "paths": "{{documentation_paths}}"
                        }
                    },
                    "condition": "len(documentation_paths) > 0"
                },
                {
                    "action_id": "analyze_code_changes",
                    "action_type": "service_call",
                    "name": "Analyze Code Changes",
                    "description": "Analyze the code changes in the PR",
                    "config": {
                        "service": "code_analyzer",
                        "endpoint": "/analyze_pr",
                        "method": "POST",
                        "parameters": {
                            "pr_data": "{{fetch_github_pr.response}}",
                            "repository": "{{parse_github_url.repository}}"
                        }
                    },
                    "depends_on": ["fetch_github_pr"]
                },
                {
                    "action_id": "cross_reference_analysis",
                    "action_type": "service_call",
                    "name": "Cross-Reference Analysis",
                    "description": "Cross-reference PR changes with Jira requirements and documentation",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/comprehensive_analysis",
                        "method": "POST",
                        "parameters": {
                            "pr_data": "{{fetch_github_pr.response}}",
                            "jira_data": "{{fetch_jira_ticket.response}}",
                            "documentation_data": "{{fetch_documentation.response}}",
                            "code_analysis": "{{analyze_code_changes.response}}"
                        }
                    },
                    "depends_on": ["fetch_github_pr", "fetch_jira_ticket", "analyze_code_changes"]
                },
                {
                    "action_id": "generate_integration_report",
                    "action_type": "service_call",
                    "name": "Generate Integration Report",
                    "description": "Generate comprehensive integration analysis report",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/generate_integration_report",
                        "method": "POST",
                        "parameters": {
                            "github_pr": "{{fetch_github_pr.response}}",
                            "jira_ticket": "{{fetch_jira_ticket.response}}",
                            "documentation": "{{fetch_documentation.response}}",
                            "analysis_results": "{{cross_reference_analysis.response}}",
                            "recommendations": "{{cross_reference_analysis.response.recommendations}}"
                        }
                    },
                    "depends_on": ["cross_reference_analysis"]
                },
                {
                    "action_id": "update_jira_ticket",
                    "action_type": "service_call",
                    "name": "Update Jira Ticket",
                    "description": "Update Jira ticket with analysis results",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/jira/update",
                        "method": "PUT",
                        "parameters": {
                            "issue_key": "{{jira_ticket_key}}",
                            "comment": "Analysis completed: {{generate_integration_report.response.summary}}",
                            "labels": ["analyzed", "pr-linked"],
                            "custom_fields": {
                                "analysis_report_url": "{{generate_integration_report.response.report_url}}",
                                "confidence_score": "{{cross_reference_analysis.response.confidence_score}}"
                            }
                        }
                    },
                    "depends_on": ["generate_integration_report"]
                },
                {
                    "action_id": "notify_team",
                    "action_type": "notification",
                    "name": "Notify Development Team",
                    "description": "Notify team of integration analysis completion",
                    "config": {
                        "message": "GitHub-Jira integration analysis completed for PR {{parse_github_url.pr_number}} and ticket {{jira_ticket_key}}. Report: {{generate_integration_report.response.report_url}}",
                        "channels": ["slack", "email", "notification_service"],
                        "priority": "normal",
                        "recipients": ["development_team", "product_owner", "qa_team"]
                    },
                    "depends_on": ["update_jira_ticket"]
                }
            ]
        }

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "github_jira_integration_test"
        )
        assert success == True
        assert len(workflow.actions) == 9

        # Verify complex workflow structure
        execution_plan = workflow.get_execution_plan()
        assert len(execution_plan) >= 6  # Complex multi-level dependencies

        # Count conditional actions
        conditional_actions = [a for a in workflow.actions if a.condition]
        assert len(conditional_actions) >= 1  # Documentation fetching is conditional

        print(f"GitHub-Jira integration workflow created with {len(execution_plan)} execution levels")

        # Test workflow validation
        is_valid, errors = workflow.validate_parameters({
            "github_pr_url": "https://github.com/myorg/myrepo/pull/123",
            "jira_ticket_key": "PROJ-456",
            "documentation_paths": ["/docs/api", "/docs/architecture"]
        })
        assert is_valid == True
        assert len(errors) == 0


class TestEventDrivenWorkflows:
    """Test event-driven workflow scenarios."""

    @pytest.fixture
    async def event_driven_setup(self):
        """Set up event-driven workflow testing."""
        workflow_service = WorkflowManagementService()
        event_stream = EventStreamProcessor()

        return {
            "workflow_service": workflow_service,
            "event_stream": event_stream
        }

    @pytest.mark.asyncio
    async def test_event_triggered_workflow_execution(self, event_driven_setup):
        """Test workflows triggered by events."""
        components = event_driven_setup
        workflow_service = components["workflow_service"]
        event_stream = components["event_stream"]

        # Create event-triggered workflow
        workflow_data = {
            "name": "Event-Driven Notification Workflow",
            "description": "Workflow triggered by system events",
            "parameters": [
                {
                    "name": "event_type",
                    "type": "string",
                    "description": "Type of event that triggered workflow",
                    "required": True
                },
                {
                    "name": "event_data",
                    "type": "object",
                    "description": "Event data payload",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "process_event",
                    "action_type": "transform_data",
                    "name": "Process Event Data",
                    "description": "Process and transform event data",
                    "config": {
                        "transformation_type": "extract_event_info",
                        "input_data": "{{event_data}}"
                    }
                },
                {
                    "action_id": "check_event_severity",
                    "action_type": "transform_data",
                    "name": "Check Event Severity",
                    "description": "Determine event severity and required actions",
                    "config": {
                        "transformation_type": "severity_analysis",
                        "event_type": "{{event_type}}",
                        "event_data": "{{event_data}}"
                    }
                },
                {
                    "action_id": "escalate_high_priority",
                    "action_type": "notification",
                    "name": "Escalate High Priority Events",
                    "description": "Send high-priority notifications",
                    "config": {
                        "message": "HIGH PRIORITY EVENT: {{event_type}} - {{process_event.summary}}",
                        "channels": ["slack", "sms", "notification_service"],
                        "priority": "critical",
                        "recipients": ["on_call_engineer", "devops_team"]
                    },
                    "condition": "check_event_severity.level == 'high' or check_event_severity.level == 'critical'",
                    "depends_on": ["check_event_severity"]
                },
                {
                    "action_id": "handle_normal_events",
                    "action_type": "notification",
                    "name": "Handle Normal Priority Events",
                    "description": "Send normal-priority notifications",
                    "config": {
                        "message": "Event notification: {{event_type}} - {{process_event.summary}}",
                        "channels": ["slack", "log"],
                        "priority": "normal",
                        "recipients": ["development_team"]
                    },
                    "condition": "check_event_severity.level == 'normal' or check_event_severity.level == 'low'",
                    "depends_on": ["check_event_severity"]
                },
                {
                    "action_id": "log_event",
                    "action_type": "service_call",
                    "name": "Log Event",
                    "description": "Log event to centralized logging service",
                    "config": {
                        "service": "logging_service",
                        "endpoint": "/events",
                        "method": "POST",
                        "parameters": {
                            "event_type": "{{event_type}}",
                            "event_data": "{{event_data}}",
                            "processed_data": "{{process_event}}",
                            "severity": "{{check_event_severity.level}}",
                            "timestamp": "{{event_data.timestamp}}"
                        }
                    },
                    "depends_on": ["process_event", "check_event_severity"]
                }
            ]
        }

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "event_driven_test"
        )
        assert success == True

        # Activate workflow
        workflow.status = WorkflowStatus.ACTIVE
        await workflow_service.repository.save_workflow_definition(workflow)

        # Simulate event triggering workflow execution
        event_data = {
            "event_type": "system_error",
            "event_data": {
                "error_code": "E001",
                "message": "Database connection failed",
                "service": "user_service",
                "timestamp": "2024-01-15T10:30:00Z",
                "severity": "high"
            }
        }

        # Execute workflow based on event
        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id, event_data, "event_system"
        )
        assert success == True

        print(f"Event-driven workflow executed: {execution.execution_id}")

        # Verify event correlation
        correlation_events = await event_stream.get_event_correlation(execution.execution_id)
        assert correlation_events is not None


class TestWorkflowPerformanceAndScalability:
    """Test workflow performance and scalability."""

    @pytest.fixture
    async def performance_setup(self):
        """Set up performance testing environment."""
        workflow_service = WorkflowManagementService()

        return {
            "workflow_service": workflow_service
        }

    @pytest.mark.asyncio
    async def test_workflow_creation_performance(self, performance_setup):
        """Test workflow creation performance with multiple workflows."""
        components = performance_setup
        workflow_service = components["workflow_service"]

        start_time = time.time()

        # Create multiple workflows concurrently
        creation_tasks = []
        for i in range(10):
            workflow_data = {
                "name": f"Performance Test Workflow {i}",
                "description": f"Workflow {i} for performance testing",
                "parameters": [
                    {
                        "name": "test_input",
                        "type": "string",
                        "required": True
                    }
                ],
                "actions": [
                    {
                        "action_id": "perf_action",
                        "action_type": "notification",
                        "name": "Performance Action",
                        "config": {
                            "message": "Processing {{test_input}}"
                        }
                    }
                ]
            }

            task = asyncio.create_task(
                workflow_service.create_workflow(workflow_data, f"perf_user_{i}")
            )
            creation_tasks.append(task)

        # Wait for all creations to complete
        results = await asyncio.gather(*creation_tasks)
        end_time = time.time()

        # Analyze results
        successful_creations = sum(1 for success, _, _ in results if success)
        total_time = end_time - start_time
        avg_time_per_workflow = total_time / len(results)

        assert successful_creations == len(results)  # All should succeed
        assert total_time < 5.0  # Should complete within 5 seconds
        assert avg_time_per_workflow < 0.5  # Less than 500ms per workflow

        print(f"Performance test: {successful_creations}/{len(results)} workflows created in {total_time:.2f}s")
        print(".3f")

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, performance_setup):
        """Test concurrent workflow execution performance."""
        components = performance_setup
        workflow_service = components["workflow_service"]

        # Create a test workflow
        workflow_data = {
            "name": "Concurrent Execution Test",
            "description": "Workflow for concurrent execution testing",
            "parameters": [
                {
                    "name": "execution_id",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "concurrent_action",
                    "action_type": "notification",
                    "name": "Concurrent Action",
                    "config": {
                        "message": "Concurrent execution {{execution_id}}"
                    }
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "concurrent_test"
        )
        assert success == True

        # Activate workflow
        workflow.status = WorkflowStatus.ACTIVE
        await workflow_service.repository.save_workflow_definition(workflow)

        start_time = time.time()

        # Execute multiple workflows concurrently
        execution_tasks = []
        for i in range(20):
            execution_params = {"execution_id": f"exec_{i}"}
            task = asyncio.create_task(
                workflow_service.execute_workflow(
                    workflow.workflow_id, execution_params, f"user_{i}"
                )
            )
            execution_tasks.append(task)

        # Wait for all executions to complete
        results = await asyncio.gather(*execution_tasks)
        end_time = time.time()

        # Analyze results
        successful_executions = sum(1 for success, _, _ in results if success)
        total_time = end_time - start_time
        executions_per_second = len(results) / total_time

        assert successful_executions == len(results)  # All should succeed
        assert total_time < 10.0  # Should complete within 10 seconds
        assert executions_per_second >= 2.0  # At least 2 executions per second

        print(f"Concurrent execution test: {successful_executions}/{len(results)} executions in {total_time:.2f}s")
        print(".1f")


if __name__ == "__main__":
    # Run integration test smoke tests
    async def smoke_test():
        print("🧪 Running Integration Scenario Smoke Tests...")

        workflow_service = WorkflowManagementService()

        # Test simple integration workflow
        workflow_data = {
            "name": "Integration Smoke Test",
            "description": "Basic integration test workflow",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "smoke_action",
                    "action_type": "notification",
                    "name": "Smoke Test Action",
                    "config": {
                        "message": "Integration test: {{test_param}}"
                    }
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "smoke_test"
        )

        if success:
            print("✅ Integration smoke test passed - workflow created")
        else:
            print(f"❌ Integration smoke test failed: {message}")

    asyncio.run(smoke_test())
