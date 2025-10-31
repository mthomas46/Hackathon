# Phase 3: Multi-File Analysis - Implementation Plan

**Date:** October 21, 2025  
**Status:** 🚀 Starting Implementation  
**Goal:** Analyze relationships across files for better documentation

---

## 🎯 Objectives

Build a system to analyze cross-file relationships, dependencies, and architecture patterns to enhance documentation generation.

### Key Capabilities
1. **Cross-File Dependency Analysis**
   - Import/export relationships
   - Function call graphs
   - Class inheritance hierarchies

2. **Architecture Detection**
   - Identify architectural patterns (MVC, microservices, etc.)
   - Detect service boundaries
   - Map component relationships

3. **API Endpoint Discovery**
   - REST endpoint mapping
   - GraphQL schema extraction
   - WebSocket handlers

4. **Code Structure Analysis**
   - Module organization
   - Package structure
   - Entry points and main flows

---

## 📦 Components to Build

### 1. Dependency Analyzer (Priority: HIGH)
**File:** `src/services/analysis/dependency_analyzer.py`

**Features:**
- Parse import statements (Python, JS, Go, etc.)
- Build dependency graph
- Detect circular dependencies
- Calculate coupling metrics

**Methods:**
```python
class DependencyAnalyzer:
    async def analyze_dependencies(files: List[FileInfo]) -> DependencyGraph
    async def detect_circular_dependencies() -> List[Cycle]
    async def calculate_coupling_metrics() -> Dict[str, float]
```

---

### 2. Architecture Detector (Priority: HIGH)
**File:** `src/services/analysis/architecture_detector.py`

**Features:**
- Pattern recognition (MVC, layered, microservices)
- Service boundary detection
- Component relationship mapping

**Methods:**
```python
class ArchitectureDetector:
    async def detect_patterns(files: List[FileInfo]) -> List[Pattern]
    async def identify_services() -> List[Service]
    async def map_components() -> ComponentMap
```

---

### 3. API Endpoint Extractor (Priority: MEDIUM)
**File:** `src/services/analysis/api_extractor.py`

**Features:**
- REST endpoint discovery (FastAPI, Flask, Express, etc.)
- HTTP method mapping
- Request/response schema extraction
- Route parameter detection

**Methods:**
```python
class APIExtractor:
    async def extract_endpoints(files: List[FileInfo]) -> List[Endpoint]
    async def analyze_schemas() -> Dict[str, Schema]
    async def map_routes() -> RouteMap
```

---

### 4. Code Structure Analyzer (Priority: MEDIUM)
**File:** `src/services/analysis/structure_analyzer.py`

**Features:**
- Module organization analysis
- Package hierarchy mapping
- Entry point detection
- Main execution flow tracking

**Methods:**
```python
class StructureAnalyzer:
    async def analyze_structure(files: List[FileInfo]) -> Structure
    async def detect_entry_points() -> List[EntryPoint]
    async def map_execution_flows() -> List[Flow]
```

---

### 5. Multi-File Analysis Engine (Priority: HIGH)
**File:** `src/services/analysis/analysis_engine.py`

**Features:**
- Orchestrate all analyzers
- Aggregate results
- Generate comprehensive analysis report

**Methods:**
```python
class AnalysisEngine:
    async def analyze(plan_id: str) -> AnalysisReport
    async def get_dependencies() -> DependencyGraph
    async def get_architecture() -> Architecture
    async def get_endpoints() -> List[Endpoint]
```

---

## 🗄️ Data Models

### DependencyGraph
```python
@dataclass
class Dependency:
    source_file: str
    target_file: str
    import_type: str  # 'direct', 'indirect'
    items: List[str]  # What was imported

@dataclass
class DependencyGraph:
    nodes: List[str]  # File paths
    edges: List[Dependency]
    cycles: List[List[str]]
    metrics: Dict[str, Any]
```

### Architecture Pattern
```python
@dataclass
class ArchitecturePattern:
    pattern_type: str  # 'MVC', 'Layered', 'Microservices'
    confidence: float  # 0.0-1.0
    components: List[Component]
    relationships: List[Relationship]
```

### API Endpoint
```python
@dataclass
class APIEndpoint:
    path: str
    method: str  # GET, POST, etc.
    handler_file: str
    handler_function: str
    parameters: List[Parameter]
    request_schema: Optional[Dict]
    response_schema: Optional[Dict]
```

---

## 🔄 Integration with Phase 1 & 2

