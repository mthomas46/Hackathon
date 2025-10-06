# MCP Orchestrator Service

**Version:** 1.0.0-alpha  
**Port:** 5200 (Internal) / 8153 (External - Planned)  
**Status:** 🚧 45% Complete (Domain + Application Layers Done)

---

## Overview

The **MCP Orchestrator Service** is the brain of the MCP ecosystem. It orchestrates complex queries across multiple MCPs using 24 advanced LLM patterns, intelligent workflow planning, and sophisticated execution strategies.

### Core Mission

- **Plan workflows** - Create intelligent execution plans
- **Orchestrate queries** - Coordinate queries across multiple MCPs
- **Apply LLM patterns** - Use 24 advanced patterns for superior results
- **Aggregate results** - Combine and refine results intelligently
- **Manage state** - Track workflow lifecycle and progress

---

## Key Features

### 🧠 24 Advanced LLM Patterns
Organized across **9 categories:**

**1. Ensemble (3 patterns)**
- Orchestration - Route to specialized models
- Analysis - Combine weighted results
- Selective Ensemble - Hybrid approach

**2. Reasoning (3 patterns)**
- Chain of Thought - Step-by-step reasoning
- Tree of Thoughts - Multiple reasoning paths
- Graph of Thoughts - Interconnected reasoning nodes

**3. Self-Improvement (3 patterns)**
- Self-Consistency - Multiple answers, select best
- Self-Critique - Iterative refinement
- Constitutional AI - Principle-guided responses

**4. Multi-Agent (3 patterns)**
- Debate - Agents debate positions
- Collaboration - Distributed subtasks
- Voting - Aggregate decisions

**5. Retrieval (3 patterns)**
- Advanced RAG - Retrieval with reranking
- Hierarchical Retrieval - Tier-by-tier (MCP-specific!)
- Dynamic Context Pruning - Token budget management

**6. Uncertainty (3 patterns)**
- Confidence Scoring - Explicit confidence
- Epistemic Uncertainty - Model uncertainty
- Calibration - Align confidence to accuracy

**7. Human-in-Loop (2 patterns)**
- Confidence-Based Approval - Low confidence → review
- Active Learning - Identify uncertain cases

**8. Robustness (2 patterns)**
- Fallback Cascade - Chain of fallbacks
- Error Recovery - Graceful degradation

**9. Optimization (2 patterns)**
- Prompt Caching - Cache embeddings
- Parallel Execution - Parallel subtasks

### 🎯 10 Execution Strategies

- **Sequential** - One at a time
- **Parallel** - All simultaneously  
- **Waterfall** - Data pipeline
- **Scatter-Gather** - Parallel + aggregate
- **Priority-First** - Most important first
- **Lazy** - On-demand execution
- **Adaptive** - Dynamic strategy selection
- **Failfast** - Stop on first error
- **Resilient** - Continue despite failures
- **Budget-Aware** - Cost optimization

### 📊 10 Workflow States

- PENDING → PLANNING → READY → EXECUTING  
→ AGGREGATING → REFINING → COMPLETED

Terminal states: COMPLETED, FAILED, CANCELLED, TIMEOUT

### 🔍 Intelligent Planning

- **Auto-strategy selection** based on query complexity
- **Auto-pattern selection** based on accuracy requirements
- **MCP selection** via intelligent criteria
- **Step dependencies** with automatic resolution
- **Cost estimation** before execution

---

## Architecture

**Domain-Driven Design (DDD)** with clean layers:

```
services/mcp-orchestrator/
├── domain/                     # Business logic (~1,440 LOC)
│   ├── value_objects/          # LLMPattern, WorkflowState, etc.
│   ├── entities/               # Workflow, ExecutionPlan, etc.
│   └── repositories/           # WorkflowRepository interface
├── application/                # Use cases (~950 LOC)
│   ├── dto/                    # Request/Response DTOs
│   └── use_cases/              # Create, Execute, Get workflows
├── infrastructure/             # External integrations (~400 LOC)
│   ├── config/                 # Settings (60+ parameters)
│   └── repositories/           # Redis implementation
└── presentation/               # API layer (TBD)
    └── api/                    # FastAPI routes
```

**Total:** ~3,600 LOC across 32 files

---

## Domain Model

### Core Entities

**Workflow** (Aggregate Root)
- Complete query workflow with state management
- Tracks from creation through execution to completion
- Supports approval workflows

**ExecutionPlan**
- Intelligent execution planning
- Step sequencing with dependencies
- Cost and duration estimation

**WorkflowStep**
- Individual execution steps
- Pattern application
- Multiple MCP queries per step

**MCPQuery**
- Single query to an MCP instance
- Retry logic
- Result tracking

### Value Objects

**LLMPattern** - 24 patterns with categories  
**WorkflowState** - 10 lifecycle states  
**ExecutionStrategy** - 10 execution approaches  
**MCPSelectionCriteria** - Smart MCP filtering  
**LLMPatternCategory** - Pattern organization  

---

## Use Cases

### 1. CreateWorkflowUseCase
Creates and plans workflows.

**Process:**
1. Create workflow entity
2. Select execution strategy (auto or manual)
3. Select LLM patterns (auto or manual)
4. Create MCP selection criteria
5. Query MCP Gateway for available instances
6. Build execution plan with steps
7. Handle approval if required
8. Persist and return

**Features:**
- Intelligent strategy selection
- Smart pattern recommendations
- Automatic MCP discovery
- Step dependency management

### 2. ExecuteWorkflowUseCase
Executes workflows with full orchestration.

