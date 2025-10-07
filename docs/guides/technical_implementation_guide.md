---
llm_metadata:
  document_type: guide
  content_focus: operational
  platform:
    primary: shared
    secondary: []
  status: active
  created_date: '2025-10-01'
  last_modified: '2025-10-07'
  topics:
  - microservices
  - event_sourcing
  - python
  - langgraph
  - llm_orchestration
  - rag
  - testing
  - deployment
  - security
  - monitoring
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about operational aspects of the shared platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 🔧 Technical Implementation Guide - Enhanced Roadmap v2.0

**Document Version:** 1.0  
**Date:** October 3, 2025  
**Status:** Production-Ready Architecture  
**Audience:** Development Team, DevOps, Architects

---

## 📋 Table of Contents

1. [Service Architecture Audit](#service-architecture-audit)
2. [Implementation Workflow with Logging](#implementation-workflow-with-logging)
3. [Service-Specific Implementation Details](#service-specific-implementation-details)
4. [Logging Integration Patterns](#logging-integration-patterns)
5. [Data Flow Specifications](#data-flow-specifications)
6. [Configuration Requirements](#configuration-requirements)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Guide](#deployment-guide)

---

## 🏗️ Service Architecture Audit

### **Service Inventory & Status**

| Service | Port | Status | Capabilities | Integration Points |
|---------|------|--------|--------------|-------------------|
| **Interpreter** | 5120 | ✅ Ready | NL processing, LangGraph, ecosystem awareness | All services |
| **Orchestrator** | 5099 | ✅ Ready | Workflow coordination, service registry | All services |
| **Memory Agent** | 5090 | ✅ Ready | Context storage, TTL management | Orchestrator, all workflows |
| **Log Collector** | 5040 | ✅ Ready | Centralized logging, statistics | All services (universal) |
| **Source Agent** | TBD | ✅ Ready | GitHub/Jira/Confluence connectors | Doc Store, Orchestrator |
| **Discovery Agent** | 5045 | ✅ Ready | Service registration, OpenAPI parsing | Orchestrator |
| **LLM Gateway** | 5000 | ✅ Ready | Multi-provider LLM access | Interpreter, decomposer |
| **Project Simulation** | TBD | ✅ Ready | Timeline analysis, simulation | Analysis Service |
| **Analysis Service** | TBD | ✅ Ready | Complexity analysis, pattern detection | Project Simulation |
| **Summarizer Hub** | 5160 | ✅ Ready | Content summarization | Multiple services |
| **Code Analyzer** | TBD | ✅ Ready | Code pattern analysis | Source Agent |
| **User Store** | TBD | ✅ Ready | Team data, skills matching | Project Planning |
| **Project Planning** | TBD | ✅ Ready | Roadmap generation, planning | Orchestrator |
| **Doc Store** | 5140 | ✅ Ready | Document storage, full-text search | All services |
| **Prompt Store** | 5110 | ✅ Ready | Prompt management, versioning | LLM Gateway, AI services |

---

## 📊 Implementation Workflow with Logging

### **Complete Workflow with Log Collector Integration**

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 1: USER QUERY                                              │
│  Input: "Plan authentication for my mobile app with my team"    │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 2: INTERPRETER SERVICE (Port 5120)                         │
│  ─────────────────────────────────────────────────────────────  │
│  Endpoint: POST /natural-query                                   │
│  Input: { query, user_id, context }                             │
│                                                                  │
│  Processing:                                                     │
│  1. Log start: POST /logs { level: "INFO", service: "interpreter" } │
│  2. Advanced NLP engine analyzes query                           │
│  3. Extract entities: feature_type, platform, team_id           │
│  4. Generate structured intent                                   │
│  5. Log completion: POST /logs { result: "success" }            │
│                                                                  │
│  Output: { interpreted_intent, entities, confidence }           │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 3: ORCHESTRATOR SERVICE (Port 5099)                        │
│  ─────────────────────────────────────────────────────────────  │
│  Endpoint: POST /workflows                                       │
│  Input: { intent, workflows: ["A", "B", "C", "D"] }            │
│                                                                  │
│  Processing:                                                     │
│  1. Log workflow creation: POST /logs { workflow_id: "wf-123" } │
│  2. Query Discovery Agent for service registry                  │
│  3. Create workflow orchestration plan                          │
│  4. Initialize Memory Agent context                             │
│  5. Launch parallel workflows                                   │
│  6. Log workflow start: POST /logs { workflows: 4, status: "started" } │
│                                                                  │
│  Output: { workflow_id, sub_workflows: [A, B, C, D] }          │
└──────────────────────────────────────────────────────────────────┘
             │
             ├────────────────────────────────────────┐
             │                                        │
             ▼                                        ▼
┌───────────────────────┐              ┌───────────────────────┐
│  WORKFLOW A:          │              │  WORKFLOW B:          │
│  AI Decomposition     │              │  Historical Context   │
│  ─────────────────   │              │  ─────────────────   │
│  Services:            │              │  Services:            │
│  - LLM Gateway        │              │  - Source Agent       │
│  - Prompt Store       │              │  - Doc Store          │
│  - Doc Store          │              │                       │
│                       │              │  LOG EACH STEP:       │
│  LOG EACH STEP:       │              │  POST /logs {         │
│  POST /logs {         │              │    service,           │
│    service,           │              │    operation,         │
│    operation,         │              │    duration_ms,       │
│    duration_ms,       │              │    workflow_id        │
│    workflow_id        │              │  }                    │
│  }                    │              │                       │
│                       │              │  Fetch Documents:     │
│  AI Processing:       │              │  - Confluence: 15     │
│  - Generate stories   │              │  - Jira: 23           │
│  - Create tasks       │              │  - GitHub: 47         │
│  - Assess complexity  │              │                       │
│                       │              │  Store in Memory      │
│  Store results in     │              │  Agent: workflow_b    │
│  Memory Agent:        │              │                       │
│  workflow_a           │              │                       │
└───────────────────────┘              └───────────────────────┘
             │                                        │
             ▼                                        ▼
┌───────────────────────┐              ┌───────────────────────┐
│  WORKFLOW C:          │              │  WORKFLOW D:          │
│  Timeline Analysis    │              │  Team Skills          │
│  ─────────────────   │              │  ─────────────────   │
│  Services:            │              │  Services:            │
│  - Project Sim        │              │  - User Store         │
│  - Analysis Service   │              │  - Memory Agent       │
│  - Summarizer Hub     │              │                       │
│  - Code Analyzer      │              │  LOG EACH STEP:       │
│                       │              │  POST /logs {         │
│  LOG EACH STEP:       │              │    service,           │
│  POST /logs {         │              │    team_query,        │
│    service,           │              │    members_found,     │
│    analysis_type,     │              │    workflow_id        │
│    documents_count,   │              │  }                    │
│    workflow_id        │              │                       │
│  }                    │              │  Operations:          │
│                       │              │  - Query team data    │
│  Operations:          │              │  - Calculate capacity │
│  - Plot timeline      │              │  - Match skills       │
│  - Analyze patterns   │              │  - Assess proficiency │
│  - Extract insights   │              │                       │
│  - Generate report    │              │  Store in Memory      │
│                       │              │  Agent: workflow_d    │
│  Store in Memory      │              │                       │
│  Agent: workflow_c    │              │                       │
└───────────────────────┘              └───────────────────────┘
             │                                        │
             └─────────────┬──────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 4: MEMORY AGENT AGGREGATION (Port 5090)                   │
│  ─────────────────────────────────────────────────────────────  │
│  Endpoint: GET /memory/list?workflow_id=wf-123                  │
│                                                                  │
│  Processing:                                                     │
│  1. Log aggregation start: POST /logs { operation: "aggregate" } │
│  2. Retrieve all workflow results:                              │
│     - workflow_a: AI decomposition results                      │
│     - workflow_b: Historical documents                          │
│     - workflow_c: Analysis insights                             │
│     - workflow_d: Team data                                     │
│  3. Link all artifacts:                                         │
│     - Documents → Doc Store                                     │
│     - Prompts → Prompt Store                                    │
│     - Users → User Store                                        │
│  4. Create synthesis document                                   │
│  5. Log aggregation complete: POST /logs { artifacts: 85 }      │
│                                                                  │
│  Output: { comprehensive_context_package }                      │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 5: PROJECT PLANNING SERVICE                                │
│  ─────────────────────────────────────────────────────────────  │
│  Endpoint: POST /api/v1/roadmaps/generate                       │
│  Input: { comprehensive_context_package }                       │
│                                                                  │
│  Processing:                                                     │
│  1. Log plan generation start: POST /logs                        │
│  2. Run dependency analysis                                     │
│     └─ Log: POST /logs { dependencies_analyzed: 47 }           │
│  3. Run timeline estimation                                     │
│     └─ Log: POST /logs { sprints_estimated: 3 }                │
│  4. Run milestone planning                                      │
│     └─ Log: POST /logs { milestones_created: 5 }               │
│  5. Run roadmap generation                                      │
│     └─ Log: POST /logs { roadmap_generated: true }             │
│  6. Generate 10-section report                                  │
│     └─ Log: POST /logs { report_sections: 10, pages: 22 }      │
│  7. Save to Doc Store                                           │
│  8. Log plan completion: POST /logs { plan_id, duration_ms }    │
│                                                                  │
│  Output: { comprehensive_development_plan }                     │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  LOG COLLECTOR CONSOLIDATION (Port 5040)                         │
│  ─────────────────────────────────────────────────────────────  │
│  GET /logs?workflow_id=wf-123                                    │
│  GET /stats                                                      │
│                                                                  │
│  Provides:                                                       │
│  - Complete workflow trace                                       │
│  - Performance metrics (duration per service)                    │
│  - Error tracking and debugging info                             │
│  - Service call statistics                                       │
│  - End-to-end observability                                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Service-Specific Implementation Details

### **1. Interpreter Service (Port 5120)**

**Current Capabilities:**
- ✅ Natural language query processing
- ✅ Intent recognition with confidence scores
- ✅ Entity extraction
- ✅ LangGraph workflow integration
- ✅ Ecosystem capabilities awareness

**API Endpoints:**
```
POST /natural-query
POST /execute-natural-workflow
GET /ecosystem/capabilities
POST /workflows/discover
POST /prompt/translate
GET /intents
```

**Enhanced Implementation:**

```python
# services/interpreter/domain/services/enhanced_interpreter.py

from typing import Dict, Any
import httpx
from datetime import datetime

class EnhancedInterpreterService:
    """Enhanced interpreter with full logging integration."""
    
    def __init__(self, log_collector_url: str):
        self.log_collector_url = log_collector_url
        self.client = httpx.AsyncClient()
    
    async def process_natural_query(
        self,
        query: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process natural language query with comprehensive logging."""
        
        start_time = datetime.now()
        workflow_id = f"wf-{int(start_time.timestamp() * 1000000)}"
        
        # Log query start
        await self._log({
            "level": "INFO",
            "service": "interpreter",
            "message": f"Processing natural language query",
            "context": {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "query_length": len(query),
                "operation": "natural_query_start"
            }
        })
        
        try:
            # Step 1: Preprocess query
            cleaned_query = self._preprocess_query(query)
            await self._log({
                "level": "DEBUG",
                "service": "interpreter",
                "message": "Query preprocessed",
                "context": {"workflow_id": workflow_id}
            })
            
            # Step 2: Extract intent and entities
            intent_result = await self._extract_intent(cleaned_query, context)
            await self._log({
                "level": "INFO",
                "service": "interpreter",
                "message": "Intent extracted",
                "context": {
                    "workflow_id": workflow_id,
                    "intent": intent_result["intent"],
                    "confidence": intent_result["confidence"]
                }
            })
            
            # Step 3: Generate structured output
            structured_intent = self._structure_intent(intent_result, context)
            
            # Log completion
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            await self._log({
                "level": "INFO",
                "service": "interpreter",
                "message": "Natural query processing complete",
                "context": {
                    "workflow_id": workflow_id,
                    "duration_ms": duration_ms,
                    "success": True
                }
            })
            
            return {
                "workflow_id": workflow_id,
                "interpreted_intent": structured_intent,
                "entities": intent_result["entities"],
                "confidence": intent_result["confidence"],
                "processing_time_ms": duration_ms
            }
            
        except Exception as e:
            # Log error
            await self._log({
                "level": "ERROR",
                "service": "interpreter",
                "message": f"Error processing query: {str(e)}",
                "context": {
                    "workflow_id": workflow_id,
                    "error_type": type(e).__name__
                }
            })
            raise
    
    async def _log(self, log_entry: Dict[str, Any]):
        """Send log to log collector."""
        try:
            await self.client.post(
                f"{self.log_collector_url}/logs",
                json=log_entry
            )
        except Exception as e:
            # Fail gracefully if logging fails
            print(f"Logging failed: {e}")
```

**Configuration:**
```yaml
# config.yaml
interpreter:
  port: 5120
  log_collector_url: "http://log-collector:5040"
  nlp_model: "advanced"
  confidence_threshold: 0.7
  max_query_length: 5000
```

---

### **2. Orchestrator Service (Port 5099)**

**Current Capabilities:**
- ✅ Workflow management
- ✅ Service registry
- ✅ Multi-service orchestration
- ✅ Event-driven processing
- ✅ LangGraph integration

**API Endpoints:**
```
POST /workflows (create workflow)
POST /workflows/{id}/execute
GET /workflows/executions/{id}
POST /registry/register
GET /registry (list services)
POST /query (NL query processing)
```

**Enhanced Implementation:**

```python
# services/orchestrator/domain/services/workflow_orchestrator.py

class EnhancedWorkflowOrchestrator:
    """Orchestrator with parallel workflow coordination and logging."""
    
    def __init__(
        self,
        log_collector_url: str,
        memory_agent_url: str,
        discovery_agent_url: str
    ):
        self.log_collector_url = log_collector_url
        self.memory_agent_url = memory_agent_url
        self.discovery_agent_url = discovery_agent_url
        self.client = httpx.AsyncClient()
    
    async def create_multi_workflow_execution(
        self,
        interpreted_intent: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create and execute multiple parallel workflows."""
        
        workflow_id = interpreted_intent.get("workflow_id")
        
        # Log workflow creation
        await self._log({
            "level": "INFO",
            "service": "orchestrator",
            "message": "Creating multi-workflow execution",
            "context": {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "operation": "workflow_creation"
            }
        })
        
        # Step 1: Query Discovery Agent for available services
        services = await self._discover_services()
        await self._log({
            "level": "INFO",
            "service": "orchestrator",
            "message": f"Discovered {len(services)} services",
            "context": {"workflow_id": workflow_id}
        })
        
        # Step 2: Initialize Memory Agent context
        await self._initialize_memory_context(workflow_id, interpreted_intent)
        
        # Step 3: Create workflow definitions
        workflows = {
            "workflow_a": self._create_ai_decomposition_workflow(interpreted_intent),
            "workflow_b": self._create_historical_context_workflow(interpreted_intent),
            "workflow_c": self._create_timeline_analysis_workflow(interpreted_intent),
            "workflow_d": self._create_team_skills_workflow(interpreted_intent)
        }
        
        await self._log({
            "level": "INFO",
            "service": "orchestrator",
            "message": "Workflows defined",
            "context": {
                "workflow_id": workflow_id,
                "workflows": list(workflows.keys())
            }
        })
        
        # Step 4: Execute workflows in parallel
        results = await asyncio.gather(*[
            self._execute_workflow(wf_id, wf_def, workflow_id)
            for wf_id, wf_def in workflows.items()
        ])
        
        # Step 5: Store all results in Memory Agent
        for i, (wf_id, result) in enumerate(zip(workflows.keys(), results)):
            await self._store_workflow_result(workflow_id, wf_id, result)
        
        await self._log({
            "level": "INFO",
            "service": "orchestrator",
            "message": "All workflows completed",
            "context": {
                "workflow_id": workflow_id,
                "completed_workflows": len(results),
                "success": all(r.get("success") for r in results)
            }
        })
        
        return {
            "workflow_id": workflow_id,
            "sub_workflows": workflows.keys(),
            "results": results,
            "status": "completed"
        }
    
    async def _execute_workflow(
        self,
        workflow_id: str,
        workflow_def: Dict[str, Any],
        parent_workflow_id: str
    ) -> Dict[str, Any]:
        """Execute a single workflow with logging."""
        
        start_time = datetime.now()
        
        await self._log({
            "level": "INFO",
            "service": "orchestrator",
            "message": f"Executing workflow: {workflow_id}",
            "context": {
                "workflow_id": parent_workflow_id,
                "sub_workflow_id": workflow_id,
                "operation": "workflow_execution"
            }
        })
        
        try:
            # Execute workflow steps
            result = await self._execute_workflow_steps(workflow_def)
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            await self._log({
                "level": "INFO",
                "service": "orchestrator",
                "message": f"Workflow {workflow_id} completed",
                "context": {
                    "workflow_id": parent_workflow_id,
                    "sub_workflow_id": workflow_id,
                    "duration_ms": duration_ms,
                    "success": True
                }
            })
            
            return {
                "workflow_id": workflow_id,
                "success": True,
                "result": result,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            await self._log({
                "level": "ERROR",
                "service": "orchestrator",
                "message": f"Workflow {workflow_id} failed: {str(e)}",
                "context": {
                    "workflow_id": parent_workflow_id,
                    "sub_workflow_id": workflow_id,
                    "error": str(e)
                }
            })
            raise
    
    async def _store_workflow_result(
        self,
        workflow_id: str,
        sub_workflow_id: str,
        result: Dict[str, Any]
    ):
        """Store workflow result in Memory Agent."""
        
        await self.client.post(
            f"{self.memory_agent_url}/memory/put",
            json={
                "key": f"{workflow_id}:{sub_workflow_id}",
                "content": result,
                "metadata": {
                    "workflow_id": workflow_id,
                    "sub_workflow_id": sub_workflow_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
        
        await self._log({
            "level": "DEBUG",
            "service": "orchestrator",
            "message": f"Stored workflow result in Memory Agent",
            "context": {
                "workflow_id": workflow_id,
                "sub_workflow_id": sub_workflow_id
            }
        })
```

**Configuration:**
```yaml
# config.yaml
orchestrator:
  port: 5099
  log_collector_url: "http://log-collector:5040"
  memory_agent_url: "http://memory-agent:5090"
  discovery_agent_url: "http://discovery-agent:5045"
  max_parallel_workflows: 10
  workflow_timeout_seconds: 300
```

---

### **3. Memory Agent Service (Port 5090)**

**Current Capabilities:**
- ✅ Context storage with TTL
- ✅ In-memory key-value store
- ✅ Session management
- ✅ Event correlation

**API Endpoints:**
```
POST /memory/put (store context)
GET /memory/list (retrieve with filters)
GET /memory/{key} (get specific context)
DELETE /memory/{key} (remove context)
```

**Enhanced Implementation:**

```python
# services/memory-agent/domain/services/workflow_context_manager.py

class WorkflowContextManager:
    """Manages workflow context with comprehensive linking."""
    
    def __init__(self, log_collector_url: str):
        self.log_collector_url = log_collector_url
        self.contexts: Dict[str, WorkflowContext] = {}
        self.client = httpx.AsyncClient()
    
    async def store_workflow_context(
        self,
        workflow_id: str,
        sub_workflow_id: str,
        result: Dict[str, Any],
        links: Dict[str, List[str]]  # Links to doc-store, prompt-store, user-store
    ) -> Dict[str, Any]:
        """Store workflow context with artifact links."""
        
        await self._log({
            "level": "INFO",
            "service": "memory-agent",
            "message": "Storing workflow context",
            "context": {
                "workflow_id": workflow_id,
                "sub_workflow_id": sub_workflow_id,
                "operation": "context_storage"
            }
        })
        
        # Create context entry
        context_entry = {
            "workflow_id": workflow_id,
            "sub_workflow_id": sub_workflow_id,
            "result": result,
            "links": {
                "documents": links.get("documents", []),  # doc-store://doc-id
                "prompts": links.get("prompts", []),      # prompt-store://prompt-id
                "users": links.get("users", [])           # user-store://user-id
            },
            "timestamp": datetime.now().isoformat(),
            "ttl_seconds": 3600  # 1 hour
        }
        
        # Store in memory
        key = f"{workflow_id}:{sub_workflow_id}"
        self.contexts[key] = context_entry
        
        await self._log({
            "level": "INFO",
            "service": "memory-agent",
            "message": "Context stored successfully",
            "context": {
                "workflow_id": workflow_id,
                "sub_workflow_id": sub_workflow_id,
                "documents_linked": len(context_entry["links"]["documents"]),
                "prompts_linked": len(context_entry["links"]["prompts"]),
                "users_linked": len(context_entry["links"]["users"])
            }
        })
        
        return {
            "success": True,
            "key": key,
            "links": context_entry["links"]
        }
    
    async def aggregate_workflow_contexts(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Aggregate all contexts for a workflow."""
        
        await self._log({
            "level": "INFO",
            "service": "memory-agent",
            "message": "Aggregating workflow contexts",
            "context": {
                "workflow_id": workflow_id,
                "operation": "context_aggregation"
            }
        })
        
        # Find all contexts for this workflow
        matching_contexts = {
            key: context
            for key, context in self.contexts.items()
            if context["workflow_id"] == workflow_id
        }
        
        # Aggregate all links
        aggregated_links = {
            "documents": [],
            "prompts": [],
            "users": []
        }
        
        for context in matching_contexts.values():
            aggregated_links["documents"].extend(context["links"]["documents"])
            aggregated_links["prompts"].extend(context["links"]["prompts"])
            aggregated_links["users"].extend(context["links"]["users"])
        
        # Remove duplicates
        for key in aggregated_links:
            aggregated_links[key] = list(set(aggregated_links[key]))
        
        await self._log({
            "level": "INFO",
            "service": "memory-agent",
            "message": "Context aggregation complete",
            "context": {
                "workflow_id": workflow_id,
                "sub_workflows": len(matching_contexts),
                "total_documents": len(aggregated_links["documents"]),
                "total_prompts": len(aggregated_links["prompts"]),
                "total_users": len(aggregated_links["users"])
            }
        })
        
        return {
            "workflow_id": workflow_id,
            "contexts": matching_contexts,
            "aggregated_links": aggregated_links,
            "context_count": len(matching_contexts)
        }
```

**Configuration:**
```yaml
# config.yaml
memory-agent:
  port: 5090
  log_collector_url: "http://log-collector:5040"
  default_ttl_seconds: 3600
  max_contexts: 10000
  cleanup_interval_seconds: 300
```

---

## 📝 Logging Integration Patterns

### **Universal Logging Client**

```python
# services/shared/infrastructure/logging/workflow_logger.py

import httpx
from typing import Dict, Any
from datetime import datetime

class WorkflowLogger:
    """Universal logging client for all services."""
    
    def __init__(self, service_name: str, log_collector_url: str):
        self.service_name = service_name
        self.log_collector_url = log_collector_url
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def log_workflow_start(
        self,
        workflow_id: str,
        operation: str,
        context: Dict[str, Any] = None
    ):
        """Log workflow start."""
        await self._send_log({
            "level": "INFO",
            "service": self.service_name,
            "message": f"Workflow started: {operation}",
            "context": {
                "workflow_id": workflow_id,
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
                **(context or {})
            }
        })
    
    async def log_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        step_data: Dict[str, Any]
    ):
        """Log individual workflow step."""
        await self._send_log({
            "level": "DEBUG",
            "service": self.service_name,
            "message": f"Workflow step: {step_name}",
            "context": {
                "workflow_id": workflow_id,
                "step_name": step_name,
                **step_data
            }
        })
    
    async def log_workflow_complete(
        self,
        workflow_id: str,
        duration_ms: float,
        success: bool,
        metrics: Dict[str, Any] = None
    ):
        """Log workflow completion."""
        await self._send_log({
            "level": "INFO",
            "service": self.service_name,
            "message": f"Workflow {'completed' if success else 'failed'}",
            "context": {
                "workflow_id": workflow_id,
                "duration_ms": duration_ms,
                "success": success,
                **(metrics or {})
            }
        })
    
    async def log_error(
        self,
        workflow_id: str,
        error: Exception,
        context: Dict[str, Any] = None
    ):
        """Log error with full context."""
        await self._send_log({
            "level": "ERROR",
            "service": self.service_name,
            "message": f"Error: {str(error)}",
            "context": {
                "workflow_id": workflow_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                **(context or {})
            }
        })
    
    async def _send_log(self, log_entry: Dict[str, Any]):
        """Send log to collector."""
        try:
            await self.client.post(
                f"{self.log_collector_url}/logs",
                json=log_entry
            )
        except Exception:
            # Fail silently - don't break workflow if logging fails
            pass
```

### **Logging at Each Service Integration Point**

```python
# Example: Source Agent with full logging

class SourceAgentWithLogging:
    """Source Agent with comprehensive logging."""
    
    def __init__(self):
        self.logger = WorkflowLogger(
            service_name="source-agent",
            log_collector_url="http://log-collector:5040"
        )
    
    async def fetch_historical_documents(
        self,
        workflow_id: str,
        sources: List[str],
        query_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch documents with full logging."""
        
        start_time = datetime.now()
        
        await self.logger.log_workflow_start(
            workflow_id,
            "historical_document_fetch",
            {"sources": sources, "params": query_params}
        )
        
        results = {
            "confluence": [],
            "jira": [],
            "github": []
        }
        
        # Fetch from each source
        for source in sources:
            try:
                await self.logger.log_workflow_step(
                    workflow_id,
                    f"fetch_{source}",
                    {"operation": "start"}
                )
                
                if source == "confluence":
                    docs = await self._fetch_confluence(query_params)
                    results["confluence"] = docs
                elif source == "jira":
                    docs = await self._fetch_jira(query_params)
                    results["jira"] = docs
                elif source == "github":
                    docs = await self._fetch_github(query_params)
                    results["github"] = docs
                
                await self.logger.log_workflow_step(
                    workflow_id,
                    f"fetch_{source}",
                    {
                        "operation": "complete",
                        "documents_fetched": len(docs)
                    }
                )
                
            except Exception as e:
                await self.logger.log_error(
                    workflow_id,
                    e,
                    {"source": source}
                )
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        total_docs = sum(len(docs) for docs in results.values())
        
        await self.logger.log_workflow_complete(
            workflow_id,
            duration_ms,
            True,
            {
                "total_documents": total_docs,
                "confluence_count": len(results["confluence"]),
                "jira_count": len(results["jira"]),
                "github_count": len(results["github"])
            }
        )
        
        return results
```

---

## 🎯 Quick Implementation Checklist

### **Phase 1: Logging Infrastructure** (Week 1)
- [ ] Deploy/verify Log Collector Service is operational
- [ ] Create WorkflowLogger shared library
- [ ] Test logging from 3 services
- [ ] Verify logs appear in Log Collector
- [ ] Create log query/visualization tools

### **Phase 2: Interpreter → Orchestrator** (Week 2)
- [ ] Enhance Interpreter with structured output
- [ ] Implement Orchestrator workflow creation
- [ ] Add logging at each step
- [ ] Test end-to-end flow
- [ ] Verify logs trace complete workflow

### **Phase 3: Memory Agent Integration** (Week 3)
- [ ] Enhance Memory Agent with linking capability
- [ ] Implement context storage from workflows
- [ ] Add doc-store, prompt-store, user-store links
- [ ] Test context aggregation
- [ ] Verify all links resolve correctly

### **Phase 4: Parallel Workflows** (Weeks 4-6)
- [ ] Implement Workflow A (AI Decomposition)
- [ ] Implement Workflow B (Historical Context)
- [ ] Implement Workflow C (Timeline Analysis)
- [ ] Implement Workflow D (Team Skills)
- [ ] Test parallel execution
- [ ] Verify all workflows log correctly

### **Phase 5: Final Report Generation** (Weeks 7-8)
- [ ] Enhance Project Planning Service
- [ ] Implement 10-section report generation
- [ ] Add artifact linking
- [ ] Generate PDF output
- [ ] End-to-end testing

---

## ✅ Success Criteria

1. **Logging Coverage:** 100% of workflow steps logged
2. **Traceability:** Every artifact linked to Memory Agent
3. **Performance:** < 5 minutes end-to-end
4. **Reliability:** 99% success rate
5. **Observability:** Complete workflow trace available

---

**Document Status:** Ready for Implementation  
**Next Steps:** Begin Phase 1 - Logging Infrastructure

