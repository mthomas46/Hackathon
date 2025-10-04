# 🗄️ Data Architecture & Store Relationships Report

**Generated:** 2025-10-04 06:26:00 UTC  
**Report Type:** Data Architecture & Ecosystem Integration Analysis  
**Related Reports:**  
- [Planning Service Report](./Planning_Service_Report.md) - Production planning output  
- [Behind-the-Scenes Report](./Behind_the_Scenes_Report.md) - Demo execution details  
- [Ecosystem Validation Report](./Ecosystem_Validation_Report.md) - Live code proof  
- [Main README](../README.md) - Demo overview

---

## 📊 Executive Summary

This report provides an in-depth analysis of how data flows through the ecosystem's multiple data stores, including:
- **4 Primary Data Stores** (doc_store, prompt_store, external-service-store, memory-agent)
- **16 Services** discovered from 24 historical documents
- **66 Document-Service Linkings** created
- Complete data architecture visualizations and schemas

---

## 1. Ecosystem Data Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LLM DOCUMENTATION ECOSYSTEM                           │
│                        Data Layer Architecture                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  doc_store   │       │ prompt_store │       │ memory-agent │
│   (SQLite)   │       │   (SQLite)   │       │(Redis+SQLite)│
│              │       │              │       │              │
│ Historical   │       │  Workflow    │       │  Execution   │
│  Documents   │       │  Prompts     │       │  Contexts    │
│              │       │              │       │              │
│ • Jira       │       │ • Planning   │       │ • Workflow A │
│ • Confluence │       │ • Analysis   │       │ • Workflow B │
│ • GitHub PRs │       │ • Discovery  │       │ • Workflow C │
│              │       │              │       │ • Workflow D │
│              │       │              │       │ • Workflow E │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                       │
       │              ┌───────┴───────┐              │
       │              │                │              │
       └──────────────┤  Orchestrator  ├──────────────┘
                      │                │
                      └───────┬────────┘
                              │
                      ┌───────┴────────┐
                      │                │
                ┌─────┴─────┐    ┌────┴─────┐
                │ external- │    │  user-   │
                │ service-  │    │  store   │
                │  store    │    │ (SQLite) │
                │ (SQLite)  │    │          │
                │           │    │  Team    │
                │ Discovered│    │  Skills  │
                │ Services  │    │  Data    │
                └───────────┘    └──────────┘
```

### 1.2 Data Flow Diagram

```
Historical Documents (doc_store)
        │
        ├──> Service Discovery Engine
        │         │
        │         ├──> Extract Service Mentions
        │         │
        │         └──> Store in external-service-store
        │                     │
        │                     └──> Create Linkings
        │                               │
        ├───────────────────────────────┘
        │
        └──> Workflow Execution
                 │
                 ├──> Use Prompts (prompt_store)
                 │
                 ├──> Analyze Services (external-service-store)
                 │
                 ├──> Match Team Skills (user-store)
                 │
                 └──> Store Context (memory-agent)
```

---

## 2. Live Data Store Contents

**This section shows ACTUAL data currently persisted in the ecosystem datastores - real records with IDs, timestamps, and relationships:**

⚠️ No live data available. Ensure all services are running.

---

## 3. Data Store Schemas

### 3.1 doc_store (Historical Documents)

**Purpose:** Stores all historical project documents (Jira tickets, Confluence docs, GitHub PRs)

**Schema:**
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    content_hash TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_doc_metadata ON documents(metadata);
CREATE INDEX idx_doc_created ON documents(created_at);
CREATE INDEX idx_doc_source ON documents((metadata->>'source'));
CREATE INDEX idx_doc_type ON documents((metadata->>'doc_type'));
```

**Metadata Structure:**
```json
{
    "source": "jira|confluence|github",
    "doc_type": "jira_ticket|confluence_doc|github_pr",
    "category": "historical_data",
    "tech_stack": ["Scala", "Elm", "CRUD"],
    "created_date": "2025-10-03",
    "status": "completed|merged",
    "key": "PROJ-123",
    "summary": "Feature summary...",
    "author": "user_name",
    "linked_services": ["service-id-1", "service-id-2"]
}
```

