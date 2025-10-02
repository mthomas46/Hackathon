# Audit & Verification Test Runners

Comprehensive testing framework for the LLM Documentation Ecosystem audit and verification capabilities.

## Overview

This directory contains executable test runners that prove all audit and verification features work correctly and can be run against specific services or the entire ecosystem.

## Test Runners

### 1. Audit Test Runner (`audit_test_runner.py`)

General-purpose audit test runner that validates all audit endpoints with dry-run support.

```bash
# Run all audit tests
python scripts/test/audit_test_runner.py

# Run tests for specific service
python scripts/test/audit_test_runner.py --service user-store

# Run specific test category
python scripts/test/audit_test_runner.py --category docker-compose

# Run against running ecosystem
python scripts/test/audit_test_runner.py --live

# Generate detailed report
python scripts/test/audit_test_runner.py --report audit_report.json
```

### 2. Service Audit Tester (`service_audit_tester.py`)

Service-specific audit testing with comparative analysis.

```bash
# Test all services
python scripts/test/service_audit_tester.py

# Test specific service
python scripts/test/service_audit_tester.py --service user-store

# Test multiple services
python scripts/test/service_audit_tester.py --services user-store doc_store orchestrator

# Generate comparative report
python scripts/test/service_audit_tester.py --compare --output comparison.json

# Run with health checks
python scripts/test/service_audit_tester.py --health-check

# Run performance tests
python scripts/test/service_audit_tester.py --performance
```

### 3. Ecosystem Audit Runner (`ecosystem_audit_runner.py`)

Full ecosystem audit with comprehensive reporting and continuous monitoring.

```bash
# Run full ecosystem audit
python scripts/test/ecosystem_audit_runner.py

# Run with specific focus areas
python scripts/test/ecosystem_audit_runner.py --focus docker infrastructure

# Generate comprehensive report
python scripts/test/ecosystem_audit_runner.py --report ecosystem_audit_2024.json

# Run against staging environment
python scripts/test/ecosystem_audit_runner.py --env staging

# Continuous monitoring mode
python scripts/test/ecosystem_audit_runner.py --continuous --interval 300

# CI/CD mode (non-interactive)
python scripts/test/ecosystem_audit_runner.py --ci
```

## Features Tested

### Audit Endpoints
- ✅ **Docker Compose Validation** - Port conflicts, shared volumes, build contexts
- ✅ **Configuration Drift Detection** - Runtime vs config file differences
- ✅ **Production Readiness Validation** - Infrastructure and API health checks
- ✅ **Configuration Standardization** - Port mapping and environment variable consistency
- ✅ **Docker Standardization** - Dockerfile best practices and Compose optimization

### Service-Specific Testing
- ✅ **Individual Service Audit** - Per-service configuration validation
- ✅ **Comparative Analysis** - Cross-service performance and health comparison
- ✅ **Health Monitoring** - Service availability and response times
- ✅ **Performance Benchmarking** - Request latency and throughput metrics

### Ecosystem-Wide Testing
- ✅ **Infrastructure Validation** - Docker daemon, networks, volumes
- ✅ **Cross-Service Dependencies** - Service interaction and dependency validation
- ✅ **Configuration Consistency** - Environment-wide config standardization
- ✅ **Production Readiness Assessment** - End-to-end ecosystem health

## Test Execution Modes

### 1. Unit Testing Mode
```bash
# Run against mocked services (fast, for development)
python scripts/test/audit_test_runner.py
```

### 2. Integration Testing Mode
```bash
# Run against running ecosystem (comprehensive, for staging)
python scripts/test/audit_test_runner.py --live
```

### 3. CI/CD Mode
```bash
# Automated testing with pass/fail exit codes
python scripts/test/ecosystem_audit_runner.py --ci
```

### 4. Continuous Monitoring Mode
```bash
# Background monitoring with alerting
python scripts/test/ecosystem_audit_runner.py --continuous --interval 300
```

## Test Results & Reporting

### Console Output
```
🚀 Starting Audit Test Suite
   Target URL: http://localhost:8080
   Target Category: docker-compose

✅ docker-compose: 5 services, 2 issues, 0 conflicts

🎯 Overall Results:
   Total Tests: 1
   Passed: 1
   Failed: 0
   Success Rate: 100.0%
```

### JSON Reports
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_tests": 5,
  "passed_tests": 4,
  "failed_tests": 1,
  "execution_time": 45.2,
  "results": [
    {
      "test_name": "docker-compose",
      "category": "docker-compose",
      "success": true,
      "execution_time": 5.2,
      "response": {
        "docker_compose_validation": {
          "success": true,
          "services_count": 5,
          "issues": []
        }
      }
    }
  ]
}
```

### Ecosystem Audit Reports
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "environment": "production",
  "duration": 120.5,
  "infrastructure_health": {
    "docker_daemon": true,
    "containers_running": 12,
    "containers_healthy": 10
  },
  "overall_score": 0.87,
  "readiness_level": "development_ready",
  "recommendations": [
    "Address 2 failed services",
    "Fix Docker Compose validation issues"
  ]
}
```

## Service Targeting

### Available Services
- **Core Services**: `orchestrator`, `doc_store`, `analysis-service`, `source-agent`, `frontend`
- **Infrastructure**: `redis`, `log-collector`
- **Integrations**: `llm-gateway`, `summarizer-hub`, `github-mcp`, `bedrock-proxy`

