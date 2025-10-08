# LLM Documentation Ecosystem Services

## 🏗️ Architecture Overview

The LLM Documentation Ecosystem is a comprehensive platform for intelligent prompt engineering, documentation generation, and cross-service orchestration:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Service   │    │ Prompt Store    │    │ Interpreter     │    │ Document Store  │
│   (Port 5130)   │◄──►│   (Port 5110)   │◄──►│   (Port 5120)   │◄──►│   (Port 5140)   │
│                 │    │                 │    │                 │    │                 │
│ • Interactive   │    │ • AI Analytics  │    │ • NLP Engine     │    │ • Doc Storage    │
│ • Menu System   │    │ • A/B Testing   │    │ • Intent Recog   │    │ • Versioning     │
│ • Workflow Exec │    │ • Optimization  │    │ • Query Parsing  │    │ • Search         │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Code Analyzer   │    │  Summarizer     │    │ Notification    │    │  Orchestrator   │
│   (Port 5150)   │    │   Hub (5160)    │    │ Service (5210)   │    │   (Port 5000)   │
│                 │    │                 │    │                 │    │                 │
│ • Code Analysis │    │ • Doc Summary   │    │ • Event Notif    │    │ • Service Coord │
│ • AST Parsing   │    │ • Key Concepts  │    │ • Webhooks       │    │ • Load Balance  │
│ • Complexity    │    │ • Topic Extract │    │ • Email/Slack    │    │ • Health Checks │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Core Services

### 1. 🤖 Prompt Store Service (`services/prompt_store/`)
[README](./prompt_store/README.md) · [Tests](../tests/unit/prompt_store)
**Port: 5110** | **Purpose: Intelligent Prompt Engineering Platform**

### 2. 🧠 MCP Local LLM Service (`services/mcp-local-llm/`)
[README](./mcp-local-llm/README.md)
**Port: 8014** | **Purpose: Local Language Model Inference Platform**

#### 🤖 Advanced Features:
- ✅ **Multi-Model Support**: Concurrent management of multiple local LLMs
- ✅ **Dynamic Loading**: On-demand model loading and unloading
- ✅ **Privacy-First**: All inference happens locally, no external API dependencies
- ✅ **GPU Optimization**: Resource management and CPU offloading
- ✅ **Streaming Responses**: Real-time token streaming for interactive applications
- ✅ **Context Management**: Intelligent context window optimization
- ✅ **MCP Protocol**: Full compatibility with Model Context Protocol

### 3. 📊 Data Dashboard Service (`services/datas-dashboard/`)
[README](./datas-dashboard/README.md)
**Port: 8015** | **Purpose: Real-Time Analytics & Data Visualization Platform**

#### 📈 Advanced Features:
- ✅ **Real-Time Streaming**: Live data updates from all system components
- ✅ **Multi-Source Integration**: Aggregate data from APIs, databases, and logs
- ✅ **Interactive Visualizations**: Drill-down capable charts and dashboards
- ✅ **Custom Dashboards**: User-configurable views and layouts
- ✅ **Alerting System**: Configurable thresholds and notification channels
- ✅ **Performance Analytics**: Response times, throughput, and error tracking
- ✅ **Business Intelligence**: ROI metrics and efficiency analysis

### 4. 📝 MCP Logs Service (`services/mcp-logs/`)
[README](./mcp-logs/README.md)
**Port: 8016** | **Purpose: Centralized Logging & Observability Platform**

#### 📊 Advanced Features:
- ✅ **Multi-Source Aggregation**: Collect logs from files, syslog, journald, and APIs
- ✅ **Real-Time Processing**: Live log ingestion and analysis
- ✅ **Elasticsearch Integration**: Full-text search and time-series analysis
- ✅ **Correlation Engine**: Link related log entries across services
- ✅ **Anomaly Detection**: Statistical analysis for unusual patterns
- ✅ **Alerting & Monitoring**: Log-based alerts and performance tracking
- ✅ **Compliance Ready**: Audit trails and regulatory compliance logging

