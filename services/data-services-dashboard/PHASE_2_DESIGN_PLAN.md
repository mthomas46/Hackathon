# Phase 2: Design & Planning - data-services-dashboard

**Service**: data-services-dashboard  
**Type**: Streamlit Dashboard  
**Date**: October 9, 2025  
**Status**: 🎯 In Progress

---

## 🎯 Design Philosophy

### **Approach**: Modular by Feature (NOT DDD Layers)

**Rationale**: 
- Streamlit dashboards are **visualization-centric**, not business-logic-centric
- Code organization should match the **execution model** (script re-runs)
- **Practical modularity** beats artificial layer separation

**Key Principles**:
1. ✅ Organize by **feature** (data fetching, metrics, visualization)
2. ✅ Keep functions **small and testable**
3. ✅ **Separate concerns** without over-engineering
4. ✅ Maintain **Streamlit idioms** (caching, session state)
5. ✅ **Testable** data processing, **visual** UI components

---

## 📁 Target File Structure

### **Current** (Monolithic)
```
data-services-dashboard/
└── app.py (868 lines)  # Everything in one file
```

### **Proposed** (Modular by Feature)
```
data-services-dashboard/
├── app.py (100 lines)                    # Main entry point
│   └── Imports, page config, main() function
│
├── config.py (50 lines)                  # Configuration management
│   ├── DashboardConfig class
│   ├── Load from env vars
│   └── Default values
│
├── data/ (250 lines total)
│   ├── __init__.py
│   ├── fetcher.py (100 lines)           # Log fetching
│   │   └── fetch_logs() with caching
│   ├── parser.py (100 lines)            # Data parsing
│   │   └── parse_log_entry(), validate_log()
│   └── models.py (50 lines)             # Pydantic models
│       └── LogEntry, MetricsSummary
│
├── metrics/ (100 lines total)
│   ├── __init__.py
│   └── calculator.py (100 lines)        # Metric calculations
│       └── calculate_metrics(), aggregate_by_service()
│
├── visualization/ (400 lines total)
│   ├── __init__.py
│   ├── overview.py (80 lines)           # Overview tab
│   ├── performance.py (80 lines)        # Performance tab
│   ├── operations.py (80 lines)         # Operations tab
│   ├── workflows.py (120 lines)         # Workflows tab (complex)
│   └── errors.py (80 lines)             # Errors tab
│
├── utils/ (50 lines total)
│   ├── __init__.py
│   └── formatting.py (50 lines)         # Helper utilities
│       └── format_duration(), truncate_workflow_id()
│
├── tests/ (500+ lines total)
│   ├── __init__.py
│   ├── conftest.py (100 lines)          # Shared fixtures
│   ├── unit/
│   │   ├── test_data_fetcher.py
│   │   ├── test_data_parser.py
│   │   ├── test_metrics_calculator.py
│   │   └── test_utils_formatting.py
│   ├── integration/
│   │   └── test_log_collector_integration.py
│   └── functional/
│       └── test_dashboard_rendering.py
│
├── requirements.txt (10 deps)           # Streamlined
├── requirements-test.txt                # Test dependencies
├── Dockerfile                           # NEW: Streamlit container
├── docker-compose.yml (updated)         # Proper dependencies
├── .dockerignore                        # NEW: Exclude unnecessary files
├── config.yaml (updated)                # Dashboard-specific config
├── pytest.ini                           # NEW: Test configuration
├── README.md (updated)                  # Enhanced documentation
└── DEPLOYMENT_GUIDE.md                  # NEW: How to deploy
```

**Lines of Code Breakdown**:
- app.py: 100 (from 868) → -768 lines ✅
- data/: 250
- metrics/: 100
- visualization/: 400
- utils/: 50
- tests/: 500+
- **Total**: ~1,400 lines (including 500+ test lines)

**Quality Improvement**:
- Separation of concerns ✅
- Each file < 150 lines ✅
- Testable modules ✅
- Clear responsibilities ✅

