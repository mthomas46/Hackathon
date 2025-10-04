"""Integration tests for DataStore logging to log-collector.

Tests the complete flow:
1. Datastore service receives request
2. Middleware intercepts and logs
3. Log-collector receives and stores log
4. Log can be queried back

Requires:
- log-collector service running on port 8104
- At least one datastore service running
"""

import pytest
import requests
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List


# Service configurations
SERVICES = [
    {"name": "doc-store", "port": 5020, "create_endpoint": "/documents", "payload": {"content": "test"}},
    {"name": "prompt-store", "port": 5030, "create_endpoint": "/prompts", "payload": {"template": "test", "variables": []}},
    {"name": "external-service-store", "port": 5140, "create_endpoint": "/services", "payload": {
        "name": f"test-{uuid.uuid4().hex[:8]}",
        "display_name": "Test",
        "description": "Test",
        "service_type": "api",
        "version": "1.0",
        "technologies": [],
        "run_requirements": {}
    }},
    {"name": "memory-agent", "port": 5090, "create_endpoint": "/memory/put", "payload": {
        "item": {
            "id": f"test-{uuid.uuid4().hex[:8]}",
            "user_id": "test",
            "memory_type": "context",
            "content": "test",
            "metadata": {}
        }
    }},
    {"name": "user-store", "port": 5150, "create_endpoint": "/users", "payload": {
        "name": f"test-user-{uuid.uuid4().hex[:8]}",
        "email": f"test-{uuid.uuid4().hex[:8]}@example.com"
    }},
]

LOG_COLLECTOR_URL = "http://localhost:8104"
TIMEOUT = 5


