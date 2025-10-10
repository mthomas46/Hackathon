"""
Utility modules for expert-finder-service.

This package contains reusable utility functions, validators, transformers,
and constants used throughout the service.
"""

from .validators import (
    validate_query_text,
    validate_limit,
    validate_id,
    validate_min_count,
    ValidationError
)

from .transformers import (
    user_dict_to_expert,
    enrich_with_documents
)

from .constants import (
    # Scoring Weights
    DEFAULT_ROLE_WEIGHT,
    DEFAULT_TOPIC_WEIGHT,
    DEFAULT_SERVICE_WEIGHT,
    DEFAULT_DOCUMENT_WEIGHT,
    
    # Validation Limits
    MIN_QUERY_LENGTH,
    MAX_QUERY_LENGTH,
    MAX_RESULTS,
    DEFAULT_RESULTS,
    
    # SME Thresholds
    SME_MIN_DOCUMENTS,
    SME_MIN_SCORE,
    
    # HTTP Configuration
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_RETRY_ATTEMPTS,
    
    # Scoring Thresholds
    EXCELLENT_MATCH_THRESHOLD,
    GOOD_MATCH_THRESHOLD,
    FAIR_MATCH_THRESHOLD,
    
    # Service URLs
    DEFAULT_USER_STORE_URL,
    DEFAULT_DOC_STORE_URL,
    DEFAULT_SERVICE_STORE_URL
)

__all__ = [
    # Validators
    "validate_query_text",
    "validate_limit",
    "validate_id",
    "validate_min_count",
    "ValidationError",
    
    # Transformers
    "user_dict_to_expert",
    "enrich_with_documents",
    
    # Constants
    "DEFAULT_ROLE_WEIGHT",
    "DEFAULT_TOPIC_WEIGHT",
    "DEFAULT_SERVICE_WEIGHT",
    "DEFAULT_DOCUMENT_WEIGHT",
    "MIN_QUERY_LENGTH",
    "MAX_QUERY_LENGTH",
    "MAX_RESULTS",
    "DEFAULT_RESULTS",
    "SME_MIN_DOCUMENTS",
    "SME_MIN_SCORE",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_RETRY_ATTEMPTS",
    "EXCELLENT_MATCH_THRESHOLD",
    "GOOD_MATCH_THRESHOLD",
    "FAIR_MATCH_THRESHOLD",
    "DEFAULT_USER_STORE_URL",
    "DEFAULT_DOC_STORE_URL",
    "DEFAULT_SERVICE_STORE_URL",
]

