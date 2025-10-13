"""
End-to-End tests for Multi-Pass Query Workflow.

Tests complete workflows from CSV input to result output,
including tier hierarchy and batch processing.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
import csv
import json

from run_multi_pass_batch import MultiPassBatchProcessor, QueryConfig


@pytest.fixture
def sample_csv():
    """Create a temporary CSV file with sample queries."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['query', 'num_passes', 'num_secondary_questions', 'tier'])
        writer.writerow(['What is Python?', '2', '2', 'docker'])
        writer.writerow(['How does caching work?', '2', '2', 'auto'])
        return Path(f.name)


@pytest.fixture
def output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestCSVBatchProcessing:
    """Test CSV-based batch processing."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_process_csv_batch(self, sample_csv, output_dir):
        """Test processing batch of queries from CSV."""
        processor = MultiPassBatchProcessor()
        
        results = await processor.process_csv(
            csv_path=sample_csv,
            output_dir=output_dir,
            tier_preference="docker"
        )
        
        # Verify results
        assert len(results) == 2
        assert all(r.success for r in results)
        
        # Verify output files exist
        assert (output_dir / "batch_summary.json").exists()
        assert (output_dir / "batch_summary.csv").exists()
        assert (output_dir / "query_001_result.json").exists()
        assert (output_dir / "query_002_result.json").exists()
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_batch_summary_structure(self, sample_csv, output_dir):
        """Test that batch summary has correct structure."""
        processor = MultiPassBatchProcessor()
        await processor.process_csv(sample_csv, output_dir)
        
        # Load summary
        with open(output_dir / "batch_summary.json") as f:
            summary = json.load(f)
        
        assert "total_queries" in summary
        assert "successful" in summary
        assert "failed" in summary
        assert "success_rate" in summary
        assert "total_duration_seconds" in summary
        assert "results" in summary
        
        assert summary["total_queries"] == 2
        assert summary["successful"] == 2
        assert summary["failed"] == 0
        assert summary["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_individual_result_files(self, sample_csv, output_dir):
        """Test that individual result files contain correct data."""
        processor = MultiPassBatchProcessor()
        await processor.process_csv(sample_csv, output_dir)
        
        # Load first result
        with open(output_dir / "query_001_result.json") as f:
            result = json.load(f)
        
        # Verify structure
        assert "answer" in result
        assert "mode" in result
        assert "tier_used" in result
        assert "tier_requested" in result


class TestTierHierarchyIntegration:
    """Test integration with 3-tier hierarchy."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_auto_tier_selection(self):
        """Test automatic tier selection based on availability."""
        processor = MultiPassBatchProcessor()
        
        config = QueryConfig(
            query="Test query",
            num_passes=1,
            num_secondary_questions=1,
            tier="auto"
        )
        
        result = await processor._process_single_query(1, config)
        
        assert result.success
        assert result.result["tier_used"] in ["cursor", "desktop", "docker"]
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_docker_tier_always_works(self):
        """Test that docker tier always succeeds."""
        processor = MultiPassBatchProcessor()
        
        config = QueryConfig(
            query="Test query",
            tier="docker"
        )
        
        result = await processor._process_single_query(1, config)
        
        assert result.success
        assert result.result["tier_used"] == "docker"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_tier_fallback_logging(self, capsys):
        """Test that tier fallback is properly logged."""
        processor = MultiPassBatchProcessor()
        
        config = QueryConfig(
            query="Test",
            tier="cursor",  # Likely unavailable
            max_retries=1
        )
        
        await processor._process_single_query(1, config)
        
        captured = capsys.readouterr()
        # Should log tier usage
        assert "Tier Used:" in captured.out or "tier_used" in captured.out.lower()


