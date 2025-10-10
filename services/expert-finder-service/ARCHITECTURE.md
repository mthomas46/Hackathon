# Expert Finder Service - Architecture & Workflows

**Version**: 1.0.0  
**Last Updated**: October 10, 2025  
**Status**: ✅ Production Ready

---

## 📑 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Domain-Driven Design (DDD)](#domain-driven-design-ddd)
3. [Service Architecture](#service-architecture)
4. [Data Flow](#data-flow)
5. [Workflow Diagrams](#workflow-diagrams)
6. [Integration Patterns](#integration-patterns)
7. [Scoring Algorithm](#scoring-algorithm)
8. [Deployment Architecture](#deployment-architecture)

---

## 🏗️ Architecture Overview

### **High-Level System Context**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Hackathon Ecosystem                         │
│                                                                 │
│  ┌──────────┐      ┌──────────────────┐      ┌──────────────┐ │
│  │ Frontend │─────▶│  Expert Finder   │◀─────│  CLI Tool    │ │
│  └──────────┘      │     Service      │      └──────────────┘ │
│                    │   (Port 5160)    │                        │
│  ┌──────────┐      └────────┬─────────┘      ┌──────────────┐ │
│  │ Project  │──────────────▲│▲                │   Unified    │ │
│  │ Planning │              │││                │   Dashboard  │ │
│  └──────────┘              │││                └──────────────┘ │
│                            │││                                 │
│         Dependencies       │││                                 │
│                            │││                                 │
│  ┌──────────┐  ┌──────────┴┴┴────────┐  ┌──────────────────┐ │
│  │   User   │  │    Doc Store        │  │ External Service │ │
│  │  Store   │  │   (Port 5087)       │  │     Store        │ │
│  │(Port5150)│  │   [Optional]        │  │   (Port 5140)    │ │
│  │[Required]│  └─────────────────────┘  │   [Optional]     │ │
│  └──────────┘                           └──────────────────┘ │
│       ▲                                                        │
│       │                                                        │
│  ┌────┴──────┐         ┌──────────────┐                      │
│  │   Redis   │         │ Log Collector│                       │
│  │  (Cache)  │         │  (Port 5050) │                       │
│  └───────────┘         │  [Optional]  │                       │
│                        └──────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### **Service Characteristics**

- **Type**: Query Service / Search Engine
- **Architecture**: Domain-Driven Design (DDD)
- **Communication**: Synchronous HTTP/REST
- **State**: Stateless (no persistent storage)
- **Scalability**: Horizontal (multiple instances)
- **Availability**: High (graceful degradation)

---

## 🎯 Domain-Driven Design (DDD)

### **DDD Layers**

```
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ FastAPI Application (main.py)                          │  │
│  │  • CORS Middleware                                     │  │
│  │  • Request/Response Validation                         │  │
│  │  • Error Handling                                      │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Routes                                                 │  │
│  │  • standard_routes.py (health, about-me, etc.)       │  │
│  │  • expert_routes.py (business endpoints)              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Use Cases (Orchestration)                              │  │
│  │  • FindExpertsUseCase                                  │  │
│  │  • IdentifySMEsUseCase                                 │  │
│  │  • FindTeammatesUseCase                                │  │
│  │  • AggregateTeamExpertiseUseCase                       │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Entities (Core Business Objects)                       │  │
│  │  • Expert                                              │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Value Objects (Immutable)                              │  │
│  │  • ExpertQuery                                         │  │
│  │  • ExpertMatch                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Domain Services (Business Logic)                       │  │
│  │  • RelevanceScoringService                            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Repositories (Data Access)                             │  │
│  │  • UserRepository                                      │  │
│  │  • DocumentRepository                                  │  │
│  │  • ServiceRepository                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Configuration                                          │  │
│  │  • Settings (pydantic-settings)                       │  │
│  │  • Environment Variables                               │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ External Integrations                                  │  │
│  │  • HTTP Client (httpx + tenacity)                     │  │
│  │  • Log Collector Client                                │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### **Key DDD Patterns**

1. **Repository Pattern**: Abstraction for data access
2. **Use Case Pattern**: Application-level orchestration
3. **Value Objects**: Immutable domain concepts
4. **Domain Services**: Complex business logic
5. **Dependency Injection**: Loose coupling

---

## 🔧 Service Architecture

### **Component Diagram**

```
expert-finder-service/
│
├─ presentation/              # API Layer
│  ├─ routes/
│  │  ├─ standard_routes.py  # /health, /about-me, /endpoints
│  │  └─ expert_routes.py    # /api/v1/find-experts, etc.
│  └─ models/                 # Request/Response DTOs
│
├─ application/               # Use Cases
│  └─ use_cases/
│     ├─ find_experts_use_case.py          # Core search logic
│     ├─ identify_smes_use_case.py         # SME identification
│     ├─ find_teammates_use_case.py        # Teammate search
│     └─ aggregate_team_expertise_use_case.py # Team analysis
│
├─ domain/                    # Business Logic
│  ├─ entities/
│  │  └─ expert.py           # Expert aggregate root
│  ├─ value_objects/
│  │  ├─ expert_query.py     # Search query
│  │  └─ expert_match.py     # Match result with score
│  └─ services/
│     └─ relevance_scoring_service.py # Scoring algorithm
│
├─ infrastructure/            # External Systems
│  ├─ repositories/
│  │  ├─ base_repository.py  # Shared HTTP logic
│  │  ├─ user_repository.py  # User-store integration
│  │  ├─ document_repository.py # Doc-store integration
│  │  └─ service_repository.py # Service-store integration
│  └─ config/
│     └─ settings.py         # Configuration management
│
└─ utils/                     # Shared Utilities
   ├─ validators.py          # Input validation
   ├─ transformers.py        # Data transformation
   └─ constants.py           # Constants
```

### **Dependency Flow**

```
┌─────────────┐
│    Client   │
└──────┬──────┘
       │ HTTP Request
       ▼
┌────────────────────────────┐
│  Presentation (FastAPI)    │
│  • Validation              │
│  • Error Handling          │
└──────┬─────────────────────┘
       │ DTO
       ▼
┌────────────────────────────┐
│  Application (Use Cases)   │
│  • Business Workflow       │
│  • Orchestration           │
└──────┬─────────────────────┘
       │ Domain Objects
       ▼
┌────────────────────────────┐
│  Domain (Business Logic)   │
│  • Scoring Algorithm       │
│  • Business Rules          │
└──────┬─────────────────────┘
       │ Data Requests
       ▼
┌────────────────────────────┐
│  Infrastructure (Repos)    │
│  • HTTP Clients            │
│  • External Services       │
└────────────────────────────┘
       │ HTTP
       ▼
┌────────────────────────────┐
│  External Services         │
│  • user-store              │
│  • doc-store               │
│  • service-store           │
└────────────────────────────┘
```

---

## 📊 Data Flow

### **Request Flow: Find Experts**

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ POST /api/v1/find-experts
     │ {query_text: "Python dev", limit: 10}
     ▼
┌─────────────────────────────────────┐
│ 1. Presentation Layer               │
│    - Validate request                │
│    - Parse JSON body                 │
│    - Create ExpertQuery value object │
└─────────────┬───────────────────────┘
              │ ExpertQuery
              ▼
┌─────────────────────────────────────┐
│ 2. Application Layer                │
│    FindExpertsUseCase.execute()      │
│    - Fetch candidates                │
│    - Enrich with metadata            │
│    - Score and rank                  │
│    - Filter by min_score             │
└─────────────┬───────────────────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
┌──────────────┐  ┌──────────────────┐
│ 3a. Fetch    │  │ 3b. Enrich       │
│ Candidates   │  │ Metadata         │
│              │  │                  │
│ UserRepo     │  │ DocRepo          │
│ .get_by_role │  │ .get_doc_count   │
│ .get_by_topic│  │                  │
│              │  │ ServiceRepo      │
│              │  │ .get_services    │
└──────┬───────┘  └────────┬─────────┘
       │                   │
       │ List[Expert]      │ Enriched Data
       │                   │
       └──────────┬────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 4. Domain Layer                     │
│    RelevanceScoringService          │
│    - Calculate role score            │
│    - Calculate topic score           │
│    - Calculate service score         │
│    - Calculate document score        │
│    - Combine with weights            │
│    - Generate explanations           │
└─────────────┬───────────────────────┘
              │ List[ExpertMatch]
              │ (sorted by score)
              ▼
┌─────────────────────────────────────┐
│ 5. Application Layer                │
│    - Filter by min_score             │
│    - Limit results                   │
│    - Format response                 │
└─────────────┬───────────────────────┘
              │ Response DTO
              ▼
┌─────────────────────────────────────┐
│ 6. Presentation Layer               │
│    - Serialize to JSON               │
│    - Add metadata                    │
│    - Return HTTP 200                 │
└─────────────┬───────────────────────┘
              │ JSON Response
              ▼
          ┌──────────┐
          │  Client  │
          └──────────┘
```

---

## 🔄 Workflow Diagrams

### **Workflow 1: Expert Discovery**

```
User searches for "Python backend developer"
│
├─ Step 1: Parse Query
│  ├─ Extract keywords: [Python, backend, developer]
│  ├─ Create ExpertQuery object
│  └─ Set query parameters (limit, min_score)
│
├─ Step 2: Fetch Candidates
│  ├─ Query user-store by role ("developer")
│  ├─ Query user-store by topic ("Python")
│  ├─ Deduplicate results
│  └─ Result: List of 50 candidate users
│
├─ Step 3: Enrich Candidates
│  ├─ For each candidate:
│  │  ├─ Fetch document count from doc-store
│  │  └─ Fetch service list from service-store
│  └─ Result: Enriched candidate list
│
├─ Step 4: Score Candidates
│  ├─ For each candidate:
│  │  ├─ Calculate role_score (0.3 weight)
│  │  ├─ Calculate topic_score (0.4 weight)
│  │  ├─ Calculate service_score (0.2 weight)
│  │  ├─ Calculate document_score (0.1 weight)
│  │  └─ overall_score = weighted sum
│  └─ Result: List of ExpertMatch objects
│
├─ Step 5: Filter & Sort
│  ├─ Filter by min_score (e.g., 0.7)
│  ├─ Sort by overall_score (descending)
│  ├─ Limit to top N results (e.g., 10)
│  └─ Result: Top 10 experts
│
└─ Step 6: Return Response
   ├─ Format as JSON
   ├─ Include scores and explanations
   └─ Return HTTP 200 OK
```

### **Workflow 2: SME Identification**

```
System needs to identify Python SMEs
│
├─ Step 1: Define SME Criteria
│  ├─ min_documents = 10 (proven contributions)
│  ├─ min_score = 0.8 (high expertise)
│  └─ topic = "Python"
│
├─ Step 2: Fetch All Experts
│  ├─ Query user-store for topic="Python"
│  └─ Result: All Python users
│
├─ Step 3: Filter by Document Count
│  ├─ Fetch document counts for all users
│  ├─ Filter users with >= 10 documents
│  └─ Result: Users with proven contributions
│
├─ Step 4: Score Remaining Candidates
│  ├─ Use standard scoring algorithm
│  ├─ Calculate overall_score
│  └─ Result: Scored candidates
│
├─ Step 5: Apply SME Thresholds
│  ├─ Filter by overall_score >= 0.8
│  ├─ Sort by score (descending)
│  ├─ Limit to top 5
│  └─ Result: Top 5 SMEs
│
└─ Step 6: Return SME List
   ├─ Format with detailed scores
   ├─ Include evidence (document count, topics, services)
   └─ Return HTTP 200 OK
```

### **Workflow 3: Team Formation**

```
Project needs 3 team members: Python, React, PostgreSQL
│
├─ Step 1: Parse Requirements
│  ├─ required_topics = ["Python", "React", "PostgreSQL"]
│  ├─ team_size = 3
│  └─ exclude_users = [current_team]
│
├─ Step 2: Find Candidates for Each Topic
│  ├─ Python experts: Query user-store
│  ├─ React experts: Query user-store
│  ├─ PostgreSQL experts: Query user-store
│  └─ Result: 3 candidate pools
│
├─ Step 3: Score All Candidates
│  ├─ Score for "Python"
│  ├─ Score for "React"
│  ├─ Score for "PostgreSQL"
│  └─ Result: Candidates with topic-specific scores
│
├─ Step 4: Optimize Team Composition
│  ├─ Find users covering multiple topics
│  ├─ Prefer users with broad expertise
│  ├─ Ensure all topics are covered
│  └─ Result: Optimal 3-person team
│
└─ Step 5: Return Recommendations
   ├─ Team member 1: Python + PostgreSQL expert
   ├─ Team member 2: React specialist
   ├─ Team member 3: Full-stack (all 3 topics)
   └─ Return HTTP 200 OK with team composition
```

---

## 🔗 Integration Patterns

### **Repository Pattern**

```
Use Case
   │
   │ calls
   ▼
UserRepository (Interface/Abstract)
   │
   │ implements
   ▼
UserRepository (Concrete)
   │
   │ uses
   ▼
BaseRepository (HTTP Client + Retry Logic)
   │
   │ HTTP GET/POST
   ▼
user-store (External Service)
```

### **Retry Pattern**

```
Request
   │
   ▼
┌─────────────────┐
│ Try 1           │───┐ Success ──▶ Return Response
└─────────────────┘   │
   │                  │
   │ Timeout/Error    │
   ▼                  │
┌─────────────────┐   │
│ Wait 1s         │   │
│ Try 2           │───┤ Success ──▶ Return Response
└─────────────────┘   │
   │                  │
   │ Timeout/Error    │
   ▼                  │
┌─────────────────┐   │
│ Wait 2s         │   │
│ Try 3 (final)   │───┤ Success ──▶ Return Response
└─────────────────┘   │
   │                  │
   │ Final Failure    │
   ▼                  │
Return Error 503      │
```

### **Graceful Degradation**

```
┌──────────────────────────────┐
│ Find Experts Request         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Query user-store (REQUIRED)  │
└──────────────┬───────────────┘
               │
           ┌───┴────┐
           │Success?│
           └───┬────┘
               │
      ┌────────┴────────┐
      │                 │
     YES               NO
      │                 │
      ▼                 ▼
┌─────────────┐   ┌────────────┐
│ Continue    │   │ Return 503 │
│ Processing  │   │ (Required) │
└─────┬───────┘   └────────────┘
      │
      ▼
┌──────────────────────────────┐
│ Query doc-store (OPTIONAL)   │
└──────────────┬───────────────┘
               │
           ┌───┴────┐
           │Success?│
           └───┬────┘
               │
      ┌────────┴────────┐
      │                 │
     YES               NO
      │                 │
      ▼                 ▼
┌─────────────┐   ┌────────────────┐
│ Enrich with │   │ Skip enrichment│
│ doc counts  │   │ Continue       │
└─────┬───────┘   └────────┬───────┘
      │                    │
      └────────┬───────────┘
               │
               ▼
┌──────────────────────────────┐
│ Return Results (200 OK)      │
└──────────────────────────────┘
```

---

## 📐 Scoring Algorithm

### **Multi-Factor Scoring Architecture**

```
ExpertQuery + Candidate Expert
         │
         ▼
┌──────────────────────────────────────┐
│ RelevanceScoringService              │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ 1. Role Scoring (30%)          │ │
│  │    - Exact match: 1.0          │ │
│  │    - Fuzzy match: 0.5-0.9      │ │
│  │    - No match: 0.0             │ │
│  └────────────┬───────────────────┘ │
│               │ role_score          │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │ 2. Topic Scoring (40%)         │ │
│  │    - Count matching topics     │ │
│  │    - Normalize by total topics │ │
│  │    - Fuzzy matching            │ │
│  └────────────┬───────────────────┘ │
│               │ topic_score         │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │ 3. Service Scoring (20%)       │ │
│  │    - Count matching services   │ │
│  │    - Weight by importance      │ │
│  │    - Normalize                 │ │
│  └────────────┬───────────────────┘ │
│               │ service_score       │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │ 4. Document Scoring (10%)      │ │
│  │    - Normalize document count  │ │
│  │    - Cap at maximum            │ │
│  │    - Logarithmic scaling       │ │
│  └────────────┬───────────────────┘ │
│               │ document_score      │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │ 5. Weighted Combination        │ │
│  │    overall = Σ(score × weight) │ │
│  │    - role × 0.3                │ │
│  │    - topic × 0.4               │ │
│  │    - service × 0.2             │ │
│  │    - document × 0.1            │ │
│  └────────────┬───────────────────┘ │
│               │ overall_score       │
│               ▼                     │
│  ┌────────────────────────────────┐ │
│  │ 6. Generate Explanation        │ │
│  │    - Top contributing factors  │ │
│  │    - Match quality label       │ │
│  │    - Evidence summary          │ │
│  └────────────┬───────────────────┘ │
└───────────────┼────────────────────┘
                │
                ▼
         ExpertMatch
      (with scores & explanation)
```

### **Scoring Example**

```
Candidate: "Alice Developer"
Query: "Python backend developer with FastAPI"

┌─────────────────────────────────────┐
│ Role Matching                       │
│   Candidate role: "Backend Developer"│
│   Query includes: "backend", "developer"│
│   Match: EXACT                      │
│   Role Score: 1.0 × 0.3 = 0.30      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Topic Matching                      │
│   Candidate topics: [Python, FastAPI, PostgreSQL]│
│   Query topics: [Python, FastAPI, backend]│
│   Matches: 2/3 topics               │
│   Topic Score: 0.95 × 0.4 = 0.38    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Service Experience                  │
│   Candidate services: [api-gateway, user-service]│
│   Query services: []                │
│   Matches: N/A (not specified)      │
│   Service Score: 0.5 × 0.2 = 0.10   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Document Contributions              │
│   Candidate docs: 25 documents      │
│   Normalized: 25/30 = 0.83          │
│   Document Score: 0.83 × 0.1 = 0.08 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Overall Score                       │
│   0.30 + 0.38 + 0.10 + 0.08 = 0.86  │
│   Match Quality: EXCELLENT          │
│   Explanation: "Strong match on Python│
│   and FastAPI expertise with proven │
│   contributions (25 documents)"     │
└─────────────────────────────────────┘
```

---

## 🚀 Deployment Architecture

### **Docker Deployment**

```
┌────────────────────────────────────────────────┐
│              Docker Host                       │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  expert-finder-service container         │ │
│  │                                          │ │
│  │  ┌────────────────────────────────────┐ │ │
│  │  │  Uvicorn (ASGI Server)             │ │ │
│  │  │  Port: 5160                        │ │ │
│  │  │                                    │ │ │
│  │  │  ┌──────────────────────────────┐ │ │ │
│  │  │  │  FastAPI Application         │ │ │ │
│  │  │  │  - Routes                    │ │ │ │
│  │  │  │  - Middleware                │ │ │ │
│  │  │  │  - Validation                │ │ │ │
│  │  │  └──────────────────────────────┘ │ │ │
│  │  │                                    │ │ │
│  │  │  Environment Variables:            │ │ │
│  │  │  - USER_STORE_URL                  │ │ │
│  │  │  - DOC_STORE_URL                   │ │ │
│  │  │  - SERVICE_PORT=5160               │ │ │
│  │  │                                    │ │ │
│  │  │  Health Check:                     │ │ │
│  │  │  curl localhost:5160/health        │ │ │
│  │  │  Interval: 30s, Timeout: 10s       │ │ │
│  │  └────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────┘ │
│                      │                         │
│                      │ Port Mapping            │
│                      │ 5160:5160               │
│                      ▼                         │
│  ┌──────────────────────────────────────────┐ │
│  │         Docker Network (hackathon_default)│ │
│  │                                          │ │
│  │  Services:                               │ │
│  │  - user-store:5150                       │ │
│  │  - doc-store:5087                        │ │
│  │  - external-service-store:5140           │ │
│  │  - log-collector:5050                    │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

### **Kubernetes Deployment** (Future)

```
┌──────────────────────────────────────────────────┐
│           Kubernetes Cluster                     │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Namespace: hackathon                      │ │
│  │                                            │ │
│  │  ┌──────────────────────────────────────┐ │ │
│  │  │  Service: expert-finder              │ │ │
│  │  │  Type: ClusterIP                     │ │ │
│  │  │  Port: 5160                          │ │ │
│  │  └────────┬─────────────────────────────┘ │ │
│  │           │                                │ │
│  │           │ Load Balance                   │ │
│  │           ▼                                │ │
│  │  ┌──────────────────────────────────────┐ │ │
│  │  │  Deployment: expert-finder           │ │ │
│  │  │  Replicas: 3                         │ │ │
│  │  │                                      │ │ │
│  │  │  ┌─────────┐  ┌─────────┐  ┌──────┐│ │ │
│  │  │  │ Pod 1   │  │ Pod 2   │  │Pod 3 ││ │ │
│  │  │  │ 5160    │  │ 5160    │  │5160  ││ │ │
│  │  │  └─────────┘  └─────────┘  └──────┘│ │ │
│  │  │                                      │ │ │
│  │  │  ConfigMap: expert-finder-config     │ │ │
│  │  │  Secret: expert-finder-secrets       │ │ │
│  │  └──────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

---

## 📈 Performance Architecture

### **Scaling Strategy**

```
Load Balancer
     │
     ├──▶ Instance 1 (expert-finder:5160)
     │    - Handles 50 req/s
     │    - Memory: 150 MB
     │    - CPU: 10%
     │
     ├──▶ Instance 2 (expert-finder:5160)
     │    - Handles 50 req/s
     │    - Memory: 150 MB
     │    - CPU: 10%
     │
     └──▶ Instance 3 (expert-finder:5160)
          - Handles 50 req/s
          - Memory: 150 MB
          - CPU: 10%

Total Capacity: 150 req/s
```

### **Caching Strategy** (Future)

```
Request
   │
   ▼
┌─────────────┐
│ Check Cache │───┐ Cache Hit ──▶ Return Cached Result
│  (Redis)    │   │                (< 10ms)
└─────────────┘   │
   │              │
   │ Cache Miss   │
   ▼              │
┌─────────────┐   │
│ Query       │   │
│ user-store  │   │
└─────┬───────┘   │
      │           │
      ▼           │
┌─────────────┐   │
│ Calculate   │   │
│ Scores      │   │
└─────┬───────┘   │
      │           │
      ▼           │
┌─────────────┐   │
│ Store in    │───┘
│ Cache (5min)│
└─────────────┘
      │
      ▼
   Return Result
```

---

## 🔐 Security Architecture

### **Security Layers**

```
┌──────────────────────────────────────┐
│  1. Network Security                 │
│     - HTTPS/TLS                      │
│     - API Gateway (future)           │
│     - Rate Limiting (future)         │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  2. Authentication (future)          │
│     - JWT Tokens                     │
│     - API Keys                       │
│     - OAuth2                         │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  3. Input Validation                 │
│     - Pydantic models                │
│     - Custom validators              │
│     - Sanitization                   │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  4. Business Logic                   │
│     - Authorization checks (future)  │
│     - Data access control (future)   │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  5. Audit Logging                    │
│     - Request logging                │
│     - Error tracking                 │
│     - No PII in logs                 │
└──────────────────────────────────────┘
```

---

## 📚 Related Documentation

- **README.md** - Service overview and quick start
- **TESTING_GUIDE.md** - Testing strategies and patterns
- **DOCKER_TEST_VALIDATION.md** - Docker testing guide
- **ECOSYSTEM_TEST_VALIDATION.md** - Ecosystem integration guide
- **API_PATTERNS.md** - API design patterns and best practices

---

**Last Updated**: October 10, 2025  
**Document Version**: 1.0.0  
**Status**: ✅ Production Ready

