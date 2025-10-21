# Phase 3: Multi-File Analysis - Enhanced with Full Context

**Date:** October 21, 2025  
**Status:** 🚀 IN PROGRESS  
**Context:** Aligned with FINAL_IMPLEMENTATION_PLAN.md, GIT_HISTORY_OPTIONAL_REFACTOR_PLAN.md, and CRITICAL_ANALYSIS_AND_PHASE_10.md

---

## 🎯 Enhanced Objectives

Building on the comprehensive planning documents, Phase 3 now includes:

### Core Analysis (Original)
1. ✅ Cross-file dependency analysis
2. ✅ Architecture pattern detection
3. ✅ API endpoint discovery
4. ✅ Code structure analysis

### Enhanced Features (From Planning Docs)
5. 🆕 **Repository Context Generation** (for context-aware RAG)
6. 🆕 **CodeLlama Integration** (code-specific analysis)
7. 🆕 **Dependency-Aware Topological Ordering**
8. 🆕 **Service Boundary Detection** (microservices)
9. 🆕 **Technology Stack Detection** (languages, frameworks)
10. 🆕 **Entry Point & Flow Analysis** (execution paths)

---

## 📚 Integration with Planning Documents

### From FINAL_IMPLEMENTATION_PLAN.md

**Phase 3 Goals (Page 101):**
> "Detect cross-file patterns and architecture for 50K+ file systems"

**Key Requirements:**
- Multi-file dependency graphs
- Architecture pattern recognition (MVC, microservices, layered)
- Service boundary detection
- Component relationship mapping

### From GIT_HISTORY_OPTIONAL_REFACTOR_PLAN.md

**Git-Optional Support:**
- Analysis should work with OR without Git history
- Support snapshot mode (current files only)
- Content-addressable versioning fallback

### From CRITICAL_ANALYSIS_AND_PHASE_10.md