### 5. 🌿 MCP Evergreen Docs Service (`services/mcp-evergreen-docs/`)
[README](./mcp-evergreen-docs/README.md)
**Port: 8017** | **Purpose: Automated Documentation Maintenance & Knowledge Base Management**

#### 📚 Advanced Features:
- ✅ **Automated Updates**: Sync documentation from code comments and APIs
- ✅ **Accuracy Validation**: Cross-reference docs against actual implementations
- ✅ **Multi-Source Sync**: Synchronize docs across Git repositories and platforms
- ✅ **Version Control Integration**: Git-based documentation versioning
- ✅ **Knowledge Base**: Indexed search and relationship mapping
- ✅ **Lifecycle Management**: Automated documentation maintenance and updates
- ✅ **Validation Engine**: Completeness and consistency checking

### 6. ☁️ External Store Service (`services/external-store/`)
[README](./external-store/README.md)
**Port: 8018** | **Purpose: Unified Cloud Storage & Data Persistence Platform**

#### 💾 Advanced Features:
- ✅ **Multi-Cloud Support**: AWS S3, Azure Blob Storage, Google Cloud Storage
- ✅ **Automated Backups**: Scheduled and incremental backup strategies
- ✅ **Encryption & Security**: At-rest and in-transit data encryption
- ✅ **CDN Integration**: Global content delivery for performance
- ✅ **Lifecycle Management**: Automated data retention and archival
- ✅ **Cross-Region Replication**: Disaster recovery and high availability
- ✅ **Cost Optimization**: Intelligent tiering and storage class management

### 8. 🤖 Prompt Store Service (`services/prompt_store/`)
[README](./prompt_store/README.md) · [Tests](../tests/unit/prompt_store)
**Port: 5110** | **Purpose: Intelligent Prompt Engineering Platform**

#### 🧠 Advanced Features:
- ✅ **Full CRUD Operations**: Create, read, update, delete prompts with validation
- ✅ **Version Control**: Complete prompt evolution tracking with change summaries
- ✅ **Lifecycle Management**: Draft → Published → Deprecated → Archived workflow
- ✅ **Semantic Relationships**: Extends, references, alternatives between prompts
- ✅ **A/B Testing Automation**: Automated optimization experiments with traffic splitting
- ✅ **AI-Powered Analytics**: Performance metrics, user satisfaction, cost optimization
- ✅ **Dynamic Orchestration**: Conditional chains and prompt pipelines
- ✅ **Cross-Service Intelligence**: Code-to-prompt and document-driven generation
- ✅ **Quality Assurance**: Automated testing, linting, bias detection
- ✅ **Real-time Notifications**: Webhook + notification service integration
- ✅ **Bulk Operations**: Batch processing for efficiency

#### 🎯 Key Endpoints (28+ total):
```bash
# Core Operations
GET    /health                    # Health check
POST   /api/v1/prompts            # Create prompt
GET    /api/v1/prompts            # List prompts
GET    /api/v1/prompts/{id}       # Get specific prompt
PUT    /api/v1/prompts/{id}       # Update prompt

# Analytics & Intelligence
GET    /api/v1/analytics/dashboard    # Performance dashboard
POST   /api/v1/analytics/usage        # Record usage metrics
POST   /api/v1/analytics/satisfaction # User feedback

# A/B Testing & Optimization
POST   /api/v1/optimization/ab-tests       # Create A/B test
GET    /api/v1/optimization/ab-tests/{id}/results # Test results
POST   /api/v1/optimization/variations     # Generate variations

# Orchestration & Workflows
POST   /api/v1/orchestration/chains        # Create conditional chains
POST   /api/v1/orchestration/pipelines     # Create prompt pipelines
POST   /api/v1/orchestration/prompts/select # Optimal prompt selection

# Cross-Service Intelligence
POST   /api/v1/intelligence/code/generate      # Generate from code
POST   /api/v1/intelligence/document/generate  # Generate from docs
POST   /api/v1/intelligence/service/generate   # Service integration prompts

# Quality Assurance
POST   /api/v1/validation/lint         # Lint prompts
POST   /api/v1/validation/bias-detect  # Detect bias
POST   /api/v1/validation/test-suites  # Create test suites
```

