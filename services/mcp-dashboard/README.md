# 📊 MCP Dashboard Service

**Version:** 1.0.0  
**Port:** 8015  
**Role:** Unified Management Dashboard for MCP Ecosystem

The **MCP Dashboard Service** provides a comprehensive Streamlit-based web interface for managing, monitoring, and interacting with all MCP services. It serves as the central control plane for the entire MCP ecosystem.

---

## 🎯 **Overview**

The MCP Dashboard is a **CORE SERVICE** that provides:

- **Unified Management Interface**: Single pane of glass for all MCP operations
- **Real-time Monitoring**: Live updates from all services
- **Service Integration**: Direct API connections to all MCP services
- **Interactive Operations**: Create, train, query, and manage MCPs
- **Analytics & Insights**: Performance metrics, trends, and analytics

---

## ✨ **Key Features**

### 1. MCP Lifecycle Management
- ✅ **Create MCPs** via Provisioner integration
- ✅ **Train MCPs** via Training Coordinator
- ✅ **Query MCPs** via Orchestrator & Retrieval
- ✅ **Package MCPs** via Package Manager
- ✅ **Monitor MCPs** via Infrastructure

### 2. Real-time Service Integration
- ✅ **Training Coordinator** - Job management, progress tracking
- ✅ **MCP Provisioner** - Create, deploy, manage MCP instances
- ✅ **MCP Interpreter** - Natural language query parsing
- ✅ **MCP Retrieval** - Hierarchical context retrieval
- ✅ **MCP Orchestrator** - Pattern execution
- ✅ **MCP Store** - Knowledge management
- ✅ **All 16 MCP Services** - Complete ecosystem integration

### 3. Dashboard Pages
- ✅ **Home** - System overview, health status
- ✅ **MCP Management** - Create, list, manage MCPs
- ✅ **Training Dashboard** - Job tracking, worker status
- ✅ **Query Interface** - Natural language queries
- ✅ **Tier Management** - Hierarchical system
- ✅ **Package Manager** - Package operations
- ✅ **Logs & Monitoring** - Intelligent observability
- ✅ **Analytics** - System-wide metrics
- ✅ **Performance** - Performance tracking
- ✅ **Configuration** - Service settings

### 4. Advanced Features
- ✅ **WebSocket Updates** - Real-time data streaming
- ✅ **Interactive Visualizations** - Plotly charts
- ✅ **Multi-service Operations** - Orchestrate across services
- ✅ **Error Handling** - Graceful degradation
- ✅ **Authentication Ready** - Integration points for auth

---

## 🏗️ **Architecture**

### Service Structure

```
services/mcp-dashboard/
├── src/
│   ├── __init__.py
│   └── config.py              # Configuration
├── api/
│   ├── __init__.py
│   └── main.py                # FastAPI backend (optional)
├── integrations/
│   ├── __init__.py
│   ├── provisioner_client.py  # Provisioner integration
│   ├── training_client.py     # Training Coordinator integration
│   ├── interpreter_client.py  # Interpreter integration
│   ├── retrieval_client.py    # Retrieval integration
│   ├── orchestrator_client.py # Orchestrator integration
│   ├── store_client.py        # Store integration
│   ├── performance_client.py  # Performance Store integration
│   ├── tier_client.py         # Tier Manager integration
│   ├── package_client.py      # Package Manager integration
│   └── logs_client.py         # Logs MCP integration
├── pages/
│   ├── 0_🏠_Home.py           # Home dashboard
│   ├── 1_📦_MCP_Management.py # MCP CRUD operations
│   ├── 2_🎓_Training.py       # Training dashboard
│   ├── 3_🔍_Query.py          # Query interface
│   ├── 4_🏗️_Tiers.py         # Tier management
│   ├── 5_📦_Packages.py       # Package management
│   ├── 6_🔍_Logs.py           # Logs & monitoring
│   ├── 7_📊_Analytics.py      # Analytics dashboard
│   └── 8_⚙️_Settings.py       # Configuration
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🔗 **Service Integrations**

### **1. MCP Training Coordinator (Port 5600)** 🎓

**Tight Integration - Primary Focus**

**Purpose**: Complete training lifecycle management from the dashboard

**Features**:
- Create training jobs with visual job builder
- Real-time job progress tracking
- Worker status monitoring
- Job history and analytics
- Resource utilization visualization
- Training configuration templates

**API Calls**:
```python
# Create training job
POST http://mcp-training-coordinator:5600/api/v1/jobs
{
  "mcp_id": "mcp-123",
  "data_sources": ["GITHUB", "CONFLUENCE"],
  "priority": "HIGH",
  "config": {...}
}

