---
llm_metadata:
  document_type: reference
  content_focus: technical
  platform:
    primary: shared
  status: active
  created_date: '2025-10-07'
  last_modified: '2025-10-07'
  topics:
  - project_management
  - integration
  - asana
  - linear
  - jira
  - workflow_automation
  concepts: []
  technologies:
  - python
  - fastapi
  - asana_api
  - linear_api
  - jira_api
  semantic_summary: Reference documentation for the PM Integration service providing unified project management tool integration and workflow automation
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 📋 PM Integration Service

**Port: 8019** | **Purpose: Unified Project Management & Workflow Integration Platform**

The PM Integration Service provides comprehensive integration with popular project management tools (Asana, Linear, Jira), enabling seamless workflow automation, task synchronization, and project tracking across the LLM Documentation Ecosystem.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PM Tools      │    │   PM Integration│    │  Unified API    │
│                 │◄──►│   Service       │◄──►│   Interface     │
│ • Asana         │    │   (Port 8019)   │    │                 │
│ • Linear        │    │                 │    │ • Task Mgmt     │
│ • Jira          │    │ • Multi-Platform│    │ • Project Sync  │
│ • Custom APIs   │    │ • Workflow Auto │    │ • Status Updates│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Event Bridge   │    │   Data Sync     │    │   Analytics     │
│                 │    │   Engine        │    │                 │
│ • Webhook Proc  │    │                 │    │ • Progress      │
│ • Event Routing │    │ • Bidirectional │    │ • Velocity      │
│ • Queue Mgmt    │    │ • Conflict Res  │    │ • Forecasting   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Core Features

### 🔗 Multi-Platform Integration
- **Asana Integration**: Complete task, project, and workspace management
- **Linear Integration**: Issue tracking, project management, and team workflows
- **Jira Integration**: Enterprise project management and issue tracking
- **Custom API Support**: Extensible architecture for additional PM tools

### 🔄 Bidirectional Synchronization
- **Real-Time Sync**: Instant updates across all connected platforms
- **Conflict Resolution**: Intelligent merging of changes and updates
- **Data Mapping**: Flexible field mapping between different systems
- **Status Synchronization**: Keep task statuses aligned across platforms

### 🤖 Workflow Automation
- **Trigger-Based Actions**: Automate workflows based on PM events
- **Rule Engine**: Configurable automation rules and conditions
- **Template System**: Standardized project and task templates
- **Notification System**: Automated alerts and status updates

### 📊 Analytics & Reporting
- **Progress Tracking**: Project velocity and completion metrics
- **Team Productivity**: Individual and team performance analytics
- **Workflow Efficiency**: Identify bottlenecks and optimization opportunities
- **Predictive Insights**: Project completion forecasting and risk assessment

## 📋 Supported PM Platforms

### Asana Integration
- **Workspaces**: Multi-workspace support with access control
- **Projects**: Complete project lifecycle management
- **Tasks**: Task creation, assignment, due dates, and dependencies
- **Teams**: Team management and collaboration features
- **Portfolios**: Program-level project portfolio management

### Linear Integration
- **Issues**: Issue tracking with labels, priorities, and assignees
- **Projects**: Project management with milestones and timelines
- **Teams**: Team organization and workflow management
- **Cycles**: Sprint-based development cycles
- **Roadmaps**: Long-term planning and feature roadmaps

### Jira Integration
- **Projects**: Project configuration and management
- **Issues**: Comprehensive issue tracking and management
- **Workflows**: Custom workflow definitions and transitions
- **Boards**: Agile boards and kanban workflows
- **Reports**: Built-in reporting and analytics capabilities

## 🛠️ API Endpoints

### Platform Management
```bash
# Connect to PM platform
POST /api/v1/platforms/connect
{
  "platform": "asana",
  "credentials": {
    "access_token": "your-asana-token",
    "workspace_id": "workspace-123"
  },
  "options": {
    "sync_interval": 300,
    "webhooks_enabled": true
  }
}

# List connected platforms
GET /api/v1/platforms

# Test platform connection
GET /api/v1/platforms/{platform_id}/test

# Disconnect platform
DELETE /api/v1/platforms/{platform_id}
```

