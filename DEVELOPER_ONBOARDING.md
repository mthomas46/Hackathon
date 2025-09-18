# 🚀 Developer Onboarding Guide - LLM Documentation Ecosystem

**Welcome to the LLM Documentation Ecosystem!** This guide will get you up and running with our enterprise-grade, AI-first microservices architecture in under 30 minutes.

---

## 📋 **Quick Start Checklist**

### **✅ Phase 1: Environment Setup (5 minutes)**
- [ ] Clone repository and verify Docker setup
- [ ] Start all services with docker-compose
- [ ] Verify 17 services are healthy
- [ ] Access the main dashboard

### **✅ Phase 2: Core Concepts (10 minutes)**
- [ ] Understand the 17 services architecture
- [ ] Learn Domain-Driven Design patterns
- [ ] Explore the API documentation index
- [ ] Test basic service interactions

### **✅ Phase 3: Development Workflow (15 minutes)**
- [ ] Set up development environment
- [ ] Run sample API calls
- [ ] Use the CLI interface
- [ ] Create your first document workflow

---

## 🏗️ **Architecture Overview**

### **🎯 What You're Working With**
The LLM Documentation Ecosystem is a **production-ready, enterprise-grade platform** featuring:

- **17 Microservices** with clear bounded contexts
- **350+ API Endpoints** across all services
- **Domain-Driven Design** with CQRS and Event Sourcing
- **AI-First Capabilities** with unified LLM access
- **Complete Documentation** and testing infrastructure

### **🔧 Core Services You'll Use Daily**

| Service | Purpose | Port | Key for Developers |
|---------|---------|------|-------------------|
| **Frontend** | Main UI & Dashboard | 3000 | Your development console |
| **CLI Service** | Command-line interface | N/A | Testing and automation |
| **LLM Gateway** | AI operations | 5055 | All AI functionality |
| **Prompt Store** | Prompt management | 5110 | AI prompt optimization |
| **Interpreter** | Natural language processing | 5120 | User query handling |
| **Orchestrator** | Workflow coordination | 5099 | Service orchestration |
| **Doc Store** | Document storage | 5087 | Content persistence |

---

## 🚀 **Getting Started**

### **Step 1: Environment Setup**

```bash
# Clone and navigate to project
git clone <repository-url>
cd LLM-Documentation-Ecosystem

# Start all services (takes 2-3 minutes)
docker-compose -f docker-compose.dev.yml up -d

# Verify all services are healthy
./scripts/validation/health_check_all.sh
```

**Expected Output**: All 17 services showing "healthy" status

### **Step 2: Access the Main Dashboard**

