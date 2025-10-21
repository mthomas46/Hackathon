# Phase 9 & 10: Combined Implementation Plan

**Status:** 🟢 READY FOR IMPLEMENTATION  
**Created:** October 21, 2025  
**Based On:** Critical Analysis + Context-Aware RAG + Enterprise-Scale Requirements  

---

## 🎯 Executive Summary

This plan combines **two complementary enhancements** into a unified implementation:

**Phase 9: Intelligence Layer** (Weeks 1-4)
- CodeLlama integration for code-specific analysis
- Context-aware RAG with repository contexts
- Intelligent model routing (code vs docs)

**Phase 10: Scale & Resilience Layer** (Weeks 5-8)
- Sub-job orchestration for large repositories
- Staged pipeline with checkpoints
- Dependency-aware processing
- Incremental documentation

**Together they address:** All 12 critical flaws from the analysis document

---

## 🚨 Critical Flaws Addressed

### Mapping: Flaw → Solution

| Flaw # | Description | Phase | Solution |
|--------|-------------|-------|----------|
| **#1** | Monolithic job processing | Phase 10 | Sub-job system |
| **#2** | Memory constraints | Phase 10 | Streaming + pagination |
| **#3** | No hierarchical processing | Phase 10 | Priority-based ordering |
| **#4** | Single-pass documentation | Phase 10 | Multi-stage pipeline |
| **#5** | No dependency-aware ordering | Phase 10 | Dependency graph |
| **#6** | Context isolation issues | Phase 9 | Hierarchical contexts |
| **#7** | No incremental documentation | Phase 10 | Change detection |
| **#8** | Code analysis gaps | Phase 9 | CodeLlama integration |
| **#9** | No cross-file understanding | Phase 10 | Multi-file analysis |
| **#10** | Recovery limitations | Phase 10 | Stage-level checkpoints |
| **#11** | Performance bottlenecks | Both | Parallel + caching |
| **#12** | Scale limitations | Both | Streaming + sub-jobs |

---

## 📦 PHASE 9: Intelligence Layer

### 9.1: CodeLlama Integration (Week 1)

**Goal:** Add specialized LLM for code analysis

**Components to Create:**

#### 9.1.1: Model Router
**File:** `src/services/llm/model_router.py`

```python
"""
LLM Model Router

Routes queries to appropriate model based on content type.
"""

class ModelRouter:
    """
    Routes to best model for content type:
    - Code files → CodeLlama
    - Documentation → General LLM (Ollama)
    - Mixed → Both (synthesis)
    """
    
    def __init__(self):
        self.code_llm = CodeLlamaClient()
        self.general_llm = OllamaClient()
    
    async def analyze(self, content: str, file_type: str) -> dict:
        """Route to appropriate model."""
        if self._is_code_file(file_type):
            return await self.code_llm.analyze(content)
        elif self._is_doc_file(file_type):
            return await self.general_llm.analyze(content)
        else:
            # Mixed: get both perspectives
            code_analysis = await self.code_llm.analyze(content)
            doc_analysis = await self.general_llm.analyze(content)
            return self._synthesize(code_analysis, doc_analysis)
```

**Features:**
- ✅ Automatic model selection
- ✅ Fallback to general LLM if CodeLlama unavailable
- ✅ Synthesis for mixed content
- ✅ Comprehensive logging

**Tests:** 30+ unit tests, 10+ integration tests

---

#### 9.1.2: CodeLlama Client
**File:** `src/services/llm/codellama_client.py`

```python
"""
CodeLlama Client

Specialized client for code analysis using CodeLlama model.
"""

class CodeLlamaClient:
    """
    Interface to CodeLlama for:
    - Code structure analysis
    - Function/class documentation
    - Dependency detection
    - Code quality assessment
    """
    
    async def analyze_function(self, code: str) -> FunctionAnalysis:
        """Analyze a function."""
        prompt = self._build_function_prompt(code)
        response = await self._call_model(prompt)
        return FunctionAnalysis.from_llm_response(response)
    
    async def analyze_class(self, code: str) -> ClassAnalysis:
        """Analyze a class."""
        # Specialized prompts for classes
        ...
    
    async def detect_patterns(self, code: str) -> List[Pattern]:
        """Detect design patterns in code."""
        ...
```