### Targeting Examples
```bash
# Test core services only
python scripts/test/service_audit_tester.py --services orchestrator doc_store analysis-service

# Test all services
python scripts/test/service_audit_tester.py --all

# Compare specific services
python scripts/test/service_audit_tester.py --services user-store doc_store --compare
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Ecosystem Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup ecosystem
        run: docker-compose up -d
      - name: Run audit tests
        run: python scripts/test/ecosystem_audit_runner.py --ci --env testing
      - name: Upload audit report
        uses: actions/upload-artifact@v3
        with:
          name: audit-report
          path: ecosystem_audit_*.json
```

### Exit Codes
- `0`: Tests passed successfully
- `1`: Tests failed or critical issues detected
- `130`: Tests interrupted by user

## Monitoring & Alerting

### Continuous Monitoring
```bash
# Monitor every 5 minutes with alerts
python scripts/test/ecosystem_audit_runner.py --continuous --interval 5
```

### Alert Integration
The monitoring system can integrate with:
- **Slack** - Real-time notifications
- **PagerDuty** - Critical issue alerts
- **Email** - Summary reports
- **Custom Webhooks** - Integration with other systems

## Performance Considerations

### Test Execution Times
- **Unit Tests**: < 30 seconds
- **Integration Tests**: 1-5 minutes
- **Full Ecosystem Audit**: 2-10 minutes
- **Continuous Monitoring**: Configurable intervals

### Parallel Execution
- Service tests run in parallel by default
- Configurable worker pool size
- Sequential fallback available

## Troubleshooting

### Common Issues

#### Service Not Available
```bash
# Check if meta-orchestrator is running
docker-compose ps | grep meta

# Start the service
docker-compose up -d meta-orchestrator
```

#### Tests Failing
```bash
# Run with verbose output
python scripts/test/audit_test_runner.py --verbose

# Check service logs
docker-compose logs meta-orchestrator
```

#### Network Issues
```bash
# Test basic connectivity
curl http://localhost:8080/docs

# Check Docker networks
docker network ls
```

## Extending the Test Framework

### Adding New Test Categories
1. Add test logic to `AuditTestRunner` class
2. Update `test_categories` dictionary
3. Add corresponding API endpoint
4. Update result analysis methods

### Adding New Service Tests
1. Extend service test methods in `ServiceAuditTester`
2. Add service-specific validation logic
3. Update comparison algorithms
4. Add service to available services list

### Custom Reporting
1. Extend result data structures
2. Add custom analysis methods
3. Implement new output formats
4. Integrate with external reporting systems

## Dependencies

- `requests` - HTTP client for API testing
- `docker` (optional) - Direct Docker API access
- `pytest` (optional) - For unit test integration
- `schedule` - For continuous monitoring

## Dry-Run Functionality

### Overview

Dry-run modes allow testing audit and standardization features without making actual changes to configurations or services. This provides safe testing and preview capabilities.

### Supported Dry-Run Modes

#### 1. **Validate Mode** (`--mode validate`)
- Only validates configurations
- Shows potential issues
- No changes are made or shown

#### 2. **Dry-Run Mode** (`--mode dry_run`)
- Shows what changes would be made
- Includes "DRY RUN:" prefixes in output
- No actual changes are applied

#### 3. **Apply Mode** (`--mode apply`)
- Actually applies changes
- Shows real modification results
- Use with caution in production

### Dry-Run Test Runner (`dry_run_test_runner.py`)

Specialized runner for testing dry-run functionality across services.

```bash
# Test dry-run functionality for user-store
python scripts/test/dry_run_test_runner.py --service user-store

# Test all modes for user-store
python scripts/test/dry_run_test_runner.py --service user-store --all-modes

# Compare dry-run vs apply results
python scripts/test/dry_run_test_runner.py --service user-store --compare-modes

# Generate detailed comparison report
python scripts/test/dry_run_test_runner.py --service user-store --generate-comparison comparison.json

# Test all services
python scripts/test/dry_run_test_runner.py --all-services
```

### Features Tested in Dry-Run Mode

#### Configuration Standardization
- ✅ Port mapping validation and updates
- ✅ Environment variable standardization
- ✅ Configuration file format consistency
- ✅ Safe preview of all changes

#### Docker Standardization
- ✅ Dockerfile best practices validation
- ✅ Docker Compose configuration standardization
- ✅ Volume mount optimization
- ✅ Health check configuration

#### Safety Mechanisms
- ✅ Dry-run prefixes in all output
- ✅ No actual file modifications in dry-run mode
- ✅ Clear differentiation between modes
- ✅ Warning messages for dry-run operations

### Dry-Run Test Results

#### Successful Dry-Run Output
```
✅ Dry-Run Test Results: user-store
   Mode: dry_run
   Execution Time: 0.15s
   Dry-Run Correct: True

   Dry-Run Changes:
   • DRY RUN: Would update server.port from 5150 to 5151
   • DRY RUN: Would standardize environment variable naming
```

#### Safety Validation
- ✅ Changes include "DRY RUN:" prefixes
- ✅ No actual modifications made
- ✅ Warnings about hypothetical nature
- ✅ Clear mode differentiation

## Security Considerations

- Tests run with service account permissions
- No sensitive data in test reports
- Network isolation for testing environments
- Audit logging for compliance
- Dry-run modes prevent accidental changes
