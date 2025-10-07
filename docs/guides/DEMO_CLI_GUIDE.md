# CLI Demo Guide

**Related Documentation:**
- [Architecture & Workflow Execution Guide](./ARCHITECTURE_AND_WORKFLOW_EXECUTION.md) - Technical deep-dive
- [Ecosystem Validation Complete](./ECOSYSTEM_VALIDATION_COMPLETE.md) - Validation system details
- [Main Demo Script](./demo_hyper_realistic_parameterized.py) - Source code

---

## Quick Reference

### View Help
```bash
python demo_hyper_realistic_parameterized.py --help
```

### Run with Defaults
```bash
python demo_hyper_realistic_parameterized.py
```

---

## CLI Parameters

| Parameter | Short | Type | Default | Description |
|-----------|-------|------|---------|-------------|
| `--feature` | `-f` | string | Notification system | Feature description |
| `--tickets` | `-t` | integer | 5 | Historical tickets to generate |
| `--team` | `-m` | integer | 5 | Team members to generate |
| `--tech` | `-s` | list | Python iOS Android React Firebase | Tech stack (space-separated) |
| `--output` | `-o` | string | demo_output | Output folder name |

---

## Examples

### 1. API Gateway Demo
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "Build API Gateway with rate limiting and authentication" \
  --tickets 8 \
  --team 6 \
  --tech Go Kubernetes Redis Nginx \
  --output api_gateway_demo
```

### 2. Enterprise SSO Integration
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "Enterprise SSO integration with SAML and OAuth2" \
  --tickets 15 \
  --team 12 \
  --tech Python Java AWS SAML OAuth2 \
  --output enterprise_sso_demo
```

### 3. Microservices Tracing
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "Distributed tracing system for microservices" \
  --tickets 10 \
  --team 8 \
  --tech Go Kubernetes Istio Jaeger Prometheus \
  --output tracing_demo
```

### 4. Frontend Redesign
```bash
python demo_hyper_realistic_parameterized.py \
  -f "Redesign dashboard with dark mode and accessibility" \
  -t 8 \
  -m 6 \
  -s React TypeScript CSS WCAG \
  -o frontend_redesign_demo
```

### 5. Mobile App with Offline Support
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "Offline-first mobile app with data sync" \
  --tickets 12 \
  --team 7 \
  --tech Swift Kotlin SQLite GraphQL \
  --output mobile_offline_demo
```

### 6. Data Pipeline
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "Real-time data pipeline with streaming analytics" \
  --tickets 20 \
  --team 10 \
  --tech Python Kafka Spark Airflow \
  --output data_pipeline_demo
```

### 7. ML Model Serving
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "ML model serving platform with A/B testing" \
  --tickets 18 \
  --team 9 \
  --tech Python TensorFlow Kubernetes MLflow \
  --output ml_serving_demo
```

### 8. Small Team Prototype
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "MVP social sharing feature" \
  --tickets 3 \
  --team 3 \
  --tech React Node.js MongoDB \
  --output mvp_demo
```

### 9. Scala/Elm CRUD API (Large Team)
```bash
python demo_hyper_realistic_parameterized.py \
  --feature "Expand API functionality to a cats effect Scala API such that it can take in user information and display that user information from basic CRUD endpoints with Scala backend and Elm frontend" \
  --tickets 35 \
  --team 8 \
  --tech Scala "Cats Effect" Elm CRUD API \
  --output scala_elm_crud_demo
```

**Prompt Source:** "35 documents & a team of 8 developers, I want to expand API functionality to a cats effect Scala API such that it can take in user information and display that user information from basic CRUD endpoints. This project has a Scala backend and an Elm frontend"

**Output:** `scala_elm_crud_demo/` with 35 historical tickets, 8 team members

---

## Output Structure

Each demo creates:

```
{output_folder}/
├── README.md                           (Usage guide)
├── data/
│   └── mock_data.json                  (Generated data)
└── reports/
    ├── Planning_Service_Report.md      (Production output)
    └── Behind_the_Scenes_Report.md     (Technical docs)
```

---

## Tips

1. **Use quotes** for feature descriptions with spaces
2. **Tech stack** is space-separated (no commas)
3. **Short flags** available: `-f`, `-t`, `-m`, `-s`, `-o`
4. **Output folder** is created automatically
5. **All reports** are cross-linked for navigation

---

## Verification

After running a demo, verify the output:

```bash
# List generated files
ls -lh {output_folder}/**/*

# View README
cat {output_folder}/README.md

# Check mock data
cat {output_folder}/data/mock_data.json | python3 -m json.tool

# Open reports (macOS)
open {output_folder}/reports/Planning_Service_Report.md
open {output_folder}/reports/Behind_the_Scenes_Report.md
```

---

**Demo System:** Phase 9 - Hyper-Realistic Parameterized Demo v2.0  
**Generated:** 2025-10-03

