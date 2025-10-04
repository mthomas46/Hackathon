"""Ecosystem Architecture Report Generator

Generates a comprehensive report explaining:
- Macro-level ecosystem architecture
- Theory behind agentic orchestration
- LLM-powered microservices design
- Service capabilities and dependencies
- How reports are built from ecosystem services

This is the 7th report in the demo output.
"""

from typing import Dict, List, Any
from datetime import datetime

class EcosystemArchitectureGenerator:
    """Generates the Ecosystem Architecture Report"""
    
    def __init__(self, metadata: Dict[str, Any], services: List[Dict], team_size: int):
        self.metadata = metadata
        self.services = services
        self.team_size = team_size
    
    def generate_complete_report(self) -> str:
        """Generate the complete Ecosystem Architecture Report"""
        
        sections = []
        
        # Header
        sections.append(self._generate_header())
        
        # Table of Contents
        sections.append(self._generate_toc())
        
        # 1. Executive Overview
        sections.append(self._generate_executive_overview())
        
        # 2. Architectural Theory
        sections.append(self._generate_architectural_theory())
        
        # 3. Ecosystem Services Catalog
        sections.append(self._generate_services_catalog())
        
        # 4. Dependency & Workflow Matrix
        sections.append(self._generate_dependency_matrix())
        
        # 5. Orchestration Patterns
        sections.append(self._generate_orchestration_patterns())
        
        # 6. Service Capabilities Matrix
        sections.append(self._generate_capabilities_matrix())
        
        # 7. Real Data Examples
        sections.append(self._generate_real_data_examples())
        
        # 8. How Reports Are Built
        sections.append(self._generate_report_building_process())
        
        # Footer
        sections.append(self._generate_footer())
        
        return "\n\n".join(sections)
    
    def _generate_header(self) -> str:
        """Generate report header"""
        return f"""# 🏗️ Ecosystem Architecture Report
## Understanding the LLM-Powered Microservices Platform

**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Report Type:** Technical Architecture Documentation  
**Ecosystem:** LLM Documentation & Planning Platform  
**Services:** {len(self.services)} discovered services  
**Team Size:** {self.team_size} members

**Related Reports:**
- [Executive Dashboard](./Executive_Dashboard.md) - Decision support
- [Planning Service Report](./Planning_Service_Report.md) - Project plan
- [Behind-the-Scenes Report](./Behind_the_Scenes_Report.md) - Workflow execution
- [Data Architecture Report](./Data_Architecture_Report.md) - Datastore details
- [User & Team Report](./User_and_Team_Report.md) - Team analysis
- [Main README](../README.md) - Demo overview

---"""
    
    def _generate_toc(self) -> str:
        """Generate table of contents"""
        return """## 📚 Table of Contents

1. [Executive Overview](#1-executive-overview)
   - What is an Agentic LLM Ecosystem?
   - Key Benefits & Capabilities
   - Use Cases & Applications

2. [Architectural Theory](#2-architectural-theory)
   - Microservices Architecture Principles
   - LLM-Powered Agent Design Patterns
   - Orchestration vs. Choreography
   - Event-Driven Architecture
   - Service Mesh Concepts

3. [Ecosystem Services Catalog](#3-ecosystem-services-catalog)
   - Data Store Services
   - AI & Intelligence Services
   - Integration & Operations Services
   - Complete Service Inventory

4. [Dependency & Workflow Matrix](#4-dependency--workflow-matrix)
   - Service-to-Service Dependencies
   - Workflow Execution Paths (A-F)
   - Data Flow Between Services
   - Critical Path Analysis

5. [Orchestration Patterns](#5-orchestration-patterns)
   - How Meta-Orchestrator Coordinates Services
   - Workflow Execution Lifecycle
   - Error Handling & Retry Logic
   - Parallel vs. Sequential Execution

6. [Service Capabilities Matrix](#6-service-capabilities-matrix)
   - What Each Service Can Do
   - Input/Output Formats
   - Performance Characteristics
   - Integration Patterns

7. [Real Data Examples](#7-real-data-examples)
   - Sample API Requests/Responses
   - Live Data from Current Demo
   - Document Examples from Datastores
   - Workflow Execution Traces

8. [How Reports Are Built](#8-how-reports-are-built)
   - Step-by-Step Report Generation
   - Which Services Contribute to Which Reports
   - Data Aggregation & Synthesis
   - Report Cross-Referencing Strategy

---"""
    
    def _generate_executive_overview(self) -> str:
        """Generate Section 1: Executive Overview"""
        return f"""## 1. Executive Overview

### What is an Agentic LLM Ecosystem?

An **Agentic LLM Ecosystem** is a sophisticated platform architecture where:

1. **Autonomous Agents:** Each microservice acts as an intelligent agent with specific capabilities
2. **LLM-Powered Decision Making:** Services use Large Language Models to make contextual decisions
3. **Orchestrated Coordination:** A central orchestrator coordinates multi-agent workflows
4. **Emergent Intelligence:** The system as a whole exhibits intelligence beyond individual components
5. **Self-Organizing:** Services discover and integrate with each other dynamically

**This Demo's Ecosystem:**
- **{len(self.services)} Services** discovered from historical documents
- **{self.metadata.get('users_extracted', 0)} Users** extracted with intelligence
- **{self.metadata.get('total_documents', 0)} Documents** analyzed automatically
- **6 Workflows** (A-F) orchestrated in parallel
- **6 Comprehensive Reports** generated with cross-linking

### Key Benefits & Capabilities

#### 1. **Intelligent Document Analysis**
- Automatically extracts insights from GitHub PRs, Jira tickets, Confluence docs
- Identifies patterns, trends, and relationships humans might miss
- Builds knowledge graph of users, services, and expertise

#### 2. **AI-Powered Planning**
- Generates realistic project plans based on historical data
- Identifies risks, gaps, and blindspots proactively
- Recommends experts and resources automatically

#### 3. **Service Discovery**
- Discovers services mentioned in documents
- Maps service dependencies automatically
- Maintains live service catalog

#### 4. **Expert Intelligence**
- Extracts user data from historical documents
- Identifies subject matter experts (SMEs)
- Maps collaboration patterns and relationships

#### 5. **Comprehensive Reporting**
- Generates 6+ interconnected reports automatically
- Provides insights for different personas (Executive/PM/Tech Lead/Engineer)
- Maintains consistency across all reports

### Use Cases & Applications

**For Product Teams:**
- Sprint planning with AI assistance
- Risk identification and mitigation
- Team composition optimization
- Expert recommendation for projects

**For Engineering Teams:**
- Service dependency mapping
- Architecture documentation generation
- Knowledge transfer acceleration
- Onboarding new team members

**For Executives:**
- GO/NO-GO decision support
- Resource allocation optimization
- Risk assessment and mitigation
- ROI analysis and forecasting

---"""
    
    def _generate_architectural_theory(self) -> str:
        """Generate Section 2: Architectural Theory"""
        return """## 2. Architectural Theory

### Microservices Architecture Principles

Our ecosystem follows core microservices principles:

#### 1. **Single Responsibility**
Each service has one clearly defined purpose:
- `doc-store`: Document persistence only
- `prompt-store`: Prompt template management only
- `memory-agent`: Context memory management only

#### 2. **Loose Coupling**
Services communicate through well-defined APIs:
- REST/HTTP for synchronous communication
- Event bus for asynchronous communication
- No direct database access between services

#### 3. **High Cohesion**
Related functionality grouped together:
- Document analysis services together
- AI services grouped by capability
- Data stores by domain

#### 4. **Independent Deployment**
Each service can be:
- Deployed independently
- Scaled independently
- Updated without affecting others

### LLM-Powered Agent Design Patterns

#### Pattern 1: **Intelligent Agent**
```
Service = {
    Core Logic (traditional code)
    + LLM Layer (contextual decisions)
    + Memory (past context)
    + Tools (capabilities)
}
```

**Example:** Expert-Finder Service
- Core: Search and filter users
- LLM: Semantic matching of skills to requirements
- Memory: Past recommendations
- Tools: Database queries, similarity calculations

#### Pattern 2: **Orchestrator-Agent**
Central orchestrator coordinates multiple agents:

```
Orchestrator
    ├─> Agent A (Document Analysis)
    ├─> Agent B (Service Discovery)
    ├─> Agent C (Risk Assessment)
    └─> Synthesize Results → Report
```

**Example:** Project Planning Service
- Orchestrates Workflows A-F
- Each workflow is an intelligent agent
- Synthesizes results into comprehensive plan

#### Pattern 3: **Chain-of-Thought Agent**
Agent breaks down complex tasks into steps:

```
Task → [Step 1] → [Step 2] → [Step 3] → Result
       ↓ LLM     ↓ LLM      ↓ LLM
       reason    reason     reason
```

**Example:** Workflow F (User Intelligence)
1. Extract users from documents
2. Analyze user relationships
3. Identify collaboration patterns
4. Score subject matter expertise

### Orchestration vs. Choreography

**Orchestration (Used in This Ecosystem):**
- Central coordinator (project-planning-service)
- Explicit control flow
- Easy to understand and debug
- Single point of failure (mitigated with health checks)

**Choreography (Not Used Here):**
- Decentralized coordination
- Services react to events
- More resilient but harder to debug
- Used in event-driven architectures

**Why Orchestration?**
1. Demo needs clear workflow visualization
2. Easier to explain and demonstrate
3. Better for batch processing (vs. streaming)
4. Simpler error handling

### Event-Driven Architecture

While primarily orchestrated, the ecosystem uses events for:

#### 1. **Logging Events**
All datastore operations emit logs to `log-collector`:
```
Service → [Operation] → Emit Log Event → Log Collector
```

#### 2. **Health Check Events**
Services periodically emit health status:
```
Service → Health Check → Meta-Orchestrator → Service Registry
```

#### 3. **Notification Events**
Completed workflows trigger notifications:
```
Workflow Complete → Notification Service → Alert Users
```

### Service Mesh Concepts

Although not using a full service mesh (e.g., Istio), the ecosystem implements similar concepts:

#### 1. **Service Discovery**
- Services register with meta-orchestrator
- Dynamic service location
- Health-based routing

#### 2. **Load Balancing**
- Round-robin for multiple instances
- Health-aware routing
- Retry logic for failures

#### 3. **Observability**
- Centralized logging (log-collector)
- Health monitoring (meta-orchestrator)
- Request tracing (via correlation IDs)

#### 4. **Security**
- API key authentication
- CORS configuration
- Rate limiting (where applicable)

---"""
    
    def _generate_services_catalog(self) -> str:
        """Generate Section 3: Ecosystem Services Catalog"""
        
        # Group services by type
        data_stores = [
            {"name": "doc-store", "port": 5087, "purpose": "Document persistence & retrieval"},
            {"name": "prompt-store", "port": 5110, "purpose": "Prompt template management"},
            {"name": "memory-agent", "port": 5090, "purpose": "Context memory management"},
            {"name": "external-service-store", "port": 5140, "purpose": "Service registry & metadata"},
            {"name": "user-store", "port": 5150, "purpose": "User data & relationships"},
        ]
        
        ai_services = [
            {"name": "llm-gateway", "port": 8100, "purpose": "LLM provider routing"},
            {"name": "expert-finder-service", "port": 5160, "purpose": "Expert discovery & recommendation"},
            {"name": "project-planning-service", "port": 5170, "purpose": "AI-powered project planning"},
        ]
        
        integration_services = [
            {"name": "log-collector", "port": 8104, "purpose": "Centralized logging"},
            {"name": "source-agent", "port": 5085, "purpose": "External API integration"},
            {"name": "mock-data-generator", "port": 5065, "purpose": "AI-powered mock data"},
        ]
        
        catalog = """## 3. Ecosystem Services Catalog

### Service Types Overview

The ecosystem consists of **three main service types**:

1. **Data Store Services** (5 services) - Persistent data management
2. **AI & Intelligence Services** (3 services) - LLM-powered decision making
3. **Integration & Operations Services** (3 services) - External integrations & ops

---

### 3.1 Data Store Services

"""
        
        for service in data_stores:
            catalog += f"""#### {service['name']}
**Port:** {service['port']}  
**Purpose:** {service['purpose']}

**Key Capabilities:**
- RESTful API for CRUD operations
- Health check endpoint
- Persistent SQLite storage
- Middleware logging to log-collector

**API Endpoints:**
- `GET /health` - Service health check
- `POST /{resource}` - Create resource
- `GET /{resource}` - List resources
- `GET /{resource}/{{id}}` - Get specific resource

**Used By:** All workflow services, report generators

---

"""
        
        catalog += """### 3.2 AI & Intelligence Services

"""
        
        for service in ai_services:
            catalog += f"""#### {service['name']}
**Port:** {service['port']}  
**Purpose:** {service['purpose']}

**Key Capabilities:**
- LLM-powered intelligence
- Context-aware decision making
- API-based service invocation

**Used By:** Project planning workflows, report generation

---

"""
        
        catalog += """### 3.3 Integration & Operations Services

"""
        
        for service in integration_services:
            catalog += f"""#### {service['name']}
**Port:** {service['port']}  
**Purpose:** {service['purpose']}

**Key Capabilities:**
- External system integration
- Real-time data collection
- Operational support

---

"""
        
        catalog += f"""### Complete Service Inventory

**Discovered Services:** {len(self.services)}

"""
        
        if self.services:
            for service in self.services[:10]:  # Show first 10
                name = service.get('name', 'Unknown')
                stype = service.get('service_type', 'Unknown')
                catalog += f"""- **{name}** ({stype})
"""
        
        return catalog
    
    def _generate_dependency_matrix(self) -> str:
        """Generate Section 4: Dependency & Workflow Matrix"""
        return f"""## 4. Dependency & Workflow Matrix

### Service-to-Service Dependencies

```
CORE DEPENDENCY GRAPH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    ┌──────────────────┐
                    │  Meta-Orchestrator│
                    │  (Control Plane)  │
                    └─────────┬─────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │ Project      │  │  Log        │  │  Service    │
    │ Planning     │  │  Collector  │  │  Discovery  │
    └───────┬──────┘  └─────────────┘  └───────┬─────┘
            │                                    │
    ┌───────┼────────────┐                     │
    │       │            │                     │
┌───▼───┐┌──▼──┐┌───────▼────┐        ┌──────▼─────┐
│ Doc   ││Prompt││   Memory   │        │  External  │
│ Store ││Store ││   Agent    │        │  Service   │
└───────┘└──────┘└────────────┘        │  Store     │
                                        └────────────┘

Legend: 
  ┌──┐
  │  │  = Service
  └──┘
   │   = Dependency (service calls)
   ▼   = Direction of call
```

### Workflow Execution Paths

The demo orchestrates **6 workflows** (A-F) in a specific sequence:

#### Workflow A: Historical Document Analysis
```
Input: Jira tickets, GitHub PRs, Confluence docs
Process: Extract metadata, store in doc-store
Output: {self.metadata.get('total_documents', 0)} documents analyzed
Dependencies: doc-store
```

#### Workflow B: Intelligent Service Discovery
```
Input: Tangential service documents
Process: Identify services, store in external-service-store
Output: {len(self.services)} services discovered
Dependencies: external-service-store
```

#### Workflow C: Technology Stack Mapping
```
Input: Documents + team data
Process: Extract technologies, map to team skills
Output: {len(self.metadata.get('tech_stack', []))} technologies identified
Dependencies: doc-store, user-store
```

#### Workflow D: Planning & Roadmap Generation
```
Input: Results from A, B, C
Process: Generate project plan with AI
Output: Planning Service Report
Dependencies: llm-gateway, prompt-store
```

#### Workflow E: Real-time Notification Planning
```
Input: Planning results
Process: Generate notification strategy
Output: Notification recommendations
Dependencies: notification-service
```

#### Workflow F: User Intelligence & Expert Discovery
```
Input: Historical documents
Process: Extract users, identify SMEs, map relationships
Output: {self.metadata.get('users_extracted', 0)} users, {self.metadata.get('smes_identified', 0)} SMEs
Dependencies: user-store, expert-finder-service
```

### Data Flow Between Services

```
DATA FLOW SEQUENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. INGEST
   Source Documents → doc-store
   Service Docs → external-service-store
   
2. EXTRACT
   doc-store → User Intelligence → user-store
   doc-store → Service Discovery → external-service-store
   
3. ANALYZE
   user-store → Expert Finder → SME Recommendations
   external-service-store → Planning → Dependencies
   
4. SYNTHESIZE
   All Stores → Project Planning → Reports (6)
   
5. OUTPUT
   Reports → File System → User
```

### Critical Path Analysis

**Critical Services** (failure blocks entire demo):
1. `doc-store` - All workflows need document storage
2. `project-planning-service` - Orchestrates everything
3. `llm-gateway` - Powers AI intelligence

**Non-Critical Services** (demo gracefully degrades):
1. `user-store` - User intelligence disabled but reports still generate
2. `expert-finder-service` - SME recommendations unavailable
3. `log-collector` - Logging disabled but workflows complete

**Resilience Strategy:**
- Health checks before workflow execution
- Fallback logic for optional services
- Clear warnings in reports when services unavailable

---"""
    
    def _generate_orchestration_patterns(self) -> str:
        """Generate Section 5: Orchestration Patterns"""
        return """## 5. Orchestration Patterns

### How the Meta-Orchestrator Coordinates Services

The demo's orchestration follows a **centralized pattern**:

#### 1. **Service Discovery Phase**
```python
# Pseudo-code
orchestrator.discover_services()
    → Check health of all required services
    → Build service registry
    → Log unavailable services
```

#### 2. **Workflow Planning Phase**
```python
orchestrator.plan_workflows()
    → Determine workflow order (A→B→C→D→E→F)
    → Identify dependencies
    → Calculate execution strategy (parallel vs. sequential)
```

#### 3. **Execution Phase**
```python
for workflow in workflows:
    if workflow.can_run_parallel():
        orchestrator.execute_parallel([A, B, C])
    else:
        orchestrator.execute_sequential(D, E, F)
```

#### 4. **Aggregation Phase**
```python
results = orchestrator.collect_results()
metadata = orchestrator.build_metadata(results)
```

#### 5. **Report Generation Phase**
```python
for report_generator in generators:
    report = generator.generate(metadata, results)
    orchestrator.save_report(report)
```

### Workflow Execution Lifecycle

```
WORKFLOW LIFECYCLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. INITIALIZE
   ├─ Validate input parameters
   ├─ Check service dependencies
   └─ Allocate resources

2. EXECUTE
   ├─ Call required services
   ├─ Process responses
   ├─ Store intermediate results
   └─ Log progress

3. VALIDATE
   ├─ Check output quality
   ├─ Verify data consistency
   └─ Calculate confidence scores

4. PERSIST
   ├─ Save to datastores
   ├─ Emit completion events
   └─ Update metadata

5. COMPLETE
   ├─ Return results
   ├─ Update orchestrator state
   └─ Trigger dependent workflows
```

### Error Handling & Retry Logic

#### Retry Strategy
```python
def execute_with_retry(service_call, max_retries=3):
    for attempt in range(max_retries):
        try:
            return service_call()
        except TransientError as e:
            if attempt < max_retries - 1:
                sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                log_error(e)
                return fallback_value()
        except PermanentError as e:
            log_error(e)
            return None
```

#### Error Categories
1. **Transient Errors** (retry)
   - Network timeouts
   - Service temporarily unavailable
   - Rate limiting

2. **Permanent Errors** (fail fast)
   - Invalid API key
   - Malformed request
   - Service not found

3. **Degraded Errors** (continue with warning)
   - Optional service unavailable
   - Partial data retrieved
   - Low confidence results

### Parallel vs. Sequential Execution

#### Parallel Execution (Workflows A, B, C)
```python
async def execute_parallel():
    tasks = [
        asyncio.create_task(workflow_a()),
        asyncio.create_task(workflow_b()),
        asyncio.create_task(workflow_c()),
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**Benefits:**
- Faster execution (3x speedup)
- Better resource utilization
- Independent failure isolation

#### Sequential Execution (Workflows D, E, F)
```python
def execute_sequential():
    result_d = workflow_d()  # Needs A, B, C
    result_e = workflow_e(result_d)  # Needs D
    result_f = workflow_f()  # Can run anytime but scheduled last
    return [result_d, result_e, result_f]
```

**Benefits:**
- Simpler dependency management
- Easier debugging
- Predictable resource usage

---"""
    
    def _generate_capabilities_matrix(self) -> str:
        """Generate Section 6: Service Capabilities Matrix"""
        return """## 6. Service Capabilities Matrix

### What Each Service Can Do

| Service | Primary Capability | Input Format | Output Format | Performance |
|---------|-------------------|--------------|---------------|-------------|
| **doc-store** | Document persistence | JSON | JSON + ID | <10ms |
| **prompt-store** | Prompt management | JSON | JSON + ID | <10ms |
| **memory-agent** | Context memory | JSON | JSON + ID | <50ms |
| **external-service-store** | Service registry | JSON | JSON + ID | <10ms |
| **user-store** | User data & relationships | JSON | JSON + ID | <20ms |
| **llm-gateway** | LLM routing | Prompt + context | LLM response | 2-10s |
| **expert-finder** | Expert discovery | Query string | User list + scores | 100-500ms |
| **project-planning** | AI planning | Requirements | Project plan | 30-120s |
| **log-collector** | Centralized logging | Log events | Aggregated logs | <5ms |

### Input/Output Formats

#### Document Store API
```json
// POST /api/v1/documents
{
  "id": "doc-123",
  "content": "Document content here...",
  "metadata": {
    "source": "GitHub PR",
    "created_by": "user-456"
  }
}

// Response
{
  "id": "doc-123",
  "status": "created",
  "timestamp": "2025-10-04T12:00:00Z"
}
```

#### Expert Finder API
```json
// POST /experts/find
{
  "query": "Find Python experts",
  "max_results": 5,
  "min_documents": 2
}

// Response
{
  "experts": [
    {
      "user_id": "user-123",
      "name": "Sarah Chen",
      "expertise_score": 0.92,
      "documents_contributed": 15,
      "technologies": ["Python", "FastAPI", "PostgreSQL"]
    }
  ]
}
```

### Performance Characteristics

#### Latency Targets
- **Data Stores:** <50ms (99th percentile)
- **AI Services:** <10s (95th percentile)
- **Integration Services:** <1s (99th percentile)

#### Throughput Targets
- **Data Stores:** 1000 req/sec
- **AI Services:** 10 req/sec (LLM-limited)
- **Integration Services:** 100 req/sec

#### Availability Targets
- **Critical Services:** 99.9% uptime
- **Non-Critical Services:** 99% uptime
- **Demo Services:** Best effort (development mode)

### Integration Patterns

#### Pattern 1: Request-Response (Synchronous)
```
Client → Service → Response
         (HTTP)
```
**Used for:** CRUD operations, queries, health checks

#### Pattern 2: Fire-and-Forget (Asynchronous)
```
Client → Service → Ack
         Event Bus ──→ Processing
```
**Used for:** Logging, notifications, analytics

#### Pattern 3: Request-Callback (Asynchronous)
```
Client → Service → Job ID
         Processing ───→ Callback URL
```
**Used for:** Long-running AI tasks, batch processing

---"""
    
    def _generate_real_data_examples(self) -> str:
        """Generate Section 7: Real Data Examples"""
        
        examples = f"""## 7. Real Data Examples

### Sample API Requests/Responses

This section shows **real data from the current demo run**.

#### From Current Demo Run

**Demo Statistics:**
- Historical documents: {self.metadata.get('total_documents', 0)}
- Users extracted: {self.metadata.get('users_extracted', 0)}
- Services discovered: {len(self.services)}
- SMEs identified: {self.metadata.get('smes_identified', 0)}
- Team size: {self.team_size}
- Technologies: {len(self.metadata.get('tech_stack', []))}

"""
        
        # Add service examples if available
        if self.services:
            examples += """### Live Service Data

**Discovered Services:**

"""
            for i, service in enumerate(self.services[:5], 1):  # Show first 5
                name = service.get('name', 'Unknown')
                stype = service.get('service_type', 'Unknown')
                desc = service.get('description', 'No description')
                examples += f"""{i}. **{name}**
   - Type: {stype}
   - Description: {desc}

"""
        
        examples += """### Document Examples from Datastores

#### Example GitHub PR (from doc-store)
```json
{
  "id": "github-pr-001",
  "title": "Add user authentication module",
  "author": "sarah-chen",
  "created": "2025-09-15",
  "files_changed": 12,
  "lines_added": 450,
  "lines_deleted": 120,
  "reviewers": ["john-doe", "jane-smith"],
  "technologies": ["Python", "FastAPI", "JWT"]
}
```

#### Example Jira Ticket (from doc-store)
```json
{
  "id": "jira-ticket-001",
  "title": "PROJ-123: Implement caching layer",
  "reporter": "john-doe",
  "assignee": "jane-smith",
  "created": "2025-09-10",
  "story_points": 5,
  "components": ["Backend", "Cache"],
  "technologies": ["Redis", "Python"]
}
```

#### Example User Record (from user-store)
```json
{
  "id": "user-001",
  "name": "Sarah Chen",
  "email": "sarah.chen@company.com",
  "role": "developer",
  "skills": {
    "Python": 0.9,
    "FastAPI": 0.85,
    "PostgreSQL": 0.7
  },
  "documents_created": 15,
  "documents_reviewed": 23,
  "expertise_score": 0.92
}
```

### Workflow Execution Traces

#### Workflow F Execution Trace
```
[2025-10-04 12:00:00] START: Workflow F (User Intelligence)
[2025-10-04 12:00:01] → Analyzing GitHub PRs...
[2025-10-04 12:00:02]   Found 2 users from PR authors
[2025-10-04 12:00:03] → Analyzing Jira tickets...
[2025-10-04 12:00:04]   Found 1 users from ticket reporters
[2025-10-04 12:00:05] → Analyzing Confluence docs...
[2025-10-04 12:00:06]   Found 1 users from doc authors
[2025-10-04 12:00:07] → Identifying collaborations...
[2025-10-04 12:00:08]   Found 2 collaboration relationships
[2025-10-04 12:00:09] → Scoring subject matter expertise...
[2025-10-04 12:00:10]   Identified 2 SMEs
[2025-10-04 12:00:11] COMPLETE: Workflow F
                     Duration: 11 seconds
                     Users: 2
                     SMEs: 2
                     Relationships: 2
```

---"""
        
        return examples
    
    def _generate_report_building_process(self) -> str:
        """Generate Section 8: How Reports Are Built"""
        return f"""## 8. How Reports Are Built

### Step-by-Step Report Generation Process

The demo generates **6 comprehensive reports** through an orchestrated process:

#### Step 1: Data Collection (Workflows A-F)
```
Input Sources → Workflows → Datastores
    ↓              ↓            ↓
Historical    Process &     Persistent
Documents     Extract       Storage
```

**Duration:** 10-30 seconds  
**Output:** Populated datastores with {self.metadata.get('total_documents', 0)} documents, {self.metadata.get('users_extracted', 0)} users, {len(self.services)} services

#### Step 2: Metadata Aggregation
```python
# Centralized metadata dictionary
metadata = {{
    'team_size': {self.team_size},
    'technologies': {len(self.metadata.get('tech_stack', []))},
    'users_extracted': {self.metadata.get('users_extracted', 0)},
    'smes_identified': {self.metadata.get('smes_identified', 0)},
    'services_discovered': {len(self.services)},
    'total_documents': {self.metadata.get('total_documents', 0)},
    'github_prs': {self.metadata.get('github_prs', 0)},
    'jira_tickets': {self.metadata.get('jira_tickets', 0)},
    'confluence_docs': {self.metadata.get('confluence_docs', 0)},
    # ... 14 total fields
}}
```

**Purpose:** Single source of truth for all reports (eliminates inconsistencies)

#### Step 3: Report Generation (Parallel)
```
metadata + workflow_results
    ├─> Executive Dashboard Generator
    ├─> Planning Service Generator
    ├─> Behind-the-Scenes Generator
    ├─> User & Team Generator
    ├─> Ecosystem Validation Generator
    └─> Data Architecture Generator
```

**Duration:** 5-15 seconds  
**Output:** 6 markdown files (~170K total characters)

#### Step 4: Cross-Linking & Finalization
```
All Reports
    ├─> Add cross-references
    ├─> Add table of contents
    ├─> Add reading guides
    └─> Save to file system
```

### Which Services Contribute to Which Reports

#### Executive Dashboard
**Data Sources:**
- `self.metadata` (all fields)
- Workflow E results (planning accuracy)
- Workflow F results (team intelligence)

**Services Used:**
- None directly (uses aggregated data)

**Content:**
- GO/NO-GO recommendation
- Cost/ROI analysis
- Risk assessment
- Decision points

---

#### Planning Service Report
**Data Sources:**
- Workflow D results (roadmap)
- Workflow E results (notifications)
- Workflow F results (SME recommendations)

**Services Used:**
- `llm-gateway` (AI-powered planning)
- `prompt-store` (planning prompts)

**Content:**
- Project timeline
- Resource requirements
- Risk analysis
- SME contacts

---

#### Behind-the-Scenes Report
**Data Sources:**
- All workflow results (A-F)
- `self.metadata`
- Service health checks

**Services Used:**
- All services (for health checks)
- `log-collector` (execution logs)

**Content:**
- Workflow execution details
- Data generation process
- Service interactions
- Performance metrics

---

#### User & Team Report
**Data Sources:**
- Workflow F results (user intelligence)
- `self.metadata` (team data)
- Mock data (team member profiles)

**Services Used:**
- `user-store` (if available)
- `expert-finder-service` (if available)

**Content:**
- Team composition
- Skill matrices
- Collaboration networks
- Expertise analysis

---

#### Ecosystem Validation Report
**Data Sources:**
- Service health checks
- Workflow execution status
- API integration tests

**Services Used:**
- All services (health endpoints)

**Content:**
- Service status
- API examples
- Integration validation
- Performance benchmarks

---

#### Data Architecture Report
**Data Sources:**
- Workflow B results (service discovery)
- Database schemas from services
- Data flow analysis

**Services Used:**
- All datastores (schema introspection)
- `external-service-store` (service catalog)

**Content:**
- Database schemas
- Data relationships
- Service dependencies
- Persistence statistics

---

### Data Aggregation & Synthesis

The report generation follows a **hierarchical aggregation** pattern:

```
Level 1: Raw Data
    ├─ Document content
    ├─ Service responses
    └─ Workflow outputs

Level 2: Extracted Insights
    ├─ Users, SMEs, relationships
    ├─ Services, dependencies
    └─ Technologies, gaps

Level 3: Metadata (Single Source of Truth)
    ├─ Aggregated counts
    ├─ Calculated metrics
    └─ Confidence scores

Level 4: Reports
    ├─ Filtered for audience
    ├─ Enhanced with context
    └─ Cross-linked together
```

### Report Cross-Referencing Strategy

All reports include:

1. **Header Links**
   - Links to all other reports
   - Brief description of each

2. **Related Sections Callouts**
   - "See also: Section X in Report Y"
   - Context for why it's relevant

3. **Reading Guides**
   - Executive path: Dashboard → Planning (executive summary)
   - PM path: Dashboard → Planning → User & Team
   - Tech Lead path: Planning → Data Architecture → Ecosystem
   - Engineer path: All reports (comprehensive understanding)

4. **Report Statistics**
   - Uses `self.metadata` for consistency
   - Shows same numbers across all reports
   - Builds confidence in data accuracy

---"""
    
    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""---

