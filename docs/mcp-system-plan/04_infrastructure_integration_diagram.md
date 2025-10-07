---
llm_metadata:
  document_type: planning
  content_focus: technical
  platform:
    primary: mcp
    secondary: []
  status: active
  created_date: '2025-10-01'
  last_modified: '2025-10-07'
  topics:
  - event_sourcing
  - python
  - redis
  - llm_orchestration
  - context_management
  - rag
  - embeddings
  - monitoring
  - documentation
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Planning document about technical aspects of the mcp platform
  archive_reason: n/a
  historical_value: current
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# MCP Infrastructure Service - Integration Diagram

**Date:** October 6, 2025  
**Version:** 1.0.0  
**Purpose:** Visualize how MCP Infrastructure Service integrates with all MCP services and the ecosystem

---

## System Integration Overview

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                         ECOSYSTEM SERVICES                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ LLM Gateway  │  │ Memory Agent │  │ Source Agent │  │ Log Collector│     │
│  │   :5055      │  │    :5040     │  │    :5085     │  │    :5080     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │                  │              │
└─────────┼─────────────────┼──────────────────┼──────────────────┼──────────────┘
          │                 │                  │                  │
          │   ┌─────────────┴──────────────────┴──────────────────┴─────────┐
          │   │                                                               │
          │   │        🏗️ MCP INFRASTRUCTURE SERVICE (Port 5500)             │
          │   │           Memory & Coordination Backbone                     │
          │   │                                                               │
          │   │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
          │   │  │    Context     │  │    Training    │  │   Knowledge    │ │
          │   │  │   Management   │  │     State      │  │    Metadata    │ │
          │   │  │                │  │   Tracking     │  │   Management   │ │
          │   │  └────────────────┘  └────────────────┘  └────────────────┘ │
          │   │                                                               │
          │   │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
          │   │  │  Coordination  │  │   Performance  │  │  Event         │ │
          │   │  │   State        │  │   Metrics      │  │  Processing    │ │
          │   │  │   Manager      │  │   Analytics    │  │  (Pub/Sub)     │ │
          │   │  └────────────────┘  └────────────────┘  └────────────────┘ │
          │   │                                                               │
          │   │  Storage: Redis (In-Memory + Persistence)                    │
          │   │  Pattern: Ring Buffer + TTL + Event-Driven Updates           │
          │   │                                                               │
          │   └───────────────────┬───────────────────────────────────────────┘
          │                       │
          │                       │ (All MCP Services integrate here)
          │                       │
          ├───────────────────────┼───────────────────────────────────────────┐
          │                       │                                           │
          │                       ▼                                           │
┌─────────▼──────────────────────────────────────────────────────────────────┐ │
│                        MCP SERVICES ECOSYSTEM                               │ │
│                                                                             │ │
│  ┌──────────────────────────────────────────────────────────────────────┐ │ │
│  │                    ORCHESTRATION LAYER                                │ │ │
│  │                                                                        │ │ │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │ │ │
│  │  │     MCP      │ → │     MCP      │ → │     MCP      │            │ │ │
│  │  │ Interpreter  │   │ Orchestrator │   │   Gateway    │            │ │ │
│  │  │   :5100      │   │    :5200     │   │    :5300     │            │ │ │
│  │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │ │ │
│  │         │                  │                   │                      │ │ │
│  │         └──────────────────┴───────────────────┘                      │ │ │
│  │                          │                                            │ │ │
│  │         Stores: Query context, workflow state, routing decisions     │ │ │
│  │         Retrieves: Hot MCP metrics, coordination state               │ │ │
│  │                                                                        │ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │ │
│                                                                             │ │
│  ┌──────────────────────────────────────────────────────────────────────┐ │ │
│  │                  LIFECYCLE MANAGEMENT LAYER                           │ │ │
│  │                                                                        │ │ │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │ │ │
│  │  │     MCP      │   │     MCP      │   │     MCP      │            │ │ │
│  │  │ Provisioner  │   │   Registry   │   │   Composer   │            │ │ │
│  │  │   :5400 ✅   │   │    :5550     │   │    :5600     │            │ │ │
│  │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │ │ │
│  │         │                  │                   │                      │ │ │
│  │         └──────────────────┴───────────────────┘                      │ │ │
│  │                          │                                            │ │ │
│  │         Stores: Instance context, lifecycle events, compositions     │ │ │
│  │         Retrieves: Existing context, coordination state              │ │ │
│  │                                                                        │ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │ │
│                                                                             │ │
│  ┌──────────────────────────────────────────────────────────────────────┐ │ │
│  │                    TRAINING LAYER                                     │ │ │
│  │                                                                        │ │ │
│  │  ┌──────────────────────────────────────────────────────────────┐   │ │ │
│  │  │                 Training Coordinator (:5700)                  │   │ │ │
│  │  │                                                                │   │ │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │ │ │
│  │  │  │ Extraction  │  │Normalization│  │  Embedding  │          │   │ │ │
│  │  │  │   Workers   │ →│   Workers   │ →│   Workers   │          │   │ │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │   │ │ │
│  │  └──────────────────────────────────────────────────────────────┘   │ │ │
│  │                          │                                            │ │ │
│  │         Stores: Training phase, progress, statistics, checkpoints    │ │ │
│  │         Retrieves: Previous training state, knowledge metadata       │ │ │
│  │                                                                        │ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │ │
│                                                                             │ │
│  ┌──────────────────────────────────────────────────────────────────────┐ │ │
│  │                  DEPLOYED MCP INSTANCES                               │ │ │
│  │                                                                        │ │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │ │
│  │  │ Client   │  │ Project  │  │ Company  │  │Ecosystem │            │ │ │
│  │  │MCP (T0)  │  │MCP (T1)  │  │MCP (T2)  │  │MCP (T4)  │            │ │ │
│  │  │ :9001    │  │ :9002    │  │ :9003    │  │ :9004    │            │ │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │ │ │
│  │       │             │             │              │                    │ │ │
│  │       └─────────────┴─────────────┴──────────────┘                   │ │ │
│  │                          │                                            │ │ │
│  │         Stores: Query metrics, performance data, access patterns     │ │ │
│  │         Retrieves: Context for query optimization                    │ │ │
│  │                                                                        │ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │ │
└─────────────────────────────────────────────────────────────────────────────┘ │
                                                                                 │
                                      ▲                                          │
                                      │                                          │
                                      └──────────────────────────────────────────┘
                                            (Feedback loop)
