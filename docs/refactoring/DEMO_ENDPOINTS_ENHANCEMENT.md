<!-- AI_READ_PRIORITY: 2 -->
<!-- AI_TAGS: demo-endpoints, testing, standard-apis, automation -->
<!-- AI_KEY_SECTIONS: Demo Endpoints Specification, Implementation Guide -->

---
ai_metadata:
  purpose: demo_endpoints_specification
  read_priority: 2
  context_level: strategic
  tags:
  - demo-endpoints
  - testing
  - standard-apis
  - automation
  when_to_read: During service refactoring (Phase 2, 6, 9) and when implementing demos
  key_sections:
  - Demo Endpoints Specification
  - Implementation Guide
  - Demo Types
  execution_relevance: high
---

# Demo Endpoints Enhancement

**Version**: 1.0.0  
**Created**: October 10, 2025  
**Status**: Approved  
**Impact**: MAJOR - Adds 2 new standard endpoints to all services

---

## 📋 Executive Summary

This document specifies the addition of **2 new standard API endpoints** to all services (excluding dashboards):

1. **`GET /demos`** - Lists all executable demos for the service
2. **`POST /run-demo`** - Executes a specific demo and returns tangible results

These endpoints enable:
- ✅ Automated testing and validation
- ✅ Stakeholder demonstrations
- ✅ Service capability showcasing
- ✅ Onboarding and training
- ✅ Integration testing

---

## 🎯 Motivation

### Problem: No Standardized Demo Mechanism

**Current State**:
- Demos are manual processes
- No programmatic way to execute demos
- Demo planning documents exist but aren't executable
- Stakeholders can't easily see service capabilities

**Desired State**:
- Services can execute demos via API
- Demos are self-documenting via `/demos` endpoint
- Mix of self-contained and ecosystem-based demos
- Tangible data/reports produced

---

## 📖 Endpoint Specifications

### Endpoint 1: `GET /demos`

**Purpose**: List all available demos for this service

**URL**: `/demos`  
**Method**: `GET`  
**Authentication**: Optional (depends on service)

**Response Schema**:
```json
{
  "service": "string",
  "version": "string",
  "demos": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "type": "self-contained | ecosystem | hybrid",
      "duration_seconds": number,
      "requirements": {
        "services_needed": ["string"],
        "credentials_needed": ["string"],
        "data_needed": ["string"]
      },
      "produces": {
        "reports": ["string"],
        "artifacts": ["string"],
        "data_files": ["string"]
      },
      "status": "available | unavailable | blocked",
      "blocker_reason": "string (if status is blocked/unavailable)"
    }
  ],
  "total_demos": number,
  "available_demos": number
}
```

**Example Response**:
```json
{
  "service": "architecture-digitizer",
  "version": "1.0.0",
  "demos": [
    {
      "id": "normalize-miro-sample",
      "name": "Normalize Sample Miro Board",
      "description": "Normalizes a canned Miro board JSON into standard architecture format",
      "type": "self-contained",
      "duration_seconds": 2,
      "requirements": {
        "services_needed": [],
        "credentials_needed": [],
        "data_needed": ["sample_miro_board.json (included)"]
      },
      "produces": {
        "reports": ["normalization_report.json"],
        "artifacts": ["normalized_architecture.json"],
        "data_files": ["components.json", "connections.json"]
      },
      "status": "available",
      "blocker_reason": null
    },
    {
      "id": "architecture-documentation-workflow",
      "name": "Full Architecture Documentation Workflow",
      "description": "Demonstrates end-to-end workflow: normalize diagram -> analyze -> generate docs",
      "type": "ecosystem",
      "duration_seconds": 10,
      "requirements": {
        "services_needed": ["analysis-service", "bedrock-proxy", "doc-store"],
        "credentials_needed": ["AWS_BEDROCK_API_KEY"],
        "data_needed": ["sample_microservices_diagram.json"]
      },
      "produces": {
        "reports": ["architecture_analysis_report.md", "documentation_report.md"],
        "artifacts": ["normalized_diagram.json", "architecture_patterns.json"],
        "data_files": ["stored_doc_id.txt"]
      },
      "status": "blocked",
      "blocker_reason": "AWS_BEDROCK_API_KEY not configured"
    },
    {
      "id": "multi-format-processing",
      "name": "Multi-Format Diagram Processing",
      "description": "Processes Miro, FigJam, and Lucid diagrams sequentially",
      "type": "self-contained",
      "duration_seconds": 5,
      "requirements": {
        "services_needed": [],
        "credentials_needed": [],
        "data_needed": ["sample_miro.json", "sample_figjam.json", "sample_lucid.json (all included)"]
      },
      "produces": {
        "reports": ["multi_format_report.json"],
        "artifacts": ["normalized_miro.json", "normalized_figjam.json", "normalized_lucid.json"],
        "data_files": ["format_comparison.csv"]
      },
      "status": "available",
      "blocker_reason": null
    }
  ],
  "total_demos": 3,
  "available_demos": 2
}
```

