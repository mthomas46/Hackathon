# Consolidated Service Management

This directory contains unified service management for the entire LLM Documentation Ecosystem.

## Scripts

### `service_manager.py`
**Enterprise Service Orchestration Platform** - Comprehensive service management and orchestration system for the entire LLM Documentation Ecosystem.

#### Features
- **Individual Service Control**: Precise startup, shutdown, and restart of any single service
- **Bulk Service Orchestration**: Intelligent startup of all 29 services in optimal dependency order
- **Multi-Environment Support**: Seamless operation in Docker, Kubernetes, and local development environments
- **Real-time Health Monitoring**: Continuous service health checking with automated recovery
- **Graceful Lifecycle Management**: Proper startup sequencing, shutdown cleanup, and resource management
- **Interactive Management Console**: Rich CLI interface with progress indicators and status visualization
- **Dependency-Aware Scheduling**: Automatic resolution of service dependencies and startup ordering
- **Resource Management**: CPU, memory, and disk usage monitoring with optimization recommendations

#### Capabilities
- Environment-aware configuration with automatic adaptation (development/staging/production)
- Comprehensive error handling with intelligent retry mechanisms and failure recovery
- Detailed logging and audit trails for all service operations
- Background service management with process monitoring and automatic restart
- Service grouping and selective startup (core services, processing services, integrations)
- Performance monitoring with resource usage alerts and optimization suggestions
- Integration with monitoring systems and alerting platforms

#### Use Cases
- **Development Environment Setup**: Quick local development environment configuration
- **Production Deployment**: Reliable, sequenced startup of enterprise-scale service ecosystems
- **Service Maintenance**: Individual service updates, restarts, and troubleshooting
- **Disaster Recovery**: Automated service recovery and dependency-aware restart procedures
- **Capacity Management**: Resource monitoring and scaling decision support
- **CI/CD Integration**: Automated service lifecycle management in deployment pipelines

## What Was Consolidated

This script combines functionality from all previously separate startup scripts:
- `start_all_services.py` → Master service orchestration
- `start_analysis_service.py` → Analysis service startup
- `start_architecture_digitizer.py` → Architecture digitizer startup
- `start_bedrock_proxy.py` → Bedrock proxy startup
- `start_code_analyzer.py` → Code analyzer startup
- `start_docstore.py` → Document store startup
- `start_github_mcp.py` → GitHub MCP startup
- `start_interpreter.py` → Interpreter startup
- `start_log_collector.py` → Log collector startup
- `start_orchestrator.py` → Orchestrator startup
- `start_prompt_store.py` → Prompt store startup
- `start_secure_analyzer.py` → Secure analyzer startup
- `start_summarizer_hub.py` → Summarizer hub startup

## Usage Examples

```bash
# Start all services in dependency order
python scripts/startup/service_manager.py start-all

# Start individual service
python scripts/startup/service_manager.py start doc_store

# Start core services only
python scripts/startup/service_manager.py start-core

# Check service status
python scripts/startup/service_manager.py status

# Stop all services
python scripts/startup/service_manager.py stop-all

# Restart specific service
python scripts/startup/service_manager.py restart orchestrator

# View service logs
python scripts/startup/service_manager.py logs frontend --follow
```

## Service Categories

**Infrastructure Services:**
- Redis (caching and data storage)

**Core Services:**
- Doc Store (document management)
- Prompt Store (prompt management)
- Analysis Service (content analysis)

**Workflow Services:**
- Orchestrator (workflow management)
- Source Agent (data ingestion)

**Processing Services:**
- Summarizer Hub (content summarization)
- Interpreter (code execution)
- Code Analyzer (code analysis)
- Secure Analyzer (security analysis)

**Integration Services:**
- GitHub MCP (GitHub integration)
- Bedrock Proxy (AWS integration)

**Advanced Services:**
- Architecture Digitizer (architecture analysis)
- Log Collector (monitoring)

**User Interface:**
- Frontend (web interface)
- CLI (command interface)

## Startup Order

Services are started in optimal dependency order:
1. Infrastructure (Redis)
2. Core storage (Doc Store, Prompt Store)
3. Core analysis (Analysis Service)
4. Orchestration (Orchestrator)
5. Data processing (Source Agent, Summarizer Hub, etc.)
6. Integrations (GitHub MCP, Bedrock Proxy)
7. Advanced features (Architecture Digitizer)
8. Monitoring (Log Collector)
9. User interfaces (Frontend, CLI)