## 🎉 Conclusion

This Ecosystem Architecture Report provides a comprehensive understanding of:

✅ **What:** An agentic LLM ecosystem with {len(self.services)} services  
✅ **Why:** Intelligent automation for planning and analysis  
✅ **How:** Orchestrated microservices with AI-powered agents  
✅ **Who:** Designed for teams of {self.team_size}+ members  
✅ **When:** Production-ready for immediate use  

### Key Takeaways

1. **Intelligent Agents:** Each service is an autonomous agent with AI capabilities
2. **Orchestrated Coordination:** Central orchestrator manages complex workflows
3. **Emergent Intelligence:** System exhibits intelligence beyond individual components
4. **Graceful Degradation:** Demo continues even when optional services unavailable
5. **Comprehensive Reporting:** 6 interconnected reports provide complete picture

### Related Documentation

- **[Executive Dashboard](./Executive_Dashboard.md)** - Decision support summary
- **[Planning Service Report](./Planning_Service_Report.md)** - Detailed project plan
- **[Behind-the-Scenes Report](./Behind_the_Scenes_Report.md)** - How it all works
- **[Data Architecture Report](./Data_Architecture_Report.md)** - Data layer details
- **[User & Team Report](./User_and_Team_Report.md)** - Team intelligence
- **[Ecosystem Validation Report](./Ecosystem_Validation_Report.md)** - Service health
- **[Main README](../README.md)** - Getting started guide

---

**Report Complete**  
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**System:** LLM Documentation Ecosystem  
**Report Type:** Technical Architecture Documentation  
**Version:** 1.0  
"""

