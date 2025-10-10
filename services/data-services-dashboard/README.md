# 📊 Data Services Dashboard - Real-Time Monitoring & Visualization

<!--
AI/LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "data-services-dashboard"
- ports: { ui: 8501, api: 8080 }
- version: "1.0.0"
- status: "refactored"
- architecture: "Hybrid (Streamlit UI + FastAPI REST API)"
- test_coverage: "80%+"
- key_concepts: ["dashboard", "monitoring", "visualization", "streamlit", "fastapi", "hybrid_architecture", "real_time"]
- processing_hints: "Hybrid dashboard with Streamlit UI for humans and FastAPI REST API for systems. Monitors datastore operations across ecosystem."
- cross_references: ["PHASE_1_SERVICE_AUDIT.md", "PHASE_2_DESIGN_PLAN.md"]
- integration_points: ["log-collector", "monitoring-systems", "human-operators"]
- refactoring_date: "2025-10-09"
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Services](../README_SERVICES.md)  
**Tests**: [tests/](./tests/)  
**Refactoring Docs**: [Phase 1](./PHASE_1_SERVICE_AUDIT.md) · [Phase 2](./PHASE_2_DESIGN_PLAN.md)

---

## 📊 Service Status

| Attribute | Value |
|-----------|-------|
| **Status** | ✅ **Production Ready** (Refactored October 2025) |
| **UI Port** | `8501` (Streamlit) |
| **API Port** | `8080` (FastAPI) |
| **Version** | `1.0.0` |
| **Ecosystem Role** | Monitoring & Observability |
| **Architecture** | **Hybrid** (Streamlit UI + FastAPI REST API) |
| **Test Coverage** | **80%+** (105+ comprehensive tests) |
| **Quality Grade** | **A** |
| **Python Version** | 3.12+ |

---

## 🎯 Overview & Purpose

The **Data Services Dashboard** is a **real-time monitoring and visualization platform** for tracking datastore operations across the ecosystem. It provides:

1. **Streamlit Web UI** (8501) - Rich interactive visualizations for human operators
2. **FastAPI REST API** (8080) - Programmatic access for monitoring systems

**Core Mission**: Provide comprehensive observability into datastore service health, performance, errors, and workflows through intuitive visualizations and standard API endpoints.

---

## 🚀 Key Features & Capabilities

### **📊 Interactive Dashboards (5 Tabs)**

#### **1. Overview Tab**
- ✅ **Metrics Row** - Total, successful, failed operations, avg duration, error rate
- ✅ **Operations by Service** - Pie chart showing distribution across services
- ✅ **Operations by Type** - Bar chart of CREATE, READ, UPDATE, DELETE operations
- ✅ **Operations Timeline** - Scatter plot of operations over time

#### **2. Performance Tab**
- ✅ **Performance Metrics** - Average, median (p50), p95, p99, max/min durations
- ✅ **Duration Histogram** - Distribution of operation durations by service
- ✅ **Percentiles by Service** - P95 comparison across services
- ✅ **Duration Timeline** - Scatter plot showing duration trends
- ✅ **Statistics Table** - Min, avg, max, std dev by service

#### **3. Operations Tab**
- ✅ **Search & Filter** - Search messages, filter by type and status
- ✅ **Operations Table** - Detailed log table with all metadata
- ✅ **Export to CSV** - Download filtered operations
- ✅ **Raw JSON View** - Inspect raw log data

#### **4. Workflows Tab**
- ✅ **Workflow Selector** - Choose specific workflow to analyze
- ✅ **Workflow Summary** - Table of all workflows with metrics
- ✅ **Gantt Chart Timeline** - Visual workflow execution timeline
- ✅ **Cross-Service Tracing** - Track operations across multiple services
- ✅ **Operation Details** - Step-by-step workflow breakdown

#### **5. Errors Tab**
- ✅ **Error Summary** - Total errors, affected services, error rate, success rate
- ✅ **Errors by Service** - Bar chart of error distribution
- ✅ **Status Code Distribution** - Pie chart of HTTP status codes
- ✅ **Error Timeline** - When and where errors occurred
- ✅ **Failed Operations Table** - Detailed error messages and context

### **🔄 Real-Time Features**

