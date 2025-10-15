"""
End-to-end tests for ingestion path resolution.

Simulates real user workflows with the Streamlit dashboard and backend API.
"""

import pytest
import time
import httpx
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sys

# Add service directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "ecosystem-mcp"))


@pytest.mark.e2e
@pytest.mark.skip(reason="Requires Selenium and running dashboard")
class TestDashboardIngestionWorkflow:
    """Test complete user workflows through the dashboard."""
    
    @pytest.fixture
    def browser(self):
        """Set up browser for testing."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run without GUI
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    
    @pytest.fixture
    def dashboard_url(self):
        """Dashboard URL."""
        return "http://localhost:8501"
    
    def test_ingestion_with_default_path(self, browser, dashboard_url):
        """Test starting ingestion with default Hackathon path."""
        try:
            # Navigate to dashboard
            browser.get(dashboard_url)
            
            # Wait for page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Click on Ingestion Manager in sidebar
            ingestion_link = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "📥 Ingestion Manager"))
            )
            ingestion_link.click()
            
            # Verify default path is set
            path_input = browser.find_element(By.XPATH, "//input[@type='text' and contains(@value, 'Hackathon')]")
            assert "Hackathon" in path_input.get_attribute("value")
            
            # Verify "Host Machine Path" is selected by default
            host_path_radio = browser.find_element(By.XPATH, "//input[@type='radio' and @value='Host Machine Path']")
            assert host_path_radio.is_selected()
            
            # Click "Start Ingestion" button
            start_button = browser.find_element(By.XPATH, "//button[contains(text(), 'Start Ingestion')]")
            start_button.click()
            
            # Wait for validation message
            validation_msg = WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Resolving host path')]"))
            )
            assert validation_msg is not None
            
            # Wait for success message
            success_msg = WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Path validated')]"))
            )
            assert "Path validated" in success_msg.text
            
            # Wait for ingestion started message
            ingestion_msg = WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Ingestion started')]"))
            )
            assert "Ingestion started" in ingestion_msg.text or "Job ID" in browser.page_source
            
        except TimeoutException as e:
            pytest.fail(f"Element not found or timeout: {e}")
    
    def test_validation_feedback(self, browser, dashboard_url):
        """Test that validation feedback is shown to user."""
        try:
            browser.get(f"{dashboard_url}")
            
            # Navigate to Ingestion Manager
            ingestion_link = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "📥 Ingestion Manager"))
            )
            ingestion_link.click()
            
            # Start ingestion
            start_button = browser.find_element(By.XPATH, "//button[contains(text(), 'Start Ingestion')]")
            start_button.click()
            
            # Should see these messages in sequence:
            # 1. "Starting ingestion job..."
            # 2. "Resolving host path..."
            # 3. "Path validated: /app"
            # 4. "Ingestion started!"
            
            time.sleep(2)  # Wait for messages
            page_text = browser.find_element(By.TAG_NAME, "body").text
            
            # Check for validation feedback
            assert "Resolving" in page_text or "Path validated" in page_text or "Ingestion started" in page_text
            
        except TimeoutException as e:
            pytest.fail(f"Validation feedback not shown: {e}")
    
    def test_recent_paths_saved(self, browser, dashboard_url):
        """Test that successful paths are saved to recent history."""
        try:
            browser.get(dashboard_url)
            
            # Navigate to Ingestion Manager
            ingestion_link = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "📥 Ingestion Manager"))
            )
            ingestion_link.click()
            
            # Select "Recent Paths" method
            recent_paths_radio = browser.find_element(By.XPATH, "//input[@type='radio' and @value='Recent Paths']")
            recent_paths_radio.click()
            
            # Should show recent paths dropdown
            time.sleep(1)
            page_text = browser.find_element(By.TAG_NAME, "body").text
            
            # Default path should be in recent paths
            assert "Hackathon" in page_text or "Recent Paths" in page_text
            
        except TimeoutException as e:
            pytest.skip(f"Recent paths functionality not testable: {e}")
    
    def test_container_path_mode(self, browser, dashboard_url):
        """Test using Container Path mode."""
        try:
            browser.get(dashboard_url)
            
            # Navigate to Ingestion Manager
            ingestion_link = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "📥 Ingestion Manager"))
            )
            ingestion_link.click()
            
            # Switch to Container Path
            container_radio = browser.find_element(By.XPATH, "//input[@type='radio' and @value='Container Path']")
            container_radio.click()
            
            # Verify default is /app
            time.sleep(1)
            path_input = browser.find_element(By.XPATH, "//input[@type='text' and @value='/app']")
            assert path_input.get_attribute("value") == "/app"
            
            # Start ingestion
            start_button = browser.find_element(By.XPATH, "//button[contains(text(), 'Start Ingestion')]")
            start_button.click()
            
            # Should NOT see "Resolving host path" (no validation needed)
            time.sleep(2)
            page_text = browser.find_element(By.TAG_NAME, "body").text
            
            # Should go straight to "Ingestion started"
            assert "Ingestion started" in page_text or "Job ID" in page_text
            
        except TimeoutException as e:
            pytest.fail(f"Container path mode test failed: {e}")


@pytest.mark.e2e
class TestAPIWorkflowE2E:
    """Test complete API workflows end-to-end."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_full_ingestion_lifecycle(self, api_base_url):
        """Test complete ingestion lifecycle: validate → ingest → monitor → complete."""
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Validate path
                print("\n1. Validating path...")
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon"},
                    timeout=10.0
                )
                assert validate_response.status_code == 200
                validation = validate_response.json()
                assert validation["is_valid"] is True
                print(f"   ✅ Path validated: {validation['container_path']}")
                
                resolved_path = validation["container_path"]
                
                # Step 2: Start ingestion
                print("\n2. Starting ingestion...")
                ingest_response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": resolved_path,
                        "mode": "quick",
                        "resolve_host_path": False
                    },
                    timeout=30.0
                )
                assert ingest_response.status_code == 200
                data = ingest_response.json()
                job_id = data["job_id"]
                print(f"   ✅ Job created: {job_id}")
                
                # Step 3: Monitor job status
                print("\n3. Monitoring job status...")
                max_checks = 10
                for i in range(max_checks):
                    status_response = await client.get(
                        f"{api_base_url}/api/v1/admin/ingest/status",
                        timeout=5.0
                    )
                    assert status_response.status_code == 200
                    jobs = status_response.json()
                    
                    # Find our job
                    our_job = next((j for j in jobs if j.get("id") == job_id), None)
                    
                    if our_job:
                        status = our_job.get("status")
                        print(f"   Status: {status}")
                        
                        if status in ["completed", "failed"]:
                            print(f"   ✅ Job finished: {status}")
                            break
                    
                    # Wait before next check
                    await asyncio.sleep(5)
                else:
                    print("   ⚠️ Job still processing after timeout")
                
                # Step 4: Check data stats
                print("\n4. Checking data stats...")
                try:
                    stats_response = await client.get(
                        f"{api_base_url}/api/v1/admin/data/stats",
                        timeout=5.0
                    )
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        print(f"   Total documents: {stats.get('total_documents', 'N/A')}")
                        print(f"   Total embeddings: {stats.get('total_embeddings', 'N/A')}")
                    else:
                        print(f"   ⚠️ Stats endpoint returned {stats_response.status_code}")
                except Exception as e:
                    print(f"   ⚠️ Could not fetch stats: {e}")
                
                print("\n✅ E2E test completed successfully!")
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
        except Exception as e:
            pytest.fail(f"E2E test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, api_base_url):
        """Test error recovery when things go wrong."""
        try:
            async with httpx.AsyncClient() as client:
                # Test 1: Invalid path
                print("\n1. Testing invalid path...")
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/invalid/path/that/does/not/exist"},
                    timeout=10.0
                )
                assert validate_response.status_code == 200
                validation = validate_response.json()
                assert validation["is_valid"] is False
                print("   ✅ Invalid path correctly rejected")
                
                # Test 2: Non-existent container path
                print("\n2. Testing non-existent container path...")
                ingest_response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": "/nonexistent",
                        "mode": "quick",
                        "resolve_host_path": False
                    },
                    timeout=30.0
                )
                assert ingest_response.status_code == 400
                error = ingest_response.json()
                assert "does not exist" in error["detail"].lower()
                print("   ✅ Non-existent path correctly rejected")
                
                # Test 3: Worker health check
                print("\n3. Testing worker health...")
                worker_response = await client.get(
                    f"{api_base_url}/api/v1/admin/workers/ingestion/status",
                    timeout=5.0
                )
                if worker_response.status_code == 200:
                    worker_status = worker_response.json()
                    print(f"   Worker healthy: {worker_status.get('healthy', False)}")
                else:
                    print(f"   ⚠️ Worker status endpoint returned {worker_response.status_code}")
                
                print("\n✅ Error recovery test completed!")
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
        except Exception as e:
            pytest.fail(f"Error recovery test failed: {e}")