**Current Data:**
- **Jira Tickets:** 4 documents
- **Confluence Docs:** 4 documents
- **GitHub PRs:** 6 documents
- **Total:** 14 documents

### 3.2 prompt_store (Workflow Prompts)

**Purpose:** Stores all prompts used by AI-powered workflows

**Schema:**
```sql
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    tags JSON,
    variables JSON,
    model_params JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prompt_category ON prompts(category);
CREATE INDEX idx_prompt_tags ON prompts(tags);
CREATE INDEX idx_prompt_active ON prompts(is_active);
```

**Prompt Categories:**
- `planning` - Feature decomposition and planning prompts
- `analysis` - Historical context analysis prompts
- `estimation` - Timeline and resource estimation prompts
- `discovery` - External service discovery prompts
- `validation` - Compliance and validation prompts
- `risk_analysis` - Blindspot and risk detection prompts

**Current Data:**
- **Prompts Stored:** 8 workflow prompts
  - feature_decomposition_prompt
  - historical_context_analysis_prompt
  - timeline_estimation_prompt
  - team_skills_matching_prompt
  - external_service_discovery_prompt
  - compliance_validation_prompt
  - knowledge_gap_detection_prompt
  - blindspot_detection_prompt

### 3.3 external-service-store (Discovered Services)

**Purpose:** Catalog of all external services discovered from documents and user input

**Schema:**
```sql
CREATE TABLE external_services (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    service_type TEXT NOT NULL,
    description TEXT,
    version TEXT,
    technologies JSON,
    tags JSON,
    endpoints JSON,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_document_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    document_type TEXT,
    relationship TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES external_services(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE INDEX idx_service_type ON external_services(service_type);
CREATE INDEX idx_service_tags ON external_services(tags);
CREATE INDEX idx_service_doc_links ON service_document_links(service_id, document_id);
```

**Service Types:**
- `API` - REST APIs, GraphQL, etc.
- `DATABASE` - PostgreSQL, MongoDB, Redis, etc.
- `FRAMEWORK` - HTTP4s, React, Elm, etc.
- `LIBRARY` - Circe, Doobie, etc.
- `TOOL` - Docker, Kubernetes, SBT, etc.
- `LANGUAGE` - Scala, JavaScript, Python, etc.

**Current Data:**
- **Services Discovered:** 16 services
- **Services Stored:** 16 services
- **Document Links:** 66 linkings

**Top Discovered Services:**


1. **Redis**
   - Mentions: 12
   - Confidence: 1.00
   - Source Types: github
   - Linked Documents: 12

2. **Datadog**
   - Mentions: 10
   - Confidence: 1.00
   - Source Types: tangential
   - Linked Documents: 10

3. **Auth0**
   - Mentions: 10
   - Confidence: 1.00
   - Source Types: tangential
   - Linked Documents: 10

4. **Python**
   - Mentions: 8
   - Confidence: 0.95
   - Source Types: confluence
   - Linked Documents: 8

5. **FastAPI**
   - Mentions: 6
   - Confidence: 0.95
   - Source Types: confluence
   - Linked Documents: 6

6. **OAuth**
   - Mentions: 5
   - Confidence: 0.95
   - Source Types: confluence
   - Linked Documents: 5

7. **Swagger**
   - Mentions: 4
   - Confidence: 1.00
   - Source Types: tangential
   - Linked Documents: 4

8. **PostgreSQL**
   - Mentions: 2
   - Confidence: 0.95
   - Source Types: github
   - Linked Documents: 2

9. **Kubernetes**
   - Mentions: 2
   - Confidence: 1.00
   - Source Types: tangential
   - Linked Documents: 2

10. **JWT**
   - Mentions: 1
   - Confidence: 0.95
   - Source Types: tangential
   - Linked Documents: 1


### 3.4 memory-agent (Workflow Execution Contexts)

**Purpose:** Stores execution history and context for all workflows

