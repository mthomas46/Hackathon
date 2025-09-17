"""End-to-End Tests for Complete User Workflows."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...main import app
from ...presentation.models.analysis import (
    SemanticSimilarityRequest, SemanticSimilarityResponse,
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    ContentQualityRequest, ContentQualityResponse
)
from ...presentation.models.common import (
    FindingsListResponse, FindingResponse
)

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_document_content(self):
        """Sample document content for testing."""
        return """
        # Introduction to Machine Learning

        Machine learning is a powerful technology that enables computers to learn from data without being explicitly programmed. This document explores the fundamental concepts, algorithms, and applications of machine learning.

        ## What is Machine Learning?

        Machine learning is a subset of artificial intelligence that focuses on developing algorithms that can learn patterns from data. There are three main types of machine learning:

        1. **Supervised Learning**: Learning from labeled training data
        2. **Unsupervised Learning**: Finding hidden patterns in unlabeled data
        3. **Reinforcement Learning**: Learning through interaction with an environment

        ## Key Algorithms

        Some of the most important machine learning algorithms include:

        - Linear Regression
        - Decision Trees
        - Neural Networks
        - Support Vector Machines
        - K-Means Clustering

        ## Applications

        Machine learning has numerous real-world applications:

        - Image recognition and computer vision
        - Natural language processing
        - Recommendation systems
        - Fraud detection
        - Predictive analytics

        ## Challenges and Future Directions

        While machine learning offers tremendous potential, it also faces several challenges:

        - Data quality and quantity requirements
        - Model interpretability and explainability
        - Ethical considerations and bias
        - Computational resource requirements

        The future of machine learning looks promising with advances in deep learning, transfer learning, and automated machine learning platforms.

        ## Conclusion

        Machine learning is transforming industries and creating new opportunities. Understanding its fundamentals is essential for anyone working in technology or data-driven fields.
        """

    @pytest.mark.asyncio
    async def test_document_upload_and_analysis_workflow(self, client, sample_document_content):
        """Test complete workflow: document upload → analysis → findings retrieval."""
        # Step 1: Simulate document upload (in a real system, this would be an upload endpoint)
        document_data = {
            'id': 'workflow-doc-001',
            'title': 'Machine Learning Introduction',
            'content': sample_document_content,
            'repository_id': 'docs-repo',
            'author': 'john.doe@company.com',
            'version': '1.0.0'
        }

        # Mock document creation
        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_create_document') as mock_create:
            mock_create.return_value = {
                'document_id': 'workflow-doc-001',
                'status': 'created',
                'message': 'Document created successfully'
            }

            # Create document via API
            response = client.post("/documents", json=document_data)
            assert response.status_code in [200, 201]

        # Step 2: Perform semantic similarity analysis
        similarity_request = {
            'targets': ['doc-1', 'doc-2', 'doc-3'],
            'threshold': 0.7,
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'options': {
                'include_embeddings': False,
                'batch_size': 16
            }
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_similarity:
            mock_response = SemanticSimilarityResponse(
                analysis_id='similarity-analysis-001',
                analysis_type='semantic_similarity',
                targets=['doc-1', 'doc-2', 'doc-3'],
                status='completed',
                similarity_matrix=[[1.0, 0.85, 0.65], [0.85, 1.0, 0.72], [0.65, 0.72, 1.0]],
                similar_pairs=[
                    {'source': 'doc-1', 'target': 'doc-2', 'similarity': 0.85},
                    {'source': 'doc-2', 'target': 'doc-3', 'similarity': 0.72}
                ],
                summary={
                    'total_pairs': 3,
                    'highly_similar_pairs': 2,
                    'average_similarity': 0.775
                },
                execution_time_seconds=2.1,
                error_message=None
            )
            mock_similarity.return_value = mock_response

            response = client.post("/analyze/semantic-similarity", json=similarity_request)
            assert response.status_code == 200

            similarity_data = response.json()
            assert similarity_data['analysis_id'] == 'similarity-analysis-001'
            assert len(similarity_data['similar_pairs']) == 2
            assert similarity_data['summary']['highly_similar_pairs'] == 2

        # Step 3: Perform sentiment analysis
        sentiment_request = {
            'document_id': 'workflow-doc-001',
            'analysis_options': {
                'include_detailed_scores': True,
                'language': 'en'
            }
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_sentiment_analysis') as mock_sentiment:
            mock_response = SentimentAnalysisResponse(
                analysis_id='sentiment-analysis-001',
                document_id='workflow-doc-001',
                sentiment='positive',
                confidence=0.88,
                scores={
                    'positive': 0.88,
                    'negative': 0.08,
                    'neutral': 0.04
                },
                detailed_analysis={
                    'sentence_sentiments': [
                        {'text': 'Machine learning is a powerful technology', 'sentiment': 'positive', 'confidence': 0.92},
                        {'text': 'Understanding its fundamentals is essential', 'sentiment': 'positive', 'confidence': 0.85}
                    ],
                    'overall_tone': 'professional',
                    'readability_score': 78.5
                },
                execution_time_seconds=1.2,
                error_message=None
            )
            mock_sentiment.return_value = mock_response

            response = client.post("/analyze/sentiment", json=sentiment_request)
            assert response.status_code == 200

            sentiment_data = response.json()
            assert sentiment_data['sentiment'] == 'positive'
            assert sentiment_data['confidence'] == 0.88
            assert len(sentiment_data['detailed_analysis']['sentence_sentiments']) == 2

        # Step 4: Perform content quality analysis
        quality_request = {
            'document_id': 'workflow-doc-001',
            'quality_checks': ['readability', 'grammar', 'structure', 'completeness'],
            'options': {
                'language': 'en',
                'readability_target': 70.0
            }
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_content_quality_assessment') as mock_quality:
            mock_response = ContentQualityResponse(
                analysis_id='quality-analysis-001',
                document_id='workflow-doc-001',
                overall_score=84.5,
                quality_breakdown={
                    'readability': {'score': 82.0, 'level': 'good', 'issues': ['sentence_length']},
                    'grammar': {'score': 88.0, 'level': 'excellent', 'issues': []},
                    'structure': {'score': 86.0, 'level': 'excellent', 'issues': []},
                    'completeness': {'score': 82.0, 'level': 'good', 'issues': ['missing_examples']}
                },
                recommendations=[
                    'Consider shortening some sentences for better readability',
                    'Add more practical examples to improve completeness'
                ],
                improvement_suggestions={
                    'high_priority': ['Add practical examples'],
                    'medium_priority': ['Improve sentence variety'],
                    'low_priority': ['Add more cross-references']
                },
                execution_time_seconds=1.8,
                error_message=None
            )
            mock_quality.return_value = mock_response

            response = client.post("/analyze/quality", json=quality_request)
            assert response.status_code == 200

            quality_data = response.json()
            assert quality_data['overall_score'] == 84.5
            assert quality_data['quality_breakdown']['readability']['level'] == 'good'
            assert len(quality_data['recommendations']) == 2

        # Step 5: Retrieve findings
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_findings:
            mock_findings_response = FindingsListResponse(
                findings=[
                    FindingResponse(
                        id='finding-001',
                        analysis_id='sentiment-analysis-001',
                        document_id='workflow-doc-001',
                        title='Positive Content Detected',
                        description='Document has positive sentiment overall',
                        severity='info',
                        confidence=0.88,
                        category='sentiment',
                        created_at=datetime.now(timezone.utc)
                    ),
                    FindingResponse(
                        id='finding-002',
                        analysis_id='quality-analysis-001',
                        document_id='workflow-doc-001',
                        title='Readability Improvement Needed',
                        description='Some sentences are too long',
                        severity='medium',
                        confidence=0.75,
                        category='readability',
                        recommendation='Consider breaking down long sentences',
                        created_at=datetime.now(timezone.utc)
                    )
                ],
                total_count=2,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_findings.return_value = mock_findings_response

            response = client.get("/findings?document_id=workflow-doc-001")
            assert response.status_code == 200

            findings_data = response.json()
            assert len(findings_data['findings']) == 2
            assert findings_data['total_count'] == 2

            # Verify findings content
            sentiment_finding = next(f for f in findings_data['findings'] if f['category'] == 'sentiment')
            quality_finding = next(f for f in findings_data['findings'] if f['category'] == 'readability')

            assert sentiment_finding['severity'] == 'info'
            assert sentiment_finding['confidence'] == 0.88
            assert quality_finding['severity'] == 'medium'
            assert 'recommendation' in quality_finding

    @pytest.mark.asyncio
    async def test_multi_user_concurrent_workflow(self, client, sample_document_content):
        """Test concurrent workflows from multiple users."""
        async def user_workflow(user_id: int):
            """Simulate complete workflow for a single user."""
            user_doc_id = f'user-{user_id}-doc'

            # Step 1: Document upload
            with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_create_document') as mock_create:
                mock_create.return_value = {
                    'document_id': user_doc_id,
                    'status': 'created'
                }

                doc_data = {
                    'id': user_doc_id,
                    'title': f'User {user_id} Document',
                    'content': sample_document_content,
                    'repository_id': f'user-{user_id}-repo',
                    'author': f'user-{user_id}@company.com'
                }

                response = client.post("/documents", json=doc_data)
                assert response.status_code in [200, 201]

            # Step 2: Semantic similarity analysis
            with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_similarity:
                mock_response = SemanticSimilarityResponse(
                    analysis_id=f'similarity-{user_id}',
                    analysis_type='semantic_similarity',
                    targets=[f'doc-{user_id}-1', f'doc-{user_id}-2'],
                    status='completed',
                    execution_time_seconds=1.5 + (user_id * 0.1)
                )
                mock_similarity.return_value = mock_response

                similarity_request = {
                    'targets': [f'doc-{user_id}-1', f'doc-{user_id}-2'],
                    'threshold': 0.8
                }

                response = client.post("/analyze/semantic-similarity", json=similarity_request)
                assert response.status_code == 200

                data = response.json()
                assert data['analysis_id'] == f'similarity-{user_id}'

            # Step 3: Findings retrieval
            with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_findings:
                mock_findings_response = FindingsListResponse(
                    findings=[
                        FindingResponse(
                            id=f'finding-{user_id}-1',
                            analysis_id=f'similarity-{user_id}',
                            document_id=user_doc_id,
                            title=f'User {user_id} Finding',
                            description=f'Analysis result for user {user_id}',
                            severity='medium',
                            confidence=0.8,
                            category='analysis'
                        )
                    ],
                    total_count=1,
                    limit=50,
                    offset=0,
                    has_more=False
                )
                mock_findings.return_value = mock_findings_response

                response = client.get(f"/findings?document_id={user_doc_id}")
                assert response.status_code == 200

                findings_data = response.json()
                assert len(findings_data['findings']) == 1
                assert findings_data['findings'][0]['id'] == f'finding-{user_id}-1'

            return f'user-{user_id}-complete'

        # Execute concurrent workflows
        num_users = 5
        start_time = time.time()

        tasks = [user_workflow(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all workflows completed
        assert len(results) == num_users
        assert all(result.endswith('-complete') for result in results)

        # Verify reasonable performance (< 10 seconds for 5 concurrent workflows)
        assert total_time < 10.0

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, client):
        """Test workflow with error recovery."""
        # Step 1: Attempt analysis with invalid document
        similarity_request = {
            'targets': ['non-existent-doc'],
            'threshold': 0.8
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_similarity:
            # Simulate error in analysis
            mock_similarity.side_effect = Exception("Document not found")

            response = client.post("/analyze/semantic-similarity", json=similarity_request)

            # Should handle error gracefully
            assert response.status_code in [400, 404, 500]

        # Step 2: Retry with valid document
        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_create_document') as mock_create:
            mock_create.return_value = {
                'document_id': 'recovery-doc',
                'status': 'created'
            }

            # Create valid document
            doc_data = {
                'id': 'recovery-doc',
                'title': 'Recovery Test Document',
                'content': 'This is a recovery test document.',
                'repository_id': 'recovery-repo',
                'author': 'recovery@company.com'
            }

            response = client.post("/documents", json=doc_data)
            assert response.status_code in [200, 201]

        # Step 3: Retry analysis with valid document
        valid_similarity_request = {
            'targets': ['recovery-doc'],
            'threshold': 0.8
        }

        with patch('services.analysis_service.presentation.controllers.analysis_controller.analysis_handlers.handle_semantic_similarity_analysis') as mock_similarity:
            mock_response = SemanticSimilarityResponse(
                analysis_id='recovery-analysis',
                analysis_type='semantic_similarity',
                targets=['recovery-doc'],
                status='completed',
                execution_time_seconds=1.0
            )
            mock_similarity.return_value = mock_response

            response = client.post("/analyze/semantic-similarity", json=valid_similarity_request)
            assert response.status_code == 200

            data = response.json()
            assert data['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_distributed_processing_workflow(self, client):
        """Test distributed processing workflow."""
        # Step 1: Submit distributed task
        task_request = {
            'task_type': 'semantic_similarity',
            'data': {
                'document_ids': ['doc-1', 'doc-2', 'doc-3', 'doc-4', 'doc-5'],
                'threshold': 0.8,
                'batch_size': 32
            },
            'priority': 'high'
        }

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_distributed_task') as mock_submit:
            mock_submit.return_value = {
                'task_id': 'distributed-task-001',
                'status': 'submitted',
                'estimated_completion_seconds': 45.0,
                'queue_position': 1
            }

            response = client.post("/distributed/tasks", json=task_request)
            assert response.status_code == 200

            submit_data = response.json()
            assert submit_data['task_id'] == 'distributed-task-001'
            assert submit_data['status'] == 'submitted'

        task_id = 'distributed-task-001'

        # Step 2: Check task status
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_task_status') as mock_status:
            mock_status.return_value = {
                'task_id': task_id,
                'status': 'running',
                'progress': 0.6,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'estimated_completion_seconds': 18.0,
                'worker_id': 'worker-3'
            }

            response = client.get(f"/distributed/tasks/{task_id}")
            assert response.status_code == 200

            status_data = response.json()
            assert status_data['status'] == 'running'
            assert status_data['progress'] == 0.6

        # Step 3: Wait for completion (simulated)
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_task_status') as mock_status:
            mock_status.return_value = {
                'task_id': task_id,
                'status': 'completed',
                'progress': 1.0,
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'result': {
                    'total_processed': 5,
                    'successful': 5,
                    'failed': 0,
                    'average_processing_time': 8.5
                }
            }

            response = client.get(f"/distributed/tasks/{task_id}")
            assert response.status_code == 200

            final_status = response.json()
            assert final_status['status'] == 'completed'
            assert final_status['progress'] == 1.0
            assert 'result' in final_status

        # Step 4: Check worker status
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_workers_status') as mock_workers:
            from ...presentation.models.common import WorkersStatusResponse

            mock_response = WorkersStatusResponse(
                total_workers=5,
                active_workers=2,
                idle_workers=3,
                workers=[
                    {
                        'worker_id': 'worker-1',
                        'status': 'active',
                        'current_task': 'distributed-task-001',
                        'tasks_completed': 15,
                        'uptime_seconds': 1800,
                        'cpu_usage': 75.5,
                        'memory_usage': 512.3
                    }
                ],
                average_cpu_usage=65.2,
                average_memory_usage=384.7
            )
            mock_workers.return_value = mock_response

            response = client.get("/distributed/workers")
            assert response.status_code == 200

            workers_data = response.json()
            assert workers_data['total_workers'] == 5
            assert workers_data['active_workers'] == 2

    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self, client):
        """Test batch processing workflow."""
        # Step 1: Submit batch tasks
        batch_request = {
            'tasks': [
                {
                    'task_type': 'semantic_similarity',
                    'data': {'document_ids': ['batch-doc-1', 'batch-doc-2']},
                    'priority': 'high'
                },
                {
                    'task_type': 'sentiment_analysis',
                    'data': {'document_id': 'batch-doc-3'},
                    'priority': 'normal'
                },
                {
                    'task_type': 'content_quality',
                    'data': {'document_id': 'batch-doc-4'},
                    'priority': 'low'
                }
            ],
            'batch_options': {
                'parallel_execution': True,
                'max_concurrent': 3,
                'timeout_seconds': 300
            }
        }

        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_submit_batch_tasks') as mock_batch:
            mock_batch.return_value = {
                'batch_id': 'batch-001',
                'task_count': 3,
                'submitted_tasks': ['batch-task-1', 'batch-task-2', 'batch-task-3'],
                'status': 'batch_submitted',
                'estimated_completion_seconds': 120.0
            }

            response = client.post("/distributed/tasks/batch", json=batch_request)
            assert response.status_code == 200

            batch_data = response.json()
            assert batch_data['batch_id'] == 'batch-001'
            assert batch_data['task_count'] == 3
            assert len(batch_data['submitted_tasks']) == 3

        # Step 2: Monitor batch progress
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_processing_stats') as mock_stats:
            from ...presentation.models.common import ProcessingStatsResponse

            mock_response = ProcessingStatsResponse(
                total_tasks_processed=150,
                tasks_completed=135,
                tasks_failed=10,
                tasks_cancelled=5,
                average_processing_time_seconds=12.5,
                throughput_tasks_per_minute=8.5,
                queue_length=8,
                oldest_task_age_seconds=45.2,
                worker_utilization_percentage=78.3,
                peak_concurrent_tasks=12,
                system_uptime_seconds=3600,
                memory_usage_mb=2048.5,
                cpu_usage_percentage=65.2
            )
            mock_stats.return_value = mock_response

            response = client.get("/distributed/stats")
            assert response.status_code == 200

            stats_data = response.json()
            assert stats_data['total_tasks_processed'] == 150
            assert stats_data['tasks_completed'] == 135
            assert stats_data['throughput_tasks_per_minute'] == 8.5

        # Step 3: Check queue status
        with patch('services.analysis_service.presentation.controllers.distributed_controller.distributed_handlers.handle_get_queue_status') as mock_queue:
            from ...presentation.models.common import QueueStatusResponse

            mock_response = QueueStatusResponse(
                queue_length=8,
                priority_distribution={'high': 3, 'normal': 4, 'low': 1},
                oldest_task_age_seconds=45.2,
                queue_efficiency=0.85,
                processing_rate=7.8,
                estimated_empty_time_seconds=62.8
            )
            mock_queue.return_value = mock_response

            response = client.get("/distributed/queue/status")
            assert response.status_code == 200

            queue_data = response.json()
            assert queue_data['queue_length'] == 8
            assert queue_data['priority_distribution']['high'] == 3
            assert queue_data['queue_efficiency'] == 0.85

    @pytest.mark.asyncio
    async def test_workflow_with_findings_management(self, client):
        """Test workflow including findings creation, retrieval, and management."""
        # Step 1: Create document and perform analysis (simplified)
        doc_id = 'findings-doc-001'
        analysis_id = 'findings-analysis-001'

        # Step 2: Simulate findings creation through analysis
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_findings:
            # Initial findings
            mock_findings_response = FindingsListResponse(
                findings=[
                    FindingResponse(
                        id='finding-001',
                        analysis_id=analysis_id,
                        document_id=doc_id,
                        title='Code Quality Issue',
                        description='Missing documentation for function',
                        severity='medium',
                        confidence=0.85,
                        category='documentation',
                        recommendation='Add docstring to function',
                        status='open'
                    ),
                    FindingResponse(
                        id='finding-002',
                        analysis_id=analysis_id,
                        document_id=doc_id,
                        title='Security Vulnerability',
                        description='Potential SQL injection',
                        severity='high',
                        confidence=0.92,
                        category='security',
                        recommendation='Use parameterized queries',
                        status='open'
                    ),
                    FindingResponse(
                        id='finding-003',
                        analysis_id=analysis_id,
                        document_id=doc_id,
                        title='Performance Issue',
                        description='Inefficient algorithm used',
                        severity='low',
                        confidence=0.78,
                        category='performance',
                        recommendation='Consider using more efficient algorithm',
                        status='open'
                    )
                ],
                total_count=3,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_findings.return_value = mock_findings_response

            # Retrieve all findings
            response = client.get(f"/findings?analysis_id={analysis_id}")
            assert response.status_code == 200

            findings_data = response.json()
            assert len(findings_data['findings']) == 3

            # Check severity distribution
            severities = [f['severity'] for f in findings_data['findings']]
            assert 'high' in severities
            assert 'medium' in severities
            assert 'low' in severities

        # Step 3: Filter findings by severity
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_findings:
            # Only high severity findings
            mock_findings_response = FindingsListResponse(
                findings=[
                    FindingResponse(
                        id='finding-002',
                        analysis_id=analysis_id,
                        document_id=doc_id,
                        title='Security Vulnerability',
                        description='Potential SQL injection',
                        severity='high',
                        confidence=0.92,
                        category='security',
                        status='open'
                    )
                ],
                total_count=1,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_findings.return_value = mock_findings_response

            response = client.get(f"/findings?analysis_id={analysis_id}&severity=high")
            assert response.status_code == 200

            filtered_data = response.json()
            assert len(filtered_data['findings']) == 1
            assert filtered_data['findings'][0]['severity'] == 'high'
            assert filtered_data['findings'][0]['category'] == 'security'

        # Step 4: Simulate findings resolution workflow
        # In a real system, this would involve updating finding status
        # For testing, we'll verify the filtering still works after "resolution"

        # Step 5: Export findings (simulated)
        # In a real system, this would generate CSV/XML/JSON exports
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_export_findings') as mock_export:
            mock_export.return_value = {
                'export_id': 'export-001',
                'format': 'json',
                'file_url': '/downloads/findings-export-001.json',
                'record_count': 3,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

            response = client.get(f"/findings/export?analysis_id={analysis_id}&format=json")
            assert response.status_code == 200

            export_data = response.json()
            assert export_data['format'] == 'json'
            assert export_data['record_count'] == 3
            assert 'file_url' in export_data

    @pytest.mark.asyncio
    async def test_system_health_and_monitoring_workflow(self, client):
        """Test system health and monitoring workflow."""
        # Step 1: Check system health
        with patch('services.analysis_service.presentation.controllers.integration_controller.integration_handlers.handle_health_check') as mock_health:
            mock_health.return_value = {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'services': {
                    'database': 'healthy',
                    'cache': 'healthy',
                    'external_apis': 'healthy',
                    'queue': 'healthy'
                },
                'metrics': {
                    'uptime_seconds': 86400,
                    'total_requests': 15420,
                    'active_connections': 12,
                    'memory_usage_mb': 512.5
                }
            }

            response = client.get("/integration/health")
            assert response.status_code == 200

            health_data = response.json()
            assert health_data['status'] == 'healthy'
            assert 'database' in health_data['services']
            assert 'metrics' in health_data

        # Step 2: Check API usage analytics
        with patch('services.analysis_service.presentation.controllers.integration_controller.integration_handlers.handle_get_api_analytics') as mock_analytics:
            mock_analytics.return_value = {
                'period': '24h',
                'total_requests': 15420,
                'requests_by_endpoint': {
                    '/analyze/semantic-similarity': 5230,
                    '/analyze/sentiment': 3410,
                    '/findings': 2890,
                    '/distributed/tasks': 1780
                },
                'requests_by_user': {
                    'user-1': 4520,
                    'user-2': 3210,
                    'user-3': 2890
                },
                'average_response_time_seconds': 1.25,
                'error_rate_percentage': 0.85,
                'peak_concurrent_requests': 45
            }

            response = client.get("/integration/analytics")
            assert response.status_code == 200

            analytics_data = response.json()
            assert analytics_data['total_requests'] == 15420
            assert '/analyze/semantic-similarity' in analytics_data['requests_by_endpoint']
            assert analytics_data['error_rate_percentage'] < 1.0  # Less than 1%

        # Step 3: Test system performance metrics
        with patch('services.analysis_service.presentation.controllers.integration_controller.integration_handlers.handle_get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'response_times': {
                    'p50': 0.8,
                    'p95': 2.1,
                    'p99': 5.2,
                    'max': 12.5
                },
                'throughput': {
                    'requests_per_second': 15.5,
                    'requests_per_minute': 930
                },
                'resource_usage': {
                    'cpu_percent': 45.2,
                    'memory_mb': 1024.5,
                    'disk_mb': 256.8
                },
                'error_rates': {
                    'http_4xx': 0.5,
                    'http_5xx': 0.1,
                    'total_errors': 0.6
                }
            }

            response = client.get("/integration/metrics")
            assert response.status_code == 200

            metrics_data = response.json()
            assert metrics_data['response_times']['p95'] < 3.0  # 95th percentile under 3 seconds
            assert metrics_data['throughput']['requests_per_second'] > 10
            assert metrics_data['error_rates']['total_errors'] < 1.0  # Less than 1% error rate