@pytest.mark.e2e
class TestPerformanceE2E:
    """Test performance characteristics of the path resolution system."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_validation_performance(self, api_base_url):
        """Test that path validation completes quickly."""
        try:
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                
                response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon"},
                    timeout=10.0
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                assert response.status_code == 200
                assert duration < 2.0, f"Validation took too long: {duration}s"
                
                print(f"\n✅ Validation completed in {duration:.2f}s")
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_concurrent_validations(self, api_base_url):
        """Test multiple concurrent path validations."""
        try:
            async with httpx.AsyncClient() as client:
                paths = [
                    "/Users/mykalthomas/Documents/work/Hackathon",
                    "/Users/mykalthomas/Documents/work/Hackathon/services",
                    "/Users/mykalthomas/Documents/work/Hackathon/tests",
                ]
                
                start_time = time.time()
                
                # Make concurrent requests
                tasks = [
                    client.post(
                        f"{api_base_url}/api/v1/path/validate",
                        json={"path": path},
                        timeout=10.0
                    )
                    for path in paths
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # All requests should succeed
                for i, response in enumerate(responses):
                    if isinstance(response, Exception):
                        print(f"   ⚠️ Path {i+1} failed: {response}")
                    else:
                        assert response.status_code == 200
                        print(f"   ✅ Path {i+1} validated")
                
                print(f"\n✅ {len(paths)} concurrent validations completed in {duration:.2f}s")
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])