### Project Synchronization
```bash
# Sync project from platform
POST /api/v1/projects/sync
{
  "platform": "linear",
  "project_id": "project-456",
  "target_platform": "asana",
  "mapping_rules": {
    "status_mapping": {
      "todo": "To Do",
      "in_progress": "In Progress",
      "done": "Done"
    }
  }
}

# Get project status
GET /api/v1/projects/{project_id}/status

# Update project mapping
PUT /api/v1/projects/{project_id}/mapping
{
  "field_mappings": {
    "title": "summary",
    "description": "description",
    "assignee": "assignee"
  }
}
```

### Task Management
```bash
# Create unified task
POST /api/v1/tasks
{
  "title": "Implement user authentication",
  "description": "Add OAuth2 authentication flow",
  "assignee": "developer@company.com",
  "platforms": ["asana", "linear"],
  "metadata": {
    "priority": "high",
    "labels": ["backend", "security"]
  }
}

# Sync task across platforms
POST /api/v1/tasks/{task_id}/sync

# Get task status across platforms
GET /api/v1/tasks/{task_id}/status

# Update task in all platforms
PUT /api/v1/tasks/{task_id}
{
  "status": "in_progress",
  "comment": "Started implementation"
}
```

### Workflow Automation
```bash
# Create automation rule
POST /api/v1/automations
{
  "name": "Code Review Assignment",
  "trigger": {
    "platform": "github",
    "event": "pull_request.opened",
    "conditions": {
      "labels": ["backend"]
    }
  },
  "actions": [
    {
      "platform": "asana",
      "action": "create_task",
      "template": "code_review_task",
      "assignee": "lead-developer@company.com"
    }
  ]
}

# List active automations
GET /api/v1/automations

# Test automation rule
POST /api/v1/automations/{automation_id}/test

# Disable automation
PUT /api/v1/automations/{automation_id}
{
  "enabled": false
}
```

## ⚙️ Configuration

### Environment Variables
```bash
# Service Configuration
PM_INTEGRATION_PORT=8019
PM_INTEGRATION_HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/pm_integration

# Redis for Caching & Queues
REDIS_URL=redis://localhost:6379

# API Keys & Tokens
ASANA_ACCESS_TOKEN=your-asana-token
LINEAR_API_KEY=your-linear-key
JIRA_USERNAME=your-jira-user
JIRA_API_TOKEN=your-jira-token
JIRA_BASE_URL=https://your-domain.atlassian.net

# Security
API_KEY=your-service-key
ENABLE_HTTPS=true
WEBHOOK_SECRET=your-webhook-secret
```

### Platform Configuration
```yaml
# platforms.yaml
platforms:
  asana:
    enabled: true
    access_token: "${ASANA_ACCESS_TOKEN}"
    workspace_id: "123456789"
    sync_interval_seconds: 300
    webhooks_enabled: true

  linear:
    enabled: true
    api_key: "${LINEAR_API_KEY}"
    team_id: "team-123"
    sync_interval_seconds: 180
    webhooks_enabled: true

  jira:
    enabled: true
    base_url: "${JIRA_BASE_URL}"
    username: "${JIRA_USERNAME}"
    api_token: "${JIRA_API_TOKEN}"
    project_key: "PROJ"
    sync_interval_seconds: 600

automations:
  enabled: true
  max_concurrent: 10
  retry_attempts: 3
  retry_delay_seconds: 60

logging:
  level: "INFO"
  format: "json"
  file_path: "/var/log/pm-integration.log"
```