#### 📊 Advanced Capabilities:
- **Performance Analytics**: Success rates, response times, token usage, cost tracking
- **User Satisfaction**: Rating system with AI-assisted quality assessment
- **Cost Optimization**: Monitor and optimize LLM API usage across services
- **Bias Detection**: Pattern matching and LLM-based bias analysis
- **Automated Testing**: Comprehensive test suites for prompt validation
- **Evolution Tracking**: Monitor prompt improvements over time
- **Context-Aware Selection**: Intelligent prompt recommendation engine

#### Usage Examples:
```bash
# Create a prompt
curl -X POST http://localhost:5110/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code_review",
    "category": "code_analysis", 
    "content": "Review this code: {code}",
    "variables": ["code"]
  }'

# Get prompt with variables filled
curl "http://localhost:5110/prompts/search/code_analysis/code_review?code=print('hello')"

# Migrate from YAML
curl -X POST http://localhost:5110/migrate
```

---

### 2. 📄 Document Store Service (`services/doc_store/`)
[README](./doc_store/README.md) · [Tests](../tests/unit/doc_store)
**Port: 5140** | **Purpose: Advanced document storage and management**

#### Features:
- ✅ **Document CRUD**: Full create, read, update operations
- ✅ **Version Control**: Track document evolution
- ✅ **Content Hashing**: Duplicate detection and integrity
- ✅ **Metadata Management**: Rich metadata with JSON support
- ✅ **Correlation Tracking**: Link documents to related entities
- ✅ **Search & Filtering**: Full-text search and metadata filtering
- ✅ **Bulk Operations**: Batch document processing
- ✅ **Analytics**: Usage tracking and performance metrics

#### Key Endpoints:
```bash
POST   /api/v1/documents         # Create document
GET    /api/v1/documents         # List documents
GET    /api/v1/documents/{id}    # Get document
PUT    /api/v1/documents/{id}    # Update document
DELETE /api/v1/documents/{id}    # Delete document
GET    /api/v1/search            # Search documents
```

---

### 3. 🔍 Code Analyzer Service (`services/code-analyzer/`)
[README](./code-analyzer/README.md) · [Tests](../tests/unit/code-analyzer)
**Port: 5150** | **Purpose: Static code analysis for prompt generation**

#### Features:
- ✅ **AST Parsing**: Abstract syntax tree analysis
- ✅ **Function/Method Detection**: Extract function signatures and purposes
- ✅ **Class Analysis**: Object-oriented structure analysis
- ✅ **Complexity Metrics**: Cyclomatic complexity calculation
- ✅ **Language Support**: Multiple programming language support
- ✅ **Dependency Analysis**: Import and dependency mapping
- ✅ **Documentation Generation**: Automatic docstring analysis

#### Key Endpoints:
```bash
POST   /analyze                  # Analyze code
GET    /health                   # Health check
```

---

### 4. 📝 Summarizer Hub Service (`services/summarizer-hub/`)
[README](./summarizer-hub/README.md) · [Tests](../tests/unit/summarizer-hub)
**Port: 5160** | **Purpose: Document summarization and key concept extraction**

#### Features:
- ✅ **Document Summarization**: Extractive and abstractive summarization
- ✅ **Key Concept Extraction**: Identify main topics and concepts
- ✅ **Topic Modeling**: Uncover latent topics in documents
- ✅ **Sentiment Analysis**: Document sentiment and tone analysis
- ✅ **Language Detection**: Automatic language identification
- ✅ **Readability Scoring**: Assess document complexity
- ✅ **Multi-format Support**: Handle various document formats

#### Key Endpoints:
```bash
POST   /summarize                # Summarize document
GET    /health                   # Health check
```

---

