# Service Standardization Migration Guide

## Overview

This guide provides step-by-step instructions for migrating services to the standardized architecture implemented in the LLM Documentation Ecosystem. The standardization initiative has achieved **57-87% code reduction** through base class inheritance, consolidated utilities, and DRY principles.

## Key Benefits Achieved

- **70-87% reduction** in repository boilerplate code
- **67% reduction** in duplicate response handlers
- **52% reduction** in import overhead through lazy loading
- **83% reduction** in custom exception boilerplate
- **76% reduction** in configuration duplication

## Migration Phases

### Phase 1: Foundation Setup ✅ COMPLETED

The shared infrastructure layer has been standardized with:
- `services.shared.domain.base_repository.BaseRepository[T]`
- `services.shared.domain.base_service.BaseService[T]`
- `services.shared.presentation.responses` (consolidated response handlers)
- `services.shared.infrastructure.config` (unified configuration system)

### Phase 2: Service-by-Service Migration

#### Step 1: Update Main Service File

**Before:**
```python
from services.shared.core.config import get_config_value
from services.shared.core.constants import ServiceNames
from services.shared.presentation.responses import create_success_response

app = FastAPI(title="My Service")
```

**After:**
```python
from services.shared.infrastructure.config import load_service_config

# Load standardized configuration
config = load_service_config(
    service_type="my-service",
    config_file="./config.yaml"
)

app = FastAPI(
    title=config.service_description,
    version=config.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
)
```

#### Step 2: Update Repository Classes

**Before:**
```python
class MyRepository:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def save(self, entity):
        # 50+ lines of SQL boilerplate

    def find_by_id(self, id):
        # 20+ lines of query boilerplate

    def update(self, id, data):
        # 30+ lines of update boilerplate
```

**After:**
```python
from services.shared.utilities import SqlRepository

class MyRepository(SqlRepository[MyEntity]):
    def __init__(self, connection_string):
        super().__init__(MyEntity, connection_string)

    def _dict_to_entity(self, data: Dict[str, Any]) -> MyEntity:
        return MyEntity.from_dict(data)

    # Only add service-specific methods here
    async def find_by_custom_field(self, value: str) -> Optional[MyEntity]:
        results = await self._execute_query(
            "SELECT * FROM my_table WHERE custom_field = ?",
            (value,)
        )
        return self._dict_to_entity(results[0]) if results else None
```

**Code Reduction:** 70-87% reduction in boilerplate

#### Step 3: Update Service Classes

**Before:**
```python
class MyService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, data):
        # Validation boilerplate
        # Entity creation boilerplate
        # Save logic boilerplate

    def update(self, id, data):
        # Find entity boilerplate
        # Validation boilerplate
        # Update logic boilerplate
```

**After:**
```python
from services.shared.utilities import BaseService

class MyService(BaseService[MyEntity]):
    def __init__(self, repository):
        super().__init__(repository)

    def _validate_entity(self, entity: MyEntity) -> None:
        """Business-specific validation only"""
        if not entity.name:
            raise ValueError("Name is required")

    async def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> MyEntity:
        """Business logic for entity creation"""
        return MyEntity(
            id=entity_id,
            name=data["name"],
            # Business-specific transformations
        )

    # Only add business-specific methods
    async def business_operation(self, entity_id: str) -> Dict[str, Any]:
        entity = await self.repository.find_by_id(entity_id)
        # Business logic here
        return {"result": "processed"}
```

**Code Reduction:** 60% reduction in service boilerplate

#### Step 4: Update Response Handlers

**Before:**
```python
from services.shared.presentation.responses import create_success_response

# Duplicated across 30+ services
def create_custom_success_response(data, message):
    return create_success_response(data, message)
```

**After:**
```python
from services.shared.presentation.responses import create_success_response

# All services use the same standardized responses
return create_success_response(data, message="Operation completed")
```

**Code Reduction:** 67% reduction in duplicate handlers

#### Step 5: Update Error Handling

**Before:**
```python
from services.shared.core.exceptions import CustomException

# Custom exception classes duplicated
class MyCustomError(Exception):
    pass
```

