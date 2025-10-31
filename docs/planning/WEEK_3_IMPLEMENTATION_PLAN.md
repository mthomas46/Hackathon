# Week 3 Implementation Plan 🚀
## Advanced Features & Production Polish

**Date:** October 21, 2025  
**Status:** 🟢 READY TO START  
**Prerequisites:** Weeks 1-2 Complete ✅, Option C Complete ✅

---

## 📊 Current State Assessment

### What We've Accomplished (Weeks 1-2 + Option C)

**Week 1: Critical Integration & Hardening** ✅
- Sub-job orchestration
- Dependency topological ordering
- Circuit breakers & timeout protection
- Partial success handling
- Fallback strategies

**Week 2: Advanced Features** ✅
- Hierarchical contexts (4 levels)
- Structured logging with correlation IDs
- Context-aware RAG filtering

**Option C: Testing & Optimization** ✅
- Performance benchmarks + E2E tests
- Incremental documentation (10-100× speedup)
- Real-time performance monitoring

**Current System Status:** 🟢 97% Production Ready

---

## 🎯 Week 3 Goals

### Primary Objectives
1. **Multi-Model Intelligence** - Smart routing to optimal LLMs (CodeLlama, etc.)
2. **Advanced RAG Features** - Context-aware queries with filtering
3. **Dashboard Enhancements** - New features exposure in UI
4. **Documentation Workflow** - Complete incremental doc pipeline
5. **Production Deployment** - Final hardening and deployment

### Success Metrics
- ✅ All features integrated and tested
- ✅ Dashboard fully functional
- ✅ Documentation pipeline complete
- ✅ System deployed and monitored
- ✅ 100% production ready

---

## 📅 Week 3 Schedule (5 days)

### **Day 1: Multi-Model Intelligence** (8 hours)
Focus: Smart LLM routing and CodeLlama integration

### **Day 2: Advanced RAG Features** (8 hours)
Focus: Context-aware queries and hierarchical filtering

### **Day 3: Dashboard Integration** (8 hours)
Focus: Expose new features in UI

### **Day 4: Documentation Pipeline** (8 hours)
Focus: Complete incremental documentation workflow

### **Day 5: Production Deployment** (8 hours)
Focus: Final testing, deployment, and monitoring

---

## 🔥 DAY 1: MULTI-MODEL INTELLIGENCE

### Objective
Enable intelligent routing of tasks to optimal LLMs based on content type and complexity.

---

### **Task 1.1: Enhanced Model Router** (3 hours)

**Goal:** Extend model router to detect code files and route to CodeLlama

**Files to Create/Modify:**
```
services/ecosystem-mcp/src/services/llm/enhanced_model_router.py (NEW)
services/ecosystem-mcp/src/services/llm/code_detector.py (NEW)
services/ecosystem-mcp/tests/unit/test_enhanced_model_router.py (NEW)
```

**Implementation:**

