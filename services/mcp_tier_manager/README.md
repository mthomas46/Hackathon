# MCP Tier Manager - 5-Tier Hierarchical System

**Progressive context refinement across organizational tiers**

## 📋 Overview

The **MCP Tier Manager** implements a 5-tier hierarchical system (Client → Project → Team → Company → Ecosystem) for managing MCP knowledge at scale with progressive context refinement, inheritance, and access control.

### Key Features

- **5-Tier Hierarchy**: Client, Project, Team, Company, Ecosystem
- **Tier Management**: CRUD operations for all tiers
- **Inheritance & Cascading**: Policies flow down the hierarchy
- **Progressive Refinement**: Bottom-up, top-down, and hybrid strategies
- **Token Budget Management**: Intelligent distribution across tiers
- **Access Control**: Role-based access and tier isolation

## 🏗️ Architecture Role

### Position in MCP Ecosystem

```
┌──────────────────────────────────────────────────────────┐
│                   MCP Ecosystem                           │
│                                                           │
│             ┌──────────────┐                             │
│             │ Tier Manager │                             │
│             │  (5 Tiers)   │                             │
│             └──────────────┘                             │
│           /       |        \                             │
│          /        |         \                            │
│    ┌────────┐  ┌────────┐  ┌────────┐                  │
│    │Retrieval│  │Package │  │Context │                  │
│    │ System  │  │Manager │  │Pruning │                  │
│    └────────┘  └────────┘  └────────┘                  │
│          \        |         /                            │
│           \       |        /                             │
│        ┌─────────────────────┐                          │
│        │  MCP Orchestrator   │                          │
│        │  (Query Execution)  │                          │
│        └─────────────────────┘                          │
│                   │                                       │
│                   ▼                                       │
│            ┌─────────────┐                               │
│            │  MCP Store  │                               │
│            │  (Storage)  │                               │
│            └─────────────┘                               │
└──────────────────────────────────────────────────────────┘
```

### Tier Hierarchy

```
Ecosystem (Global Knowledge)
    ↓
Company (Organization-wide)
    ↓
Team (Cross-project)
    ↓
Project (Specific initiative)
    ↓
Client (Individual scope)
```

### Core Responsibilities

1. **Tier Lifecycle**
   - Create/update/delete tiers
   - Configure tier policies
   - Manage tier relationships
   - Track tier metadata

2. **Inheritance Management**
   - Policy cascading from parent to child
   - Configuration inheritance
   - Override mechanisms
   - Conflict resolution

3. **Context Refinement**
   - Bottom-up aggregation (Client → Ecosystem)
   - Top-down distribution (Ecosystem → Client)
   - Hybrid strategies (bidirectional)
   - Token budget optimization

4. **Access Control**
   - Role-based permissions
   - Tier isolation
   - Data visibility rules
   - Audit trails

## 🔗 Service Interactions

### Inbound: Services That Use Tier Manager

| Service | Use Case | Integration |
|---------|----------|-------------|
| **MCP Retrieval** | Get tier-specific context | Query by tier hierarchy |
| **MCP Orchestrator** | Execute tier-scoped patterns | Access tier configurations |
| **MCP Package Manager** | Package tier knowledge | Export/import by tier |
| **MCP Gateway** | Route requests by tier | Tier identification |
| **Dashboard UI** | Tier management interface | CRUD + visualization |

### Outbound: Services Tier Manager Depends On

| Service | Purpose | Usage |
|---------|---------|-------|
| **MCP Store** | Tier data persistence | Store tier metadata & relationships |
| **MCP Retrieval** | Context retrieval | Get knowledge for tiers |
| **MCP Performance Store** | Tier metrics | Track tier performance |
| **MCP Logs** | Tier operations logging | Audit tier changes |

## 🎯 Integration Points

### With MCP Retrieval
```python
# Hierarchical retrieval with tier context
from mcp_tier_manager import TierManager
from mcp_retrieval import HierarchicalRetriever

tier_manager = TierManager()
retriever = HierarchicalRetriever()

# Get client tier
client_tier = tier_manager.get_tier(client_id)

# Retrieve context progressively
result = await retriever.retrieve(
    query="What are our API best practices?",
    client_tier_id=client_tier.tier_id,
    strategy="bottom_up",  # Client → Project → Team → Company → Ecosystem
    token_budget=4000
)

print(f"Retrieved from tiers: {result.tiers_used}")
print(f"Total tokens: {result.total_tokens}")
```

### With MCP Orchestrator
```python
# Execute pattern with tier context
tier_context = tier_manager.get_tier_context(
    tier_id=project_tier.tier_id,
    include_ancestors=True  # Include Company and Ecosystem
)

result = await orchestrator.execute_pattern(
    pattern="rag",
    query="Analyze customer feedback",
    tier_context=tier_context
)
```

### With MCP Package Manager
```python
# Package tier-specific knowledge
tier_knowledge = tier_manager.export_tier_knowledge(team_tier.tier_id)

package = package_manager.create_package(
    metadata=PackageMetadata(
        name=f"team_{team_tier.name}_knowledge",
        version="1.0.0",
        tier_type="team"
    )
)

for item in tier_knowledge:
    package_manager.add_knowledge_to_package(
        package.package_id,
        content=item.content,
        relevance=item.relevance
    )
```

## 🚀 Core Components