**Schema (Redis + Context Structure):**
```python
# Redis Key Pattern
workflow:<workflow_type>:<workflow_id>

# Context Structure
{{
    "workflow_id": "workflow_a_20251003_120000",
    "workflow_type": "workflow_a",
    "workflow_name": "Feature Decomposition",
    "input_data": {{
        "feature": "Feature description...",
        "tech_stack": ["Scala", "Elm"]
    }},
    "output_data": {{
        "user_stories": 4,
        "technical_tasks": 5,
        "total_story_points": 68,
        "confidence": 0.78
    }},
    "execution_metadata": {{
        "execution_time_seconds": 0.5,
        "timestamp": "2025-10-03T12:00:00.000Z",
        "status": "completed"
    }},
    "ttl": 604800  # 7 days
}}
```

**Workflow Types Stored:**
- `workflow_a` - Feature Decomposition contexts
- `workflow_b` - Historical Context Analysis contexts
- `workflow_c` - Timeline Estimation contexts
- `workflow_d` - Team Skills Matching contexts
- `workflow_e` - External Service Validation contexts

**Current Data:**
- **Workflow Contexts:** 5 workflows executed
- **Total Execution Time:** 0.00s
- **Storage TTL:** 7 days

### 3.5 user-store (Team & Skills Data)

**Purpose:** Stores team member profiles, skills, and capacity data

**Schema:**
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    email TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    proficiency_level TEXT,
    years_experience INTEGER,
    projects_completed INTEGER,
    last_used DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_user_skills ON skills(user_id, skill_name);
CREATE INDEX idx_skill_proficiency ON skills(proficiency_level);
```

**Current Data:**
- **Team Members:** 6 members
- **Total Skills:** 18 skill entries
- **Skills Coverage:** 96.0%

---

## 4. Data Relationships & Linkings

### 3.1 Document → Service Linkings

**Relationship Type:** `mentions`

Documents in `doc_store` are automatically linked to services in `external-service-store` based on:
- Explicit service mentions in document content
- Technology stack tags
- Keywords and patterns
- Contextual analysis

**Link Structure:**
```json
{
    "service_id": "scala-http4s-api",
    "service_name": "Scala HTTP4s API",
    "document_type": "jira_ticket",
    "document_id": "PROJ-123",
    "relationship": "mentions",
    "confidence": 0.95
}
```

**Current Linkings:**


- **Jira → Services:** 0 linkings
- **Confluence → Services:** 13 linkings
- **GitHub → Services:** 3 linkings
- **Total Links:** 66 linkings

### 3.2 Service → Document Reverse Index

Each service in `external-service-store` maintains a list of source documents:

```python
service.metadata = {
    "source_documents": [
        {
            "type": "jira_ticket",
            "key": "PROJ-123",
            "summary": "Implement Scala API..."
        },
        {
            "type": "confluence_doc",
            "doc_id": "CONF-001",
            "title": "Architecture Overview"
        }
    ],
    "mention_count": 5,
    "confidence": 0.92
}
```

### 3.3 Workflow → Documents

Workflows reference historical documents stored in `doc_store`:

```
Workflow B (Historical Context)
    │
    ├──> Query doc_store for relevant Jira tickets
    │
    ├──> Analyze Confluence documentation
    │
    └──> Review GitHub PR history
         │
         └──> Extract velocity, patterns, complexity
```

### 3.4 Workflow → Services

Workflow E specifically analyzes services from `external-service-store`:

```
Workflow E (External Service Validation)
    │
    ├──> Query external-service-store
    │
    ├──> Validate API contracts
    │
    ├──> Check version compatibility
    │
    └──> Detect integration risks
```

### 3.5 Workflow → Prompts

All workflows use prompts from `prompt_store`:

| Workflow | Prompts Used |
|----------|--------------|
| Workflow A | feature_decomposition_prompt |
| Workflow B | historical_context_analysis_prompt |
| Workflow C | timeline_estimation_prompt |
| Workflow D | team_skills_matching_prompt |
| Workflow E | external_service_discovery_prompt, compliance_validation_prompt, knowledge_gap_detection_prompt, blindspot_detection_prompt |

### 3.6 Workflow → Memory

All workflow executions are stored in `memory-agent`:

```
memory-agent
    │
    ├──> workflow:workflow_a:* (Feature Decomposition executions)
    ├──> workflow:workflow_b:* (Historical Context executions)
    ├──> workflow:workflow_c:* (Timeline Estimation executions)
    ├──> workflow:workflow_d:* (Skills Matching executions)
    └──> workflow:workflow_e:* (Service Validation executions)