```

---

## Data Flow Patterns

### 1. MCP Provisioning Flow

```
User Request
    ↓
MCP Provisioner
    ↓ (1) Provision MCP Instance
    ↓
MCP Infrastructure ← (2) Store initial context
    - context_type: "instance"
    - data: {client_id, tier, config}
    - ttl: 7200 (2 hours)
    ↓
Redis (Persist)
    ↓
Pub/Sub Event → (3) "mcp.provisioned"
    ↓
All MCP Services (Notification)
```

### 2. Training Pipeline Flow

```
Training Request
    ↓
Training Coordinator
    ↓ (1) Start extraction
    ↓
MCP Infrastructure ← (2) Initialize training state
    - phase: "extraction"
    - progress: 0.0
    - sources: [...]
    ↓
Workers (Extract, Normalize, Embed)
    ↓ (3) Progress updates
    ↓
MCP Infrastructure ← (4) Update training state
    - phase: "embedding"
    - progress: 0.65
    - statistics: {...}
    ↓
Redis (Persist) + Pub/Sub Event → "mcp.training.progress"
    ↓
Dashboard (Real-time updates via WebSocket)
```

### 3. Query Routing Flow

```
Query Request
    ↓
MCP Gateway
    ↓ (1) Get hot MCPs
    ↓
MCP Infrastructure → (2) Retrieve metrics
    - Returns: [{mcp_id, queries_last_hour, response_time}]
    ↓
MCP Gateway (3) Route to best MCP
    ↓
Selected MCP Instance
    ↓ (4) Process query
    ↓
MCP Gateway (5) Track query
    ↓
MCP Infrastructure ← (6) Update metrics
    - queries_total++
    - avg_response_time: update
    - last_accessed: now()
```

### 4. Multi-MCP Coordination Flow

```
Complex Query (requires multiple MCPs)
    ↓
MCP Orchestrator
    ↓ (1) Identify required MCPs
    ↓
MCP Infrastructure ← (2) Start coordination
    - operation_id: uuid
    - operation_type: "multi_mcp_query"
    - involved_services: ["gateway", "orchestrator"]
    - mcp_ids: ["mcp-1", "mcp-2", "mcp-3"]
    ↓
Execute Query on Each MCP
    ↓ (3) Update coordination state
    ↓
MCP Infrastructure ← (4) Track progress
    - status: "step_1_complete"
    - context: {results_so_far}
    ↓
Combine Results
    ↓ (5) Complete coordination
    ↓
MCP Infrastructure ← (6) Store final state
    - status: "complete"
    - context: {final_results}
```

---

## Integration Patterns

### Pattern 1: Context Storage (Every Service)

```python
from services.shared.clients.mcp_infrastructure_client import MCPInfraClient

mcp_infra = MCPInfraClient()

# After any significant operation
await mcp_infra.store_context(
    mcp_id=mcp_id,
    context_type="operation",
    data={
        "operation": "provision",
        "timestamp": datetime.utcnow().isoformat(),
        "result": "success"
    },
    ttl=3600
)
```

### Pattern 2: Training Progress (Training Coordinator)

```python
# Initialize training
await mcp_infra.store_training_state(
    mcp_id=mcp_id,
    phase="extraction",
    progress=0.0,
    sources=data_sources
)

