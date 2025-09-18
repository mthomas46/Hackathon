"""Tests for workflow-triggered analysis functionality in Analysis Service.

Tests the workflow trigger module and its integration with the analysis service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from services.analysis_service.modules.workflow_trigger import (
    WorkflowTrigger,
    process_workflow_event
)


@pytest.fixture
def sample_pull_request_event():
    """Create sample pull request event data."""
    return {
        'event_type': 'pull_request',
        'action': 'opened',
        'repository': 'my-org/docs-repo',
        'branch': 'feature/add-api-docs',
        'base_branch': 'main',
        'commit_sha': 'abc123def456',
        'pr_number': 42,
        'author': 'developer@example.com',
        'title': 'Add comprehensive API documentation',
        'description': 'This PR adds detailed API documentation for the new endpoints.',
        'files_changed': [
            'docs/api/v2/endpoints.md',
            'docs/api/v2/authentication.md',
            'docs/examples/python_client.py'
        ],
        'files_added': ['docs/api/v2/endpoints.md'],
        'files_modified': ['docs/api/v2/authentication.md'],
        'files_deleted': [],
        'lines_changed': 150,
        'labels': ['documentation', 'enhancement']
    }


@pytest.fixture
def sample_push_event():
    """Create sample push event data."""
    return {
        'event_type': 'push',
        'action': 'push',
        'repository': 'my-org/docs-repo',
        'branch': 'main',
        'commit_sha': 'def789ghi012',
        'author': 'ci-bot@example.com',
        'files_changed': [
            'docs/getting-started.md',
            'docs/troubleshooting.md'
        ],
        'files_added': [],
        'files_modified': ['docs/getting-started.md', 'docs/troubleshooting.md'],
        'files_deleted': [],
        'lines_changed': 25
    }


@pytest.fixture
def sample_release_event():
    """Create sample release event data."""
    return {
        'event_type': 'release',
        'action': 'published',
        'repository': 'my-org/docs-repo',
        'branch': 'main',
        'commit_sha': 'jkl345mno678',
        'author': 'release-manager@example.com',
        'title': 'v2.1.0 Release',
        'description': 'Major release with new documentation features',
        'files_changed': [],  # Release events typically don't include file changes
        'lines_changed': 0
    }


class TestWorkflowTrigger:
    """Test the WorkflowTrigger class."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test successful initialization of the workflow trigger."""
        trigger = WorkflowTrigger()
        assert trigger.initialized is True
        assert len(trigger.event_handlers) > 0
        assert len(trigger.trigger_rules) > 0
        assert len(trigger.analysis_queues) > 0

    @pytest.mark.asyncio
    async def test_analyze_event_context_pull_request(self, sample_pull_request_event):
        """Test event context analysis for pull request events."""
        trigger = WorkflowTrigger()

        context = trigger._analyze_event_context(sample_pull_request_event)

        assert context['event_type'] == 'pull_request'
        assert context['event_action'] == 'opened'
        assert context['priority'] == 'high'
        assert 'quality_check' in context['analysis_types']
        assert 'consistency_check' in context['analysis_types']
        assert len(context['file_changes']) > 0
        assert context['has_documentation_changes'] is True

    @pytest.mark.asyncio
    async def test_analyze_event_context_push(self, sample_push_event):
        """Test event context analysis for push events."""
        trigger = WorkflowTrigger()

        context = trigger._analyze_event_context(sample_push_event)

        assert context['event_type'] == 'push'
        assert context['event_action'] == 'push'
        assert context['priority'] == 'medium'
        assert 'change_analysis' in context['analysis_types']
        assert context['has_documentation_changes'] is True

    @pytest.mark.asyncio
    async def test_analyze_file_changes(self, sample_pull_request_event):
        """Test file changes analysis."""
        trigger = WorkflowTrigger()

        file_analysis = trigger._analyze_file_changes(sample_pull_request_event)

        assert file_analysis['total_files'] == 3
        assert file_analysis['documentation_files'] == ['docs/api/v2/endpoints.md', 'docs/api/v2/authentication.md']
        assert file_analysis['code_files'] == ['docs/examples/python_client.py']
        assert file_analysis['has_documentation_changes'] is True
        assert file_analysis['has_code_changes'] is True

    @pytest.mark.asyncio
    async def test_analyze_branch_context(self, sample_pull_request_event):
        """Test branch context analysis."""
        trigger = WorkflowTrigger()

        branch_context = trigger._analyze_branch_context(sample_pull_request_event)

        assert branch_context['branch_name'] == 'feature/add-api-docs'
        assert branch_context['base_branch'] == 'main'
        assert branch_context['branch_type'] == 'feature'
        assert branch_context['is_feature_branch'] is True

    @pytest.mark.asyncio
    async def test_assess_change_size(self, sample_pull_request_event):
        """Test change size assessment."""
        trigger = WorkflowTrigger()

        size = trigger._assess_change_size(sample_pull_request_event)

        assert size == 'medium'  # 150 lines changed

        # Test small change
        small_event = sample_pull_request_event.copy()
        small_event['lines_changed'] = 5
        small_size = trigger._assess_change_size(small_event)
        assert small_size == 'small'

        # Test large change
        large_event = sample_pull_request_event.copy()
        large_event['lines_changed'] = 1500
        large_size = trigger._assess_change_size(large_event)
        assert large_size == 'large'

    @pytest.mark.asyncio
    async def test_determine_urgency(self, sample_pull_request_event, sample_release_event):
        """Test urgency determination."""
        trigger = WorkflowTrigger()

        pr_urgency = trigger._determine_urgency(sample_pull_request_event)
        assert pr_urgency == 'medium'

        release_urgency = trigger._determine_urgency(sample_release_event)
        assert release_urgency == 'high'

    @pytest.mark.asyncio
    async def test_create_analysis_plan(self, sample_pull_request_event):
        """Test analysis plan creation."""
        trigger = WorkflowTrigger()

        event_context = trigger._analyze_event_context(sample_pull_request_event)
        plan = trigger._create_analysis_plan(event_context)

        assert 'analysis_types' in plan
        assert 'priority' in plan
        assert 'processing_mode' in plan
        assert 'time_window' in plan
        assert 'quality_checks' in plan
        assert 'consistency_checks' in plan

        assert plan['priority'] == 'high'
        assert len(plan['quality_checks']) > 0
        assert len(plan['consistency_checks']) > 0

    @pytest.mark.asyncio
    async def test_estimate_processing_time(self, sample_pull_request_event):
        """Test processing time estimation."""
        trigger = WorkflowTrigger()

        event_context = trigger._analyze_event_context(sample_pull_request_event)
        plan = trigger._create_analysis_plan(event_context)

        estimated_time = trigger._estimate_processing_time(plan)

        assert isinstance(estimated_time, float)
        assert estimated_time > 0
        assert estimated_time < 60  # Should be reasonable time

    @pytest.mark.asyncio
    async def test_process_workflow_event(self, sample_pull_request_event):
        """Test workflow event processing."""
        trigger = WorkflowTrigger()

        result = await trigger.process_workflow_event(sample_pull_request_event)

        assert 'workflow_id' in result
        assert 'status' in result
        assert 'priority' in result
        assert 'analysis_types' in result
        assert 'estimated_processing_time' in result
        assert 'processing_time' in result

        assert result['status'] == 'accepted'
        assert result['priority'] == 'high'
        assert len(result['analysis_types']) > 0

        # Check that workflow was stored
        workflow_id = result['workflow_id']
        assert workflow_id in trigger.active_workflows

    @pytest.mark.asyncio
    async def test_get_workflow_status(self, sample_pull_request_event):
        """Test workflow status retrieval."""
        trigger = WorkflowTrigger()

        # First process an event
        result = await trigger.process_workflow_event(sample_pull_request_event)
        workflow_id = result['workflow_id']

        # Get status
        status = trigger.get_workflow_status(workflow_id)

        assert status is not None
        assert status['workflow_id'] == workflow_id
        assert status['status'] in ['queued', 'processing', 'completed']
        assert 'analysis_plan' in status
        assert 'event_context' in status

    @pytest.mark.asyncio
    async def test_get_queue_status(self, sample_pull_request_event, sample_push_event):
        """Test queue status retrieval."""
        trigger = WorkflowTrigger()

        # Process multiple events
        await trigger.process_workflow_event(sample_pull_request_event)
        await trigger.process_workflow_event(sample_push_event)

        queue_status = trigger.get_queue_status()

        assert isinstance(queue_status, dict)
        assert 'critical' in queue_status
        assert 'high' in queue_status
        assert 'medium' in queue_status
        assert 'low' in queue_status

        # Should have items in queues
        total_queued = sum(queue_status.values())
        assert total_queued >= 2

    @pytest.mark.asyncio
    async def test_get_event_history(self, sample_pull_request_event):
        """Test event history retrieval."""
        trigger = WorkflowTrigger()

        # Process an event
        await trigger.process_workflow_event(sample_pull_request_event)

        history = trigger.get_event_history(limit=10)

        assert isinstance(history, list)
        assert len(history) > 0
        assert 'workflow_id' in history[0]
        assert 'event_type' in history[0]
        assert 'event_action' in history[0]
        assert 'timestamp' in history[0]

    @pytest.mark.asyncio
    async def test_configure_webhook_secret(self):
        """Test webhook secret configuration."""
        trigger = WorkflowTrigger()

        secret = "my-webhook-secret-12345"
        trigger.configure_webhook_secret(secret)

        assert trigger.webhook_secret == secret

    @pytest.mark.asyncio
    async def test_clear_old_workflows(self, sample_pull_request_event):
        """Test clearing old workflows."""
        trigger = WorkflowTrigger()

        # Process an event and manually set old timestamp
        await trigger.process_workflow_event(sample_pull_request_event)
        workflow_id = list(trigger.active_workflows.keys())[0]
        trigger.active_workflows[workflow_id]['created_at'] = 0  # Very old timestamp

        # Clear old workflows
        cleared_count = trigger.clear_old_workflows(max_age_hours=0)

        assert cleared_count >= 1
        assert len(trigger.active_workflows) < 1

    @pytest.mark.asyncio
    async def test_validate_webhook_signature(self):
        """Test webhook signature validation."""
        trigger = WorkflowTrigger()

        # Without configured secret, should return True (placeholder implementation)
        event_data = {'test': 'data'}
        signature = 'test-signature'

        is_valid = trigger._validate_webhook_signature(event_data, signature)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_process_workflow_event_error_handling(self):
        """Test error handling in workflow event processing."""
        trigger = WorkflowTrigger()

        # Invalid event data
        invalid_event = {'invalid': 'data'}

        result = await trigger.process_workflow_event(invalid_event)

        assert 'error' in result
        assert 'status' not in result or result.get('status') != 'accepted'