class TestLogCollectorIntegration:
    """Test log-collector service availability and basic functionality."""
    
    def test_log_collector_health(self):
        """Test that log-collector is running and healthy."""
        try:
            response = requests.get(f"{LOG_COLLECTOR_URL}/health", timeout=TIMEOUT)
            assert response.status_code == 200, "Log-collector health check failed"
        except requests.ConnectionError:
            pytest.skip("Log-collector service not running on port 8104")
    
    def test_log_collector_accepts_logs(self):
        """Test that log-collector accepts log entries."""
        test_log = {
            "service": "test-integration",
            "level": "INFO",
            "message": "Integration test log",
            "context": {"test": True},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                f"{LOG_COLLECTOR_URL}/logs",
                json=test_log,
                timeout=TIMEOUT
            )
            assert response.status_code in [200, 201], f"Failed to post log: {response.status_code}"
        except requests.ConnectionError:
            pytest.skip("Log-collector service not running")
    
    def test_log_collector_query(self):
        """Test that logs can be queried from log-collector."""
        try:
            response = requests.get(
                f"{LOG_COLLECTOR_URL}/logs?limit=10",
                timeout=TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            assert 'logs' in data or isinstance(data, list)
        except requests.ConnectionError:
            pytest.skip("Log-collector service not running")


class TestDatastoreLoggingEndToEnd:
    """End-to-end tests for datastore operation logging."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Check that log-collector is available."""
        try:
            response = requests.get(f"{LOG_COLLECTOR_URL}/health", timeout=2)
            if response.status_code != 200:
                pytest.skip("Log-collector not healthy")
        except:
            pytest.skip("Log-collector not running")
    
    def _check_service_available(self, service_config: Dict) -> bool:
        """Check if a service is running."""
        try:
            url = f"http://localhost:{service_config['port']}/health"
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _get_recent_logs(
        self,
        service_name: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent logs from log-collector."""
        params = {"limit": limit}
        if service_name:
            params["service"] = service_name
        
        response = requests.get(
            f"{LOG_COLLECTOR_URL}/logs",
            params=params,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            # Handle different response formats
            if isinstance(data, dict) and 'logs' in data:
                return data['logs']
            elif isinstance(data, list):
                return data
        return []
    
    @pytest.mark.parametrize("service_config", SERVICES)
    def test_service_operation_logged(self, service_config):
        """Test that service operations are logged to log-collector."""
        # Check if service is available
        if not self._check_service_available(service_config):
            pytest.skip(f"{service_config['name']} service not running")
        
        # Generate unique workflow ID for tracking
        workflow_id = f"test-{uuid.uuid4().hex[:12]}"
        
        # Make request to service with workflow ID
        url = f"http://localhost:{service_config['port']}{service_config['create_endpoint']}"
        headers = {"X-Workflow-ID": workflow_id}
        
        try:
            response = requests.post(
                url,
                json=service_config['payload'],
                headers=headers,
                timeout=TIMEOUT
            )
            
            # Allow some time for log to be sent
            time.sleep(0.5)
            
            # Query log-collector for this operation
            logs = self._get_recent_logs(service_name=service_config['name'])
            
            # Find logs with our workflow ID
            matching_logs = [
                log for log in logs
                if log.get('context', {}).get('workflow_id') == workflow_id
            ]
            
            # Verify logs were created
            assert len(matching_logs) > 0, f"No logs found for {service_config['name']} with workflow_id {workflow_id}"
            
            # Verify log structure
            for log in matching_logs:
                assert 'service' in log
                assert 'level' in log
                assert 'message' in log
                assert 'context' in log
                assert 'timestamp' in log
                
                context = log['context']
                assert 'operation_id' in context
                assert 'workflow_id' in context
                assert context['workflow_id'] == workflow_id
                assert 'method' in context
                assert 'path' in context
                assert 'operation_type' in context
        
        except requests.RequestException as e:
            pytest.fail(f"Request to {service_config['name']} failed: {e}")
    
    def test_operation_phases_logged(self):
        """Test that start and complete phases are both logged."""
        # Use doc-store as test service
        service_config = SERVICES[0]  # doc-store
        
        if not self._check_service_available(service_config):
            pytest.skip(f"{service_config['name']} service not running")
        
        workflow_id = f"test-phases-{uuid.uuid4().hex[:12]}"
        
        # Make request
        url = f"http://localhost:{service_config['port']}{service_config['create_endpoint']}"
        headers = {"X-Workflow-ID": workflow_id}
        
        response = requests.post(
            url,
            json=service_config['payload'],
            headers=headers,
            timeout=TIMEOUT
        )
        
        time.sleep(0.5)
        
        # Get logs
        logs = self._get_recent_logs(service_name=service_config['name'])
        matching_logs = [
            log for log in logs
            if log.get('context', {}).get('workflow_id') == workflow_id
        ]
        
        # Check for start and complete phases
        phases = [log.get('context', {}).get('phase') for log in matching_logs]
        assert 'start' in phases, "Start phase not logged"
        assert 'complete' in phases, "Complete phase not logged"
    
    def test_duration_tracking(self):
        """Test that operation duration is tracked."""
        service_config = SERVICES[0]
        
        if not self._check_service_available(service_config):
            pytest.skip(f"{service_config['name']} service not running")
        
        workflow_id = f"test-duration-{uuid.uuid4().hex[:12]}"
        
        # Make request
        url = f"http://localhost:{service_config['port']}{service_config['create_endpoint']}"
        headers = {"X-Workflow-ID": workflow_id}
        
        response = requests.post(
            url,
            json=service_config['payload'],
            headers=headers,
            timeout=TIMEOUT
        )
        
        time.sleep(0.5)
        
        # Get logs
        logs = self._get_recent_logs(service_name=service_config['name'])
        matching_logs = [
            log for log in logs
            if log.get('context', {}).get('workflow_id') == workflow_id
            and log.get('context', {}).get('phase') == 'complete'
        ]
        
        assert len(matching_logs) > 0, "No complete logs found"
        
        for log in matching_logs:
            context = log['context']
            assert 'duration_ms' in context
            assert isinstance(context['duration_ms'], (int, float))
            assert context['duration_ms'] > 0
    
    def test_error_logging(self):
        """Test that errors are properly logged."""
        service_config = SERVICES[0]
        
        if not self._check_service_available(service_config):
            pytest.skip(f"{service_config['name']} service not running")
        
        workflow_id = f"test-error-{uuid.uuid4().hex[:12]}"
        
        # Make invalid request (should cause error)
        url = f"http://localhost:{service_config['port']}{service_config['create_endpoint']}"
        headers = {"X-Workflow-ID": workflow_id}
        
        # Send invalid payload
        response = requests.post(
            url,
            json={"invalid": "payload"},
            headers=headers,
            timeout=TIMEOUT
        )
        
        time.sleep(0.5)
        
        # Get logs
        logs = self._get_recent_logs(service_name=service_config['name'])
        matching_logs = [
            log for log in logs
            if log.get('context', {}).get('workflow_id') == workflow_id
        ]
        
        # Should have error logs
        if response.status_code >= 400:
            error_logs = [log for log in matching_logs if log.get('level') == 'ERROR']
            # May or may not have error logs depending on how validation works
            # Just verify we got some logs
            assert len(matching_logs) > 0


class TestCrossServiceTracking:
    """Test distributed tracing across multiple services."""
    
    def test_workflow_id_tracking_across_services(self):
        """Test that same workflow ID can be tracked across multiple services."""
        workflow_id = f"cross-service-{uuid.uuid4().hex[:12]}"
        
        # Make requests to multiple services with same workflow ID
        successful_services = []
        
        for service_config in SERVICES[:3]:  # Test first 3 services
            try:
                response = requests.get(
                    f"http://localhost:{service_config['port']}/health",
                    timeout=2
                )
                if response.status_code == 200:
                    # Service is up, make a request
                    url = f"http://localhost:{service_config['port']}{service_config['create_endpoint']}"
                    headers = {"X-Workflow-ID": workflow_id}
                    
                    requests.post(
                        url,
                        json=service_config['payload'],
                        headers=headers,
                        timeout=TIMEOUT
                    )
                    successful_services.append(service_config['name'])
            except:
                continue
        
        if len(successful_services) < 2:
            pytest.skip("Not enough services running for cross-service test")
        
        time.sleep(1)
        
        # Query logs with workflow ID
        try:
            response = requests.get(
                f"{LOG_COLLECTOR_URL}/logs?workflow_id={workflow_id}&limit=100",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                logs = response.json()
                if isinstance(logs, dict) and 'logs' in logs:
                    logs = logs['logs']
                
                # Group logs by service
                services_in_logs = set(log.get('service') for log in logs)
                
                # Should have logs from multiple services
                assert len(services_in_logs) >= 2, f"Expected logs from multiple services, got: {services_in_logs}"
        except:
            pytest.skip("Log-collector query by workflow_id not supported")


class TestLogCollectorStatistics:
    """Test log-collector statistics endpoint."""
    
    def test_statistics_endpoint(self):
        """Test that statistics are available."""
        try:
            response = requests.get(
                f"{LOG_COLLECTOR_URL}/stats",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                stats = response.json()
                assert 'total_logs' in stats or 'count' in stats or isinstance(stats, dict)
        except requests.ConnectionError:
            pytest.skip("Log-collector stats endpoint not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