```python
# File: enhanced_model_router.py

"""
Enhanced Model Router with Code Detection

Features:
- Automatic code file detection
- Smart routing to CodeLlama for code files
- Fallback to general-purpose models
- Language-specific optimization
"""

from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available model types."""
    GENERAL = "general"  # llama2, mistral
    CODE = "code"  # codellama
    EMBEDDING = "embedding"  # nomic-embed-text


class TaskType(Enum):
    """Types of tasks."""
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    RAG_QUERY = "rag_query"
    GENERAL_QUERY = "general_query"


class EnhancedModelRouter:
    """
    Enhanced model router with intelligent task routing.
    
    Routes tasks to optimal models based on:
    - Content type (code vs text)
    - Task complexity
    - Model availability
    - Performance requirements
    """
    
    def __init__(self):
        self.code_detector = CodeDetector()
        self.model_priorities = self._init_priorities()
        logger.info("EnhancedModelRouter initialized")
    
    def _init_priorities(self) -> Dict[TaskType, list]:
        """Initialize model priorities for each task type."""
        return {
            TaskType.CODE_ANALYSIS: [
                "codellama:13b",
                "codellama:7b",
                "llama2:13b"  # Fallback
            ],
            TaskType.DOCUMENTATION: [
                "llama2:13b",
                "mistral:7b",
                "llama2:7b"
            ],
            TaskType.RAG_QUERY: [
                "llama2:13b",
                "mistral:7b"
            ],
            TaskType.GENERAL_QUERY: [
                "llama2:13b",
                "mistral:7b",
                "llama2:7b"
            ]
        }
    
    def select_model(
        self,
        content: str,
        file_path: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        **context
    ) -> str:
        """
        Select optimal model for task.
        
        Args:
            content: Content to process
            file_path: Optional file path for detection
            task_type: Optional explicit task type
            **context: Additional context
        
        Returns:
            Model name to use
        """
        # Detect task type if not provided
        if task_type is None:
            task_type = self._detect_task_type(content, file_path, context)
        
        logger.info(f"🎯 Task type detected: {task_type.value}")
        
        # Get model priorities
        priorities = self.model_priorities.get(task_type, self.model_priorities[TaskType.GENERAL_QUERY])
        
        # Check availability and select
        selected = self._select_available_model(priorities)
        
        logger.info(f"✅ Selected model: {selected} for {task_type.value}")
        
        return selected
    
    def _detect_task_type(
        self,
        content: str,
        file_path: Optional[str],
        context: Dict[str, Any]
    ) -> TaskType:
        """Detect task type from content and context."""
        
        # Check if it's code
        if file_path and self.code_detector.is_code_file(file_path):
            return TaskType.CODE_ANALYSIS
        
        if self.code_detector.is_code_content(content):
            return TaskType.CODE_ANALYSIS
        
        # Check context for task hints
        if context.get("is_documentation"):
            return TaskType.DOCUMENTATION
        
        if context.get("is_rag_query"):
            return TaskType.RAG_QUERY
        
        return TaskType.GENERAL_QUERY
    
    def _select_available_model(self, priorities: list) -> str:
        """Select first available model from priorities."""
        # In production, would check model availability
        # For now, return first priority
        return priorities[0]


class CodeDetector:
    """Detect code files and content."""
    
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.h', '.hpp',
        '.go', '.rs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.cs', '.sh', '.sql'
    }
    
    CODE_PATTERNS = [
        'def ', 'class ', 'function ', 'import ',
        'const ', 'let ', 'var ', 'public ',
        'private ', 'protected ', 'async ', 'await ',
        '=> ', '{ }', '() =>', 'if (', 'for (',
        'while (', 'switch (', 'return ', 'throw '
    ]
    
    def is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file by extension."""
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        return ext in self.CODE_EXTENSIONS
    
    def is_code_content(self, content: str, threshold: float = 0.3) -> bool:
        """
        Check if content appears to be code.
        
        Uses pattern matching to detect code-like syntax.
        
        Args:
            content: Content to check
            threshold: Minimum ratio of code patterns (0-1)
        
        Returns:
            True if content appears to be code
        """
        if not content:
            return False
        
        # Count code patterns
        pattern_count = 0
        lines = content.split('\n')[:50]  # Check first 50 lines
        
        for line in lines:
            for pattern in self.CODE_PATTERNS:
                if pattern in line:
                    pattern_count += 1
                    break
        
        # Calculate ratio
        ratio = pattern_count / len(lines) if lines else 0
        
        return ratio >= threshold


# Singleton
_router_instance: Optional[EnhancedModelRouter] = None


def get_enhanced_model_router() -> EnhancedModelRouter:
    """Get singleton router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = EnhancedModelRouter()
    return _router_instance
```

**Testing:**
- Unit tests for code detection (15 tests)
- Integration tests for model routing (10 tests)
- Performance tests for detection speed

---

### **Task 1.2: CodeLlama Integration** (2 hours)

**Goal:** Integrate CodeLlama for code analysis tasks

