# 🛠️ Orchestrator Test Suite Setup Guide

**Complete Setup and Configuration Guide for the Orchestrator Test Suite**

This guide provides step-by-step instructions for setting up the orchestrator test suite, including environment configuration, dependency installation, and troubleshooting common issues.

## 📋 Table of Contents

- [🎯 Prerequisites](#-prerequisites)
- [🚀 Quick Setup](#-quick-setup)
- [🔧 Detailed Installation](#-detailed-installation)
- [⚙️ Configuration](#-configuration)
- [🧪 Test Execution](#-test-execution)
- [🐛 Troubleshooting](#-troubleshooting)
- [🔄 Updating Tests](#-updating-tests)
- [📊 Monitoring & Reporting](#-monitoring--reporting)

## 🎯 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 4GB+ RAM recommended
- **Disk Space**: 2GB+ free space
- **Network**: Internet connection for dependencies

### Required Software
```bash
# Python package manager (pip is usually included with Python)
python --version  # Should be 3.8+
pip --version     # Should be 20.0+

# Git (for repository operations)
git --version

# Optional: Virtual environment manager
# conda --version  # or
# virtualenv --version
```

### Project Structure
```
Hackathon/
├── services/
│   └── orchestrator/
│       ├── main.py
│       ├── modules/
│       └── ...
├── tests/
│   └── orchestrator/
│       ├── test_*.py
│       ├── conftest.py
│       └── test_runner.py
└── requirements.txt
```

## 🚀 Quick Setup

### One-Command Setup (Recommended)
```bash
# 1. Clone and navigate to project
cd /Users/mykalthomas/Documents/work/Hackathon

# 2. Set PYTHONPATH (critical!)
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# 3. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-xdist

# 4. Verify setup
python -c "import orchestrator; print('✅ Orchestrator import successful')"

# 5. Run basic test
python -m pytest tests/orchestrator/test_orchestrator_features.py::TestOrchestratorWorkflowManagement::test_workflow_creation -v
```

### Automated Setup Script
```bash
#!/bin/bash
# setup_orchestrator_tests.sh

echo "🚀 Setting up Orchestrator Test Suite..."

# Navigate to project directory
cd /Users/mykalthomas/Documents/work/Hackathon

# Set PYTHONPATH
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Install core dependencies
echo "📦 Installing core dependencies..."
pip install -r requirements.txt

# Install test dependencies
echo "🧪 Installing test dependencies..."
pip install pytest pytest-asyncio pytest-cov pytest-xdist black isort mypy

# Verify imports
echo "🔍 Verifying imports..."
python -c "import orchestrator; print('✅ Orchestrator import successful')"
python -c "import pytest; print('✅ Pytest import successful')"

# Run basic test
echo "🧪 Running basic test..."
python -m pytest tests/orchestrator/test_orchestrator_features.py::TestOrchestratorWorkflowManagement::test_workflow_creation -v

echo "🎉 Setup complete! Run 'python tests/orchestrator/test_runner.py' to run all tests."
```

## 🔧 Detailed Installation

### Step 1: Environment Setup
```bash
# Create and activate virtual environment (recommended)
python -m venv orchestrator_env
source orchestrator_env/bin/activate  # On Windows: orchestrator_env\Scripts\activate

# Or using conda
conda create -n orchestrator_env python=3.8
conda activate orchestrator_env
```

### Step 2: PYTHONPATH Configuration
```bash
# Method 1: Export in current session
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Method 2: Add to shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH' >> ~/.zshrc
source ~/.zshrc

# Method 3: Create .env file
echo 'PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH' > .env

# Verify PYTHONPATH
echo $PYTHONPATH
python -c "import sys; print('/Users/mykalthomas/Documents/work/Hackathon/services' in sys.path)"
```

### Step 3: Install Dependencies
```bash
# Install core project dependencies
pip install -r /Users/mykalthomas/Documents/work/Hackathon/requirements.txt

# Install test-specific dependencies
pip install pytest pytest-asyncio pytest-cov pytest-xdist

# Optional: Install development tools
pip install black isort mypy pre-commit

# Verify installations
python -c "import orchestrator, pytest, pytest_asyncio; print('✅ All imports successful')"
```

### Step 4: Database Setup (if required)
```bash
# If using SQLite database
mkdir -p /Users/mykalthomas/Documents/work/Hackathon/data

# Set database path environment variable
export ORCHESTRATOR_DB_PATH=/Users/mykalthomas/Documents/work/Hackathon/data/orchestrator.db

# Initialize database (if needed)
python -c "from orchestrator.modules.workflow_management.repository import WorkflowRepository; repo = WorkflowRepository(); print('✅ Database initialized')"
```

### Step 5: Service Dependencies (if needed)
```bash
# Start required services (Redis, etc.)
# Example for Redis
redis-server &

# Set service URLs
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

## ⚙️ Configuration

### Test Configuration Files

#### pytest.ini
```ini
# pytest.ini - Main pytest configuration
[tool:pytest]
testpaths = tests/orchestrator
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
    -v
asyncio_mode = auto
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    enterprise: marks tests as enterprise features
```

#### conftest.py Configuration
```python
# tests/orchestrator/conftest.py
import pytest
import pytest_asyncio
import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Database configuration
@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    """Create temporary database path."""
    return tmp_path_factory.mktemp("orchestrator") / "test.db"
```

### Environment Variables
```bash
# Required
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Optional
export ORCHESTRATOR_DB_PATH=/tmp/orchestrator_test.db
export REDIS_HOST=localhost
export REDIS_PORT=6379
export LOG_LEVEL=INFO
export TEST_MODE=true

# Performance testing
export PERFORMANCE_TEST_TIMEOUT=300
export CONCURRENT_USERS=10
export LOAD_TEST_DURATION=60
```

### Custom Configuration
```python
# tests/orchestrator/test_config.py
import os

class TestConfig:
    """Test configuration settings."""

    # Database settings
    DB_PATH = os.getenv("ORCHESTRATOR_DB_PATH", "/tmp/orchestrator_test.db")

    # Service URLs
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

    # Test settings
    TEST_TIMEOUT = int(os.getenv("TEST_TIMEOUT", "30"))
    PERFORMANCE_TIMEOUT = int(os.getenv("PERFORMANCE_TEST_TIMEOUT", "300"))

    # Concurrent settings
    MAX_CONCURRENT_USERS = int(os.getenv("CONCURRENT_USERS", "10"))
    LOAD_TEST_DURATION = int(os.getenv("LOAD_TEST_DURATION", "60"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Export configuration
test_config = TestConfig()
```

## 🧪 Test Execution

### Basic Test Running
```bash
# Run all tests
python -m pytest tests/orchestrator/ -v

# Run specific test file
python -m pytest tests/orchestrator/test_orchestrator_features.py -v

# Run specific test class
python -m pytest tests/orchestrator/test_orchestrator_features.py::TestOrchestratorWorkflowManagement -v

# Run specific test method
python -m pytest tests/orchestrator/test_orchestrator_features.py::TestOrchestratorWorkflowManagement::test_workflow_creation -v
```

### Advanced Test Execution
```bash
# Run with coverage
python -m pytest tests/orchestrator/ --cov=orchestrator --cov-report=html

# Run in parallel
python -m pytest tests/orchestrator/ -n auto

# Run with specific markers
python -m pytest tests/orchestrator/ -m "not slow"

# Run with timeout
python -m pytest tests/orchestrator/ --timeout=300

# Run performance tests only
python -m pytest tests/orchestrator/ -k "performance"

# Run with detailed output
python -m pytest tests/orchestrator/ -vv --tb=long
```

### Test Runner Execution
```bash
# Run test runner
python tests/orchestrator/test_runner.py

# Run specific category
python tests/orchestrator/test_runner.py --category unit

# Run smoke tests
python tests/orchestrator/test_runner.py --smoke

# Generate detailed report
python tests/orchestrator/test_runner.py --verbose
```

### Continuous Integration
```bash
# CI mode
export CI=true

# Run tests with CI settings
python -m pytest tests/orchestrator/ \
    --cov=orchestrator \
    --cov-report=xml \
    --junitxml=test-results.xml \
    --tb=short
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Import Errors
```
ModuleNotFoundError: No module named 'orchestrator'
```
**Solution**:
```bash
# Check PYTHONPATH
echo $PYTHONPATH

# Set PYTHONPATH correctly
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Verify path exists
ls /Users/mykalthomas/Documents/work/Hackathon/services/orchestrator/

# Test import
python -c "import sys; sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services'); import orchestrator"
```

#### Issue 2: Async Test Errors
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```
**Solution**:
```python
# Use pytest-asyncio correctly
import pytest_asyncio

@pytest_asyncio.fixture
async def workflow_service():
    service = WorkflowManagementService()
    yield service

@pytest.mark.asyncio
async def test_something(workflow_service):
    # Test code here
    pass
```

#### Issue 3: Database Connection Errors
```
sqlite3.OperationalError: unable to open database file
```
**Solution**:
```bash
# Create database directory
mkdir -p /tmp/orchestrator_test

# Set permissions
chmod 755 /tmp/orchestrator_test

# Set database path
export ORCHESTRATOR_DB_PATH=/tmp/orchestrator_test/orchestrator.db

# Test database creation
python -c "
from orchestrator.modules.workflow_management.repository import WorkflowRepository
import os
os.makedirs('/tmp/orchestrator_test', exist_ok=True)
repo = WorkflowRepository()
print('✅ Database created successfully')
"
```

#### Issue 4: Service Connection Errors
```
ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```
**Solution**:
```bash
# Start Redis service
redis-server &

# Or use Docker
docker run -d -p 6379:6379 redis:alpine

# Set correct host/port
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Test connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6379)
r.ping()
print('✅ Redis connection successful')
"
```

#### Issue 5: Test Timeout Errors
```
pytest-timeout: Timeout after 300 seconds
```
**Solution**:
```bash
# Increase timeout
python -m pytest tests/orchestrator/ --timeout=600

# Or set per test
@pytest.mark.timeout(600)
def test_slow_operation():
    pass

# Run specific slow tests
python -m pytest tests/orchestrator/ -m "slow" --timeout=1200
```

#### Issue 6: Memory Issues
```
MemoryError: Unable to allocate memory
```
**Solution**:
```bash
# Run tests with less parallelism
python -m pytest tests/orchestrator/ -n 2

# Or run sequentially
python -m pytest tests/orchestrator/ -s

# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

#### Issue 7: Coverage Issues
```
CoverageWarning: Module orchestrator was never imported
```
**Solution**:
```bash
# Check PYTHONPATH in coverage
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Run coverage with explicit paths
python -m pytest tests/orchestrator/ \
    --cov=orchestrator \
    --cov-report=html \
    --cov-config=.coveragerc

# Create .coveragerc file
echo "[run]
source = orchestrator
omit =
    */tests/*
    */venv/*" > .coveragerc
```

### Debugging Techniques

#### 1. Verbose Test Output
```bash
# Maximum verbosity
python -m pytest tests/orchestrator/test_problematic.py -vvv

# Show all output
python -m pytest tests/orchestrator/test_problematic.py -s

# Debug specific test
python -m pytest tests/orchestrator/test_problematic.py::TestClass::test_method --pdb
```

#### 2. Log Analysis
```python
# Enable debug logging in test
import logging
logging.basicConfig(level=logging.DEBUG)

@pytest.mark.asyncio
async def test_with_debugging(workflow_service):
    logger = logging.getLogger(__name__)
    logger.debug("Starting test execution")

    try:
        # Test code
        result = await workflow_service.some_operation()
        logger.debug(f"Operation result: {result}")
    except Exception as e:
        logger.exception("Test failed with exception")
        raise
```

#### 3. Performance Profiling
```bash
# Profile test execution
python -c "
import cProfile
import asyncio
from tests.orchestrator.test_problematic import *

async def profile_test():
    # Setup and run test
    pass

cProfile.run('asyncio.run(profile_test())', 'test_profile.prof')
"

# Analyze profile
python -c "
import pstats
p = pstats.Stats('test_profile.prof')
p.sort_stats('cumulative').print_stats(20)
"
```

## 🔄 Updating Tests

### Adding New Tests
```bash
# 1. Create new test file
touch tests/orchestrator/test_new_feature.py

# 2. Write test structure
cat > tests/orchestrator/test_new_feature.py << 'EOF'
import pytest
import pytest_asyncio

class TestNewFeature:
    @pytest_asyncio.fixture
    async def setup_fixture(self):
        # Setup code
        yield resource
        # Cleanup code

    @pytest.mark.asyncio
    async def test_new_functionality(self, setup_fixture):
        # Test code
        assert True
EOF

# 3. Run new test
python -m pytest tests/orchestrator/test_new_feature.py -v

# 4. Add to test runner (if needed)
# Update tests/orchestrator/test_runner.py
```

### Updating Existing Tests
```bash
# 1. Make changes to test file
vim tests/orchestrator/test_orchestrator_features.py

# 2. Run updated tests
python -m pytest tests/orchestrator/test_orchestrator_features.py -v

# 3. Run full test suite to ensure no regressions
python tests/orchestrator/test_runner.py
```

### Test Maintenance
```bash
# Update test dependencies
pip install --upgrade pytest pytest-asyncio pytest-cov

# Clean up old test artifacts
find tests/orchestrator/ -name "*.pyc" -delete
find tests/orchestrator/ -name "__pycache__" -type d -exec rm -rf {} +

# Reformat test code
black tests/orchestrator/
isort tests/orchestrator/

# Type check tests
mypy tests/orchestrator/
```

## 📊 Monitoring & Reporting

### Test Metrics Collection
```python
# tests/orchestrator/test_monitor.py
import pytest
import time
import psutil
import os
from typing import Dict, Any

class TestMonitor:
    """Monitor test execution metrics."""

    def __init__(self):
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "memory_usage": [],
            "test_count": 0,
            "failure_count": 0
        }

    def start_monitoring(self):
        """Start collecting metrics."""
        self.metrics["start_time"] = time.time()
        self.process = psutil.Process(os.getpid())

    def record_metric(self):
        """Record current metrics."""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        self.metrics["memory_usage"].append(memory_mb)

    def stop_monitoring(self):
        """Stop collecting metrics."""
        self.metrics["end_time"] = time.time()

    def get_report(self) -> Dict[str, Any]:
        """Generate monitoring report."""
        duration = self.metrics["end_time"] - self.metrics["start_time"]
        avg_memory = sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"])
        max_memory = max(self.metrics["memory_usage"])

        return {
            "duration_seconds": duration,
            "average_memory_mb": avg_memory,
            "max_memory_mb": max_memory,
            "test_count": self.metrics["test_count"],
            "failure_count": self.metrics["failure_count"]
        }
```

### Automated Reporting
```bash
# Generate test reports
python -m pytest tests/orchestrator/ \
    --cov=orchestrator \
    --cov-report=html \
    --cov-report=xml \
    --junitxml=test-results.xml

# Generate test runner report
python tests/orchestrator/test_runner.py

# View HTML coverage report
open htmlcov/index.html

# View test results
cat test-results.xml
```

### Continuous Monitoring
```bash
# Monitor test execution in real-time
python -c "
import time
import psutil
import os

process = psutil.Process(os.getpid())
print('Monitoring test execution...')

while True:
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent()
    print(f'Memory: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%')
    time.sleep(1)
" &
```

### Performance Baselines
```python
# tests/orchestrator/performance_baselines.py
PERFORMANCE_BASELINES = {
    "workflow_creation": {
        "max_time_seconds": 2.0,
        "target_time_seconds": 1.0,
        "min_time_seconds": 0.5
    },
    "workflow_execution": {
        "max_time_seconds": 5.0,
        "target_time_seconds": 2.0,
        "min_time_seconds": 1.0
    },
    "concurrent_executions": {
        "max_throughput": 10,  # executions per second
        "target_throughput": 20,
        "min_throughput": 5
    },
    "memory_usage": {
        "max_mb": 500,
        "target_mb": 200,
        "min_mb": 100
    }
}

def check_performance_baseline(metric_name: str, actual_value: float) -> Dict[str, Any]:
    """Check if performance metric meets baseline requirements."""
    if metric_name not in PERFORMANCE_BASELINES:
        return {"status": "unknown", "message": f"No baseline for {metric_name}"}

    baseline = PERFORMANCE_BASELINES[metric_name]

    if actual_value <= baseline["target_time_seconds"]:
        return {"status": "excellent", "message": f"Exceeds target: {actual_value}"}
    elif actual_value <= baseline["max_time_seconds"]:
        return {"status": "good", "message": f"Meets requirements: {actual_value}"}
    else:
        return {"status": "poor", "message": f"Below requirements: {actual_value}"}
```

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Set PYTHONPATH (always required!)
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Run all tests
python -m pytest tests/orchestrator/ -v

# Run with coverage
python -m pytest tests/orchestrator/ --cov=orchestrator --cov-report=html

# Run test runner
python tests/orchestrator/test_runner.py

# Debug test
python -m pytest tests/orchestrator/test_file.py::TestClass::test_method --pdb
```

### Common Issues Quick Fix
```bash
# Import issues
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Database issues
mkdir -p /tmp/orchestrator_test
export ORCHESTRATOR_DB_PATH=/tmp/orchestrator_test/orchestrator.db

# Service issues
redis-server &

# Memory issues
python -m pytest tests/orchestrator/ -n 2
```

### Configuration Checklist
- ✅ PYTHONPATH set correctly
- ✅ Dependencies installed
- ✅ Database path configured
- ✅ Service URLs set
- ✅ Test fixtures working
- ✅ Coverage configured

---

**Setup Complete! 🛠️🚀**

Your orchestrator test suite is now fully configured and ready for comprehensive testing. Use this guide as reference for maintenance and troubleshooting.