---

## 🔧 Module Design

### **1. app.py** (Main Entry Point)

**Responsibility**: Streamlit app initialization and orchestration

**Design**:
```python
#!/usr/bin/env python3
"""
Datastore Operations Dashboard
Main entry point for Streamlit application.
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import load_config
from data.fetcher import fetch_logs
from data.parser import parse_logs
from metrics.calculator import calculate_metrics
from visualization import (
    render_overview_tab,
    render_performance_tab,
    render_operations_tab,
    render_workflows_tab,
    render_errors_tab
)


def main():
    """Main dashboard application."""
    # Page configuration
    st.set_page_config(
        page_title="Datastore Operations Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    # Load configuration
    config = load_config()
    
    # Sidebar filters
    service_filter = st.sidebar.selectbox("Service", config.services)
    time_range = st.sidebar.selectbox("Time Range", config.time_ranges)
    
    # Auto-refresh
    refresh_interval = st.sidebar.select_slider(
        "Auto-refresh (seconds)",
        options=[0, 5, 10, 30, 60],
        value=10
    )
    if refresh_interval > 0:
        st_autorefresh(interval=refresh_interval * 1000, key="refresh")
    
    # Fetch and parse data
    with st.spinner("Fetching logs..."):
        raw_logs = fetch_logs(
            url=config.log_collector_url,
            service=service_filter,
            limit=time_range
        )
        logs = parse_logs(raw_logs)
    
    # Calculate metrics
    metrics = calculate_metrics(logs)
    
    # Display metrics
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Operations", metrics.total_operations)
    with col2:
        st.metric("Successful", metrics.successful_operations)
    # ... etc
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "⏱️ Performance", "🔍 Operations",
        "🌊 Workflows", "⚠️ Errors"
    ])
    
    with tab1:
        render_overview_tab(logs, metrics)
    with tab2:
        render_performance_tab(logs)
    # ... etc


if __name__ == "__main__":
    main()
```

**Tests**: Functional tests for main flow

---

### **2. config.py** (Configuration Management)

**Responsibility**: Load and manage dashboard configuration

**Design**:
```python
"""Configuration management for dashboard."""
import os
from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DashboardConfig(BaseSettings):
    """Dashboard configuration from environment."""
    
    # Log Collector
    log_collector_url: str = "http://localhost:8104"
    
    # Services to monitor
    default_services: List[str] = [
        "doc_store",
        "prompt_store",
        "external-service-store",
        "memory-agent"
    ]
    
    # Time ranges
    time_ranges: List[str] = [
        "Last 100 operations",
        "Last 500 operations",
        "Last 1000 operations"
    ]
    
    # Cache settings
    cache_ttl: int = 5  # seconds
    
    class Config:
        env_prefix = "DASHBOARD_"
        case_sensitive = False


def load_config() -> DashboardConfig:
    """Load dashboard configuration."""
    return DashboardConfig()
```

**Benefits**:
- ✅ Environment-based configuration
- ✅ Type-safe with Pydantic
- ✅ Easy to test with mock config

---

### **3. data/fetcher.py** (Log Fetching)

**Responsibility**: Fetch logs from log-collector with caching

**Design**:
```python
"""Log fetching from log-collector service."""
import streamlit as st
import httpx
from typing import List, Dict, Any, Optional


@st.cache_data(ttl=5)
def fetch_logs(
    url: str,
    service: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch logs from log-collector with caching.
    
    Args:
        url: Log collector base URL
        service: Optional service filter
        limit: Maximum number of logs
        
    Returns:
        List of log entries
        
    Raises:
        httpx.HTTPError: If request fails
    """
    params = {"limit": limit}
    if service and service != "All":
        params["service"] = service
    
    try:
        response = httpx.get(
            f"{url}/logs",
            params=params,
            timeout=5.0
        )
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except httpx.RequestError as e:
        st.error(f"Failed to fetch logs: {e}")
        return []
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return []
```

