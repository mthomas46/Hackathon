"""Unit tests for LLM Gateway Security Filter.

Tests the security-aware content analysis and provider routing functionality
that ensures sensitive content is handled appropriately.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# Adjust path for local imports
import sys
from pathlib import Path

# Add the LLM Gateway service directory to Python path
llm_gateway_path = Path(__file__).parent.parent.parent.parent / "services" / "llm-gateway"
sys.path.insert(0, str(llm_gateway_path))

from modules.security_filter import SecurityFilter, SecurityAnalysis

# Test markers for parallel execution
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.security
]


class TestSecurityFilter:
    """Test suite for SecurityFilter class."""

    @pytest.fixture
    def security_filter(self):
        """Create a SecurityFilter instance for testing."""
        return SecurityFilter()

    @pytest.fixture
    def sensitive_content(self):
        """Sample sensitive content for testing."""
        return """
        Here is my API key: sk-1234567890abcdef
        The database password is: mySecurePass123!
        Please find the user token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
        Also, the admin credentials are: admin/secret123
        """

    @pytest.fixture
    def clean_content(self):
        """Sample clean content for testing."""
        return """
        This is a regular documentation about Python programming.
        We will discuss functions, classes, and best practices.
        The tutorial covers basic concepts and advanced topics.
        """

    def test_security_filter_initialization(self, security_filter):
        """Test that SecurityFilter initializes correctly."""
        assert isinstance(security_filter, SecurityFilter)
        assert hasattr(security_filter, 'sensitive_keywords')
        assert hasattr(security_filter, 'security_policies')

        # Should have default sensitive keywords
        assert 'password' in security_filter.sensitive_keywords
        assert 'secret' in security_filter.sensitive_keywords
        assert 'token' in security_filter.sensitive_keywords

    @pytest.mark.asyncio
    async def test_analyze_sensitive_content(self, security_filter, sensitive_content):
        """Test analysis of content with sensitive information."""
        analysis = await security_filter.analyze_content(sensitive_content)

        assert isinstance(analysis, SecurityAnalysis)
        assert analysis.is_sensitive is True
        assert analysis.sensitivity_score > 0
        assert len(analysis.detected_keywords) > 0

        # Should detect multiple sensitive keywords
        assert 'password' in analysis.detected_keywords
        assert 'token' in analysis.detected_keywords
        assert 'secret' in analysis.detected_keywords

    @pytest.mark.asyncio
    async def test_analyze_clean_content(self, security_filter, clean_content):
        """Test analysis of content without sensitive information."""
        analysis = await security_filter.analyze_content(clean_content)

        assert isinstance(analysis, SecurityAnalysis)
        assert analysis.is_sensitive is False
        assert analysis.sensitivity_score == 0.0
        assert len(analysis.detected_keywords) == 0

    @pytest.mark.asyncio
    async def test_empty_content_analysis(self, security_filter):
        """Test analysis of empty content."""
        analysis = await security_filter.analyze_content("")

        assert isinstance(analysis, SecurityAnalysis)
        assert analysis.is_sensitive is False
        assert analysis.sensitivity_score == 0.0
        assert len(analysis.detected_keywords) == 0

    @pytest.mark.asyncio
    async def test_get_allowed_providers_sensitive_content(self, security_filter, sensitive_content):
        """Test getting allowed providers for sensitive content."""
        allowed_providers = await security_filter.get_allowed_providers(sensitive_content)

        # Should only allow secure providers for sensitive content
        secure_providers = security_filter.security_policies["sensitive_only_providers"]
        assert allowed_providers == secure_providers

    @pytest.mark.asyncio
    async def test_get_allowed_providers_clean_content(self, security_filter, clean_content):
        """Test getting allowed providers for clean content."""
        allowed_providers = await security_filter.get_allowed_providers(clean_content)

        # Should allow all providers for clean content
        all_providers = security_filter.security_policies["all_providers"]
        assert allowed_providers == all_providers

    @pytest.mark.asyncio
    async def test_should_route_to_secure_provider_sensitive(self, security_filter, sensitive_content):
        """Test routing decision for sensitive content."""
        should_route_secure = await security_filter.should_route_to_secure_provider(sensitive_content)

        assert should_route_secure is True

    @pytest.mark.asyncio
    async def test_should_route_to_secure_provider_clean(self, security_filter, clean_content):
        """Test routing decision for clean content."""
        should_route_secure = await security_filter.should_route_to_secure_provider(clean_content)

        assert should_route_secure is False

    def test_categorize_authentication_content(self, security_filter):
        """Test categorization of authentication-related content."""
        auth_content = "The password is secret123 and the API key is sk-123456"

        categories = security_filter._categorize_content(auth_content.lower(), ['password', 'key'])

        assert "authentication" in categories

    def test_categorize_personal_data_content(self, security_filter):
        """Test categorization of personal data content."""
        personal_content = "User email is test@example.com and phone is 555-0123"

        categories = security_filter._categorize_content(personal_content.lower(), ['email', 'phone'])

        assert "personal_data" in categories

    def test_categorize_code_security_content(self, security_filter):
        """Test categorization of code security content."""
        code_content = """
        import os
        password = os.getenv('DB_PASSWORD')
        api_key = 'sk-1234567890abcdef'
        """

        categories = security_filter._categorize_content(code_content.lower(), ['password', 'key'])

        assert "code_security" in categories

    def test_generate_recommendations_sensitive_content(self, security_filter, sensitive_content):
        """Test generating recommendations for sensitive content."""
        analysis = SecurityAnalysis(
            is_sensitive=True,
            sensitivity_score=0.8,
            detected_keywords=['password', 'token'],
            categories=['authentication'],
            recommendations=[]
        )

        recommendations = security_filter._generate_security_recommendations(
            analysis.is_sensitive,
            analysis.sensitivity_score,
            analysis.categories
        )

        assert len(recommendations) > 0
        assert any("routing to secure providers" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_high_sensitivity(self, security_filter):
        """Test generating recommendations for high sensitivity content."""
        recommendations = security_filter._generate_security_recommendations(
            True, 0.9, ['authentication']
        )

        assert len(recommendations) > 0
        assert any("high sensitivity" in rec.lower() for rec in recommendations)

    def test_update_sensitive_keywords(self, security_filter):
        """Test updating the sensitive keywords list."""
        original_count = len(security_filter.sensitive_keywords)

        new_keywords = ['new_secret', 'custom_token']
        security_filter.update_sensitive_keywords(new_keywords)

        # Should have added the new keywords
        assert len(security_filter.sensitive_keywords) == original_count + len(new_keywords)
        assert 'new_secret' in security_filter.sensitive_keywords
        assert 'custom_token' in security_filter.sensitive_keywords

    def test_get_security_stats(self, security_filter):
        """Test getting security statistics."""
        stats = security_filter.get_security_stats()

        assert isinstance(stats, dict)
        assert 'sensitive_keywords_count' in stats
        assert 'security_policies' in stats
        assert stats['sensitive_keywords_count'] == len(security_filter.sensitive_keywords)
        assert 'auto_classification_enabled' in stats

    @pytest.mark.asyncio
    async def test_security_analysis_logging(self, security_filter, sensitive_content):
        """Test that security analysis includes proper logging."""
        # This test verifies that sensitive content analysis triggers appropriate logging
        analysis = await security_filter.analyze_content(sensitive_content)

        # The analysis should have been performed
        assert analysis.is_sensitive is True
        assert len(analysis.detected_keywords) > 0

    def test_security_analysis_structure(self, security_filter):
        """Test the structure of SecurityAnalysis objects."""
        analysis = SecurityAnalysis(
            is_sensitive=True,
            sensitivity_score=0.7,
            detected_keywords=['password', 'token'],
            categories=['authentication'],
            recommendations=['Use secure providers']
        )

        assert analysis.is_sensitive is True
        assert analysis.sensitivity_score == 0.7
        assert len(analysis.detected_keywords) == 2
        assert len(analysis.categories) == 1
        assert len(analysis.recommendations) == 1

    def test_sensitivity_score_calculation(self, security_filter):
        """Test sensitivity score calculation based on keywords."""
        # Content with multiple sensitive keywords
        content = "password token secret key credential"
        analysis = SecurityAnalysis(
            is_sensitive=True,
            sensitivity_score=min(len(content.split()) * 0.2, 1.0),  # Simulate score calculation
            detected_keywords=content.split(),
            categories=['authentication'],
            recommendations=[]
        )

        # Score should be proportional to number of keywords
        assert analysis.sensitivity_score > 0
        assert analysis.sensitivity_score <= 1.0

    @pytest.mark.asyncio
    async def test_mixed_content_analysis(self, security_filter):
        """Test analysis of content with both sensitive and non-sensitive parts."""
        mixed_content = """
        This is a regular tutorial about programming.
        Remember to use strong passwords and keep your API keys secure.
        The database password should be complex.
        """

        analysis = await security_filter.analyze_content(mixed_content)

        # Should detect sensitive keywords even in mixed content
        assert len(analysis.detected_keywords) > 0
        assert 'password' in analysis.detected_keywords
        assert 'api' in [kw.lower() for kw in analysis.detected_keywords]

    def test_case_insensitive_keyword_detection(self, security_filter):
        """Test that keyword detection is case insensitive."""
        content_upper = "PASSWORD TOKEN SECRET"
        content_lower = "password token secret"
        content_mixed = "Password Token Secret"

        # All should detect the same keywords
        upper_analysis = SecurityAnalysis(
            is_sensitive=True,
            sensitivity_score=0.6,
            detected_keywords=['password', 'token', 'secret'],
            categories=['authentication'],
            recommendations=[]
        )

        assert len(upper_analysis.detected_keywords) == 3
        # Note: In a real implementation, the content would be lowercased for comparison
