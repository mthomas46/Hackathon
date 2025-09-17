# LLM Documentation Ecosystem

A modular, service-oriented platform for documentation analysis, prompt management, natural language workflows, and developer tooling. Built with FastAPI, Redis, and a microservices architecture.

## 🚀 Quick Start (3 minutes)

```bash
# 1. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/requirements.base.txt

# 2. Run the test suite to verify setup
pytest -q

# 3. Start core services locally
python services/orchestrator/main.py     # 5099 - Control plane
python services/doc_store/main.py        # 5087 - Document storage
python services/source-agent/main.py     # 5000 - Data ingestion
```

## 📋 What This Project Does

- **Document Analysis**: AI-powered consistency checking across documentation sources
- **Prompt Management**: Version-controlled prompt storage with A/B testing
- **Natural Language Workflows**: Intent recognition and automated task execution
- **Multi-Source Integration**: GitHub, Jira, Confluence, and custom sources
- **Developer Tooling**: CLI interface, web UI, and comprehensive APIs

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source Agent  │───▶│  Orchestrator   │───▶│ Analysis Service│
│ (GitHub, Jira,  │    │ (Control Plane) │    │ (AI Analysis)   │
│  Confluence)    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Doc Store     │    │  Prompt Store   │    │   Summarizer    │
│ (Document DB)   │    │ (Prompt Mgmt)   │    │   Hub (LLMs)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🧪 Comprehensive Testing Suite

### **End-to-End Workflow Testing**
The ecosystem includes comprehensive testing that validates complete workflows from mock data generation through final report creation.

```bash
# Run the complete end-to-end test (recommended)
python test_end_to_end_workflow.py

# Run comprehensive test suite with parallel execution
python tests/run_mock_data_generator_tests.py --comprehensive
python tests/run_llm_gateway_tests.py --parallel --workers 4
```

### **Test Coverage Areas**
- ✅ **Mock Data Generation**: LLM-integrated realistic test data
- ✅ **Service Integration**: All 8+ services working together
- ✅ **End-to-End Workflows**: Complete user journey validation
- ✅ **Performance Testing**: Scalability and load testing
- ✅ **Parallel Execution**: Multi-worker test execution
- ✅ **Coverage Reporting**: 85%+ code coverage requirements

### **Quick Test Commands**
```bash
# Test service health
python test_end_to_end_workflow.py

# Run all unit tests in parallel
python tests/run_llm_gateway_tests.py --parallel

# Run mock data generator tests
python tests/run_mock_data_generator_tests.py --unit

# Generate coverage reports
pytest --cov=services --cov-report=html
```

## 🔧 Development Environment

### Prerequisites
- **Python**: 3.11 or higher
- **Redis**: For caching and message queues (optional for basic development)
- **Git**: For version control

### Local Development Setup

1. **Clone and setup**:
```bash
git clone <repository-url>
cd llm-documentation-ecosystem
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/requirements.base.txt
```

2. **Start Redis** (optional, for full functionality):
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
brew install redis && redis-server
```

3. **Run development stack**:
```bash
# Start core services
docker-compose -f docker-compose.dev.yml up -d orchestrator doc_store source-agent

# Or run individually
python services/orchestrator/main.py &
python services/doc_store/main.py &
python services/source-agent/main.py &
```

4. **Verify setup**:
```bash
# Run tests
pytest tests/unit/orchestrator/ -v

# Check service health
curl http://localhost:5099/health/system
```

## 📚 Documentation

| Section | Description | Key Files |
|---------|-------------|-----------|
| **🚀 Getting Started** | Quick setup and first steps | [`docs/guides/GETTING_STARTED.md`](docs/guides/GETTING_STARTED.md) |
| **🏗️ Architecture** | System design and patterns | [`docs/architecture/`](docs/architecture/) |
| **🧪 Testing** | Test suite and patterns | [`docs/guides/TESTING_GUIDE.md`](docs/guides/TESTING_GUIDE.md) |
| **⚙️ Operations** | Deployment and monitoring | [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md) |
| **🔧 Development** | Code standards and tools | [`docs/development/`](docs/development/) |

### Service Documentation

| Service | Port | Purpose | Documentation |
|---------|------|---------|---------------|
| **Orchestrator** | 5099 | Control plane, workflows | [`services/orchestrator/`](services/orchestrator/) |
| **Doc Store** | 5087 | Document storage & search | [`services/doc_store/`](services/doc_store/) |
| **Source Agent** | 5000 | Multi-source data ingestion | [`services/source-agent/`](services/source-agent/) |
| **Analysis Service** | 5020 | AI-powered analysis | [`services/analysis-service/`](services/analysis-service/) |
| **Prompt Store** | 5110 | Prompt management | [`services/prompt-store/`](services/prompt-store/) |
| **Interpreter** | 5120 | Natural language processing | [`services/interpreter/`](services/interpreter/) |
| **Summarizer Hub** | 5060 | LLM provider abstraction | [`services/summarizer-hub/`](services/summarizer-hub/) |
| **CLI** | N/A | Command-line interface | [`services/cli/`](services/cli/) |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific service tests
pytest tests/unit/orchestrator/ -v

# Run integration tests
pytest tests/integration/ -v --test-mode=integration

# Run with coverage
pytest --cov=services --cov-report=html
```

## 🤝 Contributing

### Development Workflow
1. **Fork and clone** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make changes** following our patterns
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Submit a pull request**

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for all function parameters
- Add comprehensive docstrings
- Keep services consistent with shared utilities in `services/shared/`
- Add/refresh tests under `tests/unit/<service>/`

### Service Development
- Use FastAPI for HTTP services
- Implement standard health endpoints (`/health`)
- Use shared utilities from `services/shared/`
- Follow envelope patterns for API responses
- Add structured logging

## 📞 Support

- **📖 Documentation**: [Full Documentation Index](docs/README.md)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-org/llm-documentation-ecosystem/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-org/llm-documentation-ecosystem/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