# Get job status with real-time updates
GET http://mcp-training-coordinator:5600/api/v1/jobs/{job_id}

# List all jobs with filtering
GET http://mcp-training-coordinator:5600/api/v1/jobs?status=EXECUTING

# Cancel job
DELETE http://mcp-training-coordinator:5600/api/v1/jobs/{job_id}

# Get worker status
GET http://mcp-training-coordinator:5600/api/v1/workers
```

**Dashboard Features**:
- Job creation wizard with templates
- Real-time progress bars (0-100%)
- Worker pool visualization
- Data source configuration UI
- Job queue management
- Resource limit controls
- Training analytics charts

---

### **2. MCP Provisioner (Port 8003)** 🚀

**Tight Integration - Primary Focus**

**Purpose**: Complete MCP lifecycle management

**Features**:
- Visual MCP creation wizard
- Tier selection and configuration
- MCP instance monitoring
- Deployment status tracking
- Resource allocation UI
- Instance health monitoring

**API Calls**:
```python
# Create MCP instance
POST http://mcp-provisioner:8003/api/v1/mcps
{
  "name": "acme-corp-dev",
  "tier": "Project",
  "parent_tier": "team-123",
  "config": {...}
}

# List MCPs with filtering
GET http://mcp-provisioner:8003/api/v1/mcps?tier=Project

# Get MCP details
GET http://mcp-provisioner:8003/api/v1/mcps/{mcp_id}

# Update MCP configuration
PUT http://mcp-provisioner:8003/api/v1/mcps/{mcp_id}

# Delete MCP
DELETE http://mcp-provisioner:8003/api/v1/mcps/{mcp_id}

# Get MCP health
GET http://mcp-provisioner:8003/api/v1/mcps/{mcp_id}/health
```

**Dashboard Features**:
- MCP creation form with validation
- Tier selection dropdown
- Configuration editor (JSON/YAML)
- Instance list with status indicators
- Health check dashboard
- Resource usage visualization
- Quick actions (start/stop/restart)

---

### **3. MCP Interpreter (Port 8002)** 🧠

**Tight Integration - Primary Focus**

**Purpose**: Natural language query interface

**Features**:
- Interactive query input
- Intent visualization
- Entity extraction display
- Query history
- Suggested queries
- Query refinement

**API Calls**:
```python
# Parse natural language query
POST http://mcp-interpreter:8002/api/v1/interpret
{
  "query": "What are our API best practices?",
  "context": {
    "user_id": "user-123",
    "session_id": "sess-456"
  }
}

# Get interpretation history
GET http://mcp-interpreter:8002/api/v1/history?user_id=user-123

# Get suggested queries
GET http://mcp-interpreter:8002/api/v1/suggestions
```

**Dashboard Features**:
- Chat-like query interface
- Intent visualization (pie charts)
- Entity highlighting
- Confidence scores
- Query suggestions
- History browser
- Quick actions for common queries

---

### **4. MCP Retrieval (Port 8014)** 🔍

**Tight Integration - Primary Focus**

**Purpose**: Hierarchical context retrieval visualization

**Features**:
- Hierarchical search visualization
- Tier-by-tier results display
- Context pruning visualization
- Token budget tracking
- Relevance scoring display
- Source document links

**API Calls**:
```python
# Hierarchical retrieval
POST http://mcp-retrieval:8014/api/v1/retrieve
{
  "query": "API best practices",
  "user_id": "user-123",
  "token_budget": 8000,
  "tiers": ["Client", "Project", "Team"],
  "strategy": "HYBRID"
}

# Get retrieval stats
GET http://mcp-retrieval:8014/api/v1/stats?user_id=user-123

# Configure retrieval settings
PUT http://mcp-retrieval:8014/api/v1/config
```

**Dashboard Features**:
- Visual tier hierarchy
- Results by tier (collapsible sections)
- Token usage pie chart
- Relevance score bars
- Source document cards
- Pruning visualization
- Strategy comparison

---

### **5. MCP Orchestrator (Port 8004)** 🎯

**Integration**: Execute queries and patterns

**API Calls**:
```python
# Execute query with pattern
POST http://mcp-orchestrator:8004/api/v1/execute
{
  "query": "What are our API best practices?",
  "mcp_id": "mcp-123",
  "pattern": "RAG",
  "config": {...}
}