- ✅ **Auto-Refresh** - Configurable intervals (5, 10, 30, 60 seconds, or off)
- ✅ **Live Data** - Real-time updates from log-collector
- ✅ **Caching** - Configurable TTL (default 5s) for performance
- ✅ **Connection Pooling** - Efficient HTTP client with persistent connections

### **🔌 Hybrid Architecture**

#### **Streamlit Web UI (Port 8501)**
- 🎨 Interactive visualizations with Plotly
- 🖱️ Rich filtering and search controls
- 📥 CSV export functionality
- 📊 Real-time metrics and charts
- 👤 Designed for human operators

#### **FastAPI REST API (Port 8080)**
- 🔗 Standard endpoints for ecosystem integration
- 📖 OpenAPI/Swagger documentation
- 🔍 Programmatic health checks
- 📡 Service discovery compatible
- 🤖 Designed for monitoring systems

### **🛡️ Network Resilience**

- ✅ **Retry Logic** - 3 attempts with exponential backoff (1s, 2s, 4s)
- ✅ **Connection Pooling** - Reuse HTTP connections for efficiency
- ✅ **Graceful Degradation** - Display cached data or empty state on failure
- ✅ **Error Handling** - Never crashes, always provides feedback
- ✅ **Timeout Management** - Configurable timeouts (default 5s)

### **📝 Centralized Logging**

- ✅ **Log-Collector Integration** - All events sent to centralized service
- ✅ **Standard Events** - Dashboard lifecycle, data fetching, user interactions
- ✅ **Non-Blocking** - Logging failures don't affect dashboard
- ✅ **Structured Logs** - JSON format with context

### **✅ Type Safety & Validation**

- ✅ **Pydantic Models** - Type-safe data models throughout
- ✅ **Input Validation** - All user inputs validated
- ✅ **Error Boundaries** - Comprehensive error handling at all layers

---

## 🏗️ Architecture

### **Hybrid Architecture Pattern**

```
Data Services Dashboard
├── Streamlit UI (8501)          # Human Interface
│   ├── 5 Interactive Tabs
│   ├── Plotly Visualizations
│   ├── Search & Filtering
│   └── Real-Time Updates
│
└── FastAPI REST API (8080)      # System Interface
    ├── GET /health
    ├── GET /about-me
    ├── GET /endpoints
    ├── GET /provider-consumer
    └── GET /openapi.json
```

### **Modular by Feature Organization**

Unlike traditional DDD (which is overkill for dashboards), we use **"Modular by Feature"**:

```
services/data-services-dashboard/
├── app.py                    # Main entry (hybrid: Streamlit + FastAPI)
├── config.py                 # Configuration management (Pydantic Settings)
│
├── api/                      # REST API Layer
│   ├── router.py            # Standard endpoints
│   └── models.py            # API models
│
├── data/                     # Data Fetching & Processing
│   ├── fetcher.py           # Fetch logs (with retry)
│   ├── parser.py            # Parse & validate logs
│   └── models.py            # Pydantic data models
│
├── metrics/                  # Metric Calculations
│   └── calculator.py        # Aggregate metrics
│
├── visualization/            # Dashboard Tabs
│   ├── overview.py          # Overview tab
│   ├── performance.py       # Performance tab
│   ├── operations.py        # Operations tab
│   ├── workflows.py         # Workflows tab
│   └── errors.py            # Errors tab
│
└── utils/                    # Utilities
    ├── retry.py             # @with_retry decorator
    ├── logging_client.py    # Log-collector client
    └── formatting.py        # Display formatting
```

**Why "Modular by Feature" vs DDD?**

| Aspect | Dashboard (Modular) | REST API Service (DDD) |
|--------|---------------------|------------------------|
| **Purpose** | Visualization | Business logic |
| **Consumers** | Humans (+ systems) | Services (programmatic) |
| **State** | Stateful (UI session) | Stateless (request/response) |
| **Logic** | Data transformation | Domain rules |
| **Organization** | By feature/tab | By layer |
| **Reusability** | Dashboard-specific | Domain-agnostic |

---

## 📡 API Reference

### **Standard Endpoints**

All services expose these endpoints for ecosystem integration:

#### **GET /health**

Health check with dependency status.

```json
{
  "status": "healthy",
  "service": "data-services-dashboard",
  "version": "1.0.0",
  "timestamp": "2025-10-09T12:00:00Z",
  "uptime_seconds": 3600,
  "dependencies": {
    "log_collector": "connected",
    "ui": "running"
  }
}
```

