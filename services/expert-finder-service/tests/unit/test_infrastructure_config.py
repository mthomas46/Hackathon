"""
Unit tests for infrastructure configuration (Settings).

Tests the pydantic-settings integration and configuration validation.
"""

import pytest
from infrastructure.config.settings import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration class."""
    
    def test_settings_initialization_with_defaults(self):
        """Test settings can be initialized with default values."""
        settings = Settings()
        
        assert settings.service_name == "expert-finder-service"
        assert settings.service_version == "1.0.0"
        assert settings.service_port == 5160
        assert settings.environment == "dev"
        assert settings.debug == False
    
    def test_settings_initialization_with_env_vars(self, monkeypatch):
        """Test settings can be overridden with environment variables."""
        monkeypatch.setenv("SERVICE_NAME", "test-service")
        monkeypatch.setenv("SERVICE_VERSION", "2.0.0")
        monkeypatch.setenv("SERVICE_PORT", "9999")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "true")
        
        settings = Settings()
        
        assert settings.service_name == "test-service"
        assert settings.service_version == "2.0.0"
        assert settings.service_port == 9999
        assert settings.environment == "production"
        assert settings.debug == True
    
    def test_settings_scoring_weights_sum_to_one(self):
        """Test that scoring weights sum to 1.0."""
        settings = Settings()
        
        total = (
            settings.role_weight +
            settings.topic_weight +
            settings.service_weight +
            settings.document_weight
        )
        
        assert total == pytest.approx(1.0)
    
    def test_settings_scoring_weights_validation(self, monkeypatch):
        """Test that invalid scoring weights raise validation error."""
        # Set weights that don't sum to 1.0
        monkeypatch.setenv("ROLE_WEIGHT", "0.5")
        monkeypatch.setenv("TOPIC_WEIGHT", "0.5")
        monkeypatch.setenv("SERVICE_WEIGHT", "0.5")
        monkeypatch.setenv("DOCUMENT_WEIGHT", "0.5")
        
        with pytest.raises(ValueError, match="must sum"):
            Settings()
    
    def test_settings_cors_defaults(self):
        """Test CORS settings have sensible defaults."""
        settings = Settings()
        
        assert settings.cors_origins == ["*"]
        assert settings.cors_allow_credentials == True
        assert settings.cors_allow_methods == ["*"]
        assert settings.cors_allow_headers == ["*"]
    
    def test_settings_dependency_urls(self):
        """Test dependency URL configuration."""
        settings = Settings()
        
        assert "user-store" in settings.user_store_url
        assert "doc-store" in settings.doc_store_url
        assert "service-store" in settings.service_store_url
    
    def test_settings_http_timeout(self):
        """Test HTTP timeout configuration."""
        settings = Settings()
        
        assert settings.http_timeout == 10.0
        assert settings.http_timeout > 0
    
    def test_settings_retry_configuration(self):
        """Test retry configuration."""
        settings = Settings()
        
        assert settings.http_retry_attempts == 3
        assert settings.http_retry_max_wait == 10.0
        assert settings.http_retry_min_wait == 1.0
    
    def test_settings_sme_thresholds(self):
        """Test SME threshold configuration."""
        settings = Settings()
        
        assert settings.sme_min_documents == 10
        assert settings.sme_min_score == 0.7
        assert 0.0 <= settings.sme_min_score <= 1.0
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_settings_cache_ttl(self):
        """Test cache TTL configuration."""
        settings = Settings()
        
        assert settings.cache_ttl_seconds > 0
        assert isinstance(settings.cache_ttl_seconds, int)