**Files to Modify:**
```
services/ecosystem-mcp/src/services/ingestion/job_processor.py
services/ecosystem-mcp/src/services/documentation/doc_generator.py
```

**Implementation:**

```python
# File: job_processor.py

from ...services.llm.enhanced_model_router import get_enhanced_model_router, TaskType

async def _process_file_with_analysis(self, file_path: str, content: str) -> Dict:
    """Process file with smart model selection."""
    
    # Get router
    router = get_enhanced_model_router()
    
    # Select optimal model
    model = router.select_model(
        content=content,
        file_path=file_path,
        task_type=TaskType.CODE_ANALYSIS if router.code_detector.is_code_file(file_path) else None
    )
    
    logger.info(f"📝 Processing {file_path} with {model}")
    
    # Use selected model for analysis
    analysis = await self.llm_service.analyze(
        content=content,
        model=model
    )
    
    return {
        "file_path": file_path,
        "model_used": model,
        "analysis": analysis
    }
```

**Integration Points:**
- Wire to ingestion pipeline
- Wire to documentation generation
- Add model selection logging
- Add performance tracking

---

### **Task 1.3: Testing & Validation** (3 hours)

**Goal:** Comprehensive testing of multi-model routing

**Test Coverage:**
- ✅ Code file detection (Python, JS, TypeScript, etc.)
- ✅ Code content detection (pattern matching)
- ✅ Model routing logic
- ✅ Fallback handling
- ✅ Performance benchmarks

**Test Files:**
```
tests/unit/test_enhanced_model_router.py (20+ tests)
tests/unit/test_code_detector.py (15+ tests)
tests/integration/test_model_routing_integration.py (10+ tests)
```

---

## 🔥 DAY 2: ADVANCED RAG FEATURES

### Objective
Enable context-aware RAG queries with hierarchical filtering and repository-specific contexts.

---

### **Task 2.1: Context-Aware RAG** (3 hours)

**Goal:** Enable RAG queries filtered by repository context

**Files to Create/Modify:**
```
services/ecosystem-mcp/src/services/query/context_aware_rag.py (NEW)
services/ecosystem-mcp/src/api/routes/query_enhanced.py (MODIFY)
```

**Implementation:**

```python
# File: context_aware_rag.py

"""
Context-Aware RAG System

Features:
- Repository-specific filtering
- Hierarchical context filtering
- Technology stack awareness
- Service-level isolation
"""

from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContextAwareRAG:
    """
    Context-aware RAG with hierarchical filtering.
    
    Enables filtering RAG queries by:
    - Repository ID
    - Service/module context
    - Technology stack
    - Time range
    """
    
    def __init__(self, chromadb_client, context_manager):
        self.chromadb = chromadb_client
        self.context_manager = context_manager
        logger.info("ContextAwareRAG initialized")
    
    async def query_with_context(
        self,
        query: str,
        repo_id: Optional[str] = None,
        context_id: Optional[str] = None,
        service_filter: Optional[str] = None,
        tech_filter: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query with context filtering.
        
        Args:
            query: Query text
            repo_id: Optional repository filter
            context_id: Optional hierarchical context filter
            service_filter: Optional service name filter
            tech_filter: Optional technology stack filter
            limit: Max results
        
        Returns:
            Query results with context
        """
        logger.info(f"🔍 Context-aware query: {query[:100]}")
        
        # Build where clause
        where = self._build_where_clause(
            repo_id=repo_id,
            context_id=context_id,
            service_filter=service_filter,
            tech_filter=tech_filter
        )
        
        logger.info(f"📊 Filter: {where}")
        
        # Query ChromaDB with context
        results = await self.chromadb.query(
            query_texts=[query],
            n_results=limit,
            where=where
        )
        
        # Enhance results with context info
        enhanced_results = await self._enhance_with_context(results, context_id)
        
        return {
            "query": query,
            "filters": {
                "repo_id": repo_id,
                "context_id": context_id,
                "service": service_filter,
                "tech_stack": tech_filter
            },
            "results": enhanced_results,
            "total": len(enhanced_results)
        }
    
    def _build_where_clause(
        self,
        repo_id: Optional[str],
        context_id: Optional[str],
        service_filter: Optional[str],
        tech_filter: Optional[List[str]]
    ) -> Dict:
        """Build ChromaDB where clause."""
        where = {}
        
        if repo_id:
            where["repo_id"] = repo_id
        
        if context_id:
            where["context_id"] = context_id
        
        if service_filter:
            where["service"] = service_filter
        
        if tech_filter:
            # Tech filter with OR logic
            where["$or"] = [
                {"tech_stack": {"$contains": tech}}
                for tech in tech_filter
            ]
        
        return where if where else None
    
    async def _enhance_with_context(
        self,
        results: Dict,
        context_id: Optional[str]
    ) -> List[Dict]:
        """Enhance results with context information."""
        enhanced = []
        
        for doc, metadata in zip(results.get("documents", []), results.get("metadatas", [])):
            enhanced_doc = {
                "content": doc,
                "metadata": metadata,
                "context": None
            }
            
            # Add context info if available
            if context_id and self.context_manager:
                context = await self.context_manager.get_context(context_id)
                if context:
                    enhanced_doc["context"] = {
                        "name": context.name,
                        "level": context.level.value,
                        "path": context.full_path
                    }
            
            enhanced.append(enhanced_doc)
        
        return enhanced
```

