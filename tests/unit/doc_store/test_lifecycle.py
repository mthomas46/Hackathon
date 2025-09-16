"""Tests for Doc Store lifecycle management functionality.

Tests policy-based retention, automated lifecycle transitions,
compliance monitoring, and audit trails.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import pytest

# Import modules normally now that directory uses underscores
from services.doc_store.modules.lifecycle_management import (
    LifecycleManager, LifecyclePolicy, DocumentLifecycle, lifecycle_manager
)


class TestLifecyclePolicy:
    """Test LifecyclePolicy class functionality."""

    def test_policy_initialization(self):
        """Test policy initialization."""
        conditions = {"content_types": ["api"], "max_age_days": 365}
        actions = {"retention_days": 730}

        policy = LifecyclePolicy(
            id="test-policy",
            name="Test Policy",
            description="Test lifecycle policy",
            conditions=conditions,
            actions=actions,
            priority=5,
            enabled=True
        )

        assert policy.id == "test-policy"
        assert policy.name == "Test Policy"
        assert policy.conditions == conditions
        assert policy.actions == actions
        assert policy.priority == 5
        assert policy.enabled is True

    def test_policy_matches_document(self):
        """Test policy matching against documents."""
        policy = LifecyclePolicy(
            id="api-policy",
            name="API Policy",
            description="Policy for API documentation",
            conditions={"content_types": ["api"], "max_age_days": 365},
            actions={"retention_days": 730}
        )

        # Matching document (older than 365 days)
        document = {
            "metadata": {"type": "api"},
            "created_at": (datetime.now() - timedelta(days=400)).isoformat()
        }
        lifecycle = {"analysis_count": 5, "tags": ["api", "rest"]}

        assert policy.matches_document(document, lifecycle)

        # Non-matching document (wrong type)
        document_wrong_type = {
            "metadata": {"type": "documentation"},
            "created_at": (datetime.now() - timedelta(days=400)).isoformat()
        }
        assert not policy.matches_document(document_wrong_type, lifecycle)


class TestLifecycleManager:
    """Test LifecycleManager class functionality."""

    @pytest.fixture
    def manager(self):
        """Create a test lifecycle manager instance."""
        return LifecycleManager()

    @patch('services.doc_store.modules.lifecycle_management.execute_db_query')
    def test_create_policy(self, mock_execute, manager):
        """Test creating lifecycle policies."""
        mock_execute.return_value = []

        policy_id = manager.create_policy(
            name="Test Policy",
            description="A test policy",
            conditions={"content_types": ["api"]},
            actions={"retention_days": 365},
            priority=10
        )

        assert "policy_test_policy" in policy_id
        assert policy_id in manager.policies

        policy = manager.policies[policy_id]
        assert policy.name == "Test Policy"
        assert policy.conditions == {"content_types": ["api"]}
        assert policy.actions == {"retention_days": 365}
        assert policy.priority == 10

    @patch('services.doc_store.modules.lifecycle_management.execute_db_query')
    def test_get_document_lifecycle(self, mock_execute):
        """Test retrieving document lifecycle information."""
        # Mock both the policy loading (for __init__) and the lifecycle query
        mock_execute.side_effect = [
            [],  # Empty policies list for _load_policies
            {    # Document lifecycle row for get_document_lifecycle
                'id': 'lifecycle_doc1',
                'document_id': 'doc1',
                'current_phase': 'active',
                'retention_period_days': 365,
                'archival_date': '2025-01-01T00:00:00Z',
                'deletion_date': '2026-01-01T00:00:00Z',
                'last_reviewed': None,
                'compliance_status': 'compliant',
                'applied_policies': '["policy1"]',
                'metadata': '{"custom": "data"}',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        ]

        # Create manager after setting up mock
        manager = LifecycleManager()
        lifecycle = manager.get_document_lifecycle("doc1")

        assert lifecycle is not None
        assert lifecycle.document_id == "doc1"
        assert lifecycle.current_phase == "active"
        assert lifecycle.retention_period_days == 365
        assert lifecycle.applied_policies == ["policy1"]

    @patch('services.doc_store.modules.lifecycle_management.execute_db_query')
    def test_initialize_document_lifecycle(self, mock_execute, manager):
        """Test initializing lifecycle for documents."""
        # Mock policy evaluation
        with patch.object(manager, '_evaluate_policies', return_value=[
            LifecyclePolicy(
                id="policy1",
                name="Test Policy",
                description="Test policy for initialization",
                conditions={},
                actions={"retention_days": 365}
            )
        ]):
            # Mock database operations
            mock_execute.return_value = []

            lifecycle_id = manager.initialize_document_lifecycle("doc1")

            assert "lifecycle_doc1" == lifecycle_id
            # Verify database calls were made
            assert mock_execute.call_count > 0

    @patch('services.doc_store.modules.lifecycle_management.execute_db_query')
    def test_evaluate_policies(self, mock_execute, manager):
        """Test policy evaluation for documents."""
        # Mock document data
        mock_doc = {
            'id': 'doc1',
            'metadata': '{"type": "api"}',
            'created_at': (datetime.now() - timedelta(days=100)).isoformat()
        }
        mock_analysis = [5]  # Analysis count
        mock_tags = [{'tag': 'api'}, {'tag': 'rest'}]

        mock_execute.side_effect = [mock_doc, mock_analysis, mock_tags]

        # Create a test policy
        policy = LifecyclePolicy(
            id="test-policy",
            name="Test Policy",
            description="Test policy for evaluation",
            conditions={"content_types": ["api"]},
            actions={"retention_days": 365}
        )
        manager.policies = {"test-policy": policy}

        policies = manager._evaluate_policies("doc1")

        assert len(policies) == 1
        assert policies[0].id == "test-policy"

    def test_calculate_retention_period(self, manager):
        """Test retention period calculation."""
        policies = [
            LifecyclePolicy(id="p1", name="Policy 1", description="Low retention policy", conditions={}, actions={"retention_days": 365}),
            LifecyclePolicy(id="p2", name="Policy 2", description="High retention policy", conditions={}, actions={"retention_days": 730})
        ]

        retention = manager._calculate_retention_period(policies)

        # Should return the maximum retention period
        assert retention == 730

    @patch('services.doc_store.modules.lifecycle_management.execute_db_query')
    def test_process_lifecycle_transitions(self, mock_execute, manager):
        """Test automated lifecycle transitions."""
        # Mock documents ready for archival
        archival_docs = [
            {'document_id': 'doc1', 'archival_date': '2020-01-01T00:00:00Z', 'metadata': '{}'},
            {'document_id': 'doc2', 'archival_date': '2020-01-01T00:00:00Z', 'metadata': '{}'}
        ]

        # Mock documents ready for deletion
        deletion_docs = [
            {'document_id': 'doc3', 'deletion_date': '2020-01-01T00:00:00Z', 'metadata': '{}'}
        ]

        # Mock database calls - return different results based on the query
        def mock_db_call(*args, **kwargs):
            query = args[0] if args else ""
            if "archival_date" in query:
                return archival_docs
            elif "deletion_date" in query:
                return deletion_docs
            else:
                return None  # For UPDATE/DELETE/INSERT queries

        mock_execute.side_effect = mock_db_call

        result = manager.process_lifecycle_transitions()

        assert result["archived"] == 2
        assert result["deleted"] == 1

    def test_transition_document_phase(self, manager):
        """Test document phase transitions."""
        with patch('services.doc_store.modules.lifecycle_management.execute_db_query') as mock_execute:
            mock_execute.return_value = []

            manager._transition_document_phase("doc1", "active", "archived", "Policy triggered")

            # Verify database updates were made
            assert mock_execute.call_count >= 2  # Update lifecycle + log event

    @patch('services.doc_store.modules.lifecycle_management.execute_db_query')
    def test_get_lifecycle_report(self, mock_execute, manager):
        """Test lifecycle report generation."""
        # Mock phase distribution
        phase_data = [
            {'current_phase': 'active', 'count': 100},
            {'current_phase': 'archived', 'count': 50},
            {'current_phase': 'deleted', 'count': 25}
        ]

        # Mock upcoming transitions
        upcoming_archival = [10]
        upcoming_deletion = [5]

        # Mock recent events
        recent_events = [
            {'document_id': 'doc1', 'event_type': 'archived', 'old_phase': 'active', 'new_phase': 'archived', 'created_at': '2024-01-01T00:00:00Z'}
        ]

        # Mock policy effectiveness
        policy_stats = [
            {'name': 'API Policy', 'events_count': 15}
        ]

        mock_execute.side_effect = [
            phase_data, upcoming_archival, upcoming_deletion, recent_events, policy_stats
        ]

        report = manager.get_lifecycle_report(days_back=30)

        assert report["phase_distribution"][0]["phase"] == "active"
        assert report["phase_distribution"][0]["count"] == 100
        assert report["upcoming_transitions"]["archivals_next_30_days"] == 10
        assert report["upcoming_transitions"]["deletions_next_30_days"] == 5
        assert len(report["recent_events"]) == 1
        assert len(report["policy_effectiveness"]) == 1


class TestLifecycleManagementIntegration:
    """Test lifecycle management integration with doc store operations."""

    @pytest.mark.asyncio
    async def test_lifecycle_api_endpoints(self):
        """Test lifecycle management API endpoints."""
        from services.doc_store.modules.lifecycle_handlers import LifecycleHandlers
        from services.doc_store.core.models import LifecyclePolicyRequest

        # Test policy creation
        policy_request = LifecyclePolicyRequest(
            name="Test Policy",
            description="Integration test policy",
            conditions={"content_types": ["api"]},
            actions={"retention_days": 365},
            priority=5
        )

        with patch('services.doc_store.modules.lifecycle_handlers.lifecycle_manager') as mock_manager:
            mock_manager.create_policy.return_value = "policy_test_policy"

            handler = LifecycleHandlers()
            result = await handler.handle_create_policy(policy_request)

            assert result["data"]["policy_id"] == "policy_test_policy"

    @pytest.mark.asyncio
    async def test_lifecycle_initialization_api(self):
        """Test document lifecycle initialization API."""
        from services.doc_store.modules.lifecycle_handlers import LifecycleHandlers

        with patch('services.doc_store.modules.lifecycle_handlers.lifecycle_manager') as mock_manager:
            mock_manager.initialize_document_lifecycle.return_value = "lifecycle_doc1"

            handler = LifecycleHandlers()
            result = await handler.handle_initialize_document_lifecycle("doc1")

            assert result["data"]["lifecycle_id"] == "lifecycle_doc1"

    @pytest.mark.asyncio
    async def test_lifecycle_transitions_api(self):
        """Test lifecycle transitions API."""
        from services.doc_store.modules.lifecycle_handlers import LifecycleHandlers

        with patch('services.doc_store.modules.lifecycle_handlers.lifecycle_manager') as mock_manager:
            mock_manager.process_lifecycle_transitions.return_value = {
                "archived": 5,
                "deleted": 2
            }

            handler = LifecycleHandlers()
            result = await handler.handle_process_lifecycle_transitions()

            assert result["data"]["archived"] == 5
            assert result["data"]["deleted"] == 2

    @pytest.mark.asyncio
    async def test_lifecycle_report_api(self):
        """Test lifecycle report API."""
        from services.doc_store.modules.lifecycle_handlers import LifecycleHandlers

        mock_report = {
            "phase_distribution": [{"phase": "active", "count": 100}],
            "upcoming_transitions": {"archivals_next_30_days": 10},
            "recent_events": [],
            "policy_effectiveness": []
        }

        with patch('services.doc_store.modules.lifecycle_handlers.lifecycle_manager') as mock_manager:
            mock_manager.get_lifecycle_report.return_value = mock_report

            handler = LifecycleHandlers()
            result = await handler.handle_get_lifecycle_report(days_back=30)

            assert result["data"]["phase_distribution"][0]["count"] == 100

    @pytest.mark.asyncio
    async def test_document_phase_transition_api(self):
        """Test document phase transition API."""
        from services.doc_store.modules.lifecycle_handlers import LifecycleHandlers
        from services.doc_store.core.models import LifecycleTransitionRequest

        transition_request = LifecycleTransitionRequest(
            new_phase="archived",
            reason="Manual archival for compliance"
        )

        with patch('services.doc_store.modules.lifecycle_handlers.lifecycle_manager') as mock_manager, \
             patch('services.doc_store.modules.shared_utils.execute_db_query') as mock_execute:
            mock_lifecycle = Mock()
            mock_lifecycle.current_phase = "active"
            mock_manager.get_document_lifecycle.return_value = mock_lifecycle
            mock_manager._transition_document_phase.return_value = None
            mock_execute.return_value = None

            handler = LifecycleHandlers()
            result = await handler.handle_transition_document_phase("doc1", transition_request)

            assert result["data"]["old_phase"] == "active"
            assert result["data"]["new_phase"] == "archived"
            assert result["data"]["reason"] == "Manual archival for compliance"


class TestLifecycleCompliance:
    """Test lifecycle compliance and audit functionality."""

    def test_compliance_status_tracking(self):
        """Test compliance status tracking."""
        lifecycle = DocumentLifecycle(
            id="test-lifecycle",
            document_id="doc1",
            current_phase="active",
            compliance_status="compliant",
            applied_policies=["policy1", "policy2"]
        )

        assert lifecycle.compliance_status == "compliant"
        assert len(lifecycle.applied_policies) == 2

    def test_policy_priority_handling(self):
        """Test policy priority handling in evaluation."""
        policies = [
            LifecyclePolicy(id="low", name="Low Priority", description="Low priority policy", conditions={}, actions={"retention_days": 180}, priority=1),
            LifecyclePolicy(id="high", name="High Priority", description="High priority policy", conditions={}, actions={"retention_days": 365}, priority=10),
            LifecyclePolicy(id="medium", name="Medium Priority", description="Medium priority policy", conditions={}, actions={"retention_days": 270}, priority=5)
        ]

        # Sort by priority (highest first)
        policies.sort(key=lambda p: p.priority, reverse=True)

        assert policies[0].id == "high"
        assert policies[1].id == "medium"
        assert policies[2].id == "low"

    def test_lifecycle_event_logging(self):
        """Test lifecycle event logging."""
        manager = LifecycleManager()

        with patch('services.doc_store.modules.lifecycle_management.execute_db_query') as mock_execute:
            mock_execute.return_value = []

            manager._log_lifecycle_event(
                document_id="doc1",
                event_type="phase_transition",
                old_phase="active",
                new_phase="archived",
                policy_id="policy1",
                details={"reason": "Retention policy"}
            )

            # Verify database call was made for event logging
            assert mock_execute.call_count == 1
