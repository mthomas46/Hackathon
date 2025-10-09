# Data Models - data-services-dashboard

**Service**: data-services-dashboard  
**Type**: Streamlit Dashboard  
**Date**: October 9, 2025

---

## ⚠️ Note: Dashboard Data Models (Not DDD Domain)

**Important**: This document describes **data models** for a Streamlit dashboard, **not** a Domain-Driven Design domain model.

**Why No DDD Domain**:
- Dashboards are **visualization-centric**, not business-logic-centric
- No external API consumers (only human users via browser)
- No reusable business logic across multiple contexts
- Data models are for **type safety and validation**, not domain behavior

**What We Have Instead**: Pydantic models for data transformation pipeline

---

## 📊 Data Flow Pipeline

```
Log Collector API
       ↓
  Raw JSON Logs
       ↓
  [Parser] → LogEntry (Pydantic Model)
       ↓
  [Calculator] → MetricsSummary (Pydantic Model)
       ↓
  [Visualizer] → Streamlit Charts
       ↓
    Browser UI
```

---

## 🔧 Data Models

### **1. LogEntry** (Core Data Model)

**Purpose**: Type-safe representation of a parsed log entry

**Module**: `data/models.py`

**Design**:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """
    Parsed log entry from log-collector service.
    
    Represents a single datastore operation logged by a service.
    """
    
    # Metadata
    timestamp: datetime = Field(..., description="When the operation occurred")
    service: str = Field(..., description="Service that performed operation")
    level: str = Field(default="INFO", description="Log level (INFO, WARNING, ERROR)")
    message: str = Field(default="", description="Log message")
    
    # Operation details
    operation_type: str = Field(default="unknown", description="Type (CREATE, READ, UPDATE, DELETE, SEARCH)")
    method: str = Field(default="", description="HTTP method (GET, POST, PUT, DELETE)")
    path: str = Field(default="", description="API endpoint path")
    
    # Metrics
    status_code: Optional[int] = Field(None, description="HTTP status code")
    duration_ms: Optional[float] = Field(None, description="Operation duration in milliseconds")
    success: Optional[bool] = Field(None, description="Whether operation succeeded")
    
    # Tracing
    phase: str = Field(default="", description="Operation phase (start, complete)")
    workflow_id: str = Field(default="", description="Workflow ID for tracing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-09T12:00:00Z",
                "service": "doc_store",
                "level": "INFO",
                "message": "Document created",
                "operation_type": "CREATE",
                "method": "POST",
                "path": "/api/v1/documents",
                "status_code": 201,
                "duration_ms": 15.5,
                "success": True,
                "phase": "complete",
                "workflow_id": "wf_abc123"
            }
        }
```

**Validation Rules**:
- `timestamp`: Must be valid datetime
- `service`: Required, non-empty string
- `operation_type`: Limited to known types (enforced via enum if strict)
- `duration_ms`: Must be non-negative if present
- `status_code`: Must be valid HTTP status if present (100-599)

**Usage**:
```python
# Parsing raw log
raw_log = {"timestamp": "2025-10-09T12:00:00Z", "service": "doc_store", ...}
log_entry = LogEntry(**raw_log)

# Type-safe access
print(log_entry.service)  # IDE autocomplete works!
print(log_entry.duration_ms)  # Optional[float], properly typed
```

---

### **2. MetricsSummary** (Aggregate Metrics)

**Purpose**: Type-safe representation of calculated metrics

**Module**: `data/models.py`

**Design**:
```python
from typing import Dict
from pydantic import BaseModel, Field


class MetricsSummary(BaseModel):
    """
    Aggregate metrics calculated from log entries.
    
    Provides summary statistics for dashboard display.
    """
    
    # Operation counts
    total_operations: int = Field(default=0, description="Total completed operations", ge=0)
    successful_operations: int = Field(default=0, description="Successfully completed operations", ge=0)
    failed_operations: int = Field(default=0, description="Failed operations", ge=0)
    
    # Performance metrics
    avg_duration_ms: float = Field(default=0.0, description="Average operation duration", ge=0.0)
    
    # Quality metrics
    error_rate: float = Field(default=0.0, description="Error rate as percentage", ge=0.0, le=100.0)
    
    # Breakdown by service
    operations_per_service: Dict[str, int] = Field(
        default_factory=dict,
        description="Operation count per service"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_operations": 100,
                "successful_operations": 95,
                "failed_operations": 5,
                "avg_duration_ms": 12.5,
                "error_rate": 5.0,
                "operations_per_service": {
                    "doc_store": 50,
                    "prompt_store": 30,
                    "memory-agent": 20
                }
            }
        }
```

**Validation Rules**:
- `total_operations`: Must be >= 0
- `successful_operations + failed_operations <= total_operations`
- `avg_duration_ms`: Must be >= 0
- `error_rate`: Must be 0-100

**Usage**:
```python
# Calculate metrics
logs = [log_entry1, log_entry2, ...]
metrics = calculate_metrics(logs)

