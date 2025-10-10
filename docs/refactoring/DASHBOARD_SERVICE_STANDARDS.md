# Dashboard Service Standards

**Version**: 1.0.0  
**Created**: October 9, 2025  
**Purpose**: Standards for dashboard/visualization services in the ecosystem  
**Applies To**: Streamlit dashboards, monitoring UIs, admin panels

---

## 🎯 Overview

Dashboard services are **hybrid services** that provide:
1. **Web UI** (Streamlit/React/etc.) for human operators
2. **REST API** for programmatic access and ecosystem integration

**Key Principle**: Dashboards are **"Modular by Feature"** (NOT DDD architecture)

---

## 🏗️ Architecture: "Modular by Feature"

### **Why Not DDD for Dashboards?**

| Aspect | REST API Service | Dashboard Service |
|--------|------------------|-------------------|
| **Purpose** | Business logic + API | Visualization + monitoring |
| **Consumers** | Services (programmatic) | Humans + services (hybrid) |
| **State** | Stateless | Stateful (UI session) |
| **Logic** | Domain business rules | Data transformation + display |
| **Architecture** | DDD + Clean (4 layers) | Modular by Feature |

**Conclusion**: DDD over-engineers dashboards. Use **Modular by Feature** instead.

---

## 📁 Standard Dashboard Structure

```
dashboard-service/
├── app.py (100-150 lines)              # Main entry point (Streamlit/FastAPI)
│   └── Initializes both UI and API
│
├── config.py (50-100 lines)            # Configuration management
│   ├── DashboardConfig (Pydantic Settings)
│   ├── Environment variables
│   └── Default values
│
├── api/ (if using FastAPI alongside Streamlit)
│   ├── __init__.py
│   ├── router.py                       # Standard endpoints
│   │   ├── GET /health
│   │   ├── GET /about-me
│   │   ├── GET /endpoints
│   │   ├── GET /provider-consumer
│   │   └── GET /openapi.json
│   └── models.py                       # API request/response models
│
├── data/                               # Data fetching & processing
│   ├── __init__.py
│   ├── fetcher.py                      # Fetch from external services
│   │   ├── with_retry() decorator
│   │   ├── Connection pooling
│   │   └── Error handling
│   ├── parser.py                       # Parse & validate data
│   ├── models.py                       # Pydantic data models
│   └── validator.py                    # Input validation
│
├── metrics/                            # Metric calculations
│   ├── __init__.py
│   └── calculator.py                   # Aggregate metrics
│
├── visualization/                      # UI rendering (by feature)
│   ├── __init__.py
│   ├── overview.py                     # Overview tab/page
│   ├── performance.py                  # Performance tab/page
│   ├── errors.py                       # Errors tab/page
│   └── [feature].py                    # One file per feature
│
├── utils/                              # Utilities
│   ├── __init__.py
│   ├── formatting.py                   # Display formatting
│   ├── logging_client.py               # Log to log-collector
│   └── retry.py                        # Retry logic
│
├── tests/                              # Comprehensive tests
│   ├── conftest.py                     # Shared fixtures
│   ├── unit/                           # Unit tests (70%)
│   ├── integration/                    # Integration tests (20%)
│   └── functional/                     # Functional tests (10%)
│
├── requirements.txt                    # Production dependencies
├── requirements-test.txt               # Test dependencies
├── Dockerfile                          # Container (Streamlit + FastAPI)
├── docker-compose.yml                  # Multi-service setup
├── pytest.ini                          # Test configuration
├── README.md                           # Service documentation
├── DEPLOYMENT_GUIDE.md                 # Deployment instructions
└── CONFIG.md                           # Configuration reference
```

---

## 🔌 Required Standard Endpoints

**All dashboard services MUST expose REST API endpoints** for ecosystem integration.

### **1. Health Endpoint** ✅

```python
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status, uptime, dependencies
    """
    return {
        "status": "healthy",
        "service": "data-services-dashboard",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime(),
        "dependencies": {
            "log_collector": check_log_collector_health(),
            "ui": "running"
        }
    }
```

### **2. About-Me Endpoint** ✅

```python
@router.get("/about-me")
async def about_me() -> Dict[str, Any]:
    """
    Service descriptor endpoint.
    
    Returns comprehensive information about the dashboard.
    """
    return {
        "service": "data-services-dashboard",
        "version": "1.0.0",
        "type": "dashboard",
        "description": "Real-time monitoring dashboard for datastore operations",
        
        "interfaces": {
            "web_ui": {
                "type": "streamlit",
                "url": "http://localhost:8501",
                "consumers": "human-operators"
            },
            "rest_api": {
                "type": "rest",
                "base_path": "/api/v1",
                "consumers": "monitoring-systems"
            }
        },
        
        "capabilities": [
            "Real-time operation monitoring",
            "Performance visualization",
            "Error analysis",
            "Workflow tracing"
        ],
        
        "dependencies": {
            "providers": [
                {
                    "service": "log-collector",
                    "purpose": "Operation logs and metrics"
                }
            ]
        }
    }
```