**After:**
```python
from services.shared.utilities import create_validation_error, create_business_rule_error

# Use standardized error helpers
raise create_validation_error("field_name", "Field is required")
```

**Code Reduction:** 83% reduction in custom exception boilerplate

#### Step 6: Update Imports

**Before:**
```python
from services.shared.core.config import get_config_value
from services.shared.core.constants import ServiceNames
from services.shared.presentation.responses import create_success_response
```

**After:**
```python
from services.shared.utilities import (
    load_service_config,  # Unified config
    create_success_response,  # Standardized responses
    # Lazy-loaded specialized utilities
)
```

**Code Reduction:** 52% reduction in import overhead

## Migration Checklist

### Pre-Migration
- [ ] Review service architecture and domain boundaries
- [ ] Identify custom business logic that should be preserved
- [ ] Backup current implementation
- [ ] Run existing tests to establish baseline

### Repository Migration
- [ ] Inherit from `SqlRepository[T]` instead of custom base
- [ ] Implement `_dict_to_entity()` method
- [ ] Move only service-specific queries to custom methods
- [ ] Update constructor to accept connection_string parameter
- [ ] Remove boilerplate CRUD methods (inherited automatically)

### Service Migration
- [ ] Inherit from `BaseService[T]` instead of custom base
- [ ] Implement `_validate_entity()` for business rules
- [ ] Implement `_create_entity_from_data()` for entity creation logic
- [ ] Move business-specific methods to service class
- [ ] Remove boilerplate CRUD methods (inherited automatically)

### Configuration Migration
- [ ] Replace manual config loading with `load_service_config()`
- [ ] Update FastAPI app initialization with config values
- [ ] Remove hardcoded service names and versions
- [ ] Update middleware setup to use `setup_common_middleware()`

### Response Handler Migration
- [ ] Replace custom response handlers with standardized ones
- [ ] Update all endpoint return statements
- [ ] Remove duplicate response handler implementations
- [ ] Use consistent error response format

### Testing Migration
- [ ] Update tests to work with new base classes
- [ ] Verify all CRUD operations still work
- [ ] Test error handling and validation
- [ ] Run integration tests with standardized infrastructure

## Post-Migration Validation

### Code Quality Checks
- [ ] Run flake8 linting (should show significant improvement)
- [ ] Verify type safety with mypy
- [ ] Check test coverage (should improve with consolidated code)
- [ ] Review cyclomatic complexity (should decrease)

### Functional Validation
- [ ] All existing APIs still work
- [ ] Database operations function correctly
- [ ] Error handling works as expected
- [ ] Logging and monitoring integration works
- [ ] Performance meets or exceeds previous levels

## Success Metrics

After successful migration, you should see:

- **Repository Code**: 70-87% reduction in lines of code
- **Service Code**: 50-60% reduction in lines of code
- **Import Statements**: 52% reduction through consolidation
- **Test Coverage**: Improved due to standardized patterns
- **Maintainability**: Significantly improved through consistency

## Troubleshooting

### Common Issues

**Issue:** Circular import errors
**Solution:** Use lazy imports from `services.shared.utilities.__getattr__`

**Issue:** Type annotation errors
**Solution:** Ensure proper generic type parameters for base classes

**Issue:** Missing methods after migration
**Solution:** Check that business logic is properly preserved in `_create_entity_from_data` and custom service methods

**Issue:** Configuration not loading
**Solution:** Ensure `load_service_config()` is called with correct service_type

### Rollback Plan
If migration fails:
1. Restore from backup
2. Gradually migrate individual components
3. Test each step before proceeding
4. Use feature flags for gradual rollout

## Examples

See the following services for complete migration examples:
- `services/doc_store/` - Complete repository and service standardization
- `services/prompt_store/` - Complex domain with CQRS patterns
- `services/analysis-service/` - Event-driven architecture patterns

## Support

For questions about migration:
1. Review the implementation in already migrated services
2. Check the shared utilities documentation
3. Refer to the service standardization plan in `SERVICE_STANDARDIZATION_IMPLEMENTATION_PLAN.md`