# Type-safe access
st.metric("Total Operations", metrics.total_operations)
st.metric("Error Rate", f"{metrics.error_rate:.1f}%")
```

---

### **3. DashboardConfig** (Configuration)

**Purpose**: Type-safe dashboard configuration

**Module**: `config.py`

**Design**:
```python
from typing import List
from pydantic_settings import BaseSettings


class DashboardConfig(BaseSettings):
    """
    Dashboard configuration loaded from environment.
    """
    
    # Log Collector
    log_collector_url: str = Field(
        default="http://localhost:8104",
        description="Log collector service URL"
    )
    
    # Services to monitor
    default_services: List[str] = Field(
        default_factory=lambda: [
            "doc_store",
            "prompt_store",
            "external-service-store",
            "memory-agent"
        ],
        description="Default services to monitor"
    )
    
    # Time ranges
    time_ranges: List[str] = Field(
        default_factory=lambda: [
            "Last 100 operations",
            "Last 500 operations",
            "Last 1000 operations"
        ],
        description="Available time range options"
    )
    
    # Cache settings
    cache_ttl: int = Field(
        default=5,
        ge=0,
        le=300,
        description="Cache TTL in seconds"
    )
    
    class Config:
        env_prefix = "DASHBOARD_"
        case_sensitive = False
```

**Environment Variables**:
```bash
DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104
DASHBOARD_CACHE_TTL=10
```

---

## 📈 Data Transformation Pipeline

### **Step 1: Fetch** (`data/fetcher.py`)
```
HTTP GET /logs
    ↓
List[Dict[str, Any]]  # Raw JSON from log-collector
```

### **Step 2: Parse** (`data/parser.py`)
```
List[Dict[str, Any]]
    ↓
parse_logs()
    ↓
List[LogEntry]  # Type-safe, validated Pydantic models
```

### **Step 3: Calculate** (`metrics/calculator.py`)
```
List[LogEntry]
    ↓
calculate_metrics()
    ↓
MetricsSummary  # Aggregated metrics
```

### **Step 4: Visualize** (`visualization/*.py`)
```
List[LogEntry] + MetricsSummary
    ↓
pandas DataFrames
    ↓
plotly Figures
    ↓
Streamlit charts
```

---

## 🧪 Testing Data Models

### **Unit Tests** (`tests/unit/test_models.py`)

```python
def test_log_entry_validation():
    """Test LogEntry validates fields correctly."""
    # Valid log entry
    log = LogEntry(
        timestamp=datetime.now(timezone.utc),
        service="doc_store",
        operation_type="CREATE",
        method="POST",
        path="/api/v1/documents",
        status_code=201,
        duration_ms=15.5,
        success=True,
        phase="complete"
    )
    assert log.service == "doc_store"
    assert log.success is True


def test_log_entry_invalid_status_code():
    """Test LogEntry rejects invalid status code."""
    with pytest.raises(ValidationError):
        LogEntry(
            timestamp=datetime.now(timezone.utc),
            service="doc_store",
            status_code=999  # Invalid HTTP status
        )


def test_metrics_summary_calculation():
    """Test MetricsSummary calculates correctly."""
    metrics = MetricsSummary(
        total_operations=100,
        successful_operations=95,
        failed_operations=5,
        avg_duration_ms=12.5,
        error_rate=5.0
    )
    assert metrics.error_rate == 5.0
    assert metrics.total_operations == 100
```

---

## 🔄 Comparison: DDD Domain vs Dashboard Data Models

| Aspect | DDD Domain (REST API) | Dashboard Data Models |
|--------|----------------------|---------------------|
| **Purpose** | Business logic encapsulation | Data transformation & validation |
| **Behavior** | Rich (methods, invariants) | Minimal (data containers) |
| **Reusability** | High (across endpoints) | Low (dashboard-specific) |
| **Lifecycle** | Managed by repository | Transient (created per request) |
| **Validation** | Business rules | Schema/type validation |
| **Persistence** | Often persisted | Never persisted |
| **Example** | `Order.calculateTotal()` | `LogEntry.duration_ms` |

**Key Difference**: 
- **DDD Domain** = Objects with **behavior** (methods, business rules)
- **Dashboard Data** = Objects for **type safety** (schemas, validation)

---

## ✅ Summary

**Data Models for data-services-dashboard**:
1. ✅ `LogEntry` - Parsed log entry (core data model)
2. ✅ `MetricsSummary` - Aggregated metrics
3. ✅ `DashboardConfig` - Configuration settings

**Not DDD Domain Because**:
- ❌ No business logic (just data transformation)
- ❌ No external consumers (only internal to dashboard)
- ❌ No reusable behavior (visualization-specific)

**What We Gain**:
- ✅ Type safety (IDE autocomplete, type checking)
- ✅ Validation (Pydantic ensures data integrity)
- ✅ Documentation (models document data structure)
- ✅ Testing (easy to test with known data)

---

**Date**: October 9, 2025  
**Type**: Data Models (not DDD Domain)  
**Status**: Design Complete

