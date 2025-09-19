#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

import sys
import os

# Add shared infrastructure to path
shared_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'shared')
sys.path.insert(0, shared_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'project-simulation'))

def test_shared_imports():
    """Test all shared service imports."""
    print("Testing shared service imports...")

    try:
        from services.shared.core.responses.responses import (
            create_success_response,
            create_error_response,
            create_validation_error_response,
            create_paginated_response,
            create_list_response,
            create_crud_response,
            SuccessResponse,
            ErrorResponse,
            ValidationErrorResponse,
            PaginatedResponse,
            ListResponse,
            CreateResponse,
            HealthResponse,
            SystemHealthResponse,
            HTTP_STATUS_CODES
        )
        print('✓ Shared responses imported successfully')
    except ImportError as e:
        print(f'✗ Shared responses import failed: {e}')

    try:
        from services.shared.utilities.utilities import (
            setup_common_middleware,
            attach_self_register,
            generate_id,
            clean_string
        )
        print('✓ Shared utilities imported successfully')
    except ImportError as e:
        print(f'✗ Shared utilities import failed: {e}')

    try:
        from services.shared.utilities.middleware import ServiceMiddleware
        print('✓ Shared middleware imported successfully')
    except ImportError as e:
        print(f'✗ Shared middleware import failed: {e}')

    try:
        from services.shared.monitoring.health import register_health_endpoints
        print('✓ Shared health imported successfully')
    except ImportError as e:
        print(f'✗ Shared health import failed: {e}')

    try:
        from services.shared.core.logging.correlation_middleware import CorrelationIdMiddleware
        print('✓ Shared correlation middleware imported successfully')
    except ImportError as e:
        print(f'✗ Shared correlation middleware import failed: {e}')

    try:
        from services.shared.utilities.error_handling import register_exception_handlers
        print('✓ Shared error handling imported successfully')
    except ImportError as e:
        print(f'✗ Shared error handling import failed: {e}')

def test_local_imports():
    """Test local project-simulation imports."""
    print("\nTesting local imports...")

    try:
        from services.project_simulation.simulation.infrastructure.di_container import get_simulation_container
        print('✓ DI container imported successfully')
    except ImportError as e:
        print(f'✗ DI container import failed: {e}')

    try:
        from services.project_simulation.simulation.infrastructure.logging import with_correlation_id, generate_correlation_id
        print('✓ Local logging imported successfully')
    except ImportError as e:
        print(f'✗ Local logging import failed: {e}')

    try:
        from services.project_simulation.simulation.infrastructure.health import create_simulation_health_endpoints
        print('✓ Local health imported successfully')
    except ImportError as e:
        print(f'✗ Local health import failed: {e}')

    try:
        from services.project_simulation.simulation.infrastructure.config import get_config, is_development
        print('✓ Config imported successfully')
    except ImportError as e:
        print(f'✗ Config import failed: {e}')

    try:
        from services.project_simulation.simulation.infrastructure.config.discovery import (
            get_service_discovery,
            start_service_discovery,
            stop_service_discovery
        )
        print('✓ Service discovery imported successfully')
    except ImportError as e:
        print(f'✗ Service discovery import failed: {e}')

    try:
        from services.project_simulation.simulation.presentation.api.hateoas import (
            SimulationResource,
            RootResource,
            HealthResource,
            create_hateoas_response,
            create_error_response
        )
        print('✓ HATEOAS imported successfully')
    except ImportError as e:
        print(f'✗ HATEOAS import failed: {e}')

if __name__ == "__main__":
    test_shared_imports()
    test_local_imports()