**Tests**: Unit tests with mocked HTTP responses

---

### **4. data/parser.py** (Data Parsing)

**Responsibility**: Parse and validate log entries

**Design**:
```python
"""Log parsing and validation."""
from datetime import datetime, timezone
from typing import Dict, List, Any
from .models import LogEntry


def parse_log_entry(log: Dict[str, Any]) -> LogEntry:
    """
    Parse a log entry into structured data.
    
    Args:
        log: Raw log dictionary from log-collector
        
    Returns:
        Parsed and validated LogEntry
    """
    context = log.get("context", {})
    return LogEntry(
        timestamp=datetime.fromisoformat(log.get("timestamp", datetime.now(timezone.utc).isoformat())),
        service=log.get("service", "unknown"),
        level=log.get("level", "INFO"),
        message=log.get("message", ""),
        operation_type=context.get("operation_type", "unknown"),
        method=context.get("method", ""),
        path=context.get("path", ""),
        status_code=context.get("status_code"),
        duration_ms=context.get("duration_ms"),
        success=context.get("success"),
        phase=context.get("phase", ""),
        workflow_id=context.get("workflow_id", "")
    )


def parse_logs(raw_logs: List[Dict[str, Any]]) -> List[LogEntry]:
    """Parse a list of logs."""
    return [parse_log_entry(log) for log in raw_logs]


def validate_log(log: Dict[str, Any]) -> bool:
    """Validate log structure."""
    required_fields = ["timestamp", "service", "level"]
    return all(field in log for field in required_fields)
```

**Tests**: Unit tests for parsing logic

---

### **5. data/models.py** (Pydantic Models)

**Responsibility**: Type-safe data models

**Design**:
```python
"""Data models for dashboard."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """Parsed log entry."""
    timestamp: datetime
    service: str
    level: str
    message: str
    operation_type: str
    method: str
    path: str
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    phase: str = ""
    workflow_id: str = ""


class MetricsSummary(BaseModel):
    """Aggregate metrics."""
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_duration_ms: float
    error_rate: float
    operations_per_service: Dict[str, int] = Field(default_factory=dict)
```

**Benefits**:
- ✅ Type safety
- ✅ Validation
- ✅ Easy testing

---

### **6. metrics/calculator.py** (Metrics Calculation)

**Responsibility**: Calculate aggregate metrics

**Design**:
```python
"""Metric calculation logic."""
from typing import List
from collections import defaultdict
from data.models import LogEntry, MetricsSummary


def calculate_metrics(logs: List[LogEntry]) -> MetricsSummary:
    """
    Calculate aggregate metrics from logs.
    
    Args:
        logs: List of parsed log entries
        
    Returns:
        Metrics summary
    """
    if not logs:
        return MetricsSummary(
            total_operations=0,
            successful_operations=0,
            failed_operations=0,
            avg_duration_ms=0.0,
            error_rate=0.0
        )
    
    completed = [l for l in logs if l.phase == "complete"]
    successful = [l for l in completed if l.success is True]
    failed = [l for l in completed if l.success is False]
    
    durations = [l.duration_ms for l in completed if l.duration_ms is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    
    ops_by_service = defaultdict(int)
    for log in completed:
        ops_by_service[log.service] += 1
    
    error_rate = (len(failed) / len(completed) * 100) if completed else 0.0
    
    return MetricsSummary(
        total_operations=len(completed),
        successful_operations=len(successful),
        failed_operations=len(failed),
        avg_duration_ms=avg_duration,
        error_rate=error_rate,
        operations_per_service=dict(ops_by_service)
    )
```

**Tests**: Unit tests with sample data

---

### **7. visualization/*.py** (Tab Rendering)

**Responsibility**: Render each dashboard tab