```

---

## 5. Data Architecture Patterns

### 4.1 Source-of-Truth Pattern

Each data store is the authoritative source for its domain:

| Store | Source of Truth For |
|-------|---------------------|
| **doc_store** | Historical project documents |
| **prompt_store** | Workflow prompt templates |
| **external-service-store** | Discovered external services |
| **memory-agent** | Workflow execution history |
| **user-store** | Team member data and skills |

### 4.2 Linking Pattern

Cross-store relationships are maintained through:
1. **Metadata References** - Store IDs in JSON metadata fields
2. **Linking Tables** - Dedicated tables for N:M relationships
3. **Reverse Indexes** - Source document lists in service metadata
4. **Key Patterns** - Redis key patterns for workflow contexts

### 4.3 Discovery Pattern

Services are discovered through multi-source analysis:

```
Historical Documents
    │
    ├──> Jira Tickets
    │    └──> Extract: tech_stack, description mentions
    │
    ├──> Confluence Docs
    │    └──> Extract: tags, section titles, content
    │
    └──> GitHub PRs
         └──> Extract: tech_stack, commit messages
              │
              └──> Aggregate & Deduplicate
                   │
                   └──> Store in external-service-store
                        │
                        └──> Create document linkings
```

### 4.4 Context Accumulation Pattern

Workflow contexts accumulate over time in `memory-agent`:

```
Initial Run:
  workflow:workflow_a:001 (Feature X)

Second Run:
  workflow:workflow_a:001 (Feature X)
  workflow:workflow_a:002 (Feature Y)

Third Run:
  workflow:workflow_a:001 (Feature X)
  workflow:workflow_a:002 (Feature Y)
  workflow:workflow_a:003 (Feature Z)
  
→ Historical context grows
→ Pattern recognition improves
→ Velocity calculations become more accurate
```

---

## 6. Query Examples

### 5.1 Find All Documents Mentioning a Service

```bash
# Query doc_store for documents with specific service
curl 'http://localhost:5087/api/v1/documents?metadata.linked_services=scala-http4s-api' | jq '.'
```

### 5.2 Find All Services from Jira Tickets

```bash
# Query external-service-store for services discovered from Jira
curl 'http://localhost:5090/services?source_type=jira' | jq '.'
```

### 5.3 Get Workflow Execution History

```bash
# Query memory-agent for all Workflow E executions
curl 'http://localhost:5090/memory/get?key=workflow:workflow_e:*' | jq '.'
```

### 5.4 Find Prompts for Planning

```bash
# Query prompt_store for planning category
curl 'http://localhost:5110/api/v1/prompts?category=planning' | jq '.'
```

### 5.5 Cross-Store Query Pattern

```python
# 1. Get service from external-service-store
service = await get_service("scala-http4s-api")

# 2. Get linked documents
doc_ids = service.metadata["source_documents"]

# 3. Fetch documents from doc_store
documents = await get_documents_by_ids(doc_ids)

# 4. Get workflow contexts that used this service
workflows = await get_workflows_by_service(service.id)

# 5. Get prompts used in those workflows
prompts = await get_prompts_by_workflow_type(workflows[0].workflow_type)
```

---

## 7. User Intelligence & User-Store Enhancements (Workflow F)

**New user intelligence capabilities integrated into the ecosystem:**

### 7.1 User-Store Schema Enhancements

**Enhanced User Schema with Workflow F Fields**:

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    role TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    
    -- ⭐ NEW: Workflow F Enhancements
    team_id TEXT,  -- Groups users into teams
    
    -- Profile & Metadata
    skills JSON,  -- [{"skill": "Python", "level": "Expert", "years": 8}]
    experience_level TEXT,
    years_experience INTEGER,
    
    -- Activity & Relationships
    documents_created JSON,  -- List of document IDs
    documents_updated JSON,
    documents_commented JSON,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ⭐ NEW: Team grouping index
CREATE INDEX idx_users_team_id ON users(team_id);

-- Existing indexes
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_email ON users(email);
```