### 5. 📢 Notification Service (`services/notification-service/`)
[README](./notification-service/README.md) · [Tests](../tests/unit/notification-service)
**Port: 5210** | **Purpose: Centralized notification management**

#### Features:
- ✅ **Multi-channel Support**: Email, Slack, webhooks, SMS
- ✅ **Owner Resolution**: Map owners to notification targets
- ✅ **Deduplication**: Prevent notification spam
- ✅ **Dead Letter Queue**: Handle failed deliveries
- ✅ **Template Support**: Customizable notification templates
- ✅ **Priority Levels**: High, medium, low priority notifications
- ✅ **Retry Logic**: Automatic retry for failed deliveries
- ✅ **Analytics**: Delivery success tracking

#### Key Endpoints:
```bash
POST   /notify                  # Send notification
POST   /owners/update           # Update owner mappings
POST   /owners/resolve          # Resolve owners to targets
GET    /dlq                     # View dead letter queue
GET    /health                  # Health check
```

---

### 6. 🎯 Interpreter Service (`services/interpreter/`)
[README](./interpreter/README.md) · [Tests](../tests/unit/interpreter)
**Port: 5120** | **Purpose: Natural language processing and intent recognition**

#### Features:
- ✅ **Intent Recognition**: Understand user intentions
- ✅ **Entity Extraction**: Extract structured data from text
- ✅ **Query Parsing**: Convert natural language to structured queries
- ✅ **Multi-intent Support**: Handle complex multi-step requests
- ✅ **Confidence Scoring**: Rate interpretation accuracy
- ✅ **Context Awareness**: Maintain conversation context
- ✅ **Language Support**: Multiple language processing

#### Supported Intents:
```python
{
  "intents": [
    "create_prompt", "get_prompt", "list_prompts",
    "run_analysis", "generate_report", "health_check",
    "ab_test_create", "workflow_execute"
  ]
}
```

---

### 7. 🧪 Analysis Service (`services/analysis-service/`)
[README](./analysis-service/README.md) · [Tests](../tests/unit/analysis_service)
**Purpose: Code and documentation analysis**

#### Features:
- ✅ **Code Analysis**: Static analysis for multiple languages
- ✅ **Documentation Consistency**: Check doc alignment
- ✅ **Quality Metrics**: Code quality and documentation scores
- ✅ **Dependency Analysis**: Module and package relationships
- ✅ **Security Scanning**: Basic security vulnerability detection

---

### 8. 🎮 CLI Service (`services/cli/`)
[README](./cli/README.md) · [Tests](../tests/unit/cli)
**Port: 5130** | **Purpose: Interactive command-line interface**

#### Enhanced Features:
- ✅ **Interactive Menu System**: User-friendly navigation
- ✅ **Rich Terminal UI**: Beautiful console interface with colors
- ✅ **Workflow Orchestration**: Execute complex workflows
- ✅ **Health Monitoring**: Real-time service status
- ✅ **Advanced Prompt Management**: Full CRUD operations
- ✅ **A/B Testing Interface**: Create and monitor tests
- ✅ **Analytics Dashboard**: CLI-based analytics viewing
- ✅ **Bulk Operations**: Batch processing commands

#### Enhanced Menu Structure:
```
Main Menu:
1. 🤖 Prompt Management
   ├── 📋 List all prompts
   ├── ➕ Create new prompt
   ├── 👁️  View prompt details
   ├── ✏️  Update prompt
   ├── 🗑️  Delete prompt
   └── 🍴 Fork prompt
   └── 🔗 Manage relationships

2. 🧪 A/B Testing
   ├── 🆕 Create new test
   ├── 📊 View test results
   ├── 🎯 Select prompts for testing
   └── 🏁 End test and declare winner

3. 🔄 Workflow Orchestration
   ├── 📄 Run document analysis
   ├── 📥 Trigger ingestion workflow
   ├── ✅ Execute consistency check
   ├── 📊 Generate reports
   └── 📈 View workflow status

4. 📊 Analytics & Intelligence
   ├── 📈 View performance dashboard
   ├── 💰 Cost optimization insights
   ├── 👥 User satisfaction metrics
   └── 🎯 Usage trends analysis

5. 🔧 Quality Assurance
   ├── 🔍 Lint prompts
   ├── ⚖️  Detect bias
   ├── 🧪 Run test suites
   └── 📋 Create validation rules

6. 🌐 Cross-Service Intelligence
   ├── 💻 Generate from code analysis
   ├── 📄 Generate from documents
   ├── 🔧 Service integration prompts
   └── 📊 Effectiveness analysis

7. 🔔 Notifications & Monitoring
   └── 📡 Service health check
```

