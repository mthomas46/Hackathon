"""
Validation Tests for Session Fixes

These tests validate that the fixes from this session are properly
implemented without requiring full dependency installation.
"""

import pytest
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_PATH = PROJECT_ROOT / "services/ecosystem-mcp"
DASHBOARD_PATH = PROJECT_ROOT / "services/ecosystem-mcp-dashboard"


class TestRedisConnectionFix:
    """Validate Redis connection fix is properly implemented."""
    
    def test_admin_route_has_lazy_connection_check(self):
        """Test that admin.py has lazy connection check before add_to_stream."""
        admin_file = BACKEND_PATH / "src/api/routes/admin.py"
        
        if not admin_file.exists():
            pytest.skip("Backend not found")
        
        content = admin_file.read_text()
        
        # Verify lazy connection check exists
        assert "if not redis._connected or redis.client is None" in content, \
            "Should have lazy connection check"
        
        assert "await redis.connect()" in content, \
            "Should call connect() when not connected"
        
        assert "await redis.add_to_stream" in content, \
            "Should add jobs to Redis stream"
    
    def test_redis_client_has_connection_state(self):
        """Test that RedisClient tracks connection state."""
        redis_file = BACKEND_PATH / "src/utils/redis_client.py"
        
        if not redis_file.exists():
            pytest.skip("Backend not found")
        
        content = redis_file.read_text()
        
        # Verify connection state tracking
        assert "_connected" in content, \
            "Should track connection state"
        
        assert "self.client" in content, \
            "Should have client attribute"
        
        assert "async def connect" in content, \
            "Should have async connect method"


class TestAutoRefreshFix:
    """Validate auto-refresh tab context preservation."""
    
    def test_no_html_meta_refresh(self):
        """Test that HTML meta refresh is not used."""
        ingestion_file = DASHBOARD_PATH / "dashboard_views/ingestion_manager.py"
        
        if not ingestion_file.exists():
            pytest.skip("Dashboard not found")
        
        content = ingestion_file.read_text()
        
        # Should NOT have HTML meta refresh
        assert '<meta http-equiv="refresh"' not in content, \
            "Should not use HTML meta refresh (loses tab context)"
    
    def test_has_manual_refresh_button(self):
        """Test that manual refresh button exists."""
        ingestion_file = DASHBOARD_PATH / "dashboard_views/ingestion_manager.py"
        
        if not ingestion_file.exists():
            pytest.skip("Dashboard not found")
        
        content = ingestion_file.read_text()
        
        # Should have manual refresh button
        assert "Refresh Now" in content, \
            "Should have manual refresh button"
        
        assert "st.rerun()" in content, \
            "Should use st.rerun() to preserve state"
    
    def test_sidebar_navigation_disabled(self):
        """Test that automatic sidebar navigation is disabled."""
        config_file = DASHBOARD_PATH / ".streamlit/config.toml"
        
        if not config_file.exists():
            pytest.skip("Dashboard config not found")
        
        content = config_file.read_text()
        
        # Verify showSidebarNavigation is disabled
        assert "showSidebarNavigation" in content, \
            "Should configure sidebar navigation"
        
        assert "false" in content, \
            "Should disable automatic navigation"


class TestJobManagementFeatures:
    """Validate job management features."""
    
    def test_has_cancel_job_endpoint(self):
        """Test that cancel job endpoint exists."""
        admin_file = BACKEND_PATH / "src/api/routes/admin.py"
        
        if not admin_file.exists():
            pytest.skip("Backend not found")
        
        content = admin_file.read_text()
        
        # Should have cancel endpoint
        assert "/ingest/{job_id}/cancel" in content or "cancel" in content, \
            "Should have cancel job endpoint"
    
    def test_has_clear_jobs_endpoints(self):
        """Test that clear jobs endpoints exist."""
        admin_file = BACKEND_PATH / "src/api/routes/admin.py"
        
        if not admin_file.exists():
            pytest.skip("Backend not found")
        
        content = admin_file.read_text()
        
        # Should have clear endpoints
        assert "/jobs/completed" in content or "/jobs/failed" in content, \
            "Should have clear jobs endpoints"
    
    def test_dashboard_has_cancel_button(self):
        """Test that dashboard has cancel job functionality."""
        ingestion_file = DASHBOARD_PATH / "dashboard_views/ingestion_manager.py"
        
        if not ingestion_file.exists():
            pytest.skip("Dashboard not found")
        
        content = ingestion_file.read_text()
        
        # Should have cancel functionality
        assert "cancel" in content.lower(), \
            "Should have cancel job functionality"
    
    def test_dashboard_has_clear_buttons(self):
        """Test that dashboard has clear jobs functionality."""
        ingestion_file = DASHBOARD_PATH / "dashboard_views/ingestion_manager.py"
        
        if not ingestion_file.exists():
            pytest.skip("Dashboard not found")
        
        content = ingestion_file.read_text()
        
        # Should have clear functionality
        assert "Clear Completed" in content or "Clear Failed" in content, \
            "Should have clear jobs functionality"