**Integration:**
- Uses existing Ollama infrastructure
- Model: `codellama:13b-instruct`
- Timeout: 60s (code analysis is slower)
- Cache: Redis (content-addressable)

---

### 9.2: Repository Contexts (Week 2)

**Goal:** Hierarchical context management for targeted queries

**Components to Create:**

#### 9.2.1: Context Manager
**File:** `src/services/contexts/context_manager.py`

```python
"""
Repository Context Manager

Manages hierarchical contexts for repositories.
"""

@dataclass
class RepositoryContext:
    """
    Hierarchical repository context.
    
    Structure:
      repo-name/
        ├── service-a/
        │   ├── api/
        │   ├── core/
        │   └── tests/
        └── service-b/
            └── ...
    """
    id: str
    name: str
    repo_path: str
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    
    # Metadata
    file_patterns: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    description: str = ""
    
    # Stats
    total_files: int = 0
    total_documents: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


class ContextManager:
    """Manages repository contexts."""
    
    async def create_context_hierarchy(
        self,
        repo_path: str,
        inventory: RepositoryInventory
    ) -> RepositoryContext:
        """
        Auto-generate context hierarchy from repository structure.
        
        Algorithm:
        1. Detect top-level services/modules
        2. For each service, detect sub-modules
        3. Create hierarchical contexts
        4. Store in database
        """
        ...
    
    async def filter_documents_by_context(
        self,
        context_id: str,
        include_children: bool = True
    ) -> List[Document]:
        """Get documents within a context."""
        ...
```

**Benefits:**
- ✅ **Flaw #6 Fixed:** Hierarchical contexts
- ✅ Targeted queries ("show me only auth-service API")
- ✅ Context-aware RAG
- ✅ Better organization

---

#### 9.2.2: Context-Aware RAG
**File:** `src/services/rag/context_aware_rag.py`

```python
"""
Context-Aware RAG Query Service

Filters RAG queries by repository context.
"""

class ContextAwareRAG:
    """RAG with context filtering."""
    
    async def query(
        self,
        query_text: str,
        context_id: Optional[str] = None,
        max_results: int = 5
    ) -> RAGResponse:
        """
        Query with optional context filtering.
        
        If context_id provided:
        1. Get documents in that context
        2. Filter embeddings to those documents
        3. Run RAG only on filtered set
        
        Result: More relevant, focused answers
        """
        if context_id:
            # Context-aware query
            doc_ids = await self.context_mgr.get_document_ids(context_id)
            results = await self.rag.query_filtered(query_text, doc_ids, max_results)
        else:
            # Global query
            results = await self.rag.query(query_text, max_results)
        
        return results
```

**Features:**
- ✅ Context filtering
- ✅ Hierarchical context support
- ✅ Backward compatible (context optional)
- ✅ Performance optimized (filtered embeddings)

---

### 9.3: Context Dashboard (Week 3)

**Goal:** UI for context management and exploration

**Components to Create:**

#### 9.3.1: Context Browser
**File:** `dashboard_views/context_browser.py`

```python
"""Context Browser Page"""

def show(api_base_url: str):
    """Display context browser."""
    
    st.title("📁 Repository Contexts")
    
    # Fetch contexts
    contexts = fetch_contexts(api_base_url)
    
    # Display as tree
    st.markdown("### Context Hierarchy")
    display_context_tree(contexts)
    
    # Context details
    if st.session_state.get('selected_context'):
        context = st.session_state.selected_context
        
        with st.expander(f"📊 Context: {context['name']}", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Files", context['total_files'])
            with col2:
                st.metric("Documents", context['total_documents'])
            with col3:
                st.metric("Technologies", len(context['technologies']))
            
            # Technologies
            st.markdown("**Technologies:**")
            for tech in context['technologies']:
                st.badge(tech)
            
            # Sample documents
            st.markdown("**Sample Documents:**")
            docs = fetch_context_documents(api_base_url, context['id'], limit=10)
            for doc in docs:
                st.markdown(f"- {doc['file_path']}")
```