---

### 9. 🎪 GitHub MCP (`services/github-mcp/`)
[README](./github-mcp/README.md) · [Tests](../tests/unit/github_mcp)
**Purpose: GitHub integration and repository management**

#### Features:
- ✅ **Repository Analysis**: Code and documentation analysis
- ✅ **Issue/PR Management**: GitHub workflow integration
- ✅ **Webhook Processing**: Real-time GitHub event handling
- ✅ **Documentation Sync**: Keep docs aligned with code
- ✅ **Collaboration Tools**: Team workflow support

#### Features:
- ✅ **Intent Recognition**: Understand user intentions from natural language
- ✅ **Entity Extraction**: Extract URLs, emails, file paths, etc.
- ✅ **Workflow Generation**: Convert queries to executable workflows
- ✅ **Multi-intent Support**: Handle complex multi-step requests
- ✅ **Confidence Scoring**: Rate interpretation confidence

#### Supported Intents:
```python
{
  "analyze_document": ["analyze this document", "check consistency"],
  "consistency_check": ["find inconsistencies", "validate consistency"],
  "ingest_github": ["ingest from github", "pull from github repo"],
  "ingest_jira": ["import jira tickets", "sync jira"],
  "ingest_confluence": ["pull from confluence", "sync confluence pages"],
  "create_prompt": ["create a new prompt", "make a prompt"],
  "find_prompt": ["find a prompt", "search for prompts"],
  "generate_report": ["generate a report", "create a report"],
  "show_analytics": ["show analytics", "view analytics"]
}
```

#### Usage Examples:
```bash
# Interpret a query
curl -X POST http://localhost:5120/interpret \
  -H "Content-Type: application/json" \
  -d '{"query": "analyze this document for consistency issues"}'

# Execute interpreted workflow
curl -X POST http://localhost:5120/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "ingest from github repo https://github.com/user/repo"}'
```

---

## 🛠️ Quick Start

### 1. Start Services with Docker Compose:
```bash
# Dev stack (active code mounted, runs `python .../main.py`)
docker compose -f docker-compose.dev.yml up -d

# Or start individual services
docker-compose -f docker-compose.services.yml up prompt-store -d
docker-compose -f docker-compose.services.yml up interpreter -d

# Pass secrets safely (examples)
# 1) Use env file (never commit!)
cat > .env.local <<'EOF'
EXTERNAL_GITHUB_TOKEN=ghp_xxx
EXTERNAL_AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
BEDROCK_API_KEY=...
EOF
docker compose --env-file .env.local -f docker-compose.dev.yml up -d summarizer-hub source-agent

# 2) Inline env for one-off local runs
EXTERNAL_GITHUB_TOKEN=ghp_xxx docker compose -f docker-compose.dev.yml up -d source-agent

# 3) Docker secrets (compose v3+; stub)
#   Define `secrets:` in compose and mount into the container; map them to envs in entrypoint.
```

### 2. Migrate Existing Prompts:
```bash
# Migrate from YAML to database
curl -X POST http://localhost:5110/migrate
```

### 3. Test the CLI:
```bash
# Interactive mode
docker exec -it llm-cli python services/cli/main.py interactive

# Or direct commands
docker exec llm-cli python services/cli/main.py health
```

### 4. Test Natural Language Queries:
```bash
# Test interpretation
curl -X POST http://localhost:5120/interpret \
  -H "Content-Type: application/json" \
  -d '{"query": "analyze my documents"}'

# Execute workflow
curl -X POST http://localhost:5120/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "create a summary report"}'
```

