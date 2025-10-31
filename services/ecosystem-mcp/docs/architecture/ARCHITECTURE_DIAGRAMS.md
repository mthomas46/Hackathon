# Ecosystem MCP - Architecture Diagrams

**Date:** October 28, 2025  
**Version:** 1.0  
**Status:** Comprehensive Architecture Documentation

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Ingestion Pipeline](#ingestion-pipeline)
3. [RAG Query Flow](#rag-query-flow)
4. [Temporal RAG System](#temporal-rag-system)
5. [Caching Architecture](#caching-architecture)
6. [Database Schema](#database-schema)
7. [Deployment Architecture](#deployment-architecture)
8. [Error Handling & Resilience](#error-handling--resilience)

---

## High-Level Architecture

### System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Tool]
        Dashboard[Dashboard UI]
        API_Client[API Clients]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Server]
        Routes[API Routes]
        Middleware[Middleware]
    end
    
    subgraph "Service Layer"
        RAG[RAG Service]
        Temporal[Temporal RAG]
        Ingest[Ingestion Service]
        Embedding[Embedding Service]
    end
    
    subgraph "Storage Layer"
        Postgres[(PostgreSQL)]
        ChromaDB[(ChromaDB)]
        Redis[(Redis)]
    end
    
    subgraph "LLM Layer"
        Desktop[Desktop Ollama]
        Docker_Ollama[Docker Ollama]
        FastEmbed[FastEmbed Service]
    end
    
    CLI --> FastAPI
    Dashboard --> FastAPI
    API_Client --> FastAPI
    
    FastAPI --> Middleware
    Middleware --> Routes
    Routes --> RAG
    Routes --> Temporal
    Routes --> Ingest
    
    RAG --> Postgres
    RAG --> ChromaDB
    RAG --> Redis
    RAG --> Desktop
    
    Temporal --> Postgres
    Temporal --> ChromaDB
    Temporal --> Desktop
    
    Ingest --> Postgres
    Ingest --> ChromaDB
    Ingest --> Embedding
    Ingest --> Redis
    
    Embedding --> FastEmbed
    Embedding --> Docker_Ollama
```

---

## Ingestion Pipeline

### Complete Ingestion Flow

```mermaid
graph LR
    subgraph "Input"
        Repo[Git Repository]
    end
    
    subgraph "Stage 1: Discovery"
        Git[Git Service]
        Files[File Scanner]
        Git --> Files
    end
    
    subgraph "Stage 2: Processing"
        Norm[Content Normalizer]
        Extract[Metadata Extractor]
        Files --> Norm
        Files --> Extract
    end
    
    subgraph "Stage 3: Embedding"
        Batch[Batch Processor]
        FastE[FastEmbed]
        Ollama[Ollama]
        Norm --> Batch
        Batch --> FastE
        Batch --> Ollama
    end
    
    subgraph "Stage 4: Storage"
        PG[(PostgreSQL)]
        Chroma[(ChromaDB)]
        FastE --> PG
        FastE --> Chroma
        Ollama --> PG
        Ollama --> Chroma
    end
    
    subgraph "Stage 5: Indexing"
        Cache[(Redis Cache)]
        Index[Search Index]
        PG --> Cache
        Chroma --> Index
    end
    
    Repo --> Git
```

### Ingestion Modes

```mermaid
graph TB
    Start[Start Ingestion]
    
    Start --> Mode{Mode?}
    
    Mode -->|Snapshot| Snapshot[Snapshot Mode]
    Mode -->|Enriched| Enriched[Enriched Mode]
    Mode -->|Full| Full[Full History Mode]
    Mode -->|Incremental| Incremental[Incremental Mode]
    
    Snapshot --> Files1[Scan Current Files]
    Files1 --> Process1[Process Files]
    
    Enriched --> Git1[Read Git Metadata]
    Git1 --> Files2[Scan Current Files]
    Files2 --> Enrich[Enrich with Git Data]
    Enrich --> Process2[Process Files]
    
    Full --> Commits[Read All Commits]
    Commits --> Process3[Process Each Commit]
    
    Incremental --> LastCommit[Find Last Commit]
    LastCommit --> NewCommits[Get New Commits]
    NewCommits --> Process4[Process New Files]
    
    Process1 --> Store[Store in Database]
    Process2 --> Store
    Process3 --> Store
    Process4 --> Store
    
    Store --> Done[Ingestion Complete]
```

---

## RAG Query Flow

### Standard RAG Query

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Cache
    participant ChromaDB
    participant Ollama
    participant Postgres
    
    Client->>API: POST /api/v1/query
    API->>Cache: Check cache
    
    alt Cache Hit
        Cache-->>API: Return cached result
        API-->>Client: Return answer
    else Cache Miss
        API->>ChromaDB: Vector search
        ChromaDB-->>API: Return documents
        API->>Postgres: Get metadata
        Postgres-->>API: Return metadata
        API->>Ollama: Synthesize answer
        Ollama-->>API: Return answer
        API->>Cache: Store result
        API-->>Client: Return answer
    end
```

### Multi-Pass RAG Query

```mermaid
graph TB
    Start[Multi-Pass Query]
    
    Start --> Gen[Generate Sub-Questions]
    Gen --> Section1[Section 1]
    Gen --> Section2[Section 2]
    Gen --> Section3[Section 3]
    
    Section1 --> Q1[Query 1]
    Section1 --> Q2[Query 2]
    Section1 --> Q3[Query 3]
    
    Section2 --> Q4[Query 4]
    Section2 --> Q5[Query 5]
    Section2 --> Q6[Query 6]
    
    Section3 --> Q7[Query 7]
    Section3 --> Q8[Query 8]
    Section3 --> Q9[Query 9]
    
    Q1 --> RAG1[RAG Query]
    Q2 --> RAG2[RAG Query]
    Q3 --> RAG3[RAG Query]
    Q4 --> RAG4[RAG Query]
    Q5 --> RAG5[RAG Query]
    Q6 --> RAG6[RAG Query]
    Q7 --> RAG7[RAG Query]
    Q8 --> RAG8[RAG Query]
    Q9 --> RAG9[RAG Query]
    
    RAG1 --> Synth1[Synthesize Section 1]
    RAG2 --> Synth1
    RAG3 --> Synth1
    
    RAG4 --> Synth2[Synthesize Section 2]
    RAG5 --> Synth2
    RAG6 --> Synth2
    
    RAG7 --> Synth3[Synthesize Section 3]
    RAG8 --> Synth3
    RAG9 --> Synth3
    
    Synth1 --> Final[Final Synthesis]
    Synth2 --> Final
    Synth3 --> Final
    
    Final --> Result[Return Comprehensive Answer]
```

---

## Temporal RAG System

### Timeline Architecture

```mermaid
graph LR
    subgraph "Timeline Layer"
        TL[Timeline Model]
        TP[Time Periods]
        TL --> TP
    end
    
    subgraph "Document Layer"
        Doc[Documents]
        Meta[Git Metadata]
        Doc --> Meta
    end
    
    subgraph "Query Layer"
        DateRange[Date Range Query]
        PointTime[Point-in-Time Query]
        Evolution[Evolution Query]
    end
    
    TL --> DateRange
    TL --> PointTime
    TL --> Evolution
    
    DateRange --> Doc
    PointTime --> Doc
    Evolution --> Doc
    
    Doc --> Result[Temporal Results]
```

### Temporal Query Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Temporal
    participant Postgres
    participant ChromaDB
    participant Ollama
    
    Client->>API: POST /api/v1/temporal/query/date-range
    API->>Temporal: Process temporal query
    Temporal->>Postgres: Get timeline + periods
    Postgres-->>Temporal: Return timeline data
    Temporal->>ChromaDB: Vector search with date filter
    ChromaDB-->>Temporal: Return documents
    Temporal->>Postgres: Get temporal metadata
    Postgres-->>Temporal: Return metadata
    Temporal->>Ollama: Synthesize with temporal context
    Ollama-->>Temporal: Return answer
    Temporal-->>API: Return temporal result
    API-->>Client: Return answer
```

---

## Caching Architecture

### Multi-Level Cache

```mermaid
graph TB
    Request[Incoming Request]
    
    Request --> L1{L1 Cache<br/>Memory}
    
    L1 -->|Hit| Return1[Return Result]
    L1 -->|Miss| L2{L2 Cache<br/>Redis}
    
    L2 -->|Hit| Promote[Promote to L1]
    L2 -->|Miss| Database{Database}
    
    Promote --> Return2[Return Result]
    
    Database -->|Hit| Cache[Cache in L2 & L1]
    Database -->|Miss| Generate[Generate Result]
    
    Cache --> Return3[Return Result]
    Generate --> Store[Store in DB + Cache]
    Store --> Return4[Return Result]
    
    Return1 --> Stats[Update Stats]
    Return2 --> Stats
    Return3 --> Stats
    Return4 --> Stats
```

### Cache Strategy

```mermaid
graph LR
    subgraph "Cache Types"
        RAG[RAG Cache<br/>TTL: 30min]
        Embed[Embedding Cache<br/>TTL: 1hr]
        Search[Search Cache<br/>TTL: 15min]
        Meta[Metadata Cache<br/>TTL: 5min]
    end
    
    subgraph "Invalidation"
        TimeExpiry[Time-based Expiry]
        EventBased[Event-based Invalidation]
        Manual[Manual Clear]
    end
    
    RAG --> TimeExpiry
    Embed --> TimeExpiry
    Search --> TimeExpiry
    Meta --> TimeExpiry
    
    RAG --> EventBased
    Embed --> EventBased
    
    RAG --> Manual
    Embed --> Manual
    Search --> Manual
    Meta --> Manual
```

---

## Database Schema

### Core Tables

```mermaid
erDiagram
    IngestionJob ||--o{ Document : creates
    Document ||--o{ GitCommit : tracked_by
    Document ||--o{ Embedding : has
    Timeline ||--o{ TimePeriod : contains
    Document }o--|| Repository : belongs_to
    
    IngestionJob {
        uuid id PK
        string repo_path
        string mode
        string status
        json stats
        timestamp created_at
        timestamp completed_at
    }
    
    Document {
        uuid id PK
        uuid repo_id FK
        string file_path
        text content
        string content_hash
        json metadata
        timestamp git_date
        timestamp created_at
    }
    
    GitCommit {
        uuid id PK
        string sha
        string author
        string message
        timestamp commit_date
        json metadata
    }
    
    Embedding {
        uuid id PK
        uuid document_id FK
        vector embedding
        string model
        int dimensions
    }
    
    Timeline {
        uuid id PK
        string name
        timestamp start_date
        timestamp end_date
    }
    
    TimePeriod {
        uuid id PK
        uuid timeline_id FK
        string name
        timestamp start_date
        timestamp end_date
    }
    
    Repository {
        uuid id PK
        string path
        string name
        json metadata
    }
```

---

## Deployment Architecture

### Docker Compose Stack

```mermaid
graph TB
    subgraph "Application Services"
        API[ecosystem-mcp<br/>Port 8002]
        Dashboard[dashboard<br/>Port 8501]
        Worker[ingestion-worker]
        Embedding[embedding-service<br/>Port 8001]
    end
    
    subgraph "Data Services"
        Postgres[(PostgreSQL<br/>Port 5432)]
        Redis[(Redis<br/>Port 6379)]
        ChromaDB[(ChromaDB<br/>Port 8000)]
    end
    
    subgraph "LLM Services"
        Ollama[Ollama<br/>Port 11434]
        FastE[FastEmbed<br/>internal)]
    end
    
    API --> Postgres
    API --> Redis
    API --> ChromaDB
    API --> Ollama
    
    Dashboard --> API
    
    Worker --> Redis
    Worker --> Postgres
    Worker --> ChromaDB
    
    Embedding --> FastE
    Embedding --> Ollama
    
    API --> Embedding
    Worker --> Embedding
```

### Volume Mounts

```mermaid
graph LR
    subgraph "Host"
        Repo[/path/to/repo]
        Data[./data]
    end
    
    subgraph "Container"
        App[/app]
        ChromaData[/chroma_db]
        PGData[/var/lib/postgresql/data]
    end
    
    Repo -->|read-only| App
    Data -->|read-write| ChromaData
    Data -->|read-write| PGData
```

---

## Error Handling & Resilience

### Circuit Breaker Pattern

```mermaid
stateDiagram-v2
    [*] --> Closed: Initial State
    
    Closed --> Open: Error Threshold<br/>Exceeded
    Open --> HalfOpen: Timeout Elapsed
    HalfOpen --> Closed: Success
    HalfOpen --> Open: Failure
    
    Closed: Normal Operation<br/>Requests Pass Through
    Open: Reject Requests<br/>Return Error
    HalfOpen: Test Single Request
```

### Retry Strategy

```mermaid
graph TB
    Request[Request]
    
    Request --> Attempt1[Attempt 1]
    Attempt1 --> Success1{Success?}
    
    Success1 -->|Yes| Return1[Return Result]
    Success1 -->|No| Transient{Transient<br/>Error?}
    
    Transient -->|Yes| Wait1[Wait 1s]
    Transient -->|No| Return2[Return Error]
    
    Wait1 --> Attempt2[Attempt 2]
    Attempt2 --> Success2{Success?}
    
    Success2 -->|Yes| Return3[Return Result]
    Success2 -->|No| Wait2[Wait 2s]
    
    Wait2 --> Attempt3[Attempt 3]
    Attempt3 --> Success3{Success?}
    
    Success3 -->|Yes| Return4[Return Result]
    Success3 -->|No| Return5[Return Error]
```

### Fallback Architecture

```mermaid
graph LR
    Request[Request]
    
    Request --> Primary[Primary Service]
    Primary --> Check1{Success?}
    
    Check1 -->|Yes| Result1[Return Result]
    Check1 -->|No| Fallback1[Fallback Service]
    
    Fallback1 --> Check2{Success?}
    
    Check2 -->|Yes| Result2[Return Result]
    Check2 -->|No| Error[Return Error]
```

---

## Performance Optimizations

### Request Flow with Optimizations

```mermaid
graph TB
    Request[Incoming Request]
    
    Request --> RateLimit{Rate Limit<br/>Check}
    RateLimit -->|Reject| Error429[429 Too Many Requests]
    RateLimit -->|Accept| Cache{Cache<br/>Check}
    
    Cache -->|Hit| Return1[Return Cached]
    Cache -->|Miss| CircuitBreaker{Circuit<br/>Breaker}
    
    CircuitBreaker -->|Open| Error503[503 Service Unavailable]
    CircuitBreaker -->|Closed| Process[Process Request]
    
    Process --> Parallel{Can<br/>Parallelize?}
    
    Parallel -->|Yes| Batch[Batch Processing]
    Parallel -->|No| Sequential[Sequential Processing]
    
    Batch --> Result1[Combine Results]
    Sequential --> Result2[Return Result]
    
    Result1 --> Store[Store in Cache]
    Result2 --> Store
    
    Store --> Return2[Return Result]
```

---

## Monitoring & Observability

### Metrics Collection

```mermaid
graph LR
    subgraph "Application"
        API[API Service]
        Worker[Worker Service]
    end
    
    subgraph "Metrics"
        Prometheus[Prometheus<br/>Metrics]
        Logs[Application<br/>Logs]
        Traces[Distributed<br/>Tracing]
    end
    
    subgraph "Dashboards"
        Grafana[Grafana<br/>Dashboard]
        Kibana[Kibana<br/>Logs]
    end
    
    API --> Prometheus
    API --> Logs
    API --> Traces
    
    Worker --> Prometheus
    Worker --> Logs
    
    Prometheus --> Grafana
    Logs --> Kibana
```

---

## Development Workflow

### CI/CD Pipeline

```mermaid
graph LR
    Commit[Git Commit]
    
    Commit --> Lint[Linting]
    Lint --> Test[Unit Tests]
    Test --> Build[Docker Build]
    Build --> Integration[Integration Tests]
    Integration --> Deploy{Deploy?}
    
    Deploy -->|Dev| DevEnv[Dev Environment]
    Deploy -->|Staging| StagingEnv[Staging Environment]
    Deploy -->|Prod| ProdEnv[Production Environment]
    
    DevEnv --> Monitor1[Monitor]
    StagingEnv --> Monitor2[Monitor]
    ProdEnv --> Monitor3[Monitor]
```

---

## Security Architecture

### Authentication & Authorization (Future)

```mermaid
graph TB
    Request[Incoming Request]
    
    Request --> Auth{Authenticated?}
    Auth -->|No| Login[Login Required]
    Auth -->|Yes| RBAC{Authorized?}
    
    RBAC -->|No| Forbidden[403 Forbidden]
    RBAC -->|Yes| Process[Process Request]
    
    Login --> OAuth[OAuth Provider]
    OAuth --> Tokens[JWT Tokens]
    Tokens --> Cache[Token Cache]
```

---

## Additional Resources

- [API Documentation](../api/EXAMPLES.md)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)
- [Testing Guide](../development/TESTING_GUIDE.md)
- [Performance Guide](./RAG_PERFORMANCE_OPTIMIZATION_GUIDE.md)

---

**Last Updated:** October 28, 2025  
**Version:** 1.0  
**Maintainer:** Ecosystem MCP Team

