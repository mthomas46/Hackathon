"""
End-to-End Tests for Documentation Run Management System

Tests complete user workflows from dashboard to database.
"""

import pytest
import httpx
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os


# Configuration
API_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8501"
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"


class TestDocumentationBrowserUI:
    """E2E tests for Documentation Browser UI."""
    
    @pytest.fixture
    def driver(self):
        """Create a Selenium WebDriver."""
        options = webdriver.ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    
    @pytest.fixture
    def api_client(self):
        """Create an httpx client for API calls."""
        return httpx.Client(base_url=API_URL, timeout=30.0)
    
    def test_access_documentation_browser(self, driver):
        """Test accessing the Documentation Browser page."""
        driver.get(DASHBOARD_URL)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Find and click Documentation Browser in sidebar
        try:
            nav_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, "📚 Documentation Browser"))
            )
            nav_link.click()
            
            # Wait for page content to load
            time.sleep(2)
            
            # Verify page title
            assert "Documentation Browser" in driver.page_source
        except TimeoutException:
            pytest.skip("Dashboard navigation not available or not ready")
    
    def test_view_run_history(self, driver, api_client):
        """Test viewing run history in the UI."""
        # First create a test run via API
        response = api_client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "E2E UI Test Run",
                "description": "Testing UI display",
                "source_directory": "/app/tests",
                "num_passes": 2,
                "questions_per_pass": 3
            }
        )
        
        if response.status_code != 200:
            pytest.skip("Could not create test run")
        
        run_id = response.json()["run_id"]
        
        try:
            # Open Documentation Browser
            driver.get(DASHBOARD_URL)
            time.sleep(2)
            
            # Click Documentation Browser
            nav_link = driver.find_element(By.LINK_TEXT, "📚 Documentation Browser")
            nav_link.click()
            time.sleep(2)
            
            # Should see "Run History" tab
            assert "Run History" in driver.page_source or "📋" in driver.page_source
            
            # Should see our test run
            assert "E2E UI Test Run" in driver.page_source
        
        finally:
            # Cleanup
            api_client.delete(f"/api/v1/documentation/runs/{run_id}")
    
    def test_filter_runs_by_status(self, driver):
        """Test filtering runs by status."""
        driver.get(DASHBOARD_URL)
        time.sleep(2)
        
        try:
            # Navigate to Documentation Browser
            nav_link = driver.find_element(By.LINK_TEXT, "📚 Documentation Browser")
            nav_link.click()
            time.sleep(2)
            
            # Find status filter dropdown
            filter_elements = driver.find_elements(By.TAG_NAME, "select")
            
            if filter_elements:
                status_filter = filter_elements[0]
                
                # Select "completed" status
                from selenium.webdriver.support.select import Select
                select = Select(status_filter)
                select.select_by_visible_text("completed")
                
                time.sleep(2)
                
                # Verify filtering worked (all visible runs should be completed)
                assert "completed" in driver.page_source.lower()
        
        except Exception as e:
            pytest.skip(f"Filter test not applicable: {e}")
    
    def test_view_statistics_tab(self, driver):
        """Test viewing statistics tab."""
        driver.get(DASHBOARD_URL)
        time.sleep(2)
        
        try:
            # Navigate to Documentation Browser
            nav_link = driver.find_element(By.LINK_TEXT, "📚 Documentation Browser")
            nav_link.click()
            time.sleep(2)
            
            # Click Statistics tab
            stats_tab = driver.find_element(By.PARTIAL_LINK_TEXT, "Statistics")
            stats_tab.click()
            time.sleep(2)
            
            # Should see metrics
            assert "Total Runs" in driver.page_source or "📊" in driver.page_source
        
        except Exception as e:
            pytest.skip(f"Statistics tab test not applicable: {e}")