---

## 🔧 Configuration

### Environment Variables:
```bash
# Prompt Store
PROMPT_STORE_DB=/app/data/prompt_store.db
PROMPT_STORE_API_PORT=5110

# Interpreter
INTERPRETER_API_PORT=5120

# CLI
CLI_VERBOSE=true
```

### Database Schema:
The Prompt Store uses SQLite with the following tables:
- `prompts` - Core prompt data
- `prompt_versions` - Version history
- `ab_tests` - A/B test configurations
- `ab_test_results` - Test results and metrics
- `prompt_usage` - Usage logging
- `prompt_analytics` - Aggregated analytics
- `user_sessions` - User session tracking

---

## 📊 Integration Examples

### Python Integration:
```python
from services.shared.clients import ServiceClients

clients = ServiceClients()

# Get a prompt
prompt = await clients.get_json("prompt-store/prompts/search/summarization/default?content=test")

# Interpret user query
interpretation = await clients.post_json("interpreter/interpret", {
    "query": "analyze this document"
})

# Execute workflow
result = await clients.post_json("interpreter/execute", {
    "query": "generate a report"
})
```

### CLI Integration:
```bash
# Get prompt
llm-cli get-prompt summarization default --content "my content"

# Health check
llm-cli health

# List prompts
llm-cli list-prompts --category analysis
```

---

## 🔍 Monitoring & Debugging

### Health Checks:
```bash
# All services
curl http://localhost:5110/health  # Prompt Store
curl http://localhost:5120/health  # Interpreter

# Service-specific health
docker ps  # Container status
docker logs llm-prompt-store  # Service logs
```

### Logs:
```bash
# View service logs
docker-compose -f docker-compose.services.yml logs prompt-store
docker-compose -f docker-compose.services.yml logs interpreter
docker-compose -f docker-compose.services.yml logs cli
```

### Database Access:
```bash
# Access SQLite database
docker exec -it llm-prompt-store sqlite3 /app/data/prompt_store.db

# Run queries
.schema
SELECT name FROM prompts LIMIT 5;
```

---

## 🚀 Advanced Features

### A/B Testing Workflow:
```python
# 1. Create test
test = await clients.post_json("prompt-store/ab-tests", {
    "name": "summary_improvement",
    "prompt_a_id": "summary_v1",
    "prompt_b_id": "summary_v2",
    "test_metric": "response_quality"
})

# 2. Get test prompt for user
result = await clients.get_json(f"prompt-store/ab-tests/{test['id']}/select")

# 3. Use selected prompt
prompt = await clients.get_json(f"prompt-store/prompts/{result['prompt_id']}")

# 4. Record results
await clients.post_json(f"prompt-store/ab-tests/{test['id']}/results", {
    "prompt_id": result['prompt_id'],
    "metric_value": 0.85,
    "sample_size": 100
})
```

### Workflow Orchestration:
```python
# Complex multi-step workflow
interpretation = await clients.post_json("interpreter/interpret", {
    "query": "analyze the github repo, check for security issues, and generate a report"
})

# Execute the generated workflow
result = await clients.post_json("interpreter/execute", {
    "query": "analyze the github repo, check for security issues, and generate a report"
})
```

---

## 📈 Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| **Prompt Management** | Static YAML files | Full CRUD with database |
| **User Interface** | Command line only | Rich interactive CLI |
| **A/B Testing** | Not supported | Built-in framework |
| **Analytics** | None | Comprehensive tracking |
| **NLP Integration** | Manual parsing | Intelligent interpretation |
| **Workflow Execution** | Manual steps | Automated orchestration |
| **Version Control** | Git only | Full version history |
| **Collaboration** | Single user | Multi-user support |

This upgrade transforms the LLM Documentation Ecosystem from a collection of basic services into a sophisticated, user-friendly platform with advanced AI-powered capabilities! 🎉✨
