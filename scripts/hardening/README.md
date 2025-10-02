# Configuration Management Scripts

This directory contains scripts for managing configuration across the LLM Documentation Ecosystem. The scripts have been standardized to provide consistent interfaces and functionality.

## 🆕 Unified Configuration Management

**Primary Interface:** `unified_config_manager.py`

This is the main entry point for all configuration management operations. It consolidates functionality from multiple legacy scripts into a single, user-friendly interface.

### Quick Start

```bash
# Show system status
python unified_config_manager.py status

# Run configuration audit
python unified_config_manager.py audit

# Preview standardization changes
python unified_config_manager.py standardize --dry-run

# Apply standardization (with confirmation)
python unified_config_manager.py standardize --apply

# Generate environment variable migration report
python unified_config_manager.py migrate --report

# Validate Docker consistency
python unified_config_manager.py docker-check

# Generate comprehensive report
python unified_config_manager.py report --output config_report.json
```

## 📋 Available Scripts

### Primary Scripts (Recommended)

| Script | Purpose | Status |
|--------|---------|---------|
| `unified_config_manager.py` | **Unified interface for all config operations** | ✅ Active |
| `configuration_standardization.py` | Automated config standardization | ✅ Active |
| `migrate_env_vars.py` | Environment variable migration | ✅ Active |

### Legacy Scripts (Deprecated)

| Script | Purpose | Replacement |
|--------|---------|-------------|
| `configuration_management_system.py` | Legacy port-focused config management | `unified_config_manager.py` |
| `apply_config_standardization.py` | Legacy standardization script | `unified_config_manager.py standardize` |
| `validate_service_configs.py` | Legacy validation script | `unified_config_manager.py audit` |
| `config_drift_detector.py` | Docker-specific drift detection | `unified_config_manager.py docker-check` |

### Supporting Scripts

| Script | Purpose | Status |
|--------|---------|---------|
| `analyze_deployment_configurations.py` | Deployment config analysis | ✅ Active |
| `environment_detector.py` | Environment detection utilities | ✅ Active |
| `environment_validator.py` | Environment validation | ✅ Active |
| `validate_service_configs.py` | Service config validation (legacy) | ⚠️ Deprecated |

## 📋 **Detailed Script Descriptions**

### Primary Scripts

#### `unified_config_manager.py`
**Unified Configuration Management System** - The primary interface for all configuration management operations across the ecosystem.

**Features:**
- Centralized configuration management for all 29 services
- Automated configuration standardization and validation
- Environment variable migration and conflict resolution
- Docker Compose configuration validation and optimization
- Comprehensive auditing and reporting capabilities
- Interactive command-line interface with help system
- Dry-run capabilities for safe configuration changes

**Use Cases:**
- Enterprise-wide configuration standardization
- Automated deployment preparation and validation
- Configuration drift detection and remediation
- Multi-environment configuration management
- Compliance auditing and reporting
- Development workflow automation

#### `configuration_standardization.py`
**Automated Configuration Standardizer** - Intelligent configuration standardization across all services and environments.

**Features:**
- Automated detection and fixing of configuration inconsistencies
- Schema validation against standardized configuration formats
- Environment variable standardization and migration
- Docker configuration optimization and validation
- Batch processing capabilities for large-scale changes
- Rollback capabilities for failed standardization attempts

**Use Cases:**
- Configuration consistency enforcement across teams
- Automated remediation of configuration drift
- Standardization during service onboarding
- Compliance with organizational configuration policies
- Preparation for production deployments

#### `migrate_env_vars.py`
**Environment Variable Migration Engine** - Comprehensive environment variable migration and conflict resolution.

**Features:**
- Automated detection of environment variable conflicts
- Intelligent migration planning and conflict resolution
- Batch migration capabilities for multiple services
- Validation of migration results and rollback options
- Integration with configuration management systems
- Comprehensive reporting and audit trails

**Use Cases:**
- Environment variable standardization across services
- Conflict resolution in multi-service deployments
- Migration planning for configuration changes
- Compliance with environment variable naming standards
- Development to production environment transitions

### Supporting Scripts

#### `analyze_deployment_configurations.py`
**Deployment Configuration Analyzer** - Advanced analysis and optimization of deployment configurations.

**Features:**
- Comprehensive deployment configuration analysis
- Performance optimization recommendations
- Security vulnerability assessment
- Resource utilization analysis
- Dependency mapping and optimization
- Automated optimization suggestions

**Use Cases:**
- Pre-deployment configuration validation
- Performance optimization planning
- Security assessment of deployment configurations
- Resource capacity planning
- Deployment troubleshooting and optimization

#### `environment_detector.py`
**Environment Detection Utilities** - Intelligent environment detection and configuration adaptation.

**Features:**
- Automatic environment detection (development/staging/production)
- Dynamic configuration loading based on environment
- Environment-specific validation rules
- Configuration override management
- Environment consistency validation

**Use Cases:**
- Automated environment-specific configuration
- Development workflow optimization
- Deployment environment validation
- Configuration testing across environments
- Environment-specific feature toggling

#### `environment_validator.py`
**Environment Validation Framework** - Comprehensive environment validation and compliance checking.

