# Consolidated Service Management

This directory contains unified service management for the entire LLM Documentation Ecosystem.

## Main Script

### `service_manager.py`
**Consolidated Service Startup Manager** - Unified service management combining all individual startup scripts:

**Capabilities:**
- **Individual Service Startup**: Start any single service with proper configuration
- **Bulk Service Management**: Start all services in dependency order
- **Docker Integration**: Support for both local development and Docker environments
- **Health Monitoring**: Real-time service health checking and status reporting
- **Graceful Shutdown**: Proper cleanup and shutdown handling
- **Interactive CLI**: Rich console interface for service management
- **Dependency Resolution**: Automatic startup order based on service dependencies

**Features:**
- Environment-aware configuration (local vs Docker)
- Comprehensive error handling and logging
- Progress indicators and status updates
- Service restart and rebuild capabilities
- Resource usage monitoring
- Background service management

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