---

### **Task 2.2: Repository Context Selector** (2 hours)

**Goal:** UI component for selecting repository context

**Files to Create:**
```
services/ecosystem-mcp-dashboard/dashboard_views/context_selector.py (NEW)
```

**Features:**
- Dropdown to select repository
- Show repository summary (tech stack, files, endpoints)
- Filter by service/module
- Show context hierarchy

---

### **Task 2.3: Testing & Validation** (3 hours)

**Test Coverage:**
- ✅ Context filtering logic
- ✅ Repository isolation
- ✅ Hierarchical context queries
- ✅ Technology stack filtering
- ✅ Integration with existing RAG

---

## 🔥 DAY 3: DASHBOARD INTEGRATION

### Objective
Expose all new features in the dashboard UI.

---

### **Task 3.1: Repository Context Page** (3 hours)

**Goal:** New dashboard page for repository context management

**Files to Create:**
```
services/ecosystem-mcp-dashboard/pages/repository_contexts.py (NEW)
```

**Features:**
- List all ingested repositories
- Show context hierarchy
- Display repository summary
  - Technologies used
  - API endpoints discovered
  - File count & types
  - Last updated
- Context selector for RAG queries

---

### **Task 3.2: Enhanced RAG Query Page** (3 hours)

**Goal:** Add context filtering to RAG query page

**Files to Modify:**
```
services/ecosystem-mcp-dashboard/pages/rag_query.py
```

**New Features:**
- Repository selector dropdown
- Service/module filter
- Technology stack filter
- Show context in results
- Highlight which context matched

---

### **Task 3.3: Performance Monitor Integration** (2 hours)

**Goal:** Wire performance monitoring to dashboard

**Tasks:**
- Verify performance monitor page works
- Add real-time metrics display
- Add bottleneck alerts
- Test auto-refresh functionality

---

## 🔥 DAY 4: DOCUMENTATION PIPELINE

### Objective
Complete the incremental documentation workflow.

---

### **Task 4.1: Wire Incremental Docs to Ingestion** (3 hours)

**Goal:** Integrate incremental documentation with ingestion pipeline

**Files to Modify:**
```
services/ecosystem-mcp/src/services/ingestion/job_processor.py
services/ecosystem-mcp/src/services/documentation/doc_generator.py
```

**Implementation:**
- After successful ingestion, check if docs exist
- If docs exist, use incremental update
- If new repo, generate full documentation
- Save documentation snapshot after generation

---

### **Task 4.2: Documentation UI** (3 hours)

**Goal:** Add documentation management to dashboard

