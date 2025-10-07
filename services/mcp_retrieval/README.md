# MCP Retrieval - Advanced Context Management

**Hierarchical retrieval, context pruning, and human-in-the-loop workflows**

## 📋 Overview

The **MCP Retrieval** service provides sophisticated context management capabilities including hierarchical retrieval across tiers, intelligent context pruning, human-in-the-loop approval workflows, and user feedback collection.

### Key Features

- **Hierarchical Retrieval**: Multi-tier context retrieval with token budgets
- **Context Pruning**: Dynamic pruning based on relevance, recency, importance
- **HITL Workflows**: Human approval for critical decisions
- **Feedback System**: Collect and analyze user feedback
- **Token Management**: Intelligent budget distribution
- **Strategy Selection**: Multiple retrieval strategies

## 🏗️ Architecture Role

### Position in MCP Ecosystem

```
┌──────────────────────────────────────────────────────────┐
│                   MCP Ecosystem                           │
│                                                           │
│        ┌──────────────┐         ┌──────────────┐        │
│        │Tier Manager  │────────▶│  Retrieval   │        │
│        │(Hierarchy)   │  Query  │   System     │        │
│        └──────────────┘         └──────────────┘        │
│               │                        │                 │
│               │                        ▼                 │
│               │                 ┌──────────────┐        │
│               │                 │   Context    │        │
│               │                 │   Pruning    │        │
│               │                 └──────────────┘        │
│               │                        │                 │
│               ▼                        ▼                 │
│        ┌──────────────┐         ┌──────────────┐        │
│        │  MCP Store   │◀────────│     HITL     │        │
│        │  (Storage)   │  Store  │  Workflows   │        │
│        └──────────────┘         └──────────────┘        │
│               │                        │                 │
│               ▼                        ▼                 │
│        ┌──────────────────────────────────────┐         │
│        │      MCP Orchestrator                │         │
│        │      (Pattern Execution)             │         │
│        └──────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────┘
```

### Core Responsibilities

1. **Hierarchical Retrieval**
   - Multi-tier context aggregation
   - Token budget distribution
   - Tier weight configuration
   - Strategy-based retrieval

2. **Context Pruning**
   - Relevance-based pruning
   - Recency-based pruning
   - Importance scoring
   - Hybrid strategies

3. **HITL Workflows**
   - Approval request management
   - Queue management
   - Audit trail generation
   - Decision tracking

4. **Feedback Collection**
   - User feedback recording
   - Sentiment analysis
   - Trend identification
   - Quality metrics

## 🔗 Service Interactions

### Inbound: Services That Use Retrieval

| Service | Use Case | Integration |
|---------|----------|-------------|
| **MCP Orchestrator** | Get context for patterns | Hierarchical retrieval + pruning |
| **MCP Gateway** | Route with context | Initial context retrieval |
| **Dashboard UI** | Query interface | All retrieval features |
| **MCP Tier Manager** | Tier-specific queries | Coordinated retrieval |

### Outbound: Services Retrieval Depends On

| Service | Purpose | Usage |
|---------|---------|-------|
| **MCP Tier Manager** | Tier hierarchy | Get tier relationships |
| **MCP Store** | Knowledge storage | Retrieve actual content |
| **MCP Performance Store** | Retrieval metrics | Track performance |
| **MCP Logs** | Operation logging | Log all retrievals |

## 🎯 Integration Points

### With MCP Tier Manager
```python
from mcp_retrieval import HierarchicalRetriever

retriever = HierarchicalRetriever()

# Retrieve across tier hierarchy
result = await retriever.retrieve(
    query="What are our API guidelines?",
    client_tier_id="tier_client_123",
    strategy="bottom_up",
    token_budget=4000,
    tier_weights={
        "client": 0.4,
        "project": 0.3,
        "team": 0.2,
        "company": 0.1
    }
)
```

### With MCP Orchestrator
```python
from mcp_retrieval import ContextPruner, PruningStrategy

# Retrieve and prune context
raw_context = await retriever.retrieve(query, tier_id, token_budget=8000)

pruner = ContextPruner()
pruned = pruner.prune(
    context_items=raw_context.items,
    max_tokens=4000,
    strategy=PruningStrategy.HYBRID
)

# Use in orchestration
result = await orchestrator.execute_pattern(
    pattern="rag",
    query=query,
    context=pruned.items
)
```

### With Dashboard (HITL)
```python
from mcp_retrieval import HITLWorkflow, ApprovalType

workflow = HITLWorkflow()

# Create approval request
request = await workflow.create_approval_request(
    title="Deploy ML Model v2",
    description="New model with 5% accuracy improvement",
    approval_type=ApprovalType.DEPLOYMENT,
    metadata={"model": "v2.0.0", "accuracy": 0.95}
)

# Check status
status = await workflow.get_request_status(request.request_id)

# Approve/reject
await workflow.review_request(
    request.request_id,
    action="approve",
    reviewer_id="user_123",
    comments="Looks good!"
)
```

## 🚀 Core Components

### 1. Hierarchical Retriever
```python
from mcp_retrieval import HierarchicalRetriever, TierConfig

retriever = HierarchicalRetriever()

# Configure tier weights
tier_configs = [
    TierConfig(name="client", weight=0.4),
    TierConfig(name="project", weight=0.3),
    TierConfig(name="team", weight=0.2),
    TierConfig(name="company", weight=0.1)
]

result = await retriever.retrieve(
    query="Security best practices",
    client_tier_id="tier_123",
    tier_configs=tier_configs,
    token_budget=4000
)

print(f"Retrieved {len(result.items)} items")
print(f"Used {result.total_tokens} tokens")
print(f"Tiers involved: {result.tiers_used}")
```