@pytest.mark.asyncio
class TestWorkflowTriggerIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_process_workflow_event_function(self, sample_pull_request_event):
        """Test the convenience function for workflow event processing."""
        with patch('services.analysis_service.modules.workflow_trigger.workflow_trigger') as mock_trigger:
            mock_trigger.process_workflow_event.return_value = {
                'workflow_id': 'wf_1234567890_1234',
                'status': 'accepted',
                'priority': 'high',
                'analysis_types': ['quality_check', 'consistency_check'],
                'estimated_processing_time': 15.5,
                'processing_time': 2.1
            }

            result = await process_workflow_event(sample_pull_request_event)

            assert result['workflow_id'] == 'wf_1234567890_1234'
            assert result['status'] == 'accepted'
            assert result['priority'] == 'high'
            mock_trigger.process_workflow_event.assert_called_once()


class TestWorkflowHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_workflow_event_success(self, mock_service_client, sample_pull_request_event):
        """Test successful workflow event handling."""
        from services.analysis_service.modules.models import WorkflowEventRequest

        with patch('services.analysis_service.modules.workflow_trigger.process_workflow_event') as mock_process:

            mock_process.return_value = {
                'workflow_id': 'wf_1234567890_1234',
                'status': 'accepted',
                'priority': 'high',
                'analysis_types': ['quality_check', 'consistency_check'],
                'estimated_processing_time': 15.5,
                'processing_time': 2.1
            }

            request = WorkflowEventRequest(
                event_type='pull_request',
                action='opened',
                repository='my-org/docs-repo',
                branch='feature/add-api-docs',
                files_changed=['docs/api.md'],
                lines_changed=50
            )

            # Import the handler method
            from services.analysis_service.modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_workflow_event(request)

            assert result.workflow_id == 'wf_1234567890_1234'
            assert result.status == 'accepted'
            assert result.priority == 'high'
            assert len(result.analysis_types) > 0

    @pytest.mark.asyncio
    async def test_handle_workflow_status_success(self, mock_service_client):
        """Test successful workflow status handling."""
        from services.analysis_service.modules.models import WorkflowStatusRequest

        with patch('services.analysis_service.modules.workflow_trigger.workflow_trigger') as mock_trigger:

            mock_trigger.get_workflow_status.return_value = {
                'workflow_id': 'wf_1234567890_1234',
                'status': 'completed',
                'event_context': {'priority': 'high'},
                'created_at': 1234567890.0,
                'processed_at': 1234567891.0,
                'completed_at': 1234567892.0,
                'analysis_plan': {'priority': 'high'},
                'results': {'summary': {'total_analyses': 2}},
                'error': None
            }

            request = WorkflowStatusRequest(workflow_id='wf_1234567890_1234')

            # Import the handler method
            from services.analysis_service.modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_workflow_status(request)

            assert result.workflow_id == 'wf_1234567890_1234'
            assert result.status == 'completed'
            assert result.priority == 'high'
            assert result.created_at == 1234567890.0

    @pytest.mark.asyncio
    async def test_handle_workflow_queue_status_success(self, mock_service_client):
        """Test successful workflow queue status handling."""
        with patch('services.analysis_service.modules.workflow_trigger.workflow_trigger') as mock_trigger:

            mock_trigger.get_queue_status.return_value = {
                'critical': 0,
                'high': 2,
                'medium': 1,
                'low': 0
            }

            mock_trigger.get_event_history.return_value = [
                {
                    'workflow_id': 'wf_1234567890_1234',
                    'event_type': 'pull_request',
                    'event_action': 'opened',
                    'priority': 'high',
                    'timestamp': 1234567890.0
                }
            ]

            mock_trigger.active_workflows = {'wf_1234567890_1234': {}}

            # Import the handler method
            from services.analysis_service.modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_workflow_queue_status()

            assert result.queues['high'] == 2
            assert result.total_queued == 3
            assert result.active_workflows == 1
            assert len(result.recent_events) == 1

    @pytest.mark.asyncio
    async def test_handle_webhook_config_success(self, mock_service_client):
        """Test successful webhook configuration handling."""
        from services.analysis_service.modules.models import WebhookConfigRequest

        with patch('services.analysis_service.modules.workflow_trigger.workflow_trigger') as mock_trigger:

            mock_trigger.configure_webhook_secret.return_value = None

            request = WebhookConfigRequest(
                secret='my-webhook-secret-12345',
                enabled_events=['pull_request', 'push']
            )

            # Import the handler method
            from services.analysis_service.modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_webhook_config(request)

            assert result.configured is True
            assert len(result.enabled_events) == 2
            assert 'pull_request' in result.enabled_events
            assert 'push' in result.enabled_events


if __name__ == "__main__":
    pytest.main([__file__])
