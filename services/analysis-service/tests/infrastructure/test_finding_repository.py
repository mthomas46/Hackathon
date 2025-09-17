"""Tests for Finding Repository Implementation."""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...infrastructure.repositories.finding_repository import (
    FindingRepository, InMemoryFindingRepository
)
from ...infrastructure.repositories.sqlite_finding_repository import SQLiteFindingRepository

from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.confidence import Confidence
from ...domain.value_objects.location import FileLocation, CodeLocation


class TestFindingRepositoryInterface:
    """Test cases for FindingRepository interface."""

    def test_repository_interface_definition(self):
        """Test that FindingRepository defines the expected interface."""
        repo_methods = [method for method in dir(FindingRepository) if not method.startswith('_')]

        expected_methods = [
            'save', 'get_by_id', 'get_all', 'get_by_analysis_id',
            'get_by_document_id', 'get_by_severity', 'delete'
        ]

        for method in expected_methods:
            assert method in repo_methods, f"Method {method} should be defined in FindingRepository"


class TestInMemoryFindingRepository:
    """Test cases for InMemoryFindingRepository."""

    @pytest.fixture
    def repository(self):
        """Create a fresh in-memory finding repository for each test."""
        return InMemoryFindingRepository()

    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding for testing."""
        return Finding(
            id='test-finding-123',
            analysis_id='analysis-456',
            document_id='doc-789',
            title='Test Finding',
            description='This is a test finding',
            severity=FindingSeverity.MEDIUM,
            confidence=Confidence(0.8),
            category='code_quality',
            location=FileLocation('/src/main.py', 42)
        )

    def test_repository_creation(self, repository):
        """Test creating an in-memory finding repository."""
        assert repository is not None
        assert isinstance(repository, FindingRepository)
        assert isinstance(repository, InMemoryFindingRepository)
        assert len(repository._findings) == 0

    @pytest.mark.asyncio
    async def test_save_and_retrieve_finding(self, repository, sample_finding):
        """Test saving and retrieving a finding."""
        await repository.save(sample_finding)

        retrieved = await repository.get_by_id(sample_finding.id.value)

        assert retrieved is not None
        assert retrieved == sample_finding
        assert retrieved.id.value == sample_finding.id.value
        assert retrieved.severity == FindingSeverity.MEDIUM
        assert retrieved.confidence.value == 0.8

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent(self, repository):
        """Test getting non-existent finding."""
        retrieved = await repository.get_by_id('non-existent-id')
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_all_findings(self, repository):
        """Test getting all findings."""
        # Create and save multiple findings
        findings = []
        for i in range(3):
            finding = Finding(
                id=f'test-finding-{i}',
                analysis_id='analysis-123',
                document_id='doc-456',
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)
            findings.append(finding)

        all_findings = await repository.get_all()
        assert len(all_findings) == 3

        retrieved_ids = [f.id.value for f in all_findings]
        expected_ids = [f.id.value for f in findings]
        assert set(retrieved_ids) == set(expected_ids)

    @pytest.mark.asyncio
    async def test_get_by_analysis_id(self, repository):
        """Test getting findings by analysis ID."""
        # Create findings for different analyses
        analysis_ids = ['analysis-1', 'analysis-2', 'analysis-1', 'analysis-3']

        for i, analysis_id in enumerate(analysis_ids):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id=analysis_id,
                document_id='doc-123',
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        # Get findings for analysis-1
        analysis_findings = await repository.get_by_analysis_id('analysis-1')
        assert len(analysis_findings) == 2
        for finding in analysis_findings:
            assert finding.analysis_id == 'analysis-1'

    @pytest.mark.asyncio
    async def test_get_by_document_id(self, repository):
        """Test getting findings by document ID."""
        # Create findings for different documents
        document_ids = ['doc-1', 'doc-2', 'doc-1', 'doc-3']

        for i, doc_id in enumerate(document_ids):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id='analysis-123',
                document_id=doc_id,
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        # Get findings for doc-1
        doc_findings = await repository.get_by_document_id('doc-1')
        assert len(doc_findings) == 2
        for finding in doc_findings:
            assert finding.document_id == 'doc-1'

    @pytest.mark.asyncio
    async def test_get_by_severity(self, repository):
        """Test getting findings by severity."""
        severities = [FindingSeverity.LOW, FindingSeverity.MEDIUM, FindingSeverity.HIGH, FindingSeverity.CRITICAL]

        for i, severity in enumerate(severities):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id='analysis-123',
                document_id='doc-456',
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=severity,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        # Get high severity findings
        high_findings = await repository.get_by_severity(FindingSeverity.HIGH)
        assert len(high_findings) == 1
        assert high_findings[0].severity == FindingSeverity.HIGH

        # Get all medium and higher severity findings
        medium_plus_findings = await repository.get_by_severity(FindingSeverity.MEDIUM)
        assert len(medium_plus_findings) >= 2  # Should include MEDIUM, HIGH, CRITICAL

    @pytest.mark.asyncio
    async def test_delete_finding(self, repository, sample_finding):
        """Test deleting a finding."""
        await repository.save(sample_finding)
        assert len(repository._findings) == 1

        result = await repository.delete(sample_finding.id.value)
        assert result is True
        assert len(repository._findings) == 0

        retrieved = await repository.get_by_id(sample_finding.id.value)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_finding(self, repository):
        """Test deleting non-existent finding."""
        result = await repository.delete('non-existent-id')
        assert result is False

    @pytest.mark.asyncio
    async def test_finding_with_file_location(self, repository):
        """Test finding with file location."""
        location = FileLocation('/src/utils.py', 150)

        finding = Finding(
            id='location-finding',
            analysis_id='analysis-123',
            document_id='doc-456',
            title='Location Finding',
            description='Finding with file location',
            severity=FindingSeverity.MEDIUM,
            confidence=Confidence(0.85),
            category='code_quality',
            location=location
        )

        await repository.save(finding)

        retrieved = await repository.get_by_id('location-finding')
        assert retrieved is not None
        assert retrieved.location == location
        assert retrieved.location.file_path == '/src/utils.py'
        assert retrieved.location.line_number == 150

    @pytest.mark.asyncio
    async def test_finding_with_code_location(self, repository):
        """Test finding with code location."""
        location = CodeLocation(
            file_path='/src/parser.py',
            start_line=25,
            end_line=35,
            start_column=10,
            end_column=25
        )

        finding = Finding(
            id='code-location-finding',
            analysis_id='analysis-123',
            document_id='doc-456',
            title='Code Location Finding',
            description='Finding with code location',
            severity=FindingSeverity.HIGH,
            confidence=Confidence(0.9),
            category='security',
            location=location
        )

        await repository.save(finding)

        retrieved = await repository.get_by_id('code-location-finding')
        assert retrieved is not None
        assert retrieved.location == location
        assert retrieved.location.start_line == 25
        assert retrieved.location.end_line == 35

    @pytest.mark.asyncio
    async def test_finding_with_recommendation(self, repository):
        """Test finding with recommendation."""
        finding = Finding(
            id='recommendation-finding',
            analysis_id='analysis-123',
            document_id='doc-456',
            title='Recommendation Finding',
            description='Finding with recommendation',
            severity=FindingSeverity.LOW,
            confidence=Confidence(0.7),
            category='style',
            recommendation='Consider using more descriptive variable names'
        )

        await repository.save(finding)

        retrieved = await repository.get_by_id('recommendation-finding')
        assert retrieved is not None
        assert retrieved.recommendation == 'Consider using more descriptive variable names'

    @pytest.mark.asyncio
    async def test_finding_with_metadata(self, repository):
        """Test finding with metadata."""
        metadata = {
            'rule_id': 'STYLE-001',
            'tags': ['style', 'naming'],
            'code_snippet': 'var x = 1;',
            'suggestion_confidence': 0.85,
            'automated_fix_available': True
        }

        finding = Finding(
            id='metadata-finding',
            analysis_id='analysis-123',
            document_id='doc-456',
            title='Metadata Finding',
            description='Finding with metadata',
            severity=FindingSeverity.INFO,
            confidence=Confidence(0.6),
            category='style',
            metadata=metadata
        )

        await repository.save(finding)

        retrieved = await repository.get_by_id('metadata-finding')
        assert retrieved is not None
        assert retrieved.metadata == metadata
        assert retrieved.metadata['rule_id'] == 'STYLE-001'
        assert retrieved.metadata['automated_fix_available'] is True


class TestSQLiteFindingRepository:
    """Test cases for SQLiteFindingRepository."""

    @pytest.fixture
    async def repository(self):
        """Create a fresh SQLite finding repository for each test."""
        repo = SQLiteFindingRepository(':memory:')
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding for testing."""
        return Finding(
            id='test-finding-123',
            analysis_id='analysis-456',
            document_id='doc-789',
            title='Test Finding',
            description='This is a test finding',
            severity=FindingSeverity.MEDIUM,
            confidence=Confidence(0.8),
            category='code_quality'
        )

    @pytest.mark.asyncio
    async def test_repository_creation(self, repository):
        """Test creating a SQLite finding repository."""
        assert repository is not None
        assert isinstance(repository, FindingRepository)
        assert isinstance(repository, SQLiteFindingRepository)
        assert repository.database_path == ':memory:'

    @pytest.mark.asyncio
    async def test_save_and_retrieve_finding_sqlite(self, repository, sample_finding):
        """Test saving and retrieving a finding with SQLite."""
        await repository.save(sample_finding)

        retrieved = await repository.get_by_id(sample_finding.id.value)

        assert retrieved is not None
        assert retrieved.id.value == sample_finding.id.value
        assert retrieved.analysis_id == sample_finding.analysis_id
        assert retrieved.document_id == sample_finding.document_id
        assert retrieved.severity == sample_finding.severity

    @pytest.mark.asyncio
    async def test_get_by_analysis_id_sqlite(self, repository):
        """Test getting findings by analysis ID with SQLite."""
        # Create findings for different analyses
        for i in range(3):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id=f'analysis-{i % 2}',  # 2 for analysis-0, 1 for analysis-1
                document_id='doc-123',
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        analysis_findings = await repository.get_by_analysis_id('analysis-0')
        assert len(analysis_findings) == 2
        for finding in analysis_findings:
            assert finding.analysis_id == 'analysis-0'

    @pytest.mark.asyncio
    async def test_get_by_document_id_sqlite(self, repository):
        """Test getting findings by document ID with SQLite."""
        # Create findings for different documents
        for i in range(3):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id='analysis-123',
                document_id=f'doc-{i % 2}',  # 2 for doc-0, 1 for doc-1
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        doc_findings = await repository.get_by_document_id('doc-0')
        assert len(doc_findings) == 2
        for finding in doc_findings:
            assert finding.document_id == 'doc-0'

    @pytest.mark.asyncio
    async def test_get_by_severity_sqlite(self, repository):
        """Test getting findings by severity with SQLite."""
        severities = [FindingSeverity.LOW, FindingSeverity.MEDIUM, FindingSeverity.HIGH]

        for i, severity in enumerate(severities):
            finding = Finding(
                id=f'finding-{i}',
                analysis_id='analysis-123',
                document_id='doc-456',
                title=f'Finding {i}',
                description=f'Description {i}',
                severity=severity,
                confidence=Confidence(0.8),
                category='test'
            )
            await repository.save(finding)

        high_findings = await repository.get_by_severity(FindingSeverity.HIGH)
        assert len(high_findings) == 1
        assert high_findings[0].severity == FindingSeverity.HIGH

    @pytest.mark.asyncio
    async def test_delete_finding_sqlite(self, repository, sample_finding):
        """Test deleting a finding with SQLite."""
        await repository.save(sample_finding)

        result = await repository.delete(sample_finding.id.value)
        assert result is True

        retrieved = await repository.get_by_id(sample_finding.id.value)
        assert retrieved is None