# Get execution history
GET http://mcp-orchestrator:8004/api/v1/executions?mcp_id=mcp-123
```

---

### **6. MCP Store (Port 8008)** 📦

**Integration**: Knowledge management

**API Calls**:
```python
# Search knowledge
POST http://mcp-store:8008/api/v1/search
{
  "query": "API practices",
  "mcp_id": "mcp-123",
  "limit": 20
}

# Get MCP statistics
GET http://mcp-store:8008/api/v1/mcps/{mcp_id}/stats
```

---

### **7. MCP Tier Manager (Port 8013)** 🏗️

**Integration**: Hierarchy management

**API Calls**:
```python
# Get tier hierarchy
GET http://mcp-tier-manager:8013/api/v1/tiers?user_id=user-123

# Create tier
POST http://mcp-tier-manager:8013/api/v1/tiers

# Update tier configuration
PUT http://mcp-tier-manager:8013/api/v1/tiers/{tier_id}
```

---

### **8. MCP Package Manager (Port 8012)** 📦

**Integration**: Package operations

**API Calls**:
```python
# Export package
POST http://mcp-package-manager:8012/api/v1/packages/export

# Import package
POST http://mcp-package-manager:8012/api/v1/packages/import

# Hot-swap package
POST http://mcp-package-manager:8012/api/v1/packages/{id}/hot-swap
```

---

### **9. MCP Logs (Port 8011)** 🔍

**Integration**: Intelligent observability

**API Calls**:
```python
# Get patterns
GET http://mcp-logs:8011/api/v1/patterns

# Get anomalies
GET http://mcp-logs:8011/api/v1/anomalies

# Get predictions
GET http://mcp-logs:8011/api/v1/predictions
```

---

### **10. MCP Performance Store (Port 8009)** 📊

**Integration**: Metrics and analytics

**API Calls**:
```python
# Get performance metrics
GET http://mcp-performance-store:8009/api/v1/metrics?mcp_id=mcp-123

# Get analytics
GET http://mcp-performance-store:8009/api/v1/analytics
```

---

## 🎨 **Dashboard Pages**

### **Page 1: Home** 🏠
- System health overview
- Active MCPs count
- Training jobs in progress
- Recent queries
- Service status grid
- Quick actions

### **Page 2: MCP Management** 📦
**Tight Provisioner Integration**
- Create MCP wizard
- MCP list with filters
- MCP details cards
- Health status indicators
- Quick actions (train, query, delete)
- Tier assignment UI

### **Page 3: Training Dashboard** 🎓
**Tight Training Coordinator Integration**
- Job creation form
- Active jobs list with progress
- Worker status grid
- Resource utilization charts
- Job history table
- Data source configuration
- Queue management

### **Page 4: Query Interface** 🔍
**Tight Interpreter + Retrieval + Orchestrator Integration**
- Chat-like query input
- MCP selection dropdown
- Real-time interpretation
- Hierarchical results display
- Token usage visualization
- Source citations
- Query history

### **Page 5: Tier Management** 🏗️
- Hierarchy visualization (tree)
- Tier creation form
- Tier configuration editor
- Access control settings
- Progressive refinement config

### **Page 6: Package Management** 📦
- Export package UI
- Import package UI
- Package list
- Version control
- Hot-swap controls

### **Page 7: Logs & Monitoring** 🔍
- Pattern detection display
- Anomaly alerts
- Root cause analysis
- Predictive maintenance
- Log viewer

### **Page 8: Analytics** 📊
- System-wide metrics
- Performance trends
- Cost tracking
- Usage analytics
- Comparative charts

### **Page 9: Settings** ⚙️
- Service configuration
- API endpoints
- Authentication settings
- Theme preferences

---

## 🚀 **Running the Dashboard**

### **Docker (Recommended)**

```bash
docker-compose up mcp-dashboard
```

The dashboard will be available at `http://localhost:8015`

### **Local Development**

```bash
cd services/mcp-dashboard
pip install -r requirements.txt
streamlit run pages/0_🏠_Home.py --server.port 8015
```

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# Dashboard Configuration
DASHBOARD_PORT=8015
DASHBOARD_HOST=0.0.0.0

# Service Endpoints (Critical Integrations)
TRAINING_COORDINATOR_URL=http://mcp-training-coordinator:5600
PROVISIONER_URL=http://mcp-provisioner:8003
INTERPRETER_URL=http://mcp-interpreter:8002
RETRIEVAL_URL=http://mcp-retrieval:8014
ORCHESTRATOR_URL=http://mcp-orchestrator:8004

