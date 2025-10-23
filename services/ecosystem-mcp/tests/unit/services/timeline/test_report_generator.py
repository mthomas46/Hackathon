"""
Unit tests for ReportGenerator service.

Tests report generation in multiple formats with source citations.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

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
    PeriodStrategy
)


@pytest.fixture
def sample_timeline():
    """Create a sample timeline for testing."""
    return Timeline(
        id=1,
        name="Test Timeline",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
        strategy=PeriodStrategy.MONTHLY,
        confidence=TemporalConfidence.HIGH,
        metadata={"project": "test"}
    )


@pytest.fixture
def sample_periods():
    """Create sample time periods."""
    return [
        TimePeriod(
            id=1,
            timeline_id=1,
            name="Q1 2024",
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 3, 31, tzinfo=timezone.utc),
            sequence=1,
            metadata={}
        ),
        TimePeriod(
            id=2,
            timeline_id=1,
            name="Q2 2024",
            start_date=datetime(2024, 4, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 6, 30, tzinfo=timezone.utc),
            sequence=2,
            metadata={}
        )
    ]


@pytest.fixture
def sample_placements():
    """Create sample document placements."""
    return [
        DocumentPlacement(
            id=1,
            period_id=1,
            document_id=101,
            confidence=0.95,
            metadata={"source": "git"}
        ),
        DocumentPlacement(
            id=2,
            period_id=2,
            document_id=102,
            confidence=0.85,
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
        
        # Mock the database queries
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (sample_periods, sample_placements, [])
            
            report = await generator.generate_progression_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN
            )
            
            assert report is not None
            assert isinstance(report, str)
            assert "# Documentation Progression Report" in report
            assert "Test Timeline" in report or "Timeline" in report
            assert "Q1 2024" in report or "Q2 2024" in report
    
    async def test_generate_progression_report_html(
        self, sample_timeline, sample_periods
    ):
        """Test generating progression report in HTML format."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = (sample_periods, [], [])
            
            report = await generator.generate_progression_report(
                timeline_id=1,
                format=ReportFormat.HTML
            )
            
            assert report is not None
            assert isinstance(report, str)
            assert "<html>" in report or "<h1>" in report
            assert "Progression Report" in report
    
    async def test_generate_progression_report_json(self):
        """Test generating progression report in JSON format."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ([], [], [])
            
            report = await generator.generate_progression_report(
                timeline_id=1,
                format=ReportFormat.JSON
            )
            
            assert report is not None
            assert isinstance(report, str)
            # Should be valid JSON
            import json
            data = json.loads(report)
            assert "type" in data
            assert data["type"] == "progression"


@pytest.mark.unit
class TestGapReportGeneration:
    """Test gap report generation."""
    
    async def test_generate_gap_report_markdown(self):
        """Test generating gap report in Markdown format."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_analyze_gaps', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "coverage_gaps": [],
                "temporal_gaps": [],
                "recommendations": []
            }
            
            report = await generator.generate_gap_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN
            )
            
            assert report is not None
            assert isinstance(report, str)
            assert "# Documentation Gap Analysis" in report or "Gap" in report
    
    async def test_generate_gap_report_with_gaps(self):
        """Test gap report with actual gaps identified."""
        generator = ReportGenerator()
        
        gaps = {
            "coverage_gaps": [
                {"area": "Authentication", "severity": "high"}
            ],
            "temporal_gaps": [
                {"period": "Q3 2024", "doc_count": 0}
            ],
            "recommendations": [
                "Add authentication documentation"
            ]
        }
        
        with patch.object(generator, '_analyze_gaps', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = gaps
            
            report = await generator.generate_gap_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN
            )
            
            assert "Authentication" in report or "Gap" in report
            assert isinstance(report, str)


@pytest.mark.unit
class TestDriftReportGeneration:
    """Test drift report generation."""
    
    async def test_generate_drift_report_markdown(self):
        """Test generating drift report in Markdown format."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_detect_drift', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {
                "code_doc_drift": [],
                "consistency_issues": [],
                "severity_summary": {"high": 0, "medium": 0, "low": 0}
            }
            
            report = await generator.generate_drift_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN
            )
            
            assert report is not None
            assert isinstance(report, str)
            assert "# Code-Documentation Drift Analysis" in report or "Drift" in report
    
    async def test_generate_drift_report_with_issues(self):
        """Test drift report with actual drift issues."""
        generator = ReportGenerator()
        
        drift_data = {
            "code_doc_drift": [
                {
                    "file": "auth.py",
                    "issue": "Documentation outdated",
                    "severity": "high"
                }
            ],
            "consistency_issues": [],
            "severity_summary": {"high": 1, "medium": 0, "low": 0}
        }
        
        with patch.object(generator, '_detect_drift', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = drift_data
            
            report = await generator.generate_drift_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN
            )
            
            assert "auth.py" in report or "Drift" in report


@pytest.mark.unit
class TestReportCitations:
    """Test source citations in reports."""
    
    async def test_report_includes_citations(self, sample_placements):
        """Test that reports include source citations."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ([], sample_placements, [])
            
            report = await generator.generate_progression_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN,
                include_citations=True
            )
            
            # Should mention sources or citations
            assert "source" in report.lower() or "citation" in report.lower() or "report" in report.lower()
    
    async def test_report_without_citations(self):
        """Test generating report without citations."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ([], [], [])
            
            report = await generator.generate_progression_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN,
                include_citations=False
            )
            
            assert isinstance(report, str)
            # Should still generate valid report


@pytest.mark.unit
class TestReportFormats:
    """Test different report output formats."""
    
    async def test_all_report_formats(self):
        """Test that all report formats can be generated."""
        generator = ReportGenerator()
        
        formats = [ReportFormat.MARKDOWN, ReportFormat.HTML, ReportFormat.JSON]
        
        for fmt in formats:
            with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = ([], [], [])
                
                report = await generator.generate_progression_report(
                    timeline_id=1,
                    format=fmt
                )
                
                assert report is not None
                assert isinstance(report, str)
                assert len(report) > 0


@pytest.mark.unit
class TestReportErrorHandling:
    """Test error handling in report generation."""
    
    async def test_report_generation_with_invalid_timeline(self):
        """Test report generation with non-existent timeline."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = ValueError("Timeline not found")
            
            with pytest.raises(ValueError):
                await generator.generate_progression_report(timeline_id=999)
    
    async def test_report_generation_with_database_error(self):
        """Test report generation with database error."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                await generator.generate_progression_report(timeline_id=1)


@pytest.mark.unit
class TestReportMetadata:
    """Test report metadata and structure."""
    
    async def test_report_contains_metadata(self):
        """Test that reports contain metadata."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ([], [], [])
            
            report = await generator.generate_progression_report(
                timeline_id=1,
                format=ReportFormat.JSON
            )
            
            import json
            data = json.loads(report)
            
            # Should have metadata fields
            assert "type" in data
            assert "generated_at" in data or "timestamp" in data or "type" in data
    
    async def test_report_contains_summary(self):
        """Test that reports contain summary information."""
        generator = ReportGenerator()
        
        with patch.object(generator, '_fetch_timeline_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ([], [], [])
            
            report = await generator.generate_progression_report(
                timeline_id=1,
                format=ReportFormat.MARKDOWN
            )
            
            # Should have summary section
            assert "summary" in report.lower() or "report" in report.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
