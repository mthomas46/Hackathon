# Roadmap Orchestration API Documentation

## Overview

The Roadmap Orchestration API provides comprehensive endpoints for generating, validating, and managing development roadmaps using AI-powered intelligence.

**Base URL:** `http://localhost:5170/api/v1/roadmap`

---

## Endpoints

### 1. Generate Roadmap

**POST** `/api/v1/roadmap/generate`

Generate a comprehensive development roadmap from features.

#### Request Body

```json
{
  "features": [
    {
      "id": "f1",
      "title": "User Authentication",
      "description": "Implement login and registration",
      "priority": "high",
      "estimated_effort": 13.0,
      "dependencies": []
    },
    {
      "id": "f2",
      "title": "Dashboard",
      "description": "Admin dashboard",
      "priority": "medium",
      "estimated_effort": 8.0,
      "dependencies": ["f1"]
    }
  ],
  "team_id": "team-alpha",
  "start_date": "2025-01-01",
  "team_velocity": 20.0,
  "sprint_duration_weeks": 2,
  "generation_strategy": "sprint_based",
  "create_milestones": true,
  "milestone_frequency_weeks": 4
}
```

#### Response (201 Created)

```json
{
  "roadmap_id": "roadmap-team-alpha",
  "roadmap_name": "Development Roadmap - team-alpha",
  "start_date": "2025-01-01",
  "end_date": "2025-02-14",
  "total_features": 2,
  "total_sprints": 2,
  "estimated_completion": "2025-02-14",
  "story_points": 21.0,
  "milestone_count": 1,
  "milestones": [
    {
      "id": "milestone-1",
      "name": "Milestone 1",
      "description": "Complete 2 features",
      "milestone_type": "phase",
      "target_date": "2025-01-29",
      "feature_ids": ["f1", "f2"],
      "completed": false,
      "story_points": 21.0
    }
  ],
  "warnings": [
    "Feature decomposition temporarily disabled in orchestrator (requires async implementation)",
    "Dependency analysis temporarily disabled due to known issue"
  ],
  "recommendations": [],
  "confidence_score": 0.85
}
```

---

### 2. Validate Roadmap

**POST** `/api/v1/roadmap/validate`

Validate roadmap generation request without full generation.

#### Request Body

Same as generate roadmap.

#### Response (200 OK)

```json
{
  "valid": true,
  "quality_score": 0.85,
  "checks_passed": [
    "All features are included in roadmap",
    "Timeline estimate available",
    "No circular dependencies",
    "All features scheduled",
    "1 milestones defined"
  ],
  "issues": [],
  "warnings": [
    "Feature decomposition temporarily disabled in orchestrator (requires async implementation)"
  ]
}
```

---

### 3. Health Check

**GET** `/api/v1/roadmap/health`

Check service health and component status.

#### Response (200 OK)

```json
{
  "status": "healthy",
  "service": "roadmap-orchestration",
  "components": {
    "roadmap_generator": "available",
    "timeline_estimator": "available",
    "milestone_planner": "available",
    "feature_decomposer": "disabled (requires async)",
    "dependency_resolver": "disabled (known issue)"
  }
}
```

---

### 4. Get Strategies

**GET** `/api/v1/roadmap/strategies`

Get available roadmap generation strategies.

#### Response (200 OK)

```json
{
  "strategies": [
    {
      "id": "sprint_based",
      "name": "Sprint-Based Planning",
      "description": "Organize features into fixed-length sprints",
      "best_for": "Agile teams with regular sprint cadence",
      "characteristics": [
        "Predictable sprint boundaries",
        "Even workload distribution",
        "Easy capacity planning"
      ]
    },
    {
      "id": "release_based",
      "name": "Release-Based Planning",
      "description": "Group features into major releases",
      "best_for": "Projects with defined release milestones",
      "characteristics": [
        "Feature grouping by release",
        "Milestone-driven planning",
        "Flexible sprint allocation"
      ]
    }
  ],
  "milestone_strategies": [
    {
      "id": "balanced",
      "name": "Balanced Milestones",
      "description": "Even distribution of work across milestones"
    },
    {
      "id": "sprint_based",
      "name": "Sprint-Aligned Milestones",
      "description": "Milestones aligned with sprint boundaries"
    },
    {
      "id": "value_based",
      "name": "Value-Based Milestones",
      "description": "Milestones grouped by priority/value"
    }
  ]
}
```

