# Dashboard Validation & Health Monitoring

## Overview

Comprehensive validation and health monitoring system for the Ecosystem MCP Dashboard, ensuring all datasources are connected, configurations are correct, and services are healthy.

---

## 🎯 Features Implemented

### 1. Health Monitoring (`utils/health_monitor.py`)

Real-time health monitoring for all dashboard datasources with:

- **HealthStatus dataclass**: Structured health information
  - Name, status, latency, timestamp
  - Error messages and details
  - Status types: `healthy`, `degraded`, `unhealthy`, `unknown`

- **HealthMonitor class**: Comprehensive monitoring
  - Check API health (sync and async)
  - Check individual datasources
  - Check all datasources at once
  - Track health history (up to 100 checks)
  - Calculate overall system status
  - Measure average latency
  - Calculate uptime percentages

- **Monitored Datasources**:
  - Ecosystem MCP API
  - PostgreSQL
  - Redis
  - Docker containers
  - Diagnostics endpoints

### 2. Configuration Validation (`utils/config_validator.py`)

Automated validation of dashboard configuration:

- **ValidationResult dataclass**: Structured validation results
  - Check name, passed/failed status
  - Descriptive messages
  - Detailed information

- **ConfigValidator class**: Multiple validation checks
  - Environment variables
  - API connectivity
  - API endpoints availability
  - Page imports
  - Docker connectivity
  - Datasources health

### 3. Validation Script (`validate_dashboard.py`)

Command-line tool for comprehensive validation:

```bash
python3 validate_dashboard.py
# or with custom API URL
API_BASE_URL=http://localhost:8000 python3 validate_dashboard.py
```

**Validates**:
- ✅ Environment variables
- ✅ API connectivity
- ✅ Critical API endpoints
- ✅ Docker connectivity
- ✅ Datasource health (Redis, PostgreSQL, ChromaDB)
- ✅ Page imports

**Output**:
- Detailed results for each check
- Pass/fail counts
- Recommendations for failures
- Exit code 0 for success, 1 for failures

### 4. Sidebar Health Widget (`app.py`)

Real-time connection status in dashboard sidebar:

- **Overall Status**: Visual indicator (🟢/🟡/🔴)
- **Expandable Details**: Individual datasource status
  - Name and status icon
  - Latency (ms or seconds)
  - Error messages (if any)
- **Refresh Button**: Manual status refresh
- **Auto-updates**: Status checks on every page load

---

## 🧪 Test Suite

### Unit Tests (21 tests, all passing)

**Config Validation Tests** (`test_config_validation.py`):
- Validator initialization
- Environment variable validation
- Page import validation
- ValidationResult dataclass
- API connectivity with multiple URLs
- Full validation run
- ValidationResult without details

**Health Monitor Tests** (`test_health_monitor.py`):
- HealthStatus dataclass creation
- HealthStatus with errors and details
- HealthMonitor initialization
- API health check (sync)
- Datasource health check
- All datasources check
- Overall status calculation
- Status color mapping
- Health history limit
- Average latency calculation
- Uptime percentage calculation

### Integration Tests (`test_integration.py`)

Tests requiring live API (9 tests):
- API accessibility
- Health endpoint JSON response
- OpenAPI spec accessibility
- All datasources check with live API
- Latency measurement
- History tracking
- Full validation with live API
- API endpoints validation
- Datasources validation

**Run Tests**:
```bash
# Unit tests only (no API required)
pytest tests/ -m unit -v

# Integration tests (requires live API)
pytest tests/ -m integration -v

# All tests
pytest tests/ -v
```

---

## 📊 Usage

### In Dashboard

The health widget appears automatically in the sidebar:

1. **Overall Status**: Shows at a glance if system is healthy
2. **Click "View Details"**: Expand to see individual datasource status
3. **Refresh Button**: Manually refresh connection status
4. **Color Coding**:
   - 🟢 Healthy
   - 🟡 Degraded
   - 🔴 Unhealthy
   - ⚪ Unknown

### Validation Script

Run before deploying or when troubleshooting:

```bash
cd services/ecosystem-mcp-dashboard

# Run validation
python3 validate_dashboard.py

# With custom API URL
API_BASE_URL=http://localhost:8000 python3 validate_dashboard.py
```

### In Code

```python
from utils.health_monitor import HealthMonitor
from utils.config_validator import ConfigValidator

# Health monitoring
monitor = HealthMonitor("http://localhost:8000", timeout=5.0)
results = monitor.check_all_datasources()
overall = monitor.get_overall_status(results)

# Configuration validation
validator = ConfigValidator()
results, all_passed = validator.run_all_validations("http://localhost:8000")
```

---

## 🔍 Validation Checks

### Environment Variables
- `API_BASE_URL`: Required
- `STREAMLIT_SERVER_PORT`: Optional (default: 8501)
- `STREAMLIT_SERVER_HEADLESS`: Optional (default: true)

### API Connectivity
- Health endpoint reachable
- Returns HTTP 200
- Valid JSON response

### API Endpoints
- `/health`
- `/api/v1/diagnostics/health`
- `/api/v1/containers`
- `/api/v1/redis/info`
- `/api/v1/postgres/info`
- `/openapi.json`

### Page Imports
All 14 dashboard pages:
- home
- health
- diagnostics
- config_viewer
- logs_viewer
- api_explorer
- containers
- redis_explorer
- postgres_explorer
- rag
- documents
- cache
- metrics
- settings

### Docker Connectivity
- Docker API accessible via ecosystem-mcp
- Can list containers

### Datasources
- PostgreSQL: Accessible and responding
- Redis: Accessible and responding
- ChromaDB: Accessible via diagnostics

