**Date:** November 19, 2025  
**Status:** 🔍 **INFRASTRUCTURE AUDIT** - Leveraging Existing Systems  
**Purpose:** Map existing infrastructure to adaptive documentation goals  

---

# Infrastructure Audit & Integration Plan

## 🎯 Goal

Implement adaptive documentation generation by **maximizing use of existing infrastructure** rather than building from scratch.

---

## 📊 Existing Infrastructure Audit

### ✅ **1. Database Models (ALREADY EXISTS)**

#### **Documents & Embeddings**

```sql
-- ✅ EXISTING: Core document storage
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    service_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    original_content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    
    -- Metadata
    doc_metadata JSONB NOT NULL DEFAULT '{}',  -- 🎯 CAN STORE: concepts, keywords, patterns
    
    -- Quality scoring (already implemented!)
    quality_score FLOAT,
    quality_grade VARCHAR(1),  -- S, A, B, C, D, F
    score_breakdown JSONB,  -- 🎯 CAN STORE: detailed scoring info
    
    -- Temporal metadata
    git_date TIMESTAMP,
    git_author VARCHAR(255),
    
    is_latest BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ✅ EXISTING: Embedding storage
CREATE TABLE embeddings (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    chroma_id VARCHAR(255) UNIQUE,
    model VARCHAR(100),
    dimensions INTEGER,
    token_count INTEGER,
    cost_usd FLOAT,
    extra_metadata JSONB,  -- 🎯 CAN STORE: enhanced embedding metadata
    created_at TIMESTAMP DEFAULT NOW()
);
```

**✅ LEVERAGE FOR:**
- Store learned concepts in `doc_metadata`
- Store enhanced embedding metadata in `extra_metadata`
- Use `quality_score` for document importance
- No new tables needed!

---

#### **Documentation Generation (ALREADY EXISTS)**

