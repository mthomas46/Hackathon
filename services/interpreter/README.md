# Interpreter Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Natural language interpretation and workflow generation.

- **Port**: 5120
- **Endpoints**: `/health`, `/interpret`, `/execute`, `/intents`, `/natural-query`, `/execute-natural-workflow`, `/ecosystem/capabilities`, `/workflows/discover`, `/prompt/translate`
- **Tests**: [tests/unit/interpreter](../../tests/unit/interpreter), [test_enhanced_integration.py](./test_enhanced_integration.py)

## Features
- **🧠 Ecosystem-Aware NLP**: Advanced natural language processing with full LLM Documentation Ecosystem context
- **🔗 Orchestrator Integration**: Direct integration with orchestrator for workflow execution
- **🎯 LangGraph Workflow Discovery**: Automatic discovery and execution of LangGraph workflows
- **⚡ Prompt Engineering**: Intelligent translation of natural language to structured workflow prompts
- **🌐 Multi-Service Orchestration**: Coordinate complex operations across all ecosystem services
- **🎭 Intelligent Fallbacks**: Graceful handling of ambiguous queries with contextual suggestions
- **📊 Real-Time Context**: Dynamic understanding of available services, capabilities, and workflows

## Overview and role in the ecosystem
- **🆕 Enhanced Entry Point**: Advanced natural language interface to the entire LLM Documentation Ecosystem
- **🔄 Full Ecosystem Integration**: Works with ALL services (Prompt Store, Analysis Service, Doc Store, Source Agent, Code Analyzer, Summarizer Hub, Notification Service, Secure Analyzer, Orchestrator)
- **🎯 Intelligent Workflow Mapping**: Automatically maps natural language queries to appropriate workflows
- **🚀 LangGraph Orchestration**: Seamless integration with LangGraph for AI-powered workflow execution
- **💬 Conversational Interface**: Enables natural language interaction with the entire platform

## API

### Core Endpoints
| Method | Path       | Description |
|--------|------------|-------------|
| GET    | /health    | Health check |
| POST   | /interpret | Interpret natural language query (legacy) |
| POST   | /execute   | Interpret and execute workflow (legacy) |
| GET    | /intents   | List supported intents |

### 🆕 Enhanced Natural Language Endpoints
| Method | Path                      | Description |
|--------|---------------------------|-------------|
| POST   | **/natural-query**       | **🆕 Process natural language query with full ecosystem context** |
| POST   | **/execute-natural-workflow** | **🆕 Execute natural language query as complete workflow** |
| GET    | **/ecosystem/capabilities** | **🆕 Get comprehensive ecosystem capabilities** |
| POST   | **/workflows/discover**  | **🆕 Discover all available workflows** |
| POST   | **/prompt/translate**    | **🆕 Translate natural language to structured workflow prompt** |

## Environment
| Name | Description | Default |
|------|-------------|---------|
| INTERPRETER_PORT | Service port | 5120 |

## Quickstart
```bash
python services/interpreter/main.py
```

## Examples

### Legacy API Usage
```bash
# Basic interpretation
curl -X POST http://localhost:5120/interpret -H 'Content-Type: application/json' \
  -d '{"query":"analyze this document"}'

# Execute workflow
curl -X POST http://localhost:5120/execute -H 'Content-Type: application/json' \
  -d '{"query":"analyze this document"}'
```

### 🆕 Enhanced Natural Language API Usage

#### 1. Process Natural Language Query
```bash
curl -X POST http://localhost:5120/natural-query -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze this document for quality issues and generate a summary",
    "user_id": "user123",
    "context": {"domain": "documentation", "priority": "high"}
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "original_query": "analyze this document for quality issues and generate a summary",
    "interpretation": {
      "intent": "analyze_document",
      "confidence": 0.9,
      "entities": {"document_type": ["general"]}
    },
    "ecosystem_context": {
      "detected_services": ["document_store", "analysis_service", "summarizer_hub"],
      "detected_capabilities": ["analyze_quality", "generate_summary"],
      "available_workflows": [...]
    },
    "langgraph_workflows": {
      "best_match": {
        "workflow_name": "document-analysis",
        "match_score": 0.9
      }
    }
  }
}
```