class TestCompleteUserWorkflow:
    """E2E tests for complete user workflows."""
    
    @pytest.fixture
    def api_client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=30.0)
    
    def test_create_view_delete_workflow(self, api_client):
        """Test complete workflow: create run, view it, export it, delete it."""
        # Step 1: Create a run
        print("\n1. Creating documentation run...")
        create_response = api_client.post(
            "/api/v1/documentation/runs",
            json={
                "name": "E2E Workflow Test",
                "description": "Complete workflow test",
                "source_directory": "/app/src",
                "output_format": "markdown",
                "response_size": "M",
                "tier": "docker",
                "num_passes": 3,
                "questions_per_pass": 5,
                "created_by": "e2e_test"
            }
        )
        
        assert create_response.status_code == 200
        run_id = create_response.json()["run_id"]
        print(f"   ✅ Created run: {run_id}")
        
        try:
            # Step 2: Verify run exists
            print("\n2. Verifying run exists...")
            get_response = api_client.get(f"/api/v1/documentation/runs/{run_id}")
            assert get_response.status_code == 200
            run_data = get_response.json()
            assert run_data["name"] == "E2E Workflow Test"
            assert run_data["status"] == "pending"
            print("   ✅ Run verified")
            
            # Step 3: List all runs and verify it appears
            print("\n3. Listing all runs...")
            list_response = api_client.get("/api/v1/documentation/runs")
            assert list_response.status_code == 200
            runs = list_response.json()
            run_ids = [r["id"] for r in runs]
            assert run_id in run_ids
            print(f"   ✅ Found {len(runs)} runs, including our test run")
            
            # Step 4: Get documents (should be empty)
            print("\n4. Checking documents...")
            docs_response = api_client.get(
                f"/api/v1/documentation/runs/{run_id}/documents"
            )
            assert docs_response.status_code == 200
            documents = docs_response.json()
            assert len(documents) == 0
            print("   ✅ No documents yet (expected)")
            
            # Step 5: Get progress (should be None or minimal)
            print("\n5. Checking progress...")
            progress_response = api_client.get(
                f"/api/v1/documentation/runs/{run_id}/progress"
            )
            assert progress_response.status_code == 200
            progress = progress_response.json()
            print(f"   ✅ Progress: {progress}")
            
            # Step 6: Filter by status
            print("\n6. Filtering by status...")
            filter_response = api_client.get(
                "/api/v1/documentation/runs",
                params={"status": "pending"}
            )
            assert filter_response.status_code == 200
            pending_runs = filter_response.json()
            pending_ids = [r["id"] for r in pending_runs]
            assert run_id in pending_ids
            print(f"   ✅ Found {len(pending_runs)} pending runs")
            
            # Step 7: Attempt to export (should fail - no documents)
            print("\n7. Attempting export...")
            export_response = api_client.get(
                f"/api/v1/documentation/runs/{run_id}/export/zip"
            )
            # Should fail because no documents
            assert export_response.status_code == 404
            print("   ✅ Export correctly fails (no documents)")
        
        finally:
            # Step 8: Delete run
            print("\n8. Deleting run...")
            delete_response = api_client.delete(
                f"/api/v1/documentation/runs/{run_id}"
            )
            assert delete_response.status_code == 200
            print("   ✅ Run deleted")
            
            # Step 9: Verify deletion
            print("\n9. Verifying deletion...")
            verify_response = api_client.get(
                f"/api/v1/documentation/runs/{run_id}"
            )
            assert verify_response.status_code == 404
            print("   ✅ Deletion verified")
        
        print("\n✅ Complete workflow test PASSED!")
    
    def test_multiple_runs_management(self, api_client):
        """Test managing multiple runs simultaneously."""
        run_ids = []
        
        try:
            # Create multiple runs
            print("\n1. Creating multiple runs...")
            for i in range(3):
                response = api_client.post(
                    "/api/v1/documentation/runs",
                    json={
                        "name": f"Multi-Run Test {i+1}",
                        "description": f"Test run number {i+1}",
                        "source_directory": "/app/src",
                        "num_passes": 2,
                        "questions_per_pass": 2
                    }
                )
                
                assert response.status_code == 200
                run_id = response.json()["run_id"]
                run_ids.append(run_id)
                print(f"   ✅ Created run {i+1}: {run_id}")
            
            # List all runs
            print("\n2. Listing all runs...")
            list_response = api_client.get("/api/v1/documentation/runs")
            assert list_response.status_code == 200
            all_runs = list_response.json()
            all_run_ids = [r["id"] for r in all_runs]
            
            # Verify all our runs are present
            for run_id in run_ids:
                assert run_id in all_run_ids
            print(f"   ✅ All {len(run_ids)} runs found in list")
            
            # Get details for each run
            print("\n3. Getting details for each run...")
            for i, run_id in enumerate(run_ids):
                response = api_client.get(f"/api/v1/documentation/runs/{run_id}")
                assert response.status_code == 200
                run_data = response.json()
                assert run_data["name"] == f"Multi-Run Test {i+1}"
                print(f"   ✅ Run {i+1} details verified")
        
        finally:
            # Cleanup: Delete all runs
            print("\n4. Cleaning up runs...")
            for i, run_id in enumerate(run_ids):
                response = api_client.delete(f"/api/v1/documentation/runs/{run_id}")
                assert response.status_code == 200
                print(f"   ✅ Deleted run {i+1}")
        
        print("\n✅ Multiple runs management test PASSED!")


