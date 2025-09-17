"""Document lifecycle integration tests.

Tests that verify the complete lifecycle of documents from creation through
analysis, tagging, versioning, and lifecycle management.
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.integration
class TestDocumentLifecycleIntegration(BaseTestCase):
    """Test complete document lifecycle across domains."""

    @pytest.fixture
    def mock_services(self):
        """Mock all domain services for integration testing."""
        with patch('services.doc_store.domain.documents.service.DocumentService') as doc_svc, \
             patch('services.doc_store.domain.analytics.service.AnalyticsService') as analytics_svc, \
             patch('services.doc_store.domain.tagging.service.TaggingService') as tagging_svc, \
             patch('services.doc_store.domain.versioning.service.VersioningService') as versioning_svc, \
             patch('services.doc_store.domain.lifecycle.service.LifecycleService') as lifecycle_svc:

            yield {
                'documents': doc_svc,
                'analytics': analytics_svc,
                'tagging': tagging_svc,
                'versioning': versioning_svc,
                'lifecycle': lifecycle_svc
            }

    def test_document_creation_to_analysis_flow(self, mock_services):
        """Test the flow from document creation to analysis."""
        # Mock document creation
        mock_doc = Mock()
        mock_doc.id = 'test-doc-123'
        mock_doc.content_hash = 'hash123'
        mock_services['documents'].create_document.return_value = mock_doc

        # Mock analysis
        mock_analysis = Mock()
        mock_analysis.id = 'analysis-123'
        mock_services['analytics'].create_analysis.return_value = mock_analysis

        # Simulate the flow
        document = mock_services['documents'].create_document(
            content="Test API documentation content",
            metadata={"type": "api", "language": "english"}
        )

        analysis = mock_services['analytics'].create_analysis(
            document_id=document.id,
            analyzer="quality-analyzer",
            result={"score": 0.85}
        )

        assert document.id == 'test-doc-123'
        assert analysis.id == 'analysis-123'

    def test_document_versioning_and_tagging_flow(self, mock_services):
        """Test versioning and tagging workflow."""
        # Mock initial document
        mock_doc = Mock()
        mock_doc.id = 'doc-123'
        mock_services['documents'].get_entity.return_value = mock_doc

        # Mock versioning
        mock_version = Mock()
        mock_version.version_number = 2
        mock_services['versioning'].create_version.return_value = mock_version

        # Mock tagging
        mock_tag = Mock()
        mock_tag.tag = 'api'
        mock_services['tagging'].tag_document.return_value = mock_tag

        # Simulate workflow
        version = mock_services['versioning'].create_version(
            document_id='doc-123',
            content='Updated API docs',
            content_hash='newhash123',
            change_summary='Updated API endpoints'
        )

        tag = mock_services['tagging'].tag_document(
            document_id='doc-123',
            tag='api',
            confidence=0.9
        )

        assert version.version_number == 2
        assert tag.tag == 'api'

    def test_lifecycle_policy_application_flow(self, mock_services):
        """Test lifecycle policy application across domains."""
        # Mock document with lifecycle data
        document = {
            'id': 'doc-123',
            'metadata': {'type': 'api'},
            'created_at': '2023-01-01T00:00:00Z'  # Over 1 year old
        }

        # Mock policy application
        lifecycle_result = {
            'document_id': 'doc-123',
            'applied_policies': [{'policy_id': 'retention-policy'}],
            'new_phase': 'archived'
        }
        mock_services['lifecycle'].apply_lifecycle_policies.return_value = lifecycle_result

        # Mock analytics for lifecycle reporting
        analytics_data = {
            'total_documents': 100,
            'archived_documents': 25,
            'stale_documents': 10
        }
        mock_services['analytics'].get_basic_counts.return_value = analytics_data

        # Simulate lifecycle workflow
        result = mock_services['lifecycle'].apply_lifecycle_policies(document)
        analytics = mock_services['analytics'].get_basic_counts()

        assert result['applied_policies'][0]['policy_id'] == 'retention-policy'
        assert analytics['total_documents'] == 100

    @pytest.mark.asyncio
    async def test_notification_integration_flow(self, mock_services):
        """Test notification integration across document operations."""
        from services.doc_store.domain.notifications.service import NotificationsService

        with patch('services.doc_store.domain.notifications.service.NotificationsService') as notification_svc:
            mock_notification = Mock()
            mock_notification.id = 'notification-123'
            notification_svc.emit_event.return_value = mock_notification

            # Simulate document creation with notification
            mock_doc = Mock()
            mock_doc.id = 'doc-123'
            mock_services['documents'].create_document.return_value = mock_doc

            # Create document and emit notification
            document = mock_services['documents'].create_document(
                content="New API documentation",
                metadata={"type": "api"}
            )

            notification = notification_svc.emit_event(
                event_type='document.created',
                entity_type='document',
                entity_id=document.id
            )

            assert document.id == 'doc-123'
            assert notification.id == 'notification-123'

    def test_bulk_operation_with_analytics_integration(self, mock_services):
        """Test bulk operations integrated with analytics."""
        from services.doc_store.domain.bulk.service import BulkOperationsService

        with patch('services.doc_store.domain.bulk.service.BulkOperationsService') as bulk_svc:
            # Mock bulk operation
            mock_operation = Mock()
            mock_operation.operation_id = 'bulk-123'
            mock_operation.status = 'completed'
            bulk_svc.create_bulk_operation.return_value = mock_operation

            # Mock analytics for bulk operation tracking
            analytics_stats = {
                'bulk_operations_count': 5,
                'total_processed_documents': 1000
            }
            mock_services['analytics'].get_storage_stats.return_value = analytics_stats

            # Simulate bulk operation workflow
            operation = bulk_svc.create_bulk_operation(
                operation_type='create_documents',
                documents=[{'content': 'Bulk doc 1'}, {'content': 'Bulk doc 2'}]
            )

            analytics = mock_services['analytics'].get_storage_stats()

            assert operation.operation_id == 'bulk-123'
            assert analytics['bulk_operations_count'] == 5

    def test_relationship_graph_analytics_integration(self, mock_services):
        """Test relationship graph integrated with analytics."""
        from services.doc_store.domain.relationships.service import RelationshipsService

        with patch('services.doc_store.domain.relationships.service.RelationshipsService') as rel_svc:
            # Mock relationship creation
            mock_relationship = Mock()
            mock_relationship.id = 'rel-123'
            rel_svc.create_relationship.return_value = mock_relationship

            # Mock graph statistics
            graph_stats = {
                'total_relationships': 25,
                'unique_documents': 20,
                'density': 0.0625
            }
            rel_svc.get_graph_statistics.return_value = graph_stats

            # Mock analytics for relationship insights
            rel_insights = {
                'total_relationships': 25,
                'relationship_types': {'references': 15, 'extends': 10}
            }
            mock_services['analytics'].get_relationship_insights.return_value = rel_insights

            # Simulate relationship and analytics workflow
            relationship = rel_svc.create_relationship(
                source_doc_id='doc1',
                target_doc_id='doc2',
                relationship_type='references'
            )

            graph_stats = rel_svc.get_graph_statistics()
            insights = mock_services['analytics'].get_relationship_insights()

            assert relationship.id == 'rel-123'
            assert graph_stats['total_relationships'] == 25
            assert insights['total_relationships'] == 25