Open your browser to [http://localhost:3000](http://localhost:3000)

**What You'll See**:
- **Service Overview**: Health status of all 17 services
- **Interactive Dashboards**: For each service category
- **CLI Terminal**: Built-in command interface
- **API Browser**: Test APIs directly from the UI

### **Step 3: Verify Your Setup**

```bash
# Test core services
curl http://localhost:5055/health  # LLM Gateway
curl http://localhost:5110/health  # Prompt Store
curl http://localhost:5120/health  # Interpreter

# Should all return: {"status": "healthy", ...}
```

---

## 🎯 **Understanding the Architecture**

### **🏗️ Domain-Driven Design (DDD) Structure**

Our ecosystem follows enterprise DDD patterns:

#### **Bounded Contexts**
```
📁 services/
├── 🤖 AI Services (LLM Gateway, Interpreter, Summarizer Hub)
├── 📊 Analysis Services (Analysis Service, Secure Analyzer, Code Analyzer)
├── 🔧 Infrastructure (Orchestrator, Discovery Agent, Memory Agent)
├── 💾 Data Services (Doc Store, Prompt Store)
├── 🔗 Integration (Source Agent, GitHub MCP, Bedrock Proxy)
└── 🖥️ Presentation (Frontend, CLI, Notification Service)
```

#### **Example: Prompt Store Architecture**
```
services/prompt_store/
├── domain/           # 11 business domains
│   ├── prompts/     # Core prompt management
│   ├── ab_testing/  # A/B testing and optimization
│   ├── analytics/   # Performance metrics
│   └── ...          # 8 more domains
├── infrastructure/  # Technical concerns
├── core/           # Shared entities and models
└── main.py         # Service entry point
```

### **🔄 Communication Patterns**

#### **Synchronous (HTTP APIs)**
- **Direct Service Calls**: For immediate responses
- **REST APIs**: Standard CRUD operations
- **Health Checks**: Service monitoring

#### **Asynchronous (Events)**
- **Redis Events**: For workflow coordination
- **Background Tasks**: For long-running operations
- **Event Sourcing**: For audit trails and state management

---

## 🛠️ **Development Workflow**

### **🎯 Common Development Tasks**

#### **1. Testing an API Endpoint**
```bash
# Example: Create a prompt in Prompt Store
curl -X POST http://localhost:5110/api/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "content": "You are a helpful AI assistant",
    "category": "general",
    "tags": ["assistant", "helpful"]
  }'
```

#### **2. Using the LLM Gateway**
```bash
# Example: Generate text with auto-provider selection
curl -X POST http://localhost:5055/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Docker containers in simple terms",
    "max_tokens": 200
  }'
```

#### **3. End-to-End Document Generation**
```bash
# Example: Natural language query to persistent document
curl -X POST http://localhost:5120/execute-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a technical specification document for a REST API",
    "format": "markdown"
  }'
```

### **🧪 Using the CLI Interface**

The CLI provides powerful development and testing capabilities:

```bash
# Access via web terminal (http://localhost:3000/cli/terminal) or docker exec

# Test service health
./cli.py health-check

# Execute workflows
./cli.py execute-e2e-query --query "Generate test data" --format json

# Browse stored data
./cli.py list-prompts --category development
./cli.py list-documents --workflow test_generation

# Get service metrics
./cli.py get-service-metrics --service llm-gateway
```

---

## 📚 **Key Resources for Developers**

### **📖 Essential Documentation**

1. **[API Documentation Index](API_DOCUMENTATION_INDEX.md)** - Complete API reference
2. **[Architecture Guide](docs/architecture/ARCHITECTURE.md)** - Detailed architecture patterns
3. **[Testing Guide](docs/guides/TESTING_GUIDE.md)** - Testing strategies and examples
4. **[Service READMEs](services/)** - Individual service documentation

### **🎯 Service-Specific Guides**

#### **For AI/ML Development**
- **[LLM Gateway README](services/llm-gateway/README.md)** - Multi-provider AI access
- **[Prompt Store README](services/prompt_store/README.md)** - Advanced prompt management
- **[Interpreter README](services/interpreter/README.md)** - Natural language processing

#### **For Backend Development**
- **[Analysis Service README](services/analysis-service/README.md)** - DDD reference implementation
- **[Orchestrator README](services/orchestrator/README.md)** - Workflow coordination
- **[Doc Store README](services/doc_store/README.md)** - Document management

#### **For Integration Development**
- **[Source Agent README](services/source-agent/README.md)** - Data ingestion patterns
- **[GitHub MCP README](services/github-mcp/README.md)** - GitHub integration
- **[Discovery Agent README](services/discovery-agent/README.md)** - Service discovery

---

## 🔧 **Development Environment Setup**

### **🐳 Docker Development Workflow**

#### **Start Development Environment**
```bash
# Start all services in development mode
docker-compose -f docker-compose.dev.yml up -d

# View logs for specific service
docker-compose -f docker-compose.dev.yml logs -f interpreter

# Restart a single service
docker-compose -f docker-compose.dev.yml restart llm-gateway
```

#### **Code Changes and Hot Reload**
Most services support volume mounting for live development:

```yaml
# Example: services/interpreter/ is mounted for live editing
volumes:
  - ./services/interpreter:/app/services/interpreter
  - ./services/shared:/app/services/shared
```

### **🧪 Testing Your Changes**

#### **Unit Testing**
```bash
# Run tests for specific service
cd services/prompt_store
python -m pytest tests/ -v

# Run all unit tests
python scripts/test_runner.py --unit-only
```

#### **Integration Testing**
```bash
# Test service interactions
python scripts/integration/test_full_integration.py

# Test specific workflow
python scripts/integration/test_document_persistence.py
```

#### **API Testing**
```bash
# Validate all endpoints
python scripts/validation/test_all_endpoints.py

# Test specific service APIs
python scripts/validation/test_api_compatibility.py --service prompt_store
```

---

## 🎯 **Common Use Cases & Examples**

### **🤖 AI-Powered Development**

#### **1. Using LLM Gateway for AI Operations**
```python
import aiohttp
import asyncio

async def test_llm_gateway():
    async with aiohttp.ClientSession() as session:
        # Auto-select best provider
        response = await session.post(
            "http://localhost:5055/query",
            json={
                "prompt": "Generate Python code for a REST API",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        result = await response.json()
        print(f"Provider: {result['provider']}")
        print(f"Response: {result['response']}")

asyncio.run(test_llm_gateway())
```

#### **2. Managing Prompts with Prompt Store**
```python
async def manage_prompts():
    async with aiohttp.ClientSession() as session:
        # Create a new prompt
        await session.post(
            "http://localhost:5110/api/v1/prompts",
            json={
                "content": "Code review: {code}\nProvide suggestions:",
                "category": "development",
                "tags": ["code-review", "development"]
            }
        )
        
        # Search prompts
        response = await session.get(
            "http://localhost:5110/api/v1/prompts?category=development"
        )
        prompts = await response.json()
        print(f"Found {len(prompts['items'])} development prompts")
```

### **📄 Document Processing Workflows**

#### **3. End-to-End Document Generation**
```python
async def generate_document():
    async with aiohttp.ClientSession() as session:
        # Natural language to document
        response = await session.post(
            "http://localhost:5120/execute-query",
            json={
                "query": "Create API documentation for user management",
                "format": "markdown"
            }
        )
        
        result = await response.json()
        document_id = result['document_id']
        
        # Download the generated document
        doc_response = await session.get(
            f"http://localhost:5087/documents/{document_id}/download"
        )
        document_content = await doc_response.text()
        print(f"Generated document ({len(document_content)} chars)")
```

### **🔍 Service Integration Patterns**

#### **4. Service Discovery and Health Monitoring**
```python
async def monitor_ecosystem():
    async with aiohttp.ClientSession() as session:
        # Get all service health
        services = [
            "llm-gateway:5055", "prompt-store:5110", 
            "interpreter:5120", "orchestrator:5099"
        ]
        
        for service in services:
            host, port = service.split(":")
            try:
                response = await session.get(
                    f"http://localhost:{port}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                )
                health = await response.json()
                print(f"{host}: {health['status']}")
            except Exception as e:
                print(f"{host}: ERROR - {e}")
```

---

## 🚨 **Troubleshooting Guide**

### **Common Issues & Solutions**

#### **🔧 Service Won't Start**
```bash
# Check service logs
docker-compose -f docker-compose.dev.yml logs service-name

# Common fixes:
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d --force-recreate
```

#### **🔌 Connection Refused**
```bash
# Verify service is running
docker ps | grep service-name

# Check if port is available
netstat -an | grep PORT_NUMBER

# Restart specific service
docker-compose -f docker-compose.dev.yml restart service-name
```

#### **📦 Import Errors**
Most services use shared modules. If you see import errors:
```bash
# Ensure shared modules are mounted
ls services/shared/  # Should show multiple directories

# Restart with fresh shared modules
docker-compose -f docker-compose.dev.yml restart service-name
```

#### **🗄️ Database/Redis Issues**
```bash
# Check Redis connectivity
docker exec -it hackathon-redis-1 redis-cli ping
# Should return: PONG

# Reset Redis if needed
docker-compose -f docker-compose.dev.yml restart redis
```

### **📊 Health Check Dashboard**

Access [http://localhost:3000/services/overview](http://localhost:3000/services/overview) for:
- Real-time service health status
- Performance metrics
- Recent error logs
- Resource utilization

---

## 🎓 **Next Steps & Advanced Topics**

### **🚀 Ready to Contribute?**

1. **Start with Simple Changes**:
   - Add a new endpoint to an existing service
   - Enhance error messages or logging
   - Improve documentation or examples

2. **Intermediate Challenges**:
   - Add new analysis capabilities to Analysis Service
   - Create new prompt optimization algorithms
   - Implement additional AI provider integrations

3. **Advanced Projects**:
   - Design new bounded contexts using DDD
   - Implement new event sourcing patterns
   - Create cross-service workflow orchestrations

### **📚 Deep Learning Resources**

- **[DDD Implementation Guide](docs/architecture/DDD_MIGRATION.md)** - Learn our DDD patterns
- **[Event Sourcing Examples](services/orchestrator/domain/)** - See event sourcing in action
- **[CQRS Patterns](services/prompt_store/domain/)** - Command/Query separation examples
- **[Microservices Communication](docs/architecture/FEATURES_AND_INTERACTIONS.md)** - Service interaction patterns

### **🔧 Development Tools**

- **API Testing**: Use the built-in frontend API browser
- **Database Inspection**: Access Redis CLI via `docker exec`
- **Log Analysis**: Use `docker-compose logs` with service filtering
- **Performance Monitoring**: Built-in metrics endpoints on all services

---

## 🎉 **Welcome to the Team!**

You're now ready to work with our enterprise-grade LLM Documentation Ecosystem. The architecture is designed to be:

- **Developer-Friendly**: Clear patterns and comprehensive documentation
- **Scalable**: Microservices with proper bounded contexts
- **AI-First**: Complete LLM integration infrastructure
- **Production-Ready**: Enterprise patterns and monitoring

### **🤝 Getting Help**

- **Architecture Questions**: Review service READMEs and architecture docs
- **API Questions**: Check the [API Documentation Index](API_DOCUMENTATION_INDEX.md)
- **Testing Issues**: Follow the [Testing Guide](docs/guides/TESTING_GUIDE.md)
- **Development Patterns**: Study the DDD implementations in core services

**Happy coding!** 🚀 You're working with one of the most sophisticated open-source AI ecosystems available.