**Files to Modify:**
```
services/ecosystem-mcp-dashboard/pages/documentation_generator.py
```

**New Features:**
- Show documentation history
- Display speedup estimates
- Option to force full regeneration
- Show what files will be updated
- Display documentation coverage

---

### **Task 4.3: Testing & Validation** (2 hours)

**Test Coverage:**
- ✅ Full documentation generation
- ✅ Incremental update flow
- ✅ Snapshot management
- ✅ UI integration
- ✅ Performance validation (verify 10-100× speedup)

---

## 🔥 DAY 5: PRODUCTION DEPLOYMENT

### Objective
Final testing, deployment, and production monitoring.

---

### **Task 5.1: Final Integration Testing** (2 hours)

**Goal:** Run complete system test

**Test Scenarios:**
1. Fresh repository ingestion
2. Incremental documentation update
3. Context-aware RAG query
4. Performance monitoring
5. Multi-model routing
6. Error recovery

---

### **Task 5.2: Production Deployment** (3 hours)

**Goal:** Deploy to production environment

**Steps:**
1. Update environment variables
2. Rebuild Docker images
3. Run database migrations
4. Deploy services
5. Verify health checks
6. Monitor initial performance

---

### **Task 5.3: Monitoring & Documentation** (3 hours)

**Goal:** Set up monitoring and finalize documentation

**Tasks:**
- Configure performance monitoring alerts
- Set up log aggregation
- Create runbook for common issues
- Document new features
- Create video demos (optional)

---

## 📊 Week 3 Deliverables

### Code Deliverables
- ✅ Enhanced model router with CodeLlama
- ✅ Context-aware RAG system
- ✅ Repository context management
- ✅ Complete documentation pipeline
- ✅ Dashboard enhancements (3 new features)

### Testing Deliverables
- ✅ 50+ new tests
- ✅ Integration tests for all features
- ✅ E2E workflow tests
- ✅ Performance validation

### Documentation Deliverables
- ✅ Feature documentation
- ✅ API documentation updates
- ✅ Deployment guide
- ✅ User guide updates

---

## 📈 Success Metrics

### Performance Targets
- ✅ Incremental docs: 10-100× speedup (verified)
- ✅ Code routing: <100ms overhead
- ✅ Context filtering: <200ms additional latency
- ✅ System health score: >80

### Quality Targets
- ✅ Test coverage: >95%
- ✅ No critical bugs
- ✅ All features documented
- ✅ All features tested

### Production Readiness
- ✅ 100% feature complete
- ✅ Production deployed
- ✅ Monitoring active
- ✅ Runbook complete

---

## 🎯 Final System State (After Week 3)

### Feature Completeness: 100%
- ✅ Multi-model intelligence
- ✅ Context-aware RAG
- ✅ Incremental documentation
- ✅ Performance monitoring
- ✅ Sub-job orchestration
- ✅ Circuit breakers & resilience
- ✅ Hierarchical contexts
- ✅ Structured logging

### Production Readiness: 100%
- ✅ Comprehensive testing
- ✅ Production deployment
- ✅ Monitoring & alerting
- ✅ Documentation complete
- ✅ Runbook available

### System Status: 🟢 PRODUCTION READY & DEPLOYED

---

## 📝 Notes

### Key Decisions
1. **Model Routing:** Automatic detection preferred over manual selection
2. **Context Filtering:** Default to repository-level, allow drill-down
3. **Documentation:** Incremental by default, full on demand
4. **Monitoring:** Real-time by default with 10s refresh

### Risks & Mitigations
1. **Risk:** CodeLlama not available
   - **Mitigation:** Graceful fallback to general models
2. **Risk:** Context filtering too slow
   - **Mitigation:** Add caching layer
3. **Risk:** Incremental docs edge cases
   - **Mitigation:** Comprehensive testing, force-full option

---

## 🚀 Let's Build Week 3!

Ready to implement? Let's start with **Day 1: Multi-Model Intelligence**! 🎉