**Design** (example for overview.py):
```python
"""Overview tab rendering."""
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import List
from data.models import LogEntry, MetricsSummary


def render_overview_tab(logs: List[LogEntry], metrics: MetricsSummary):
    """
    Render the overview tab.
    
    Args:
        logs: Parsed log entries
        metrics: Calculated metrics
    """
    col1, col2 = st.columns(2)
    
    with col1:
        render_operations_by_service(metrics)
    
    with col2:
        render_operation_types(logs)
    
    render_activity_timeline(logs)


def render_operations_by_service(metrics: MetricsSummary):
    """Render pie chart of operations by service."""
    st.markdown("#### 🏢 Operations by Service")
    
    if not metrics.operations_per_service:
        st.info("No operation data available")
        return
    
    df = pd.DataFrame([
        {"Service": service, "Operations": count}
        for service, count in metrics.operations_per_service.items()
    ])
    
    fig = px.pie(
        df,
        values="Operations",
        names="Service",
        hole=0.4
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


# ... other rendering functions
```

**Tests**: Functional tests (mock Streamlit, verify data transformation)

---

## 🧪 Testing Strategy

### **Test Pyramid** (Dashboard-Adapted)

```
         /\
        /  \       E2E/Visual (10%)
       /____\      - Manual testing
      /      \     - Visual regression
     /  Func  \    Functional (20%)
    /__________\   - Tab rendering logic
   /            \  - Dashboard flow
  /   Unit (70%) \ Unit (70%)
 /________________\- Data parsing, metrics
                   - HTTP mocking
```

### **Unit Tests** (70% - 200+ tests)

**Target Coverage**: 80%+

**Test Files**:
1. `test_data_fetcher.py` (30 tests)
   - Mock HTTP responses
   - Cache behavior
   - Error handling

2. `test_data_parser.py` (40 tests)
   - Parse valid logs
   - Handle malformed data
   - Validation logic

3. `test_metrics_calculator.py` (60 tests)
   - Calculate metrics correctly
   - Handle empty data
   - Edge cases (all success, all failures)

4. `test_utils_formatting.py` (20 tests)
   - Format durations
   - Truncate workflow IDs
   - Helper functions

5. `test_config.py` (15 tests)
   - Load from env vars
   - Default values
   - Validation

**Example Test**:
```python
def test_calculate_metrics_with_mixed_results():
    """Test metrics calculation with mixed success/failure."""
    logs = [
        LogEntry(
            timestamp=datetime.now(timezone.utc),
            service="doc_store",
            phase="complete",
            success=True,
            duration_ms=100.0,
            # ... other fields
        ),
        LogEntry(
            timestamp=datetime.now(timezone.utc),
            service="doc_store",
            phase="complete",
            success=False,
            duration_ms=50.0,
            # ... other fields
        )
    ]
    
    metrics = calculate_metrics(logs)
    
    assert metrics.total_operations == 2
    assert metrics.successful_operations == 1
    assert metrics.failed_operations == 1
    assert metrics.error_rate == 50.0
    assert metrics.avg_duration_ms == 75.0
```

### **Integration Tests** (20% - 30 tests)

**Test Files**:
1. `test_log_collector_integration.py` (30 tests)
   - Fetch logs from real log-collector
   - Handle connection failures
   - Timeout behavior
   - Parse real responses

**Example Test**:
```python
@pytest.mark.integration
def test_fetch_logs_from_log_collector():
    """Integration test with log-collector service."""
    config = load_config()
    logs = fetch_logs(
        url=config.log_collector_url,
        service=None,
        limit=10
    )
    
    assert isinstance(logs, list)
    if logs:
        assert "timestamp" in logs[0]
        assert "service" in logs[0]
```

### **Functional Tests** (10% - 20 tests)

**Test Files**:
1. `test_dashboard_rendering.py` (20 tests)
   - Test tab rendering with sample data
   - Verify chart generation
   - Check error handling

**Note**: Streamlit testing is limited - focus on data transformation, not visual output

---

## 🐳 Docker Design