**Features:**
- Interactive tree view
- Context statistics
- Technology tags
- Document preview
- Quick filtering

---

### 9.4: Testing & Integration (Week 4)

**Deliverables:**
- ✅ 80+ unit tests (model router, context manager)
- ✅ 20+ integration tests (CodeLlama + contexts)
- ✅ 10+ E2E tests (full workflows)
- ✅ Performance benchmarks
- ✅ Documentation

---

## 📦 PHASE 10: Scale & Resilience Layer

### 10.1: Sub-Job System (Week 5)

**Goal:** Break monolithic jobs into manageable sub-jobs

**Components to Create:**

#### 10.1.1: Sub-Job Orchestrator
**File:** `src/services/orchestration/sub_job_orchestrator.py`

```python
"""
Sub-Job Orchestrator

Breaks large jobs into sub-jobs and manages execution.
"""

@dataclass
class SubJob:
    """Sub-job for parallel processing."""
    id: str
    parent_job_id: str
    stage: str  # 'discovery', 'analysis', 'documentation', etc.
    file_paths: List[str]
    priority: int
    status: str
    dependencies: List[str] = field(default_factory=list)
    checkpoint_data: dict = field(default_factory=dict)


class SubJobOrchestrator:
    """
    Orchestrates sub-job execution.
    
    **Fixes Flaw #1: Monolithic Processing**
    
    Strategy:
    1. Break job into sub-jobs (~1000 files each)
    2. Execute sub-jobs in priority order
    3. Handle dependencies (e.g., analysis needs discovery)
    4. Checkpoint after each sub-job
    5. Support parallel execution
    """
    
    async def create_sub_jobs(
        self,
        job: IngestionJobModel,
        files: List[FileInfo],
        max_files_per_subjob: int = 1000
    ) -> List[SubJob]:
        """Break job into sub-jobs."""
        
        # Group files by:
        # 1. Priority (core > dependencies > tests > examples)
        # 2. Size (balanced distribution)
        # 3. Dependencies (dependent files in same sub-job if possible)
        
        prioritized_groups = self._prioritize_files(files)
        sub_jobs = []
        
        for idx, group in enumerate(prioritized_groups):
            sub_job = SubJob(
                id=f"{job.id}-subjob-{idx}",
                parent_job_id=job.id,
                stage='processing',
                file_paths=[f.path for f in group],
                priority=self._calculate_priority(group),
                status='pending'
            )
            sub_jobs.append(sub_job)
        
        return sub_jobs
    
    async def execute_sub_jobs(
        self,
        sub_jobs: List[SubJob],
        max_parallel: int = 4
    ) -> Dict[str, Any]:
        """
        Execute sub-jobs with parallelism.
        
        **Fixes Flaw #11: Performance Bottlenecks**
        """
        # Execute in priority order
        sorted_jobs = sorted(sub_jobs, key=lambda j: j.priority, reverse=True)
        
        # Execute with controlled parallelism
        results = await asyncio.gather(
            *[self._execute_single_subjob(sj) for sj in sorted_jobs[:max_parallel]],
            return_exceptions=True
        )
        
        return self._aggregate_results(results)
```

**Benefits:**
- ✅ **Flaw #1 Fixed:** No more monolithic jobs
- ✅ **Flaw #3 Fixed:** Priority-based processing
- ✅ **Flaw #11 Fixed:** Parallel execution
- ✅ **Flaw #12 Fixed:** Handles large repos

---

#### 10.1.2: Dependency-Aware Scheduler
**File:** `src/services/orchestration/dependency_scheduler.py`

