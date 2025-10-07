# 🚀 **Implementation Plan: Phases 6, 7, and FUTURE**

## **Test-Driven Development (TDD) & UI Integration Plan**

**Date:** October 7, 2025  
**Status:** Planning Phase  
**Approach:** TDD + Continuous UI Integration  

---

## **Table of Contents**

1. [Overview](#overview)
2. [TDD Methodology](#tdd-methodology)
3. [Phase 6: Advanced Features](#phase-6-advanced-features)
4. [Phase 7: Production](#phase-7-production)
5. [FUTURE: 6-12 Months](#future-6-12-months)
6. [FUTURE: 12-18 Months](#future-12-18-months)
7. [FUTURE: 12-24 Months](#future-12-24-months)
8. [FUTURE: 18-24 Months](#future-18-24-months)
9. [Dashboard UI Roadmap](#dashboard-ui-roadmap)
10. [Testing Strategy](#testing-strategy)
11. [Timeline & Milestones](#timeline--milestones)

---

## **Overview**

### **Guiding Principles**

1. ✅ **Test-Driven Development (TDD)** - Write tests first, then implementation
2. ✅ **UI-First Design** - Every feature exposed in dashboard
3. ✅ **Incremental Delivery** - Ship working features continuously
4. ✅ **Production-Ready** - Every feature deployment-ready
5. ✅ **Documentation-Driven** - Complete docs for every feature

### **Core Philosophy**

```
Write Test → Fail → Implement → Pass → Refactor → Document → UI → Ship
```

---

## **TDD Methodology**

### **Development Cycle**

For **every** feature, follow this cycle:

#### **1. Write Tests First** (Red Phase)
```python
# tests/unit/test_feature.py
def test_feature_does_x():
    """Test that feature does X."""
    result = feature.do_x()
    assert result == expected
```

#### **2. Run Tests (Should Fail)**
```bash
pytest tests/unit/test_feature.py -v
# EXPECTED: FAILED
```

#### **3. Implement Minimum Code** (Green Phase)
```python
# services/service-name/feature.py
def do_x():
    return expected  # Simplest implementation
```

#### **4. Run Tests (Should Pass)**
```bash
pytest tests/unit/test_feature.py -v
# EXPECTED: PASSED
```

#### **5. Refactor** (Blue Phase)
- Improve code quality
- Add error handling
- Optimize performance
- Maintain passing tests

#### **6. Integration Tests**
```python
# tests/integration/test_feature_integration.py
@pytest.mark.asyncio
async def test_feature_integration():
    """Test feature with real services."""
    # Integration test
```

#### **7. E2E Tests**
```python
# tests/e2e/test_feature_e2e.py
@pytest.mark.e2e
async def test_feature_end_to_end():
    """Test complete workflow."""
    # E2E test
```

#### **8. UI Integration**
```python
# dashboard/pages/feature_page.py
def render():
    """Expose feature in UI."""
    st.title("Feature Name")
    # UI implementation
```

#### **9. Documentation**
```markdown
# docs/FEATURE_GUIDE.md
## Feature Name
Usage, examples, API reference
```

#### **10. Ship** ✅
```bash
git add .
git commit -m "feat: Implement feature X with TDD"
git push
```

---

## **Phase 6: Advanced Features**

### **Duration:** 4-6 weeks  
### **LOC Estimate:** ~6,000 LOC  
### **Tests:** ~2,000 LOC  

---

### **Phase 6.1: Hierarchical Retrieval** (Week 1-2)

#### **Overview**
Implement tier-by-tier retrieval system (Client → Project → Company → Team → Ecosystem).

#### **TDD Implementation Plan**

##### **Step 1: Write Tests** (Day 1)
```python
# tests/unit/test_hierarchical_retrieval.py

class TestHierarchicalRetrieval:
    def test_retrieve_from_single_tier(self):
        """Test retrieval from single tier."""
        retriever = HierarchicalRetriever(tiers=["client"])
        results = retriever.retrieve("query", max_results=5)
        assert len(results) <= 5
        assert all(r.tier == "client" for r in results)
    
    def test_retrieve_cascading(self):
        """Test cascading across tiers."""
        retriever = HierarchicalRetriever(
            tiers=["client", "project", "company"]
        )
        results = retriever.retrieve("query", max_results=10)
        # Should retrieve from client first, then project, then company
        assert len(results) <= 10
    
    def test_tier_budget_distribution(self):
        """Test token budget distribution across tiers."""
        retriever = HierarchicalRetriever(
            tiers=["client", "project"],
            token_budget=1000
        )
        results = retriever.retrieve_with_budget("query")
        total_tokens = sum(r.token_count for r in results)
        assert total_tokens <= 1000
```

##### **Step 2: Implement** (Day 2-4)
```python
# services/mcp-retrieval/src/hierarchical_retrieval.py

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class RetrievalResult:
    content: str
    tier: str
    score: float
    token_count: int
    metadata: Dict[str, Any]

class HierarchicalRetriever:
    """Tier-by-tier hierarchical retrieval."""
    
    TIER_ORDER = ["client", "project", "company", "team", "ecosystem"]
    
    def __init__(
        self,
        tiers: List[str],
        token_budget: int = 4000,
        tier_weights: Dict[str, float] = None
    ):
        self.tiers = tiers
        self.token_budget = token_budget
        self.tier_weights = tier_weights or self._default_weights()
    
    def _default_weights(self) -> Dict[str, float]:
        """Default tier weights (client has highest priority)."""
        return {
            "client": 0.4,
            "project": 0.3,
            "company": 0.15,
            "team": 0.1,
            "ecosystem": 0.05,
        }
    
    def retrieve(
        self,
        query: str,
        max_results: int = 10
    ) -> List[RetrievalResult]:
        """Retrieve results with cascading across tiers."""
        # Implementation
        pass
    
    def retrieve_with_budget(
        self,
        query: str
    ) -> List[RetrievalResult]:
        """Retrieve with token budget constraints."""
        # Implementation
        pass
```

##### **Step 3: Integration Tests** (Day 5)
```python
# tests/integration/test_hierarchical_retrieval_integration.py

@pytest.mark.asyncio
async def test_hierarchical_retrieval_with_chromadb():
    """Test with real ChromaDB."""
    # Test with actual vector store
    pass
```

##### **Step 4: UI Integration** (Day 6-7)
```python
# dashboard/pages/hierarchical_retrieval.py

def render():
    st.title("🔍 Hierarchical Retrieval")
    
    # Tier selection
    tiers = st.multiselect(
        "Select MCP Tiers",
        ["client", "project", "company", "team", "ecosystem"],
        default=["client", "project"]
    )
    
    # Token budget
    budget = st.slider("Token Budget", 500, 8000, 4000)
    
    # Query
    query = st.text_area("Query")
    
    if st.button("Retrieve"):
        results = retriever.retrieve_with_budget(query)
        # Display results by tier
        for tier in tiers:
            tier_results = [r for r in results if r.tier == tier]
            st.subheader(f"📁 {tier.title()} Tier")
            for result in tier_results:
                st.markdown(result.content)
```

#### **Deliverables**
- ✅ HierarchicalRetriever class (~400 LOC)
- ✅ Unit tests (20+ tests, ~300 LOC)
- ✅ Integration tests (~200 LOC)
- ✅ UI page (~200 LOC)
- ✅ Documentation (~150 LOC)

**Total:** ~1,250 LOC

---

### **Phase 6.2: Dynamic Context Pruning** (Week 2-3)

#### **Overview**
Implement intelligent context pruning with token budgets.

#### **TDD Implementation Plan**

##### **Step 1: Write Tests**
```python
# tests/unit/test_context_pruning.py

def test_prune_by_relevance():
    """Test pruning keeps most relevant content."""
    pruner = ContextPruner(strategy="relevance")
    context = large_context  # 10k tokens
    pruned = pruner.prune(context, target_tokens=2000)
    assert pruned.token_count <= 2000
    assert pruned.relevance_score > 0.8

def test_prune_by_recency():
    """Test pruning keeps most recent content."""
    pruner = ContextPruner(strategy="recency")
    pruned = pruner.prune(context, target_tokens=2000)
    assert all(item.timestamp > threshold for item in pruned.items)

def test_prune_hybrid():
    """Test hybrid pruning (relevance + recency)."""
    pruner = ContextPruner(strategy="hybrid")
    pruned = pruner.prune(context, target_tokens=2000)
    assert pruned.token_count <= 2000
```

##### **Step 2: Implement**
```python
# services/mcp-orchestrator/src/context_pruning.py

class ContextPruner:
    """Dynamic context pruning with multiple strategies."""
    
    STRATEGIES = ["relevance", "recency", "hybrid", "importance"]
    
    def __init__(self, strategy: str = "hybrid"):
        self.strategy = strategy
    
    def prune(
        self,
        context: Context,
        target_tokens: int,
        query: str = None
    ) -> PrunedContext:
        """Prune context to target token budget."""
        if self.strategy == "relevance":
            return self._prune_by_relevance(context, target_tokens, query)
        elif self.strategy == "recency":
            return self._prune_by_recency(context, target_tokens)
        elif self.strategy == "hybrid":
            return self._prune_hybrid(context, target_tokens, query)
        elif self.strategy == "importance":
            return self._prune_by_importance(context, target_tokens)
```

##### **Step 3: UI Integration**
```python
# dashboard/pages/context_pruning.py

def render():
    st.title("✂️ Dynamic Context Pruning")
    
    # Strategy selection
    strategy = st.selectbox(
        "Pruning Strategy",
        ["relevance", "recency", "hybrid", "importance"]
    )
    
    # Token budget
    budget = st.slider("Target Token Budget", 500, 8000, 2000)
    
    # Upload context
    context_file = st.file_uploader("Upload Context")
    
    if st.button("Prune"):
        pruned = pruner.prune(context, target_tokens=budget)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Original Tokens", context.token_count)
        with col2:
            st.metric("Pruned Tokens", pruned.token_count)
        
        st.json(pruned.to_dict())
```

#### **Deliverables**
- ✅ ContextPruner class (~500 LOC)
- ✅ Unit tests (25+ tests, ~400 LOC)
- ✅ UI page (~250 LOC)
- ✅ Documentation (~150 LOC)

**Total:** ~1,300 LOC

---

### **Phase 6.3: Human-in-the-Loop Workflows** (Week 3-4)

#### **Overview**
Implement HITL with confidence thresholds and approval workflows.

#### **TDD Implementation Plan**

##### **Step 1: Write Tests**
```python
# tests/unit/test_hitl_workflows.py

def test_confidence_threshold_triggers_approval():
    """Test low confidence triggers human approval."""
    workflow = HITLWorkflow(confidence_threshold=0.8)
    result = workflow.process(query, confidence=0.6)
    assert result.requires_approval is True

def test_high_confidence_bypasses_approval():
    """Test high confidence bypasses approval."""
    workflow = HITLWorkflow(confidence_threshold=0.8)
    result = workflow.process(query, confidence=0.95)
    assert result.requires_approval is False

def test_approval_workflow():
    """Test approval workflow."""
    workflow = HITLWorkflow()
    result = workflow.request_approval(
        query="query",
        response="response",
        confidence=0.6
    )
    assert result.status == "pending_approval"
```

##### **Step 2: Implement**
```python
# services/mcp-orchestrator/src/hitl_workflow.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ApprovalStatus(Enum):
    PENDING = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

@dataclass
class HITLResult:
    query: str
    response: str
    confidence: float
    requires_approval: bool
    status: ApprovalStatus
    approver: Optional[str] = None
    feedback: Optional[str] = None

class HITLWorkflow:
    """Human-in-the-loop workflow manager."""
    
    def __init__(
        self,
        confidence_threshold: float = 0.8,
        high_stakes_patterns: List[str] = None
    ):
        self.confidence_threshold = confidence_threshold
        self.high_stakes_patterns = high_stakes_patterns or []
    
    def process(
        self,
        query: str,
        response: str,
        confidence: float
    ) -> HITLResult:
        """Process query through HITL workflow."""
        requires_approval = self._requires_approval(query, confidence)
        
        if requires_approval:
            return self.request_approval(query, response, confidence)
        else:
            return HITLResult(
                query=query,
                response=response,
                confidence=confidence,
                requires_approval=False,
                status=ApprovalStatus.AUTO_APPROVED
            )
    
    def _requires_approval(self, query: str, confidence: float) -> bool:
        """Determine if approval required."""
        # Low confidence
        if confidence < self.confidence_threshold:
            return True
        
        # High-stakes query
        if any(pattern in query.lower() for pattern in self.high_stakes_patterns):
            return True
        
        return False
```

##### **Step 3: UI Integration**
```python
# dashboard/pages/hitl_workflows.py

def render():
    st.title("👤 Human-in-the-Loop Workflows")
    
    # Configuration
    st.subheader("Configuration")
    threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.8, 0.05)
    
    # Pending approvals
    st.subheader("⏳ Pending Approvals")
    pending = workflow_manager.get_pending_approvals()
    
    for approval in pending:
        with st.expander(f"Query: {approval.query[:50]}..."):
            st.write("**Query:**", approval.query)
            st.write("**Response:**", approval.response)
            st.metric("Confidence", f"{approval.confidence:.2%}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"approve-{approval.id}"):
                    workflow_manager.approve(approval.id)
                    st.success("Approved!")
            with col2:
                if st.button("❌ Reject", key=f"reject-{approval.id}"):
                    feedback = st.text_input("Feedback")
                    workflow_manager.reject(approval.id, feedback)
                    st.warning("Rejected")
    
    # Approval history
    st.subheader("📜 Approval History")
    history = workflow_manager.get_approval_history(limit=50)
    st.dataframe(history)
```

#### **Deliverables**
- ✅ HITLWorkflow class (~600 LOC)
- ✅ Approval queue management (~300 LOC)
- ✅ Unit tests (30+ tests, ~500 LOC)
- ✅ UI page (~400 LOC)
- ✅ Documentation (~200 LOC)

**Total:** ~2,000 LOC

---

### **Phase 6.4: Feedback Incorporation System** (Week 4-5)

#### **Overview**
System to incorporate human feedback into future responses.

#### **TDD Implementation Plan**

##### **Step 1: Write Tests**
```python
# tests/unit/test_feedback_system.py

def test_record_feedback():
    """Test feedback recording."""
    system = FeedbackSystem()
    system.record_feedback(
        query="query",
        response="response",
        feedback="This is incorrect because...",
        correction="The correct answer is..."
    )
    assert system.feedback_count == 1

def test_feedback_improves_future_responses():
    """Test feedback improves responses."""
    system = FeedbackSystem()
    
    # First response (before feedback)
    response1 = system.generate_response("query")
    
    # Record feedback
    system.record_feedback("query", response1, "incorrect", "correct answer")
    
    # Second response (after feedback)
    response2 = system.generate_response("query")
    
    assert response2 != response1
    assert "correct answer" in response2
```

##### **Step 2: Implement**
```python
# services/mcp-orchestrator/src/feedback_system.py

class FeedbackSystem:
    """Incorporate human feedback into responses."""
    
    def __init__(self, feedback_store: FeedbackStore):
        self.feedback_store = feedback_store
    
    def record_feedback(
        self,
        query: str,
        response: str,
        feedback: str,
        correction: Optional[str] = None,
        rating: Optional[int] = None
    ):
        """Record feedback for a response."""
        self.feedback_store.store({
            "query": query,
            "response": response,
            "feedback": feedback,
            "correction": correction,
            "rating": rating,
            "timestamp": datetime.now()
        })
    
    def get_relevant_feedback(
        self,
        query: str,
        limit: int = 5
    ) -> List[Feedback]:
        """Get relevant feedback for query."""
        return self.feedback_store.search(query, limit=limit)
    
    def apply_feedback_to_context(
        self,
        query: str,
        context: str
    ) -> str:
        """Apply relevant feedback to context."""
        relevant_feedback = self.get_relevant_feedback(query)
        
        # Add feedback to context
        feedback_context = "\n\n".join([
            f"Previous feedback: {fb.feedback}\nCorrection: {fb.correction}"
            for fb in relevant_feedback
        ])
        
        return f"{context}\n\n{feedback_context}"
```

##### **Step 3: UI Integration**
```python
# dashboard/pages/feedback_system.py

def render():
    st.title("💬 Feedback System")
    
    # Submit feedback
    st.subheader("Submit Feedback")
    query = st.text_area("Original Query")
    response = st.text_area("Response Received")
    feedback = st.text_area("Your Feedback")
    correction = st.text_area("Correct Answer (optional)")
    rating = st.slider("Rating", 1, 5, 3)
    
    if st.button("Submit Feedback"):
        feedback_system.record_feedback(
            query, response, feedback, correction, rating
        )
        st.success("Feedback recorded!")
    
    # Feedback analytics
    st.subheader("📊 Feedback Analytics")
    metrics = feedback_system.get_metrics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Feedback", metrics["total_count"])
    with col2:
        st.metric("Avg Rating", f"{metrics['avg_rating']:.2f}")
    with col3:
        st.metric("Improvement Rate", f"{metrics['improvement_rate']:.1%}")
    
    # Recent feedback
    st.subheader("Recent Feedback")
    recent = feedback_system.get_recent(limit=20)
    for fb in recent:
        with st.expander(f"{fb.query[:50]}..."):
            st.write("**Feedback:**", fb.feedback)
            if fb.correction:
                st.write("**Correction:**", fb.correction)
            st.write("**Rating:**", "⭐" * fb.rating)
```

#### **Deliverables**
- ✅ FeedbackSystem class (~400 LOC)
- ✅ FeedbackStore (Redis-backed) (~300 LOC)
- ✅ Unit tests (25+ tests, ~400 LOC)
- ✅ UI page (~350 LOC)
- ✅ Documentation (~150 LOC)

**Total:** ~1,600 LOC

---

### **Phase 6 Summary**

| Feature | LOC | Tests | UI | Docs | Total |
|---------|-----|-------|----|----- |-------|
| Hierarchical Retrieval | 400 | 500 | 200 | 150 | 1,250 |
| Context Pruning | 500 | 400 | 250 | 150 | 1,300 |
| HITL Workflows | 900 | 500 | 400 | 200 | 2,000 |
| Feedback System | 700 | 400 | 350 | 150 | 1,600 |
| **TOTAL** | **2,500** | **1,800** | **1,200** | **650** | **~6,150** |

**Duration:** 4-6 weeks  
**Tests:** 100+ tests  
**UI Pages:** 4 new pages  

---

## **Phase 7: Production**

### **Duration:** 6-8 weeks  
### **LOC Estimate:** ~8,000 LOC  
### **Tests:** ~2,500 LOC  

---

### **Phase 7.1: Infrastructure & Optimization** (Week 1-3)

#### **Features:**
1. ✅ Network policies and security
2. ✅ Query caching strategy
3. ✅ Parallel execution optimization
4. ✅ Lazy loading
5. ✅ Connection pooling

#### **Implementation:**

##### **7.1.1: Query Caching** (Week 1)
```python
# services/mcp-orchestrator/src/query_cache.py

from redis import Redis
import hashlib

class QueryCache:
    """Redis-backed query cache."""
    
    def __init__(self, redis_client: Redis, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl
    
    def get(self, query: str, context: str = "") -> Optional[str]:
        """Get cached response."""
        cache_key = self._generate_key(query, context)
        return self.redis.get(cache_key)
    
    def set(self, query: str, response: str, context: str = ""):
        """Cache response."""
        cache_key = self._generate_key(query, context)
        self.redis.setex(cache_key, self.ttl, response)
    
    def _generate_key(self, query: str, context: str) -> str:
        """Generate cache key."""
        data = f"{query}:{context}"
        return hashlib.sha256(data.encode()).hexdigest()
```

**Tests:**
```python
def test_cache_hit():
    cache = QueryCache(redis_mock)
    cache.set("query", "response")
    assert cache.get("query") == "response"

def test_cache_miss():
    cache = QueryCache(redis_mock)
    assert cache.get("nonexistent") is None

def test_cache_expiration():
    cache = QueryCache(redis_mock, ttl=1)
    cache.set("query", "response")
    time.sleep(2)
    assert cache.get("query") is None
```

##### **7.1.2: Connection Pooling** (Week 2)
```python
# common/connection_pool.py

from typing import Dict, Any
import asyncpg
from redis import ConnectionPool
from pymongo import MongoClient

class ConnectionPoolManager:
    """Manage connection pools for all data stores."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pools = {}
    
    async def init_postgres_pool(self):
        """Initialize PostgreSQL connection pool."""
        self.pools['postgres'] = await asyncpg.create_pool(
            host=self.config['postgres']['host'],
            port=self.config['postgres']['port'],
            database=self.config['postgres']['database'],
            min_size=10,
            max_size=100,
            command_timeout=60
        )
    
    def init_redis_pool(self):
        """Initialize Redis connection pool."""
        self.pools['redis'] = ConnectionPool(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            max_connections=50,
            decode_responses=True
        )
```

##### **7.1.3: Parallel Execution** (Week 3)
```python
# services/mcp-orchestrator/src/parallel_executor.py

import asyncio
from typing import List, Callable

class ParallelExecutor:
    """Execute patterns in parallel."""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_patterns(
        self,
        patterns: List[Callable],
        query: str
    ) -> List[Any]:
        """Execute multiple patterns in parallel."""
        async def _execute_with_semaphore(pattern):
            async with self.semaphore:
                return await pattern.execute(query)
        
        tasks = [_execute_with_semaphore(p) for p in patterns]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
```

#### **UI Integration:**
```python
# dashboard/pages/system_performance.py

def render():
    st.title("⚡ System Performance")
    
    # Cache metrics
    st.subheader("💾 Query Cache")
    cache_stats = cache_manager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Hit Rate", f"{cache_stats['hit_rate']:.1%}")
    with col2:
        st.metric("Total Hits", cache_stats['hits'])
    with col3:
        st.metric("Total Misses", cache_stats['misses'])
    with col4:
        st.metric("Cached Queries", cache_stats['size'])
    
    # Connection pool status
    st.subheader("🔌 Connection Pools")
    pools = pool_manager.get_all_pools()
    
    for name, pool in pools.items():
        with st.expander(f"{name.title()} Pool"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Active", pool.active_connections)
            with col2:
                st.metric("Idle", pool.idle_connections)
            with col3:
                st.metric("Max", pool.max_connections)
    
    # Parallel execution metrics
    st.subheader("⚡ Parallel Execution")
    exec_metrics = executor.get_metrics()
    
    st.metric("Avg Parallelism", f"{exec_metrics['avg_parallel']:.1f}")
    st.metric("Max Concurrent", exec_metrics['max_concurrent'])
```

#### **Deliverables:**
- ✅ Query caching (~400 LOC)
- ✅ Connection pooling (~500 LOC)
- ✅ Parallel execution (~300 LOC)
- ✅ Lazy loading (~300 LOC)
- ✅ Network policies (config)
- ✅ Tests (~800 LOC)
- ✅ UI page (~400 LOC)

**Total:** ~2,700 LOC

---

### **Phase 7.2: Kubernetes & Deployment** (Week 4-6)

#### **Features:**
1. ✅ Kubernetes manifests
2. ✅ Helm charts
3. ✅ CI/CD pipelines
4. ✅ Auto-scaling policies
5. ✅ API rate limiting

#### **Implementation:**

##### **7.2.1: Kubernetes Manifests** (Week 4)
```yaml
# k8s/deployments/mcp-orchestrator.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-orchestrator
  labels:
    app: mcp-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-orchestrator
  template:
    metadata:
      labels:
        app: mcp-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: mcp/orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-orchestrator
spec:
  selector:
    app: mcp-orchestrator
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-orchestrator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

##### **7.2.2: Helm Charts** (Week 5)
```yaml
# helm/mcp-ecosystem/Chart.yaml

apiVersion: v2
name: mcp-ecosystem
description: Model Context Protocol Ecosystem
type: application
version: 1.0.0
appVersion: "1.0.0"
```

```yaml
# helm/mcp-ecosystem/values.yaml

orchestrator:
  replicas: 3
  image:
    repository: mcp/orchestrator
    tag: latest
  resources:
    requests:
      memory: 512Mi
      cpu: 500m
    limits:
      memory: 2Gi
      cpu: 2000m
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPU: 70
    targetMemory: 80

composer:
  replicas: 2
  # Similar configuration

registry:
  replicas: 2
  # Similar configuration

# Data stores
redis:
  enabled: true
  master:
    persistence:
      enabled: true
      size: 10Gi

postgres:
  enabled: true
  persistence:
    size: 50Gi
```

##### **7.2.3: CI/CD Pipeline** (Week 5-6)
```yaml
# .github/workflows/ci-cd.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=services --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker-compose build
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker-compose push
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v4
        with:
          manifests: |
            k8s/deployments/
          images: |
            mcp/orchestrator:${{ github.sha }}
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
```

##### **7.2.4: Rate Limiting** (Week 6)
```python
# common/rate_limiter.py

from redis import Redis
import time

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self,
        redis_client: Redis,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        window_key = f"rate_limit:{key}:{int(now / self.window)}"
        
        current = self.redis.incr(window_key)
        
        if current == 1:
            self.redis.expire(window_key, self.window)
        
        return current <= self.max_requests
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests in window."""
        now = time.time()
        window_key = f"rate_limit:{key}:{int(now / self.window)}"
        current = int(self.redis.get(window_key) or 0)
        return max(0, self.max_requests - current)
```

#### **Deliverables:**
- ✅ Kubernetes manifests for all services (~1,000 LOC YAML)
- ✅ Helm chart (~800 LOC YAML)
- ✅ CI/CD pipeline (~400 LOC YAML)
- ✅ Rate limiting (~300 LOC)
- ✅ Tests (~600 LOC)
- ✅ Documentation (~500 LOC)

**Total:** ~3,600 LOC

---

### **Phase 7 Summary**

| Feature | LOC | Tests | Docs | Total |
|---------|-----|-------|------|-------|
| Infrastructure & Optimization | 1,500 | 800 | 400 | 2,700 |
| Kubernetes & Deployment | 2,500 | 600 | 500 | 3,600 |
| **TOTAL** | **4,000** | **1,400** | **900** | **~6,300** |

**Duration:** 6-8 weeks  
**Tests:** 80+ tests  

---

## **FUTURE: 6-12 Months**

### **Priority Features:**

1. **5-Tier Hierarchical MCP System**
2. **MCP Portability (Export/Import)**
3. **Logs MCP**
4. **Neo4j & ChromaDB Optimization**
5. **Source-Specific Extractors**

**Estimated:** ~15,000 LOC  
**Duration:** 6 months  

*(Detailed plan in separate document due to length)*

---

## **Dashboard UI Roadmap**

### **Current Dashboard** (Complete)
✅ Home - System overview  
✅ Registry - Package browser  
✅ Performance - Metrics & analytics  
✅ Analytics - Trends & anomalies  

### **Phase 6 UI Additions**
- [ ] **Hierarchical Retrieval** - Tier-by-tier query interface
- [ ] **Context Pruning** - Dynamic pruning controls
- [ ] **HITL Workflows** - Approval queue & management
- [ ] **Feedback System** - Submit & view feedback

### **Phase 7 UI Additions**
- [ ] **System Performance** - Cache, pools, execution metrics
- [ ] **Deployment Status** - K8s pods, services, health
- [ ] **Rate Limiting** - Monitor API usage
- [ ] **Security Dashboard** - Network policies, access logs

### **FUTURE UI Features**
- [ ] **MCP Builder** - Visual MCP creation
- [ ] **Marketplace** - Browse & download MCPs
- [ ] **Logs Intelligence** - Log analytics
- [ ] **Live Architecture** - Auto-updating diagrams

---

## **Testing Strategy**

### **TDD Requirements**

For **every** feature:
1. ✅ Unit tests (min 80% coverage)
2. ✅ Integration tests
3. ✅ E2E tests (for workflows)
4. ✅ Load tests (for critical paths)
5. ✅ UI tests (for dashboard pages)

### **Test Pyramid**

```
        /\
       /E2\      10% E2E Tests (workflows)
      /----\
     / Intg \    20% Integration Tests
    /--------\
   /   Unit   \  70% Unit Tests
  /____________\
```

### **Continuous Testing**

```bash
# Pre-commit hook
pytest tests/unit/ -v --cov

# CI Pipeline
pytest tests/ -v --cov=services --cov-report=xml

# Nightly
pytest tests/load/ -v -m load
```

---

## **Timeline & Milestones**

### **Phase 6** (Weeks 1-6)
- Week 1-2: Hierarchical Retrieval ✅
- Week 2-3: Context Pruning ✅
- Week 3-4: HITL Workflows ✅
- Week 4-5: Feedback System ✅
- Week 6: Testing & Documentation ✅

### **Phase 7** (Weeks 7-14)
- Week 7-9: Infrastructure & Optimization ✅
- Week 10-12: Kubernetes & Deployment ✅
- Week 13-14: Testing & Documentation ✅

### **FUTURE** (6-24 months)
- Months 1-6: Tier system, Portability, Logs MCP
- Months 7-12: Marketplace, Local LLM
- Months 13-18: Advanced features
- Months 19-24: Polish & optimization

---

## **Success Criteria**

### **Phase 6**
✅ All 4 features implemented with TDD  
✅ 100+ tests passing  
✅ 4 new dashboard pages  
✅ Complete documentation  

### **Phase 7**
✅ Production-ready deployment  
✅ Auto-scaling working  
✅ CI/CD pipeline functional  
✅ Rate limiting active  
✅ 80+ tests passing  

### **Overall**
✅ TDD practiced throughout  
✅ Every feature exposed in UI  
✅ Complete test coverage  
✅ Production-ready code  
✅ Comprehensive documentation  

---

**Status:** Ready to start Phase 6! 🚀  
**Approach:** TDD + UI-First + Incremental Delivery  
**Next:** Implement Phase 6.1 (Hierarchical Retrieval)  

---

**Let's build this systematically, one test at a time!** ✅