class TestFindingRepositoryIntegration:
    """Test integration between finding repository and other components."""

    @pytest.mark.asyncio
    async def test_finding_repository_with_analysis_repository(self):
        """Test finding repository integration with analysis repository."""
        from ...infrastructure.repositories.analysis_repository import InMemoryAnalysisRepository

        analysis_repo = InMemoryAnalysisRepository()
        finding_repo = InMemoryFindingRepository()

        # Create an analysis
        analysis = Analysis(
            id='integration-analysis',
            document_id='integration-doc',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.COMPLETED
        )
        await analysis_repo.save(analysis)

        # Create findings for the analysis
        findings = []
        for i in range(3):
            finding = Finding(
                id=f'integration-finding-{i}',
                analysis_id='integration-analysis',
                document_id='integration-doc',
                title=f'Integration Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM if i % 2 == 0 else FindingSeverity.HIGH,
                confidence=Confidence(0.7 + i * 0.1),
                category='integration_test'
            )
            await finding_repo.save(finding)
            findings.append(finding)

        # Verify the relationship
        analysis_findings = await finding_repo.get_by_analysis_id('integration-analysis')
        assert len(analysis_findings) == 3

        for finding in analysis_findings:
            assert finding.analysis_id == 'integration-analysis'
            assert finding.document_id == 'integration-doc'

    @pytest.mark.asyncio
    async def test_finding_repository_cross_document_analysis(self):
        """Test finding repository with cross-document analysis."""
        repo = InMemoryFindingRepository()

        # Simulate findings from cross-document analysis
        documents = ['doc-1', 'doc-2', 'doc-3']
        severities = [FindingSeverity.LOW, FindingSeverity.MEDIUM, FindingSeverity.HIGH]

        findings = []
        for i, doc_id in enumerate(documents):
            for j, severity in enumerate(severities):
                finding = Finding(
                    id=f'cross-finding-{i}-{j}',
                    analysis_id='cross-analysis',
                    document_id=doc_id,
                    title=f'Cross-document finding {i}-{j}',
                    description=f'Finding in document {doc_id}',
                    severity=severity,
                    confidence=Confidence(0.6 + j * 0.2),
                    category='cross_document_analysis'
                )
                await repo.save(finding)
                findings.append(finding)

        # Verify cross-document queries work
        all_findings = await repo.get_all()
        assert len(all_findings) == 9  # 3 documents * 3 severities

        # Verify document-specific queries
        for doc_id in documents:
            doc_findings = await repo.get_by_document_id(doc_id)
            assert len(doc_findings) == 3  # 3 findings per document

        # Verify severity queries
        high_findings = await repo.get_by_severity(FindingSeverity.HIGH)
        assert len(high_findings) == 3  # 1 high finding per document

    @pytest.mark.asyncio
    async def test_finding_repository_bulk_operations(self):
        """Test bulk operations on finding repository."""
        repo = InMemoryFindingRepository()

        # Create multiple findings
        findings = []
        for i in range(100):
            finding = Finding(
                id=f'bulk-finding-{i:03d}',
                analysis_id='bulk-analysis',
                document_id='bulk-doc',
                title=f'Bulk Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.LOW if i % 3 == 0 else FindingSeverity.MEDIUM if i % 3 == 1 else FindingSeverity.HIGH,
                confidence=Confidence(0.5 + (i % 50) * 0.01),
                category='bulk_test'
            )
            findings.append(finding)
            await repo.save(finding)

        # Verify bulk save
        all_findings = await repo.get_all()
        assert len(all_findings) == 100

        # Test bulk queries
        analysis_findings = await repo.get_by_analysis_id('bulk-analysis')
        assert len(analysis_findings) == 100

        doc_findings = await repo.get_by_document_id('bulk-doc')
        assert len(doc_findings) == 100

        # Test severity distribution
        low_findings = await repo.get_by_severity(FindingSeverity.LOW)
        medium_findings = await repo.get_by_severity(FindingSeverity.MEDIUM)
        high_findings = await repo.get_by_severity(FindingSeverity.HIGH)

        # Should be roughly equal distribution (33-34 each)
        assert 30 <= len(low_findings) <= 40
        assert 30 <= len(medium_findings) <= 40
        assert 30 <= len(high_findings) <= 40

    @pytest.mark.asyncio
    async def test_finding_repository_with_complex_locations(self):
        """Test finding repository with complex location data."""
        repo = InMemoryFindingRepository()

        # Create findings with various location types
        locations = [
            FileLocation('/src/main.py', 42),
            CodeLocation('/src/utils.py', 10, 15, 5, 20),
            FileLocation('/tests/test_main.py', 123),
            CodeLocation('/src/parser.py', 25, 35, 10, 25)
        ]

        findings = []
        for i, location in enumerate(locations):
            finding = Finding(
                id=f'location-finding-{i}',
                analysis_id='location-analysis',
                document_id='location-doc',
                title=f'Location Finding {i}',
                description=f'Finding at location {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='location_test',
                location=location
            )
            await repo.save(finding)
            findings.append(finding)

        # Verify all findings were saved with correct locations
        all_findings = await repo.get_all()
        assert len(all_findings) == 4

        for i, finding in enumerate(all_findings):
            assert finding.location == locations[i]