### **3. Endpoints Listing** ✅

```python
@router.get("/endpoints")
async def list_endpoints() -> Dict[str, Any]:
    """
    List all API endpoints.
    
    Returns list of available endpoints.
    """
    return {
        "service": "data-services-dashboard",
        "version": "1.0.0",
        "endpoints": [
            {
                "path": "/health",
                "method": "GET",
                "summary": "Health check"
            },
            {
                "path": "/about-me",
                "method": "GET",
                "summary": "Service descriptor"
            },
            {
                "path": "/endpoints",
                "method": "GET",
                "summary": "Endpoint listing"
            },
            {
                "path": "/provider-consumer",
                "method": "GET",
                "summary": "Service relationships"
            },
            {
                "path": "/openapi.json",
                "method": "GET",
                "summary": "OpenAPI specification"
            }
        ]
    }
```

### **4. Provider-Consumer Relationships** ✅

```python
@router.get("/provider-consumer")
async def provider_consumer() -> Dict[str, Any]:
    """
    Service relationship matrix.
    
    Returns provider and consumer relationships.
    """
    return {
        "service": "data-services-dashboard",
        "version": "1.0.0",
        
        "relationships": {
            "providers": [
                {
                    "service": "log-collector",
                    "relationship": "provider",
                    "purpose": "Provides operation logs",
                    "endpoints_used": ["GET /logs"]
                }
            ],
            "consumers": [
                {
                    "service": "monitoring-systems",
                    "relationship": "consumer",
                    "purpose": "Consumes health status",
                    "endpoints_provided": ["/health", "/about-me"]
                },
                {
                    "service": "human-operators",
                    "relationship": "consumer",
                    "purpose": "Uses dashboard UI",
                    "interface": "web-ui"
                }
            ]
        }
    }
```

### **5. OpenAPI Specification** ✅

```python
@router.get("/openapi.json")
async def openapi_spec() -> Dict[str, Any]:
    """
    OpenAPI 3.0 specification.
    
    Returns OpenAPI spec for API endpoints.
    """
    # FastAPI automatically generates this
    return app.openapi()
```

---

## 🔄 Network Resilience & Retry Logic

### **Standard Retry Decorator**

**Required for all external service calls**

```python
from functools import wraps
import time
from typing import Callable, Any
import httpx


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (httpx.RequestError, httpx.HTTPStatusError)
):
    """
    Retry decorator for network calls.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay (exponential backoff)
        exceptions: Exceptions to catch and retry
        
    Example:
        @with_retry(max_attempts=3, delay=1.0)
        def fetch_data():
            return httpx.get("http://service/api")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    
                    print(f"Attempt {attempt}/{max_attempts} failed: {e}")
                    print(f"Retrying in {current_delay}s...")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            raise RuntimeError(f"Failed after {max_attempts} attempts")
        
        return wrapper
    return decorator
```

**Usage**:
```python
@with_retry(max_attempts=3, delay=1.0, backoff=2.0)
def fetch_logs(url: str, params: dict) -> List[Dict]:
    """Fetch logs with automatic retry."""
    response = httpx.get(f"{url}/logs", params=params, timeout=5.0)
    response.raise_for_status()
    return response.json().get("items", [])
```

### **Connection Pooling**

```python
from httpx import Client, Limits

# Create persistent HTTP client with connection pooling
http_client = Client(
    limits=Limits(
        max_connections=10,
        max_keepalive_connections=5
    ),
    timeout=5.0
)

@with_retry(max_attempts=3)
def fetch_with_pool(url: str) -> dict:
    """Fetch using connection pool."""
    response = http_client.get(url)
    response.raise_for_status()
    return response.json()
```

---

## ✅ Input Validation & Controls