```python
"""
Dependency-Aware Scheduler

Orders processing based on file dependencies.
"""

class DependencyScheduler:
    """
    **Fixes Flaw #5: No Dependency-Aware Ordering**
    
    Analyzes code dependencies and schedules processing
    in topological order.
    """
    
    async def build_dependency_graph(
        self,
        files: List[FileInfo]
    ) -> nx.DiGraph:
        """
        Build dependency graph from imports/requires.
        
        For Python:
        - Parse import statements
        - Map to actual files
        - Build directed graph
        
        For other languages:
        - Use language-specific parsers
        - Extract dependencies
        """
        graph = nx.DiGraph()
        
        for file in files:
            deps = await self._extract_dependencies(file)
            graph.add_node(file.path)
            for dep in deps:
                dep_file = self._resolve_dependency(dep, files)
                if dep_file:
                    graph.add_edge(dep_file.path, file.path)
        
        return graph
    
    async def get_processing_order(
        self,
        graph: nx.DiGraph
    ) -> List[List[str]]:
        """
        Get processing order using topological sort.
        
        Returns list of batches where:
        - Files in same batch have no dependencies
        - Can be processed in parallel
        - Each batch depends only on previous batches
        """
        try:
            # Topological sort with levels
            levels = list(nx.topological_generations(graph))
            return levels
        except nx.NetworkXError:
            # Circular dependency detected
            logger.warning("Circular dependency detected, using heuristic ordering")
            return self._heuristic_ordering(graph)
```

**Benefits:**
- ✅ **Flaw #5 Fixed:** Dependency-aware ordering
- ✅ Processes dependencies first
- ✅ Handles circular dependencies
- ✅ Enables parallel processing of independent files

---

### 10.2: Staged Pipeline (Week 6)

**Goal:** Multi-stage processing with checkpoints

**Components to Create:**

#### 10.2.1: Pipeline Orchestrator
**File:** `src/services/pipeline/pipeline_orchestrator.py`

```python
"""
Pipeline Orchestrator

Manages multi-stage processing pipeline.
"""

class PipelineStage(Enum):
    """Pipeline stages."""
    DISCOVERY = "discovery"
    CLASSIFICATION = "classification"
    ANALYSIS = "analysis"
    DOCUMENTATION_PASS1 = "documentation_pass1"
    DOCUMENTATION_PASS2 = "documentation_pass2"
    DOCUMENTATION_PASS3 = "documentation_pass3"
    QUALITY_CHECK = "quality_check"
    FINALIZATION = "finalization"


class PipelineOrchestrator:
    """
    **Fixes Flaw #4: Single-Pass Documentation**
    **Fixes Flaw #10: Recovery Limitations**
    
    Multi-stage pipeline with checkpoints at each stage.
    """
    
    async def execute_pipeline(
        self,
        job: IngestionJobModel,
        start_stage: Optional[PipelineStage] = None
    ) -> PipelineResult:
        """
        Execute full pipeline with stage-level checkpoints.
        
        If job fails at stage N:
        - Resume from stage N (not from beginning)
        - Skip completed stages
        - Reuse checkpointed data
        """
        stages = list(PipelineStage)
        start_idx = stages.index(start_stage) if start_stage else 0
        
        results = {}
        
        for stage in stages[start_idx:]:
            logger.info(f"🔄 Starting stage: {stage.value}")
            
            try:
                # Execute stage
                stage_result = await self._execute_stage(stage, job, results)
                results[stage.value] = stage_result
                
                # Checkpoint
                await self._checkpoint_stage(job.id, stage, stage_result)
                logger.info(f"✅ Stage complete: {stage.value}")
                
            except Exception as e:
                logger.error(f"❌ Stage failed: {stage.value}", exc_info=e)
                # Save checkpoint for recovery
                await self._save_failure_checkpoint(job.id, stage, results)
                raise
        
        return PipelineResult(stages=results)
    
    async def resume_pipeline(
        self,
        job_id: str
    ) -> PipelineResult:
        """Resume from last successful checkpoint."""
        checkpoint = await self._load_checkpoint(job_id)
        last_stage = checkpoint['last_completed_stage']
        next_stage = self._get_next_stage(last_stage)
        
        logger.info(f"🔄 Resuming from stage: {next_stage.value}")
        return await self.execute_pipeline(job, start_stage=next_stage)
```