### Docker Deployment
```yaml
version: '3.8'
services:
  pm-integration:
    image: pm-integration:latest
    ports:
      - "8019:8019"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/pm_integration
      - REDIS_URL=redis://redis:6379
      - ASANA_ACCESS_TOKEN=${ASANA_ACCESS_TOKEN}
      - LINEAR_API_KEY=${LINEAR_API_KEY}
    volumes:
      - ./platforms.yaml:/app/config/platforms.yaml
      - ./logs:/var/log/pm-integration
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: pm_integration
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 🔄 Synchronization Engine

### Real-Time Synchronization
- **Webhook Processing**: Instant updates from PM platform events
- **Event Queue**: Asynchronous processing with guaranteed delivery
- **Conflict Resolution**: Intelligent merging of concurrent changes
- **Rollback Support**: Undo erroneous synchronizations

### Batch Synchronization
- **Scheduled Sync**: Regular full synchronization cycles
- **Incremental Updates**: Only sync changed items to improve performance
- **Progress Tracking**: Monitor long-running synchronization jobs
- **Error Recovery**: Resume interrupted synchronizations

### Data Mapping & Transformation
- **Field Mapping**: Configurable field mappings between platforms
- **Data Transformation**: Convert data formats and structures
- **Validation Rules**: Ensure data integrity during synchronization
- **Custom Mappings**: Support for platform-specific field requirements

## 📊 Analytics & Reporting

### Project Analytics
- **Velocity Tracking**: Team and project velocity measurements
- **Burndown Charts**: Sprint and project progress visualization
- **Cycle Time Analysis**: Measure time from creation to completion
- **Predictive Forecasting**: Project completion date predictions

### Team Performance
- **Individual Metrics**: Personal productivity and contribution analysis
- **Team Collaboration**: Cross-team work and dependency tracking
- **Workload Balancing**: Identify overloaded team members
- **Skill Utilization**: Track usage of different skill sets

### Workflow Efficiency
- **Bottleneck Identification**: Find workflow slowdowns and blockages
- **Process Optimization**: Suggest workflow improvements
- **Automation Impact**: Measure effectiveness of automated processes
- **Quality Metrics**: Track error rates and rework percentages

## 🔧 Troubleshooting

### Common Issues

#### Connection Failures
```bash
# Test platform connectivity
curl http://localhost:8019/api/v1/platforms/asana/test

# Check API credentials
curl -H "Authorization: Bearer $ASANA_ACCESS_TOKEN" \
  https://app.asana.com/api/1.0/users/me

# Verify webhook endpoints
curl http://localhost:8019/health/webhooks
```

#### Synchronization Issues
```bash
# Check sync status
curl http://localhost:8019/api/v1/sync/status

# View sync logs
curl http://localhost:8019/api/v1/sync/logs?limit=50

# Force manual sync
curl -X POST http://localhost:8019/api/v1/sync/manual \
  -H "Content-Type: application/json" \
  -d '{"platform": "asana", "full_sync": true}'
```

#### Automation Failures
```bash
# List failed automations
curl "http://localhost:8019/api/v1/automations?status=failed"

# Check automation logs
curl http://localhost:8019/api/v1/automations/logs

# Test automation rule
curl -X POST http://localhost:8019/api/v1/automations/123/test
```

## 🔗 Integration Examples

### Basic PM Tool Integration
```python
import requests

class PMIntegrationClient:
    def __init__(self, base_url="http://localhost:8019"):
        self.base_url = base_url

    def connect_platform(self, platform, credentials):
        """Connect to a PM platform."""
        response = requests.post(
            f"{self.base_url}/api/v1/platforms/connect",
            json={
                "platform": platform,
                "credentials": credentials
            }
        )
        return response.json()

    def create_unified_task(self, task_data):
        """Create a task that syncs across all connected platforms."""
        response = requests.post(
            f"{self.base_url}/api/v1/tasks",
            json=task_data
        )
        return response.json()

    def get_project_status(self, project_id):
        """Get project status across all platforms."""
        response = requests.get(f"{self.base_url}/api/v1/projects/{project_id}/status")
        return response.json()

# Usage
client = PMIntegrationClient()

# Connect to Asana
asana_creds = {"access_token": "your-token", "workspace_id": "123"}
client.connect_platform("asana", asana_creds)

# Create unified task
task = client.create_unified_task({
    "title": "Implement user dashboard",
    "description": "Create responsive user dashboard with real-time data",
    "assignee": "developer@company.com",
    "platforms": ["asana", "linear"],
    "metadata": {"priority": "high", "component": "frontend"}
})
```

### Workflow Automation
```python
import requests

class WorkflowAutomation:
    def __init__(self, base_url="http://localhost:8019"):
        self.base_url = base_url

    def create_code_review_automation(self):
        """Create automation for code review assignment."""
        automation = {
            "name": "PR Code Review Assignment",
            "trigger": {
                "platform": "github",
                "event": "pull_request.opened",
                "conditions": {
                    "base_branch": "main",
                    "required_labels": ["backend"]
                }
            },
            "actions": [
                {
                    "platform": "asana",
                    "action": "create_task",
                    "template": "code_review_template",
                    "assignee_field": "lead_backend_developer"
                },
                {
                    "platform": "linear",
                    "action": "create_issue",
                    "template": "code_review_issue",
                    "priority": "high"
                }
            ]
        }

        response = requests.post(f"{self.base_url}/api/v1/automations", json=automation)
        return response.json()

    def create_release_automation(self):
        """Create automation for release process."""
        automation = {
            "name": "Release Process Automation",
            "trigger": {
                "platform": "github",
                "event": "release.published"
            },
            "actions": [
                {
                    "platform": "jira",
                    "action": "transition_issues",
                    "jql": "fixVersion = {release.version}",
                    "transition": "Ready for Release"
                },
                {
                    "platform": "asana",
                    "action": "update_project_status",
                    "project_id": "release_project",
                    "status": "released"
                }
            ]
        }

        response = requests.post(f"{self.base_url}/api/v1/automations", json=automation)
        return response.json()