**Key Enhancements**:
- **Team Organization**: `team_id` field enables team-based queries and analytics
- **Document Relationships**: Track user's document authorship, edits, and comments
- **Skills Tracking**: Structured skill data with proficiency levels and years
- **Experience Metrics**: Capture experience level and years for expertise scoring

### 7.2 User Extraction Data Flow

**Workflow F User Extraction Pipeline**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW F: USER EXTRACTION FLOW                      │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: Document Analysis
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ GitHub PRs   │    │ Jira Tickets │    │ Confluence   │
│              │    │              │    │  Documents   │
│ • Author     │    │ • Reporter   │    │ • Author     │
│ • Reviewers  │    │ • Assignee   │    │ • Editors    │
│ • Assignees  │    │ • Watchers   │    │ • Maintainers│
│ • Merger     │    │ • Worklog    │    │ • Watchers   │
│ • Commenters │    │ • Commenters │    │ • Commenters │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       └───────────────────┴────────────────────┘
                           │
                           ↓
Step 2: User Metadata Extraction
┌─────────────────────────────────────────────────────────────┐
│ UserIntelligenceWorkflow.extract_user_from_*()               │
│                                                               │
│ Extracts:                                                     │
│ • Username, email, display name                               │
│ • Role based on activity patterns                             │
│ • Skills from technologies used                               │
│ • Document relationships (created/edited/commented)           │
│ • Collaboration patterns                                      │
│ • Expertise indicators (commit count, review quality, etc.)   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
Step 3: User Deduplication & Aggregation
┌─────────────────────────────────────────────────────────────┐
│ • Merge users by username                                     │
│ • Aggregate document relationships                            │
│ • Calculate total interactions                                │
│ • Identify primary skills                                     │
│ • Determine expertise areas                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
Step 4: User-Store Persistence
┌─────────────────────────────────────────────────────────────┐
│ POST http://localhost:5060/api/v1/users                      │
│                                                               │
│ Payload:                                                      │
│ {                                                             │
│   "username": "sarah.chen",                                   │
│   "email": "sarah.chen@company.com",                          │
│   "role": "developer",                                        │
│   "team_id": "team-abc-123",                                  │
│   "skills": [{"skill": "Python", "level": "Expert"}],        │
│   "documents_created": ["doc-123", "doc-456"]                 │
│ }                                                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
Step 5: Expert-Finder Integration
┌─────────────────────────────────────────────────────────────┐
│ Expert-finder service queries user-store for:                 │
│ • Natural language expert search                              │
│ • Topic-based expert discovery                                │
│ • SME identification                                          │
│ • Teammate recommendations                                    │
│ • Team expertise analysis                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
Step 6: Planning Service Enrichment
┌─────────────────────────────────────────────────────────────┐
│ Planning Service Report (Section 10):                         │
│ • SME recommendations                                         │
│ • Technology coverage analysis                                │
│ • Knowledge gap identification                                │
│ • Pairing suggestions                                         │
│ • Expert-finder API examples                                  │
└─────────────────────────────────────────────────────────────┘
```

**Flow Statistics (This Demo)**:
- Documents Analyzed: 6 GitHub PRs, 4 Jira tickets, 4 Confluence docs
- Users Extracted: 10 unique users
- SMEs Identified: 12 experts
- Team ID: N/A

### 7.3 Document-User Relationships

**Relationship Types Tracked**:

| Relationship Type | Description | Source Documents | Storage |
|-------------------|-------------|------------------|---------|
| **Created By** | User authored the document | GitHub PRs, Jira (reporter), Confluence (author) | `documents_created` JSON array |
| **Updated By** | User edited/modified | GitHub (commits), Confluence (editors) | `documents_updated` JSON array |
| **Commented By** | User left comments | GitHub (PR comments), Jira (comments), Confluence (comments) | `documents_commented` JSON array |
| **Reviewed By** | User reviewed code | GitHub (PR reviewers) | User metadata |
| **Assigned To** | User assigned to work | GitHub (assignees), Jira (assignee) | User metadata |
| **Merged By** | User merged PR | GitHub (merger) | User metadata |
| **Maintained By** | User maintains documentation | Confluence (maintainers) | User metadata |
| **Watched By** | User follows updates | Jira (watchers), Confluence (watchers) | User metadata |

**Relationship Mapping Example**:

```
User: sarah.chen
├── documents_created: ["doc-gh-pr-789", "doc-jira-456", "doc-conf-123"]
├── documents_updated: ["doc-gh-pr-234", "doc-conf-567"]
├── documents_commented: ["doc-gh-pr-111", "doc-jira-222"]
└── metadata:
    ├── github_prs_authored: 5
    ├── github_prs_reviewed: 12
    ├── jira_tickets_reported: 8
    ├── confluence_pages_authored: 3
    └── total_interactions: 28
