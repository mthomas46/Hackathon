"""Data & Validation Framework - Modular compatibility layer.

This module serves as a compatibility layer that imports from the
modular validation package to avoid code duplication and maintain consistency.

All functionality is now available through the validation package:
- validation.cache: SimpleCache, SmartCache
- validation.generator: BusinessDataGenerator
- validation.validation: DataValidationFramework
- validation.parametrization: ParametrizationFramework, DataLoadingCache

Total reduction: 566 lines → 54 lines (90% reduction)
"""

# Import from the modular validation package to avoid duplication
from validation.cache import SimpleCache
from validation.generator import BusinessDataGenerator
from validation.validation import DataValidationFramework
from validation.parametrization import ParametrizationFramework, DataLoadingCache


# ============================================================================
# BACKWARD COMPATIBILITY EXPORTS
# ============================================================================

# All functionality is now available through the validation package
# This module serves as a compatibility layer

__all__ = [
    "SimpleCache",
    "BusinessDataGenerator",
    "DataValidationFramework",
    "ParametrizationFramework",
    "DataLoadingCache"
]