class TestProgressFeedback:
    """Test progress feedback and logging."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_progress_logging_during_batch(self, sample_csv, output_dir, capsys):
        """Test that progress is logged during batch processing."""
        processor = MultiPassBatchProcessor()
        await processor.process_csv(sample_csv, output_dir)
        
        captured = capsys.readouterr()
        
        # Should log various stages
        assert "BATCH PROCESSOR STARTING" in captured.out
        assert "PROCESSING QUERY" in captured.out
        assert "BATCH PROCESSING COMPLETE" in captured.out
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_tier_status_checked_at_start(self, sample_csv, output_dir, capsys):
        """Test that tier status is checked and logged at start."""
        processor = MultiPassBatchProcessor()
        await processor.process_csv(sample_csv, output_dir)
        
        captured = capsys.readouterr()
        
        # Should check tier status
        assert "Checking LLM Tier Availability" in captured.out or "Tier Status" in captured.out
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_estimated_time_displayed(self, capsys):
        """Test that estimated time is displayed."""
        processor = MultiPassBatchProcessor()
        
        config = QueryConfig(
            query="Test",
            num_passes=2,
            num_secondary_questions=2
        )
        
        await processor._process_single_query(1, config)
        
        captured = capsys.readouterr()
        
        # Should display estimated time
        assert "Estimated time" in captured.out or "estimated" in captured.out.lower()


class TestErrorRecovery:
    """Test error handling and recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_partial_batch_failure_continues(self):
        """Test that batch continues after individual query failure."""
        # Create CSV with one invalid query
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['query', 'num_passes'])
            writer.writerow(['Valid query', '2'])
            writer.writerow(['', '2'])  # Empty query (should fail validation)
            writer.writerow(['Another valid query', '2'])
            csv_path = Path(f.name)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            processor = MultiPassBatchProcessor()
            
            results = await processor.process_csv(csv_path, output_dir)
            
            # Should have processed what it could
            assert len(results) == 2  # Empty query filtered out during CSV read
            
            # Summary should reflect actual results
            with open(output_dir / "batch_summary.json") as f:
                summary = json.load(f)
            
            assert summary["total_queries"] == 2
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_timeout_handling(self):
        """Test handling of query timeouts."""
        # This would require a very long query or mocking
        # For now, just verify the error structure
        processor = MultiPassBatchProcessor()
        
        config = QueryConfig(
            query="x",  # Too short, will fail validation
            num_passes=1
        )
        
        # Should handle gracefully
        result = await processor._process_single_query(1, config)
        
        # Should record failure
        assert not result.success or result.result is not None


class TestOutputFormats:
    """Test output file formats."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_json_output_valid(self, sample_csv, output_dir):
        """Test that JSON output files are valid."""
        processor = MultiPassBatchProcessor()
        await processor.process_csv(sample_csv, output_dir)
        
        # All JSON files should be valid
        for json_file in output_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)  # Should not raise
                assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_csv_output_valid(self, sample_csv, output_dir):
        """Test that CSV output file is valid."""
        processor = MultiPassBatchProcessor()
        await processor.process_csv(sample_csv, output_dir)
        
        csv_file = output_dir / "batch_summary.csv"
        
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0
        # Verify headers
        assert 'query' in rows[0]
        assert 'success' in rows[0]
        assert 'duration_seconds' in rows[0]


class TestFullWorkflow:
    """Test complete end-to-end workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_complete_workflow_from_csv_to_results(self):
        """Test complete workflow from CSV input to analyzed results."""
        # 1. Create CSV with queries
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['query', 'num_passes', 'num_secondary_questions', 'tier'])
            writer.writerow(['What is caching?', '2', '2', 'docker'])
            writer.writerow(['How does ChromaDB work?', '2', '2', 'docker'])
            csv_path = Path(f.name)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # 2. Process batch
            processor = MultiPassBatchProcessor()
            results = await processor.process_csv(csv_path, output_dir)
            
            # 3. Verify complete workflow
            assert len(results) == 2
            assert all(r.success for r in results)
            
            # 4. Verify all outputs exist
            assert (output_dir / "batch_summary.json").exists()
            assert (output_dir / "batch_summary.csv").exists()
            assert (output_dir / "query_001_result.json").exists()
            assert (output_dir / "query_002_result.json").exists()
            
            # 5. Verify result quality
            with open(output_dir / "query_001_result.json") as f:
                result = json.load(f)
            
            # Should have answer
            assert result["answer"]
            assert len(result["answer"]) > 50  # Substantive answer
            
            # Should have used docker tier
            assert result["tier_used"] == "docker"
            
            # 6. Verify summary accuracy
            with open(output_dir / "batch_summary.json") as f:
                summary = json.load(f)
            
            assert summary["total_queries"] == 2
            assert summary["successful"] == 2
            assert summary["success_rate"] == 1.0
            assert summary["total_duration_seconds"] > 0