# Update progress
async for progress in training_stream:
    await mcp_infra.update_training_state(
        mcp_id=mcp_id,
        phase=progress.phase,
        progress=progress.percentage,
        statistics=progress.stats
    )
```

### Pattern 3: Performance Tracking (MCP Gateway)

```python
# Before routing
hot_mcps = await mcp_infra.get_hot_mcps(tier=0, limit=5)
selected_mcp = load_balancer.select(hot_mcps)

# After query
await mcp_infra.update_metrics(
    mcp_id=selected_mcp.id,
    query_count=1,
    response_time=elapsed_ms
)
```

### Pattern 4: Coordination (MCP Orchestrator)

```python
# Start multi-service operation
coordination_id = await mcp_infra.start_coordination(
    operation_type="workflow",
    involved_services=["gateway", "orchestrator", "interpreter"],
    mcp_ids=required_mcps
)

# Update as workflow progresses
await mcp_infra.update_coordination(
    coordination_id,
    status="step_3_complete",
    context={"results": step_results}
)
```

---

## WebSocket Event Streams

### Real-Time MCP Events

```javascript
// Frontend dashboard connection
const ws = new WebSocket('ws://localhost:8150/api/v1/events/mcp/mcp-123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.event_type) {
    case 'state_changed':
      updateMCPStatus(data.mcp_id, data.new_state);
      break;
    
    case 'training_progress':
      updateProgressBar(data.mcp_id, data.progress);
      break;
    
    case 'query_received':
      incrementQueryCounter(data.mcp_id);
      break;
    
    case 'knowledge_updated':
      refreshKnowledgeGraph(data.mcp_id);
      break;
  }
};
```

### Training Event Stream

```javascript
// Training dashboard connection
const ws = new WebSocket('ws://localhost:8150/api/v1/events/training');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event_type === 'training_progress') {
    updateTrainingPipeline({
      mcp_id: data.mcp_id,
      phase: data.phase,
      progress: data.progress,
      eta: data.estimated_completion
    });
  }
};
```

---

## Key Benefits

### For MCP Services

1. **Reduced Boilerplate** - No need for each service to implement context management
2. **Consistent State** - Single source of truth for MCP operational state
3. **Easy Coordination** - Simple API for multi-service coordination
4. **Performance Insights** - Automatic metrics collection and analytics

### For Ecosystem

1. **Observability** - Centralized visibility into all MCP operations
2. **Debugging** - Complete audit trail of MCP lifecycle events
3. **Optimization** - Data-driven insights for resource allocation
4. **Integration** - Clean integration point for new services

### For Users

1. **Transparency** - Real-time visibility into training and query execution
2. **Reliability** - Automatic error tracking and recovery
3. **Performance** - Optimized routing based on real-time metrics
4. **Analytics** - Comprehensive usage and performance analytics

---

## Comparison with Memory Agent

| Aspect | Memory Agent | MCP Infrastructure |
|--------|--------------|-------------------|
| **Scope** | General operational memory | MCP-specific context |
| **Granularity** | Service-level events | MCP instance-level |
| **Analytics** | Basic statistics | MCP-specific insights |
| **Coordination** | Event correlation | Multi-MCP workflows |
| **Duration** | Short-term (1 hour default) | Variable (1 hour - 7 days) |
| **Integration** | All ecosystem services | MCP services + select ecosystem |
| **Real-time** | Pub/Sub events | Pub/Sub + WebSockets |

---

## Implementation Priority

**Phase 1: Core Infrastructure (Week 1)** ✅
- Context storage and retrieval
- Redis persistence
- Basic API endpoints

**Phase 2: Training State (Week 2)** 🔄
- Training phase tracking
- Progress monitoring
- Integration with Training Coordinator

**Phase 3: Coordination & Analytics (Week 3)** 📋
- Multi-service coordination
- Performance metrics
- WebSocket events

**Phase 4: Advanced Features (Week 4)** 📋
- LLM-powered insights
- Auto-scaling recommendations
- Predictive analytics

---

## Related Documentation

- **Design Spec:** [`MCP_INFRASTRUCTURE_SERVICE_DESIGN.md`](./MCP_INFRASTRUCTURE_SERVICE_DESIGN.md)
- **System Architecture:** [`MCP_SYSTEM_ARCHITECTURE.md`](./MCP_SYSTEM_ARCHITECTURE.md)
- **Memory Agent:** `/services/memory-agent/README.md`
- **Ecosystem Integration:** [`ECOSYSTEM_INTEGRATION_GUIDE.md`](./ECOSYSTEM_INTEGRATION_GUIDE.md)

---

*Last Updated: October 6, 2025*  
*Version: 1.0.0*  
*Status: Design Complete*