```

### 7.4 Team Organization

**Team-Based User Grouping**:

The `team_id` field enables powerful team-level queries and analytics:

**Query 1: Get All Team Members**
```bash
curl 'http://localhost:5060/api/v1/users?team_id={team_id}' | jq '.'
```

**Query 2: Team Expertise Overview**
```bash
curl 'http://localhost:5160/teams/{team_id}/expertise' | jq '.'
```

**Response Example**:
```json
{
  "team_id": "team-abc-123",
  "team_size": 6,
  "total_skills": 18,
  "technology_coverage": {
    "Python": {"experts": 2, "avg_years": 6.5},
    "React": {"experts": 2, "avg_years": 3.5},
    "Docker": {"experts": 1, "avg_years": 10}
  },
  "knowledge_gaps": ["FastAPI", "Redis", "OAuth", "JWT"],
  "team_documents": 42,
  "team_contributions": 156
}
```

**Benefits**:
- Team-wide skill assessments
- Identify team knowledge gaps
- Track team productivity
- Facilitate team-based work assignments
- Enable cross-team collaboration analysis

### 7.5 User Intelligence Metrics

**Key Metrics Tracked Per User**:

| Metric Category | Metrics | Purpose |
|-----------------|---------|---------|
| **Contribution** | Documents created, updated, commented | Activity level assessment |
| **Code Review** | PRs reviewed, review quality score, review comments | Code review expertise |
| **Documentation** | Pages authored, pages edited, documentation quality | Documentation expertise |
| **Collaboration** | Teammates worked with, cross-team interactions | Collaboration patterns |
| **Expertise** | Technologies used, complexity handled, leadership | Expertise identification |
| **Experience** | Years in role, years per technology | Proficiency estimation |
| **Activity** | Last active date, frequency, consistency | Engagement tracking |

**Sample User Intelligence Profile**:

```json
{
  "username": "sarah.chen",
  "email": "sarah.chen@company.com",
  "role": "developer",
  "experience_level": "Expert",
  "years_experience": 8,
  "team_id": "team-abc-123",
  
  "skills": [
    {"skill": "Python", "level": "Expert", "years": 8},
    {"skill": "Go", "level": "Expert", "years": 8},
    {"skill": "APIs", "level": "Expert", "years": 9}
  ],
  
  "contributions": {
    "documents_created": 5,
    "documents_updated": 12,
    "documents_commented": 11,
    "total_interactions": 28
  },
  
  "github_metrics": {
    "prs_authored": 5,
    "prs_reviewed": 12,
    "lines_added": 4500,
    "files_touched": 87,
    "review_quality_score": 0.85
  },
  
  "jira_metrics": {
    "tickets_reported": 8,
    "tickets_assigned": 15,
    "story_points": 120,
    "resolution_speed": "fast"
  },
  
  "confluence_metrics": {
    "pages_authored": 3,
    "pages_edited": 7,
    "documentation_quality": 0.78,
    "spaces": ["Engineering", "API Docs"]
  },
  
  "sme_score": 0.82,
  "collaboration_score": 0.75
}
```

### 7.6 Integration with Expert-Finder

**Expert-Finder Service Integration Flow**:

```
User Intelligence Data → User-Store → Expert-Finder → Planning Service
```

**Integration Points**:

1. **Data Source**: Expert-finder queries user-store for user metadata
2. **Search Capabilities**:
   - Natural language queries ("Who knows OAuth 2.0?")
   - Topic-based search (Python experts, React experts)
   - SME identification (authentication experts, infrastructure experts)
   - Teammate discovery (who has worked together)
   - Team expertise overview (team skill matrix)

3. **Planning Service Usage**:
   - Section 10 (SME & Contacts) uses expert-finder recommendations
   - Technology coverage analysis
   - Knowledge gap identification
   - Pairing suggestions based on complementary skills

4. **User & Team Report Usage**:
   - Team member profiles with real expertise data
   - Skill matrix populated from user-store
   - Collaboration insights from document relationships

**Example Expert Query**:
```bash
# Find Python experts
curl 'http://localhost:5160/experts/by-topic/Python?max_results=5'

