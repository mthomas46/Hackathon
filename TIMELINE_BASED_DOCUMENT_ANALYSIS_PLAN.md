# Timeline-Based Document Analysis Infrastructure Plan

## Executive Summary

This document outlines the architecture and implementation plan for adding **Timeline-Based Document Analysis** infrastructure to the `ecosystem-mcp` service. This feature enables users to plot normalized documents on a timeline, perform temporal analysis, track progression of work, detect API/data contract drift, perform gap analysis, and generate comprehensive reports with proper citation.

**Inspired by:** `services/project-simulation` timeline and analysis architecture  
**Target Service:** `services/ecosystem-mcp`  
**Integration Approach:** DDD-based, leveraging existing infrastructure

---

## Table of Contents

1. [Core Capabilities](#core-capabilities)
2. [Architecture Overview](#architecture-overview)
3. [Domain Model](#domain-model)
4. [Implementation Phases](#implementation-phases)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Integration Points](#integration-points)
8. [Usage Examples](#usage-examples)
9. [Testing Strategy](#testing-strategy)

---

## Core Capabilities

### 1. Timeline Document Placement
- **Chronological Organization**: Plot documents on a timeline using Git commit history, file timestamps, or content analysis
- **Phase Association**: Associate documents with discrete time periods (sprints, releases, phases)
- **Relevance Scoring**: Calculate document relevance to specific timeline events

### 2. Temporal Analysis
- **Progression Tracking**: Analyze how work on a subject evolved over time
- **Change Detection**: Identify when and why significant changes occurred
- **Velocity Metrics**: Calculate document creation/update velocity by period

### 3. Document Consolidation Intelligence
- **Redundancy Detection**: Identify duplicate or overlapping content across time
- **Version Clustering**: Group related document versions intelligently
- **Merge Recommendations**: Suggest document consolidation opportunities

### 4. Gap Analysis
- **Coverage Analysis**: Identify periods with insufficient documentation
- **Missing Context Detection**: Find gaps in documentation flow
- **Root Cause Analysis**: Determine what caused documentation gaps

### 5. API/Data Contract Drift Detection
- **Schema Evolution Tracking**: Track API and data model changes over time
- **Breaking Change Detection**: Identify incompatible changes
- **Deprecation Analysis**: Detect deprecated features and suggest migrations

### 6. Report Generation with Citations
- **Progression Reports**: Document evolution over time with evidence
- **Gap Analysis Reports**: Detailed gap identification with recommendations
- **Drift Reports**: API/contract changes with impact analysis
- **All reports**: Include proper citations to source documents

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ecosystem-MCP Service                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Timeline Analysis Module                   │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│    │
│  │  │  Timeline    │  │  Document    │  │   Temporal   ││    │
│  │  │  Manager     │  │  Placement   │  │   Analyzer   ││    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘│    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│    │
│  │  │  Gap         │  │  Drift       │  │   Report     ││    │
│  │  │  Analyzer    │  │  Detector    │  │   Generator  ││    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘│    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           Existing Ecosystem-MCP Services               │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  • Git Service (commit history, versioning)             │    │
│  │  • Document Store (PostgreSQL, ChromaDB)                │    │
│  │  • RAG Service (semantic search, analysis)              │    │
│  │  • Embedding Service (FastEmbed, vector ops)            │    │
│  │  • LLM Service (Ollama, content analysis)               │    │
│  │  • Analysis Service (AST, dependency analysis)          │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### DDD Bounded Contexts

```
services/ecosystem-mcp/src/services/timeline/
├── domain/                          # Timeline domain models
│   ├── __init__.py
│   ├── entities/
│   │   ├── timeline.py              # Timeline aggregate root
│   │   ├── time_period.py           # Time period entity
│   │   └── document_placement.py    # Document-timeline association
│   ├── value_objects/
│   │   ├── temporal_range.py        # Start/end timestamps
│   │   ├── placement_score.py       # Relevance scoring
│   │   └── drift_metrics.py         # Drift measurement
│   ├── events.py                    # Domain events
│   └── repositories.py              # Repository interfaces
│
├── application/                     # Use cases & application services
│   ├── __init__.py
│   ├── services/
│   │   ├── timeline_manager.py      # Timeline CRUD operations
│   │   ├── document_placer.py       # Place documents on timeline
│   │   ├── temporal_analyzer.py     # Time-based analysis
│   │   ├── gap_analyzer.py          # Gap detection & analysis
│   │   ├── drift_detector.py        # API/contract drift detection
│   │   └── report_generator.py      # Report generation with citations
│   └── dto/
│       ├── timeline_dto.py          # Timeline DTOs
│       └── analysis_dto.py          # Analysis result DTOs
│
└── infrastructure/                  # Infrastructure layer
    ├── __init__.py
    ├── repositories/
    │   └── timeline_repository.py   # PostgreSQL timeline repo
    ├── analyzers/
    │   ├── temporal_pattern_analyzer.py
    │   ├── schema_drift_analyzer.py
    │   └── gap_pattern_detector.py
    └── generators/
        ├── progression_report_generator.py
        ├── gap_report_generator.py
        └── drift_report_generator.py
```

---

## Domain Model

### Timeline Aggregate

```python
@dataclass
class Timeline:
    """Timeline aggregate root for organizing documents chronologically."""
    
    id: TimelineId
    name: str
    description: str
    repository_id: str  # Links to repository context
    temporal_range: TemporalRange  # Start and end timestamps
    periods: List[TimePeriod] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Metadata
    period_type: str = "git_based"  # git_based, date_based, phase_based
    auto_update: bool = True  # Auto-update with new commits
    
    def add_period(self, period: TimePeriod) -> None:
        """Add a time period to the timeline."""
        
    def place_document(self, document_id: str, period_id: str, 
                      relevance_score: float) -> DocumentPlacement:
        """Place a document in a specific time period."""
        
    def get_documents_for_period(self, period_id: str) -> List[DocumentPlacement]:
        """Get all documents in a time period."""
        
    def analyze_progression(self, topic: str) -> ProgressionAnalysis:
        """Analyze progression of work on a topic."""
        
    def detect_gaps(self) -> List[Gap]:
        """Detect documentation gaps across timeline."""
        
    def detect_drift(self, entity_type: str) -> List[DriftEvent]:
        """Detect API/contract drift across timeline."""
```

### Time Period Entity

```python
@dataclass
class TimePeriod:
    """Represents a discrete time period in the timeline."""
    
    id: str
    timeline_id: str
    name: str  # e.g., "Sprint 1", "v1.0 to v1.1", "Q1 2025"
    description: str
    temporal_range: TemporalRange
    documents: List[DocumentPlacement] = field(default_factory=list)
    
    # Git-based periods
    start_commit: Optional[str] = None
    end_commit: Optional[str] = None
    
    # Metrics
    document_count: int = 0
    code_changes: int = 0
    avg_document_quality: float = 0.0
    
    # Status
    is_active: bool = False
    status: str = "planned"  # planned, active, completed
```

### Document Placement Entity

```python
@dataclass
class DocumentPlacement:
    """Associates a document with a specific time period."""
    
    id: str
    document_id: str
    period_id: str
    timeline_id: str
    
    # Placement metadata
    placed_at: datetime
    placement_method: str  # git_commit, timestamp, manual, ai_inference
    relevance_score: float  # 0.0 to 1.0
    confidence_score: float  # 0.0 to 1.0
    
    # Temporal attributes from document
    commit_sha: Optional[str] = None
    commit_date: Optional[datetime] = None
    file_modified_date: Optional[datetime] = None
    content_date: Optional[datetime] = None  # Extracted from content
    
    # Analysis metadata
    topics: List[str] = field(default_factory=list)
    entities_mentioned: List[str] = field(default_factory=list)  # APIs, models, etc.
    change_type: Optional[str] = None  # create, update, delete, refactor
```

### Value Objects

```python
@dataclass(frozen=True)
class TemporalRange:
    """Value object representing a time range."""
    start_time: datetime
    end_time: datetime
    
    def duration_days(self) -> int:
        return (self.end_time - self.start_time).days
    
    def overlaps_with(self, other: 'TemporalRange') -> bool:
        return self.start_time <= other.end_time and other.start_time <= self.end_time
    
    def contains(self, timestamp: datetime) -> bool:
        return self.start_time <= timestamp <= self.end_time

@dataclass(frozen=True)
class PlacementScore:
    """Score for document placement relevance."""
    temporal_match: float  # How well timestamp matches period
    content_relevance: float  # Content relevance to period
    semantic_similarity: float  # Similarity to other period documents
    overall_score: float
    
    @classmethod
    def calculate(cls, temporal: float, content: float, semantic: float) -> 'PlacementScore':
        overall = (temporal * 0.4) + (content * 0.3) + (semantic * 0.3)
        return cls(temporal, content, semantic, overall)

@dataclass(frozen=True)
class DriftMetrics:
    """Metrics for API/data contract drift."""
    breaking_changes: int
    additions: int
    deprecations: int
    modifications: int
    drift_severity: float  # 0.0 (no drift) to 1.0 (severe drift)
    
    def is_breaking(self) -> bool:
        return self.breaking_changes > 0 or self.drift_severity > 0.7
```

---

## Implementation Phases

### Phase 1: Core Timeline Infrastructure (Week 1)

#### 1.1 Domain Layer
- [ ] Create timeline domain models (Timeline, TimePeriod, DocumentPlacement)
- [ ] Define value objects (TemporalRange, PlacementScore, DriftMetrics)
- [ ] Define domain events (TimelineCreated, DocumentPlaced, PeriodCompleted)
- [ ] Create repository interfaces

**Files to Create:**
- `src/services/timeline/domain/entities/timeline.py`
- `src/services/timeline/domain/entities/time_period.py`
- `src/services/timeline/domain/entities/document_placement.py`
- `src/services/timeline/domain/value_objects/temporal_range.py`
- `src/services/timeline/domain/value_objects/placement_score.py`
- `src/services/timeline/domain/events.py`
- `src/services/timeline/domain/repositories.py`

#### 1.2 Database Schema
- [ ] Create timeline tables (timelines, time_periods, document_placements)
- [ ] Add indexes for temporal queries
- [ ] Create migration scripts

**Migration: `src/storage/migrations/010_add_timeline_tables.py`**

#### 1.3 Infrastructure Layer
- [ ] Implement PostgreSQL repository
- [ ] Add timeline caching (Redis)
- [ ] Create basic CRUD operations

**Files to Create:**
- `src/services/timeline/infrastructure/repositories/timeline_repository.py`

#### 1.4 Application Layer & API
- [ ] Create TimelineManager service
- [ ] Create DocumentPlacer service
- [ ] Add REST API endpoints for timeline CRUD

**Files to Create:**
- `src/services/timeline/application/services/timeline_manager.py`
- `src/services/timeline/application/services/document_placer.py`
- `src/api/routes/timeline.py`

**API Endpoints:**
```
POST   /api/v1/timelines                    # Create timeline
GET    /api/v1/timelines                    # List timelines
GET    /api/v1/timelines/{id}               # Get timeline details
PUT    /api/v1/timelines/{id}               # Update timeline
DELETE /api/v1/timelines/{id}               # Delete timeline
POST   /api/v1/timelines/{id}/periods       # Add period
POST   /api/v1/timelines/{id}/place-documents  # Place documents on timeline
```

---

### Phase 2: Document Placement & Temporal Analysis (Week 2)

#### 2.1 Document Placement Logic
- [ ] Git-based placement (using commit history)
- [ ] Timestamp-based placement (file modification times)
- [ ] Content-based placement (AI-inferred temporal markers)
- [ ] Relevance scoring algorithm

**Files to Create:**
- `src/services/timeline/application/services/placement_strategies.py`
- `src/services/timeline/infrastructure/analyzers/temporal_analyzer.py`

#### 2.2 Temporal Analysis
- [ ] Progression analysis (track evolution of topics/features)
- [ ] Velocity metrics (documents per period)
- [ ] Activity heatmaps (hot periods, cold periods)
- [ ] Trend detection

**Files to Create:**
- `src/services/timeline/application/services/temporal_analyzer.py`
- `src/services/timeline/infrastructure/analyzers/progression_analyzer.py`

#### 2.3 RAG Integration for Temporal Queries
- [ ] Time-scoped RAG queries ("What changed in Q1 2025?")
- [ ] Temporal context enhancement
- [ ] Period-specific document retrieval

**Files to Update:**
- `src/services/rag/temporal_rag_service.py` (new)
- `src/api/routes/query.py` (add temporal parameters)

**API Endpoints:**
```
GET    /api/v1/timelines/{id}/analysis/progression      # Progression analysis
GET    /api/v1/timelines/{id}/analysis/velocity         # Document velocity
POST   /api/v1/timelines/{id}/query                     # Temporal RAG query
GET    /api/v1/timelines/{id}/periods/{period_id}/documents  # Period documents
```

---

### Phase 3: Gap Analysis & Detection (Week 3)

#### 3.1 Gap Detection
- [ ] Coverage gap detection (periods with insufficient docs)
- [ ] Topic gap detection (missing documentation on topics)
- [ ] Continuity gap detection (breaks in documentation flow)
- [ ] Quality gap detection (periods with low-quality docs)

**Files to Create:**
- `src/services/timeline/application/services/gap_analyzer.py`
- `src/services/timeline/infrastructure/analyzers/gap_pattern_detector.py`

#### 3.2 Root Cause Analysis
- [ ] Correlation with Git activity (low commit = low docs?)
- [ ] Team velocity analysis
- [ ] External event correlation (holidays, deadlines, etc.)

**Files to Create:**
- `src/services/timeline/infrastructure/analyzers/root_cause_analyzer.py`

#### 3.3 Gap Report Generation
- [ ] Gap identification report
- [ ] Recommendations for filling gaps
- [ ] Impact assessment

**Files to Create:**
- `src/services/timeline/infrastructure/generators/gap_report_generator.py`

**API Endpoints:**
```
POST   /api/v1/timelines/{id}/analyze/gaps              # Detect gaps
GET    /api/v1/timelines/{id}/gaps/{gap_id}             # Gap details
POST   /api/v1/timelines/{id}/reports/gap-analysis      # Generate gap report
```

---

### Phase 4: API/Contract Drift Detection (Week 4)

#### 4.1 Schema Extraction & Tracking
- [ ] Extract API schemas from documents (OpenAPI, GraphQL, etc.)
- [ ] Extract data model schemas (database schemas, Pydantic models)
- [ ] Track schema versions across timeline
- [ ] Build schema evolution graph

**Files to Create:**
- `src/services/timeline/infrastructure/analyzers/schema_extractor.py`
- `src/services/timeline/infrastructure/analyzers/schema_drift_analyzer.py`

#### 4.2 Drift Detection
- [ ] Breaking change detection
- [ ] Addition detection (new fields, endpoints)
- [ ] Deprecation detection
- [ ] Modification detection (field type changes, etc.)
- [ ] Severity scoring

**Files to Create:**
- `src/services/timeline/application/services/drift_detector.py`

#### 4.3 Impact Analysis
- [ ] Downstream impact assessment
- [ ] Migration path suggestions
- [ ] Backward compatibility analysis

**Files to Create:**
- `src/services/timeline/infrastructure/analyzers/drift_impact_analyzer.py`

#### 4.4 Drift Report Generation
- [ ] Drift detection report with timeline
- [ ] Breaking change summary
- [ ] Migration recommendations

**Files to Create:**
- `src/services/timeline/infrastructure/generators/drift_report_generator.py`

**API Endpoints:**
```
POST   /api/v1/timelines/{id}/analyze/drift             # Detect drift
GET    /api/v1/timelines/{id}/drift/schemas             # Schema evolution
GET    /api/v1/timelines/{id}/drift/breaking-changes    # Breaking changes
POST   /api/v1/timelines/{id}/reports/drift-analysis    # Generate drift report
```

---

### Phase 5: Document Consolidation Intelligence (Week 5)

#### 5.1 Redundancy Detection
- [ ] Duplicate content detection across timeline
- [ ] Semantic similarity analysis
- [ ] Version clustering (group related versions)

**Files to Create:**
- `src/services/timeline/application/services/consolidation_analyzer.py`
- `src/services/timeline/infrastructure/analyzers/redundancy_detector.py`

#### 5.2 Merge Recommendations
- [ ] Identify consolidation opportunities
- [ ] Generate merge strategies
- [ ] Preserve historical context

**Files to Create:**
- `src/services/timeline/infrastructure/generators/consolidation_recommendations.py`

**API Endpoints:**
```
POST   /api/v1/timelines/{id}/analyze/redundancy        # Detect redundancy
POST   /api/v1/timelines/{id}/consolidate/recommend     # Consolidation recommendations
POST   /api/v1/timelines/{id}/reports/consolidation     # Consolidation report
```

---

### Phase 6: Report Generation & Citations (Week 6)

#### 6.1 Report Infrastructure
- [ ] Report template system
- [ ] Citation management (link to source documents)
- [ ] Evidence collection and formatting
- [ ] Export formats (Markdown, PDF, JSON)

**Files to Create:**
- `src/services/timeline/infrastructure/generators/report_generator_base.py`
- `src/services/timeline/infrastructure/generators/citation_manager.py`

#### 6.2 Progression Reports
- [ ] Topic evolution reports
- [ ] Feature development timeline
- [ ] Documentation maturity progression

**Files to Create:**
- `src/services/timeline/infrastructure/generators/progression_report_generator.py`

#### 6.3 Comprehensive Analysis Reports
- [ ] Multi-aspect analysis (progression + gaps + drift)
- [ ] Executive summary generation
- [ ] Actionable recommendations

**Files to Create:**
- `src/services/timeline/infrastructure/generators/comprehensive_report_generator.py`

**API Endpoints:**
```
POST   /api/v1/timelines/{id}/reports/progression       # Generate progression report
POST   /api/v1/timelines/{id}/reports/comprehensive     # Comprehensive analysis report
GET    /api/v1/timelines/{id}/reports/{report_id}       # Get report
GET    /api/v1/timelines/{id}/reports/{report_id}/export # Export report (format param)
```

---

### Phase 7: Dashboard Integration & UX (Week 7)

#### 7.1 Dashboard Views
- [ ] Timeline visualization (Gantt-like view)
- [ ] Period detail views
- [ ] Document placement visualization
- [ ] Gap and drift visualization

**Files to Create (in ecosystem-mcp-dashboard):**
- `services/ecosystem-mcp-dashboard/pages/timeline_analysis.py`
- `services/ecosystem-mcp-dashboard/components/timeline_visualizer.py`

#### 7.2 Interactive Analysis
- [ ] Drill-down from timeline to documents
- [ ] Filter by time periods
- [ ] Search within temporal context
- [ ] Export visualizations

---

## API Endpoints

### Complete API Summary

```
# Timeline Management
POST   /api/v1/timelines                              # Create timeline
GET    /api/v1/timelines                              # List timelines
GET    /api/v1/timelines/{id}                         # Get timeline
PUT    /api/v1/timelines/{id}                         # Update timeline
DELETE /api/v1/timelines/{id}                         # Delete timeline

# Period Management
POST   /api/v1/timelines/{id}/periods                 # Add period
GET    /api/v1/timelines/{id}/periods                 # List periods
PUT    /api/v1/timelines/{id}/periods/{period_id}     # Update period
DELETE /api/v1/timelines/{id}/periods/{period_id}     # Delete period

# Document Placement
POST   /api/v1/timelines/{id}/place-documents         # Place documents
GET    /api/v1/timelines/{id}/placements              # Get all placements
GET    /api/v1/timelines/{id}/periods/{period_id}/documents  # Period docs
DELETE /api/v1/timelines/{id}/placements/{placement_id}  # Remove placement

# Temporal Analysis
GET    /api/v1/timelines/{id}/analysis/progression    # Progression analysis
GET    /api/v1/timelines/{id}/analysis/velocity       # Document velocity
GET    /api/v1/timelines/{id}/analysis/heatmap        # Activity heatmap
POST   /api/v1/timelines/{id}/query                   # Temporal RAG query

# Gap Analysis
POST   /api/v1/timelines/{id}/analyze/gaps            # Detect gaps
GET    /api/v1/timelines/{id}/gaps                    # List gaps
GET    /api/v1/timelines/{id}/gaps/{gap_id}           # Gap details
POST   /api/v1/timelines/{id}/gaps/{gap_id}/resolve   # Mark gap as resolved

# Drift Detection
POST   /api/v1/timelines/{id}/analyze/drift           # Detect drift
GET    /api/v1/timelines/{id}/drift/events            # Drift events
GET    /api/v1/timelines/{id}/drift/schemas           # Schema evolution
GET    /api/v1/timelines/{id}/drift/breaking-changes  # Breaking changes

# Consolidation
POST   /api/v1/timelines/{id}/analyze/redundancy      # Detect redundancy
POST   /api/v1/timelines/{id}/consolidate/recommend   # Get recommendations
POST   /api/v1/timelines/{id}/consolidate/execute     # Execute consolidation

# Reports
POST   /api/v1/timelines/{id}/reports/progression     # Progression report
POST   /api/v1/timelines/{id}/reports/gap-analysis    # Gap analysis report
POST   /api/v1/timelines/{id}/reports/drift-analysis  # Drift analysis report
POST   /api/v1/timelines/{id}/reports/consolidation   # Consolidation report
POST   /api/v1/timelines/{id}/reports/comprehensive   # Comprehensive report
GET    /api/v1/timelines/{id}/reports                 # List reports
GET    /api/v1/timelines/{id}/reports/{report_id}     # Get report
GET    /api/v1/timelines/{id}/reports/{report_id}/export  # Export (MD/PDF/JSON)
```

---

## Database Schema

### PostgreSQL Tables

```sql
-- Timelines
CREATE TABLE timelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_id VARCHAR(255),  -- Links to repository context
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    period_type VARCHAR(50) DEFAULT 'git_based',  -- git_based, date_based, phase_based
    auto_update BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT timelines_valid_range CHECK (start_time < end_time)
);

CREATE INDEX idx_timelines_repository ON timelines(repository_id);
CREATE INDEX idx_timelines_dates ON timelines(start_time, end_time);

-- Time Periods
CREATE TABLE time_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    start_commit VARCHAR(64),  -- Git commit SHA
    end_commit VARCHAR(64),    -- Git commit SHA
    status VARCHAR(50) DEFAULT 'planned',  -- planned, active, completed
    is_active BOOLEAN DEFAULT FALSE,
    document_count INTEGER DEFAULT 0,
    code_changes INTEGER DEFAULT 0,
    avg_document_quality FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT time_periods_valid_range CHECK (start_time < end_time),
    CONSTRAINT time_periods_valid_status CHECK (status IN ('planned', 'active', 'completed'))
);

CREATE INDEX idx_time_periods_timeline ON time_periods(timeline_id);
CREATE INDEX idx_time_periods_dates ON time_periods(start_time, end_time);
CREATE INDEX idx_time_periods_commits ON time_periods(start_commit, end_commit);
CREATE INDEX idx_time_periods_status ON time_periods(status);

-- Document Placements
CREATE TABLE document_placements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES time_periods(id) ON DELETE CASCADE,
    timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    
    placed_at TIMESTAMP DEFAULT NOW(),
    placement_method VARCHAR(50) NOT NULL,  -- git_commit, timestamp, manual, ai_inference
    relevance_score FLOAT DEFAULT 0.0,
    confidence_score FLOAT DEFAULT 0.0,
    
    -- Temporal attributes
    commit_sha VARCHAR(64),
    commit_date TIMESTAMP,
    file_modified_date TIMESTAMP,
    content_date TIMESTAMP,
    
    -- Analysis metadata
    topics TEXT[],  -- Array of topic strings
    entities_mentioned TEXT[],  -- APIs, models, etc.
    change_type VARCHAR(50),  -- create, update, delete, refactor
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT document_placements_valid_scores CHECK (
        relevance_score >= 0.0 AND relevance_score <= 1.0 AND
        confidence_score >= 0.0 AND confidence_score <= 1.0
    ),
    CONSTRAINT document_placements_unique_doc_period UNIQUE (document_id, period_id)
);

CREATE INDEX idx_document_placements_document ON document_placements(document_id);
CREATE INDEX idx_document_placements_period ON document_placements(period_id);
CREATE INDEX idx_document_placements_timeline ON document_placements(timeline_id);
CREATE INDEX idx_document_placements_commit ON document_placements(commit_sha);
CREATE INDEX idx_document_placements_scores ON document_placements(relevance_score, confidence_score);
CREATE INDEX idx_document_placements_topics ON document_placements USING GIN(topics);
CREATE INDEX idx_document_placements_entities ON document_placements USING GIN(entities_mentioned);

-- Gap Analysis Results
CREATE TABLE timeline_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    gap_type VARCHAR(50) NOT NULL,  -- coverage, topic, continuity, quality
    severity VARCHAR(50) DEFAULT 'medium',  -- low, medium, high, critical
    
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    affected_periods UUID[],  -- Array of period IDs
    
    description TEXT NOT NULL,
    root_causes JSONB,  -- Structured root cause data
    impact_assessment TEXT,
    recommendations TEXT[],
    
    status VARCHAR(50) DEFAULT 'identified',  -- identified, acknowledged, resolved, false_positive
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT timeline_gaps_valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT timeline_gaps_valid_status CHECK (status IN ('identified', 'acknowledged', 'resolved', 'false_positive'))
);

CREATE INDEX idx_timeline_gaps_timeline ON timeline_gaps(timeline_id);
CREATE INDEX idx_timeline_gaps_type ON timeline_gaps(gap_type);
CREATE INDEX idx_timeline_gaps_severity ON timeline_gaps(severity);
CREATE INDEX idx_timeline_gaps_status ON timeline_gaps(status);
CREATE INDEX idx_timeline_gaps_dates ON timeline_gaps(start_time, end_time);

-- Drift Events
CREATE TABLE drift_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    period_id UUID REFERENCES time_periods(id) ON DELETE SET NULL,
    
    drift_type VARCHAR(50) NOT NULL,  -- api, data_model, schema, contract
    change_category VARCHAR(50) NOT NULL,  -- breaking, addition, deprecation, modification
    severity FLOAT NOT NULL,  -- 0.0 to 1.0
    
    entity_name VARCHAR(255) NOT NULL,  -- API name, model name, etc.
    entity_type VARCHAR(50) NOT NULL,  -- endpoint, field, table, model
    
    before_state JSONB,  -- Schema/state before change
    after_state JSONB,   -- Schema/state after change
    
    detected_at TIMESTAMP DEFAULT NOW(),
    occurred_at TIMESTAMP,  -- When the actual change occurred
    
    source_document_ids UUID[],  -- Documents that evidenced the drift
    commit_shas VARCHAR(64)[],   -- Git commits related to drift
    
    description TEXT NOT NULL,
    impact_analysis TEXT,
    migration_suggestions TEXT[],
    
    is_breaking BOOLEAN DEFAULT FALSE,
    requires_attention BOOLEAN DEFAULT TRUE,
    acknowledged_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT drift_events_valid_severity CHECK (severity >= 0.0 AND severity <= 1.0)
);

CREATE INDEX idx_drift_events_timeline ON drift_events(timeline_id);
CREATE INDEX idx_drift_events_period ON drift_events(period_id);
CREATE INDEX idx_drift_events_type ON drift_events(drift_type);
CREATE INDEX idx_drift_events_category ON drift_events(change_category);
CREATE INDEX idx_drift_events_entity ON drift_events(entity_name, entity_type);
CREATE INDEX idx_drift_events_breaking ON drift_events(is_breaking);
CREATE INDEX idx_drift_events_attention ON drift_events(requires_attention);

-- Timeline Reports
CREATE TABLE timeline_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    
    report_type VARCHAR(50) NOT NULL,  -- progression, gap_analysis, drift_analysis, consolidation, comprehensive
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    content JSONB NOT NULL,  -- Full report content in structured format
    markdown_content TEXT,   -- Markdown version for easy viewing
    
    citations JSONB,  -- Array of {document_id, excerpt, line_number, url}
    metadata JSONB,   -- Additional report metadata
    
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Optional expiration for cleanup
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_timeline_reports_timeline ON timeline_reports(timeline_id);
CREATE INDEX idx_timeline_reports_type ON timeline_reports(report_type);
CREATE INDEX idx_timeline_reports_generated ON timeline_reports(generated_at);
```

---

## Integration Points

### 1. Git Service Integration
**Purpose**: Extract commit history for timeline construction  
**Usage**: Auto-create periods from Git commits, associate documents with commits

```python
from src.services.git.git_service import GitService

git_service = GitService()
commits = await git_service.get_commit_history(repo_path, start_date, end_date)
for commit in commits:
    period = create_period_from_commit(commit)
    timeline.add_period(period)
```

### 2. Document Store Integration
**Purpose**: Retrieve documents for placement and analysis  
**Usage**: Fetch documents by various criteria (commit, date range, topic)

```python
from src.storage.repositories.document_repository import DocumentRepository

doc_repo = DocumentRepository()
documents = await doc_repo.get_documents_by_date_range(start_date, end_date)
documents_by_commit = await doc_repo.get_documents_by_commit(commit_sha)
```

### 3. RAG Service Integration
**Purpose**: Enable temporal RAG queries and semantic analysis  
**Usage**: Query documents within specific time periods, detect topics

```python
from src.services.rag.rag_service import RAGService

rag_service = RAGService()
# Temporal query: "What changed in API between v1.0 and v2.0?"
result = await rag_service.query_temporal(
    query="API changes",
    timeline_id=timeline_id,
    start_period="v1.0",
    end_period="v2.0"
)
```

### 4. Embedding Service Integration
**Purpose**: Calculate semantic similarity for document clustering  
**Usage**: Group related documents, detect redundancy

```python
from src.services.embeddings.embedding_service import EmbeddingService

embedding_service = EmbeddingService()
embeddings = await embedding_service.get_document_embeddings(document_ids)
similarity_matrix = calculate_similarity_matrix(embeddings)
clusters = cluster_by_similarity(similarity_matrix, threshold=0.85)
```

### 5. Analysis Service Integration
**Purpose**: Extract structured data (APIs, models) for drift detection  
**Usage**: Parse code, extract schemas, build dependency graphs

```python
from src.services.analysis.analysis_engine import AnalysisEngine

analysis_engine = AnalysisEngine()
analysis = await analysis_engine.analyze_repository(repo_path)
api_endpoints = analysis.api_endpoints
data_models = analysis.data_models
```

### 6. LLM Service Integration
**Purpose**: Generate summaries, detect changes, explain drift  
**Usage**: Summarize progression, explain why changes occurred

```python
from src.services.llm.llm_service import LLMService

llm_service = LLMService()
summary = await llm_service.generate(
    prompt=f"Summarize the progression of {topic} from {start} to {end}",
    context=relevant_documents
)
```

---

## Usage Examples

### Example 1: Create Timeline from Git History

```python
# Create timeline for a repository
POST /api/v1/timelines
{
    "name": "Ecosystem MCP Development Timeline",
    "description": "Timeline of ecosystem-mcp development from inception",
    "repository_id": "ecosystem-mcp",
    "period_type": "git_based",
    "auto_update": true,
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2025-01-31T23:59:59Z"
}

# Response
{
    "success": true,
    "data": {
        "timeline_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Ecosystem MCP Development Timeline",
        "periods_created": 12,  # Auto-created from Git tags/releases
        "documents_placed": 1523
    }
}
```

### Example 2: Analyze Progression of a Feature

```python
# Query: "How did the RAG service evolve over time?"
GET /api/v1/timelines/{timeline_id}/analysis/progression?topic=rag_service

# Response
{
    "success": true,
    "data": {
        "topic": "rag_service",
        "timeline_coverage": "2024-03-15 to 2025-01-20",
        "total_documents": 47,
        "phases": [
            {
                "phase": "Initial Implementation",
                "period": "v0.1 to v0.5",
                "date_range": "2024-03-15 to 2024-06-20",
                "documents": 8,
                "key_changes": [
                    "Basic RAG pipeline created",
                    "ChromaDB integration",
                    "Simple vector search"
                ],
                "citations": [
                    {
                        "document_id": "doc-123",
                        "title": "RAG Service Initial Design",
                        "excerpt": "We're implementing a basic RAG pipeline using ChromaDB...",
                        "url": "/documents/doc-123"
                    }
                ]
            },
            {
                "phase": "Context-Aware RAG",
                "period": "v0.6 to v1.0",
                "date_range": "2024-06-21 to 2024-10-15",
                "documents": 15,
                "key_changes": [
                    "Context filtering added",
                    "Hierarchical contexts implemented",
                    "Performance optimization"
                ],
                "citations": [...]
            },
            {
                "phase": "Multi-Model Integration",
                "period": "v1.1 to v2.0",
                "date_range": "2024-10-16 to 2025-01-20",
                "documents": 24,
                "key_changes": [
                    "Model router integration",
                    "Dynamic model selection",
                    "Query optimization",
                    "Temporal RAG queries added"
                ],
                "citations": [...]
            }
        ],
        "summary": "The RAG service evolved from a basic vector search implementation to a sophisticated multi-model, context-aware system over 10 months. Key milestones include hierarchical context support (v0.8) and model router integration (v1.5).",
        "report_id": "report-456"
    }
}
```

### Example 3: Detect API Drift

```python
# Analyze API drift across timeline
POST /api/v1/timelines/{timeline_id}/analyze/drift
{
    "drift_type": "api",
    "entity_filter": "*/api/v1/documents/*"
}

# Response
{
    "success": true,
    "data": {
        "drift_events": [
            {
                "id": "drift-789",
                "entity_name": "/api/v1/documents",
                "entity_type": "endpoint",
                "change_category": "breaking",
                "severity": 0.9,
                "occurred_at": "2024-08-15T10:30:00Z",
                "period": "v0.8 to v0.9",
                "description": "Response schema changed: field 'metadata' type changed from Object to JSONB",
                "before_state": {
                    "response": {
                        "metadata": {"type": "object"}
                    }
                },
                "after_state": {
                    "response": {
                        "metadata": {"type": "jsonb"}
                    }
                },
                "impact_analysis": "High impact: All clients parsing metadata as plain object will break",
                "migration_suggestions": [
                    "Update client libraries to handle JSONB format",
                    "Add version header to maintain backward compatibility",
                    "Provide migration guide for existing clients"
                ],
                "source_documents": ["doc-334", "doc-335"],
                "citations": [
                    {
                        "document_id": "doc-334",
                        "title": "API Schema Update v0.9",
                        "excerpt": "Changed metadata field to JSONB for better query support...",
                        "commit_sha": "a1b2c3d4"
                    }
                ]
            }
        ],
        "summary": {
            "total_drift_events": 12,
            "breaking_changes": 3,
            "additions": 5,
            "deprecations": 2,
            "modifications": 2,
            "overall_drift_severity": 0.65
        },
        "report_id": "report-drift-123"
    }
}
```

### Example 4: Gap Analysis

```python
# Detect documentation gaps
POST /api/v1/timelines/{timeline_id}/analyze/gaps

# Response
{
    "success": true,
    "data": {
        "gaps": [
            {
                "id": "gap-101",
                "gap_type": "coverage",
                "severity": "high",
                "time_range": "2024-07-01 to 2024-07-31",
                "affected_periods": ["period-july"],
                "description": "Only 3 documents created in July 2024 compared to average of 45/month",
                "root_causes": {
                    "low_commit_activity": true,
                    "team_changes": "2 team members on leave",
                    "external_factors": "Major infrastructure migration in progress"
                },
                "impact_assessment": "Documentation severely lagging behind code changes. 23 PRs merged without documentation updates.",
                "recommendations": [
                    "Conduct documentation sprint to cover July changes",
                    "Establish documentation requirements for PRs",
                    "Add post-migration documentation tasks"
                ]
            },
            {
                "id": "gap-102",
                "gap_type": "topic",
                "severity": "medium",
                "description": "No documentation on embedding service migration from Ollama to FastEmbed",
                "affected_periods": ["v1.2-to-v1.3"],
                "time_range": "2024-09-10 to 2024-09-25",
                "recommendations": [
                    "Document migration rationale and process",
                    "Create comparison guide: Ollama vs FastEmbed",
                    "Add performance benchmarks"
                ]
            }
        ],
        "summary": {
            "total_gaps": 8,
            "critical": 0,
            "high": 2,
            "medium": 4,
            "low": 2,
            "coverage_score": 0.73  # 73% of expected documentation coverage
        },
        "report_id": "report-gaps-456"
    }
}
```

### Example 5: Document Consolidation

```python
# Analyze redundancy and get consolidation recommendations
POST /api/v1/timelines/{timeline_id}/analyze/redundancy

# Response
{
    "success": true,
    "data": {
        "redundant_document_groups": [
            {
                "group_id": "redundancy-group-1",
                "topic": "API Authentication",
                "documents": [
                    {
                        "id": "doc-111",
                        "title": "API Auth Guide",
                        "created": "2024-02-10",
                        "similarity_score": 0.95
                    },
                    {
                        "id": "doc-112",
                        "title": "Authentication Documentation",
                        "created": "2024-05-15",
                        "similarity_score": 0.94
                    },
                    {
                        "id": "doc-113",
                        "title": "API Security & Auth",
                        "created": "2024-08-20",
                        "similarity_score": 0.92
                    }
                ],
                "recommendation": {
                    "action": "consolidate",
                    "keep_document": "doc-113",  # Most recent and comprehensive
                    "merge_from": ["doc-111", "doc-112"],
                    "rationale": "doc-113 contains all content from earlier versions plus updated OAuth2 info",
                    "preserve_history": true,
                    "suggested_title": "API Authentication and Security Guide",
                    "missing_content": [
                        "Legacy OAuth 1.0 examples from doc-111 (may still be needed)"
                    ]
                }
            }
        ],
        "statistics": {
            "total_documents_analyzed": 523,
            "redundant_documents": 47,
            "potential_merges": 12,
            "estimated_consolidation_benefit": "18% reduction in document count, improved findability"
        },
        "report_id": "report-consolidation-789"
    }
}
```

---

## Testing Strategy

### Unit Tests

**Domain Logic:**
- [ ] Timeline entity tests (add period, placement logic)
- [ ] Time period entity tests (overlap detection, status transitions)
- [ ] Value object tests (TemporalRange, PlacementScore, DriftMetrics)
- [ ] Placement algorithm tests (scoring, relevance calculation)

**Files:**
- `tests/unit/test_timeline_entity.py`
- `tests/unit/test_time_period.py`
- `tests/unit/test_value_objects.py`
- `tests/unit/test_placement_algorithms.py`

### Integration Tests

**Database:**
- [ ] Timeline repository tests (CRUD operations)
- [ ] Complex queries (temporal range queries, period overlaps)
- [ ] Transaction handling (atomic period creation)

**Service Integration:**
- [ ] Git service integration (commit history extraction)
- [ ] RAG service integration (temporal queries)
- [ ] Analysis service integration (schema extraction)

**Files:**
- `tests/integration/test_timeline_repository.py`
- `tests/integration/test_git_timeline_integration.py`
- `tests/integration/test_temporal_rag.py`

### Functional Tests

**End-to-End Workflows:**
- [ ] Create timeline from Git history → place documents → analyze progression
- [ ] Detect gaps → generate gap report → verify citations
- [ ] Detect API drift → analyze impact → generate migration recommendations
- [ ] Find redundant documents → recommend consolidation → execute merge

**Files:**
- `tests/functional/test_timeline_e2e.py`
- `tests/functional/test_gap_analysis_workflow.py`
- `tests/functional/test_drift_detection_workflow.py`

### Smoke Tests

**API Endpoints:**
- [ ] All timeline CRUD endpoints
- [ ] Document placement endpoint
- [ ] Analysis endpoints (progression, gaps, drift)
- [ ] Report generation endpoints

**File:**
- `tests/smoke/test_timeline_api_smoke.py`

### Performance Tests

**Load Testing:**
- [ ] Place 10,000+ documents on timeline
- [ ] Query across 100+ time periods
- [ ] Generate comprehensive report for 1000+ documents
- [ ] Detect drift across 50+ API versions

**File:**
- `tests/performance/test_timeline_performance.py`

---

## Next Steps

1. **Review & Approval**
   - Review this plan with stakeholders
   - Prioritize features if needed
   - Allocate resources

2. **Phase 1 Implementation**
   - Start with core timeline infrastructure
   - Set up database schema
   - Implement basic CRUD operations

3. **Iterative Development**
   - Complete one phase at a time
   - Test thoroughly at each phase
   - Gather feedback and adjust

4. **Documentation**
   - API documentation (OpenAPI/Swagger)
   - User guides with examples
   - Architecture decision records

5. **Deployment**
   - Gradual rollout to users
   - Monitor performance and usage
   - Iterate based on feedback

---

## Conclusion

This timeline-based document analysis infrastructure will enable powerful temporal analysis capabilities in `ecosystem-mcp`. By leveraging existing services (Git, RAG, Analysis, Embeddings) and following DDD principles inspired by `project-simulation`, we can provide users with comprehensive insights into:

- **How work progressed** over time on any topic
- **Where gaps exist** in documentation and why
- **When and why** APIs and contracts drifted
- **Which documents** should be consolidated
- **What changed** between any two points in time

All analysis will be backed by proper citations to source documents, making reports trustworthy and actionable.

**Estimated Timeline:** 7 weeks for full implementation  
**Estimated Effort:** 1-2 engineers, full-time  
**Dependencies:** Existing ecosystem-mcp infrastructure (Git, PostgreSQL, ChromaDB, RAG, Embeddings, LLM)

---

**Document Version:** 1.0  
**Last Updated:** {{ current_date }}  
**Author:** AI Assistant (based on user requirements and project-simulation analysis)

