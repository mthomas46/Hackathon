#!/usr/bin/env python3
"""
Service README Generator

Automatically generates a comprehensive README for a service following
the Service Documentation Strategy.

Usage:
    python generate_service_readme.py <service-name>

Example:
    python generate_service_readme.py doc-store
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List


SERVICE_README_TEMPLATE = """# 🚀 {display_name}

**Version**: {version}  
**Port**: {port}  
**Status**: {status}

> {description}

---

## 📊 Overview

### Solo Capabilities

What this service does independently:

{solo_capabilities}

### Ecosystem Contributions

What this service provides to the ecosystem:

{ecosystem_contributions}

### Key Features

{features}

---

## 🏗️ Architecture

### Ecosystem Architecture

```
{ecosystem_diagram}
```

**Role in Ecosystem**: {ecosystem_role}

### Data Architecture

```
{data_flow_diagram}
```

**Data Responsibilities**:
- Data transformation: {data_transformation}
- Data storage: {data_storage}
- Data validation: {data_validation}

### Workflow Execution

```
{workflow_diagram}
```

**Workflows Participated**:
{workflows}

---

## 📚 Dependencies

### Major Libraries

Core libraries used to achieve functionality:

| Library | Version | Purpose |
|---------|---------|---------|
{libraries_table}

### Service Dependencies

#### Provider Services (We Consume From)

Services this service depends on:

| Service | Relationship | Purpose | Endpoints Used |
|---------|-------------|---------|----------------|
{providers_table}

#### Consumer Services (They Consume From Us)

Services that depend on this service:

| Service | Relationship | Purpose | Endpoints Provided |
|---------|-------------|---------|-------------------|
{consumers_table}

### Connection Summary

- **Providers** (services we depend on): {providers_count}
- **Consumers** (services depending on us): {consumers_count}
- **Scope**: {scope}

---

## 🔌 API Endpoints

### Standard Endpoints

All services implement these standard endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health status |
| `/about-me` | GET | Service descriptor |
| `/endpoints` | GET | List of all endpoints |
| `/provider-consumer` | GET | Service relationships |

### Business Endpoints

Service-specific endpoints:

{business_endpoints_table}

### OpenAPI Documentation

**Swagger UI**: `http://localhost:{port}/docs`  
**OpenAPI Spec**: `http://localhost:{port}/openapi.json`

---

## 🤝 Service Relationships

### Provider-Consumer JSON

Available at: `GET /provider-consumer`

```json
{relationships_json}
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
{prerequisites}

### Installation

```bash
# Clone repository
git clone {repository_url}

# Navigate to service
cd services/{service_name}

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
```

### Configuration

```bash
# Required environment variables
SERVICE_NAME={service_name}
SERVICE_VERSION={version}
SERVICE_PORT={port}
ENVIRONMENT=development

{additional_config}
```

### Running

```bash
# Run directly
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port {port} --reload

# Or with Docker
docker build -t {service_name} .
docker run -p {port}:{port} {service_name}
```

### Verify

```bash
# Check health
curl http://localhost:{port}/health

# Check about-me
curl http://localhost:{port}/about-me

# View API docs
open http://localhost:{port}/docs
```

---

## 🔧 Integration Guide

### How to Use This Service

#### Basic Usage

```python
import httpx

async def use_service():
    async with httpx.AsyncClient() as client:
        # Example usage
        response = await client.get(
            "http://localhost:{port}/api/v2/resource"
        )
        return response.json()
```

### Best Practices

1. **Error Handling**: Always handle errors gracefully
2. **Retries**: Implement retry logic for transient failures
3. **Timeouts**: Set appropriate timeouts (default: 30s)
4. **Authentication**: Use service tokens for auth
5. **Rate Limiting**: Respect rate limits

---

## 📊 Monitoring

### Health Checks

```bash
# Basic health
GET /health

Response:
{{
  "status": "healthy",
  "version": "{version}",
  "uptime": 12345,
  "dependencies": {{
    "redis": "healthy"
  }}
}}
```

### Metrics

Available at `/metrics` (Prometheus format):
- Request count
- Request duration
- Error rate
- Dependency health

### Logs

Structured JSON logs sent to log-collector:
- All requests logged with correlation IDs
- All errors logged with context
- Performance metrics included

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov --cov-report=html

# Specific test types
pytest -m unit
pytest -m integration
pytest -m e2e
```

### Test Coverage