# Usage
automation = WorkflowAutomation()
code_review = automation.create_code_review_automation()
release_auto = automation.create_release_automation()
```

## 📚 Dependencies

- **Python 3.9+**
- **FastAPI**: Web API framework
- **SQLAlchemy**: Database ORM
- **Redis**: Caching and message queuing
- **asana**: Asana API client
- **linear-sdk**: Linear API client
- **jira**: Atlassian Jira API client
- **requests**: HTTP client for webhooks
- **apscheduler**: Task scheduling

## 🚀 Getting Started

1. **Obtain API credentials**
   ```bash
   # Asana: Get personal access token
   # Linear: Get API key from workspace settings
   # Jira: Get API token from Atlassian account
   ```

2. **Configure environment**
   ```bash
   export PM_INTEGRATION_PORT=8019
   export DATABASE_URL=postgresql://user:pass@localhost:5432/pm_integration
   export REDIS_URL=redis://localhost:6379
   export ASANA_ACCESS_TOKEN=your-asana-token
   export LINEAR_API_KEY=your-linear-key
   ```

3. **Create platform configuration**
   ```yaml
   # platforms.yaml
   platforms:
     asana:
       enabled: true
       access_token: "${ASANA_ACCESS_TOKEN}"
     linear:
       enabled: true
       api_key: "${LINEAR_API_KEY}"
   ```

4. **Run database migrations**
   ```bash
   cd services/pm-integration
   alembic upgrade head
   ```

5. **Start the service**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8019
   ```

6. **Connect platforms**
   ```bash
   curl -X POST http://localhost:8019/api/v1/platforms/connect \
     -H "Content-Type: application/json" \
     -d '{"platform": "asana", "credentials": {"access_token": "your-token"}}'
   ```

## 🎯 Use Cases

### Development Workflow Integration
- **Pull Request Management**: Automatic task creation for code reviews
- **Sprint Planning**: Sync sprint tasks across development tools
- **Release Coordination**: Automated release checklist and tracking
- **Bug Tracking**: Unified bug reporting and tracking

### Product Management
- **Feature Development**: Track feature requests from ideation to delivery
- **Roadmap Planning**: Synchronize product roadmaps across tools
- **Stakeholder Communication**: Keep all stakeholders informed of progress
- **Requirements Gathering**: Centralized requirements management

### Team Collaboration
- **Cross-Team Coordination**: Align work across engineering, design, and product teams
- **Resource Planning**: Track team capacity and workload distribution
- **Progress Reporting**: Automated status updates and reporting
- **Knowledge Sharing**: Share project information across different tools

### Enterprise Integration
- **Compliance Tracking**: Ensure all work meets regulatory requirements
- **Audit Trails**: Complete audit logs of all project activities
- **Governance**: Centralized governance and oversight
- **Reporting**: Executive dashboards and business intelligence

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository>
cd services/pm-integration

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb pm_integration
alembic upgrade head

# Configure platforms for testing
cp config/platforms.example.yaml config/platforms.yaml

# Run tests
pytest tests/

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8019
```

### Adding New PM Platforms
1. **Create platform client** in the platforms directory
2. **Implement platform interface** with standard CRUD operations
3. **Add data mapping logic** for field transformations
4. **Create webhook handlers** for real-time updates
5. **Add platform tests** and integration tests
6. **Update documentation** with new platform details

## 📄 License

This service is part of the LLM Documentation Ecosystem. See project LICENSE for details.

---

**Status:** 🟢 Production Ready | **Port:** 8019 | **Platforms:** Asana, Linear, Jira | **Features:** Multi-platform sync, Workflow automation, Analytics