**Status Codes**:
- `200 OK` - Demos list returned successfully
- `500 Internal Server Error` - Error retrieving demos

---

### Endpoint 2: `POST /run-demo`

**Purpose**: Execute a specific demo and return results

**URL**: `/run-demo`  
**Method**: `POST`  
**Authentication**: Optional (depends on service)

**Request Schema**:
```json
{
  "demo_id": "string",
  "parameters": {
    "key": "value"
  },
  "output_format": "json | markdown | html",
  "save_artifacts": boolean
}
```

**Response Schema**:
```json
{
  "success": boolean,
  "demo_id": "string",
  "demo_name": "string",
  "execution_time_seconds": number,
  "status": "completed | failed | partial",
  "results": {
    "summary": "string",
    "details": {},
    "metrics": {}
  },
  "reports": [
    {
      "name": "string",
      "type": "string",
      "content": "string",
      "download_url": "string (optional)"
    }
  ],
  "artifacts": [
    {
      "name": "string",
      "type": "string",
      "size_bytes": number,
      "download_url": "string"
    }
  ],
  "logs": ["string"],
  "errors": ["string"],
  "warnings": ["string"]
}
```

**Example Request**:
```json
{
  "demo_id": "normalize-miro-sample",
  "parameters": {},
  "output_format": "json",
  "save_artifacts": true
}
```

**Example Response**:
```json
{
  "success": true,
  "demo_id": "normalize-miro-sample",
  "demo_name": "Normalize Sample Miro Board",
  "execution_time_seconds": 1.8,
  "status": "completed",
  "results": {
    "summary": "Successfully normalized Miro board with 15 components and 12 connections",
    "details": {
      "source_system": "miro",
      "board_id": "sample_board_123",
      "components_extracted": 15,
      "connections_extracted": 12,
      "component_types": {
        "service": 8,
        "database": 4,
        "queue": 2,
        "gateway": 1
      }
    },
    "metrics": {
      "normalization_duration_ms": 1800,
      "validation_passed": true,
      "schema_version": "1.0"
    }
  },
  "reports": [
    {
      "name": "normalization_report.json",
      "type": "application/json",
      "content": "{\"components\": [...], \"connections\": [...]}",
      "download_url": "/demo-artifacts/normalize-miro-sample/normalization_report.json"
    }
  ],
  "artifacts": [
    {
      "name": "normalized_architecture.json",
      "type": "application/json",
      "size_bytes": 4523,
      "download_url": "/demo-artifacts/normalize-miro-sample/normalized_architecture.json"
    },
    {
      "name": "components.json",
      "type": "application/json",
      "size_bytes": 2341,
      "download_url": "/demo-artifacts/normalize-miro-sample/components.json"
    }
  ],
  "logs": [
    "Loading sample Miro board data",
    "Parsing Miro board structure",
    "Extracting 15 components",
    "Extracting 12 connections",
    "Validating normalized data",
    "Normalization complete"
  ],
  "errors": [],
  "warnings": []
}
```