class TestFindingRepositoryErrorHandling:
    """Test error handling in finding repository."""

    @pytest.mark.asyncio
    async def test_sqlite_repository_invalid_path(self):
        """Test SQLite repository with invalid database path."""
        with pytest.raises(Exception):
            repo = SQLiteFindingRepository('/invalid/path/database.db')
            await repo.initialize()

    @pytest.mark.asyncio
    async def test_repository_invalid_finding_data(self):
        """Test repository handling of invalid finding data."""
        repo = InMemoryFindingRepository()

        # Try to save finding with invalid data
        try:
            invalid_finding = Finding(
                id='',  # Invalid empty ID
                analysis_id='analysis-123',
                document_id='doc-456',
                title='Invalid Finding',
                description='Description',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='test'
            )
            await repo.save(invalid_finding)
        except ValueError:
            # Expected for invalid data
            pass

    @pytest.mark.asyncio
    async def test_repository_concurrent_finding_operations(self):
        """Test concurrent finding operations."""
        repo = InMemoryFindingRepository()

        async def create_and_save_finding(i: int):
            finding = Finding(
                id=f'concurrent-finding-{i}',
                analysis_id='concurrent-analysis',
                document_id='concurrent-doc',
                title=f'Concurrent Finding {i}',
                description=f'Description {i}',
                severity=FindingSeverity.MEDIUM,
                confidence=Confidence(0.8),
                category='concurrent_test'
            )
            await repo.save(finding)
            return finding

        # Create concurrent operations
        tasks = [create_and_save_finding(i) for i in range(25)]
        results = await asyncio.gather(*tasks)

        # Verify all findings were created
        assert len(results) == 25

        all_findings = await repo.get_all()
        assert len(all_findings) == 25

        # Verify no duplicates
        finding_ids = [f.id.value for f in all_findings]
        assert len(set(finding_ids)) == 25


