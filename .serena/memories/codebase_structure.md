# Codebase Structure and Architecture

## Directory Structure
```
├── services/                    # All microservices
│   ├── shared/                 # Common utilities and patterns
│   ├── orchestrator/           # Control plane (port 5099)
│   ├── doc-store/             # Document storage (port 5087)
│   ├── source-agent/          # Data ingestion (port 5000)
│   ├── analysis-service/      # AI analysis (port 5020)
│   ├── prompt-store/          # Prompt management (port 5110)
│   ├── interpreter/           # NLP processing (port 5120)
│   ├── summarizer-hub/        # LLM abstraction (port 5060)
│   ├── cli/                   # Command-line interface
│   ├── frontend/              # Web UI
│   └── [other services]/
├── tests/                      # Test suite
│   ├── unit/<service>/        # Service-specific unit tests
│   ├── integration/           # Cross-service integration tests
│   └── helpers/               # Test utilities
├── docs/                      # Documentation
│   ├── architecture/          # System design docs
│   ├── development/           # Developer guides
│   ├── guides/                # User guides
│   └── operations/            # Deployment/ops docs
├── config/                    # Configuration files
├── infrastructure/            # Infrastructure as code
└── scripts/                   # Utility scripts
```

## Service Architecture Pattern
Each service follows a consistent structure:
```
services/<service>/
├── main.py                    # FastAPI app entry point
├── config.yaml               # Service configuration
├── routes/                    # API route handlers
├── modules/                   # Business logic modules
└── README.md                  # Service documentation
```

## Data Flow Patterns

### Primary Workflows
1. **Analysis Query**: CLI/Frontend → Interpreter → Orchestrator → Analysis/Doc Store
2. **Data Ingestion**: Source Agent → Doc Store (with optional analysis)
3. **Prompt Management**: Services/CLI → Prompt Store
4. **Document Storage**: Various sources → Doc Store → Search/Retrieval

### Inter-Service Communication
- HTTP-based microservices communication
- Service discovery via Orchestrator registry
- Event-driven workflows with saga patterns
- Circuit breaker and retry patterns via shared clients

## Shared Components (`services/shared/`)
- **clients.py**: HTTP client utilities with resilience patterns
- **envelopes.py**: Standard request/response envelope formats
- **config.py**: Configuration loading and environment handling
- **health.py**: Health check utilities
- **middleware.py**: Common FastAPI middleware
- **responses.py**: Standard response patterns
- **logging.py**: Structured logging utilities
- **models.py**: Shared data models
- **constants.py**: Project-wide constants

## Testing Structure
- Unit tests mirror service structure under `tests/unit/<service>/`
- Integration tests in `tests/integration/`
- Comprehensive pytest configuration with markers
- Test helpers for common patterns and assertions