**Status Codes**:
- `200 OK` - Demo executed successfully
- `400 Bad Request` - Invalid demo_id or parameters
- `404 Not Found` - Demo not found
- `409 Conflict` - Demo unavailable (missing requirements)
- `500 Internal Server Error` - Demo execution failed

---

## 🎭 Demo Types

### 1. Self-Contained Demos

**Definition**: Demos that run entirely within the service with canned data, no external dependencies.

**Characteristics**:
- ✅ Always available
- ✅ Use included sample data
- ✅ Fast execution (< 5 seconds)
- ✅ Predictable results
- ✅ Ideal for onboarding and validation

**Examples**:
- `architecture-digitizer`: Normalize sample Miro board JSON
- `code-analyzer`: Analyze sample Python file
- `analysis-service`: Detect patterns in sample codebase

**Implementation**:
```python
# Store sample data in service
SAMPLE_DATA_DIR = Path(__file__).parent / "demo_data"

@router.post("/run-demo")
async def run_demo(request: RunDemoRequest):
    if request.demo_id == "normalize-miro-sample":
        # Load canned data
        sample_data = load_sample_data("miro_board.json")
        
        # Execute normalization
        result = await normalize_miro_data(sample_data)
        
        # Return results with reports
        return DemoResult(
            success=True,
            demo_id="normalize-miro-sample",
            results=result,
            reports=[generate_normalization_report(result)],
            artifacts=[save_artifact(result)]
        )
```

---

### 2. Ecosystem Demos

**Definition**: Demos that integrate with other ecosystem services, demonstrating real workflows.

**Characteristics**:
- ⚠️ May be blocked if services unavailable
- ⚠️ Require credentials or configuration
- ⏱️ Longer execution time (5-30 seconds)
- 🔄 Demonstrate real integration
- 🎯 Show production-like workflows

**Examples**:
- `architecture-digitizer` → `analysis-service` → `bedrock-proxy`: Full architecture documentation workflow
- `code-analyzer` → `bedrock-proxy`: AI code review workflow
- `discovery-agent` → `data-services-dashboard`: Service monitoring workflow

**Implementation**:
```python
@router.post("/run-demo")
async def run_demo(request: RunDemoRequest):
    if request.demo_id == "architecture-documentation-workflow":
        # Check prerequisites
        if not await check_service_available("analysis-service"):
            raise HTTPException(409, "analysis-service not available")
        if not os.getenv("AWS_BEDROCK_API_KEY"):
            raise HTTPException(409, "AWS credentials not configured")
        
        # Execute workflow
        # Step 1: Normalize diagram
        normalized = await normalize_diagram(sample_diagram)
        
        # Step 2: Send to analysis-service
        analysis = await call_analysis_service(normalized)
        
        # Step 3: Generate docs via bedrock-proxy
        docs = await call_bedrock_proxy(analysis)
        
        # Return comprehensive results
        return DemoResult(
            success=True,
            demo_id="architecture-documentation-workflow",
            results={
                "normalized_data": normalized,
                "analysis": analysis,
                "documentation": docs
            },
            reports=[
                generate_workflow_report(normalized, analysis, docs)
            ],
            artifacts=[
                save_artifact(normalized, "normalized.json"),
                save_artifact(analysis, "analysis.json"),
                save_artifact(docs, "documentation.md")
            ]
        )
```

---

### 3. Hybrid Demos

**Definition**: Demos that work self-contained by default but can use ecosystem services if available.

**Characteristics**:
- ✅ Always available (degraded mode if services unavailable)
- ↕️ Enhanced mode with ecosystem integration
- 🎚️ Graceful degradation
- 📊 Shows value of integration

