# 🚀 CI/CD Audit Framework Integration Guide

## Overview

The audit framework is fully integrated into the CI/CD pipeline, providing automated quality assurance and compliance checking across all development stages.

## 🏗️ Integration Components

### 1. **Configuration Files**
- `config/audit-config.yaml` - Main audit configuration
- `.pre-commit-config.yaml` - Pre-commit hooks with audit checks
- `.github/workflows/quality-gates.yml` - GitHub Actions workflow

### 2. **Build System Integration**
- `Makefile` - Main targets with audit integration
- `Makefile.audit` - Dedicated audit framework targets
- `Dockerfile.audit` - Audit framework container

### 3. **Docker Integration**
- `docker-compose.dev.yml` - Audit service definition
- `Dockerfile.audit` - Standalone audit container

### 4. **CI/CD Scripts**
- `scripts/cicd/ecosystem-ci-runner.py` - Comprehensive CI/CD runner

## 🎯 Usage

### Local Development

```bash
# Quick audit
make audit

# Comprehensive audit
make audit-all

# CI-optimized audit
make audit-ci

# Set up audit environment
make audit-setup
```

### CI/CD Pipeline

```bash
# Quick CI validation
make ci-validate

# Full CI pipeline with audit
make ci-test

# Pre-deployment validation
make pre-deploy
```

### Docker Usage

```bash
# Run audit in Docker
make audit-docker

# Start audit service
docker-compose --profile audit up audit-framework

# Run audit on specific service
docker run --rm -v $(pwd):/app audit-framework audit --service shared --profile ci_fast
```

## ⚙️ Configuration

### Quality Gates

The audit framework enforces the following quality gates:

```yaml
quality_gates:
  minimum_scores:
    overall: 60.0      # Grade C minimum
    architecture: 70.0
    code_quality: 55.0
    performance: 65.0
    maintainability: 60.0

  critical_issues:
    max_total: 5       # Maximum critical issues
    max_per_service: 2 # Per service limit

  service_requirements:
    min_passing_services: 3  # Minimum services passing
    total_services: 5        # Total services monitored
```

### Audit Profiles

Available audit profiles for different scenarios:

- **`ci_fast`**: 60-second timeout, basic analysis for CI
- **`standard`**: Balanced analysis for development
- **`strict`**: Maximum scrutiny for production
- **`ci_comprehensive`**: Full analysis for releases

## 🔧 Advanced Configuration

### Custom Quality Thresholds

Edit `config/audit-config.yaml` to customize quality thresholds:

```yaml
# Example: Stricter requirements for production
quality_gates:
  minimum_scores:
    overall: 75.0      # Grade B minimum
    architecture: 80.0
    code_quality: 70.0

  critical_issues:
    max_total: 2       # Stricter issue limit
```

### Service-Specific Configuration

Configure individual services in `config/audit-config.yaml`:

```yaml
services:
  my-service:
    name: "My Custom Service"
    path: "services/my-service"
    critical_components: ["api", "database", "security"]
    exclude_patterns: ["test_*", "*.log"]
```

### CI/CD Integration Scripts

The CI/CD runner supports multiple validation levels:

```bash
# Quick checks (syntax, imports, basic audit)
python scripts/cicd/ecosystem-ci-runner.py --level quick

# Standard checks (includes dependencies, Docker, environment)
python scripts/cicd/ecosystem-ci-runner.py --level standard

# Comprehensive checks (includes tests, performance, integration)
python scripts/cicd/ecosystem-ci-runner.py --level comprehensive
```

## 📊 Reporting

### Output Formats

The audit framework supports multiple output formats:

- **`rich`**: Interactive console output (default)
- **`json`**: Structured data for CI/CD integration
- **`markdown`**: Comprehensive reports
- **`full`**: Complete analysis data

### Example JSON Output

```json
{
  "service_name": "shared",
  "overall_score": 77.79,
  "grade": "C",
  "critical_issues_count": 0,
  "estimated_effort_days": 14.5,
  "dimensions": {
    "architecture": 93.0,
    "code_quality": 66.0,
    "performance": 82.5,
    "maintainability": 67.55
  }
}
```

## 🚨 Quality Gate Enforcement

