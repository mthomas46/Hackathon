# 🧠 LangGraph Integration for Orchestrator Service

## Overview

The Orchestrator service now includes comprehensive LangGraph integration, transforming it into an AI-first workflow orchestration platform. This integration leverages the existing service ecosystem for maximum cross-service collaboration and intelligent workflow execution.

## 🚀 Key Features

### Maximum Service Integration
- **18 Services as LangGraph Tools**: All existing services are available as intelligent tools
- **Docker Network Communication**: Seamless service-to-service communication via container networking
- **Registry-Driven Discovery**: Dynamic service discovery and health monitoring
- **Centralized Logging**: End-to-end workflow tracing across all services

### AI-First Orchestration
- **Intelligent Workflow Execution**: LangGraph-powered decision making
- **Natural Language Interfaces**: Conversational workflow interaction
- **Self-Learning Patterns**: Continuous improvement based on execution history
- **Multi-Agent Collaboration**: Services working together autonomously

## 🏗️ Architecture

```
🐳 Docker Network (llm-ecosystem)
├── 🔄 Orchestrator (LangGraph Engine)
│   ├── 🧠 LangGraph Workflows
│   ├── 🛠️ Service Tools
│   └── 📊 State Management
├── 📊 Logging Service (Centralized Observability)
├── 🗂️ Registry Service (Dynamic Discovery)
└── 🤖 All Other Services (Tool Ecosystem)
```

## 📦 Installation

### Dependencies
```bash
cd services/orchestrator/
pip install -r requirements.txt
```

### Required Services
Ensure these services are running on the Docker network:
- `llm-logging` (Port: 5040) - Centralized logging
- `llm-registry` (Port: 8080) - Service registry
- `llm-prompt-store` (Port: 5110) - AI prompt management
- `llm-document-store` (Port: 5140) - Document storage
- `llm-summarizer-hub` (Port: 5160) - Content summarization
- And all other services in your ecosystem

## 🎯 Usage

### Basic Workflow Execution

#### 1. Document Analysis Workflow
```bash
curl -X POST "http://localhost:5000/workflows/ai/document-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "content": "Your document content here...",
      "doc_id": "doc-123"
    },
    "user_id": "user-456",
    "tags": ["analysis", "documentation"]
  }'
```

#### 2. Code Documentation Workflow
```bash
curl -X POST "http://localhost:5000/workflows/ai/code-documentation" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "repo_url": "https://github.com/user/repo",
      "languages": ["python", "javascript"]
    },
    "user_id": "developer-789"
  }'
```

#### 3. Quality Assurance Workflow
```bash
curl -X POST "http://localhost:5000/workflows/ai/quality-assurance" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "target_docs": ["doc-1", "doc-2"],
      "quality_standards": {
        "consistency_check": true,
        "completeness_check": true
      }
    }
  }'
```

### Generic Workflow Execution
```bash
curl -X POST "http://localhost:5000/workflows/run" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "document_analysis",
    "parameters": {
      "content": "Document content...",
      "analysis_type": "comprehensive"
    },
    "user_id": "user-123",
    "correlation_id": "workflow-abc-123",
    "priority": "high"
  }'
```

## 🧪 Testing

### Run Integration Tests
```bash
cd services/orchestrator/
python test_langgraph_integration.py
```

### Test Individual Components
```python
# Test LangGraph engine
from modules.langgraph.engine import LangGraphWorkflowEngine
engine = LangGraphWorkflowEngine()
tools = await engine.initialize_tools(["logging_service"])
print(f"Available tools: {list(tools.keys())}")

# Test workflow state
from modules.langgraph.state import create_workflow_state
state = create_workflow_state("test", {"param": "value"})
print(f"Workflow state: {state.workflow_id}")
```

## 📋 Available Workflows

### Core Workflows
1. **Document Analysis** (`document_analysis`)
   - Multi-service content analysis
   - Key concept extraction
   - Consistency validation
   - Automated summarization

2. **Code Documentation** (`code_documentation`)
   - Code analysis and parsing
   - Documentation gap identification
   - Automated documentation generation
   - Quality validation

3. **Quality Assurance** (`quality_assurance`)
   - Comprehensive quality checks
   - Consistency analysis
   - Compliance validation
   - Improvement recommendations

### Service Tool Ecosystem