#### 2. Execute Natural Workflow
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze this document and generate a quality report",
    "user_id": "user123"
  }'
```

#### 3. Get Ecosystem Capabilities
```bash
curl http://localhost:5120/ecosystem/capabilities
```

#### 4. Discover Available Workflows
```bash
curl -X POST http://localhost:5120/workflows/discover
```

#### 5. Translate to Workflow Prompt
```bash
curl -X POST http://localhost:5120/prompt/translate -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze code repository and generate documentation",
    "user_id": "developer123"
  }'
```

### Advanced Usage Examples

#### Document Analysis Workflow
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze the quality of this documentation, check for consistency, and generate a summary report",
    "context": {
      "document_type": "api_docs",
      "output_format": "json",
      "include_metrics": true
    }
  }'
```

#### Code Repository Processing
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "analyze this GitHub repository, generate code documentation, and check for security vulnerabilities",
    "context": {
      "repo_url": "https://github.com/example/repo",
      "analysis_types": ["security", "quality", "documentation"]
    }
  }'
```

#### Multi-Service Orchestration
```bash
curl -X POST http://localhost:5120/execute-natural-workflow -H 'Content-Type: application/json' \
  -d '{
    "query": "ingest data from Jira, analyze it for patterns, generate a report, and send notifications to stakeholders",
    "context": {
      "source": "jira",
      "analysis_depth": "comprehensive",
      "notify_channels": ["email", "slack"]
    }
  }'
```

## Related
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)
- Prompt Store: [../prompt-store/README.md](../prompt-store/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## Testing

### Test Suites
- **Legacy Unit Tests**: [tests/unit/interpreter](../../tests/unit/interpreter)
- **🆕 Enhanced Integration Tests**: [test_enhanced_integration.py](./test_enhanced_integration.py)

### Test Coverage Areas
- **Ecosystem Context Awareness**: Service capability detection, workflow mapping, alias resolution
- **Orchestrator Integration**: Workflow execution, LangGraph orchestration, error handling
- **Prompt Engineering**: Query translation, optimization, fallback mechanisms
- **LangGraph Discovery**: Workflow discovery, parameter validation, execution
- **Enhanced API Endpoints**: Natural language processing, multi-service orchestration
- **Integration Scenarios**: End-to-end workflows, error handling, performance validation

### Running Tests
```bash
# Run legacy unit tests
pytest tests/unit/interpreter/ -v

# Run enhanced integration tests
pytest test_enhanced_integration.py -v

# Run specific test categories
pytest test_enhanced_integration.py::TestEcosystemContextIntegration -v
pytest test_enhanced_integration.py::TestOrchestratorIntegration -v
pytest test_enhanced_integration.py::TestLangGraphDiscovery -v
pytest test_enhanced_integration.py::TestEnhancedInterpreterAPI -v
```

### Test Architecture
- **Mock Testing**: External service dependencies fully mocked for isolation
- **Integration Testing**: End-to-end workflow execution with real service coordination
- **Performance Testing**: Response times, resource usage, and concurrent operation validation
- **Error Scenario Testing**: Comprehensive failure mode coverage and recovery mechanisms
- **Concurrent Testing**: Multi-user and multi-workflow scenario validation

### Test Strategies
- **Legacy Endpoints**: Ensure tests import real service app by adding project root to `sys.path`
- **Enhanced Endpoints**: Full ecosystem context testing with mocked external services
- **LangGraph Integration**: Workflow discovery and execution testing with mock orchestrator
- **Error Handling**: 404-tolerant fallbacks and graceful degradation testing
- **Performance**: Response time validation and resource usage monitoring