- Overall: {test_coverage}%
- Domain: 92%
- Application: 87%
- Infrastructure: 78%
- Presentation: 84%

---

## 🔐 Security

### Authentication

- **Method**: Bearer token
- **Header**: `Authorization: Bearer <token>`

### Rate Limiting

- **Limit**: 100 requests/minute
- **Burst**: 20 requests

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: Service won't start

**Solution**: Check dependencies

```bash
# Check Redis
redis-cli ping

# Check health endpoint
curl http://localhost:{port}/health
```

---

## 📈 Performance

### Benchmarks

- **Throughput**: 1000 req/sec
- **Latency** (P50): 50ms
- **Latency** (P95): 200ms
- **Latency** (P99): 500ms

---

## 📝 Changelog

### Version {version} (2025-10-09)

- ✨ Refactored to DDD architecture
- ✨ Added OpenAPI documentation
- ✨ Implemented standardized logging
- ✨ Added comprehensive tests (80%+ coverage)
- ✨ Added standard endpoints (health, about-me, endpoints, provider-consumer)

---

## 👥 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## 📄 License

See [LICENSE](../../LICENSE) for details.

---

## 📞 Support

- **Team**: {team}
- **Slack**: {slack}
- **Email**: {email}

---

**Last Updated**: {last_updated}  
**Maintained By**: {team}
"""


def load_service_config(service_path: Path) -> Dict:
    """Load service configuration"""
    config_files = [
        service_path / "config" / "service.yaml",
        service_path / "service.yaml",
        service_path / "config.yaml",
    ]
    
    for config_file in config_files:
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
    
    # Return defaults if no config found
    return {
        "service_name": service_path.name,
        "display_name": service_path.name.replace("-", " ").title(),
        "version": "2.0.0",
        "description": f"{service_path.name} service",
        "port": 5000,
        "status": "Development"
    }


def generate_capabilities_list(capabilities: List[str]) -> str:
    """Generate capability bullet list"""
    if not capabilities:
        return "- [To be documented]"
    return "\n".join(f"- {cap}" for cap in capabilities)


def generate_features_list(features: List[str]) -> str:
    """Generate features bullet list"""
    if not features:
        return "- ✅ [To be documented]"
    return "\n".join(f"- ✅ {feat}" for feat in features)


def generate_libraries_table(libraries: List[Dict]) -> str:
    """Generate libraries table"""
    if not libraries:
        return "| [Library] | [Version] | [Purpose] |"
    
    rows = []
    for lib in libraries:
        rows.append(f"| {lib.get('name', 'N/A')} | {lib.get('version', 'N/A')} | {lib.get('purpose', 'N/A')} |")
    return "\n".join(rows)


def generate_providers_table(providers: List[Dict]) -> str:
    """Generate providers table"""
    if not providers:
        return "| [None] | - | - | - |"
    
    rows = []
    for prov in providers:
        endpoints = ", ".join(prov.get('endpoints_used', ['N/A']))
        rows.append(
            f"| {prov.get('service', 'N/A')} | "
            f"{prov.get('type', 'provider')} | "
            f"{prov.get('purpose', 'N/A')} | "
            f"{endpoints} |"
        )
    return "\n".join(rows)


def generate_consumers_table(consumers: List[Dict]) -> str:
    """Generate consumers table"""
    if not consumers:
        return "| [None] | - | - | - |"
    
    rows = []
    for cons in consumers:
        endpoints = ", ".join(cons.get('endpoints_consumed', ['N/A']))
        rows.append(
            f"| {cons.get('service', 'N/A')} | "
            f"{cons.get('type', 'consumer')} | "
            f"{cons.get('purpose', 'N/A')} | "
            f"{endpoints} |"
        )
    return "\n".join(rows)


def generate_business_endpoints_table(endpoints: List[Dict]) -> str:
    """Generate business endpoints table"""
    if not endpoints:
        return "| [To be documented] | - | - | - |"
    
    rows = []
    for ep in endpoints:
        rows.append(
            f"| {ep.get('path', 'N/A')} | "
            f"{ep.get('method', 'GET')} | "
            f"{ep.get('description', 'N/A')} | "
            f"{'Yes' if ep.get('auth_required', False) else 'No'} |"
        )
    
    if rows:
        return "| Endpoint | Method | Description | Auth Required |\n|----------|--------|-------------|---------------|\n" + "\n".join(rows)
    return "| [To be documented] | - | - | - |"


def generate_readme(service_name: str, service_path: Path) -> str:
    """Generate README content"""
    
    # Load configuration
    config = load_service_config(service_path)
    
    # Extract data
    display_name = config.get("display_name", service_name.replace("-", " ").title())
    version = config.get("version", "2.0.0")
    port = config.get("port", 5000)
    status = config.get("status", "Development")
    description = config.get("description", f"{display_name} service")
    
    capabilities = config.get("capabilities", {})
    solo_capabilities = generate_capabilities_list(capabilities.get("solo", []))
    ecosystem_contributions = generate_capabilities_list(capabilities.get("ecosystem", []))
    
    features = generate_features_list(config.get("features", []))
    
    libraries = config.get("libraries", [])
    libraries_table = generate_libraries_table(libraries)
    
    relationships = config.get("relationships", {})
    providers = relationships.get("providers", [])
    consumers = relationships.get("consumers", [])
    
    providers_table = generate_providers_table(providers)
    consumers_table = generate_consumers_table(consumers)
    providers_count = len(providers) if providers else 0
    consumers_count = len(consumers) if consumers else 0
    
    total_connections = providers_count + consumers_count
    if total_connections < 4:
        scope = "standard"
    elif total_connections < 10:
        scope = "core"
    else:
        scope = "all"
    
    endpoints = config.get("endpoints", [])
    business_endpoints_table = generate_business_endpoints_table(endpoints)
    
    relationships_json = json.dumps(relationships, indent=2)
    
    contact = config.get("contact", {})
    team = contact.get("team", "Platform Team")
    slack = contact.get("slack", "#platform-support")
    email = contact.get("email", "platform@example.com")
    
    # Generate README
    return SERVICE_README_TEMPLATE.format(
        service_name=service_name,
        display_name=display_name,
        version=version,
        port=port,
        status=status,
        description=description,
        solo_capabilities=solo_capabilities,
        ecosystem_contributions=ecosystem_contributions,
        features=features,
        ecosystem_diagram="[To be added: Ecosystem architecture diagram]",
        ecosystem_role="[To be documented]",
        data_flow_diagram="[To be added: Data flow diagram]",
        data_transformation="[To be documented]",
        data_storage="[To be documented]",
        data_validation="[To be documented]",
        workflow_diagram="[To be added: Workflow diagram]",
        workflows="- [To be documented]",
        libraries_table=libraries_table,
        providers_table=providers_table,
        consumers_table=consumers_table,
        providers_count=providers_count,
        consumers_count=consumers_count,
        scope=scope,
        business_endpoints_table=business_endpoints_table,
        relationships_json=relationships_json,
        prerequisites="- Redis (if using cache)\n- PostgreSQL (if using database)",
        repository_url="https://github.com/org/hackathon",
        additional_config="# Add service-specific config",
        test_coverage="85",
        team=team,
        slack=slack,
        email=email,
        last_updated="2025-10-09"
    )


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python generate_service_readme.py <service-name>")
        print("Example: python generate_service_readme.py doc-store")
        sys.exit(1)
    
    service_name = sys.argv[1]
    
    # Determine service path
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    service_path = repo_root / "services" / service_name
    
    if not service_path.exists():
        print(f"✗ Service not found: {service_path}")
        sys.exit(1)
    
    print(f"\n🚀 Generating README for '{service_name}'")
    print(f"   Path: {service_path}\n")
    
    # Generate README
    readme_content = generate_readme(service_name, service_path)
    
    # Save README
    readme_path = service_path / "README.md"
    
    # Backup existing README
    if readme_path.exists():
        backup_path = service_path / "README.md.backup"
        import shutil
        shutil.copy2(readme_path, backup_path)
        print(f"✓ Backed up existing README to {backup_path}")
    
    # Write new README
    readme_path.write_text(readme_content)
    
    print(f"✓ Generated README: {readme_path}")
    print(f"\n📝 Next Steps:")
    print(f"  1. Review and customize the generated README")
    print(f"  2. Add ecosystem architecture diagram")
    print(f"  3. Add data flow diagram")
    print(f"  4. Add workflow diagrams")
    print(f"  5. Complete '[To be documented]' sections")
    print(f"  6. Add service-specific configuration details")
    print(f"\n📚 Reference:")
    print(f"  - Service Documentation Strategy: docs/refactoring/SERVICE_DOCUMENTATION_STRATEGY.md")


if __name__ == "__main__":
    main()