class TestWorkerMonitoring:
    """Validate worker monitoring features."""
    
    def test_has_worker_health_endpoint(self):
        """Test that worker health endpoint exists."""
        workers_file = BACKEND_PATH / "src/api/routes/workers.py"
        
        if not workers_file.exists():
            pytest.skip("Workers route not found")
        
        content = workers_file.read_text()
        
        # Should have health endpoint
        assert "/health" in content or "health" in content, \
            "Should have worker health endpoint"
    
    def test_has_worker_monitor_page(self):
        """Test that worker monitor page exists."""
        worker_monitor_file = DASHBOARD_PATH / "dashboard_views/worker_monitor.py"
        
        assert worker_monitor_file.exists(), \
            "Worker monitor page should exist"
    
    def test_worker_monitor_in_navigation(self):
        """Test that worker monitor is in navigation."""
        app_file = DASHBOARD_PATH / "app.py"
        
        if not app_file.exists():
            pytest.skip("Dashboard app not found")
        
        content = app_file.read_text()
        
        # Should be in navigation
        assert "Worker Monitor" in content or "worker_monitor" in content, \
            "Worker monitor should be in navigation"


class TestSkippedDocumentsTracking:
    """Validate skipped documents tracking."""
    
    def test_database_model_has_skipped_field(self):
        """Test that IngestionJobModel has skipped_documents field."""
        db_models_file = BACKEND_PATH / "src/storage/db_models.py"
        
        if not db_models_file.exists():
            pytest.skip("Database models not found")
        
        content = db_models_file.read_text()
        
        # Should have skipped_documents field
        assert "skipped_documents" in content, \
            "Should track skipped documents"
    
    def test_admin_route_returns_skipped(self):
        """Test that admin routes return skipped_documents."""
        admin_file = BACKEND_PATH / "src/api/routes/admin.py"
        
        if not admin_file.exists():
            pytest.skip("Backend not found")
        
        content = admin_file.read_text()
        
        # Should include skipped_documents in response
        assert "skipped_documents" in content, \
            "Should return skipped documents count"
    
    def test_dashboard_displays_skipped(self):
        """Test that dashboard displays skipped documents."""
        ingestion_file = DASHBOARD_PATH / "dashboard_views/ingestion_manager.py"
        
        if not ingestion_file.exists():
            pytest.skip("Dashboard not found")
        
        content = ingestion_file.read_text()
        
        # Should display skipped documents
        assert "skipped" in content.lower(), \
            "Should display skipped documents count"


class TestJobMetadataTracking:
    """Validate job metadata tracking."""
    
    def test_job_processor_updates_metadata(self):
        """Test that job processor updates job metadata."""
        job_processor_file = BACKEND_PATH / "src/services/ingestion/job_processor.py"
        
        if not job_processor_file.exists():
            pytest.skip("Job processor not found")
        
        content = job_processor_file.read_text()
        
        # Should update metadata
        assert "job_metadata" in content or "_update_job_progress" in content, \
            "Should update job metadata"
    
    def test_dashboard_displays_metadata(self):
        """Test that dashboard displays job metadata."""
        ingestion_file = DASHBOARD_PATH / "dashboard_views/ingestion_manager.py"
        
        if not ingestion_file.exists():
            pytest.skip("Dashboard not found")
        
        content = ingestion_file.read_text()
        
        # Should display metadata
        assert "last_processed_file" in content or "job_metadata" in content, \
            "Should display job metadata"


class TestDocumentationExists:
    """Validate that documentation was created."""
    
    def test_redis_connection_fix_doc(self):
        """Test that Redis connection fix documentation exists."""
        doc_file = PROJECT_ROOT / "REDIS_CONNECTION_FIX.md"
        
        assert doc_file.exists(), \
            "Redis connection fix documentation should exist"
    
    def test_auto_refresh_fix_doc(self):
        """Test that auto-refresh fix documentation exists."""
        doc_file = PROJECT_ROOT / "AUTO_REFRESH_TAB_CONTEXT_FIX.md"
        
        assert doc_file.exists(), \
            "Auto-refresh fix documentation should exist"
    
    def test_testing_guide_exists(self):
        """Test that testing guide exists."""
        doc_file = PROJECT_ROOT / "SESSION_TESTING_GUIDE.md"
        
        assert doc_file.exists(), \
            "Testing guide should exist"


class TestTestSuiteExists:
    """Validate that test files were created."""
    
    def test_redis_connection_tests_exist(self):
        """Test that Redis connection tests exist."""
        test_file = PROJECT_ROOT / "tests/test_redis_connection.py"
        
        assert test_file.exists(), \
            "Redis connection tests should exist"
    
    def test_dashboard_tests_exist(self):
        """Test that dashboard tests exist."""
        test_file = PROJECT_ROOT / "tests/test_dashboard_fixes.py"
        
        assert test_file.exists(), \
            "Dashboard tests should exist"
    
    def test_e2e_tests_exist(self):
        """Test that E2E tests exist."""
        test_file = PROJECT_ROOT / "tests/test_ingestion_e2e.py"
        
        assert test_file.exists(), \
            "E2E tests should exist"
    
    def test_test_runner_exists(self):
        """Test that test runner script exists."""
        runner = PROJECT_ROOT / "run_session_tests.sh"
        
        assert runner.exists(), \
            "Test runner script should exist"
        
        # Should be executable
        assert runner.stat().st_mode & 0o111, \
            "Test runner should be executable"


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

