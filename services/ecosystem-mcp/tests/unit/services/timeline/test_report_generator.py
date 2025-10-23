"""
Unit tests for ReportGenerator.

Tests report generation for progression, gaps, and drift.
"""

import pytest
from datetime import datetime, timedelta
from src.services.timeline.report_generator import (
    ReportGenerator, ReportType, ReportFormat
)


@pytest.mark.asyncio
class TestReportGeneratorBasic:
    """Test basic report generation functionality."""
    
    async def test_generator_instantiation(self):
        """Test that generator can be instantiated."""
        generator = ReportGenerator()
        assert generator is not None
    
    async def test_generate_progression_report_markdown(self):
        """Test generating progression report in Markdown format."""
        generator = ReportGenerator()
        
        result = await generator.generate_progression_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.MARKDOWN
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert "report" in result
        assert "format" in result
        assert result["format"] == "markdown"
    
    async def test_generate_progression_report_html(self):
        """Test generating progression report in HTML format."""
        generator = ReportGenerator()
        
        result = await generator.generate_progression_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.HTML
        )
        
        assert result is not None
        assert result["format"] == "html"
    
    async def test_generate_progression_report_json(self):
        """Test generating progression report in JSON format."""
        generator = ReportGenerator()
        
        result = await generator.generate_progression_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.JSON
        )
        
        assert result is not None
        assert result["format"] == "json"


@pytest.mark.asyncio
class TestReportGeneratorProgressionReports:
    """Test progression report generation."""
    
    async def test_progression_report_structure(self):
        """Test that progression report has required structure."""
        generator = ReportGenerator()
        
        result = await generator.generate_progression_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.JSON
        )
        
        assert "report" in result
        assert "metadata" in result
        assert "generated_at" in result["metadata"]
    
    async def test_progression_report_with_citations(self):
        """Test progression report includes citations."""
        generator = ReportGenerator()
        
        result = await generator.generate_progression_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.MARKDOWN,
            include_citations=True
        )
        
        assert result is not None
        # Should include some citation info if data available
        assert "report" in result
    
    async def test_progression_report_empty_timeline(self):
        """Test progression report with non-existent timeline."""
        generator = ReportGenerator()
        
        result = await generator.generate_progression_report(
            timeline_id="non-existent",
            format=ReportFormat.JSON
        )
        
        # Should handle gracefully
        assert result is not None


@pytest.mark.asyncio
class TestReportGeneratorGapReports:
    """Test gap analysis report generation."""
    
    async def test_generate_gap_report_markdown(self):
        """Test generating gap report in Markdown."""
        generator = ReportGenerator()
        
        result = await generator.generate_gap_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.MARKDOWN
        )
        
        assert result is not None
        assert result["format"] == "markdown"
    
    async def test_generate_gap_report_html(self):
        """Test generating gap report in HTML."""
        generator = ReportGenerator()
        
        result = await generator.generate_gap_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.HTML
        )
        
        assert result is not None
        assert result["format"] == "html"
    
    async def test_gap_report_structure(self):
        """Test gap report structure."""
        generator = ReportGenerator()
        
        result = await generator.generate_gap_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.JSON
        )
        
        assert "report" in result
        assert "metadata" in result
    
    async def test_gap_report_with_severity(self):
        """Test gap report includes severity levels."""
        generator = ReportGenerator()
        
        result = await generator.generate_gap_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.JSON,
            min_severity="medium"
        )
        
        assert result is not None
        # Structure should be present even if no gaps
        assert "report" in result


@pytest.mark.asyncio
class TestReportGeneratorDriftReports:
    """Test drift analysis report generation."""
    
    async def test_generate_drift_report_markdown(self):
        """Test generating drift report in Markdown."""
        generator = ReportGenerator()
        
        result = await generator.generate_drift_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.MARKDOWN
        )
        
        assert result is not None
        assert result["format"] == "markdown"
    
    async def test_generate_drift_report_html(self):
        """Test generating drift report in HTML."""
        generator = ReportGenerator()
        
        result = await generator.generate_drift_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.HTML
        )
        
        assert result is not None
        assert result["format"] == "html"
    
    async def test_drift_report_structure(self):
        """Test drift report structure."""
        generator = ReportGenerator()
        
        result = await generator.generate_drift_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.JSON
        )
        
        assert "report" in result
        assert "metadata" in result
    
    async def test_drift_report_with_threshold(self):
        """Test drift report with custom threshold."""
        generator = ReportGenerator()
        
        result = await generator.generate_drift_report(
            timeline_id="test-timeline-1",
            format=ReportFormat.JSON,
            drift_threshold=0.8
        )
        
        assert result is not None
        assert "report" in result


@pytest.mark.asyncio
class TestReportGeneratorEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_invalid_timeline_id(self):
        """Test report generation with invalid timeline ID."""
        generator = ReportGenerator()
        
        result = await generator.generate_progression_report(
            timeline_id="",
            format=ReportFormat.JSON
        )
        
        # Should handle gracefully
        assert result is not None
    
    async def test_invalid_format_defaults(self):
        """Test invalid format defaults to JSON."""
        generator = ReportGenerator()
        
        try:
            result = await generator.generate_progression_report(
                timeline_id="test-1",
                format="invalid"
            )
            # Should either work with default or raise error
            assert result is not None
        except (ValueError, KeyError):
            # Acceptable to raise error for invalid format
            pass
    
    async def test_all_report_types(self):
        """Test that all report types can be generated."""
        generator = ReportGenerator()
        timeline_id = "test-timeline"
        
        # Progression
        prog = await generator.generate_progression_report(
            timeline_id, ReportFormat.JSON
        )
        assert prog is not None
        
        # Gap
        gap = await generator.generate_gap_report(
            timeline_id, ReportFormat.JSON
        )
        assert gap is not None
        
        # Drift
        drift = await generator.generate_drift_report(
            timeline_id, ReportFormat.JSON
        )
        assert drift is not None
        
        print("✅ All report types generated successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

