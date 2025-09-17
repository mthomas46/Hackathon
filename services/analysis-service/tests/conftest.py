"""Test configuration and shared fixtures for the analysis service test suite."""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

# Domain imports
from ..domain.entities.document import Document, DocumentStatus
from ..domain.entities.analysis import Analysis, AnalysisStatus
from ..domain.entities.finding import Finding, FindingSeverity
from ..domain.entities.repository import Repository, RepositoryType

from ..domain.value_objects.analysis_type import AnalysisType
from ..domain.value_objects.confidence import Confidence
from ..domain.value_objects.location import Location, FileLocation, CodeLocation
from ..domain.value_objects.metrics import AnalysisMetrics, QualityMetrics

from ..domain.services.analysis_service import AnalysisService
from ..domain.services.document_service import DocumentService
from ..domain.services.finding_service import FindingService

from ..domain.repositories.document_repository import DocumentRepository
from ..domain.repositories.analysis_repository import AnalysisRepository
from ..domain.repositories.finding_repository import FindingRepository

from ..domain.factories.analysis_factory import AnalysisFactory
from ..domain.factories.document_factory import DocumentFactory
from ..domain.factories.finding_factory import FindingFactory

from ..infrastructure.repositories.in_memory.document_repository import InMemoryDocumentRepository
from ..infrastructure.repositories.in_memory.analysis_repository import InMemoryAnalysisRepository
from ..infrastructure.repositories.in_memory.finding_repository import InMemoryFindingRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_directory():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Sample document data for testing."""
    return {
        'id': 'test-doc-001',
        'title': 'Test Document',
        'content': '# Test Document\n\nThis is a test document for unit testing.',
        'file_path': '/path/to/test/document.md',
        'repository_id': 'test-repo-001',
        'author': 'test-author',
        'version': '1.0.0',
        'status': DocumentStatus.ACTIVE,
        'metadata': {
            'language': 'markdown',
            'size': 1024,
            'lines': 10
        }
    }


@pytest.fixture
def sample_analysis_data() -> Dict[str, Any]:
    """Sample analysis data for testing."""
    return {
        'id': 'test-analysis-001',
        'document_id': 'test-doc-001',
        'analysis_type': AnalysisType.SEMANTIC_SIMILARITY,
        'status': AnalysisStatus.COMPLETED,
        'confidence': Confidence(0.85),
        'metrics': AnalysisMetrics(
            processing_time_seconds=2.5,
            memory_usage_mb=50.0,
            confidence_score=0.85
        ),
        'results': {
            'similarity_score': 0.85,
            'matched_documents': ['doc-002', 'doc-003']
        },
        'metadata': {
            'algorithm_version': '1.0.0',
            'model_used': 'sentence-transformers'
        }
    }


@pytest.fixture
def sample_finding_data() -> Dict[str, Any]:
    """Sample finding data for testing."""
    return {
        'id': 'test-finding-001',
        'analysis_id': 'test-analysis-001',
        'document_id': 'test-doc-001',
        'title': 'Test Finding',
        'description': 'This is a test finding for unit testing.',
        'severity': FindingSeverity.MEDIUM,
        'confidence': Confidence(0.75),
        'location': CodeLocation(
            file_path='/path/to/file.py',
            start_line=10,
            end_line=15,
            start_column=5,
            end_column=20
        ),
        'category': 'code_quality',
        'recommendation': 'Consider refactoring this code for better readability.',
        'metadata': {
            'rule_id': 'TEST-001',
            'tags': ['test', 'code_quality']
        }
    }


@pytest.fixture
def sample_repository_data() -> Dict[str, Any]:
    """Sample repository data for testing."""
    return {
        'id': 'test-repo-001',
        'name': 'Test Repository',
        'url': 'https://github.com/test/repo',
        'type': RepositoryType.GIT,
        'branch': 'main',
        'last_sync': datetime.now(timezone.utc),
        'metadata': {
            'language': 'python',
            'stars': 100,
            'forks': 20
        }
    }


@pytest.fixture
def document_factory() -> DocumentFactory:
    """Document factory fixture."""
    return DocumentFactory()


@pytest.fixture
def analysis_factory() -> AnalysisFactory:
    """Analysis factory fixture."""
    return AnalysisFactory()


@pytest.fixture
def finding_factory() -> FindingFactory:
    """Finding factory fixture."""
    return FindingFactory()


@pytest.fixture
def document_repository() -> DocumentRepository:
    """In-memory document repository fixture."""
    return InMemoryDocumentRepository()


@pytest.fixture
def analysis_repository() -> AnalysisRepository:
    """In-memory analysis repository fixture."""
    return InMemoryAnalysisRepository()


@pytest.fixture
def finding_repository() -> FindingRepository:
    """In-memory finding repository fixture."""
    return InMemoryFindingRepository()


@pytest.fixture
def document_service(document_repository: DocumentRepository) -> DocumentService:
    """Document service fixture."""
    return DocumentService(document_repository)


@pytest.fixture
def analysis_service(
    analysis_repository: AnalysisRepository,
    document_repository: DocumentRepository
) -> AnalysisService:
    """Analysis service fixture."""
    return AnalysisService(analysis_repository, document_repository)


@pytest.fixture
def finding_service(finding_repository: FindingRepository) -> FindingService:
    """Finding service fixture."""
    return FindingService(finding_repository)


@pytest.fixture
def sample_document(
    document_factory: DocumentFactory,
    sample_document_data: Dict[str, Any]
) -> Document:
    """Sample document fixture."""
    return document_factory.create_document(**sample_document_data)


@pytest.fixture
def sample_analysis(
    analysis_factory: AnalysisFactory,
    sample_analysis_data: Dict[str, Any]
) -> Analysis:
    """Sample analysis fixture."""
    return analysis_factory.create_analysis(**sample_analysis_data)


@pytest.fixture
def sample_finding(
    finding_factory: FindingFactory,
    sample_finding_data: Dict[str, Any]
) -> Finding:
    """Sample finding fixture."""
    return finding_factory.create_finding(**sample_finding_data)


@pytest.fixture
def sample_repository(sample_repository_data: Dict[str, Any]) -> Repository:
    """Sample repository fixture."""
    return Repository(**sample_repository_data)


@pytest.fixture
def confidence_high() -> Confidence:
    """High confidence fixture."""
    return Confidence(0.95)


@pytest.fixture
def confidence_medium() -> Confidence:
    """Medium confidence fixture."""
    return Confidence(0.75)


@pytest.fixture
def confidence_low() -> Confidence:
    """Low confidence fixture."""
    return Confidence(0.45)


@pytest.fixture
def file_location() -> FileLocation:
    """File location fixture."""
    return FileLocation(
        file_path='/src/main.py',
        line_number=42
    )


@pytest.fixture
def code_location() -> CodeLocation:
    """Code location fixture."""
    return CodeLocation(
        file_path='/src/utils.py',
        start_line=10,
        end_line=15,
        start_column=5,
        end_column=25
    )


@pytest.fixture
def analysis_metrics() -> AnalysisMetrics:
    """Analysis metrics fixture."""
    return AnalysisMetrics(
        processing_time_seconds=3.5,
        memory_usage_mb=75.0,
        confidence_score=0.82
    )


@pytest.fixture
def quality_metrics() -> QualityMetrics:
    """Quality metrics fixture."""
    return QualityMetrics(
        readability_score=85.0,
        complexity_score=25.0,
        maintainability_index=78.0,
        duplication_percentage=5.2
    )


@pytest.fixture
def test_data_populator(
    document_repository: DocumentRepository,
    analysis_repository: AnalysisRepository,
    finding_repository: FindingRepository,
    document_factory: DocumentFactory,
    analysis_factory: AnalysisFactory,
    finding_factory: FindingFactory
):
    """Test data populator fixture for setting up complex test scenarios."""

    class TestDataPopulator:
        def __init__(self):
            self.documents = []
            self.analyses = []
            self.findings = []

        def create_test_documents(self, count: int = 5) -> List[Document]:
            """Create multiple test documents."""
            documents = []
            for i in range(count):
                doc_data = {
                    'id': f'test-doc-{i:03d}',
                    'title': f'Test Document {i}',
                    'content': f'# Test Document {i}\n\nContent for document {i}.',
                    'file_path': f'/docs/test-doc-{i}.md',
                    'repository_id': 'test-repo-001',
                    'author': f'author-{i}',
                    'version': f'1.{i}.0'
                }
                doc = document_factory.create_document(**doc_data)
                document_repository.save(doc)
                documents.append(doc)
                self.documents.append(doc)
            return documents

        def create_test_analyses(self, document_ids: List[str], count_per_doc: int = 2) -> List[Analysis]:
            """Create test analyses for documents."""
            analyses = []
            for doc_id in document_ids:
                for i in range(count_per_doc):
                    analysis_data = {
                        'id': f'analysis-{doc_id}-{i}',
                        'document_id': doc_id,
                        'analysis_type': AnalysisType.SEMANTIC_SIMILARITY if i % 2 == 0 else AnalysisType.CODE_QUALITY,
                        'status': AnalysisStatus.COMPLETED,
                        'confidence': Confidence(0.8 + i * 0.05),
                        'results': {'test_result': f'result_{i}'}
                    }
                    analysis = analysis_factory.create_analysis(**analysis_data)
                    analysis_repository.save(analysis)
                    analyses.append(analysis)
                    self.analyses.append(analysis)
            return analyses

        def create_test_findings(self, analysis_ids: List[str], count_per_analysis: int = 3) -> List[Finding]:
            """Create test findings for analyses."""
            findings = []
            for analysis_id in analysis_ids:
                for i in range(count_per_analysis):
                    finding_data = {
                        'id': f'finding-{analysis_id}-{i}',
                        'analysis_id': analysis_id,
                        'document_id': f'doc-{analysis_id.split("-")[1]}',
                        'title': f'Test Finding {i}',
                        'description': f'Description for finding {i}',
                        'severity': FindingSeverity.LOW if i % 3 == 0 else FindingSeverity.MEDIUM if i % 3 == 1 else FindingSeverity.HIGH,
                        'confidence': Confidence(0.7 + i * 0.1),
                        'location': FileLocation(f'/src/file{i}.py', i * 10),
                        'category': 'test_category',
                        'recommendation': f'Recommendation {i}'
                    }
                    finding = finding_factory.create_finding(**finding_data)
                    finding_repository.save(finding)
                    findings.append(finding)
                    self.findings.append(finding)
            return findings

        def cleanup(self):
            """Clean up test data."""
            for finding in self.findings:
                finding_repository.delete(finding.id)
            for analysis in self.analyses:
                analysis_repository.delete(analysis.id)
            for doc in self.documents:
                document_repository.delete(doc.id)

            self.documents.clear()
            self.analyses.clear()
            self.findings.clear()

    populator = TestDataPopulator()
    yield populator
    populator.cleanup()


# Test configuration
@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration."""
    return {
        'database_url': 'sqlite:///:memory:',
        'redis_url': 'redis://localhost:6379/1',
        'log_level': 'DEBUG',
        'test_timeout': 30,
        'mock_external_services': True
    }


# Async test utilities
@pytest.fixture
def async_test_timeout():
    """Timeout for async tests."""
    return 30


# Exception testing utilities
@pytest.fixture
def expect_exception():
    """Context manager for testing exceptions."""
    class ExceptionContext:
        def __init__(self, exception_type):
            self.exception_type = exception_type
            self.exception = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                pytest.fail(f"Expected {self.exception_type.__name__} but no exception was raised")
            if not isinstance(exc_val, self.exception_type):
                pytest.fail(f"Expected {self.exception_type.__name__} but got {exc_type.__name__}")
            self.exception = exc_val
            return True

    def _expect_exception(exception_type):
        return ExceptionContext(exception_type)

    return _expect_exception


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def duration(self):
            if self.start_time is None or self.end_time is None:
                return 0
            return self.end_time - self.start_time

        def assert_less_than(self, max_duration, message="Operation took too long"):
            assert self.duration < max_duration, f"{message}: {self.duration:.3f}s >= {max_duration:.3f}s"

    return PerformanceTimer()