**Process:**
1. Load and validate workflow
2. Check approval if required
3. Execute steps in order
4. Apply LLM patterns
5. Handle failures gracefully
6. Aggregate results
7. Complete workflow

**Modes:**
- **Async:** Background execution (Celery-ready)
- **Sync:** Wait for completion

**Features:**
- Progress tracking
- Step-by-step execution
- Pattern application
- Result aggregation
- Error handling

### 3. GetWorkflowUseCase
Retrieves workflow information.

**Methods:**
- Get by ID (full details)
- Get user workflows (summaries)
- Get active workflows (summaries)

---

## API Endpoints (Planned)

### Workflows

```http
POST /api/v1/workflows
Body: CreateWorkflowRequest
Response: WorkflowResponse

POST /api/v1/workflows/{id}/execute
Body: ExecuteWorkflowRequest
Response: ExecutionResult

GET /api/v1/workflows/{id}
Response: WorkflowResponse

GET /api/v1/workflows/user/{user_id}
Response: WorkflowSummaryResponse[]

GET /api/v1/workflows/active
Response: WorkflowSummaryResponse[]
```

### Health

```http
GET /health
GET /ready
GET /live
```

---

## Configuration

**Key Settings (60+ parameters):**

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_API_PORT` | 5200 | Internal service port |
| `REDIS_DB` | 4 | Redis database number |
| `MAX_CONCURRENT_WORKFLOWS` | 100 | Max parallel workflows |
| `DEFAULT_WORKFLOW_TIMEOUT` | 300 | Default timeout (seconds) |
| `DEFAULT_EXECUTION_STRATEGY` | scatter_gather | Default strategy |
| `MAX_MCPS_PER_WORKFLOW` | 10 | Max MCPs per workflow |
| `LLM_GATEWAY_URL` | http://llm-gateway:5055 | LLM Gateway |
| `MCP_GATEWAY_URL` | http://mcp-gateway:5300 | MCP Gateway |
| `MCP_INTERPRETER_URL` | http://mcp-interpreter:5100 | Interpreter |

---

## Integration

### Dependencies
- **Redis** - Workflow state persistence
- **MCP Gateway** - MCP instance discovery and routing
- **MCP Interpreter** - Query parsing
- **LLM Gateway** - Pattern execution
- **MCP Infrastructure** - Context management
- **Log Collector** - Centralized logging

### Ecosystem Integration
- Creates workflows from interpreter output
- Routes queries through MCP Gateway
- Uses LLM Gateway for pattern execution
- Tracks context in MCP Infrastructure

---

## Examples

### Create Workflow
```python
request = CreateWorkflowRequest(
    original_query="What coding patterns does Team Alpha use?",
    parsed_query_id="query-123",
    query_intent="search",
    query_complexity=5,
    required_tiers=[2, 3],  # TEAM, COMPANY
    user_id="user-456"
)

workflow = await create_workflow_use_case.execute(request)
# → WorkflowResponse with execution plan
```

### Execute Workflow
```python
request = ExecuteWorkflowRequest(
    workflow_id="workflow-789",
    async_execution=True,
    notify_on_completion=True
)

result = await execute_workflow_use_case.execute(request)
# → ExecutionResult with status
```

### Monitor Workflow
```python
workflow = await get_workflow_use_case.execute("workflow-789")
# → WorkflowResponse with current state, progress, results
```

---

## Development Status

### ✅ Completed (~45%)

**Domain Layer (100%)**
- 5 Value Objects
- 4 Entities
- 1 Repository Interface

**Application Layer (100%)**
- 5 DTOs
- 3 Use Cases

**Infrastructure Layer (60%)**
- Settings (~130 LOC, 60+ params)
- Redis Repository (~260 LOC)

### ⏳ Remaining (~55%)

**Infrastructure Layer**
- LLM Gateway Client
- MCP Gateway Client
- Pattern execution engines

**Presentation Layer**
- API Models
- FastAPI routes
- WebSocket support
- Dependencies
- Main application

**Deployment**
- Dockerfile
- docker-compose integration
- README enhancements

**Testing**
- Unit tests
- Integration tests
- End-to-end tests

**Future Enhancements**
- Celery background tasks
- Advanced pattern implementations
- WebSocket progress streaming
- Monitoring & metrics
- Distributed tracing

---

## Statistics

- **Files:** 32 Python files
- **LOC:** ~3,600
- **Patterns:** 24 LLM patterns
- **Strategies:** 10 execution strategies
- **States:** 10 workflow states
- **Entities:** 4 core entities
- **Use Cases:** 3 main use cases
- **Settings:** 60+ configuration parameters

---

## Future Roadmap

### Phase 1: Complete Core Service
- ✅ Domain layer
- ✅ Application layer
- ⏳ Infrastructure layer
- ⏳ Presentation layer
- ⏳ Deployment

### Phase 2: Advanced Features
- Pattern execution engines
- WebSocket streaming
- Celery integration
- Advanced monitoring

### Phase 3: Optimization
- Query optimization
- Prompt caching
- Connection pooling
- Performance tuning

### Phase 4: Production
- Comprehensive testing
- Load testing
- Security hardening
- Documentation

---

## Contributing

This service follows:
- **DDD Architecture** - Clean separation of concerns
- **SOLID Principles** - Maintainable, extensible code
- **DRY & KISS** - Simple, non-repetitive implementation
- **TDD** - Test-driven development (tests TBD)

---

**Status:** 🚧 Development In Progress  
**Last Updated:** October 6, 2025  
**Version:** 1.0.0-alpha

**Next Steps:** Complete presentation layer, add Dockerfile, integrate with docker-compose.

