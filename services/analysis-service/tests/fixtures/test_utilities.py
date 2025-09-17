"""Test Utilities - Mock factories and test helpers."""

import asyncio
import time
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional, Callable, TypeVar
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.services import AnalysisService
from ...infrastructure.repositories import DocumentRepository, AnalysisRepository, FindingRepository


T = TypeVar('T')


class MockFactory:
    """Factory for creating mocks with consistent behavior."""

    @staticmethod
    def create_document_repository_mock() -> Mock:
        """Create a mock document repository."""
        mock_repo = Mock(spec=DocumentRepository)

        # Mock successful operations
        mock_repo.save = AsyncMock(return_value=None)
        mock_repo.get_by_id = AsyncMock(return_value=Mock(id='test-doc', title='Test Document'))
        mock_repo.get_all = AsyncMock(return_value=[])
        mock_repo.delete = AsyncMock(return_value=None)
        mock_repo.exists = AsyncMock(return_value=True)

        return mock_repo

    @staticmethod
    def create_analysis_repository_mock() -> Mock:
        """Create a mock analysis repository."""
        mock_repo = Mock(spec=AnalysisRepository)

        # Mock successful operations
        mock_repo.save = AsyncMock(return_value=None)
        mock_repo.get_by_id = AsyncMock(return_value=Mock(id='test-analysis', status=AnalysisStatus.COMPLETED))
        mock_repo.get_by_document_id = AsyncMock(return_value=[])
        mock_repo.get_recent = AsyncMock(return_value=[])
        mock_repo.delete = AsyncMock(return_value=None)

        return mock_repo

    @staticmethod
    def create_finding_repository_mock() -> Mock:
        """Create a mock finding repository."""
        mock_repo = Mock(spec=FindingRepository)

        # Mock successful operations
        mock_repo.save = AsyncMock(return_value=None)
        mock_repo.get_by_id = AsyncMock(return_value=Mock(id='test-finding', severity=FindingSeverity.MEDIUM))
        mock_repo.get_by_analysis_id = AsyncMock(return_value=[])
        mock_repo.get_by_document_id = AsyncMock(return_value=[])
        mock_repo.get_by_filters = AsyncMock(return_value=[])
        mock_repo.delete = AsyncMock(return_value=None)

        return mock_repo

    @staticmethod
    def create_analysis_service_mock() -> Mock:
        """Create a mock analysis service."""
        mock_service = Mock(spec=AnalysisService)

        # Mock successful analysis operations
        mock_service.perform_semantic_similarity_analysis = AsyncMock(return_value={
            'analysis_id': 'semantic-analysis-001',
            'status': 'completed',
            'similarity_matrix': [[1.0, 0.8], [0.8, 1.0]],
            'similar_pairs': [{'source': 'doc-1', 'target': 'doc-2', 'similarity': 0.8}]
        })

        mock_service.perform_sentiment_analysis = AsyncMock(return_value={
            'analysis_id': 'sentiment-analysis-001',
            'sentiment': 'positive',
            'confidence': 0.85,
            'scores': {'positive': 0.85, 'negative': 0.10, 'neutral': 0.05}
        })

        mock_service.perform_content_quality_analysis = AsyncMock(return_value={
            'analysis_id': 'quality-analysis-001',
            'overall_score': 82.5,
            'quality_breakdown': {
                'readability': {'score': 78.0, 'level': 'good'},
                'grammar': {'score': 85.0, 'level': 'excellent'}
            }
        })

        return mock_service

    @staticmethod
    def create_external_service_mock(service_name: str) -> Mock:
        """Create a mock external service."""
        mock_service = Mock()

        if service_name == 'semantic_analyzer':
            mock_service.analyze_similarity = AsyncMock(return_value={
                'similarity_score': 0.85,
                'embedding_distance': 0.15,
                'confidence': 0.92
            })
        elif service_name == 'sentiment_analyzer':
            mock_service.analyze_sentiment = AsyncMock(return_value={
                'sentiment': 'positive',
                'confidence': 0.88,
                'scores': {'positive': 0.88, 'negative': 0.08, 'neutral': 0.04}
            })
        elif service_name == 'content_quality_scorer':
            mock_service.assess_quality = AsyncMock(return_value={
                'overall_score': 82.5,
                'readability_score': 78.0,
                'grammar_score': 85.0,
                'structure_score': 80.0
            })

        return mock_service

    @staticmethod
    def create_http_client_mock() -> Mock:
        """Create a mock HTTP client."""
        mock_client = Mock()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={'status': 'success', 'data': 'test'})
        mock_response.text = 'success'
        mock_response.headers = {'content-type': 'application/json'}

        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.put = AsyncMock(return_value=mock_response)
        mock_client.delete = AsyncMock(return_value=mock_response)

        return mock_client

    @staticmethod
    def create_cache_mock() -> Mock:
        """Create a mock cache."""
        mock_cache = Mock()

        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)
        mock_cache.delete = AsyncMock(return_value=True)
        mock_cache.exists = AsyncMock(return_value=False)
        mock_cache.clear = AsyncMock(return_value=None)

        return mock_cache

    @staticmethod
    def create_queue_mock() -> Mock:
        """Create a mock queue for distributed processing."""
        mock_queue = Mock()

        mock_queue.enqueue = AsyncMock(return_value='task-123')
        mock_queue.dequeue = AsyncMock(return_value={'task_id': 'task-123', 'data': 'test'})
        mock_queue.get_status = AsyncMock(return_value={'status': 'pending', 'position': 1})
        mock_queue.cancel = AsyncMock(return_value=True)
        mock_queue.get_stats = AsyncMock(return_value={
            'queue_length': 5,
            'processing_rate': 10,
            'total_processed': 100
        })

        return mock_queue

    @staticmethod
    def create_worker_pool_mock() -> Mock:
        """Create a mock worker pool."""
        mock_pool = Mock()

        mock_pool.submit_task = AsyncMock(return_value='worker-task-123')
        mock_pool.get_worker_status = AsyncMock(return_value=[
            {'worker_id': 'worker-1', 'status': 'active', 'current_task': 'task-1'},
            {'worker_id': 'worker-2', 'status': 'idle', 'current_task': None}
        ])
        mock_pool.scale_workers = AsyncMock(return_value={'previous_count': 2, 'new_count': 4})
        mock_pool.get_stats = AsyncMock(return_value={
            'active_workers': 3,
            'idle_workers': 1,
            'total_workers': 4,
            'avg_utilization': 0.75
        })

        return mock_pool