### Automatic Blocking

The CI/CD pipeline automatically blocks deployments when:

- Overall score < 60 (Grade C minimum)
- Critical issues > 5 total
- < 3 services meet minimum standards

### Manual Override

Emergency overrides require:

```bash
# Override permissions (maintainer/admin only)
# Override conditions: hotfix, security-patch, infrastructure-failure
# Maximum override duration: 24 hours
```

## 🔍 Pre-commit Hooks

### Automatic Quality Checks

Pre-commit hooks automatically run audit checks on modified files:

```bash
# Install hooks
pip install pre-commit
pre-commit install

# Manual trigger
pre-commit run audit-framework-check

# Run on specific files
pre-commit run --files services/shared/main.py
```

### Hook Configuration

The pre-commit configuration includes:

- **Syntax validation**: Python syntax checking
- **Import validation**: Import resolution checks
- **Audit framework checks**: Quality gates on modified services
- **Security scanning**: Basic security pattern detection

## 🐳 Docker Integration

### Containerized Audit

```dockerfile
# Dockerfile.audit provides:
FROM python:3.13-slim
COPY . /app
RUN pip install -r scripts/audit-framework/requirements-audit.txt
CMD ["python3", "scripts/audit-framework/audit_cli.py", "--help"]
```

### Docker Compose Service

```yaml
audit-framework:
  build:
    context: .
    dockerfile: Dockerfile.audit
  volumes:
    - .:/app
    - audit-reports:/app/audit-reports
  profiles:
    - audit
    - development
```

## 📈 Monitoring & Analytics

### Trend Analysis

Track quality trends over time:

```bash
# Generate trend reports
make audit-trend

# Performance benchmarking
make audit-benchmark
```

### CI/CD Analytics

Monitor CI/CD pipeline performance:

```bash
# View CI analytics
make ci-analytics

# Generate CI reports
make ci-reports
```

## 🛠️ Troubleshooting

### Common Issues

1. **Audit framework not found**
   ```bash
   make audit-setup
   source venv_audit/bin/activate
   ```

2. **Permission errors**
   ```bash
   chmod +x scripts/audit-framework/audit_cli.py
   ```

3. **Docker issues**
   ```bash
   docker system prune -f
   make audit-docker
   ```

### Debug Mode

Enable verbose logging:

```bash
# Debug audit execution
make audit-debug

# Verbose CI runner
python scripts/cicd/ecosystem-ci-runner.py --level standard --verbose
```

## 📋 Best Practices

### Development Workflow

1. **Local Development**: Use `make audit` for quick feedback
2. **Pre-commit**: Automatic quality checks on commits
3. **CI Pipeline**: Comprehensive validation on pushes/PRs
4. **Pre-deployment**: Full audit before releases

### Quality Maintenance

1. **Regular Audits**: Run weekly comprehensive audits
2. **Trend Monitoring**: Track quality metrics over time
3. **Configuration Updates**: Keep quality thresholds current
4. **Service Updates**: Update service configurations as needed

### Emergency Procedures

1. **Quality Gate Failures**: Review audit reports for specific issues
2. **Override Requests**: Document reasons for quality bypasses
3. **Rollback Plans**: Maintain deployment rollback capabilities
4. **Incident Response**: Use audit data for post-mortem analysis

## 🔗 Integration Points

### GitHub Actions
- **Workflow**: `.github/workflows/quality-gates.yml`
- **Triggers**: Push, PR, weekly schedule
- **Artifacts**: Audit reports and quality metrics

### Pre-commit Hooks
- **Configuration**: `.pre-commit-config.yaml`
- **Hooks**: Syntax, audit, quality gate checks
- **Integration**: Automatic on commit

### Docker Ecosystem
- **Service**: `audit-framework` in docker-compose
- **Image**: `Dockerfile.audit` for standalone execution
- **Volumes**: Persistent audit reports and configurations

### Makefile Integration
- **Main targets**: `audit*` targets in main Makefile
- **Dedicated file**: `Makefile.audit` for comprehensive audit operations
- **CI integration**: `ci-*` targets include audit validation

This integration provides comprehensive quality assurance throughout the development lifecycle, from local commits to production deployments.