#### **GET /about-me**

Comprehensive service descriptor.

```json
{
  "service": "data-services-dashboard",
  "version": "1.0.0",
  "type": "dashboard",
  "architecture": "hybrid",
  "interfaces": {
    "web_ui": {
      "type": "streamlit",
      "url": "http://localhost:8501",
      "port": 8501
    },
    "rest_api": {
      "type": "rest",
      "base_path": "/api/v1",
      "port": 8080
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
        "port": 8104,
        "purpose": "Operation logs and metrics"
      }
    ]
  }
}
```

#### **GET /endpoints**

List all available API endpoints.

#### **GET /provider-consumer**

Service relationship matrix showing data flow.

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.12+
- Log-collector service running (port 8104)

### **Installation**

```bash
cd services/data-services-dashboard

# Install dependencies
pip install -r requirements.txt

# (Optional) Install test dependencies
pip install -r requirements-test.txt
```

### **Running the Dashboard**

#### **Method 1: Streamlit (recommended for local development)**

```bash
streamlit run app.py
```

Access:
- **Streamlit UI**: http://localhost:8501
- **FastAPI API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

#### **Method 2: Docker**

```bash
docker-compose up data-services-dashboard
```

#### **Method 3: Production (Hybrid Mode)**

The dashboard automatically starts both Streamlit UI and FastAPI REST API in a single process.

---

## ⚙️ Configuration

### **Environment Variables**

All configuration via environment variables with `DASHBOARD_` prefix:

```bash
# Service
DASHBOARD_SERVICE_NAME=data-services-dashboard
DASHBOARD_SERVICE_VERSION=1.0.0

# Ports
DASHBOARD_UI_PORT=8501          # Streamlit UI
DASHBOARD_API_PORT=8080         # FastAPI REST API

# Log Collector
DASHBOARD_LOG_COLLECTOR_URL=http://localhost:8104

# Services to Monitor
DASHBOARD_DEFAULT_SERVICES=doc_store,prompt_store,memory-agent

# Caching
DASHBOARD_CACHE_TTL=5           # Seconds (0 = disabled)

# Retry Logic
DASHBOARD_MAX_RETRY_ATTEMPTS=3
DASHBOARD_RETRY_DELAY=1.0       # Seconds
DASHBOARD_RETRY_BACKOFF=2.0     # Multiplier

# HTTP
DASHBOARD_HTTP_TIMEOUT=5.0      # Seconds

# Environment
DASHBOARD_ENVIRONMENT=production  # development, staging, production
DASHBOARD_DEBUG=false
```

### **Configuration File** (Alternative)

Create `.env` file:

```env
DASHBOARD_UI_PORT=8501
DASHBOARD_API_PORT=8080
DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104
DASHBOARD_CACHE_TTL=10
```

See [CONFIG.md](./CONFIG.md) for detailed configuration reference.

---

## 🧪 Testing

### **Run All Tests**

```bash
pytest
```

### **Run Specific Test Categories**

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# API tests only
pytest -m api
```

### **Coverage Report**

```bash
pytest --cov=./ --cov-report=html
open htmlcov/index.html
```

### **Test Statistics**

- **Total Tests**: 105+
- **Unit Tests**: 75+ (71%)
- **Integration Tests**: 30+ (29%)
- **Coverage**: 80%+
- **Test Files**: 4

---

## 📊 Data Flow

```
┌─────────────────┐
│  Human Operator │
└────────┬────────┘
         │ Access Dashboard
         ↓
┌────────────────────────────────────────────┐
│     Data Services Dashboard (8501)         │
│                                            │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐ │
│  │Overview │  │Performance│  │Operations│ │
│  └─────────┘  └──────────┘  └──────────┘ │
│  ┌─────────┐  ┌──────────┐               │
│  │Workflows│  │ Errors   │               │
│  └─────────┘  └──────────┘               │
└───────────────────┬────────────────────────┘
                    │ fetch_logs()
                    ↓ (with retry, cache)
        ┌───────────────────────┐
        │  Log-Collector (8104) │
        │                       │
        │  [Operation Logs]     │
        └───────────────────────┘
                    ↑
                    │ send_log()
        ┌───────────┴───────────┐
        │                       │
    ┌───┴────┐  ┌──────┴─────┐
    │doc_store│  │prompt_store│
    └─────────┘  └────────────┘
        Datastore Services
