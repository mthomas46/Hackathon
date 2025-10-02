# Legacy & Deprecated Scripts

This directory contains legacy scripts that have been replaced by newer, more comprehensive solutions. These scripts are maintained for backward compatibility but are no longer actively developed.

## ⚠️ Important Notice

**These scripts are deprecated and should not be used for new implementations.** They are maintained only for backward compatibility and reference purposes.

## Scripts

### Configuration Management (Replaced by `unified_config_manager.py`)

#### `configuration_management_system.py`
**Legacy Configuration Management System** - Superseded by `unified_config_manager.py` in the parent directory.

**Replacement:** `../unified_config_manager.py`

#### `config_drift_detector.py`
**Legacy Configuration Drift Detector** - Replaced by integrated drift detection in `unified_config_manager.py`.

**Replacement:** `../unified_config_manager.py docker-check`

#### `validate_service_configs.py`
**Legacy Service Configuration Validator** - Superseded by `unified_config_manager.py audit`.

**Replacement:** `../unified_config_manager.py audit`

### Docker Management (Consolidated in `docker/` directory)

#### `main_docker_compose_standardizer.py`
**Legacy Docker Compose Standardizer** - Functionality moved to `docker/unified_docker_standardizer.py`.

**Replacement:** `../docker/unified_docker_standardizer.py`

#### `validate_docker_compose.py`
**Legacy Docker Compose Validator** - Consolidated into `docker_compose_validator.py` in parent directory.

**Replacement:** `../docker_compose_validator.py`

### Service Management (Replaced by startup scripts)

#### `unified_service_manager.py`
**Legacy Service Manager** - Superseded by `service_manager.py` in `../startup/` directory.

**Replacement:** `../../startup/service_manager.py`

#### `auto_healer.py`
**Legacy Auto-Healing System** - Functionality integrated into monitoring and startup scripts.

**Replacement:** Use monitoring scripts in `../../monitoring/`

### Performance & Monitoring (Moved to specialized directories)

#### `performance_analyzer.py`
**Legacy Performance Analyzer** - Moved to monitoring scripts.

**Replacement:** Scripts in `../../monitoring/`

#### `unified_health_monitor.py`
**Legacy Health Monitor** - Consolidated into monitoring directory.

**Replacement:** `../../monitoring/automated_health_monitoring.py`

### Development Tools (Consolidated elsewhere)

#### `run_profile_manager.py`
**Legacy Profile Manager** - Development workflow tools moved to utilities.

**Replacement:** Scripts in `../../utilities/`

#### `config_monitor_cli.py`
**Legacy Config Monitor CLI** - Integrated into main configuration management.

**Replacement:** `../unified_config_manager.py`

#### `pydantic_migration_plan.py`
**Legacy Pydantic Migration** - Migration completed and tools consolidated.

**Replacement:** Configuration management tools in parent directory

## Migration Guide

### For Configuration Management
```bash
# Old way
python legacy/configuration_management_system.py

# New way
python ../unified_config_manager.py
```

### For Docker Management
```bash
# Old way
python legacy/main_docker_compose_standardizer.py

# New way
python ../docker/unified_docker_standardizer.py
```

### For Service Management
```bash
# Old way
python legacy/unified_service_manager.py

# New way
python ../../startup/service_manager.py
```

## Removal Timeline

These legacy scripts will be removed in a future major release. Please migrate to the replacement scripts listed above.

## Support

For questions about migrating from legacy scripts, refer to the documentation for the replacement scripts or contact the development team.