class AsyncMockHelper:
    """Helper for creating and managing async mocks."""

    @staticmethod
    def create_async_mock(return_value: Any = None, side_effect: Any = None) -> AsyncMock:
        """Create an async mock with specified behavior."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock

    @staticmethod
    def create_delayed_mock(delay_seconds: float, return_value: Any = None) -> AsyncMock:
        """Create an async mock that introduces a delay."""
        async def delayed_function(*args, **kwargs):
            await asyncio.sleep(delay_seconds)
            return return_value

        return AsyncMock(side_effect=delayed_function)

    @staticmethod
    def create_failing_mock(exception: Exception) -> AsyncMock:
        """Create an async mock that raises an exception."""
        return AsyncMock(side_effect=exception)

    @staticmethod
    def create_sequential_mock(return_values: List[Any]) -> AsyncMock:
        """Create an async mock that returns different values on successive calls."""
        return AsyncMock(side_effect=return_values)


class TestDataBuilder:
    """Builder for creating test data structures."""

    def __init__(self):
        self.data = {}

    def with_document(self, **kwargs) -> 'TestDataBuilder':
        """Add document data to builder."""
        default_doc = {
            'id': 'test-doc-123',
            'title': 'Test Document',
            'content': 'This is test content for unit testing.',
            'repository_id': 'test-repo',
            'author': 'test-author@test.com',
            'version': '1.0.0',
            'status': 'active'
        }
        default_doc.update(kwargs)
        self.data['document'] = default_doc
        return self

    def with_analysis(self, **kwargs) -> 'TestDataBuilder':
        """Add analysis data to builder."""
        default_analysis = {
            'id': 'test-analysis-123',
            'document_id': 'test-doc-123',
            'analysis_type': 'semantic_similarity',
            'status': 'completed',
            'confidence': 0.85,
            'results': {'score': 0.82, 'processing_time': 1.2},
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        default_analysis.update(kwargs)
        self.data['analysis'] = default_analysis
        return self

    def with_findings(self, count: int = 3, **kwargs) -> 'TestDataBuilder':
        """Add findings data to builder."""
        findings = []
        for i in range(count):
            finding = {
                'id': f'finding-{i}',
                'analysis_id': 'test-analysis-123',
                'document_id': 'test-doc-123',
                'title': f'Test Finding {i}',
                'description': f'This is test finding {i}',
                'severity': 'medium',
                'confidence': 0.8,
                'category': 'test',
                'recommendation': f'Fix issue {i}',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            finding.update(kwargs)
            findings.append(finding)

        self.data['findings'] = findings
        return self

    def with_api_request(self, request_type: str, **kwargs) -> 'TestDataBuilder':
        """Add API request data to builder."""
        requests = {
            'semantic_similarity': {
                'targets': ['doc-1', 'doc-2', 'doc-3'],
                'threshold': 0.8,
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
            },
            'sentiment_analysis': {
                'document_id': 'test-doc-123',
                'analysis_options': {'include_detailed_scores': True}
            },
            'content_quality': {
                'document_id': 'test-doc-123',
                'quality_checks': ['readability', 'grammar']
            }
        }

        request_data = requests.get(request_type, {})
        request_data.update(kwargs)
        self.data['api_request'] = request_data
        return self

    def build(self) -> Dict[str, Any]:
        """Build the test data structure."""
        return self.data.copy()


class PerformanceMonitor:
    """Monitor performance of test operations."""

    def __init__(self):
        self.start_time = None
        self.measurements = []

    def start(self):
        """Start performance measurement."""
        self.start_time = time.time()

    def stop(self) -> float:
        """Stop performance measurement and return elapsed time."""
        if self.start_time is None:
            return 0.0

        elapsed = time.time() - self.start_time
        self.measurements.append(elapsed)
        self.start_time = None
        return elapsed

    def measure_async(self, coro) -> tuple:
        """Measure the performance of an async coroutine."""
        async def _measure():
            start = time.time()
            result = await coro
            elapsed = time.time() - start
            self.measurements.append(elapsed)
            return result, elapsed

        return _measure()

    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        if not self.measurements:
            return {'count': 0, 'total': 0.0, 'average': 0.0, 'min': 0.0, 'max': 0.0}

        return {
            'count': len(self.measurements),
            'total': sum(self.measurements),
            'average': sum(self.measurements) / len(self.measurements),
            'min': min(self.measurements),
            'max': max(self.measurements)
        }

    def reset(self):
        """Reset measurements."""
        self.measurements = []
        self.start_time = None


@asynccontextmanager
async def mock_database_session():
    """Context manager for mocking database sessions."""
    mock_session = Mock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    try:
        yield mock_session
    finally:
        await mock_session.close()


@asynccontextmanager
async def mock_external_service(service_name: str, response_data: Any = None):
    """Context manager for mocking external services."""
    if response_data is None:
        response_data = {'status': 'success', 'data': f'mock_{service_name}_response'}

    mock_service = MockFactory.create_external_service_mock(service_name)

    # Override the mock to return the specified response data
    if hasattr(mock_service, 'analyze_similarity'):
        mock_service.analyze_similarity.return_value = response_data
    elif hasattr(mock_service, 'analyze_sentiment'):
        mock_service.analyze_sentiment.return_value = response_data
    elif hasattr(mock_service, 'assess_quality'):
        mock_service.assess_quality.return_value = response_data

    try:
        yield mock_service
    finally:
        pass


class TestScenarioRunner:
    """Runner for complex test scenarios."""

    def __init__(self):
        self.scenarios = {}

    def add_scenario(self, name: str, steps: List[Callable], setup: Callable = None, teardown: Callable = None):
        """Add a test scenario."""
        self.scenarios[name] = {
            'steps': steps,
            'setup': setup,
            'teardown': teardown
        }

    async def run_scenario(self, name: str, **kwargs) -> Dict[str, Any]:
        """Run a test scenario."""
        if name not in self.scenarios:
            raise ValueError(f"Scenario '{name}' not found")

        scenario = self.scenarios[name]
        results = {
            'scenario': name,
            'steps_executed': [],
            'errors': [],
            'duration': 0.0
        }

        start_time = time.time()

        try:
            # Setup
            if scenario['setup']:
                await scenario['setup'](**kwargs)

            # Execute steps
            for i, step in enumerate(scenario['steps']):
                step_name = f'step_{i}'
                try:
                    await step(**kwargs)
                    results['steps_executed'].append(step_name)
                except Exception as e:
                    results['errors'].append({
                        'step': step_name,
                        'error': str(e),
                        'type': type(e).__name__
                    })

            # Teardown
            if scenario['teardown']:
                await scenario['teardown'](**kwargs)

        except Exception as e:
            results['errors'].append({
                'step': 'setup/teardown',
                'error': str(e),
                'type': type(e).__name__
            })

        results['duration'] = time.time() - start_time
        return results


class ValidationHelper:
    """Helper for validating test data and responses."""

    @staticmethod
    def validate_document_structure(doc_data: Dict[str, Any]) -> bool:
        """Validate document data structure."""
        required_fields = ['id', 'title', 'content', 'repository_id', 'author']
        return all(field in doc_data for field in required_fields)

    @staticmethod
    def validate_analysis_structure(analysis_data: Dict[str, Any]) -> bool:
        """Validate analysis data structure."""
        required_fields = ['id', 'document_id', 'analysis_type', 'status']
        return all(field in analysis_data for field in required_fields)

    @staticmethod
    def validate_finding_structure(finding_data: Dict[str, Any]) -> bool:
        """Validate finding data structure."""
        required_fields = ['id', 'analysis_id', 'document_id', 'title', 'severity']
        return all(field in finding_data for field in required_fields)

    @staticmethod
    def validate_api_response(response_data: Dict[str, Any], expected_fields: List[str]) -> bool:
        """Validate API response structure."""
        return all(field in response_data for field in expected_fields)

    @staticmethod
    def validate_performance_threshold(actual_time: float, max_threshold: float) -> bool:
        """Validate performance against threshold."""
        return actual_time <= max_threshold

    @staticmethod
    def compare_response_times(times: List[float], tolerance_percent: float = 10.0) -> bool:
        """Compare response times for consistency."""
        if len(times) < 2:
            return True

        avg_time = sum(times) / len(times)
        tolerance = avg_time * (tolerance_percent / 100.0)

        return all(abs(t - avg_time) <= tolerance for t in times)


# Global instances for easy access
mock_factory = MockFactory()
async_helper = AsyncMockHelper()
test_builder = TestDataBuilder()
performance_monitor = PerformanceMonitor()
scenario_runner = TestScenarioRunner()
validation_helper = ValidationHelper()
