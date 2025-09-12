# LLM Documentation Ecosystem Services

## 🏗️ Architecture Overview

The LLM Documentation Ecosystem now includes advanced services for prompt management, CLI interaction, and natural language processing:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Service   │    │ Prompt Store    │    │ Interpreter     │
│   (Port 5130)   │◄──►│   (Port 5110)   │◄──►│   (Port 5120)   │
│                 │    │                 │    │                 │
│ • Interactive   │    │ • CRUD Ops      │    │ • NLP Engine     │
│ • Menu System   │    │ • A/B Testing   │    │ • Intent Recog   │
│ • Workflow Exec │    │ • Analytics     │    │ • Query Parsing  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │   (Port 5000)   │
                    └─────────────────┘
```

## 🚀 New Services

### 1. Prompt Store Service (`services/prompt-store/`)
[README](./prompt-store/README.md) · [Tests](../tests/unit/prompt_store)
**Port: 5110** | **Purpose: Advanced prompt management with persistence**

#### Features:
- ✅ **Full CRUD Operations**: Create, read, update, delete prompts
- ✅ **Version Control**: Track prompt evolution with full history
- ✅ **A/B Testing**: Test prompt variations in production
- ✅ **Analytics**: Usage tracking and performance metrics
- ✅ **Database Persistence**: SQLite with automatic migrations
- ✅ **REST API**: Complete HTTP API for prompt management

#### Key Endpoints:
```bash
GET    /health                    # Health check
POST   /prompts                   # Create prompt
GET    /prompts                   # List prompts
GET    /prompts/{id}             # Get specific prompt
PUT    /prompts/{id}             # Update prompt
DELETE /prompts/{id}             # Delete prompt
POST   /ab-tests                 # Create A/B test
GET    /analytics                # Get analytics
POST   /migrate                  # Migrate from YAML
```

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

### 2. CLI Service (`services/cli/`)
[README](./cli/README.md) · [Tests](../tests/unit/cli)
**Purpose: Interactive command-line interface**

#### Features:
- ✅ **Interactive Menu System**: User-friendly navigation
- ✅ **Rich Terminal UI**: Beautiful console interface with colors
- ✅ **Workflow Orchestration**: Execute complex workflows
- ✅ **Health Monitoring**: Real-time service status
- ✅ **Prompt Management**: Create and manage prompts via CLI

#### Usage:
```bash
# Interactive mode
python services/cli/main.py interactive

# Direct commands
python services/cli/main.py get-prompt summarization default --content "test content"
python services/cli/main.py list-prompts --category analysis
python services/cli/main.py health
```

#### Menu Structure:
```
Main Menu:
1. Prompt Management
   ├── List prompts
   ├── Create new prompt
   ├── View prompt details
   ├── Update prompt
   ├── Delete prompt
   └── Fork prompt

2. A/B Testing
   ├── Create test
   ├── View test results
   └── Select prompt for testing

3. Workflow Orchestration
   ├── Run document analysis
   ├── Trigger ingestion workflow
   ├── Execute consistency check
   ├── Generate reports
   └── View workflow status

4. Analytics & Monitoring
   └── View system analytics

5. Service Health Check
   └── Check all service statuses
```

---

### 3. Interpreter Service (`services/interpreter/`)
[README](./interpreter/README.md) · [Tests](../tests/unit/interpreter)

### 4. Analysis Service (`services/analysis-service/`)
[README](./analysis-service/README.md) · [Tests](../tests/unit/analysis_service)

### 5. Notification Service (`services/notification-service/`)
[README](./notification-service/README.md) · [Tests](../tests/unit/notification_service)

### 6. GitHub MCP (`services/github-mcp/`)
[README](./github-mcp/README.md) · [Tests](../tests/unit/github_mcp)
**Port: 5120** | **Purpose: Natural language processing for user queries**

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
GITHUB_TOKEN=ghp_xxx
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...
BEDROCK_API_KEY=...
EOF
docker compose --env-file .env.local -f docker-compose.dev.yml up -d summarizer-hub source-agent

# 2) Inline env for one-off local runs
GITHUB_TOKEN=ghp_xxx docker compose -f docker-compose.dev.yml up -d source-agent

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
PROMPT_STORE_PORT=5110

# Interpreter
INTERPRETER_PORT=5120

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