```

### **Data Processing Flow**

1. **Fetch** → Dashboard fetches logs from log-collector (HTTP GET)
2. **Cache** → Streamlit caches for 5s (configurable TTL)
3. **Parse** → Raw dicts validated into Pydantic models
4. **Calculate** → Aggregate metrics computed
5. **Visualize** → Plotly charts rendered
6. **Display** → Streamlit UI shows results

---

## 🔗 Service Relationships

### **Providers** (Services This Depends On)

| Service | Port | Purpose | Criticality |
|---------|------|---------|-------------|
| **log-collector** | 8104 | Operation logs | Critical |

### **Consumers** (Who Uses This Service)

| Consumer | Interface | Purpose |
|----------|-----------|---------|
| **human-operators** | Web UI (8501) | View dashboard visualizations |
| **monitoring-systems** | REST API (8080) | Query health and status |

---

## 📖 Additional Documentation

- **[CONFIG.md](./CONFIG.md)** - Detailed configuration reference
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Production deployment guide
- **[PHASE_1_SERVICE_AUDIT.md](./PHASE_1_SERVICE_AUDIT.md)** - Initial audit findings
- **[PHASE_2_DESIGN_PLAN.md](./PHASE_2_DESIGN_PLAN.md)** - Design & architecture decisions

---

## 🐛 Troubleshooting

### **Dashboard shows "No operations to display"**

**Cause**: Log-collector is not reachable or has no data.

**Solution**:
1. Check log-collector is running: `curl http://localhost:8104/health`
2. Check dashboard sidebar for "Log Collector: Connected" status
3. Generate test operations: `python test_generate_operations.py`

### **"Connection Error: Unable to reach log-collector"**

**Cause**: Log-collector URL misconfigured or service down.

**Solution**:
1. Verify `DASHBOARD_LOG_COLLECTOR_URL` environment variable
2. Test connectivity: `curl http://localhost:8104/logs?limit=10`
3. Check Docker network if using containers

### **Dashboard is slow to load**

**Cause**: Cache TTL too low or fetching too many logs.

**Solution**:
1. Increase `DASHBOARD_CACHE_TTL` (default: 5s, try 10s or 30s)
2. Reduce time range (use "Last 100 operations" instead of "Last 1000")
3. Check log-collector performance

### **Auto-refresh not working**

**Cause**: Browser cache or Streamlit issue.

**Solution**:
1. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
2. Check auto-refresh interval in sidebar (0 = disabled)
3. Restart Streamlit: `streamlit run app.py`

---

## 🎯 Best Practices

### **For Dashboard Users**

1. **Use Filters** - Filter by service/type to reduce data volume
2. **Adjust Cache TTL** - Balance freshness vs performance
3. **Export CSV** - Download data for offline analysis
4. **Monitor Errors Tab** - Catch issues early
5. **Use Workflows Tab** - Trace cross-service issues

### **For Monitoring Systems**

1. **Poll /health** - Regular health checks every 30-60s
2. **Use /about-me** - Discover capabilities dynamically
3. **Parse /endpoints** - Build dynamic monitoring dashboards
4. **Monitor Dependencies** - Track log-collector connectivity

---

## 📝 Version History

### **v1.0.0** (October 9, 2025)
- ✨ Initial production-ready release
- 🎨 Hybrid architecture (Streamlit + FastAPI)
- 📊 5 interactive dashboard tabs
- 🔄 Auto-refresh with configurable intervals
- 🛡️ Retry logic with exponential backoff
- 📝 Centralized logging integration
- ✅ 80%+ test coverage (105+ tests)
- 📖 Comprehensive documentation
- 🐳 Docker support

---

## 🤝 Contributing

This service follows the **Master Refactoring Plan** standards:

- **Architecture**: Modular by Feature (Dashboard-specific)
- **Testing**: 80%+ coverage, TDD approach
- **Logging**: Centralized via log-collector
- **Documentation**: Comprehensive READMEs, CONFIG.md, diagrams
- **Quality**: Type hints, Pydantic validation, error handling

---

**Dashboard Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Status**: ✅ Production Ready  
**Maintainer**: LLM Documentation Ecosystem Team