**Example**:
```python
@router.post("/run-demo")
async def run_demo(request: RunDemoRequest):
    if request.demo_id == "architecture-analysis-demo":
        # Step 1: Normalize (always works)
        normalized = await normalize_diagram(sample_diagram)
        
        # Step 2: Try to use analysis-service
        if await check_service_available("analysis-service"):
            analysis = await call_analysis_service(normalized)
            mode = "enhanced"
        else:
            analysis = basic_local_analysis(normalized)
            mode = "basic"
        
        return DemoResult(
            success=True,
            demo_id="architecture-analysis-demo",
            results={
                "mode": mode,
                "normalized_data": normalized,
                "analysis": analysis
            },
            warnings=[] if mode == "enhanced" else [
                "Running in basic mode - analysis-service unavailable"
            ]
        )
```

---

## 🏗️ Implementation Guide

### Step 1: Update Standard Endpoints List

**In Phase 2 (Design & Planning)**: Add `/demos` and `/run-demo` to standard endpoints plan.

**In Phase 6 (Documentation)**: Document these endpoints in service README and OpenAPI spec.

---

### Step 2: Create Demo Data Directory

```bash
services/<service>/
├── demo_data/          # NEW: Canned data for demos
│   ├── sample_input_1.json
│   ├── sample_input_2.json
│   └── expected_output_1.json
├── demo_artifacts/     # NEW: Generated demo artifacts
│   └── .gitkeep
└── presentation/
    └── routes/
        └── demo_routes.py  # NEW: Demo endpoints
```

---

### Step 3: Implement Demo Routes

**File**: `services/<service>/presentation/routes/demo_routes.py`

```python
"""Demo endpoints for <service-name>.

Provides programmatic demo execution for showcasing service capabilities.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import Dict, List, Any
import time
import json

from ...domain.models import DemoInfo, DemoResult, RunDemoRequest

router = APIRouter()

# Demo data directory
DEMO_DATA_DIR = Path(__file__).parent.parent.parent / "demo_data"
DEMO_ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "demo_artifacts"

# Demo registry
DEMOS: List[DemoInfo] = [
    DemoInfo(
        id="demo-1",
        name="Self-Contained Demo",
        description="Description here",
        type="self-contained",
        duration_seconds=2,
        requirements={
            "services_needed": [],
            "credentials_needed": [],
            "data_needed": ["sample_input.json"]
        },
        produces={
            "reports": ["demo_report.json"],
            "artifacts": ["demo_output.json"],
            "data_files": []
        },
        status="available"
    ),
    # Add more demos...
]


@router.get(
    "/demos",
    summary="List Available Demos",
    description="Returns a list of all executable demos for this service",
    tags=["Demos"]
)
async def list_demos() -> Dict[str, Any]:
    """List all available demos for this service."""
    
    # Check demo availability
    available_count = sum(1 for demo in DEMOS if demo.status == "available")
    
    return {
        "service": "service-name",
        "version": "1.0.0",
        "demos": [demo.dict() for demo in DEMOS],
        "total_demos": len(DEMOS),
        "available_demos": available_count
    }


@router.post(
    "/run-demo",
    summary="Execute Demo",
    description="Executes a specific demo and returns results with tangible artifacts",
    tags=["Demos"]
)
async def run_demo(request: RunDemoRequest) -> DemoResult:
    """Execute a specific demo."""
    
    # Find demo
    demo = next((d for d in DEMOS if d.id == request.demo_id), None)
    if not demo:
        raise HTTPException(status_code=404, detail=f"Demo '{request.demo_id}' not found")
    
    # Check availability
    if demo.status != "available":
        raise HTTPException(
            status_code=409, 
            detail=f"Demo unavailable: {demo.blocker_reason}"
        )
    
    # Execute demo
    start_time = time.time()
    
    try:
        # Route to appropriate demo handler
        if request.demo_id == "demo-1":
            result = await execute_demo_1(request.parameters)
        # Add more demo handlers...
        else:
            raise HTTPException(400, f"Demo '{request.demo_id}' not implemented")
        
        execution_time = time.time() - start_time
        
        return DemoResult(
            success=True,
            demo_id=request.demo_id,
            demo_name=demo.name,
            execution_time_seconds=round(execution_time, 2),
            status="completed",
            results=result["results"],
            reports=result["reports"],
            artifacts=result["artifacts"],
            logs=result["logs"],
            errors=[],
            warnings=[]
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        return DemoResult(
            success=False,
            demo_id=request.demo_id,
            demo_name=demo.name,
            execution_time_seconds=round(execution_time, 2),
            status="failed",
            results={},
            reports=[],
            artifacts=[],
            logs=[],
            errors=[str(e)],
            warnings=[]
        )


async def execute_demo_1(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute demo 1: Self-contained demo."""
    
    logs = []
    logs.append("Loading sample data")
    
    # Load canned data
    sample_data = load_demo_data("sample_input.json")
    
    logs.append("Processing data")
    
    # Execute service logic
    result = await process_data(sample_data)
    
    logs.append("Generating reports")
    
    # Generate reports
    report = generate_report(result)
    
    # Save artifacts
    artifact_path = save_artifact(result, "demo_output.json")
    
    logs.append("Demo execution complete")
    
    return {
        "results": {
            "summary": "Demo executed successfully",
            "details": result,
            "metrics": {"items_processed": len(result)}
        },
        "reports": [
            {
                "name": "demo_report.json",
                "type": "application/json",
                "content": json.dumps(report),
                "download_url": f"/demo-artifacts/demo-1/demo_report.json"
            }
        ],
        "artifacts": [
            {
                "name": "demo_output.json",
                "type": "application/json",
                "size_bytes": len(json.dumps(result)),
                "download_url": f"/demo-artifacts/demo-1/demo_output.json"
            }
        ],
        "logs": logs
    }


def load_demo_data(filename: str) -> Dict[str, Any]:
    """Load canned demo data."""
    file_path = DEMO_DATA_DIR / filename
    with open(file_path, 'r') as f:
        return json.load(f)


def save_artifact(data: Any, filename: str) -> str:
    """Save demo artifact to disk."""
    # Create demo-specific directory
    demo_dir = DEMO_ARTIFACTS_DIR / "demo-1"
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    # Save artifact
    file_path = demo_dir / filename
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return str(file_path)
```