# Returns users from user-store with Python skills, ranked by:
# - Years of experience
# - Number of Python-related documents
# - Code contribution metrics
# - Review quality in Python projects
```

---

## 8. Data Persistence Statistics

### 8.1 Current Demo Data


| Store | Data Type | Count | Status |
|-------|-----------|-------|--------|
| **doc_store** | Historical Documents | 14 | ✅ |
| **prompt_store** | Workflow Prompts | 8 | ✅ |
| **external-service-store** | Discovered Services | 16 | ✅ |
| **memory-agent** | Workflow Contexts | 5 | ✅ |
| **user-store** | Team Members | 6 | ✅ |

**Status Legend:**
- ✅ = Data successfully persisted
- ⚠️ = No data persisted (service not running, schema error, or other issue)

**Note on Zero Counts:**
If a store shows `0` with ⚠️ status, it indicates one of the following:
- **Service not running:** Start the service to enable persistence (doc_store, prompt_store, external-service-store)
- **Schema validation error:** Check console output for 422 errors indicating schema mismatches
- **Connection error:** Verify service URLs and network connectivity

To enable full persistence, start all required services:
```bash
# Start doc_store
cd services/doc_store && python main.py

# Start prompt_store  
cd services/prompt_store && python main.py

# Start external-service-store
cd services/external-service-store && python main.py

# Start memory-agent (if not running)
cd services/memory-agent && python main.py
```

### 6.2 Service Discovery Metrics

- **Documents Analyzed:** 24
- **Services Discovered:** 16
- **Services Stored:** 16
- **Document-Service Links:** 66
- **Discovery Confidence:** 0.98

### 6.3 Data Growth Over Time

```
Initial State (Before Demo):
  doc_store: 0 documents
  prompt_store: 0 prompts
  external-service-store: 0 services
  memory-agent: 0 contexts

After Demo Run:
  doc_store: 14 documents (+14)
  prompt_store: 8 prompts (+8)
  external-service-store: 16 services (+16)
  memory-agent: 5 contexts (+5)
  
→ Knowledge base grows with each demo run
→ Historical context becomes richer
→ Service catalog becomes more comprehensive
```

---

## 9. Visual Architecture Diagram

### 9.1 Complete Ecosystem Data Flow

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                    EXTERNAL SOURCES (Simulated)                               │
│                                                                               │
│        ┌──────────┐         ┌──────────┐         ┌──────────┐                │
│        │   Jira   │         │Confluence│         │  GitHub  │                │
│        │ Tickets  │         │   Docs   │         │   PRs    │                │
│        └────┬─────┘         └────┬─────┘         └────┬─────┘                │
│             │                    │                     │                      │
└─────────────┼────────────────────┼─────────────────────┼──────────────────────┘
              │                    │                     │
              └────────────────────┴─────────────────────┘
                                   │
                                   ▼
                      ┌────────────────────────┐
                      │   Demo Data Generator  │
                      │                        │
                      │ • Generate Jira        │
                      │ • Generate Confluence  │
                      │ • Generate GitHub      │
                      └───────────┬────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
    ┌──────────────┐      ┌──────────────┐     ┌──────────────┐
    │  doc_store   │      │Service       │     │ prompt_store │
    │   (SQLite)   │      │Discovery     │     │   (SQLite)   │
    │              │      │Engine        │     │              │
    │ Save         │      │              │     │ Save         │
    │ Historical   │      │ Extract      │     │ Workflow     │
    │ Documents    │      │ Services     │     │ Prompts      │
    └──────┬───────┘      └──────┬───────┘     └──────┬───────┘
           │                     │                     │
           │                     ▼                     │
           │           ┌──────────────────┐            │
           │           │external-service- │            │
           │           │     store        │            │
           │           │   (SQLite)       │            │
           │           │                  │            │
           │           │ Store Discovered │            │
           │           │ Services +       │            │
           │           │ Doc Linkings     │            │
           │           └─────────┬────────┘            │
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Workflow Orchestrator│
                    │                        │
                    │  Executes Workflows:   │
                    │  A, B, C, D, E         │
                    └───────────┬────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │user-store│ │ memory-  │ │  Report  │
            │ (SQLite) │ │  agent   │ │Generator │
            │          │ │(Redis+SQL)│ │          │
            │Team &    │ │          │ │ 4 Reports│
            │Skills    │ │Workflow  │ │Generated │
            │Data      │ │Contexts  │ │          │
            └──────────┘ └──────────┘ └──────────┘
```

