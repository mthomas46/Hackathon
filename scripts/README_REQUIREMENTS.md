# Requirements Management for LLM Documentation Ecosystem Scripts

This document outlines the requirements management for validation, hardening, and safeguard scripts.

## Overview

During the ecosystem development and validation process, several Python dependencies were identified as missing from the original requirements files. This document tracks those dependencies and provides installation instructions.

## Missing Dependencies Identified

The following dependencies were needed but not included in original requirements files:

### Core Dependencies (Added to main files)
- `requests>=2.32.0` - HTTP client library for API calls
- `aiohttp>=3.12.0` - Asynchronous HTTP client for async operations
- `redis>=6.4.0` - Updated Redis client (was 5.0.0)

### Script-Specific Dependencies
- `docker>=7.0.0` - Docker Python client for container management
- `click>=8.0.0` - CLI framework for command-line tools
- `kubernetes>=26.0.0` - Kubernetes client (optional)
- `pytest-cov>=4.0.0` - Test coverage reporting
- `matplotlib>=3.7.0` - Data visualization
- `netifaces>=0.11.0` - Network interface utilities
- `sentry-sdk>=1.0.0` - Error tracking (optional)
- `grafana-api>=1.0.0` - Grafana API client (optional)

## Requirements Files Structure

```
scripts/
├── requirements.txt                 # Main scripts requirements
├── hardening/
│   └── requirements.txt            # Hardening scripts specific deps
└── safeguards/
    └── requirements.txt            # Safeguards scripts specific deps

services/
├── shared/requirements.txt         # Updated with missing deps
└── [service]/requirements.txt      # Service-specific requirements

docker-requirements.txt             # Updated main container requirements
```

## Installation Instructions

### Option 1: Install All Dependencies (Recommended)
```bash
# Install main shared requirements
pip install -r services/shared/requirements.txt

# Install scripts requirements
pip install -r scripts/requirements.txt

# Or install hardening/safeguards specific
pip install -r scripts/hardening/requirements.txt
pip install -r scripts/safeguards/requirements.txt
```

### Option 2: Virtual Environment (Best Practice)
```bash
# Create virtual environment
python3 -m venv venv_ecosystem
source venv_ecosystem/bin/activate

# Install all requirements
pip install -r services/shared/requirements.txt
pip install -r scripts/requirements.txt
```

### Option 3: Docker Development
```bash
# Use the updated docker-requirements.txt for container builds
# This includes all necessary dependencies for both services and scripts
pip install -r docker-requirements.txt
```

## Scripts and Their Dependencies

### Core Validation Scripts
- **unified_health_monitor.py**: `redis`, `requests`, `pyyaml`
- **health_endpoint_validator.py**: `aiohttp`, `pyyaml`
- **production_readiness_validator.py**: `pyyaml`, `urllib.request`
- **service_connectivity_validator.py**: `pyyaml`, `urllib.request`

### Hardening Scripts
- **docker_standardization.py**: `docker`, `pyyaml`
- **dependency_validator.py**: `docker`, `pyyaml`
- **auto_healer.py**: `docker`, `psutil`
- **port_conflict_detector.py**: `docker`, `pyyaml`

### Safeguards Scripts
- **api_contract_validator.py**: `aiohttp`, `requests`
- **config_drift_detector.py**: `pyyaml`, `docker`
- **environment_aware_cli.py**: `click`, `rich`

## Common Issues and Solutions

### ImportError: No module named 'redis'
```bash
pip install redis>=6.4.0
```

### ImportError: No module named 'requests'
```bash
pip install requests>=2.32.0
```

### ImportError: No module named 'aiohttp'
```bash
pip install aiohttp>=3.12.0
```

### ImportError: No module named 'docker'
```bash
pip install docker>=7.0.0
```

## Version Compatibility

All dependencies have been tested with:
- Python 3.11+
- macOS 13.0+
- Docker 24.0+
- Redis 7.0+

## Optional Dependencies

Some features require optional dependencies:
- **Kubernetes integration**: `kubernetes>=26.0.0`
- **AWS services**: `boto3>=1.34.0`, `botocore>=1.34.0`
- **Monitoring**: `grafana-api>=1.0.0`, `sentry-sdk>=1.0.0`

Install these only if you need the specific features:
```bash
pip install kubernetes boto3 grafana-api sentry-sdk
```

## Testing Dependencies

For running tests and validation:
```bash
pip install pytest pytest-asyncio pytest-cov
```

## Contributing

When adding new scripts or features:

1. Check if new dependencies are needed
2. Add them to the appropriate requirements.txt file
3. Update this documentation
4. Test installation in a clean environment

## Troubleshooting

If you encounter dependency conflicts:

1. Use a virtual environment
2. Check Python version compatibility
3. Review pip install output for conflicts
4. Consider using `pip-tools` for dependency management

## Validation

To verify all dependencies are correctly installed:
```bash
python -c "import redis, requests, aiohttp, yaml, docker; print('All core dependencies installed')"
```
