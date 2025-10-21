"""
Unit Tests for Partial Success Utilities (Day 3 - Task 3.1)

Tests the partial success handling infrastructure.
"""

import pytest
from src.utils.partial_success import (
    FailureStage,
    FailureDetail,
    PartialSuccessResult,
    merge_partial_results,
    should_continue_on_failure
)


class TestFailureDetail:
    """Test FailureDetail dataclass."""
    
    def test_create_failure_detail(self):
        """Test creating a failure detail."""
        failure = FailureDetail(
            file_path="test.py",
            stage=FailureStage.EMBEDDING,
            error_message="Embedding failed",
            error_type="EmbeddingError"
        )
        
        assert failure.file_path == "test.py"
        assert failure.stage == FailureStage.EMBEDDING
        assert failure.error_message == "Embedding failed"
        assert failure.error_type == "EmbeddingError"
    
    def test_failure_detail_to_dict(self):
        """Test converting failure detail to dict."""
        failure = FailureDetail(
            file_path="test.py",
            stage=FailureStage.PARSING,
            error_message="Parse error",
            error_type="ValueError"
        )
        
        result = failure.to_dict()
        
        assert result["file_path"] == "test.py"
        assert result["stage"] == "parsing"
        assert result["error_message"] == "Parse error"
        assert result["error_type"] == "ValueError"


class TestPartialSuccessResult:
    """Test PartialSuccessResult class."""
    
    def test_empty_result(self):
        """Test empty result."""
        result = PartialSuccessResult()
        
        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.success_rate == 1.0  # Empty is considered success
    
    def test_add_success(self):
        """Test adding successful operations."""
        result = PartialSuccessResult()
        
        result.add_success()
        result.add_success()
        result.add_success()
        
        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0
        assert result.success_rate == 1.0
    
    def test_add_failure(self):
        """Test adding failed operations."""
        result = PartialSuccessResult()
        
        result.add_failure(
            file_path="test1.py",
            stage=FailureStage.EMBEDDING,
            error=Exception("Test error")
        )
        
        assert result.total == 1
        assert result.succeeded == 0
        assert result.failed == 1
        assert len(result.failures) == 1
        assert result.failures[0].file_path == "test1.py"
    
    def test_add_skip(self):
        """Test adding skipped operations."""
        result = PartialSuccessResult()
        
        result.add_skip()
        result.add_skip()
        
        assert result.total == 2
        assert result.skipped == 2
        assert result.succeeded == 0
        assert result.failed == 0
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = PartialSuccessResult()
        
        result.add_success()
        result.add_success()
        result.add_success()
        result.add_failure("test.py", FailureStage.PARSING, Exception("Error"))
        
        assert result.total == 4
        assert result.succeeded == 3
        assert result.failed == 1
        assert result.success_rate == 0.75
    
    def test_is_complete_success(self):
        """Test complete success detection."""
        result = PartialSuccessResult()
        
        result.add_success()
        result.add_success()
        
        assert result.is_complete_success is True
        assert result.is_partial_success is False
        assert result.is_complete_failure is False
    
    def test_is_partial_success(self):
        """Test partial success detection."""
        result = PartialSuccessResult()
        
        result.add_success()
        result.add_success()
        result.add_failure("test.py", FailureStage.EMBEDDING, Exception("Error"))
        
        assert result.is_complete_success is False
        assert result.is_partial_success is True
        assert result.is_complete_failure is False
    
    def test_is_complete_failure(self):
        """Test complete failure detection."""
        result = PartialSuccessResult()
        
        result.add_failure("test1.py", FailureStage.PARSING, Exception("Error 1"))
        result.add_failure("test2.py", FailureStage.EMBEDDING, Exception("Error 2"))
        
        assert result.is_complete_success is False
        assert result.is_partial_success is False
        assert result.is_complete_failure is True
    
    def test_overall_success_threshold_default(self):
        """Test overall success with default threshold (50%)."""
        result = PartialSuccessResult()
        
        # 60% success rate (above threshold)
        result.add_success()
        result.add_success()
        result.add_success()
        result.add_failure("test1.py", FailureStage.PARSING, Exception("Error"))
        result.add_failure("test2.py", FailureStage.EMBEDDING, Exception("Error"))
        
        assert result.success_rate == 0.6
        assert result.overall_success is True
    
    def test_overall_success_below_threshold(self):
        """Test overall success below threshold."""
        result = PartialSuccessResult()
        
        # 40% success rate (below default 50% threshold)
        result.add_success()
        result.add_success()
        result.add_failure("test1.py", FailureStage.PARSING, Exception("Error"))
        result.add_failure("test2.py", FailureStage.EMBEDDING, Exception("Error"))
        result.add_failure("test3.py", FailureStage.STORAGE, Exception("Error"))
        
        assert result.success_rate == 0.4
        assert result.overall_success is False
    
    def test_overall_success_custom_threshold(self):
        """Test overall success with custom threshold."""
        result = PartialSuccessResult()
        result.metadata["success_threshold"] = 0.8  # 80% threshold
        
        # 75% success rate (below custom threshold)
        result.add_success()
        result.add_success()
        result.add_success()
        result.add_failure("test.py", FailureStage.PARSING, Exception("Error"))
        
        assert result.success_rate == 0.75
        assert result.overall_success is False  # Below 80%
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = PartialSuccessResult()
        result.add_success()
        result.add_failure("test.py", FailureStage.EMBEDDING, Exception("Test error"))
        
        result_dict = result.to_dict()
        
        assert result_dict["total"] == 2
        assert result_dict["succeeded"] == 1
        assert result_dict["failed"] == 1
        assert result_dict["success_rate"] == 0.5
        assert result_dict["is_partial_success"] is True
        assert len(result_dict["failures"]) == 1
    
    def test_get_summary_complete_success(self):
        """Test summary for complete success."""
        result = PartialSuccessResult()
        result.add_success()
        result.add_success()
        
        summary = result.get_summary()
        
        assert "✅" in summary
        assert "2/2" in summary
    
    def test_get_summary_partial_success(self):
        """Test summary for partial success."""
        result = PartialSuccessResult()
        result.add_success()
        result.add_failure("test.py", FailureStage.PARSING, Exception("Error"))
        
        summary = result.get_summary()
        
        assert "⚠️" in summary
        assert "1/2" in summary
    
    def test_get_summary_complete_failure(self):
        """Test summary for complete failure."""
        result = PartialSuccessResult()
        result.add_failure("test.py", FailureStage.PARSING, Exception("Error"))
        
        summary = result.get_summary()
        
        assert "❌" in summary
        assert "0/1" in summary