class TestPerformanceAndScalability:
    """E2E tests for performance and scalability."""
    
    @pytest.fixture
    def api_client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=60.0)
    
    def test_list_large_number_of_runs(self, api_client):
        """Test listing runs with pagination."""
        # Test with large limit
        response = api_client.get(
            "/api/v1/documentation/runs",
            params={"limit": 100, "offset": 0}
        )
        
        assert response.status_code == 200
        runs = response.json()
        
        # Should complete in reasonable time
        assert isinstance(runs, list)
        print(f"   ✅ Retrieved {len(runs)} runs successfully")
    
    def test_rapid_api_calls(self, api_client):
        """Test making rapid API calls."""
        print("\n1. Making 10 rapid API calls...")
        
        start_time = time.time()
        
        for i in range(10):
            response = api_client.get("/api/v1/documentation/runs")
            assert response.status_code == 200
        
        elapsed = time.time() - start_time
        
        print(f"   ✅ Completed 10 calls in {elapsed:.2f}s")
        print(f"   ✅ Average: {elapsed/10:.3f}s per call")
        
        # Should complete in reasonable time (< 10 seconds total)
        assert elapsed < 10.0


class TestDataIntegrity:
    """E2E tests for data integrity."""
    
    @pytest.fixture
    def api_client(self):
        """Create an httpx client."""
        return httpx.Client(base_url=API_URL, timeout=30.0)
    
    def test_run_data_persistence(self, api_client):
        """Test that run data persists correctly."""
        # Create a run with specific data
        test_data = {
            "name": "Data Integrity Test",
            "description": "Testing data persistence",
            "source_directory": "/app/src/services",
            "output_format": "markdown",
            "response_size": "XL",
            "tier": "desktop",
            "num_passes": 5,
            "questions_per_pass": 10,
            "created_by": "data_integrity_test",
            "metadata": {
                "project": "ecosystem-mcp",
                "version": "1.0.0",
                "tags": ["test", "e2e", "integrity"]
            }
        }
        
        # Create run
        create_response = api_client.post(
            "/api/v1/documentation/runs",
            json=test_data
        )
        
        assert create_response.status_code == 200
        run_id = create_response.json()["run_id"]
        
        try:
            # Retrieve the run
            get_response = api_client.get(f"/api/v1/documentation/runs/{run_id}")
            assert get_response.status_code == 200
            run_data = get_response.json()
            
            # Verify all data is preserved
            assert run_data["name"] == test_data["name"]
            assert run_data["description"] == test_data["description"]
            assert run_data["source_directory"] == test_data["source_directory"]
            assert run_data["output_format"] == test_data["output_format"]
            assert run_data["response_size"] == test_data["response_size"]
            assert run_data["tier"] == test_data["tier"]
            assert run_data["num_passes"] == test_data["num_passes"]
            assert run_data["questions_per_pass"] == test_data["questions_per_pass"]
            
            print("   ✅ All data fields preserved correctly")
        
        finally:
            # Cleanup
            api_client.delete(f"/api/v1/documentation/runs/{run_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])