class TestFindingRepositoryEdgeCases:
    """Test finding repository edge cases."""

    @pytest.mark.asyncio
    async def test_empty_finding_repository(self):
        """Test operations on empty finding repository."""
        repo = InMemoryFindingRepository()

        # Operations on empty repository
        all_findings = await repo.get_all()
        assert len(all_findings) == 0

        retrieved = await repo.get_by_id('non-existent')
        assert retrieved is None

        analysis_findings = await repo.get_by_analysis_id('non-existent-analysis')
        assert len(analysis_findings) == 0

        doc_findings = await repo.get_by_document_id('non-existent-doc')
        assert len(doc_findings) == 0

        severity_findings = await repo.get_by_severity(FindingSeverity.CRITICAL)
        assert len(severity_findings) == 0

        delete_result = await repo.delete('non-existent')
        assert delete_result is False

    @pytest.mark.asyncio
    async def test_finding_repository_special_characters(self):
        """Test repository with special characters."""
        repo = InMemoryFindingRepository()

        # Create finding with special characters
        special_finding = Finding(
            id='special-finding-🚨',
            analysis_id='analysis-ñáéíóú',
            document_id='doc-🚀',
            title='Finding with ñáéíóú 🚀 📚 💻',
            description='Description with @#$%^&*()[]{}',
            severity=FindingSeverity.HIGH,
            confidence=Confidence(0.9),
            category='special_chars',
            recommendation='Fix this issue: 🚨 → ✅'
        )

        await repo.save(special_finding)

        retrieved = await repo.get_by_id('special-finding-🚨')
        assert retrieved is not None
        assert '🚨' in retrieved.id.value
        assert 'ñáéíóú' in retrieved.analysis_id
        assert '🚀' in retrieved.title
        assert retrieved.recommendation == 'Fix this issue: 🚨 → ✅'

    @pytest.mark.asyncio
    async def test_finding_repository_large_metadata(self):
        """Test repository with large metadata."""
        repo = InMemoryFindingRepository()

        # Create finding with large metadata
        large_metadata = {
            'rule_id': 'COMPLEX-001',
            'tags': [f'tag-{i}' for i in range(100)],  # 100 tags
            'code_snippet': 'x' * 5000,  # 5KB code snippet
            'related_findings': [f'finding-{i}' for i in range(200)],  # 200 related findings
            'analysis_context': {
                'file_dependencies': [f'/src/dep-{i}.py' for i in range(50)],
                'function_calls': [{'name': f'func-{i}', 'line': i*10} for i in range(100)],
                'variable_usage': {f'var-{i}': [f'usage-{j}' for j in range(20)] for i in range(30)}
            },
            'performance_impact': {
                'complexity_increase': 25.5,
                'memory_overhead': 1024.0,
                'execution_time_impact': 0.15
            }
        }

        finding = Finding(
            id='large-metadata-finding',
            analysis_id='large-analysis',
            document_id='large-doc',
            title='Finding with Large Metadata',
            description='This finding has extensive metadata',
            severity=FindingSeverity.MEDIUM,
            confidence=Confidence(0.85),
            category='complex_analysis',
            metadata=large_metadata
        )

        await repo.save(finding)

        retrieved = await repo.get_by_id('large-metadata-finding')
        assert retrieved is not None
        assert len(retrieved.metadata['tags']) == 100
        assert len(retrieved.metadata['code_snippet']) == 5000
        assert retrieved.metadata['performance_impact']['complexity_increase'] == 25.5

    @pytest.mark.asyncio
    async def test_finding_repository_null_empty_values(self):
        """Test repository handling of null and empty values."""
        repo = InMemoryFindingRepository()

        # Create finding with empty values where allowed
        finding = Finding(
            id='empty-finding',
            analysis_id='empty-analysis',
            document_id='empty-doc',
            title='Empty Finding',
            description='',  # Empty description
            severity=FindingSeverity.INFO,
            confidence=Confidence(0.5),
            category='',  # Empty category
            recommendation=''  # Empty recommendation
        )

        await repo.save(finding)

        retrieved = await repo.get_by_id('empty-finding')
        assert retrieved is not None
        assert retrieved.description == ''
        assert retrieved.category == ''
        assert retrieved.recommendation == ''

    @pytest.mark.asyncio
    async def test_finding_repository_extreme_confidence_values(self):
        """Test repository with extreme confidence values."""
        repo = InMemoryFindingRepository()

        # Test very low confidence
        low_conf_finding = Finding(
            id='low-confidence-finding',
            analysis_id='analysis-123',
            document_id='doc-456',
            title='Low Confidence Finding',
            description='Very uncertain finding',
            severity=FindingSeverity.INFO,
            confidence=Confidence(0.01),  # Very low confidence
            category='uncertain'
        )

        # Test very high confidence
        high_conf_finding = Finding(
            id='high-confidence-finding',
            analysis_id='analysis-123',
            document_id='doc-456',
            title='High Confidence Finding',
            description='Very certain finding',
            severity=FindingSeverity.CRITICAL,
            confidence=Confidence(0.99),  # Very high confidence
            category='certain'
        )

        await repo.save(low_conf_finding)
        await repo.save(high_conf_finding)

        # Verify both were saved correctly
        low_retrieved = await repo.get_by_id('low-confidence-finding')
        high_retrieved = await repo.get_by_id('high-confidence-finding')

        assert low_retrieved.confidence.value == 0.01
        assert high_retrieved.confidence.value == 0.99