### 1. Tier Management
```python
from mcp_tier_manager import TierManager, TierConfig, TierType

manager = TierManager()

# Create client tier
client_tier = manager.create_tier(
    TierConfig(
        name="acme_client",
        tier_type=TierType.CLIENT,
        parent_id=project_tier.tier_id,
        metadata={"department": "engineering"}
    )
)

# Update tier
manager.update_tier(
    client_tier.tier_id,
    TierConfig(metadata={"status": "active"})
)

# Get tier hierarchy
ancestors = manager.get_tier_ancestors(client_tier.tier_id)
descendants = manager.get_tier_descendants(company_tier.tier_id)
```

### 2. Progressive Refinement
```python
from mcp_tier_manager import ProgressiveRefiner, RefinementStrategy

refiner = ProgressiveRefiner(tier_manager)

# Bottom-up refinement (Client → Ecosystem)
result = await refiner.refine_context(
    query="What are our security policies?",
    client_tier_id=client_tier.tier_id,
    strategy=RefinementStrategy.BOTTOM_UP,
    token_budget=4000
)

# Top-down refinement (Ecosystem → Client)
result = await refiner.refine_context(
    query="Company-wide announcements",
    client_tier_id=client_tier.tier_id,
    strategy=RefinementStrategy.TOP_DOWN,
    token_budget=2000
)

# Hybrid (both directions)
result = await refiner.refine_context(
    query="Project guidelines",
    client_tier_id=client_tier.tier_id,
    strategy=RefinementStrategy.HYBRID,
    token_budget=5000
)
```

### 3. Inheritance & Cascading
```python
# Set policy at company level (cascades down)
manager.set_tier_policy(
    company_tier.tier_id,
    policy={
        "max_token_budget": 10000,
        "allowed_patterns": ["rag", "cot", "react"],
        "require_approval": True
    }
)

# Child tiers automatically inherit
project_policy = manager.get_effective_policy(project_tier.tier_id)
# Includes company policy + project-specific overrides
```

## 📊 Data Flow

```
User Query → Tier Identification → Progressive Refinement
                                          ↓
                        Bottom-Up: Client → Project → Team → Company → Ecosystem
                                          ↓
                        Token Budget Distribution (Weighted)
                                          ↓
                        Context Aggregation from Each Tier
                                          ↓
                        Refined Context → Orchestrator
```

## 🔧 Configuration

### Environment Variables
```bash
MCP_TIER_MANAGER_PORT=8013
MCP_TIER_DB=postgresql://tier_db
MCP_STORE_URL=http://mcp-store:8008
DEFAULT_TOKEN_BUDGET=4000
```

## 📈 Metrics & Monitoring

### Key Metrics
- Total tiers by type
- Tier depth distribution
- Context retrieval latency per tier
- Token usage by tier
- Access control violations

### Health Checks
- `GET /health` - Service health
- `GET /metrics` - Prometheus metrics
- `GET /tiers/stats` - Tier statistics

## 🎓 Usage Examples

### Create Tier Hierarchy
```python
# Create hierarchy
ecosystem_tier = manager.create_tier(
    TierConfig(name="global", tier_type=TierType.ECOSYSTEM)
)

company_tier = manager.create_tier(
    TierConfig(
        name="acme_corp",
        tier_type=TierType.COMPANY,
        parent_id=ecosystem_tier.tier_id
    )
)

team_tier = manager.create_tier(
    TierConfig(
        name="ml_team",
        tier_type=TierType.TEAM,
        parent_id=company_tier.tier_id
    )
)

project_tier = manager.create_tier(
    TierConfig(
        name="recommendation_engine",
        tier_type=TierType.PROJECT,
        parent_id=team_tier.tier_id
    )
)

client_tier = manager.create_tier(
    TierConfig(
        name="user_123",
        tier_type=TierType.CLIENT,
        parent_id=project_tier.tier_id
    )
)
```

### Query with Progressive Refinement
```python
# Bottom-up query (starts specific, broadens if needed)
result = await refiner.refine_context(
    query="How do I configure the ML pipeline?",
    client_tier_id=client_tier.tier_id,
    strategy=RefinementStrategy.BOTTOM_UP,
    token_budget=4000
)

print(f"Context retrieved from:")
for tier_name, tokens in result.tier_contributions.items():
    print(f"  {tier_name}: {tokens} tokens")
```

## 🔐 Security

- **Tier Isolation**: Strict data separation
- **RBAC**: Role-based access per tier
- **Audit Trails**: All tier operations logged
- **Policy Enforcement**: Cascading security policies
- **Encryption**: All tier data encrypted at rest

## 🚦 Status

**Current**: Production-Ready ✅
- ✅ 28 unit tests (100% passing)
- ✅ 8 integration tests (100% passing)
- ✅ UI complete (2 pages)
- ✅ Documentation complete

## 📚 Related Services

- **MCP Retrieval**: Hierarchical context retrieval
- **MCP Store**: Tier data persistence
- **MCP Orchestrator**: Tier-scoped execution
- **MCP Package Manager**: Tier-specific packages
- **MCP Gateway**: Tier-based routing

## 🔮 Future Enhancements

- Dynamic tier creation based on usage
- ML-based tier optimization
- Cross-tier analytics
- Tier migration tools
- Advanced inheritance rules

---

**Version**: 1.0.0  
**Status**: Production-Ready ✅  
**Maintainer**: MCP Team