---

### Step 4: Define Pydantic Models

**File**: `services/<service>/domain/models.py` or `presentation/api/models.py`

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Literal

class DemoRequirements(BaseModel):
    """Requirements for executing a demo."""
    services_needed: List[str] = []
    credentials_needed: List[str] = []
    data_needed: List[str] = []

class DemoProduces(BaseModel):
    """What a demo produces."""
    reports: List[str] = []
    artifacts: List[str] = []
    data_files: List[str] = []

class DemoInfo(BaseModel):
    """Information about a demo."""
    id: str
    name: str
    description: str
    type: Literal["self-contained", "ecosystem", "hybrid"]
    duration_seconds: int
    requirements: DemoRequirements
    produces: DemoProduces
    status: Literal["available", "unavailable", "blocked"]
    blocker_reason: Optional[str] = None

class RunDemoRequest(BaseModel):
    """Request to run a demo."""
    demo_id: str
    parameters: Dict[str, Any] = {}
    output_format: Literal["json", "markdown", "html"] = "json"
    save_artifacts: bool = True

class DemoReport(BaseModel):
    """A demo report."""
    name: str
    type: str
    content: str
    download_url: Optional[str] = None

class DemoArtifact(BaseModel):
    """A demo artifact."""
    name: str
    type: str
    size_bytes: int
    download_url: str

class DemoResult(BaseModel):
    """Result of demo execution."""
    success: bool
    demo_id: str
    demo_name: str
    execution_time_seconds: float
    status: Literal["completed", "failed", "partial"]
    results: Dict[str, Any]
    reports: List[DemoReport]
    artifacts: List[DemoArtifact]
    logs: List[str]
    errors: List[str]
    warnings: List[str]