class TestMergePartialResults:
    """Test merging multiple partial results."""
    
    def test_merge_two_results(self):
        """Test merging two results."""
        result1 = PartialSuccessResult()
        result1.add_success()
        result1.add_success()
        
        result2 = PartialSuccessResult()
        result2.add_success()
        result2.add_failure("test.py", FailureStage.EMBEDDING, Exception("Error"))
        
        merged = merge_partial_results([result1, result2])
        
        assert merged.total == 4
        assert merged.succeeded == 3
        assert merged.failed == 1
        assert len(merged.failures) == 1
    
    def test_merge_empty_results(self):
        """Test merging empty results."""
        result1 = PartialSuccessResult()
        result2 = PartialSuccessResult()
        
        merged = merge_partial_results([result1, result2])
        
        assert merged.total == 0
        assert merged.succeeded == 0
        assert merged.failed == 0
    
    def test_merge_with_skips(self):
        """Test merging results with skipped operations."""
        result1 = PartialSuccessResult()
        result1.add_success()
        result1.add_skip()
        
        result2 = PartialSuccessResult()
        result2.add_skip()
        result2.add_success()
        
        merged = merge_partial_results([result1, result2])
        
        assert merged.total == 4
        assert merged.succeeded == 2
        assert merged.skipped == 2


class TestShouldContinueOnFailure:
    """Test the should_continue_on_failure logic."""
    
    def test_continue_with_no_operations(self):
        """Test that processing continues with no operations yet."""
        result = PartialSuccessResult()
        
        assert should_continue_on_failure(result) is True
    
    def test_continue_with_low_failure_rate(self):
        """Test continuing with low failure rate."""
        result = PartialSuccessResult()
        result.add_success()
        result.add_success()
        result.add_success()
        result.add_success()
        result.add_failure("test.py", FailureStage.PARSING, Exception("Error"))
        
        # 20% failure rate (below default 50% threshold)
        assert should_continue_on_failure(result) is True
    
    def test_stop_with_high_failure_rate(self):
        """Test stopping with high failure rate."""
        result = PartialSuccessResult()
        result.add_success()
        result.add_failure("test1.py", FailureStage.PARSING, Exception("Error"))
        result.add_failure("test2.py", FailureStage.EMBEDDING, Exception("Error"))
        result.add_failure("test3.py", FailureStage.STORAGE, Exception("Error"))
        
        # 75% failure rate (above default 50% threshold)
        assert should_continue_on_failure(result) is False
    
    def test_continue_with_custom_threshold(self):
        """Test with custom failure rate threshold."""
        result = PartialSuccessResult()
        result.add_success()
        result.add_failure("test.py", FailureStage.PARSING, Exception("Error"))
        
        # 50% failure rate
        # Should stop with default threshold (0.5)
        assert should_continue_on_failure(result, max_failure_rate=0.5) is False
        
        # Should continue with higher threshold (0.7)
        assert should_continue_on_failure(result, max_failure_rate=0.7) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