### 2. Context Pruner
```python
from mcp_retrieval import ContextPruner, PruningStrategy, ContextItem

pruner = ContextPruner()

context_items = [
    ContextItem(content="...", relevance=0.9, recency_days=1, importance=0.8),
    ContextItem(content="...", relevance=0.7, recency_days=30, importance=0.6),
    # ... more items
]

# Prune to fit budget
result = pruner.prune(
    context_items=context_items,
    max_tokens=2000,
    strategy=PruningStrategy.HYBRID  # Relevance + Recency + Importance
)

print(f"Pruned from {len(context_items)} to {len(result.items)} items")
print(f"Token usage: {result.total_tokens}/{result.max_tokens}")
```

### 3. HITL Workflows
```python
from mcp_retrieval import HITLWorkflow, ApprovalQueue

workflow = HITLWorkflow()
queue = ApprovalQueue()

# Submit for approval
request = await workflow.create_approval_request(
    title="Schema Migration",
    description="Add new tables for v2 features",
    approval_type=ApprovalType.SCHEMA_CHANGE,
    required_approvers=["tech_lead", "dba"]
)

# Get pending requests
pending = await queue.get_pending_requests(
    filters={"type": ApprovalType.SCHEMA_CHANGE}
)

# Review
for req in pending:
    if meets_criteria(req):
        await workflow.review_request(
            req.request_id,
            action="approve",
            reviewer_id="tech_lead_123"
        )
```

### 4. Feedback System
```python
from mcp_retrieval import FeedbackSystem, FeedbackType

feedback_system = FeedbackSystem()

# Record feedback
await feedback_system.record_feedback(
    user_id="user_123",
    feedback_type=FeedbackType.QUALITY,
    rating=4,
    comment="Context was relevant but a bit verbose",
    metadata={"query_id": "q_456", "pattern": "rag"}
)

# Analyze feedback
analytics = await feedback_system.get_analytics(
    time_range="7d",
    groupby="pattern"
)

print(f"Average rating: {analytics.average_rating}")
print(f"Total feedback: {analytics.total_count}")
```

## 📊 Data Flow

```
Query → Tier Manager → Hierarchical Retrieval
             ↓               ↓
        Tier Configs    Context Items
             ↓               ↓
        Token Budget → Context Pruning
             ↓               ↓
        Pruned Context → HITL (if required)
             ↓               ↓
        Approved Context → Orchestrator
             ↓
        Feedback Collection
```

## 🔧 Configuration

### Environment Variables
```bash
MCP_RETRIEVAL_PORT=8014
MCP_RETRIEVAL_DB=postgresql://retrieval_db
TIER_MANAGER_URL=http://mcp-tier-manager:8013
MCP_STORE_URL=http://mcp-store:8008
DEFAULT_TOKEN_BUDGET=4000
```

## 📈 Metrics & Monitoring

### Key Metrics
- Retrieval operations per second
- Average retrieval latency
- Context pruning efficiency
- HITL approval rate
- Feedback sentiment distribution

### Health Checks
- `GET /health` - Service health
- `GET /metrics` - Prometheus metrics
- `GET /retrieval/stats` - Retrieval statistics

## 🎓 Usage Examples

### Complete Retrieval Pipeline
```python
# 1. Hierarchical Retrieval
retriever = HierarchicalRetriever()
raw_context = await retriever.retrieve(
    query="How to optimize database queries?",
    client_tier_id="tier_client_456",
    token_budget=6000
)

# 2. Context Pruning
pruner = ContextPruner()
pruned_context = pruner.prune(
    context_items=raw_context.items,
    max_tokens=3000,
    strategy=PruningStrategy.HYBRID
)

# 3. HITL (if sensitive operation)
if is_sensitive_query(query):
    workflow = HITLWorkflow()
    approval = await workflow.create_approval_request(
        title=f"Query: {query}",
        description="Accessing sensitive data",
        approval_type=ApprovalType.DATA_ACCESS
    )
    await workflow.wait_for_approval(approval.request_id)

# 4. Execute with context
result = await orchestrator.execute_pattern(
    pattern="rag",
    query=query,
    context=pruned_context.items
)

# 5. Collect Feedback
feedback_system = FeedbackSystem()
await feedback_system.record_feedback(
    user_id=user_id,
    feedback_type=FeedbackType.QUALITY,
    rating=user_rating,
    comment=user_comment
)
```

## 🔐 Security

- **Access Control**: Tier-based permissions
- **Data Filtering**: Sensitive content filtering
- **Approval Workflows**: HITL for critical operations
- **Audit Trails**: Complete operation logging
- **Encryption**: All data encrypted

## 🚦 Status

**Current**: Production-Ready ✅
- ✅ 42 unit tests (100% passing)
- ✅ 12 integration tests (100% passing)
- ✅ UI complete (4 pages)
- ✅ Documentation complete

## 📚 Related Services

- **MCP Tier Manager**: Provides tier hierarchy
- **MCP Store**: Knowledge storage
- **MCP Orchestrator**: Context consumer
- **MCP Performance Store**: Retrieval metrics
- **Dashboard UI**: User interface

## 🔮 Future Enhancements

- ML-based relevance scoring
- Adaptive token budgets
- Auto-pruning strategies
- Advanced HITL workflows
- Real-time feedback analysis

---

**Version**: 1.0.0  
**Status**: Production-Ready ✅  
**Maintainer**: MCP Team