---

## Request Parameters

### Feature Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique feature identifier |
| `title` | string | Yes | Feature title |
| `description` | string | Yes | Feature description |
| `priority` | string | No | Priority: "low", "medium", "high", "critical" (default: "medium") |
| `estimated_effort` | number | No | Story points estimate (default: 5.0) |
| `dependencies` | array | No | List of feature IDs this depends on |

### Roadmap Generation Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `features` | array | Yes | List of Feature objects |
| `team_id` | string | Yes | Team identifier |
| `start_date` | date | Yes | Project start date (YYYY-MM-DD) |
| `team_velocity` | number | No | Story points per sprint (default: 20.0) |
| `sprint_duration_weeks` | integer | No | Sprint length in weeks (default: 2) |
| `generation_strategy` | string | No | "sprint_based" or "release_based" (default: "sprint_based") |
| `decompose_features` | boolean | No | Enable feature decomposition (default: false, requires async) |
| `analyze_dependencies` | boolean | No | Enable dependency analysis (default: false, known issue) |
| `create_milestones` | boolean | No | Generate milestones (default: true) |
| `milestone_frequency_weeks` | integer | No | Weeks between milestones (default: 4) |

---

## Response Objects

### Milestone Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Milestone identifier |
| `name` | string | Milestone name |
| `description` | string | Milestone description |
| `milestone_type` | string | Type: "phase", "sprint", "release", "deliverable" |
| `target_date` | date | Target completion date |
| `feature_ids` | array | Features included in milestone |
| `completed` | boolean | Completion status |
| `story_points` | number | Total story points |

---

## Example Usage

### cURL Example

```bash
curl -X POST "http://localhost:5170/api/v1/roadmap/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [
      {
        "id": "f1",
        "title": "User Authentication",
        "description": "Implement login system",
        "priority": "high",
        "estimated_effort": 13.0
      }
    ],
    "team_id": "team-1",
    "start_date": "2025-01-01",
    "team_velocity": 20.0,
    "create_milestones": true
  }'
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:5170/api/v1/roadmap/generate",
    json={
        "features": [
            {
                "id": "f1",
                "title": "User Authentication",
                "description": "Implement login system",
                "priority": "high",
                "estimated_effort": 13.0
            }
        ],
        "team_id": "team-1",
        "start_date": "2025-01-01",
        "team_velocity": 20.0,
        "create_milestones": True
    }
)

roadmap = response.json()
print(f"Roadmap ID: {roadmap['roadmap_id']}")
print(f"Milestones: {roadmap['milestone_count']}")
```

### JavaScript Example

```javascript
const response = await fetch('http://localhost:5170/api/v1/roadmap/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    features: [
      {
        id: 'f1',
        title: 'User Authentication',
        description: 'Implement login system',
        priority: 'high',
        estimated_effort: 13.0
      }
    ],
    team_id: 'team-1',
    start_date: '2025-01-01',
    team_velocity: 20.0,
    create_milestones: true
  })
});

const roadmap = await response.json();
console.log(`Roadmap ID: ${roadmap.roadmap_id}`);
console.log(`Milestones: ${roadmap.milestone_count}`);
```

---

## Error Responses

### 400 Bad Request

Invalid request parameters or format.

```json
{
  "detail": "Invalid priority value: invalid_priority"
}
```

### 422 Unprocessable Entity

Request validation failed (missing required fields, invalid types).

```json
{
  "detail": [
    {
      "loc": ["body", "team_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

Server-side processing error.

```json
{
  "detail": "Failed to generate roadmap: <error message>"
}
```

---

## Notes

- **Feature Decomposition:** Currently disabled in the orchestrator (requires async implementation)
- **Dependency Analysis:** Temporarily disabled due to known issue with circular dependency detection
- **Confidence Score:** Calculated based on team velocity data, feature estimates, and timeline feasibility
- **Milestones:** Auto-generated based on feature distribution and sprint allocation

---

## API Access

The API is available when the project-planning-service is running:

```bash
cd services/project-planning-service
python3 main.py
```

Access the interactive API documentation at:
- **Swagger UI:** http://localhost:5170/docs
- **ReDoc:** http://localhost:5170/redoc

