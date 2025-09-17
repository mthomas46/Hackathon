"""Test configuration and fixtures for Analysis Service tests."""

import pytest
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ..domain.entities.document import Document
from ..domain.entities.analysis import Analysis
from ..domain.entities.finding import Finding
from ..domain.entities.repository import Repository
from ..domain.value_objects import AnalysisType, Confidence, Location, Metrics
from ..infrastructure.repositories import InMemoryDocumentRepository, InMemoryAnalysisRepository, InMemoryFindingRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Sample document data for testing."""
    return {
        'id': 'doc-123',
        'title': 'Test Document',
        'content': 'This is a test document for analysis.',
        'author': 'Test Author',
        'tags': ['test', 'documentation'],
        'metadata': {
            'language': 'en',
            'word_count': 50,
            'last_modified': datetime.now(timezone.utc)
        }
    }


@pytest.fixture
def sample_analysis_data() -> Dict[str, Any]:
    """Sample analysis data for testing."""
    return {
        'id': 'analysis-123',
        'document_id': 'doc-123',
        'analysis_type': AnalysisType.CONSISTENCY,
        'status': 'completed',
        'results': {'score': 0.85, 'issues_found': 2},
        'metadata': {'processing_time': 1.2}
    }


@pytest.fixture
def sample_finding_data() -> Dict[str, Any]:
    """Sample finding data for testing."""
    return {
        'id': 'finding-123',
        'document_id': 'doc-123',
        'analysis_id': 'analysis-123',
        'severity': 'medium',
        'category': 'consistency',
        'description': 'Inconsistent terminology detected',
        'location': {'line': 10, 'column': 5},
        'suggestion': 'Use consistent terminology',
        'confidence': 0.8
    }


@pytest.fixture
def sample_repository_data() -> Dict[str, Any]:
    """Sample repository data for testing."""
    return {
        'id': 'repo-123',
        'name': 'test-repo',
        'url': 'https://github.com/test/repo',
        'branch': 'main',
        'last_sync': datetime.now(timezone.utc),
        'documents': ['doc-123', 'doc-456']
    }


@pytest.fixture
def document_entity(sample_document_data) -> Document:
    """Create a sample document entity."""
    return Document(
        id=sample_document_data['id'],
        title=sample_document_data['title'],
        content=sample_document_data['content'],
        author=sample_document_data['author'],
        tags=sample_document_data['tags'],
        metadata=sample_document_data['metadata']
    )


@pytest.fixture
def analysis_entity(sample_analysis_data) -> Analysis:
    """Create a sample analysis entity."""
    return Analysis(
        id=sample_analysis_data['id'],
        document_id=sample_analysis_data['document_id'],
        analysis_type=sample_analysis_data['analysis_type'],
        status=sample_analysis_data['status'],
        results=sample_analysis_data['results'],
        metadata=sample_analysis_data['metadata']
    )


@pytest.fixture
def finding_entity(sample_finding_data) -> Finding:
    """Create a sample finding entity."""
    return Finding(
        id=sample_finding_data['id'],
        document_id=sample_finding_data['document_id'],
        analysis_id=sample_finding_data['analysis_id'],
        severity=sample_finding_data['severity'],
        category=sample_finding_data['category'],
        description=sample_finding_data['description'],
        location=Location(**sample_finding_data['location']),
        suggestion=sample_finding_data['suggestion'],
        confidence=Confidence(value=sample_finding_data['confidence'])
    )


@pytest.fixture
def repository_entity(sample_repository_data) -> Repository:
    """Create a sample repository entity."""
    return Repository(
        id=sample_repository_data['id'],
        name=sample_repository_data['name'],
        url=sample_repository_data['url'],
        branch=sample_repository_data['branch'],
        last_sync=sample_repository_data['last_sync'],
        documents=sample_repository_data['documents']
    )


@pytest.fixture
def in_memory_document_repo() -> InMemoryDocumentRepository:
    """Create an in-memory document repository."""
    return InMemoryDocumentRepository()


@pytest.fixture
def in_memory_analysis_repo() -> InMemoryAnalysisRepository:
    """Create an in-memory analysis repository."""
    return InMemoryAnalysisRepository()


@pytest.fixture
def in_memory_finding_repo() -> InMemoryFindingRepository:
    """Create an in-memory finding repository."""
    return InMemoryFindingRepository()


@pytest.fixture
def populated_document_repo(in_memory_document_repo, document_entity) -> InMemoryDocumentRepository:
    """Create a populated document repository."""
    in_memory_document_repo.save(document_entity)
    return in_memory_document_repo


@pytest.fixture
def populated_analysis_repo(in_memory_analysis_repo, analysis_entity) -> InMemoryAnalysisRepository:
    """Create a populated analysis repository."""
    in_memory_analysis_repo.save(analysis_entity)
    return in_memory_analysis_repo


@pytest.fixture
def populated_finding_repo(in_memory_finding_repo, finding_entity) -> InMemoryFindingRepository:
    """Create a populated finding repository."""
    in_memory_finding_repo.save(finding_entity)
    return in_memory_finding_repo


class MockServiceClient:
    """Mock service client for testing."""

    def __init__(self):
        self.requests = []

    async def get(self, service: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Mock GET request."""
        self.requests.append(('GET', f"{service}/{endpoint}", kwargs))
        return {'status': 'success', 'data': {'mock': True}}

    async def post(self, service: str, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Mock POST request."""
        self.requests.append(('POST', f"{service}/{endpoint}", data, kwargs))
        return {'status': 'success', 'data': {'created': True}}


@pytest.fixture
def mock_service_client() -> MockServiceClient:
    """Create a mock service client."""
    return MockServiceClient()


class AsyncMock:
    """Async mock for testing async functions."""

    def __init__(self, return_value=None):
        self.return_value = return_value
        self.call_count = 0
        self.call_args = []

    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args.append((args, kwargs))
        return self.return_value

    def assert_called_once(self):
        assert self.call_count == 1

    def assert_called_with(self, *args, **kwargs):
        assert (args, kwargs) in self.call_args


@pytest.fixture
def async_mock():
    """Create an async mock."""
    return AsyncMock


# Test utilities
def assert_entities_equal(entity1, entity2, exclude_fields=None):
    """Assert that two entities are equal, optionally excluding some fields."""
    exclude = exclude_fields or []
    exclude_set = set(exclude)

    dict1 = entity1.dict() if hasattr(entity1, 'dict') else entity1.__dict__
    dict2 = entity2.dict() if hasattr(entity2, 'dict') else entity2.__dict__

    for key in dict1:
        if key not in exclude_set:
            assert dict1[key] == dict2[key], f"Field {key} differs: {dict1[key]} != {dict2[key]}"


def assert_validation_error(func, *args, **kwargs):
    """Assert that a function raises a validation error."""
    with pytest.raises((ValueError, TypeError)):
        func(*args, **kwargs)


def assert_domain_error(func, error_type, *args, **kwargs):
    """Assert that a function raises a specific domain error."""
    with pytest.raises(error_type):
        func(*args, **kwargs)
