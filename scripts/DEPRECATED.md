# Deprecated Scripts

This document lists scripts that have been marked as deprecated and are no longer actively maintained or recommended for use.

## Categories of Deprecated Scripts

### Demo Scripts (`scripts/demo/`)
**Status**: DEPRECATED  
**Reason**: Phase-specific demonstration scripts from development phases  
**Files**:
- All files in `scripts/demo/` directory
- Created during various development phases (Phase 3, 4, 5, etc.)
- May not work with current system architecture

### Async Processing Scripts (`scripts/async/`)
**Status**: DEPRECATED  
**Reason**: Advanced async processing not currently used in the ecosystem  
**Files**:
- `async_job_processor.py`
- `async_optimizer.py` 
- `message_queue.py`
- `task_scheduler.py`

### Phase-Specific Integration Tests (`scripts/integration/`)
**Status**: DEPRECATED  
**Reason**: Phase 2 specific integration tests  
**Files**:
- `test_phase2_implementation.py`
- `test_phase2_simple.py`
- `test_phase2_focused.py`

### Migration Scripts (`scripts/migration/`)
**Status**: DEPRECATED  
**Reason**: DDD refactoring and migration completed  
**Files**:
- All files in `scripts/migration/` directory
- Used during DDD refactoring and system migration phases
- System has been successfully migrated

### Phase-Specific Scripts (Root Level)
**Status**: DEPRECATED
**Reason**: Development phase or proof-of-concept scripts
**Files**:
- `phase2_comprehensive_discovery.py`
- `phase4_security_scanning.py`
- `phase5_monitoring_observability.py`
- `proof_orchestrator_registration_capability.py`
- `final_document_persistence_proof.py`
- `discovery_agent_test_current_functionality.py`
- `orchestrator_discovery_integration_demo.py`

### Individual Deprecated Scripts in Subdirectories
**Status**: DEPRECATED
**Reason**: Various reasons - duplicates, superseded, phase-specific
**Files**:
- `scripts/cli/test_cli_simple.py` - Duplicate of `test_cli_consolidated.py`
- `scripts/ecosystem/ecosystem_api_audit.py` - Duplicate of `ecosystem_manager.py`
- `scripts/startup/start_all_services.py` - Duplicate of `service_manager.py`
- `scripts/hardening/pydantic_integration_demo.py` - Pydantic integration demo from migration phase
- `scripts/performance/caching_optimizer.py` - Unused performance optimization script
- `scripts/test/test_cli_analysis_service.py` - Superseded by consolidated CLI tests
- `scripts/testing/` (entire directory) - Individual testing scripts superseded by consolidated test suites

### Potentially Superseded CLI Scripts
**Status**: REVIEW NEEDED  
**Reason**: Multiple CLI scripts exist, some may be superseded  
**Files**:
- `enhanced_production_cli.py` - Check vs. `test_cli_consolidated.py`
- `expanded_cli_test.py` - May be superseded by consolidated tests
- `ecosystem_cli_executable.py` - Check if still needed
- `simple_document_cli.py` - May be superseded by more advanced CLIs
- `unified_ecosystem_cli.py` - Check if still current

## Current Active Scripts

### Audit Framework (`scripts/audit-framework/`)
✅ **ACTIVE** - Used in CI/CD, Docker, and Makefiles

### Docker Scripts (`scripts/docker/`)
✅ **ACTIVE** - Used for deployment validation

### Hardening Scripts (`scripts/hardening/`)
✅ **ACTIVE** - Used for configuration validation and management

### CLI Tests (`scripts/cli/`)
✅ **ACTIVE** - `test_cli_consolidated.py` is the main CLI test

### Safeguards (`scripts/safeguards/`)
✅ **ACTIVE** - Used in Makefiles for environment validation

### Services (`scripts/services/`)
✅ **ACTIVE** - Service testing and management

### Validation (`scripts/validation/`)
✅ **ACTIVE** - Validation scripts for the ecosystem

## Removal Recommendations

### Safe to Remove (Low Risk)
- All demo scripts in `scripts/demo/`
- All async processing scripts in `scripts/async/`
- Phase 2 integration tests
- Migration scripts in `scripts/migration/`
- Phase-specific root level scripts

### Review Before Removal (Medium Risk)
- Multiple CLI scripts - determine which is the canonical version
- Test scripts that might still have value

### Keep (High Value/Active Use)
- Audit framework scripts
- Docker validation scripts  
- Hardening/configuration scripts
- Current CLI test suite
- Safeguards scripts
- Service management scripts
- Validation scripts

## Migration Notes

If you need functionality from deprecated scripts:
1. Check if the functionality exists in current active scripts
2. Review recent commits to see if features were migrated
3. Contact maintainers for guidance on current equivalents

---
*Last updated: $(date)*
