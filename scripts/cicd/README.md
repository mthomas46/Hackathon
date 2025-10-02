# CI/CD Integration Scripts

This directory contains scripts for continuous integration and deployment integration with the LLM Documentation Ecosystem.

## Scripts

### `ecosystem-ci-runner.py`
**CI/CD Pipeline Runner** - Comprehensive CI/CD integration script for automated testing and deployment.

**Features:**
- Automated test execution across all services
- Deployment pipeline orchestration
- Quality gate enforcement
- Integration with CI/CD platforms (GitHub Actions, Jenkins, etc.)
- Comprehensive reporting and notifications

**Usage:**
```bash
python scripts/cicd/ecosystem-ci-runner.py --full-suite
python scripts/cicd/ecosystem-ci-runner.py --service orchestrator --deploy
```

**Integration Points:**
- Referenced in `Makefile.cicd`
- Used by GitHub Actions workflows
- Integrated with deployment pipelines

## Purpose

These scripts enable:
- ✅ Automated testing in CI/CD pipelines
- ✅ Deployment automation and orchestration
- ✅ Quality gate enforcement before releases
- ✅ Integration testing across service boundaries
- ✅ Comprehensive CI/CD reporting and monitoring

## Dependencies

Requires access to:
- All service repositories
- CI/CD platform APIs
- Deployment environments
- Monitoring and logging systems
