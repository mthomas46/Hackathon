# 🔄 CI/CD Integration Examples

## Overview

Integrate the Unified API Dashboard into your CI/CD pipelines for automated API testing, validation, and monitoring.

## GitHub Actions Integration

### Basic API Testing Workflow

```yaml
name: API Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  api-tests:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install requests python-dotenv

    - name: Run API Tests
      env:
        DASHBOARD_URL: ${{ secrets.DASHBOARD_URL }}
        API_USERNAME: ${{ secrets.API_USERNAME }}
        API_PASSWORD: ${{ secrets.API_PASSWORD }}
      run: |
        python .github/scripts/api_integration_test.py

    - name: Generate Test Report
      if: always()
      run: |
        python .github/scripts/generate_test_report.py
```

### API Testing Script

Create `.github/scripts/api_integration_test.py`:

```python
#!/usr/bin/env python3
"""
API Integration Tests for CI/CD Pipeline
"""

import os
import sys
import json
import requests
from datetime import datetime


class APITestRunner:
    def __init__(self, dashboard_url, username, password):
        self.dashboard_url = dashboard_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()

    def authenticate(self):
        """Authenticate and get JWT token."""
        auth_url = f"{self.dashboard_url}/api/auth/login"
        response = self.session.post(auth_url, json={
            "username": self.username,
            "password": self.password
        })

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = data['data']['token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                print("✅ Authentication successful")
                return True

        print(f"❌ Authentication failed: {response.status_code}")
        return False

    def test_service_health(self):
        """Test service health checks."""
        print("\n🔍 Testing Service Health...")

        health_url = f"{self.dashboard_url}/api/health/services"
        response = self.session.get(health_url)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                services = data['data']
                healthy_count = sum(1 for s in services if s['status'] == 'healthy')
                total_count = len(services)

                print(f"✅ Service Health: {healthy_count}/{total_count} services healthy")

                # Fail CI if any critical services are down
                critical_down = [s for s in services
                               if s.get('critical', False) and s['status'] != 'healthy']

                if critical_down:
                    print(f"❌ Critical services down: {[s['service'] for s in critical_down]}")
                    return False

                return True

        print(f"❌ Health check failed: {response.status_code}")
        return False

    def test_api_endpoints(self, service_configs):
        """Test API endpoints for specified services."""
        print("\n🧪 Testing API Endpoints...")

        test_url = f"{self.dashboard_url}/api/testing/execute"
        results = []

        for service_config in service_configs:
            service_name = service_config['name']
            endpoints = service_config.get('endpoints', [])

            print(f"  Testing {service_name}...")

            for endpoint in endpoints:
                test_request = {
                    "service_name": service_name,
                    "endpoint_path": endpoint['path'],
                    "method": endpoint.get('method', 'GET'),
                    "headers": endpoint.get('headers', {}),
                    "params": endpoint.get('params', {}),
                    "body": endpoint.get('body')
                }

                response = self.session.post(test_url, json=test_request)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        test_result = data['data']
                        status = "✅ PASS" if test_result['status'] == 'completed' else "❌ FAIL"
                        print(f"    {endpoint['path']}: {status}")
                        results.append({
                            'service': service_name,
                            'endpoint': endpoint['path'],
                            'status': test_result['status'],
                            'response_time': test_result.get('response', {}).get('response_time')
                        })
                    else:
                        print(f"    {endpoint['path']}: ❌ FAIL - {data.get('message')}")
                        results.append({
                            'service': service_name,
                            'endpoint': endpoint['path'],
                            'status': 'failed',
                            'error': data.get('message')
                        })
                else:
                    print(f"    {endpoint['path']}: ❌ FAIL - HTTP {response.status_code}")
                    results.append({
                        'service': service_name,
                        'endpoint': endpoint['path'],
                        'status': 'failed',
                        'http_status': response.status_code
                    })

        # Check if all tests passed
        failed_tests = [r for r in results if r['status'] != 'completed']
        if failed_tests:
            print(f"❌ {len(failed_tests)} endpoint tests failed")
            return False

        print(f"✅ All {len(results)} endpoint tests passed")
        return True

    def validate_api_specs(self, services_to_validate):
        """Validate OpenAPI specifications."""
        print("\n📋 Validating API Specifications...")

        validate_url = f"{self.dashboard_url}/api/tools/validate-spec"
        results = []

        for service_name in services_to_validate:
            # Get service spec (assuming it's available via discovery)
            discovery_url = f"{self.dashboard_url}/api/discovery/services"
            response = self.session.get(discovery_url)

            if response.status_code == 200:
                services = response.json().get('data', [])
                service_info = next((s for s in services if s['service_name'] == service_name), None)

                if service_info:
                    # Get the OpenAPI spec
                    spec_url = f"{service_info['service_url']}/openapi.json"
                    try:
                        spec_response = requests.get(spec_url, timeout=10)
                        if spec_response.status_code == 200:
                            spec = spec_response.json()

                            # Validate with dashboard
                            validate_response = self.session.post(validate_url, json={
                                "service_name": service_name,
                                "openapi_spec": spec
                            })

                            if validate_response.status_code == 200:
                                result = validate_response.json()
                                if result.get('success'):
                                    validation = result['data']
                                    if validation['valid']:
                                        print(f"  ✅ {service_name}: Valid ({validation['compliance_score']}% compliance)")
                                        results.append({
                                            'service': service_name,
                                            'valid': True,
                                            'score': validation['compliance_score']
                                        })
                                    else:
                                        print(f"  ❌ {service_name}: Invalid - {len(validation['errors'])} errors")
                                        results.append({
                                            'service': service_name,
                                            'valid': False,
                                            'errors': validation['errors']
                                        })
                                else:
                                    print(f"  ❌ {service_name}: Validation failed - {result.get('message')}")
                            else:
                                print(f"  ❌ {service_name}: HTTP {validate_response.status_code}")
                        else:
                            print(f"  ❌ {service_name}: Could not fetch OpenAPI spec")
                    except Exception as e:
                        print(f"  ❌ {service_name}: Error - {str(e)}")
                else:
                    print(f"  ❌ {service_name}: Service not found in discovery")
            else:
                print(f"❌ Could not get service discovery data")

        # Check validation results
        invalid_specs = [r for r in results if not r['valid']]
        if invalid_specs:
            print(f"❌ {len(invalid_specs)} API specs failed validation")
            return False

        print(f"✅ All {len(results)} API specs validated successfully")
        return True

    def run_integration_tests(self, test_config):
        """Run comprehensive integration tests."""
        print("🚀 Starting API Integration Tests...")

        # Authenticate
        if not self.authenticate():
            return False

        success = True

        # Test service health
        if not self.test_service_health():
            success = False

        # Test API endpoints
        service_configs = test_config.get('services', [])
        if service_configs and not self.test_api_endpoints(service_configs):
            success = False

        # Validate API specs
        services_to_validate = test_config.get('validate_specs', [])
        if services_to_validate and not self.validate_api_specs(services_to_validate):
            success = False

        # Generate test report
        self.generate_test_report(test_config)

        return success

    def generate_test_report(self, test_config):
        """Generate test report for CI/CD."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_run': os.getenv('GITHUB_RUN_ID', 'local'),
            'commit': os.getenv('GITHUB_SHA', 'unknown'),
            'branch': os.getenv('GITHUB_REF', 'unknown'),
            'config': test_config,
            'status': 'completed'
        }

        with open('api_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print("📊 Test report generated: api_test_report.json")


def main():
    """Main test runner."""
    dashboard_url = os.getenv('DASHBOARD_URL', 'http://localhost:8000')
    username = os.getenv('API_USERNAME', 'testuser')
    password = os.getenv('API_PASSWORD', 'testpass')

    # Test configuration
    test_config = {
        'services': [
            {
                'name': 'user-service',
                'endpoints': [
                    {'path': '/health', 'method': 'GET'},
                    {'path': '/users', 'method': 'GET', 'params': {'limit': 10}}
                ]
            },
            {
                'name': 'order-service',
                'endpoints': [
                    {'path': '/health', 'method': 'GET'},
                    {'path': '/orders', 'method': 'GET'}
                ]
            }
        ],
        'validate_specs': ['user-service', 'order-service']
    }

    runner = APITestRunner(dashboard_url, username, password)

    if runner.run_integration_tests(test_config):
        print("✅ All API integration tests passed!")
        sys.exit(0)
    else:
        print("❌ API integration tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

## Jenkins Pipeline Integration

### Jenkinsfile for API Testing

```groovy
pipeline {
    agent any

    environment {
        DASHBOARD_URL = credentials('dashboard-url')
        API_USERNAME = credentials('api-username')
        API_PASSWORD = credentials('api-password')
    }

    stages {
        stage('API Integration Tests') {
            steps {
                script {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install requests python-dotenv
                        python3 scripts/api_integration_test.py
                    '''
                }
            }
            post {
                always {
                    junit 'api_test_report.xml'
                    archiveArtifacts artifacts: 'api_test_report.json', fingerprint: true
                }
            }
        }

        stage('API Specification Validation') {
            steps {
                script {
                    sh '''
                        . venv/bin/activate
                        python3 scripts/validate_api_specs.py
                    '''
                }
            }
        }

        stage('Performance Regression Test') {
            steps {
                script {
                    sh '''
                        . venv/bin/activate
                        python3 scripts/performance_test.py
                    '''
                }
            }
            post {
                always {
                    publishHTML target: [
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'performance_reports',
                        reportFiles: 'index.html',
                        reportName: 'Performance Report'
                    ]
                }
            }
        }
    }

    post {
        always {
            script {
                // Send results to dashboard
                sh '''
                    curl -X POST ${DASHBOARD_URL}/api/analytics/test-results \\
                        -H "Authorization: Bearer ${API_TOKEN}" \\
                        -H "Content-Type: application/json" \\
                        -d @api_test_report.json
                '''
            }
        }
        failure {
            script {
                // Create incident in dashboard
                sh '''
                    curl -X POST ${DASHBOARD_URL}/api/incidents \\
                        -H "Authorization: Bearer ${API_TOKEN}" \\
                        -H "Content-Type: application/json" \\
                        -d '{
                            "title": "CI/CD Pipeline Failed",
                            "description": "Automated API tests failed",
                            "severity": "high",
                            "source": "jenkins"
                        }'
                '''
            }
        }
    }
}
```

## Docker Integration

### Docker Compose for Testing

```yaml
version: '3.8'

services:
  api-tests:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      - DASHBOARD_URL=http://dashboard:8000
      - API_USERNAME=testuser
      - API_PASSWORD=testpass
    depends_on:
      - dashboard
    volumes:
      - ./test-results:/app/test-results
    command: pytest tests/integration/ -v --tb=short --junitxml=test-results/results.xml

  dashboard:
    image: unified-api-dashboard:latest
    environment:
      - SERVICE_PORT=8000
      - REDIS_HOST=redis
    ports:
      - "8000:8000"
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  user-service:
    # Your microservice
    image: user-service:latest
    environment:
      - SERVICE_PORT=8081
    ports:
      - "8081:8081"

  order-service:
    # Your microservice
    image: order-service:latest
    environment:
      - SERVICE_PORT=8082
    ports:
      - "8082:8082"
```

### Test Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install test dependencies
RUN pip install pytest pytest-asyncio httpx requests

CMD ["pytest", "tests/integration/", "-v"]
```

## Kubernetes Integration

### Kubernetes Job for API Testing

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: api-integration-tests
spec:
  template:
    spec:
      containers:
      - name: api-tests
        image: your-registry/api-tests:latest
        env:
        - name: DASHBOARD_URL
          value: "http://dashboard-service:8000"
        - name: API_USERNAME
          valueFrom:
            secretKeyRef:
              name: api-credentials
              key: username
        - name: API_PASSWORD
          valueFrom:
            secretKeyRef:
              name: api-credentials
              key: password
        volumeMounts:
        - name: test-results
          mountPath: /app/test-results
      volumes:
      - name: test-results
        persistentVolumeClaim:
          claimName: test-results-pvc
      restartPolicy: Never
```

## Monitoring Integration

### Prometheus Metrics Collection

```python
#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for API Dashboard
"""

import time
import requests
from prometheus_client import start_http_server, Gauge, Counter, Histogram


class APIMetricsExporter:
    def __init__(self, dashboard_url, username, password):
        self.dashboard_url = dashboard_url
        self.session = requests.Session()

        # Authenticate
        self.authenticate(username, password)

        # Prometheus metrics
        self.api_health = Gauge('api_service_health', 'API service health status', ['service'])
        self.api_response_time = Histogram('api_response_time', 'API response time', ['service', 'endpoint'])
        self.api_requests_total = Counter('api_requests_total', 'Total API requests', ['service', 'method', 'status'])
        self.api_errors_total = Counter('api_errors_total', 'Total API errors', ['service', 'error_type'])

    def authenticate(self, username, password):
        """Authenticate with dashboard."""
        response = self.session.post(f"{self.dashboard_url}/api/auth/login", json={
            "username": username,
            "password": password
        })

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token = data['data']['token']
                self.session.headers['Authorization'] = f'Bearer {token}'

    def collect_metrics(self):
        """Collect metrics from dashboard."""
        try:
            # Get service health
            health_response = self.session.get(f"{self.dashboard_url}/api/health/services")
            if health_response.status_code == 200:
                health_data = health_response.json()
                if health_data.get('success'):
                    for service in health_data['data']:
                        health_value = 1 if service['status'] == 'healthy' else 0
                        self.api_health.labels(service=service['service']).set(health_value)

            # Get usage analytics
            usage_response = self.session.get(f"{self.dashboard_url}/api/analytics/usage/overview")
            if usage_response.status_code == 200:
                usage_data = usage_response.json()
                if usage_data.get('success'):
                    # Set usage counters (this would need historical data tracking)
                    pass

            # Get error analytics
            error_response = self.session.get(f"{self.dashboard_url}/api/analytics/errors/overview")
            if error_response.status_code == 200:
                error_data = error_response.json()
                if error_data.get('success'):
                    # Set error counters
                    pass

        except Exception as e:
            print(f"Error collecting metrics: {e}")

    def run(self):
        """Run the metrics exporter."""
        start_http_server(8000)
        print("Prometheus metrics server started on port 8000")

        while True:
            self.collect_metrics()
            time.sleep(60)  # Collect every minute


if __name__ == '__main__':
    import os

    dashboard_url = os.getenv('DASHBOARD_URL', 'http://localhost:8000')
    username = os.getenv('API_USERNAME')
    password = os.getenv('API_PASSWORD')

    exporter = APIMetricsExporter(dashboard_url, username, password)
    exporter.run()
```

## Slack/Teams Integration

### Automated Alerts and Reports

```python
#!/usr/bin/env python3
"""
Slack Integration for API Dashboard Alerts
"""

import os
import json
import requests
from datetime import datetime


class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_alert(self, title, message, color="danger", fields=None):
        """Send alert to Slack."""
        payload = {
            "attachments": [
                {
                    "title": title,
                    "text": message,
                    "color": color,
                    "fields": fields or [],
                    "footer": "Unified API Dashboard",
                    "ts": datetime.now().timestamp()
                }
            ]
        }

        response = requests.post(self.webhook_url, json=payload)
        return response.status_code == 200

    def send_health_alert(self, service, status, response_time=None):
        """Send service health alert."""
        color = "good" if status == "healthy" else "danger"

        fields = []
        if response_time:
            fields.append({
                "title": "Response Time",
                "value": f"{response_time}ms",
                "short": True
            })

        return self.send_alert(
            f"Service Health Alert: {service}",
            f"Service {service} is {status}",
            color=color,
            fields=fields
        )

    def send_test_results(self, test_results):
        """Send test results summary."""
        passed = test_results.get('passed', 0)
        failed = test_results.get('failed', 0)
        total = passed + failed

        if failed == 0:
            color = "good"
            title = f"✅ All {total} API tests passed"
        else:
            color = "danger"
            title = f"❌ {failed}/{total} API tests failed"

        fields = [
            {"title": "Passed", "value": str(passed), "short": True},
            {"title": "Failed", "value": str(failed), "short": True},
            {"title": "Success Rate", "value": ".1f", "short": True}
        ]

        return self.send_alert(title, "API integration test results", color=color, fields=fields)


class APIDashboardMonitor:
    def __init__(self, dashboard_url, username, password, slack_webhook):
        self.dashboard_url = dashboard_url
        self.session = requests.Session()
        self.slack = SlackNotifier(slack_webhook)
        self.authenticate(username, password)

    def authenticate(self, username, password):
        """Authenticate with dashboard."""
        response = self.session.post(f"{self.dashboard_url}/api/auth/login", json={
            "username": username,
            "password": password
        })

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token = data['data']['token']
                self.session.headers['Authorization'] = f'Bearer {token}'

    def monitor_health(self):
        """Monitor service health and send alerts."""
        response = self.session.get(f"{self.dashboard_url}/api/health/services")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                for service in data['data']:
                    service_name = service['service']
                    status = service['status']

                    # Alert on status changes (would need state tracking in production)
                    if status != 'healthy':
                        self.slack.send_health_alert(
                            service_name,
                            status,
                            service.get('response_time')
                        )

    def send_daily_report(self):
        """Send daily API usage report."""
        # Get usage analytics
        response = self.session.get(f"{self.dashboard_url}/api/analytics/usage/overview")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                usage = data['data']

                fields = [
                    {"title": "Total Requests", "value": str(usage['total_requests']), "short": True},
                    {"title": "Unique Users", "value": str(usage['unique_users']), "short": True},
                    {"title": "Services Used", "value": str(usage['services_used']), "short": True},
                    {"title": "Peak Hour", "value": str(usage['peak_usage_hour']), "short": True}
                ]

                self.slack.send_alert(
                    "📊 Daily API Usage Report",
                    "Summary of API usage for the past 24 hours",
                    color="good",
                    fields=fields
                )

    def run_monitoring_loop(self):
        """Run continuous monitoring."""
        import time

        print("Starting API dashboard monitoring...")

        while True:
            try:
                self.monitor_health()
                time.sleep(300)  # Check every 5 minutes

                # Send daily report at midnight
                now = datetime.now()
                if now.hour == 0 and now.minute < 5:  # Within first 5 minutes of midnight
                    self.send_daily_report()
                    time.sleep(300)  # Don't send again for 5 minutes

            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(60)  # Wait a minute before retrying


if __name__ == '__main__':
    dashboard_url = os.getenv('DASHBOARD_URL')
    username = os.getenv('API_USERNAME')
    password = os.getenv('API_PASSWORD')
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')

    monitor = APIDashboardMonitor(dashboard_url, username, password, slack_webhook)
    monitor.run_monitoring_loop()
```

## Summary

These integration examples show how to:

1. **Automate API Testing** in CI/CD pipelines
2. **Validate API Specifications** during builds
3. **Monitor Service Health** continuously
4. **Collect Metrics** for observability
5. **Send Alerts** to communication platforms
6. **Generate Reports** for stakeholders

The Unified API Dashboard serves as the central hub for all API-related operations in your CI/CD and DevOps workflows!
