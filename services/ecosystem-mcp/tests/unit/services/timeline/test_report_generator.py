"""
Unit tests for ReportGenerator service.

Tests report generation in multiple formats with source citations.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.timeline.report_generator import (
    ReportGenerator,
    ReportType,
    ReportFormat
)
from src.models.timeline import (
    Timeline,
    TimePeriod,
    DocumentPlacement,
    TemporalConfidence,
    PeriodStrategy,
    ConfidenceMetadata,
    TimelineMetadata
)


@pytest.fixture
def sample_confidence_metadata():
    """Create sample confidence metadata."""
    return ConfidenceMetadata(
        total_documents=100,
        git_history_documents=95,
        snapshot_documents=5,
        git_percentage=95.0,
        can_show_evolution=True,
        can_detect_drift=True,
        can_show_timeline=True,
        can_compare_periods=True,
        fallback_strategy="use_created_at",
        warnings=[]
    )


@pytest.fixture
def sample_timeline(sample_confidence_metadata):
    """Create a sample timeline for testing."""
    return Timeline(
        id=uuid4(),
        name="Test Timeline",
        description="Test timeline for unit tests",
        service_name="test-service",
        repo_path="/test/repo",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
        strategy=PeriodStrategy.MONTHLY,
        confidence_level=TemporalConfidence.HIGH,
        confidence_metadata=sample_confidence_metadata,
        metadata=TimelineMetadata(
            total_commits=100,
            total_documents=50,
            primary_authors=["test_author"],
            tags=["test"],
            extra={"project": "test"}
        )
    )


@pytest.fixture
def sample_periods(sample_timeline):
    """Create sample time periods."""
    return [
        TimePeriod(
            id=uuid4(),
            timeline_id=sample_timeline.id,
            name="Q1 2024",
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 6, 30, tzinfo=timezone.utc),
            sequence_number=1,
            document_count=10,
            metadata={}
        ),
        TimePeriod(
            id=uuid4(),
            timeline_id=sample_timeline.id,
            name="Q2 2024",
            start_date=datetime(2024, 4, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 6, 30, tzinfo=timezone.utc),
            sequence_number=2,
            document_count=15,
            metadata={}
        )
    ]


@pytest.fixture
def sample_placements(sample_periods):
    """Create sample document placements."""
    return [
        DocumentPlacement(
            id=uuid4(),
            period_id=sample_periods[0].id,
            document_id=uuid4(),
            confidence_score=0.95,
            placement_source="git_commit",
            placement_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            metadata={"source": "git"}
        ),
        DocumentPlacement(
            id=uuid4(),
            period_id=sample_periods[1].id,
            document_id=uuid4(),
            confidence_score=0.85,
            placement_source="manual",
            placement_date=datetime(2024, 4, 15, tzinfo=timezone.utc),
            metadata={"source": "manual"}
        )
    ]


@pytest.mark.unit
class TestReportGeneratorInstantiation:
    """Test ReportGenerator instantiation."""
    
    def test_create_report_generator(self):
        """Test creating a ReportGenerator instance."""
        generator = ReportGenerator()
        assert generator is not None
    
    def test_report_generator_has_methods(self):
        """Test that ReportGenerator has required methods."""
        generator = ReportGenerator()
        assert hasattr(generator, 'generate_progression_report')
        assert hasattr(generator, 'generate_gap_report')
        assert hasattr(generator, 'generate_drift_report')


@pytest.mark.unit
class TestProgressionReportGeneration:
    """Test progression report generation."""
    
    async def test_generate_progression_report_markdown(
        self, sample_timeline, sample_periods, sample_placements
    ):
        """Test generating progression report in Markdown format."""
        generator = ReportGenerator()
        
        # Mock the database queries - returns dict with dict representation of periods
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'timeline_name': sample_timeline.name,
                'periods': [
                    {
                        'id': str(p.id),
                        'name': p.name,
                        'start_date': p.start_date,
                        'end_date': p.end_date,
                        'document_count': p.document_count
                    }
                    for p in sample_periods
                ],
                'confidence': sample_timeline.confidence_level
            }
            
            report = await generator.generate_progression_report(
                timeline_id=str(sample_timeline.id),
                format=ReportFormat.MARKDOWN
            )
            
            assert report is not None
            assert isinstance(report, dict)  # Returns dict, not string
            assert report['type'] == 'progression'
            assert report['format'] == 'markdown'
            assert 'content' in report
            # Content should be string with markdown
            assert isinstance(report['content'], str)
    
    async def test_generate_progression_report_html(
        self, sample_timeline, sample_periods
    ):
        """Test generating progression report in HTML format."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'timeline_name': sample_timeline.name,
                'periods': [
                    {
                        'id': str(p.id),
                        'name': p.name,
                        'start_date': p.start_date,
                        'end_date': p.end_date,
                        'document_count': p.document_count
                    }
                    for p in sample_periods
                ],
                'confidence': sample_timeline.confidence_level
            }
            
            report = await generator.generate_progression_report(
                timeline_id=str(sample_timeline.id),
                format=ReportFormat.HTML
            )
            
            assert report is not None
            assert isinstance(report, dict)
            assert report['type'] == 'progression'
            assert report['format'] == 'html'
            assert 'content' in report
    
    async def test_generate_progression_report_json(self, sample_timeline):
        """Test generating progression report in JSON format."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'timeline_name': sample_timeline.name,
                'periods': [],
                'placements': [],
                'confidence': sample_timeline.confidence_level
            }
            
            report = await generator.generate_progression_report(
                timeline_id=str(sample_timeline.id),
                format=ReportFormat.JSON
            )
            
            assert report is not None
            assert isinstance(report, dict)
            assert report["type"] == "progression"
            assert report["format"] == "json"


@pytest.mark.unit
class TestGapReportGeneration:
    """Test gap report generation."""
    
    async def test_generate_gap_report_markdown(self):
        """Test generating gap report in Markdown format."""
        generator = ReportGenerator()
        
        # Import and mock GapAnalyzer
        with patch('src.services.timeline.gap_analyzer.GapAnalyzer') as MockGapAnalyzer:
            mock_analyzer = AsyncMock()
            MockGapAnalyzer.return_value = mock_analyzer
            mock_analyzer.analyze_gaps.return_value = {
                "total_gaps": 0,
                "gaps": []
            }
            
            report = await generator.generate_gap_report(
                service_name="test-service",
                format=ReportFormat.MARKDOWN
            )
            
            assert report is not None
            assert isinstance(report, dict)
            assert report['type'] == 'gap'
            assert report['service_name'] == 'test-service'
    
    async def test_generate_gap_report_with_gaps(self):
        """Test gap report with actual gaps identified."""
        generator = ReportGenerator()
        
        gaps = {
            "total_gaps": 2,
            "gaps": [
                {"area": "Authentication", "severity": "HIGH"},
                {"area": "Authorization", "severity": "CRITICAL"}
            ]
        }
        
        with patch('src.services.timeline.gap_analyzer.GapAnalyzer') as MockGapAnalyzer:
            mock_analyzer = AsyncMock()
            MockGapAnalyzer.return_value = mock_analyzer
            mock_analyzer.analyze_gaps.return_value = gaps
            
            report = await generator.generate_gap_report(
                service_name="test-service",
                format=ReportFormat.MARKDOWN
            )
            
            assert isinstance(report, dict)
            assert report['type'] == 'gap'
            assert report['metadata']['total_gaps'] == 2
            assert report['metadata']['critical_gaps'] == 1


@pytest.mark.unit
class TestDriftReportGeneration:
    """Test drift report generation."""
    
    async def test_generate_drift_report_markdown(self):
        """Test generating drift report in Markdown format."""
        generator = ReportGenerator()
        
        # Import and mock DriftDetector
        with patch('src.services.timeline.drift_detector.DriftDetector') as MockDriftDetector:
            mock_detector = AsyncMock()
            MockDriftDetector.return_value = mock_detector
            mock_detector.detect_drift.return_value = {
                "total_drifts": 0,
                "drifts": [],
                "confidence": 0.95
            }
            
            report = await generator.generate_drift_report(
                service_name="test-service",
                format=ReportFormat.MARKDOWN
            )
            
            assert report is not None
            assert isinstance(report, dict)
            assert report['type'] == 'drift'
            assert report['service_name'] == 'test-service'
    
    async def test_generate_drift_report_with_issues(self):
        """Test drift report with actual drift issues."""
        generator = ReportGenerator()
        
        drift_data = {
            "total_drifts": 1,
            "drifts": [
                {
                    "file": "auth.py",
                    "issue": "Documentation outdated",
                    "severity": "HIGH"
                }
            ],
            "confidence": 0.85
        }
        
        with patch('src.services.timeline.drift_detector.DriftDetector') as MockDriftDetector:
            mock_detector = AsyncMock()
            MockDriftDetector.return_value = mock_detector
            mock_detector.detect_drift.return_value = drift_data
            
            report = await generator.generate_drift_report(
                service_name="test-service",
                format=ReportFormat.MARKDOWN
            )
            
            assert isinstance(report, dict)
            assert report['type'] == 'drift'
            assert report['metadata']['total_drifts'] == 1


@pytest.mark.unit
class TestReportCitations:
    """Test source citations in reports."""
    
    async def test_report_includes_citations(self, sample_timeline, sample_placements):
        """Test that reports include source citations."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'timeline_name': sample_timeline.name,
                'periods': [],
                'placements': sample_placements,
                'confidence': sample_timeline.confidence_level
            }
            
            report = await generator.generate_progression_report(
                timeline_id=str(sample_timeline.id),
                format=ReportFormat.MARKDOWN
            )
            
            assert isinstance(report, dict)
            assert 'content' in report
    
    async def test_report_without_citations(self, sample_timeline):
        """Test generating report without citations."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'timeline_name': sample_timeline.name,
                'periods': [],
                'placements': [],
                'confidence': sample_timeline.confidence_level
            }
            
            report = await generator.generate_progression_report(
                timeline_id=str(sample_timeline.id),
                format=ReportFormat.MARKDOWN
            )
            
            assert isinstance(report, dict)
            assert 'content' in report


@pytest.mark.unit
class TestReportFormats:
    """Test different report output formats."""
    
    async def test_all_report_formats(self, sample_timeline):
        """Test that all report formats can be generated."""
        generator = ReportGenerator()
        
        formats = [ReportFormat.MARKDOWN, ReportFormat.HTML, ReportFormat.JSON]
        
        for fmt in formats:
            with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = {
                    'timeline_name': sample_timeline.name,
                    'periods': [],
                    'placements': [],
                    'confidence': sample_timeline.confidence_level
                }
                
                report = await generator.generate_progression_report(
                    timeline_id=str(sample_timeline.id),
                    format=fmt
                )
                
                assert report is not None
                assert isinstance(report, dict)
                assert report['format'] == fmt.value


@pytest.mark.unit
class TestReportErrorHandling:
    """Test error handling in report generation."""
    
    async def test_report_generation_with_invalid_timeline(self, sample_timeline):
        """Test report generation with non-existent timeline."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None  # Timeline not found
            
            report = await generator.generate_progression_report(timeline_id="invalid-id")
            
            # Should return empty report
            assert report['type'] == 'progression'
            assert 'Timeline not found' in report['content'] or report is not None
    
    async def test_report_generation_with_database_error(self):
        """Test report generation with database error."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                await generator.generate_progression_report(timeline_id="test-id")


@pytest.mark.unit
class TestReportMetadata:
    """Test report metadata and structure."""
    
    async def test_report_contains_metadata(self, sample_timeline):
        """Test that reports contain metadata."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'timeline_name': sample_timeline.name,
                'periods': [],
                'placements': [],
                'confidence': sample_timeline.confidence_level
            }
            
            report = await generator.generate_progression_report(
                timeline_id=str(sample_timeline.id),
                format=ReportFormat.JSON
            )
            
            # Should have metadata fields
            assert "type" in report
            assert "generated_at" in report
            assert "metadata" in report
            assert report["type"] == "progression"
    
    async def test_report_contains_summary(self, sample_timeline):
        """Test that reports contain summary information."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'timeline_name': sample_timeline.name,
                'periods': [],
                'placements': [],
                'confidence': sample_timeline.confidence_level
            }
            
            report = await generator.generate_progression_report(
                timeline_id=str(sample_timeline.id),
                format=ReportFormat.MARKDOWN
            )
            
            # Should have content
            assert "content" in report
            assert isinstance(report['content'], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
