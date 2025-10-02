# Service Test Scripts

This directory contains test scripts for individual service validation and service-specific functionality.

## Scripts

### Service Import Tests

#### `test_services.py`
**Service Import Validator** - Comprehensive validation of service module imports and dependency resolution across all services.

**Features:**
- Complete service import testing for all 29 services
- Dependency resolution and conflict detection
- Import path validation and consistency checking
- Service initialization validation
- Module loading error detection and reporting

**Use Cases:**
- Post-refactoring validation of service imports
- Dependency management and conflict resolution
- Service module integrity assurance
- Development environment setup validation
- CI/CD pipeline import validation

#### `test_services_direct.py`
**Direct Service Module Tester** - Lightweight testing of service modules without full application startup.

**Features:**
- Direct module import testing without service initialization
- Configuration validation without runtime dependencies
- Module structure and interface validation
- Fast feedback for development workflow
- Minimal resource usage for quick validation

**Use Cases:**
- Development-time module validation
- Quick import testing during development
- CI/CD pipeline fast feedback
- Pre-commit validation hooks
- Development environment sanity checks

### Service Runner Scripts

#### `run_docstore.py`
**Document Store Service Runner** - Standalone execution and testing of the document store service.

**Features:**
- Document store service startup and configuration
- Database connectivity and schema validation
- Service health monitoring and endpoint testing
- Document CRUD operation validation
- Performance benchmarking for document operations

**Use Cases:**
- Document store service development and testing
- Database connectivity troubleshooting
- Document storage functionality validation
- Performance optimization for document operations
- Service isolation testing

#### `run_promptstore.py`
**Prompt Store Service Runner** - Standalone execution and testing of the prompt store service.

**Features:**
- Prompt store service startup and configuration
- Prompt data management and validation
- Service health monitoring and API testing
- Prompt retrieval and storage operation validation
- Performance benchmarking for prompt operations

**Use Cases:**
- Prompt store service development and testing
- Prompt data management validation
- AI prompt workflow optimization
- Service isolation testing
- Prompt storage performance tuning

#### `run_orchestrator_standalone.py`
**Orchestrator Service Runner** - Standalone execution of the workflow orchestration service.

**Features:**
- Workflow orchestration service startup
- Multi-service coordination validation
- Workflow execution and state management
- Service integration point testing
- Orchestration performance monitoring

**Use Cases:**
- Workflow orchestration development and testing
- Business process automation validation
- Service coordination troubleshooting
- Workflow performance optimization
- Orchestration logic debugging

### Test Data Scripts

#### `populate_docstore_test_data.py`
**Document Store Test Data Generator** - Automated generation and population of test data for document store validation.

**Features:**
- Realistic test document generation
- Bulk data population capabilities
- Document metadata and content validation
- Performance testing data sets
- Data consistency and integrity validation

**Use Cases:**
- Document store functionality testing
- Performance benchmarking with realistic data
- Data migration and backup testing
- Content search and retrieval validation
- Document processing workflow testing

#### `populate_promptstore_test_data.py`
**Prompt Store Test Data Generator** - Automated generation and population of test prompts for prompt store validation.

**Features:**
- Diverse prompt template generation
- AI model compatibility testing data
- Prompt performance benchmarking data sets
- Prompt categorization and tagging
- Data consistency validation

**Use Cases:**
- AI prompt management testing
- Prompt retrieval performance optimization
- AI model integration validation
- Prompt workflow testing
- Prompt data quality assurance

### Interpreter Tests

#### `test_interpreter_only.py`
**Interpreter Service Validator** - Focused testing of the code execution interpreter service.

**Features:**
- Code execution environment validation
- Security sandbox testing
- Execution timeout and resource limit validation
- Multi-language support validation
- Error handling and recovery testing

**Use Cases:**
- Code execution service validation
- Security vulnerability testing for code execution
- Multi-language support verification
- Performance optimization for code execution
- Interpreter service reliability testing

## Test Scope

Service tests focus on:
- ✅ Service module imports and dependencies
- ✅ Service-specific configuration validation
- ✅ Individual service startup and basic functionality
- ✅ Service-specific business logic
- ✅ Database operations for individual services
- ✅ Service health endpoints

## What Service Tests DON'T Cover

Service tests do NOT test:
- ❌ CLI functionality (belongs in CLI tests)
- ❌ Cross-service communication (belongs in integration tests)
- ❌ Multi-service workflows (belongs in integration tests)
- ❌ Docker containerization (belongs in integration tests)

## Usage

```bash
# Test all service imports
python scripts/services/test_services.py

# Test specific service
python scripts/services/test_interpreter_only.py

# Populate test data
python scripts/services/populate_docstore_test_data.py
```

## Integration with Other Test Suites

Service tests provide the foundation for integration tests. They ensure individual services work correctly before testing cross-service interactions.