---

## 📈 Health Monitoring Features

### Status Types

1. **Healthy** (🟢): Service is fully operational
2. **Degraded** (🟡): Service is running but with issues
3. **Unhealthy** (🔴): Service is down or not responding
4. **Unknown** (⚪): Cannot determine status

### Metrics Tracked

- **Latency**: Response time in milliseconds
- **History**: Last 100 health checks
- **Average Latency**: Calculated from history
- **Uptime Percentage**: Per datasource
- **Overall Status**: Aggregated from all datasources

### History Management

- Maintains last 100 health checks
- Automatic pruning when limit reached
- Used for trends and statistics

---

## 🛠️ Troubleshooting

### Validation Failures

**Environment Variables Missing**:
```bash
export API_BASE_URL=http://host.docker.internal:8000
```

**API Connectivity Failed**:
- Check if ecosystem-mcp service is running
- Verify API_BASE_URL is correct
- For host access: use `http://host.docker.internal:8000`
- For direct access: use `http://localhost:8000`

**Page Imports Failed**:
- Check if all page files exist in `pages/` directory
- Verify no syntax errors in page files
- Check Python import statements

**Docker Connectivity Failed**:
- Ensure Docker socket is mounted in docker-compose
- Verify ecosystem-mcp has `/var/run/docker.sock` volume

**Datasources Unhealthy**:
- Check if services are running in docker-compose
- Verify network connectivity
- Check service logs

### Health Widget Issues

**Status Not Updating**:
- Click "Refresh Status" button
- Reload the page
- Check browser console for errors

**All Services Unknown**:
- API is likely down or unreachable
- Check API_BASE_URL in sidebar
- Verify ecosystem-mcp service is running

**High Latency**:
- Normal: <100ms
- Acceptable: 100-500ms
- Slow: 500-1000ms
- Problem: >1000ms

---

## 📁 File Structure

```
services/ecosystem-mcp-dashboard/
├── utils/
│   ├── __init__.py
│   ├── health_monitor.py         # Health monitoring utilities
│   └── config_validator.py       # Configuration validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # pytest configuration
│   ├── test_config_validation.py # Config validation tests
│   ├── test_health_monitor.py    # Health monitor tests
│   └── test_integration.py       # Integration tests
├── validate_dashboard.py         # Validation script
├── pytest.ini                    # pytest configuration
└── app.py                        # Updated with health widget
```

---

## ✅ Test Results

### Unit Tests
```
21 passed, 9 deselected in 1.21s
```

**Test Coverage**:
- ConfigValidator: 9 tests
- HealthMonitor: 12 tests
- All passing ✅

### Integration Tests
```
Requires live API to run
9 tests covering:
- API connectivity
- Health endpoint responses
- OpenAPI spec
- Health monitoring with live data
- Configuration validation with live API
```

---

## 🚀 Quick Start

### 1. Run Validation
```bash
cd services/ecosystem-mcp-dashboard
python3 validate_dashboard.py
```

### 2. Run Tests
```bash
# Unit tests (fast, no API required)
pytest tests/ -m unit -v

# All tests
pytest tests/ -v
```

### 3. Access Dashboard
```bash
open http://localhost:8501
```

### 4. Check Sidebar
- Look for "📊 Connection Status"
- Expand "📋 View Details" for full status
- Click "🔄 Refresh Status" to update

---

## 🎯 Benefits

### For Developers
- ✅ Automated validation before deployment
- ✅ Comprehensive test suite
- ✅ Easy debugging with detailed error messages
- ✅ CLI tool for quick checks

### For Users
- ✅ Real-time connection status in sidebar
- ✅ Visual indicators (color-coded)
- ✅ Detailed error messages
- ✅ Manual refresh capability

### For Operations
- ✅ Health monitoring with history
- ✅ Uptime percentage tracking
- ✅ Latency measurements
- ✅ Overall system status

---

## 📖 API Reference

### HealthMonitor

```python
class HealthMonitor:
    def __init__(self, api_base_url: str, timeout: float = 5.0)
    def check_api_health_sync(self) -> HealthStatus
    def check_datasource(self, name: str, endpoint: str) -> HealthStatus
    def check_all_datasources(self) -> Dict[str, HealthStatus]
    def get_overall_status(self, results: Dict[str, HealthStatus]) -> str
    def get_status_color(self, status: str) -> str
    def get_average_latency(self) -> float
    def get_uptime_percentage(self, datasource: str) -> float
```

### ConfigValidator

```python
class ConfigValidator:
    def __init__(self)
    def validate_environment_variables(self) -> ValidationResult
    def validate_api_connectivity(self, api_base_url: str) -> ValidationResult
    def validate_api_endpoints(self, api_base_url: str) -> ValidationResult
    def validate_page_imports(self) -> ValidationResult
    def validate_docker_connectivity(self, api_base_url: str) -> ValidationResult
    def validate_datasources(self, api_base_url: str) -> ValidationResult
    def run_all_validations(self, api_base_url: str) -> Tuple[List[ValidationResult], bool]
```

---

## 🔄 Continuous Monitoring

The health widget in the sidebar provides continuous monitoring:

1. **On Page Load**: Checks all datasources
2. **Manual Refresh**: Click button to recheck
3. **History Tracking**: Maintains last 100 checks
4. **Trend Analysis**: Average latency and uptime

This ensures users are always aware of the system's health status.

---

**Dashboard URL**: http://localhost:8501  
**Validation Script**: `python3 validate_dashboard.py`  
**Test Suite**: `pytest tests/ -v`