```

---

### Step 5: Add to Standard Endpoints

Update `presentation/routes/standard_routes.py`:

```python
@router.get("/endpoints")
async def list_endpoints():
    """List all endpoints."""
    endpoints = [
        # ... existing endpoints ...
        {
            "path": "/demos",
            "methods": ["GET"],
            "description": "List available demos"
        },
        {
            "path": "/run-demo",
            "methods": ["POST"],
            "description": "Execute a specific demo"
        },
    ]
    # ...
```

---

## 📊 Integration with Phase 9 (Future Expansion)

### Phase 9 Enhancement

**Previous Phase 9**: Plan workflows, create E2E test plans, create demo plans

**Enhanced Phase 9**: Plan workflows, create E2E test plans, **implement executable demos**

### New Phase 9.4: Implement Demo Endpoints

**Activities**:
1. Create `demo_data/` directory with canned data
2. Implement `/demos` endpoint with demo registry
3. Implement `/run-demo` endpoint with demo handlers
4. Create 2-3 self-contained demos
5. Create 1-2 ecosystem demos (if services available)
6. Test all demos via API
7. Document demos in README

**Deliverables**:
- ✅ `/demos` endpoint functional
- ✅ `/run-demo` endpoint functional
- ✅ 2-3 self-contained demos working
- ✅ 1-2 ecosystem demos implemented
- ✅ Demo data stored in `demo_data/`
- ✅ Artifacts generated in `demo_artifacts/`

**Quality Gate**: All demos executable via `/run-demo` with tangible results

---

## 📝 Documentation Requirements

### 1. Update README.md

Add "Demos" section:

```markdown
## 🎭 Demos

This service provides executable demos to showcase capabilities.

### List Available Demos

```bash
curl http://localhost:5105/demos
```

### Run a Demo

```bash
curl -X POST http://localhost:5105/run-demo \
  -H "Content-Type: application/json" \
  -d '{
    "demo_id": "normalize-miro-sample",
    "output_format": "json",
    "save_artifacts": true
  }'
```

### Available Demos

1. **normalize-miro-sample** (Self-Contained)
   - Normalizes a sample Miro board
   - Duration: ~2 seconds
   - Produces: normalization report, normalized JSON

2. **architecture-documentation-workflow** (Ecosystem)
   - Full workflow: normalize → analyze → generate docs
   - Duration: ~10 seconds
   - Requires: analysis-service, bedrock-proxy, AWS credentials
   - Produces: comprehensive architecture documentation
```

### 2. Update CONFIG.md

Add demo configuration:

```markdown
## Demo Configuration

### Demo Data Location
```bash
DEMO_DATA_DIR=services/<service>/demo_data
DEMO_ARTIFACTS_DIR=services/<service>/demo_artifacts
```

### Demo Endpoints
- `/demos` - Lists available demos
- `/run-demo` - Executes demos

### Demo Requirements
Some demos may require:
- External service availability
- API credentials
- Specific configuration
```

---

## 🎯 Example: architecture-digitizer Demos

### Demo 1: Normalize Miro Sample (Self-Contained)

**ID**: `normalize-miro-sample`  
**Type**: Self-contained  
**Duration**: ~2 seconds

**Sample Data**: `demo_data/sample_miro_board.json`

**Produces**:
- `normalization_report.json` - Detailed normalization report
- `normalized_architecture.json` - Standardized architecture data
- `components.json` - Extracted components
- `connections.json` - Extracted connections

**Test**:
```bash
curl -X POST http://localhost:5105/run-demo \
  -H "Content-Type: application/json" \
  -d '{"demo_id": "normalize-miro-sample"}'
