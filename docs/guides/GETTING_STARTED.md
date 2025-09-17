# 🚀 Getting Started Guide

Welcome to the LLM Documentation Ecosystem! This guide will get you up and running in under 15 minutes.

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **Git**: For cloning the repository
- **Terminal/Command Line**: Basic command line knowledge
- **Optional**: Docker for containerized development
- **Optional**: Redis for full functionality

## ⚡ Quick Start (5 minutes)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd llm-documentation-ecosystem

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r services/requirements.base.txt
```

### 2. Verify Installation

```bash
# Run a quick test to verify setup
python -c "import fastapi, uvicorn, pydantic; print('✅ Dependencies installed successfully')"
```

### 3. Run Your First Service

```bash
# Start the orchestrator (control plane)
python services/orchestrator/main.py

# In another terminal, test the service
curl http://localhost:5099/health/system
```

**Expected output:**
```json
{"success": true, "data": {"status": "healthy", "services": {...}}}
```

## 🏗️ Development Environment Setup

### Option 1: Individual Services (Recommended for Development)

```bash
# Terminal 1: Core services
python services/orchestrator/main.py     # Port 5099 - Control plane
python services/doc_store/main.py        # Port 5087 - Document storage

# Terminal 2: Data ingestion
python services/source-agent/main.py     # Port 5000 - Multi-source ingestion

# Terminal 3: AI services (optional)
python services/analysis-service/main.py # Port 5020 - AI analysis
python services/summarizer-hub/main.py   # Port 5060 - LLM providers
```

### Option 2: Docker Compose (Recommended for Full Stack)

```bash
# Start Redis (required for full functionality)
docker run -d -p 6379:6379 redis:7-alpine

# Start the development stack
docker-compose -f docker-compose.dev.yml up -d

# Check service health
curl http://localhost:5099/health/system
```

### Option 3: Minimal Setup (Just Core Services)

```bash
# Start just the essential services
python services/orchestrator/main.py &
python services/doc_store/main.py &
python services/source-agent/main.py &

# Test basic functionality
curl http://localhost:5099/health/system
curl http://localhost:5087/health
curl http://localhost:5000/health
```

## 🧪 Testing Your Setup

### Run the Test Suite

```bash
# Run all tests
pytest

# Run specific service tests
pytest tests/unit/orchestrator/ -v

# Run with verbose output
pytest -v --tb=short

# Run tests for a specific service
pytest tests/unit/doc_store/ -v
```

### Test Core Functionality

```bash
# 1. Test orchestrator health
curl http://localhost:5099/health/system

# 2. Test document ingestion
curl -X POST http://localhost:5000/docs/fetch \
  -H "Content-Type: application/json" \
  -d '{"source": "test", "identifier": "sample"}'

# 3. Test document storage
curl http://localhost:5087/health
```

## 📚 Understanding the Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source Agent  │───▶│  Orchestrator   │───▶│ Analysis Service│
│ (Data Ingestion)│    │ (Control Plane) │    │ (AI Analysis)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Doc Store     │    │  Prompt Store   │    │   Summarizer    │
│ (Document DB)   │    │ (Prompt Mgmt)   │    │   Hub (LLMs)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Services

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Orchestrator** | 5099 | Control plane, workflows | ✅ Core |
| **Doc Store** | 5087 | Document storage & search | ✅ Core |
| **Source Agent** | 5000 | Multi-source data ingestion | ✅ Core |
| **Analysis Service** | 5020 | AI-powered analysis | 🔧 AI |
| **Summarizer Hub** | 5060 | LLM provider abstraction | 🔧 AI |
| **Prompt Store** | 5110 | Prompt management and versioning | 🔧 Advanced |
| **Interpreter** | 5120 | Natural language processing | 🔧 Advanced |
| **CLI** | N/A | Command-line interface | 🔧 Advanced |

## 🎯 Your First Workflow

### 1. Ingest Sample Data

```bash
# Create a test document via the source agent
curl -X POST http://localhost:5000/docs/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "identifier": "sample-doc",
    "scope": {"include_readme": true}
  }'
```

### 2. Check Document Storage

```bash
# Query stored documents
curl "http://localhost:5087/documents/search?q=sample"
```

### 3. Trigger Analysis (if AI services running)

```bash
# Analyze the ingested document
curl -X POST http://localhost:5020/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "document",
    "target_id": "sample-doc",
    "analysis_type": "consistency"
  }'
```

## 🔧 Development Workflow

### 1. Choose a Service to Work On

```bash
# Pick a service based on your interests:
# - orchestrator: Workflow orchestration
# - doc_store: Data persistence
# - source-agent: Data ingestion
# - analysis-service: AI/ML features
```

### 2. Understand the Service Structure

```bash
# Examine a service directory
ls services/orchestrator/
# main.py - FastAPI application
# modules/ - Business logic modules
# README.md - Service documentation
```

### 3. Run Service Tests

```bash
# Test the service you're working on
pytest tests/unit/orchestrator/ -v

# Run with coverage
pytest --cov=services/orchestrator --cov-report=term-missing
```

### 4. Make Your First Change

```bash
# 1. Create a feature branch
git checkout -b feature/my-improvement

# 2. Make your changes
# 3. Add tests for new functionality
# 4. Run tests to verify
pytest tests/unit/<service>/ -v

# 5. Commit your changes
git add .
git commit -m "Add my improvement"
```

## 🐛 Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check for port conflicts
lsof -i :5099  # Check if port is in use

# Check Python environment
python --version
pip list | grep fastapi
```

**Tests failing:**
```bash
# Run with more verbose output
pytest -v --tb=long

# Check test dependencies
pip install -r services/requirements.base.txt
```

**Redis connection issues:**
```bash
# Start Redis if using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
brew install redis
redis-server
```

### Getting Help

- **📖 Documentation**: [Full Documentation Index](../README.md)
- **🐛 Issues**: Check existing GitHub issues
- **💬 Discussions**: Post questions in GitHub Discussions
- **🔍 Logs**: Check service logs for error details

## 📈 Next Steps

### Immediate Next Steps
1. **Explore the codebase**: Look at `services/shared/` for common utilities
2. **Run the full test suite**: `pytest` to understand current functionality
3. **Try the CLI**: `python services/cli/main.py --help`
4. **Read service documentation**: Start with [Orchestrator](../../services/orchestrator/README.md)

### Learning Path
1. **Week 1**: Understand architecture, run services locally
2. **Week 2**: Contribute to existing services, add tests
3. **Week 3**: Add new features or services
4. **Week 4**: Optimize performance, improve documentation

### Advanced Topics
- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing patterns
- [Architecture Overview](../../architecture/README.md) - System design patterns
- [Operations Guide](../../operations/RUNBOOK.md) - Deployment and monitoring
- [API Reference](../../reference/ERRORS_AND_ENVELOPES.md) - API specifications

---

**🎉 Congratulations!** You're now ready to contribute to the LLM Documentation Ecosystem. Happy coding!