**Features:**
- Multi-environment configuration validation
- Compliance checking against organizational standards
- Environment-specific requirement validation
- Automated validation reporting
- Integration with CI/CD pipelines
- Custom validation rule support

**Use Cases:**
- Environment compliance auditing
- Pre-deployment validation
- Configuration consistency checking
- Regulatory compliance validation
- Automated testing integration

#### `docker_compose_validator.py`
**Docker Compose Configuration Validator** - Specialized validation for Docker Compose configurations.

**Features:**
- Comprehensive Docker Compose file validation
- Port conflict detection and resolution
- Volume mount validation and optimization
- Network configuration validation
- Service dependency analysis
- Performance optimization recommendations

**Use Cases:**
- Docker deployment validation
- Port conflict resolution
- Network configuration optimization
- Service dependency management
- Performance troubleshooting

#### `production_readiness_validator.py`
**Production Readiness Assessment** - Enterprise-grade production readiness validation.

**Features:**
- Comprehensive production readiness checklist
- Security assessment and compliance validation
- Performance benchmarking and threshold validation
- Scalability and high availability validation
- Disaster recovery capability assessment
- Regulatory compliance verification

**Use Cases:**
- Pre-production deployment validation
- Enterprise software certification
- Regulatory compliance assessment
- Risk assessment and mitigation planning
- Production deployment decision support

## 🔧 Configuration Management Workflow

### 1. Initial Setup
```bash
# Check system status
python unified_config_manager.py status

# Run initial audit
python unified_config_manager.py audit
```

### 2. Standardization
```bash
# Preview changes
python unified_config_manager.py standardize --dry-run

# Apply changes (with confirmation prompt)
python unified_config_manager.py standardize --apply
```

### 3. Environment Variable Migration
```bash
# Analyze current usage
python unified_config_manager.py migrate --report

# Migrate specific service
python unified_config_manager.py migrate --service my-service
```

### 4. Validation
```bash
# Validate Docker consistency
python unified_config_manager.py docker-check

# Generate comprehensive report
python unified_config_manager.py report --output monthly_config_report.json
```

## 📊 Configuration Standards

### File Structure
```
services/{service-name}/
├── config.yaml              # Service configuration (standardized)
├── config.development.yaml  # Development overrides
├── config.production.yaml   # Production overrides
├── docker-compose.yml       # Docker Compose configuration
└── main.py                  # Service entry point (updated for config)
```

### Configuration Schema
All services follow a standardized configuration schema with these sections:

- `server`: Host, port, debug settings
- `redis`: Redis connection configuration
- `logging`: Logging configuration
- `services`: Inter-service URLs and dependencies
- `limits`: Operational limits and constraints
- `health`: Health check configuration
- `security`: Security settings
- `custom`: Service-specific configuration

### Environment Variables
- Use `SCREAMING_SNAKE_CASE` naming convention
- Prefix service-specific variables appropriately
- Document all environment variables in service READMEs

## 🔍 Troubleshooting

### Common Issues

1. **Script not found**: Ensure you're running from the project root
2. **Permission errors**: Scripts need execute permissions
3. **Import errors**: Ensure Python path includes project root
4. **Configuration not loading**: Check YAML syntax and file permissions

### Getting Help

```bash
# Show available commands
python unified_config_manager.py --help

# Show command-specific help
python unified_config_manager.py standardize --help
```

## 📈 Maintenance

### Regular Tasks
- Run configuration audit weekly
- Validate Docker consistency before deployments
- Review environment variable migration reports
- Update configuration schemas for new features

### Updating Scripts
- Test changes on development environment first
- Update documentation when modifying interfaces
- Maintain backward compatibility where possible
- Add deprecation notices for replaced functionality

## 🚀 Advanced Usage

### Custom Configuration Classes
```python
from services.shared.infrastructure.config import BaseServiceConfig, ConfigurationManager

@dataclass
class MyServiceConfig(BaseServiceConfig):
    custom_setting: str = "default_value"

manager = ConfigurationManager(
    service_name="my-service",
    config_class=MyServiceConfig
)
```

### Custom Validators
```python
from services.shared.infrastructure.config import ConfigurationValidator

class MyValidator(ConfigurationValidator):
    def validate(self, config):
        errors = []
        if config.custom_setting not in ['value1', 'value2']:
            errors.append("Invalid custom_setting value")
        return errors
```

## 📚 Related Documentation

- `CONFIGURATION_STANDARDIZATION_COMPLETE.md` - Complete implementation guide
- `docs/CONFIGURATION_MANAGEMENT.md` - Usage documentation
- `services/shared/infrastructure/config/README.md` - API reference
- Service-specific READMEs for configuration details

## 🤝 Contributing

When adding new configuration management scripts:

1. Use the unified interface pattern
2. Follow existing naming conventions
3. Include comprehensive error handling
4. Add appropriate logging
5. Update this README
6. Test on all supported environments

## 📞 Support

For issues with configuration management:

1. Check the troubleshooting section above
2. Run `python unified_config_manager.py status` to verify system state
3. Review audit reports for specific issues
4. Check service-specific configuration documentation