### Discovery Integration
- Use file classifications from Phase 1
- Analyze only classified code files
- Skip tests/docs for dependency analysis

### Execution Integration
- Run analysis as part of ingestion
- Store results in database
- Use for documentation generation

### Workflow
```
Phase 1: Discovery
  ↓
  Scan & Classify Files
  ↓
Phase 2: Sub-Job Execution
  ↓
  Process Files + Embeddings
  ↓
Phase 3: Multi-File Analysis ← NEW
  ↓
  Analyze Dependencies & Architecture
  ↓
Phase 4: Documentation Generation
```

---

## 📊 Database Schema

### Analysis Results Table
```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES processing_plans(id),
    analysis_type VARCHAR(50),  -- 'dependency', 'architecture', 'api'
    results JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analysis_results_plan_id ON analysis_results(plan_id);
CREATE INDEX idx_analysis_results_type ON analysis_results(analysis_type);
```

### Dependencies Table
```sql
CREATE TABLE file_dependencies (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES processing_plans(id),
    source_file VARCHAR(500),
    target_file VARCHAR(500),
    import_type VARCHAR(50),
    items JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_file_dependencies_plan_id ON file_dependencies(plan_id);
CREATE INDEX idx_file_dependencies_source ON file_dependencies(source_file);
```

---

## 🎯 Implementation Phases

### Phase 3.1: Dependency Analysis (Week 5, Days 1-2)
- [ ] Create DependencyAnalyzer
- [ ] Implement import parsing (Python, JS)
- [ ] Build dependency graph
- [ ] Detect circular dependencies
- [ ] Add database storage
- [ ] Create API endpoints
- [ ] Add tests

**Estimated:** 400 lines, 2 days

---

### Phase 3.2: Architecture Detection (Week 5, Days 3-4)
- [ ] Create ArchitectureDetector
- [ ] Implement pattern recognition
- [ ] Detect service boundaries
- [ ] Map components
- [ ] Add database storage
- [ ] Create API endpoints
- [ ] Add tests

**Estimated:** 350 lines, 2 days

---

### Phase 3.3: API Extraction (Week 5, Day 5)
- [ ] Create APIExtractor
- [ ] Extract FastAPI/Flask endpoints
- [ ] Parse route definitions
- [ ] Extract schemas
- [ ] Add database storage
- [ ] Create API endpoints
- [ ] Add tests

**Estimated:** 300 lines, 1 day

---

### Phase 3.4: Analysis Engine (Week 6, Day 1)
- [ ] Create AnalysisEngine
- [ ] Orchestrate analyzers
- [ ] Aggregate results
- [ ] Generate reports
- [ ] Integrate with Phase 2
- [ ] Add tests

**Estimated:** 250 lines, 1 day

---

## 📝 API Endpoints

### Analysis Endpoints
```
POST /api/v1/analysis/analyze/{plan_id}
- Trigger multi-file analysis
- Returns: analysis_id

GET /api/v1/analysis/results/{plan_id}
- Get all analysis results
- Returns: AnalysisReport

GET /api/v1/analysis/dependencies/{plan_id}
- Get dependency graph
- Returns: DependencyGraph

GET /api/v1/analysis/architecture/{plan_id}
- Get architecture patterns
- Returns: List[Pattern]

GET /api/v1/analysis/endpoints/{plan_id}
- Get API endpoints
- Returns: List[Endpoint]
```

---

## 🧪 Testing Strategy

### Unit Tests
- Dependency parsing
- Pattern recognition
- Endpoint extraction
- Graph construction

### Integration Tests
- End-to-end analysis workflow
- Database storage
- API endpoints

### Test Data
- Sample Python/JS projects
- Known architecture patterns
- API endpoint examples

---

## 📈 Success Metrics

- **Dependency Accuracy:** >90% correct imports detected
- **Architecture Detection:** >80% pattern recognition
- **API Coverage:** 100% endpoint discovery for FastAPI
- **Performance:** <30s for 1000 files
- **Test Coverage:** >80%

---

## 🚀 Quick Start (Phase 3.1)

```python
# Example usage
from src.services.analysis import DependencyAnalyzer

analyzer = DependencyAnalyzer()
graph = await analyzer.analyze_dependencies(files)
cycles = await analyzer.detect_circular_dependencies()
metrics = await analyzer.calculate_coupling_metrics()
```

---

**Next Step:** Begin implementation of Phase 3.1 (Dependency Analyzer)

