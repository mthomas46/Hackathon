# 🚀 Project Planning Service

**AI-Powered Feature Development Roadmap Planning and Team Orchestration**

[![Status](https://img.shields.io/badge/Status-Phase%201%20Complete-success)]() 
[![Tests](https://img.shields.io/badge/Tests-15%20Passed-brightgreen)]()
[![Coverage](https://img.shields.io/badge/Coverage-Core%20Entities-blue)]()

---

## 📋 Overview

The **Project Planning Service** is the central orchestration hub for comprehensive feature development planning in the LLM Documentation Ecosystem. It provides AI-powered feature analysis, intelligent task decomposition, team capacity management, and resource allocation with complete observability through log-collector integration.

### 🎯 Key Features

- **AI-Powered Feature Analysis** - Analyze feature descriptions using Interpreter and LLM Gateway
- **Intelligent Decomposition** - Break down features into user stories and implementation tasks
- **Complexity Estimation** - AI-driven story point estimation on Fibonacci scale
- **Risk Assessment** - Identify technical, schedule, quality, and business risks
- **Resource Allocation** - Skills-based task assignment with capacity management
- **Comprehensive Logging** - Full integration with log-collector for observability

---

## 🏗️ Architecture

### Domain-Driven Design

```
services/project-planning-service/
├── domain/                     # Business logic and entities
│   ├── entities/
│   │   ├── feature.py         # Feature entity with validation
│   │   ├── task.py            # Task entity with workflow
│   │   └── roadmap.py         # Roadmap entity with releases
│   └── services/
│       └── feature_planning_service.py
├── infrastructure/            # Technical infrastructure
│   ├── database/             # SQLAlchemy models & persistence
│   ├── repositories/         # Data access layer
│   └── integrations/         # Service clients
│       ├── log_collector_client.py
│       ├── interpreter_client.py
│       ├── llm_gateway_client.py
│       └── user_store_client.py
├── presentation/             # API layer
│   └── api/
│       └── routes/
│           └── planning.py   # REST API endpoints
└── tests/                    # Comprehensive test suite
    ├── unit/                 # 15+ unit tests
    └── integration/          # End-to-end workflow tests
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.13+
python3 --version

# Required packages
pip install -r requirements.txt
```

### Running the Service

```bash
# From the service directory
cd services/project-planning-service

# Start the service
uvicorn main:app --host 0.0.0.0 --port 5170 --reload
```

### Health Check

```bash
curl http://localhost:5170/health
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:5170/docs
- **ReDoc**: http://localhost:5170/redoc

---

## 📡 API Endpoints

### Feature Analysis

**POST** `/api/v1/planning/analyze`

Analyze a feature description using AI to extract requirements, estimate complexity, and identify risks.

**Request:**
```json
{
  "title": "User Authentication System",
  "description": "Implement secure user authentication with email and password",
  "context": {
    "tech_stack": ["Python", "FastAPI"],
    "priority": "High"
  },
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "feature_id": "uuid",
  "analysis": {...},
  "complexity_score": 7,
  "story_points": 8,
  "estimated_duration_days": 5,
  "risks": {...},
  "user_stories": [...],
  "technical_requirements": {...}
}
```

### Feature Decomposition

**POST** `/api/v1/planning/decompose`

Decompose a feature into detailed tasks with optional automatic assignment.

**Request:**
```json
{
  "feature_id": "feature-uuid",
  "decomposition_level": "detailed",
  "assign_automatically": true,
  "team_id": "team-1"
}
```

### List Features

**GET** `/api/v1/planning/features?status=analyzed&limit=10`

### Get Feature Details

**GET** `/api/v1/planning/features/{feature_id}`

### List Tasks

**GET** `/api/v1/planning/tasks?feature_id={id}&status=todo`

---

## 🧪 Testing

### Run Unit Tests

```bash
# All unit tests (15 tests)
python3 -m pytest tests/unit/test_feature_entity.py -v

# Specific test
python3 -m pytest tests/unit/test_feature_entity.py::TestFeatureEntity::test_create_feature_with_required_fields -v
```

### Run Functional Tests

```bash
# Run complete functional test
python3 functional_test.py
```

**Test Results:**
```
✅ 15/15 unit tests passed
✅ Feature entity validation
✅ Task entity workflow
✅ Status transitions
✅ Business logic
✅ Serialization
```

---

## 🔗 Service Integrations

### 1. Log Collector

**Purpose**: Comprehensive observability and debugging

**Features:**
- Structured logging (INFO, WARNING, ERROR, DEBUG)
- Business event tracking
- API request monitoring
- Integration call tracking

**Usage:**
```python
from infrastructure.integrations.log_collector_client import get_log_client

log_client = get_log_client()
await log_client.log_business_event(
    "feature_analysis_started",
    {"feature_id": feature.id},
    user_id="user-123"
)
```

### 2. Interpreter

**Purpose**: AI-powered content analysis and decomposition

**Features:**
- Feature description analysis
- Entity and intent extraction
- Feature decomposition into tasks
- Acceptance criteria generation
- Technical requirements extraction

### 3. LLM Gateway

**Purpose**: Advanced AI processing with multi-provider routing

**Features:**
- Complexity analysis (1-10 score)
- Story point estimation (Fibonacci)
- Risk assessment
- User story generation

### 4. User Store

**Purpose**: Team capacity management and resource allocation

**Features:**
- Get team members with skills
- Find best assignee by skills matching
- Allocate capacity to tasks
- Track user availability

---

## 📊 Database Schema

### Core Tables

- **projects** - High-level project organization
- **features** - Feature entities with AI analysis
- **tasks** - Implementation tasks with assignments
- **roadmaps** - Development roadmaps
- **releases** - Release milestones
- **team_members** - Team capacity and skills
- **planning_sessions** - Collaborative planning

### Relationships

- Projects → Features (1:many)
- Features → Tasks (1:many)
- Roadmaps → Features (1:many)
- Roadmaps → Releases (1:many)

---

## 📈 Implementation Status

### ✅ Phase 1: Complete

- [x] Domain entities (Feature, Task, Roadmap)
- [x] Database models and schema
- [x] Repository pattern implementation
- [x] Integration clients (4 services)
- [x] API routes and endpoints
- [x] Request/response models
- [x] Lifecycle management
- [x] Unit tests (15+ tests)
- [x] Integration tests
- [x] Functional tests
- [x] Comprehensive logging

### 🔄 Phase 2: Planned

- [ ] Extend Source Agent with Jira/Confluence connectors
- [ ] Enhance Interpreter with domain-specific models
- [ ] Intelligent document sampling
- [ ] Advanced prompt templates

### 🔄 Phase 3: Planned

- [ ] Team capacity extensions in User Store
- [ ] Skills management and matching
- [ ] Resource allocation algorithms
- [ ] Team velocity tracking

---

## 💡 Usage Examples

### Example 1: Analyze a Feature

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:5170/api/v1/planning/analyze",
        json={
            "title": "User Authentication System",
            "description": "Implement secure authentication with email/password",
            "context": {"tech_stack": ["Python", "FastAPI"]},
            "user_id": "user-123"
        }
    )
    result = response.json()
    print(f"Feature ID: {result['feature_id']}")
    print(f"Story Points: {result['story_points']}")
    print(f"Complexity: {result['complexity_score']}")
```

### Example 2: Decompose into Tasks

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:5170/api/v1/planning/decompose",
        json={
            "feature_id": "feature-uuid",
            "decomposition_level": "detailed",
            "assign_automatically": True,
            "team_id": "team-1"
        }
    )
    result = response.json()
    print(f"Tasks created: {len(result['tasks'])}")
    print(f"Total story points: {result['total_story_points']}")
```

---

## 📚 Documentation

- **Implementation Status**: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **Roadmap Plan**: [/docs/FEATURE_DEVELOPMENT_ROADMAP_IMPLEMENTATION_PLAN.md](/docs/FEATURE_DEVELOPMENT_ROADMAP_IMPLEMENTATION_PLAN.md)
- **API Docs**: `/docs` endpoint (Swagger UI)
- **Architecture Docs**: `/docs/architecture/`

---

## 🐛 Troubleshooting

### Import Errors

If you encounter import errors when running tests:

```bash
# Run from project root
cd /Users/mykalthomas/Documents/work/Hackathon
python3 -m pytest services/project-planning-service/tests/unit/ -v
```

### Database Initialization

The database is automatically initialized on service startup. To reset:

```python
from infrastructure.database import drop_database, init_database

drop_database()  # Caution: deletes all data
init_database()
```

---

## 🎯 Success Metrics

**Phase 1 Achievements:**
- ✅ 100% of core domain entities implemented
- ✅ 4/4 service integrations operational
- ✅ 15/15 unit tests passing
- ✅ Complete logging integration
- ✅ API endpoints functional
- ✅ Production-ready error handling

---

## 📞 Support

For issues, questions, or contributions:

- Check the [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- Review the [Roadmap Plan](/docs/FEATURE_DEVELOPMENT_ROADMAP_IMPLEMENTATION_PLAN.md)
- Run functional tests: `python3 functional_test.py`

---

**Version**: 1.0.0  
**Status**: Phase 1 Complete ✅  
**Last Updated**: October 3, 2025

