# Consolidated Ecosystem Management

This directory contains consolidated scripts for comprehensive ecosystem-level operations, testing, and management.

## Main Script

### `ecosystem_manager.py`
**Consolidated Ecosystem Management Suite** - Combines all ecosystem management functionality:

**Features:**
- **API Auditing**: Comprehensive endpoint testing and gap analysis across all services
- **Functional Testing**: End-to-end testing suite for ecosystem validation
- **Gap Analysis**: Identification of missing features and API coverage gaps
- **Health Monitoring**: Service health checks and status reporting
- **Configuration Auditing**: Service configuration validation and consistency checks
- **Integration Testing**: Cross-service integration verification
- **Performance Analysis**: Basic performance metrics and bottleneck identification

**Capabilities:**
- Multi-environment support (Docker/localhost)
- Automated service discovery and testing
- Comprehensive reporting and gap analysis
- CLI capability mapping vs API endpoints
- Health status monitoring across all services
- Configuration drift detection

## Usage Examples

```bash
# Comprehensive ecosystem audit
python scripts/ecosystem/ecosystem_manager.py audit

# Functional testing suite
python scripts/ecosystem/ecosystem_manager.py test

# Gap analysis report
python scripts/ecosystem/ecosystem_manager.py gaps

# Service health overview
python scripts/ecosystem/ecosystem_manager.py health

# Configuration audit
python scripts/ecosystem/ecosystem_manager.py config
```

## What Was Consolidated

This script combines functionality from the previously separate scripts:
- `ecosystem_api_audit.py` → API auditing and endpoint testing
- `ecosystem_functional_test_suite.py` → End-to-end functional testing
- `ecosystem_gap_analysis.py` → Feature gap analysis and reporting
- `ecosystem_test.py` → General ecosystem testing utilities
- `ecosystem_unified_test.sh` → Unified testing orchestration

## Purpose

The consolidated ecosystem manager provides:
- **Unified Interface**: Single script for all ecosystem management tasks
- **Comprehensive Analysis**: Full ecosystem health and capability assessment
- **Automated Testing**: End-to-end validation of ecosystem functionality
- **Gap Identification**: Clear identification of missing features and APIs
- **Operational Tools**: Day-to-day ecosystem monitoring and management
- **Reporting**: Detailed reports for stakeholders and development teams