### 7.2 Service Discovery Flow Detail

```
Historical Documents (doc_store)
        │
        ├──> Jira Tickets
        │    │
        │    ├──> Regex Pattern Matching
        │    ├──> Tech Stack Extraction
        │    └──> Keyword Analysis
        │              │
        │              └──> Services: ["Scala", "HTTP4s", "Circe"]
        │
        ├──> Confluence Docs
        │    │
        │    ├──> Title Analysis
        │    ├──> Tag Extraction
        │    └──> Section Analysis
        │              │
        │              └──> Services: ["PostgreSQL", "Flyway"]
        │
        └──> GitHub PRs
             │
             ├──> Description Parsing
             ├──> Tech Stack Tags
             └──> Commit Message Analysis
                       │
                       └──> Services: ["Docker", "Kubernetes"]
                                │
                                ▼
                       Aggregate & Deduplicate
                                │
                                ├──> Merge duplicate services
                                ├──> Calculate confidence scores
                                └──> Track source documents
                                         │
                                         ▼
                            Store in external-service-store
                                         │
                                         ├──> Create service entries
                                         ├──> Link to source documents
                                         └──> Index by type/technology
```

---

## 10. Related Reports & Documentation

**Navigate to other reports for complete picture:**

- **[Planning Service Report](./Planning_Service_Report.md)**  
  Production planning output with service validation

- **[Behind-the-Scenes Report](./Behind_the_Scenes_Report.md)**  
  Complete demo execution details with persistence stats

- **[Ecosystem Validation Report](./Ecosystem_Validation_Report.md)**  
  Proof of live code execution and database interactions

- **This Report (Data Architecture)**  
  In-depth analysis of data stores, schemas, and service relationships

- **[Main README](../README.md)**  
  Demo overview and quick start guide

---

## 11. Key Insights

### 11.1 Data Architecture Highlights

1. **Multi-Store Architecture:** 5 specialized data stores working in concert
2. **Intelligent Linkings:** Automatic discovery and linking of services to documents
3. **Context Accumulation:** Workflow history grows over time for better predictions
4. **Source-of-Truth Pattern:** Each store is authoritative for its domain
5. **Scalable Design:** Architecture supports growing data volumes

### 9.2 Service Discovery Success

- **16 services** discovered from 24 documents
- **66 total mentions** across all documents
- **16 unique services** cataloged
- **66 document-service linkings** established

### 9.3 Integration Achievements

1. ✅ Historical documents automatically analyzed for services
2. ✅ Services stored in external-service-store with metadata
3. ✅ Document-service linkings created for traceability
4. ✅ Workflow prompts persist across executions
5. ✅ Execution contexts stored for future analysis
6. ✅ Complete data provenance maintained

---

**Data Architecture Analysis Complete**  
**System:** LLM Documentation Ecosystem - Phase 9  
**Stores Analyzed:** 5 data stores  
**Services Discovered:** 16  
**Linkings Created:** 66  
**Generated:** 2025-10-04 06:26:00 UTC