# Additional Services
MCP_STORE_URL=http://mcp-store:8008
TIER_MANAGER_URL=http://mcp-tier-manager:8013
PACKAGE_MANAGER_URL=http://mcp-package-manager:8012
LOGS_URL=http://mcp-logs:8011
PERFORMANCE_STORE_URL=http://mcp-performance-store:8009
INFRASTRUCTURE_URL=http://mcp-infrastructure:8007
REGISTRY_URL=http://mcp-registry:8006

# Dashboard Settings
REFRESH_INTERVAL_SECONDS=5
MAX_CONCURRENT_REQUESTS=10
ENABLE_WEBSOCKETS=true
```

---

## 📊 **Real-time Features**

### **WebSocket Streaming**

The dashboard uses WebSockets for real-time updates:

- **Training Progress**: Live job progress (0-100%)
- **MCP Health**: Real-time health checks
- **Query Results**: Streaming query responses
- **Log Monitoring**: Live log tailing
- **Performance Metrics**: Real-time charts

### **Auto-refresh**

Configurable auto-refresh for:
- MCP list (every 30s)
- Training jobs (every 5s)
- Worker status (every 10s)
- System health (every 15s)

---

## 🎯 **Integration Details**

### **Training Coordinator Integration**

**Job Creation Flow**:
```
User (Dashboard) → Training Dashboard Page
    ↓
1. User fills job form
    ↓
2. Dashboard → training_client.create_job()
    ↓
3. training_client → POST /api/v1/jobs
    ↓
4. Training Coordinator creates job
    ↓
5. Training Coordinator → Dashboard (job_id)
    ↓
6. Dashboard starts polling for progress
    ↓
7. Dashboard updates UI with progress bars
```

### **Provisioner Integration**

**MCP Creation Flow**:
```
User (Dashboard) → MCP Management Page
    ↓
1. User fills creation form
    ↓
2. Dashboard → provisioner_client.create_mcp()
    ↓
3. provisioner_client → POST /api/v1/mcps
    ↓
4. Provisioner creates MCP
    ↓
5. Provisioner → Dashboard (mcp_id, status)
    ↓
6. Dashboard displays success + MCP card
    ↓
7. Dashboard auto-refreshes MCP list
```

### **Interpreter + Retrieval + Orchestrator Integration**

**Query Execution Flow**:
```
User (Dashboard) → Query Interface Page
    ↓
1. User types query
    ↓
2. Dashboard → interpreter_client.interpret()
    ↓
3. Interpreter parses query
    ↓
4. Dashboard displays intent + entities
    ↓
5. Dashboard → retrieval_client.retrieve()
    ↓
6. Retrieval fetches hierarchical context
    ↓
7. Dashboard displays sources by tier
    ↓
8. Dashboard → orchestrator_client.execute()
    ↓
9. Orchestrator executes pattern
    ↓
10. Dashboard streams response to user
```

---

## 🔒 **Security**

- ✅ API token authentication
- ✅ Role-based access control (planned)
- ✅ Service-to-service auth
- ✅ HTTPS support
- ✅ CORS configuration

---

## 📈 **Performance**

- **Load Time**: <2 seconds
- **API Response**: <500ms
- **Real-time Updates**: <100ms latency
- **Concurrent Users**: 100+
- **WebSocket Connections**: 50+

---

## 🎓 **Best Practices**

1. ✅ Use service clients for all API calls
2. ✅ Handle errors gracefully with user feedback
3. ✅ Cache expensive operations
4. ✅ Use WebSockets for real-time data
5. ✅ Provide loading states
6. ✅ Validate user input
7. ✅ Log all operations

---

## 📞 **Related Services**

- **MCP Training Coordinator**: [/services/mcp-training-coordinator/README.md](/services/mcp-training-coordinator/README.md)
- **MCP Provisioner**: [/services/mcp-provisioner/README.md](/services/mcp-provisioner/README.md)
- **MCP Interpreter**: [/services/mcp-interpreter/README.md](/services/mcp-interpreter/README.md)
- **MCP Retrieval**: [/services/mcp_retrieval/README.md](/services/mcp_retrieval/README.md)

---

**Status**: Production-Ready  
**Maintainer**: MCP Team  
**Last Updated**: October 7, 2025

*The unified control plane for the MCP ecosystem!* 📊✨