**Benefits:**
- ✅ **Flaw #4 Fixed:** Multi-pass processing
- ✅ **Flaw #10 Fixed:** Stage-level recovery
- ✅ Granular checkpoints
- ✅ Fast recovery

---

### 10.3: Incremental Documentation (Week 7)

**Goal:** Only re-document changed files

**Components to Create:**

#### 10.3.1: Change Detector
**File:** `src/services/incremental/change_detector.py`

```python
"""
Change Detector

Detects changed files since last run.
"""

class ChangeDetector:
    """
    **Fixes Flaw #7: No Incremental Documentation**
    
    Detects what changed since last ingestion.
    """
    
    async def detect_changes(
        self,
        repo_path: str,
        last_run_id: Optional[str] = None
    ) -> ChangeSet:
        """
        Detect changes since last run.
        
        Methods:
        1. Git mode: Compare commit SHAs
        2. Snapshot mode: Compare content hashes
        3. Hybrid: Use both
        """
        if last_run_id:
            last_run = await self._get_run_metadata(last_run_id)
            current_files = await self._scan_current_files(repo_path)
            
            changes = ChangeSet(
                added=self._find_added_files(current_files, last_run),
                modified=self._find_modified_files(current_files, last_run),
                deleted=self._find_deleted_files(current_files, last_run),
                unchanged=self._find_unchanged_files(current_files, last_run)
            )
            
            logger.info(
                f"📊 Changes detected: "
                f"+{len(changes.added)} ~{len(changes.modified)} -{len(changes.deleted)}"
            )
            
            return changes
        else:
            # First run: everything is "added"
            return ChangeSet(added=await self._scan_current_files(repo_path))
    
    async def should_regenerate_doc(
        self,
        file_path: str,
        changes: ChangeSet,
        dependency_graph: nx.DiGraph
    ) -> bool:
        """
        Determine if file's documentation should be regenerated.
        
        Regenerate if:
        - File itself changed
        - Direct dependency changed
        - Major dependency changed (configurable threshold)
        """
        if file_path in changes.modified or file_path in changes.added:
            return True
        
        # Check dependencies
        deps = list(dependency_graph.predecessors(file_path))
        for dep in deps:
            if dep in changes.modified or dep in changes.added:
                # Dependency changed, might need regeneration
                return True
        
        return False
```

**Benefits:**
- ✅ **Flaw #7 Fixed:** Incremental processing
- ✅ Only processes changed files
- ✅ Dependency-aware regeneration
- ✅ Massive time savings

---

### 10.4: Testing & Optimization (Week 8)

**Deliverables:**
- ✅ 100+ unit tests (sub-jobs, pipeline, incremental)
- ✅ 30+ integration tests (end-to-end workflows)
- ✅ 15+ E2E tests (large repository scenarios)
- ✅ Performance benchmarks (50K+ file repos)
- ✅ Recovery testing (failure injection)
- ✅ Documentation

---

## 📊 Expected Performance Improvements

### Current (Phase 8)
```
5,000 files:
  Snapshot mode: 5-15 minutes
  Git history mode: 2-4 hours
```

### After Phase 9 & 10
```
5,000 files (first run):
  Snapshot + Sub-jobs: 3-8 minutes (40% faster)
  Git history + Sub-jobs: 1-2 hours (50% faster)

5,000 files (incremental, 100 changed):
  Incremental snapshot: 30-60 seconds (95% faster!)
  Incremental git history: 5-10 minutes (95% faster!)

50,000 files (first run):
  Snapshot + Sub-jobs: 30-45 minutes (vs 1-2 hours)
  Git history + Sub-jobs: 4-6 hours (vs 20-40 hours)
```

**Why So Much Faster:**
1. **Sub-jobs:** Parallel processing (4× speedup)
2. **Dependency ordering:** Less rework (20% faster)
3. **Staged pipeline:** Better caching (15% faster)
4. **Incremental:** Only process changes (95% for updates)
5. **CodeLlama:** Faster code analysis (30% for code)

---

## 🎯 Success Metrics