**Enterprise-Scale Requirements (Flaws #3, #5, #6):**

**Flaw #3: No Hierarchical Processing**
> "Classify files by importance (core, dependencies, tests, examples)"
- **Phase 3 Solution:** Importance-based analysis priority

**Flaw #5: No Dependency-Aware Ordering**
> "Build dependency graph, process in topological order"
- **Phase 3 Solution:** Topological sorting of analysis

**Flaw #6: Context Isolation Issues**
> "Hierarchical contexts: service → module → component"
- **Phase 3 Solution:** Generate repository contexts

**Context-Aware RAG (Page 156):**
```
Feature: Repository Context Picker
- Each ingested repo gets a unique context
- RAG queries weighted to selected context(s)
- Context summary page with:
  • Technologies used
  • Endpoints discovered
  • Architecture type
  • Key components
```

**CodeLlama Integration (Page 163):**
```
Feature: Code-Specific Analysis
- Detect code files (vs docs/config)
- Switch from base model to code-llama
- Enhanced code understanding
- Better architecture detection
```

---

## 🔄 Enhanced Architecture

### Phase 3 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│               PHASE 3: MULTI-FILE ANALYSIS                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT: Classified files from Phase 1                       │
│                                                              │
│  Step 1: Dependency Analysis                                │
│  ├── Parse imports (Python, JS, Go, etc.)                  │
│  ├── Build dependency graph                                 │
│  ├── Detect cycles                                          │
│  └── Calculate topological order ← NEW: Use for processing │
│                                                              │
│  Step 2: Technology Stack Detection ← NEW                   │
│  ├── Detect languages (from extensions)                     │
│  ├── Detect frameworks (from imports/config)               │
│  ├── Detect databases (from connection strings)             │
│  └── Detect APIs (from route definitions)                   │
│                                                              │
│  Step 3: Architecture Detection                             │
│  ├── Identify patterns (MVC, microservices, layered)       │
│  ├── Detect service boundaries ← NEW: For microservices    │
│  ├── Map components                                         │
│  └── Find entry points ← NEW: main(), app.py, etc.         │
│                                                              │
│  Step 4: API Extraction                                      │
│  ├── REST endpoints (FastAPI, Flask, Express)              │
│  ├── GraphQL schemas                                        │
│  ├── WebSocket handlers                                     │
│  └── RPC methods                                            │
│                                                              │
│  Step 5: Repository Context Generation ← NEW                │
│  ├── Aggregate all analysis results                         │
│  ├── Generate context metadata                              │
│  ├── Create summary for RAG                                 │
│  └── Store in context_metadata table                        │
│                                                              │
│  Step 6: CodeLlama Analysis ← NEW                           │
│  ├── Identify code files needing deep analysis             │
│  ├── Route to code-llama model                             │
│  ├── Extract code patterns, idioms                         │
│  └── Enhance architecture understanding                     │
│                                                              │
│  OUTPUT: Comprehensive analysis report + Repository context │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🆕 New Components

### 1. Repository Context Generator
**File:** `src/services/analysis/context_generator.py`

**Purpose:** Create repository-level context for context-aware RAG

```python
@dataclass
class RepositoryContext:
    """Repository context for RAG filtering."""
    repo_id: str
    repo_name: str
    
    # Technology Stack
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    
    # Architecture
    architecture_type: str  # 'microservices', 'monolith', 'layered'
    service_count: int
    component_count: int
    
    # API Summary
    endpoints: List[EndpointSummary]
    endpoint_count: int
    
    # Code Metrics
    total_files: int
    total_lines: int
    test_coverage_estimate: float
    
    # Entry Points
    entry_points: List[str]
    main_flows: List[str]
    
    # AI Summary (generated by LLM)
    brief_description: str
    key_features: List[str]
    technical_highlights: List[str]

class ContextGenerator:
    async def generate_context(analysis: AnalysisReport) -> RepositoryContext
    async def generate_ai_summary(context: RepositoryContext) -> str
    async def store_context(context: RepositoryContext) -> None
```

---

### 2. Technology Stack Detector
**File:** `src/services/analysis/stack_detector.py`

**Purpose:** Identify all technologies used in the repository

```python
class TechnologyStackDetector:
    async def detect_languages(files: List[FileInfo]) -> List[str]
    async def detect_frameworks(files: List[FileInfo]) -> List[str]
    async def detect_databases(files: List[FileInfo]) -> List[str]
    async def detect_tools(files: List[FileInfo]) -> List[str]
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'python': {
            'fastapi': ['from fastapi', 'import fastapi'],
            'flask': ['from flask', 'import flask'],
            'django': ['django.conf', 'INSTALLED_APPS'],
            'sqlalchemy': ['from sqlalchemy', 'create_engine']
        },
        'javascript': {
            'react': ['import React', 'from "react"'],
            'vue': ['import Vue', 'new Vue('],
            'express': ['require("express")', 'from "express"'],
            'nextjs': ['next/router', 'getServerSideProps']
        },
        'go': {
            'gin': ['"github.com/gin-gonic/gin"'],
            'echo': ['"github.com/labstack/echo"']
        }
    }
```

---

### 3. Service Boundary Detector
**File:** `src/services/analysis/service_detector.py`

**Purpose:** Identify microservice boundaries in large systems

```python
@dataclass
class Service:
    """Detected microservice."""
    name: str
    root_path: str
    files: List[str]
    dependencies: List[str]  # Other services
    endpoints: List[Endpoint]
    databases: List[str]
    entry_point: Optional[str]

class ServiceBoundaryDetector:
    async def detect_services(files: List[FileInfo]) -> List[Service]
    async def detect_service_dependencies() -> Dict[str, List[str]]
    async def generate_service_map() -> ServiceMap
    
    # Service detection heuristics
    # - Separate directories with main/app entry points
    # - Different database connections
    # - Distinct API prefixes
    # - Docker compose services
    # - Separate package.json / requirements.txt
```

---

### 4. Code-Specific Analyzer (CodeLlama Integration)
**File:** `src/services/analysis/code_analyzer.py`

**Purpose:** Deep code analysis using CodeLlama

```python
class CodeAnalyzer:
    """
    Analyzes code files using CodeLlama model.
    
    Routes code files to specialized model for:
    - Algorithm detection
    - Design pattern recognition
    - Code complexity analysis
    - Security pattern detection
    """
    
    def __init__(self):
        self.base_model = "llama3.2:latest"  # General docs
        self.code_model = "codellama:latest"  # Code analysis
    
    async def should_use_code_model(file_info: FileInfo) -> bool:
        """Determine if file needs CodeLlama."""
        return (
            file_info.is_code and
            not file_info.is_test and
            not file_info.is_config and
            file_info.size_bytes > 500  # Substantial code
        )
    
    async def analyze_with_codellama(file_path: str, content: str) -> CodeAnalysis:
        """Perform deep code analysis."""
        # Switch to CodeLlama model
        analysis = await self._query_llm(
            model=self.code_model,
            prompt=self._build_code_analysis_prompt(content),
            context=content
        )
        
        return CodeAnalysis(
            algorithms_used=analysis['algorithms'],
            design_patterns=analysis['patterns'],
            complexity_score=analysis['complexity'],
            security_concerns=analysis['security'],
            refactoring_suggestions=analysis['suggestions']
        )
```

---

## 📊 Enhanced Database Schema

### Repository Contexts Table
```sql
CREATE TABLE repository_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id VARCHAR(500) UNIQUE NOT NULL,
    repo_name VARCHAR(500),
    
    -- Technology Stack
    languages JSONB,  -- ["Python", "JavaScript"]
    frameworks JSONB,  -- ["FastAPI", "React"]
    databases JSONB,  -- ["PostgreSQL", "Redis"]
    tools JSONB,  -- ["Docker", "pytest"]
    
    -- Architecture
    architecture_type VARCHAR(50),
    service_count INTEGER DEFAULT 1,
    component_count INTEGER,
    
    -- API Summary
    endpoint_count INTEGER DEFAULT 0,
    endpoints JSONB,  -- [{"path": "/api/v1/...", "method": "GET"}]
    
    -- Code Metrics
    total_files INTEGER,
    total_lines INTEGER,
    test_coverage_estimate FLOAT,
    
    -- Entry Points
    entry_points JSONB,  -- ["src/main.py", "app.py"]
    main_flows JSONB,
    
    -- AI Summary
    brief_description TEXT,
    key_features JSONB,
    technical_highlights JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_repo_contexts_repo_id ON repository_contexts(repo_id);
CREATE INDEX idx_repo_contexts_architecture ON repository_contexts(architecture_type);
```

### Services Table (for microservices)
```sql
CREATE TABLE detected_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id VARCHAR(500) REFERENCES repository_contexts(repo_id),
    service_name VARCHAR(200),
    root_path VARCHAR(500),
    
    -- Service Details
    file_count INTEGER,
    entry_point VARCHAR(500),
    dependencies JSONB,  -- Other services
    
    -- Service-specific
    endpoints JSONB,
    databases JSONB,
    technologies JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_detected_services_repo ON detected_services(repo_id);
CREATE INDEX idx_detected_services_name ON detected_services(service_name);
```

---

## 🔄 Integration with Phase 2 (Execution)

### Modified Sub-Job Execution Flow

```python
# In Phase 2: SubJobExecutor

async def execute_sub_job_with_analysis(sub_job, plan_id):
    """Enhanced with Phase 3 analysis."""
    
    # 1. Load file classifications (Phase 1)
    files = await load_classified_files(sub_job.id)
    
    # 2. Check if analysis is needed
    if plan_id not in analyzed_plans:
        logger.info(f"🔬 Running Phase 3 analysis for {plan_id}")
        
        # Run multi-file analysis
        analysis_engine = get_analysis_engine()
        analysis = await analysis_engine.analyze(plan_id, files)
        
        # Generate repository context
        context = await generate_repository_context(analysis)
        
        # Store context for RAG
        await store_context(context)
        
        analyzed_plans.add(plan_id)
    
    # 3. Process files in dependency order (if available)
    processing_order = await get_topological_order(plan_id) or files
    
    for file_info in processing_order:
        # 4. Determine which model to use
        if should_use_code_model(file_info):
            model = "codellama:latest"
        else:
            model = "llama3.2:latest"
        
        # 5. Process file with context
        await process_file(file_info, model=model, context=plan_id)
```

---

## 🎯 Context-Aware RAG Integration

### RAG Query with Context Filtering

```python
# In RAG Query Service

async def query_with_context(query: str, repo_context: str = None):
    """
    Query with repository context filtering.
    
    Args:
        query: User's question
        repo_context: Repository ID to filter by
    """
    
    if repo_context:
        # Filter embeddings to this repository
        filter_condition = {"repo_id": repo_context}
        
        # Add context summary to query
        context_info = await get_context_summary(repo_context)
        enhanced_query = f"""
        Repository Context: {context_info.repo_name}
        Technologies: {', '.join(context_info.technologies)}
        Architecture: {context_info.architecture_type}
        
        User Question: {query}
        """
    else:
        filter_condition = None
        enhanced_query = query
    
    # Query with context filter
    results = await chroma_db.query(
        query_text=enhanced_query,
        where=filter_condition,
        n_results=10
    )
    
    return results
```

---

## 📝 API Endpoints (Enhanced)

### Context Management
```
POST /api/v1/contexts/generate/{plan_id}
- Generate repository context from analysis
- Returns: RepositoryContext

GET /api/v1/contexts/{repo_id}
- Get repository context
- Returns: RepositoryContext with all metadata

GET /api/v1/contexts
- List all repository contexts
- Returns: List[RepositoryContext]

GET /api/v1/contexts/{repo_id}/summary
- Get AI-generated summary of repository
- Returns: Summary text + key highlights
```

### Service Detection
```
GET /api/v1/analysis/services/{repo_id}
- Get detected microservices
- Returns: List[Service]

GET /api/v1/analysis/service-map/{repo_id}
- Get service dependency map
- Returns: ServiceMap (nodes + edges)
```

### Technology Stack
```
GET /api/v1/analysis/stack/{repo_id}
- Get complete technology stack
- Returns: TechnologyStack

GET /api/v1/analysis/frameworks/{repo_id}
- Get detected frameworks
- Returns: List[Framework]
```

---

## 🧪 Testing Strategy (Enhanced)

### Unit Tests
- ✅ Dependency parsing (Python, JS, Go)
- ✅ Architecture pattern recognition
- ✅ Framework detection
- 🆕 Context generation
- 🆕 Service boundary detection
- 🆕 Topological sorting

### Integration Tests
- ✅ End-to-end analysis workflow
- 🆕 Context-aware RAG queries
- 🆕 CodeLlama model switching
- 🆕 Multi-repo context isolation

### Real-World Tests
- 🆕 Test with actual proprietary codebase
- 🆕 50K+ file repository
- 🆕 Multi-service microservices system
- 🆕 Polyglot codebase (Python + JS + Go)

---

## 🎯 Success Metrics (Enhanced)

### Technical Metrics
- Dependency accuracy: >90%
- Architecture detection: >80%
- Framework detection: >85%
- 🆕 Service boundary accuracy: >75%
- 🆕 Technology stack completeness: >90%

### Performance Metrics
- Analysis time: <2 min for 10K files
- Context generation: <30s
- 🆕 CodeLlama routing: <100ms per file
- Memory usage: <4GB for 50K files

### Business Metrics
- 🆕 RAG precision with context: +40%
- 🆕 Documentation quality: +30%
- User satisfaction: >85%

---

## 📈 Implementation Priority

### Week 1 (CURRENT)
- [x] Dependency Analyzer (basic)
- [ ] Technology Stack Detector
- [ ] Architecture Detector (basic)

### Week 2
- [ ] Service Boundary Detector
- [ ] Context Generator
- [ ] API Extraction

### Week 3
- [ ] CodeLlama Integration
- [ ] Topological Processing Order
- [ ] Context-Aware RAG

### Week 4
- [ ] Database integration
- [ ] API endpoints
- [ ] Dashboard UI
- [ ] Testing

---

**Status:** Phase 3 now fully aligned with enterprise-scale vision from planning documents!

**Next:** Complete Technology Stack Detector and Service Boundary Detector