```

---

### Demo 2: Multi-Format Processing (Self-Contained)

**ID**: `multi-format-processing`  
**Type**: Self-contained  
**Duration**: ~5 seconds

**Sample Data**:
- `demo_data/sample_miro_board.json`
- `demo_data/sample_figjam_file.json`
- `demo_data/sample_lucid_doc.json`

**Produces**:
- `multi_format_report.json` - Comparison report
- `normalized_miro.json`, `normalized_figjam.json`, `normalized_lucid.json`
- `format_comparison.csv` - Feature comparison

---

### Demo 3: Architecture Documentation Workflow (Ecosystem)

**ID**: `architecture-documentation-workflow`  
**Type**: Ecosystem  
**Duration**: ~10 seconds

**Requirements**:
- `analysis-service` running
- `bedrock-proxy` running
- `doc-store` running (optional)
- AWS Bedrock API credentials

**Produces**:
- `architecture_analysis_report.md` - Pattern analysis
- `documentation_report.md` - Generated documentation
- `workflow_visualization.json` - Workflow steps
- `doc_store_id.txt` - Stored document ID

**Test**:
```bash
curl -X POST http://localhost:5105/run-demo \
  -H "Content-Type: application/json" \
  -d '{
    "demo_id": "architecture-documentation-workflow",
    "parameters": {
      "generate_diagrams": true,
      "include_metrics": true
    }
  }'
```

---

## ✅ Quality Gates

### Phase 2 (Design & Planning)
- [ ] Demo endpoints included in design
- [ ] 2-3 self-contained demos planned
- [ ] 1-2 ecosystem demos planned

### Phase 6 (Documentation)
- [ ] `/demos` endpoint documented in README
- [ ] `/run-demo` endpoint documented in README
- [ ] OpenAPI spec includes demo endpoints
- [ ] Demo data documented

### Phase 9 (Future Expansion)
- [ ] `/demos` endpoint implemented
- [ ] `/run-demo` endpoint implemented
- [ ] 2-3 self-contained demos functional
- [ ] 1-2 ecosystem demos implemented
- [ ] All demos tested via API
- [ ] Demo artifacts generated successfully

---

## 📦 Files to Create/Modify

### New Files
```
services/<service>/
├── demo_data/                      # NEW: Canned demo data
│   ├── sample_input_1.json
│   ├── sample_input_2.json
│   └── README.md                   # Describes demo data
├── demo_artifacts/                 # NEW: Generated artifacts
│   └── .gitkeep
└── presentation/
    └── routes/
        └── demo_routes.py          # NEW: Demo endpoints
```

### Modified Files
```
services/<service>/
├── README.md                       # Add "Demos" section
├── CONFIG.md                       # Add demo configuration
└── presentation/
    └── routes/
        ├── __init__.py             # Import demo_router
        └── standard_routes.py      # Update /endpoints list
```

---

## 🚀 Rollout Strategy

### Phase 1: Documentation (Immediate)
- ✅ Create this specification document
- ✅ Update MASTER_REFACTORING_PLAN.md
- ✅ Update MASTER_SERVICE_MATRIX.md

### Phase 2: Templates (Week 1)
- Create demo_routes.py template
- Create DemoInfo/DemoResult model templates
- Create sample demo data templates

### Phase 3: Retroactive Implementation (Week 1-2)
Apply to completed services:
1. `architecture-digitizer` (highest priority - demos already planned)
2. `code-analyzer`
3. `analysis-service`
4. `bedrock-proxy`
5. `discovery-agent`
6. `data-services-dashboard` (skip - not a service)

### Phase 4: New Services (Ongoing)
- Include demo implementation in Phase 9 for all new refactorings

---

## 📊 Success Metrics

- ✅ 100% of services (non-dashboards) have `/demos` endpoint
- ✅ 100% of services have `/run-demo` endpoint
- ✅ Average 3 demos per service
- ✅ 100% of demos are executable via API
- ✅ 100% of demos produce tangible artifacts/reports

---

*Document Version: 1.0.0*  
*Created: October 10, 2025*  
*Status: Approved for Implementation*  
*Next: Update MASTER_REFACTORING_PLAN.md and MASTER_SERVICE_MATRIX.md*