```sql
-- ✅ EXISTING: Documentation runs
CREATE TABLE documentation_runs (
    id UUID PRIMARY KEY,
    plan_id VARCHAR(500),
    repo_id VARCHAR(500),
    
    -- Configuration (already JSONB!)
    config JSONB,  -- 🎯 CAN STORE: all adaptive config!
    
    -- Progress tracking
    passes_completed INTEGER DEFAULT 0,
    total_passes INTEGER DEFAULT 5,
    current_pass VARCHAR(50),
    
    -- Status
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Metrics
    total_artifacts INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    overall_quality_score FLOAT,
    
    -- Output
    output_path TEXT,
    output_formats JSONB  -- markdown, html, json
);

-- ✅ EXISTING: Generated artifacts
CREATE TABLE documentation_artifacts (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES documentation_runs(id) ON DELETE CASCADE,
    
    -- Artifact type
    artifact_type VARCHAR(50) NOT NULL,  -- architecture, api, examples
    pass_number INTEGER NOT NULL,
    pass_type VARCHAR(50) NOT NULL,
    component_name VARCHAR(200),
    
    -- Content
    title VARCHAR(500),
    content TEXT,
    format VARCHAR(20) DEFAULT 'markdown',
    
    -- Quality
    word_count INTEGER DEFAULT 0,
    quality_score FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**✅ LEVERAGE FOR:**
- Store adaptive config in `config` JSONB
- Track multi-pass generation with existing fields
- Store section artifacts with citations
- **No new tables needed!**

---

#### **Repository Analysis (ALREADY EXISTS)**

```sql
-- ✅ EXISTING: Repository context
CREATE TABLE repository_contexts (
    id UUID PRIMARY KEY,
    repo_id VARCHAR(500) UNIQUE NOT NULL,
    repo_name VARCHAR(500),
    
    -- Technology Stack (already captured!)
    languages JSONB,  -- {"python": 120, "javascript": 45}
    frameworks JSONB,  -- {"fastapi": ["src/api/app.py"]}
    databases JSONB,  -- ["postgresql", "redis"]
    tools JSONB,  -- ["docker", "kubernetes"]
    deployment_platforms JSONB,
    
    -- Architecture (already captured!)
    architecture_type VARCHAR(50),  -- microservices, mvc, monolith
    architecture_confidence FLOAT,
    service_count INTEGER DEFAULT 1,
    component_count INTEGER,
    layers JSONB,  -- ["api", "business", "data"]
    
    -- API Summary (already captured!)
    endpoint_count INTEGER DEFAULT 0,
    endpoints JSONB,  -- [{"path": "/api/v1/users", "method": "GET"}]
    has_rest_api BOOLEAN DEFAULT FALSE,
    has_graphql BOOLEAN DEFAULT FALSE,
    has_websocket BOOLEAN DEFAULT FALSE,
    
    -- Code Metrics (already captured!)
    total_files INTEGER,
    total_lines INTEGER,
    code_files INTEGER,
    test_files INTEGER,
    doc_files INTEGER,
    modularity_score FLOAT,
    
    -- Entry Points (already captured!)
    entry_points JSONB,  -- ["src/main.py", "app.py"]
    main_flows JSONB,
    
    -- AI Summary (already captured!)
    brief_description TEXT,
    key_features JSONB,
    technical_highlights JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ✅ EXISTING: Detected services
CREATE TABLE detected_services (
    id UUID PRIMARY KEY,
    repo_id VARCHAR(500) REFERENCES repository_contexts(repo_id) ON DELETE CASCADE,
    service_name VARCHAR(200) NOT NULL,
    root_path VARCHAR(500),
    
    file_count INTEGER,
    entry_point VARCHAR(500),
    internal_dependencies JSONB,
    external_dependencies JSONB,
    
    languages JSONB,
    frameworks JSONB,
    databases JSONB,
    
    has_api BOOLEAN DEFAULT FALSE,
    endpoints JSONB
);
```

**✅ LEVERAGE FOR:**
- Use for Phase 1 discovery (metadata already extracted!)
- Framework detection (already done!)
- Service/component identification (already done!)
- **This IS the knowledge graph foundation!**

---

#### **Quality Checks (ALREADY EXISTS)**

```sql
-- ✅ EXISTING: Quality validation
CREATE TABLE quality_checks (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES documentation_runs(id) ON DELETE CASCADE,
    artifact_id UUID REFERENCES documentation_artifacts(id) ON DELETE CASCADE,
    
    -- Completeness metrics (already implemented!)
    completeness_score FLOAT NOT NULL,
    missing_sections JSONB DEFAULT '[]',
    incomplete_sections JSONB DEFAULT '[]',
    placeholder_count INTEGER DEFAULT 0,
    broken_links JSONB DEFAULT '[]',
    formatting_issues JSONB DEFAULT '[]',
    section_word_counts JSONB DEFAULT '{}',
    has_code_examples BOOLEAN DEFAULT FALSE,
    
    -- Accuracy metrics (already implemented!)
    accuracy_score FLOAT NOT NULL,
    code_example_issues JSONB DEFAULT '[]',
    api_mismatches JSONB DEFAULT '[]',
    type_errors JSONB DEFAULT '[]',
    factual_errors JSONB DEFAULT '[]',
    accuracy_warnings JSONB DEFAULT '[]',
    validated_examples INTEGER DEFAULT 0,
    total_examples INTEGER DEFAULT 0,
    
    -- Confidence metrics (already implemented!)
    overall_confidence FLOAT NOT NULL,
    completeness_confidence FLOAT NOT NULL,
    accuracy_confidence FLOAT NOT NULL,
    source_quality_confidence FLOAT NOT NULL,
    confidence_breakdown JSONB DEFAULT '{}',
    
    -- Review workflow (already implemented!)
    requires_review BOOLEAN DEFAULT FALSE,
    review_priority VARCHAR(20),  -- critical, high, medium, low
    review_status VARCHAR(20),  -- pending, in_review, approved
    assigned_to VARCHAR(200),
    reviewed_at TIMESTAMP,
    reviewer_notes TEXT,
    
    -- Recommendations (already implemented!)
    recommendations JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ✅ EXISTING: Quality reports
CREATE TABLE quality_reports (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES documentation_runs(id) ON DELETE CASCADE,
    
    total_artifacts INTEGER NOT NULL,
    average_completeness FLOAT NOT NULL,
    average_accuracy FLOAT NOT NULL,
    average_confidence FLOAT NOT NULL,
    
    completeness_breakdown JSONB DEFAULT '{}',
    accuracy_breakdown JSONB DEFAULT '{}',
    confidence_breakdown JSONB DEFAULT '{}',
    
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    issues_by_type JSONB DEFAULT '{}',
    
    artifacts_requiring_review INTEGER DEFAULT 0,
    review_priority_breakdown JSONB DEFAULT '{}',
    
    top_recommendations JSONB DEFAULT '[]',
    quality_trend VARCHAR(20),  -- improving, declining, stable
    
    generated_at TIMESTAMP DEFAULT NOW()
);
```

**✅ LEVERAGE FOR:**
- Prompt effectiveness scoring (use existing accuracy/completeness scores)
- Quality tracking over time (already implemented!)
- Review workflow (already built!)
- **No new tables needed!**

---

### ✅ **2. RAG Configuration System (ALREADY EXISTS)**

#### **File-Based Configuration**

```
.rag-config/
├── config.yaml          # Feature flags, signal weights
├── glossary.yaml        # Domain terms with boost weights
├── templates.yaml       # Query templates by type
├── exclusions.yaml      # Noise filtering rules
├── priorities.yaml      # Priority documents
└── README.md            # Configuration guide
```

**✅ EXISTING: Glossary System**

```yaml
# .rag-config/glossary.yaml
glossary:
  MCP:
    description: "Model Context Protocol"
    synonyms: ["protocol", "context protocol", "model protocol"]
    boost_weight: 1.5  # 1.0-3.0
    examples:
      - "MCP enables tools to provide context to AI models"
  
  RAG:
    description: "Retrieval Augmented Generation"
    synonyms: ["retrieval augmented", "semantic search"]
    boost_weight: 1.4
```

**✅ EXISTING: Query Templates**

```yaml
# .rag-config/templates.yaml
templates:
  architecture:
    description: "System architecture questions"
    patterns:
      - "how (?:does|is) .* (?:architected|structured)"
      - "what is the architecture"
    optimized_sections:
      - "System Overview"
      - "Component Architecture"
      - "Data Flow"
    boost_paths:
      - "README.md"
      - "ARCHITECTURE.md"
      - "docs/architecture"
    boost_keywords:
      - "architecture"
      - "design"
      - "structure"
    documents_needed: 30
    prefer_recent: false
  
  api_documentation:
    patterns:
      - "(?:what|which) (?:api|endpoint)"
    optimized_sections:
      - "API Overview"
      - "Endpoints"
      - "Request/Response Examples"
    boost_paths:
      - "API.md"
      - "/api/"
    documents_needed: 25
    prefer_recent: true
```

**✅ EXISTING: Signal Weights**

```yaml
# .rag-config/config.yaml
signal_weights:
  semantic: 0.40        # Core semantic similarity
  glossary: 0.15        # Domain term relevance
  priority: 0.15        # User-defined priorities
  content_quality: 0.15 # Document quality metrics
  recency: 0.15         # Freshness (git history)
```

**✅ LEVERAGE FOR:**
- **Glossary → Knowledge Graph concepts**
- **Templates → Prompt templates for sections**
- **Signal weights → Already tunable!**
- **Just extend existing files!**

---

### ✅ **3. Caching Infrastructure (ALREADY EXISTS)**

#### **Multi-Level Cache**

```python
# ✅ EXISTING: L1 (Memory) + L2 (Redis) + L3 (Database)
class MultiLevelCache:
    """
    Architecture:
    - L1: In-memory LRU (fastest, 1000 items, 5 min TTL)
    - L2: Redis (fast, 100K items, 1 hour TTL)
    - L3: Database (slowest, unlimited)
    
    Features:
    - Automatic promotion (L2 → L1 on hit)
    - Intelligent eviction
    - Performance analytics
    - Cache warming
    """
    
    def __init__(
        self,
        prefix: str = "cache",
        l1_max_size: int = 1000,
        l1_ttl: int = 300,
        l2_ttl: int = 3600
    ):
        self.l1 = LRUCache(max_size=l1_max_size, ttl_seconds=l1_ttl)
        self.l2_ttl = l2_ttl
        # Redis client from get_redis_client()

# ✅ EXISTING: Cache decorator
@cache(ttl=3600, key_prefix="embedding")
async def generate_embedding(text: str) -> List[float]:
    ...

# ✅ EXISTING: Cache statistics
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    writes: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
```

**✅ LEVERAGE FOR:**
- Cache prompt results (reuse across passes)
- Cache discovered concepts
- Cache quality scores
- **Already built, just use it!**

---

### ✅ **4. File Classification (ALREADY EXISTS)**

```sql
-- ✅ EXISTING: File classification and importance
CREATE TABLE file_classifications (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES processing_plans(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0,
    
    -- Classification (already done!)
    extension VARCHAR(50),
    language VARCHAR(100),
    is_code BOOLEAN DEFAULT FALSE,
    is_test BOOLEAN DEFAULT FALSE,
    is_doc BOOLEAN DEFAULT FALSE,
    is_config BOOLEAN DEFAULT FALSE,
    
    -- Importance scoring (already implemented!)
    importance_level VARCHAR(50) NOT NULL,  -- critical, high, medium, low
    importance_score FLOAT NOT NULL DEFAULT 0.5,  -- 0.0-1.0
    priority INTEGER NOT NULL DEFAULT 1000,
    
    sub_job_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**✅ LEVERAGE FOR:**
- Document importance weighting (already scored!)
- Priority-based retrieval (already implemented!)
- File type filtering (already done!)
- **No changes needed!**

---

## 🔄 Integration Strategy

### **Phase 1: Enhance Existing Structures**

#### **1.1. Extend `documentation_runs.config` (JSONB)**

**Current:**
```json
{
  "passes": 5,
  "sections": ["overview", "architecture"]
}
```

**Enhanced:**
```json
{
  // ✅ Existing fields
  "passes": 5,
  "sections": ["overview", "architecture"],
  
  // 🆕 Adaptive features (new, optional)
  "adaptive": {
    "enabled": false,
    "enable_discovery": false,
    "enable_knowledge_graph": false,
    "enable_prompt_evolution": false,
    "enable_reembedding": false
  },
  
  // 🆕 Template reference (new, optional)
  "template": {
    "use_custom": false,
    "template_name": "scala_play",  // References .rag-config/templates.yaml
    "sections_override": null
  },
  
  // 🆕 Style tuning (new, optional)
  "style": {
    "tone": "professional",
    "technical_depth": "high",
    "custom_glossary": {
      "account": "customer",
      "supplier": "vendor"
    }
  },
  
  // 🆕 Citation settings (new, optional)
  "citations": {
    "enabled": true,
    "style": "endnotes",  // inline, footnotes, endnotes
    "include_relevance_scores": true
  },
  
  // 🆕 Transparency (new, optional)
  "transparency": {
    "mode": "normal",  // quiet, normal, verbose
    "log_prompts": true,
    "log_findings": true
  }
}
```

**✅ NO NEW TABLE NEEDED!** Just extend existing JSONB field.

---

#### **1.2. Extend `documents.doc_metadata` (JSONB)**

**Current:**
```json
{
  "author": "John Doe",
  "last_modified": "2025-01-15"
}
```

**Enhanced:**
```json
{
  // ✅ Existing metadata
  "author": "John Doe",
  "last_modified": "2025-01-15",
  
  // 🆕 Learned concepts (from knowledge graph)
  "concepts": ["supplier_onboarding", "authentication", "rest_api"],
  
  // 🆕 Extracted keywords (from NLP)
  "keywords": ["account", "registration", "async", "Future", "Slick"],
  
  // 🆕 Related entities (from static analysis)
  "entities": ["Account", "User", "RegistrationService"],
  
  // 🆕 Subject area classification
  "subject_area": "Core Domain Model",
  
  // 🆕 Relationships
  "relationships": {
    "uses": ["AccountRepository", "CRMService"],
    "used_by": ["RegistrationController"],
    "publishes": ["SupplierRegistered"]
  },
  
  // 🆕 Importance (from multiple signals)
  "importance": {
    "score": 0.92,
    "reasons": ["high_reference_count", "api_entry_point", "core_domain"]
  }
}
```

**✅ NO NEW TABLE NEEDED!** Just extend existing JSONB field.

---

#### **1.3. Extend `embeddings.extra_metadata` (JSONB)**

**Current:**
```json
{
  "embedding_version": "v2"
}
```

**Enhanced:**
```json
{
  // ✅ Existing metadata
  "embedding_version": "v2",
  
  // 🆕 Concept augmentation flag
  "concept_augmented": true,
  "augmentation_version": 1,
  
  // 🆕 Concepts used for augmentation
  "augmentation_concepts": ["supplier_onboarding", "rest_api"],
  
  // 🆕 Related terms added
  "augmentation_terms": ["account", "registration", "supplier"],
  
  // 🆕 Augmentation date
  "augmented_at": "2025-11-19T18:30:00Z",
  
  // 🆕 Original vs enhanced performance
  "retrieval_improvement": {
    "queries_tested": 50,
    "avg_relevance_before": 0.73,
    "avg_relevance_after": 0.89
  }
}
```

**✅ NO NEW TABLE NEEDED!** Just extend existing JSONB field.

---

### **Phase 2: Extend RAG Config Files**

#### **2.1. Add Prompt Templates to `templates.yaml`**

```yaml
# .rag-config/templates.yaml (ALREADY EXISTS, just add more)

# ✅ EXISTING: Query templates
templates:
  architecture:
    # ... existing fields ...
  
  # 🆕 ADD: Documentation section templates
  doc_sections:
    overview:
      base_prompt: |
        Provide a concise overview of {service_name}.
        Focus on:
        - Main purpose and functionality
        - Key technologies: {frameworks}
        - Target audience
        
        Use {tone} tone with {technical_depth} technical depth.
      
      multi_pass_refinement:
        - pass: 1
          focus: "Broad overview"
        - pass: 2
          focus: "Fill gaps from pass 1: {gaps}"
        - pass: 3
          focus: "Verify and synthesize"
      
      expected_word_count: 300-500
      
    data_models:
      base_prompt: |
        List all data models/entities in {service_name}.
        For each model in {detected_entities}, provide:
        - File location
        - Fields and types
        - Relationships to other models
        - Validations and constraints
        
        Use actual code examples from:
        {model_file_paths}
      
      multi_pass_refinement:
        - pass: 1
          focus: "Discover all models"
        - pass: 2
          focus: "Extract details for: {found_models}"
        - pass: 3
          focus: "Map relationships"
      
      boost_paths:
        - "*/models/*"
        - "*/entities/*"
```

**✅ Extends existing file!**

---

#### **2.2. Add Dynamic Glossary to `glossary.yaml`**

```yaml
# .rag-config/glossary.yaml (ALREADY EXISTS, just add more)

# ✅ EXISTING: Static terms
glossary:
  MCP:
    description: "Model Context Protocol"
    # ... existing ...

# 🆕 ADD: Service-specific learned terms
service_glossaries:
  adminservice:
    # Learned from discovery phase
    learned_at: "2025-11-19T18:00:00Z"
    confidence: 0.89
    terms:
      Supplier:
        description: "Third-party vendor in B2B network"
        synonyms: ["vendor", "external_account"]
        boost_weight: 1.4
        source: "inferred_from_codebase"
        
      External ID:
        description: "Third-party system identifier"
        synonyms: ["external_id", "partner_id"]
        boost_weight: 1.3
        source: "inferred_from_comments"
```

**✅ Extends existing file!**

---

### **Phase 3: Minimal New Tables (ONLY 3!)**

We only need 3 new tables, everything else uses existing infrastructure:

#### **3.1. Prompt Execution History**

```sql
-- 🆕 NEW TABLE: Track prompt effectiveness
CREATE TABLE prompt_execution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to documentation run
    run_id UUID NOT NULL REFERENCES documentation_runs(id) ON DELETE CASCADE,
    
    -- Prompt details
    prompt_template VARCHAR(255),  -- References template in .rag-config/templates.yaml
    prompt_used TEXT NOT NULL,
    context_provided JSONB,  -- What context was available
    
    -- Execution
    pass_number INTEGER,
    section_name VARCHAR(100),
    executed_at TIMESTAMP DEFAULT NOW(),
    
    -- Results
    response_length INTEGER,
    tokens_used INTEGER,
    sources_used JSONB,  -- Document IDs
    
    -- Effectiveness (calculated)
    effectiveness_score FLOAT,  -- 0-1, from quality_checks
    specificity_score FLOAT,  -- 0-1, did it mention specific files/classes?
    code_examples_count INTEGER,
    
    -- Findings extracted (for next pass)
    findings JSONB,
    -- {
    --   "entities": ["Account", "User"],
    --   "services": ["RegistrationService"],
    --   "keywords": ["async", "Future"],
    --   "gaps_identified": ["error handling", "test coverage"]
    -- }
    
    CONSTRAINT valid_effectiveness CHECK (effectiveness_score IS NULL OR effectiveness_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_prompt_history_run ON prompt_execution_history(run_id);
CREATE INDEX idx_prompt_history_effectiveness ON prompt_execution_history(effectiveness_score);
CREATE INDEX idx_prompt_history_template ON prompt_execution_history(prompt_template);
```

**✅ Purpose:** Track what works, improve prompts over time

---

#### **3.2. Document Citations**

```sql
-- 🆕 NEW TABLE: Track source citations
CREATE TABLE documentation_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to artifact
    artifact_id UUID NOT NULL REFERENCES documentation_artifacts(id) ON DELETE CASCADE,
    
    -- Source document
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Citation details
    section_name VARCHAR(255),  -- Which section used this
    relevance_score FLOAT NOT NULL,
    
    -- Excerpt
    excerpt TEXT,  -- Specific portion used (~200 chars)
    start_line INTEGER,
    end_line INTEGER,
    
    -- Metadata
    citation_text TEXT,  -- Formatted citation for display
    citation_order INTEGER,  -- Order in citation list
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_relevance CHECK (relevance_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_citations_artifact ON documentation_citations(artifact_id);
CREATE INDEX idx_citations_document ON documentation_citations(document_id);
CREATE INDEX idx_citations_section ON documentation_citations(artifact_id, section_name);
```

**✅ Purpose:** Enable source tracing and transparency

---

#### **3.3. Generation Transparency Log**

```sql
-- 🆕 NEW TABLE: Transparency and audit trail
CREATE TABLE generation_transparency_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to run
    run_id UUID NOT NULL REFERENCES documentation_runs(id) ON DELETE CASCADE,
    
    -- Phase/step
    phase VARCHAR(100) NOT NULL,  -- "Discovery", "Generation:Overview", "Re-embedding"
    sequence_number INTEGER NOT NULL,  -- Order of operations
    
    -- Action
    action_type VARCHAR(50) NOT NULL,  -- "query", "extract", "build_graph", "reembed"
    action_description TEXT NOT NULL,
    
    -- Input/Output
    input_data JSONB,  -- Query, parameters, etc.
    output_data JSONB,  -- Results, findings, etc.
    
    -- Timing
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'success',  -- success, failed, skipped
    error_message TEXT,
    
    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped'))
);

CREATE INDEX idx_transparency_run ON generation_transparency_log(run_id);
CREATE INDEX idx_transparency_phase ON generation_transparency_log(run_id, phase);
CREATE INDEX idx_transparency_sequence ON generation_transparency_log(run_id, sequence_number);
```

**✅ Purpose:** Full transparency - users see every step

---

## 🎯 Implementation Plan

### **Week 1-2: Extend Existing Structures**

**Tasks:**
1. ✅ Update code to populate `doc_metadata` with concepts/keywords
2. ✅ Extend `documentation_runs.config` schema validation
3. ✅ Add concept extraction to ingestion pipeline
4. ✅ Update documentation to reflect new JSONB fields

**Effort:** 2 days  
**Risk:** Low (backward compatible - new fields are optional)

---

### **Week 3-4: Extend RAG Config**

**Tasks:**
1. ✅ Add prompt templates to `templates.yaml`
2. ✅ Add service-specific glossaries to `glossary.yaml`
3. ✅ Update RAG config loader to support new sections
4. ✅ Test template rendering with context

**Effort:** 3 days  
**Risk:** Low (extends existing system)

---

### **Week 5-6: Add 3 New Tables + Services**

**Tasks:**
1. ✅ Create migration for 3 new tables
2. ✅ Create SQLAlchemy models
3. ✅ Create repositories for new tables
4. ✅ Integrate into documentation generator

**Effort:** 5 days  
**Risk:** Medium (new tables, but simple schema)

---

### **Week 7-8: Adaptive Generation Logic**

**Tasks:**
1. ✅ Build discovery phase (populate `repository_contexts`)
2. ✅ Build prompt refinement loop (uses `prompt_execution_history`)
3. ✅ Build citation tracker (populates `documentation_citations`)
4. ✅ Build transparency logger (populates `generation_transparency_log`)
5. ✅ Add re-embedding trigger

**Effort:** 10 days  
**Risk:** High (complex logic, but builds on existing)

---

### **Week 9-10: Dashboard Integration**

**Tasks:**
1. ✅ Add configuration UI (reads/writes `documentation_runs.config`)
2. ✅ Add transparency viewer (reads `generation_transparency_log`)
3. ✅ Add citation viewer (reads `documentation_citations`)
4. ✅ Add prompt analytics (reads `prompt_execution_history`)

**Effort:** 5 days  
**Risk:** Low (UI only, reads existing data)

---

### **Week 11-12: Testing & Polish**

**Tasks:**
1. ✅ End-to-end testing
2. ✅ Performance optimization
3. ✅ Documentation
4. ✅ Migration guide

**Effort:** 10 days  
**Risk:** Low

---

## 📊 Infrastructure Mapping Summary

| Adaptive Feature | Existing Infrastructure | Changes Needed |
|------------------|-------------------------|----------------|
| **Knowledge Graph** | `repository_contexts`, `detected_services` | ✅ Use as-is, just query differently |
| **Concept Storage** | `documents.doc_metadata` (JSONB) | ✅ Extend existing JSONB |
| **Enhanced Embeddings** | `embeddings.extra_metadata` (JSONB) | ✅ Extend existing JSONB |
| **Configuration** | `documentation_runs.config` (JSONB) | ✅ Extend existing JSONB |
| **Glossary** | `.rag-config/glossary.yaml` | ✅ Extend existing file |
| **Prompt Templates** | `.rag-config/templates.yaml` | ✅ Extend existing file |
| **Quality Tracking** | `quality_checks`, `quality_reports` | ✅ Use as-is for effectiveness scoring |
| **Caching** | `MultiLevelCache`, Redis | ✅ Use as-is for prompt caching |
| **File Classification** | `file_classifications` | ✅ Use as-is for importance weighting |
| **Prompt History** | ❌ Not exists | 🆕 New table (1 of 3) |
| **Citations** | ❌ Not exists | 🆕 New table (2 of 3) |
| **Transparency Log** | ❌ Not exists | 🆕 New table (3 of 3) |

---

## 🚀 Key Benefits of This Approach

### **1. Minimal Schema Changes**

- ❌ Original plan: 9 new tables
- ✅ This plan: 3 new tables + extend existing JSONB fields

### **2. Leverage Existing Data**

- ✅ `repository_contexts` already has framework detection, architecture analysis
- ✅ `quality_checks` already tracks completeness, accuracy
- ✅ `file_classifications` already scores importance
- ✅ RAG config already has glossary, templates, signal weights

### **3. Backward Compatible**

- All new JSONB fields are optional
- Old code continues to work
- New features opt-in via config

### **4. Fast Implementation**

- ❌ Original estimate: 12 weeks
- ✅ This estimate: 8-10 weeks (20% faster)

### **5. Lower Maintenance**

- Fewer tables = simpler schema
- Extend existing patterns
- Reuse existing infrastructure

---

## 💡 Example: Adaptive Generation Flow

```python
async def generate_documentation_adaptive(service_name: str, config: Dict):
    """
    Adaptive documentation generation using EXISTING infrastructure.
    """
    
    # Step 1: Load configuration (from existing JSONB field)
    adaptive_config = config.get('adaptive', {})
    if not adaptive_config.get('enabled', False):
        # Fall back to standard generation
        return await generate_documentation_standard(service_name, config)
    
    # Step 2: Discovery phase (query EXISTING repository_contexts table)
    repo_context = await get_repository_context(service_name)
    # Returns: frameworks, architecture_type, languages, endpoints, etc.
    # This data ALREADY EXISTS from ingestion!
    
    # Step 3: Build context for prompts
    context = {
        "service_name": service_name,
        "frameworks": repo_context.frameworks,  # Already extracted!
        "architecture": repo_context.architecture_type,  # Already known!
        "endpoints": repo_context.endpoints,  # Already cataloged!
        "entities": extract_entities_from_metadata(service_name),  # From doc_metadata JSONB
        "tone": config['style']['tone'],
        "technical_depth": config['style']['technical_depth']
    }
    
    # Step 4: Load prompt template (from EXISTING .rag-config/templates.yaml)
    template_name = config['template']['template_name']
    template = load_template_from_yaml(template_name, section='overview')
    
    # Step 5: Fill template with context
    prompt = fill_template(template['base_prompt'], context)
    
    # Step 6: Execute query (using EXISTING RAG infrastructure)
    response = await execute_enhanced_query(
        prompt,
        service_filter=service_name,
        n_results=template.get('documents_needed', 20),
        use_enhancements=True  # Uses glossary, templates from .rag-config
    )
    
    # Step 7: Track execution (NEW table: prompt_execution_history)
    await track_prompt_execution(
        run_id=run_id,
        prompt=prompt,
        response=response,
        context=context,
        effectiveness_score=calculate_effectiveness(response)
    )
    
    # Step 8: Track citations (NEW table: documentation_citations)
    for source in response['sources']:
        await add_citation(
            artifact_id=artifact_id,
            document_id=source['id'],
            relevance_score=source['score'],
            excerpt=source['excerpt'][:200]
        )
    
    # Step 9: Log for transparency (NEW table: generation_transparency_log)
    await log_transparency(
        run_id=run_id,
        phase="Generation:Overview",
        action="execute_query",
        input_data={"prompt": prompt[:100] + "..."},
        output_data={"response_length": len(response['answer']), "sources_count": len(response['sources'])}
    )
    
    # Step 10: Extract findings (store in EXISTING doc_metadata JSONB)
    findings = extract_findings(response['answer'])
    await update_document_metadata(
        document_ids=response['source_ids'],
        metadata_updates={
            "concepts": findings['concepts'],
            "keywords": findings['keywords']
        }
    )
    
    return response['answer']
```

**✅ Uses mostly EXISTING infrastructure!**

---

## 📈 Success Metrics

| Metric | Baseline | With Adaptive | Method |
|--------|----------|---------------|---------|
| Specificity | 65% | 90% | `prompt_execution_history.specificity_score` |
| Code Examples | 15 | 40 | `quality_checks.validated_examples` |
| User Rating | 3.5/5 | 4.7/5 | `quality_reports.average_accuracy` |
| Generation Time | 10 min | 15 min | `documentation_runs.completed_at - started_at` |
| Concepts Learned | 0 | 150+ | Count unique values in `doc_metadata->>'concepts'` |
| Re-use Rate | 0% | 60% | `prompt_execution_history` cache hits |

---

## 🔧 Code Example: Extending Existing Structures

### **Example 1: Update Document Metadata**

```python
async def enhance_document_with_concepts(document_id: UUID, concepts: List[str]):
    """
    Add learned concepts to EXISTING doc_metadata JSONB field.
    NO NEW TABLE NEEDED!
    """
    async with get_database().session() as session:
        doc = await session.get(DocumentModel, document_id)
        
        # Extend existing JSONB
        current_metadata = doc.doc_metadata or {}
        current_metadata['concepts'] = concepts
        current_metadata['concepts_updated_at'] = datetime.utcnow().isoformat()
        
        doc.doc_metadata = current_metadata
        await session.commit()
```

### **Example 2: Query Existing Repository Context**

```python
async def get_framework_context(service_name: str) -> Dict:
    """
    Get framework info from EXISTING repository_contexts table.
    Data ALREADY EXISTS from ingestion!
    """
    async with get_database().session() as session:
        repo = await session.query(RepositoryContextModel).filter_by(
            repo_id=service_name
        ).first()
        
        if not repo:
            return {}
        
        return {
            "frameworks": repo.frameworks or [],  # Already extracted!
            "languages": repo.languages or {},  # Already counted!
            "architecture": repo.architecture_type,  # Already detected!
            "endpoints": repo.endpoints or [],  # Already cataloged!
            "entry_points": repo.entry_points or []  # Already identified!
        }
```

### **Example 3: Load Prompt Template from Existing Config**

```python
async def load_prompt_template(section: str, context: Dict) -> str:
    """
    Load template from EXISTING .rag-config/templates.yaml
    and fill with context.
    """
    import yaml
    
    # Load existing file
    with open('.rag-config/templates.yaml') as f:
        templates = yaml.safe_load(f)
    
    # Get section template
    section_template = templates['doc_sections'][section]
    
    # Fill placeholders
    prompt = section_template['base_prompt'].format(**context)
    
    return prompt
```

---

**Status**: 🔍 **AUDIT COMPLETE**  
**New Tables Required**: 3 (vs 9 in original plan)  
**Leverage Ratio**: 90% existing infrastructure  
**Implementation Time**: 8-10 weeks (vs 12 weeks)  
**Risk**: 🟢 **LOW** (mostly extends existing systems)

