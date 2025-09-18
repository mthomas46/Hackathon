# LLM Documentation Ecosystem - Documentation Index

<!--
LLM Processing Metadata:
- document_type: "documentation_index_and_navigation"
- content_focus: "comprehensive_documentation_catalog"
- key_concepts: ["documentation_structure", "guides", "architecture", "operations"]
- processing_hints: "Complete documentation catalog with clear navigation paths"
- cross_references: ["../README.md", "../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../docs/deployment/DEPLOYMENT_GUIDE.md"]
- navigation_structure: "hierarchical_sections_with_cross_references"
-->

## 📚 **Comprehensive Documentation Overview**

This documentation provides **complete guidance** for the LLM Documentation Ecosystem, from high-level architecture to detailed implementation patterns and service-specific guides. All documentation is **LLM-optimized** with semantic embeddings and cross-references.

### 🔍 **Quick Access - Key Documents**
- 📖 **[Master Living Document](../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md)** - Complete technical documentation with function summaries (2500+ lines)
- 🗺️ **[Documentation Hierarchy](../DOCUMENTATION_HIERARCHY.md)** - **NEW**: Complete documentation map and navigation guide
- 🏗️ **[Ecosystem Architecture](architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design and architectural patterns
- 🧭 **[Architecture Diagrams](architecture/ECOSYSTEM_ARCHITECTURE_DIAGRAMS.md)** - Context, container, and sequence diagrams
- 🚀 **[Deployment Guide](../docs/deployment/DEPLOYMENT_GUIDE.md)** - Production deployment with Docker orchestration
- 📊 **[Project Overview](../README.md)** - Complete service catalog and achievements

### 📋 **Documentation Categories & Processing Hints**

```yaml
# Document Processing Guidance for LLMs
documentation_structure:
  architecture_docs: "Technical implementation details with DDD patterns"
  guides_tutorials: "Step-by-step implementation and setup instructions"
  operations_docs: "Production deployment and maintenance procedures"
  reference_docs: "API specifications and technical references"
  
content_organization:
  depth_levels:
    - overview: "High-level concepts and ecosystem understanding"
    - detailed: "Implementation specifics and code examples"
    - reference: "API documentation and configuration details"
  
cross_reference_patterns:
  - "architecture → implementation → deployment"
  - "guides → operations → troubleshooting"
  - "services → testing → monitoring"
```

## 📖 Documentation Sections

### 🏗️ **[Architecture & Design](architecture/)**
- **[🌟 Ecosystem Architecture](architecture/ECOSYSTEM_ARCHITECTURE.md)** - **NEW**: Comprehensive system architecture with DDD patterns, service interactions, and deployment strategies
- **[Master Living Document](../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md)** - **NEW**: Authoritative source of truth for the entire ecosystem (Living Document)
- **[System Architecture](architecture/ARCHITECTURE.md)** - High-level system map, envelopes, flows
- **[Features & Interactions](architecture/FEATURES_AND_INTERACTIONS.md)** - Service features, interactions, and end-to-end flows
- **[Infrastructure Guide](architecture/INFRASTRUCTURE.md)** - Infrastructure setup, Docker, and deployment
- **[Architecture Decision Records](architecture/adr/)** - Important architectural decisions and rationale
- **[System Diagrams](architecture/diagrams/)** - Detailed flow diagrams for key processes

### 📚 **[Guides & Tutorials](guides/)**
- **[Getting Started](guides/GETTING_STARTED.md)** - Quick start guide for new developers
- **[Infrastructure Setup](guides/INFRASTRUCTURE_SETUP.md)** - Detailed infrastructure configuration
- **[Testing Guide](guides/TESTING_GUIDE.md)** - Comprehensive testing framework guide
- **[Testing Recipes](guides/TESTING_RECIPES.md)** - Practical testing patterns and examples
- **[Test Suite](guides/TEST_SUITE.md)** - Complete test suite structure and conventions
- **[E2E Demo](guides/E2E_Secure_Summarization_Demo.md)** - End-to-end secure summarization workflow

### 🔧 **[Development](development/)**
- **[Code Style Guide](development/CODESTYLE.md)** - Coding standards and style guidelines
- **[Refactoring Patterns](development/REFACTORING_PATTERNS.md)** - Common refactoring techniques and patterns
- **[Optimization Guide](development/OPTIMIZATION_GUIDE.md)** - Performance optimization techniques
- **[Prompt Configuration](development/PROMPT_CONFIGURATION_GUIDE.md)** - Guide for configuring prompts and templates

### ⚙️ **[Operations](operations/)**
- **[Main Runbook](operations/RUNBOOK.md)** - Operational procedures and troubleshooting
- **[Operational Runbook](operations/Operational_Runbook.md)** - Additional operational procedures
- **[Logging Guide](operations/LOGGING.md)** - Logging configuration and best practices

### 📖 **[Reference](reference/)**
- **[Errors & Envelopes](reference/ERRORS_AND_ENVELOPES.md)** - API specifications and error handling
- **[Glossary](reference/Glossary.md)** - Terminology and definitions
- **[Documentation Matrix](reference/DOCS_PARITY_MATRIX.md)** - Service documentation completeness tracking
- **[Reports Guide](reference/REPORTS_README.md)** - Generated reports and analytics
- **[Environment Config](reference/env.example)** - Example environment variables

### 🎯 **[Business & Strategy](business/)**
- **[Project Pitch](business/PITCH.md)** - Product vision, goals, and value proposition
- **[Enhancement Roadmap](business/Strengthening_TODOs.md)** - Future improvements and strategic planning

### 📜 **[Living Documentation](living-docs/)**
- **[Component Docs](living-docs/)** - Automatically maintained documentation for specific components
  - Avetta Confluence Downloader, Jirassic Pack, Leopold, Librarian, Llamalytics Hub, LLM Doc Consistency

### 🛠️ **Service Documentation**
- **[Source Agent](../services/source-agent/README.md)** - Multi-source document ingestion service
- **[Orchestrator](../services/orchestrator/README.md)** - Control plane, registry, workflows
- **[Doc Store](../services/doc_store/README.md)** - Storage, search, quality signals
- **[Frontend](../services/frontend/README.md)** - Web UI
- **[Summarizer Hub](../services/summarizer-hub/README.md)** - Provider fan-out
- **[Prompt Store](../services/prompt-store/README.md)** - Prompts DB/API
- **[Interpreter](../services/interpreter/README.md)** - Natural language interpretation and workflows
- **[Analysis Service](../services/analysis-service/README.md)** - Consistency analysis and reporting
- **[CLI](../services/cli/README.md)** - Interactive terminal interface
- **[Code Analyzer](../services/code-analyzer/README.md)** - Code analysis helpers
- **[Log Collector](../services/log-collector/README.md)** - Centralized logs and stats
- **[Memory Agent](../services/memory-agent/README.md)** - Memory and context management
- **[Secure Analyzer](../services/secure-analyzer/README.md)** - Secure analysis surface
- **[Notification Service](../services/notification-service/README.md)** - Owner resolution and notifications
- **[GitHub MCP](../services/github-mcp/README.md)** - Local MCP-like GitHub tools

## 🚀 Quick Start

1. **New to the Ecosystem?** Start with [Getting Started](guides/GETTING_STARTED.md) or [Features & Interactions](architecture/FEATURES_AND_INTERACTIONS.md)
2. **Setting up Infrastructure?** See [Infrastructure Setup](guides/INFRASTRUCTURE_SETUP.md) or [Infrastructure Guide](architecture/INFRASTRUCTURE.md). For local dev, use `docker-compose.dev.yml`.

### Secrets in Docker and CI

```bash
# Docker Compose with env-file (do not commit .env.local)
cat > .env.local <<'EOF'
GITHUB_TOKEN=ghp_xxx
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
BEDROCK_API_KEY=...
EOF
docker compose --env-file .env.local -f docker-compose.dev.yml up -d summarizer-hub source-agent
```

GitHub Actions (excerpt):
```yaml
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Export secrets
        run: |
          echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> $GITHUB_ENV
          echo "AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY_ID }}" >> $GITHUB_ENV
          echo "AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }}" >> $GITHUB_ENV
          echo "AWS_SESSION_TOKEN=${{ secrets.AWS_SESSION_TOKEN }}" >> $GITHUB_ENV
          echo "BEDROCK_API_KEY=${{ secrets.BEDROCK_API_KEY }}" >> $GITHUB_ENV
      - name: Run tests
        run: |
          pip install -r services/requirements.base.txt
          pytest -q
```
3. **Writing Code?** Check [Refactoring Patterns](development/REFACTORING_PATTERNS.md) and [Code Style Guide](development/CODESTYLE.md)
4. **Running Operations?** Use [Main Runbook](operations/RUNBOOK.md) or [Operational Runbook](operations/Operational_Runbook.md)

## 🔍 Key Topics

### Architecture
- [Service Interactions](architecture/FEATURES_AND_INTERACTIONS.md#architecture-overview)
- [Optimization Results](development/OPTIMIZATION_GUIDE.md#quantitative-impact)
- [Refactoring Patterns](development/REFACTORING_PATTERNS.md#core-refactoring-patterns)

### Development
- [Coding Standards](development/CODESTYLE.md)
- [Error Handling](development/REFACTORING_PATTERNS.md#error-handling-standardization-pattern)
- [Testing Patterns](guides/TESTING_GUIDE.md#testing-patterns)

### Operations
- [Health Checks](architecture/FEATURES_AND_INTERACTIONS.md#service-feature-highlights)
- [Monitoring](operations/RUNBOOK.md)
- [Troubleshooting](operations/RUNBOOK.md#troubleshooting)

### Business
- [Product Pitch](business/PITCH.md)
- [Future Roadmap](business/Strengthening_TODOs.md)

## 📈 Recent Updates

- ✅ **CLI Service Refactoring Complete** - 100% test improvement (72→153 passing tests), mixin-based architecture, standardized manager interfaces
- ✅ **Major Optimization Complete** - 30-pass analysis reduced codebase by 46%
- ✅ **Service Consolidation** - Unified agent services into single Source Agent
- ✅ **Standardized Patterns** - Consistent error handling, health checks, and middleware
- ✅ **Enhanced Documentation** - Comprehensive guides for all stakeholders

## 🤝 Contributing

When adding new documentation:
1. Check if content fits existing documents or needs a new file in the appropriate folder
2. Update this README.md index if adding new documents
3. Follow the established patterns in [Refactoring Patterns](development/REFACTORING_PATTERNS.md)
4. Use consistent formatting and cross-reference related documents

### Documentation Organization Guidelines
- **Architecture docs** → `docs/architecture/`
- **Guides & tutorials** → `docs/guides/`
- **Development guides** → `docs/development/`
- **Operational docs** → `docs/operations/`
- **Reference materials** → `docs/reference/`
- **Business/strategy docs** → `docs/business/`
- **Living documentation** → `docs/living-docs/`

## 📞 Support

For questions about specific services or features, refer to the appropriate documentation section above. For operational issues, see the [Main Runbook](operations/RUNBOOK.md) or [Operational Runbook](operations/Operational_Runbook.md).