### **Pydantic Models for All Data**

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class LogEntry(BaseModel):
    """Validated log entry."""
    
    timestamp: datetime
    service: str = Field(..., min_length=1, max_length=100)
    level: str = Field(..., regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    message: str = Field(default="", max_length=1000)
    
    operation_type: str = Field(
        default="unknown",
        regex="^(CREATE|READ|UPDATE|DELETE|SEARCH|unknown)$"
    )
    method: str = Field(default="", regex="^(GET|POST|PUT|DELETE|PATCH)?$")
    
    status_code: Optional[int] = Field(None, ge=100, le=599)
    duration_ms: Optional[float] = Field(None, ge=0.0)
    
    @validator("duration_ms")
    def validate_duration(cls, v):
        """Validate duration is reasonable."""
        if v is not None and v > 300000:  # > 5 minutes
            raise ValueError("Duration too large")
        return v


class DashboardFilter(BaseModel):
    """Validated dashboard filter input."""
    
    service: Optional[str] = Field(None, max_length=100)
    time_range: str = Field(
        default="Last 100 operations",
        regex="^Last (100|500|1000) operations$"
    )
    operation_type: Optional[str] = Field(
        None,
        regex="^(CREATE|READ|UPDATE|DELETE|SEARCH)$"
    )
```

### **Streamlit Input Validation**

```python
import streamlit as st
from pydantic import ValidationError


def validate_and_apply_filters() -> DashboardFilter:
    """Validate Streamlit sidebar inputs."""
    
    service = st.sidebar.selectbox(
        "Service",
        options=["All"] + config.default_services,
        help="Filter by service name"
    )
    
    time_range = st.sidebar.selectbox(
        "Time Range",
        options=config.time_ranges,
        help="Select time window"
    )
    
    try:
        filters = DashboardFilter(
            service=service if service != "All" else None,
            time_range=time_range
        )
        return filters
    except ValidationError as e:
        st.error(f"Invalid filter configuration: {e}")
        # Return safe defaults
        return DashboardFilter()
```

---

## 📊 Standardized Dashboard Features

### **1. Standard Sidebar Controls** ✅

All dashboards MUST include:

```python
def render_standard_sidebar(config: DashboardConfig):
    """Render standardized sidebar controls."""
    
    # Service filter
    st.sidebar.markdown("## 🔍 Filters")
    service = st.sidebar.selectbox(
        "Service",
        options=["All"] + config.default_services
    )
    
    # Time range
    time_range = st.sidebar.selectbox(
        "Time Range",
        options=config.time_ranges
    )
    
    # Auto-refresh
    st.sidebar.markdown("## 🔄 Auto-Refresh")
    refresh_interval = st.sidebar.select_slider(
        "Interval (seconds)",
        options=[0, 5, 10, 30, 60],
        value=10
    )
    
    # Status indicators
    st.sidebar.markdown("## 📡 Status")
    log_collector_status = check_log_collector()
    st.sidebar.metric(
        "Log Collector",
        "✅ Connected" if log_collector_status else "❌ Disconnected"
    )
    
    return {
        "service": service,
        "time_range": time_range,
        "refresh_interval": refresh_interval
    }
```

### **2. Standard Metrics Display** ✅

```python
def render_standard_metrics(metrics: MetricsSummary):
    """Render standardized metrics row."""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Operations", metrics.total_operations)
    
    with col2:
        st.metric("Successful", metrics.successful_operations)
    
    with col3:
        st.metric(
            "Failed",
            metrics.failed_operations,
            delta=f"-{metrics.error_rate:.1f}%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric("Avg Duration", f"{metrics.avg_duration_ms:.2f}ms")
    
    with col5:
        st.metric("Error Rate", f"{metrics.error_rate:.1f}%")
```

### **3. Standard Error Handling** ✅

```python
def render_with_error_handling(render_func: Callable, *args, **kwargs):
    """Wrapper for consistent error handling."""
    
    try:
        render_func(*args, **kwargs)
    except httpx.RequestError as e:
        st.error(f"🔌 Connection Error: Unable to reach service. {e}")
        st.info("Retrying automatically...")
    except httpx.HTTPStatusError as e:
        st.error(f"⚠️ HTTP Error {e.response.status_code}: {e}")
    except ValidationError as e:
        st.error(f"❌ Data Validation Error: {e}")
    except Exception as e:
        st.error(f"💥 Unexpected Error: {e}")
        st.exception(e)
```

---

## 📝 Logging to Log-Collector

### **Standard Logging Client**

**All dashboards MUST log to log-collector**

```python
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class LogCollectorClient:
    """Client for sending logs to log-collector service."""
    
    def __init__(self, url: str = "http://log-collector:5060"):
        self.url = url
        self.service_name = "data-services-dashboard"
        self.client = httpx.Client(timeout=2.0)
    
    @with_retry(max_attempts=2, delay=0.5)
    def send_log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Send log to log-collector.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            context: Additional context
        """
        try:
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": self.service_name,
                "level": level,
                "message": message,
                "context": context or {}
            }
            
            response = self.client.post(
                f"{self.url}/api/v1/logs",
                json=log_entry
            )
            response.raise_for_status()
        except Exception as e:
            # Logging failures shouldn't break the dashboard
            print(f"Failed to send log: {e}")
    
    def info(self, message: str, **context):
        """Log info message."""
        self.send_log("INFO", message, context)
    
    def warning(self, message: str, **context):
        """Log warning message."""
        self.send_log("WARNING", message, context)
    
    def error(self, message: str, **context):
        """Log error message."""
        self.send_log("ERROR", message, context)


# Initialize global logger
logger = LogCollectorClient()
```

**Usage**:
```python
# Log dashboard events
logger.info("Dashboard started", user="admin")
logger.info("Fetched logs", service="doc_store", count=100)
logger.warning("Connection timeout", service="log-collector", retry=True)
logger.error("Failed to parse log", error=str(e), log_data=log)
```

### **Standard Log Events**

Dashboards MUST log these events:

```python
# Dashboard lifecycle
logger.info("dashboard_started", version="1.0.0")
logger.info("dashboard_stopped")

# Data fetching
logger.info("fetching_logs", service=service, limit=limit)
logger.info("logs_fetched", service=service, count=len(logs), duration_ms=elapsed)
logger.warning("fetch_timeout", service=service, timeout=5.0)
logger.error("fetch_failed", service=service, error=str(e))

# User interactions
logger.info("filter_applied", service=service, time_range=time_range)
logger.info("tab_changed", tab="performance")
logger.info("data_exported", format="csv", rows=len(data))

# Errors
logger.error("parsing_error", log_id=log_id, error=str(e))
logger.error("validation_error", field=field, value=value)
logger.error("unexpected_error", error=str(e), traceback=traceback)
```

---

## 🧪 Dashboard Testing Standards

### **Test Pyramid** (Dashboard-Adapted)

```
       /\
      /  \     Manual/Visual (5%)
     /____\    
    /      \   Functional (25%)
   /________\  - Rendering logic
  /          \ - Tab switching
 /   Unit 70% \Unit Tests (70%)
/______________\- Data processing
```

### **Required Test Coverage**

| Component | Min Coverage | Test Types |
|-----------|--------------|------------|
| `data/fetcher.py` | 90%+ | Unit (mocked HTTP) |
| `data/parser.py` | 90%+ | Unit (validation) |
| `data/models.py` | 100% | Unit (Pydantic) |
| `metrics/calculator.py` | 90%+ | Unit (aggregation) |
| `api/router.py` | 90%+ | Integration (FastAPI TestClient) |
| `visualization/*.py` | 60%+ | Functional (logic, not visual) |
| **Overall** | **80%+** | Mixed |

---

## 🐳 Docker Standards for Dashboards

### **Dockerfile Template**

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
COPY api/ ./api/
COPY utils/ ./utils/
COPY app.py .
COPY config.py .

# Streamlit configuration (if using Streamlit)
RUN mkdir -p /root/.streamlit
RUN echo '\
[server]\n\
port = 8501\n\
address = 0.0.0.0\n\
enableCORS = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
' > /root/.streamlit/config.toml

# Expose ports
EXPOSE 8501  # Streamlit UI
EXPOSE 8080  # FastAPI (if separate)

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run both Streamlit and FastAPI (if needed)
CMD ["python", "app.py"]
```

---

## ✅ Quality Gates for Dashboards

### **Phase 1: Audit**
- [ ] Current structure documented
- [ ] Dependencies analyzed
- [ ] Gaps identified (including missing API endpoints)

### **Phase 2: Design**
- [ ] Modular structure designed (by feature)
- [ ] API endpoints designed (all 5 standard endpoints)
- [ ] Test strategy defined (70/20/10 pyramid)
- [ ] Retry logic planned

### **Phase 3: Implementation**
- [ ] Code modularized
- [ ] API endpoints implemented
- [ ] Retry logic implemented
- [ ] Input validation added
- [ ] Logging client integrated

### **Phase 4: Testing**
- [ ] Unit tests ≥ 70% coverage
- [ ] Integration tests written
- [ ] API endpoint tests pass
- [ ] Retry logic tested

### **Phase 5: Documentation**
- [ ] README comprehensive
- [ ] CONFIG.md created
- [ ] Deployment guide created

### **Phase 6: Configuration**
- [ ] Dockerfile created
- [ ] docker-compose.yml updated
- [ ] Environment-based config

---

## 📚 Related Documents

- [Master Refactoring Plan](./MASTER_REFACTORING_PLAN.md)
- [Master Configuration Registry](./MASTER_CONFIGURATION_REGISTRY.md)
- [AI Agent Execution Guide](./AI_AGENT_EXECUTION_GUIDE.md)

---

**Version**: 1.0.0  
**Date**: October 9, 2025  
**Status**: Active  
**Applies To**: All dashboard/visualization services