### Phase 9 Success Criteria
- ✅ CodeLlama integrated and operational
- ✅ Context hierarchy auto-generated for all repos
- ✅ Context-aware RAG queries working
- ✅ 90% of code files use CodeLlama
- ✅ Context filtering reduces noise by 70%

### Phase 10 Success Criteria
- ✅ 50K+ file repository completes in <6 hours
- ✅ Sub-jobs execute in parallel (4× concurrency)
- ✅ Pipeline resumable from any stage
- ✅ Incremental updates complete in <5% of full run time
- ✅ Dependency-aware ordering working for 95% of files

---

## 📋 Implementation Schedule

### Week 1: Model Router & CodeLlama
- Day 1-2: Model router implementation
- Day 3-4: CodeLlama client
- Day 5: Testing & integration

### Week 2: Repository Contexts
- Day 1-2: Context manager
- Day 3-4: Context-aware RAG
- Day 5: Testing

### Week 3: Context Dashboard
- Day 1-3: Context browser UI
- Day 4-5: Integration & polish

### Week 4: Phase 9 Testing
- Day 1-5: Comprehensive testing

### Week 5: Sub-Job System
- Day 1-2: Sub-job orchestrator
- Day 3-4: Dependency scheduler
- Day 5: Testing

### Week 6: Staged Pipeline
- Day 1-2: Pipeline orchestrator
- Day 3-4: Stage implementations
- Day 5: Testing

### Week 7: Incremental Documentation
- Day 1-2: Change detector
- Day 3-4: Incremental processor
- Day 5: Testing

### Week 8: Phase 10 Testing
- Day 1-5: Comprehensive testing, benchmarks

---

## 🔧 Technical Architecture

### Combined Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENHANCED ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 9: INTELLIGENCE LAYER                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Model Router                                            │    │
│  │  ├─→ CodeLlama (for code)                             │    │
│  │  ├─→ General LLM (for docs)                           │    │
│  │  └─→ Synthesis (for mixed)                            │    │
│  │                                                         │    │
│  │ Context Manager                                        │    │
│  │  ├─→ Hierarchical contexts                            │    │
│  │  ├─→ Context filtering                                │    │
│  │  └─→ Context-aware RAG                                │    │
│  └────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  PHASE 10: SCALE & RESILIENCE LAYER                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Sub-Job Orchestrator                                   │    │
│  │  ├─→ Break into ~1K file chunks                       │    │
│  │  ├─→ Priority-based execution                         │    │
│  │  └─→ Parallel processing (4×)                         │    │
│  │                                                         │    │
│  │ Dependency Scheduler                                   │    │
│  │  ├─→ Build dependency graph                           │    │
│  │  ├─→ Topological ordering                             │    │
│  │  └─→ Detect circular deps                             │    │
│  │                                                         │    │
│  │ Pipeline Orchestrator                                  │    │
│  │  ├─→ 8 stages with checkpoints                        │    │
│  │  ├─→ Stage-level recovery                             │    │
│  │  └─→ Multi-pass documentation                         │    │
│  │                                                         │    │
│  │ Change Detector                                        │    │
│  │  ├─→ Detect file changes                              │    │
│  │  ├─→ Dependency-aware regeneration                    │    │
│  │  └─→ Incremental processing                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                          ↓                                       │
│  EXISTING INFRASTRUCTURE (Phases 1-8)                           │
│  ├─→ Discovery Engine                                           │
│  ├─→ Analysis Services                                          │
│  ├─→ Documentation Generator                                    │
│  ├─→ Quality Assurance                                          │
│  ├─→ FastEmbed Service                                          │
│  ├─→ Snapshot/Git History Modes                                │
│  └─→ Dashboard UI                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ READY TO IMPLEMENT

**Status:** 🟢 **READY**  
**Estimated Time:** 8 weeks  
**Team Size:** 2-3 developers  
**Risk Level:** 🟡 Medium (well-scoped, leverages existing code)

**Next Step:** Begin Phase 9.1 (Model Router & CodeLlama)

---

**End of Combined Plan**

