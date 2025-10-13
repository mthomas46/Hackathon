"""Tests for configuration validation."""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_validator import ConfigValidator, ValidationResult


class TestConfigValidator:
    """Test configuration validator."""
    
    def test_validator_initialization(self):
        """Test validator can be initialized."""
        validator = ConfigValidator()
        assert validator is not None
        assert isinstance(validator.results, list)
        assert len(validator.results) == 0
    
    def test_validate_environment_variables(self):
        """Test environment variable validation."""
        validator = ConfigValidator()
        
        # Set required env var
        os.environ["API_BASE_URL"] = "http://localhost:8000"
        
        result = validator.validate_environment_variables()
        
        assert isinstance(result, ValidationResult)
        assert result.check_name == "Environment Variables"
        assert isinstance(result.passed, bool)
        assert isinstance(result.message, str)
    
    def test_validate_page_imports(self):
        """Test page import validation."""
        validator = ConfigValidator()
        result = validator.validate_page_imports()
        
        assert isinstance(result, ValidationResult)
        assert result.check_name == "Page Imports"
        assert isinstance(result.passed, bool)
        
        # Should have details about importable/failed pages
        if result.details:
            assert "importable" in result.details or "pages" in result.details or "failed" in result.details
    
    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass."""
        result = ValidationResult(
            check_name="Test Check",
            passed=True,
            message="Test message",
            details={"key": "value"}
        )
        
        assert result.check_name == "Test Check"
        assert result.passed is True
        assert result.message == "Test message"
        assert result.details == {"key": "value"}
    
    @pytest.mark.parametrize("api_url", [
        "http://localhost:8000",
        "http://host.docker.internal:8000",
        "http://ecosystem-mcp:8000"
    ])
    def test_validate_api_connectivity_urls(self, api_url):
        """Test API connectivity validation with different URLs."""
        validator = ConfigValidator()
        result = validator.validate_api_connectivity(api_url)
        
        assert isinstance(result, ValidationResult)
        assert result.check_name == "API Connectivity"
        # May pass or fail depending on actual connectivity
        assert isinstance(result.passed, bool)
    
    def test_run_all_validations_returns_tuple(self):
        """Test that run_all_validations returns correct tuple."""
        validator = ConfigValidator()
        api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        results, all_passed = validator.run_all_validations(api_url)
        
        assert isinstance(results, list)
        assert isinstance(all_passed, bool)
        assert len(results) > 0
        
        # All results should be ValidationResult instances
        for result in results:
            assert isinstance(result, ValidationResult)
    
    def test_validation_result_without_details(self):
        """Test ValidationResult without details."""
        result = ValidationResult(
            check_name="Test",
            passed=True,
            message="Test message"
        )
        
        assert result.details is None

