---
title: "Ecosystem MCP Dashboard - Architecture Overview"
service: "ecosystem-mcp-dashboard"
category: "architecture"
tags: ["architecture", "streamlit", "dashboard", "ui", "components"]
related: ["../features/COMPONENTS.md", "../guides/QUICK_START.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
---

# Ecosystem MCP Dashboard - Architecture Overview

**Interactive Streamlit-based web interface for Ecosystem MCP service**

---

## 🎯 Purpose

The Ecosystem MCP Dashboard provides a user-friendly web interface for:

1. **RAG Querying**: Interactive interface for all RAG query types
2. **Ingestion Management**: Start, monitor, and troubleshoot ingestion jobs
3. **System Monitoring**: Real-time health checks and performance metrics
4. **Data Exploration**: Browse PostgreSQL, Redis, and ChromaDB data
5. **Configuration Management**: View and validate system configuration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   STREAMLIT DASHBOARD                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │               Page Layer (Streamlit Pages)              │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  • Home (overview)                                      │    │
│  │  • RAG Query (unified interface)                        │    │
│  │  • Temporal RAG (time-based queries)                    │    │
│  │  • Context-Aware RAG (filtered queries)                 │    │
│  │  • Ingestion Manager (job control)                      │    │
│  │  • Database Explorers (data viewers)                    │    │
│  │  • System Health (monitoring)                           │    │
│  │  • Configuration Registry (config viewer)               │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Component Layer (Reusable UI)                │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  • Form components (inputs, selectors)                  │    │
│  │  • Data display (tables, cards, metrics)                │    │
│  │  • Charts (Plotly, Altair)                              │    │
│  │  • Status indicators (health, progress)                 │    │
│  │  • Navigation (sidebar, tabs)                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │             API Client Layer (HTTP Client)              │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  • HTTPx client with retry logic                        │    │
│  │  • Circuit breakers (prevent cascade failures)          │    │
│  │  • Response caching (Redis + TTL)                       │    │
│  │  • Error handling (graceful degradation)                │    │
│  │  • Request/response logging                             │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Caching Layer (Performance)                │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  • Redis cache (shared across sessions)                 │    │
│  │  • Streamlit session state (per-user cache)             │    │
│  │  • TTL-based expiration                                 │    │
│  │  • Cache invalidation on mutations                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ▼                                      │
│                 Ecosystem MCP REST API                           │
│              (http://ecosystem-mcp-service:8000)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Key Components

### 1. Page Layer (Streamlit Pages)

**Technology**: Streamlit multi-page apps

**Pages**:

#### Home (`app.py`)
- Service overview
- Quick stats
- Recent activity
- Navigation links

#### RAG Query (`dashboard_views/rag_unified.py`)
- Unified interface for all RAG types
- Standard, Enhanced, Temporal, Context-Aware, Multi-Pass
- Query form with advanced options
- Results display with sources
- Query history

#### Temporal RAG (`dashboard_views/temporal_rag.py`)
- Point-in-time queries
- Period comparison queries
- Evolution tracking
- Timeline management

#### Context-Aware RAG (`dashboard_views/context_aware_rag.py`)
- Repository filtering
- Hierarchical context selection
- Service/module filtering
- Technology stack filtering

#### Ingestion Manager (`dashboard_views/ingestion_manager_improved.py`)
- Start new ingestion jobs
- Monitor active jobs
- View job history
- Error troubleshooting
- Retry failed operations

#### Database Explorers (`dashboard_views/database_explorers.py`)
- PostgreSQL explorer (tables, queries)
- Redis explorer (keys, data structures)
- ChromaDB explorer (collections, documents)

#### System Health (`dashboard_views/system_health.py`)
- Service health checks
- Dependency status
- Worker monitoring
- Performance metrics

#### Configuration Registry (`dashboard_views/config_registry.py`)
- View system configuration
- Configuration validation
- Health checks
- Diff viewer (expected vs. actual)

---

### 2. Component Layer

**Reusable UI Components**:

#### Form Components (`components/forms.py`)
- Text inputs
- Number inputs
- Select boxes
- Multi-select
- Date/time pickers
- File uploaders

#### Data Display (`components/display.py`)
- Data tables (sortable, filterable)
- Metric cards
- Status badges
- Progress bars
- Expandable sections

#### Charts (`components/charts.py`)
- Line charts (job progress over time)
- Bar charts (document counts)
- Pie charts (category distribution)
- Scatter plots (temporal data)

#### Status Indicators (`components/status.py`)
- Health status (✅ ⚠️ ❌)
- Job status (queued, running, completed, failed)
- Dependency status (healthy, degraded, unhealthy)

---

### 3. API Client Layer

**File**: `utils/api_client.py`

**Features**:
- HTTPx async client
- Automatic retries (3 attempts)
- Circuit breaker pattern
- Request/response logging
- Error standardization
- Timeout handling

**Example**:
```python
from utils.api_client import get_api_client

client = get_api_client()
response = await client.post("/api/v1/query/enhanced", json={
    "question": "How does caching work?",
    "mode": "rag",
    "n_results": 10
})
```

---

### 4. Caching Layer

**Strategy**: Multi-level caching for performance

**Levels**:

1. **Redis Cache** (`utils/cached_api.py`)
   - Shared across all users
   - TTL: 5 minutes (configurable)
   - Key format: `dashboard:cache:{endpoint}:{hash(params)}`

2. **Streamlit Session State**
   - Per-user cache
   - Persists during session
   - Fast access

3. **In-Memory TTL Cache** (`utils/caching.py`)
   - Process-level cache
   - Automatic expiration
   - For expensive computations

**Cache Invalidation**:
- Automatic on TTL expiration
- Manual via "Refresh" buttons
- Automatic on mutations (create/update/delete)

---

## 🎨 User Experience Features

### Navigation
- **Sidebar**: Main navigation menu
- **Tabs**: Sub-navigation within pages
- **Breadcrumbs**: Show current location

### Feedback
- **Success Messages**: Green notifications
- **Error Messages**: Red notifications
- **Warning Messages**: Yellow notifications
- **Loading Indicators**: Spinners for async operations

### Responsiveness
- **Auto-refresh**: Optional auto-refresh for monitoring pages
- **Lazy Loading**: Load data on demand
- **Progressive Enhancement**: Basic functionality always works

### Accessibility
- **Keyboard Navigation**: Tab through interface
- **Screen Reader Support**: Semantic HTML
- **High Contrast**: Clear visual hierarchy

---

## 🔧 Configuration

**Environment Variables**:

```bash
# API Configuration
ECOSYSTEM_MCP_API_URL=http://ecosystem-mcp-service:8000

# Redis Cache
REDIS_URL=redis://redis:6379
CACHE_TTL_SECONDS=300

# Dashboard Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Feature Flags
ENABLE_AUTO_REFRESH=true
ENABLE_CACHING=true
```

---

## 📊 Data Flow Example

### Example: RAG Query

```
1. User fills out query form:
   - Question: "How does caching work?"
   - Mode: RAG
   - Number of results: 10

2. Form submission triggers API call:
   st.form_submit_button() → call API client

3. API Client Layer:
   a. Check Redis cache for response
      - Key: "dashboard:cache:/api/v1/query/enhanced:hash(...)"
      - If hit: return cached response ✅
      - If miss: continue →
   
   b. Make HTTP request to MCP service:
      POST http://ecosystem-mcp-service:8000/api/v1/query/enhanced
      
   c. Handle response:
      - Success: cache + return
      - Error: show error message

4. Display results:
   - Answer text
   - Source documents (expandable)
   - Metadata (models used, timing)
   - Actions (save, share)
```

---

## 🛡️ Resilience & Fault Tolerance

### Circuit Breakers

**Pattern**: Prevent cascade failures when API is down

**States**:
- **Closed**: Normal operation
- **Open**: Too many failures, fast-fail with cached data
- **Half-Open**: Testing if service recovered

**Implementation** (`utils/circuit_breaker.py`):
- Failure threshold: 5 failures in 60 seconds
- Open duration: 30 seconds
- Half-open test requests: 1

### Graceful Degradation

**Strategies**:

1. **Cached Data Fallback**: Show cached results when API is down
2. **Partial Functionality**: Core features work even if some fail
3. **Clear Error Messages**: Tell user what's wrong and how to fix
4. **Retry Options**: Manual retry buttons for failed operations

---

## 📈 Performance Optimizations

### Caching Strategy
- **Expensive Queries**: Cache for 5 minutes
- **Static Data**: Cache for 1 hour
- **Real-time Data**: No caching, but show stale + update

### Lazy Loading
- Load data only when needed
- Paginate large result sets
- Virtualize long lists

### Async Operations
- Use Streamlit's async support
- Show loading indicators
- Allow cancellation

---

## 🧪 Testing Strategy

### Unit Tests
- Component rendering
- API client logic
- Cache behavior

### Integration Tests
- Page flows
- API integration
- Error handling

### E2E Tests
- Full user workflows
- Cross-page navigation
- Data consistency

**See**: [`../development/TESTING.md`](../development/TESTING.md)

---

## 🔗 Related Documentation

- [Component Catalog](../features/COMPONENTS.md) - Reusable UI components
- [API Client Guide](../guides/API_CLIENT.md) - Using the API client
- [Quick Start](../guides/QUICK_START.md) - Getting started
- [Ecosystem MCP Service](../../../ecosystem-mcp/docs/INDEX.md) - Backend service

---

## 📖 Glossary

- **Streamlit**: Python web framework for data apps
- **Circuit Breaker**: Fault tolerance pattern
- **TTL**: Time To Live (cache expiration)
- **Session State**: Per-user data storage in Streamlit
- **HTTPx**: Modern Python HTTP client

---

**Last Updated**: 2025-10-28  
**Version**: 1.0.0  
**Status**: Production-Ready