| Service | Tools Available | Key Capabilities |
|---------|-----------------|------------------|
| **Prompt Store** | 3 tools | AI prompt optimization, A/B testing |
| **Document Store** | 3 tools | Content storage, search, versioning |
| **Code Analyzer** | 2 tools | Code parsing, complexity analysis |
| **Summarizer Hub** | 2 tools | Multi-modal summarization |
| **Interpreter** | 2 tools | Natural language processing |
| **Analysis Service** | 2 tools | Quality analysis, reporting |
| **Notification Service** | 2 tools | Multi-channel communication |
| **Source Agent** | 2 tools | Multi-source data ingestion |
| **Secure Analyzer** | 2 tools | Content security, compliance |

## 🔧 Configuration

### Environment Variables
```bash
# LangGraph Configuration
LANGGRAPH_ENABLED=true
LANGGRAPH_MAX_RETRIES=3
LANGGRAPH_TIMEOUT=300

# Service Integration
LOGGING_SERVICE_URL=http://llm-logging:5040
REGISTRY_SERVICE_URL=http://llm-registry:8080

# Workflow Settings
WORKFLOW_MAX_EXECUTION_TIME=600
WORKFLOW_RETRY_DELAY=5
```

### Docker Compose Integration
```yaml
# Add to docker-compose.yml
services:
  orchestrator:
    environment:
      - LANGGRAPH_ENABLED=true
      - LOGGING_SERVICE_URL=http://llm-logging:5040
      - REGISTRY_SERVICE_URL=http://llm-registry:8080
    depends_on:
      - logging
      - registry
      - prompt-store
      - document-store
      # ... other services
    networks:
      - llm-ecosystem
```

## 📊 Monitoring & Observability

### Workflow Metrics
- **Execution Time**: End-to-end workflow duration
- **Success Rate**: Workflow completion percentage
- **Service Health**: Real-time service availability
- **Error Patterns**: Common failure modes and resolutions

### Logging Integration
All workflow events are automatically logged to the centralized logging service:
- Workflow start/completion events
- Service interaction logs
- Error and retry events
- Performance metrics

### Health Monitoring
```bash
# Check LangGraph health
curl http://localhost:5000/health/langgraph

# Get workflow statistics
curl http://localhost:5000/workflows/stats

# Monitor service integration
curl http://localhost:5000/health/services
```

## 🔧 Development

### Adding New Workflows
1. Create workflow in `modules/workflows/`
2. Register with LangGraph engine
3. Add API endpoint in `routes/workflows.py`
4. Update documentation

### Extending Service Tools
1. Add tool functions in `modules/langgraph/tools.py`
2. Update service integration mapping
3. Test tool functionality
4. Update service health checks

### Workflow State Management
- Use `WorkflowState` for consistent state tracking
- Implement proper error handling and retries
- Log all state transitions
- Maintain backward compatibility

## 🚨 Troubleshooting

### Common Issues

#### LangGraph Not Available
```bash
# Check if dependencies are installed
pip list | grep langgraph

# Reinstall if needed
pip install -r requirements.txt
```

#### Service Connection Issues
```bash
# Check Docker network connectivity
docker exec llm-orchestrator curl http://llm-prompt-store:5110/health

# Verify service registration
curl http://llm-registry:8080/services
```

#### Workflow Execution Failures
```bash
# Check workflow logs
curl http://llm-logging:5040/logs?workflow_id=wf-123

# Get workflow status
curl http://localhost:5000/workflows/status/wf-123
```

## 📈 Performance Optimization

### Caching Strategies
- **Service Response Caching**: Cache frequent service responses
- **Workflow State Persistence**: Store workflow state for recovery
- **Tool Result Caching**: Cache expensive tool operations

### Parallel Execution
- **Concurrent Service Calls**: Execute independent operations in parallel
- **Batch Processing**: Group similar operations for efficiency
- **Load Balancing**: Distribute work across service instances

### Resource Management
- **Connection Pooling**: Reuse service connections
- **Timeout Management**: Prevent hanging operations
- **Circuit Breakers**: Handle service failures gracefully

## 🎯 Next Steps

1. **Deploy Integration**: Start with document analysis workflow
2. **Monitor Performance**: Track metrics and optimize bottlenecks
3. **Expand Workflows**: Add more specialized workflows
4. **Enhance AI**: Integrate more advanced AI capabilities
5. **Scale Operations**: Add load balancing and high availability

## 📞 Support

- **Documentation**: Check this README and inline code comments
- **Testing**: Run `test_langgraph_integration.py` for validation
- **Monitoring**: Use centralized logging for troubleshooting
- **Health Checks**: Monitor service health via `/health` endpoints

---

The LangGraph integration transforms the Orchestrator from a basic coordination service into an intelligent, AI-first workflow orchestration platform that maximizes the potential of your entire service ecosystem.