### **Dockerfile** (Streamlit-Optimized)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY data/ ./data/
COPY metrics/ ./metrics/
COPY visualization/ ./visualization/
COPY utils/ ./utils/
COPY app.py .
COPY config.py .

# Streamlit configuration
RUN mkdir -p /root/.streamlit
RUN echo '\
[server]\n\
port = 8501\n\
address = 0.0.0.0\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
' > /root/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **docker-compose.yml** (Updated)

```yaml
version: '3.8'

services:
  data-services-dashboard:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: data-services-dashboard
    
    ports:
      - "8501:8501"
    
    environment:
      - DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104
      - DASHBOARD_CACHE_TTL=5
    
    depends_on:
      log-collector:
        condition: service_healthy
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    restart: unless-stopped
    
    networks:
      - hackathon_default
  
  log-collector:
    image: log-collector:latest
    container_name: log-collector
    ports:
      - "8104:8104"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8104/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default

networks:
  hackathon_default:
    driver: bridge
```

---

## 📦 Dependencies Design

### **requirements.txt** (Streamlined)

```python
# Production dependencies for data-services-dashboard
# Last Updated: October 9, 2025
# Type: Streamlit Dashboard

# Core Dashboard Framework
streamlit>=1.28.0
streamlit-autorefresh>=1.0.0

# Data Visualization
plotly>=5.17.0

# Data Processing
pandas>=2.0.0

# HTTP Client
httpx>=0.27.0

# Configuration & Validation
pydantic>=2.6.0
pydantic-settings>=2.2.0
pyyaml>=6.0.0

# Utilities
python-dotenv>=1.0.0
```

**Removed** (26 → 10 deps):
- FastAPI, Uvicorn (not using)
- Redis, aioredis (no caching needed beyond Streamlit's)
- aiohttp, aiofiles (not using async file ops)
- prometheus-client (not implementing metrics)
- questionary, prompt-toolkit, rich (no CLI)
- structlog (simple logging sufficient)
- altair (using Plotly)
- numpy (included in pandas)

### **requirements-test.txt**

```python
# Test dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.12.0
httpx>=0.27.0
faker>=20.0.0
```

---

## 📊 Quality Gates

### **Phase Completion Criteria**

**Phase 2** (Design & Planning) ✅:
- [x] File structure designed
- [x] Module responsibilities defined
- [x] Testing strategy planned
- [x] Dockerfile designed
- [x] Dependencies streamlined

**Phase 3** (Implementation):
- [ ] Code modularized into separate files
- [ ] Configuration management implemented
- [ ] Type hints added throughout
- [ ] Dockerfile created

**Phase 4** (Testing):
- [ ] Unit tests written (80% coverage)
- [ ] Integration tests written
- [ ] Functional tests written

**Phase 5** (Documentation):
- [ ] README updated
- [ ] Deployment guide created
- [ ] Development guide created

**Phase 6** (Finalization):
- [ ] All tests passing
- [ ] Docker deployment validated
- [ ] Documentation complete

---

## 📋 Migration Strategy

### **Step-by-Step Refactoring**

**Step 1**: Create new file structure (keep old app.py)
**Step 2**: Extract configuration → `config.py`
**Step 3**: Extract data fetching → `data/fetcher.py`
**Step 4**: Extract data parsing → `data/parser.py`
**Step 5**: Extract metrics → `metrics/calculator.py`
**Step 6**: Extract visualizations → `visualization/*.py`
**Step 7**: Update `app.py` to import from modules
**Step 8**: Test thoroughly
**Step 9**: Delete old code
**Step 10**: Create Dockerfile

**Risk Mitigation**:
- Keep old `app.py` as backup
- Test each extraction step
- Use Git branches for safety

---

## ✅ Phase 2 Complete

**Status**: Design plan created ✅  
**Next**: Phase 3 (Implementation)  
**Estimated Effort**: 6-8 hours

---

**Date**: October 9, 2025  
**Status**: Phase 2 Complete

