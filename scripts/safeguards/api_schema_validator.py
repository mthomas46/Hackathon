#!/usr/bin/env python3
"""
API Schema Validation Framework
Standardized response validation to prevent schema mismatches across services
"""

from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of schema validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    service_name: str
    endpoint: str
    
    
class BaseResponseModel(BaseModel):
    """Base response model all services should inherit from"""
    success: bool
    message: str
    timestamp: str
    request_id: Optional[str] = None
    

class ListResponseModel(BaseResponseModel):
    """Standardized list response model"""
    data: Dict[str, Any]
    total: int
    has_more: bool
    limit: int
    offset: int
    

class SuccessResponseModel(BaseResponseModel):
    """Standardized success response model"""
    data: Optional[Dict[str, Any]] = None
    

class ErrorResponseModel(BaseResponseModel):
    """Standardized error response model"""
    error_code: str
    error_details: Optional[Dict[str, Any]] = None
    

class HealthResponseModel(BaseResponseModel):
    """Standardized health response model"""
    status: str  # "healthy", "unhealthy", "degraded"
    service: str
    version: str
    uptime_seconds: float
    environment: str
    dependencies: Optional[Dict[str, str]] = None
    

class APISchemaValidator:
    """Central API schema validation system"""
    
    def __init__(self):
        self.service_schemas = self._load_service_schemas()
        self.validation_results = []
        
    def _load_service_schemas(self) -> Dict[str, Dict[str, Type[BaseModel]]]:
        """Load schema definitions for all services"""
        return {
            "doc_store": {
                "/api/v1/documents": ListResponseModel,
                "/api/v1/documents/*": SuccessResponseModel,
                "/health": HealthResponseModel
            },
            "orchestrator": {
                "/api/v1/services": ListResponseModel,
                "/health": HealthResponseModel
            },
            "llm-gateway": {
                "/api/v1/providers": ListResponseModel,
                "/health": HealthResponseModel
            },
            "discovery-agent": {
                "/api/v1/discovery/services": ListResponseModel,
                "/health": HealthResponseModel
            },
            "analysis-service": {
                "/api/v1/analysis/analyze": SuccessResponseModel,
                "/api/v1/analysis/capabilities": ListResponseModel,
                "/health": HealthResponseModel
            },
            "prompt_store": {
                "/api/v1/prompts": ListResponseModel,
                "/health": HealthResponseModel
            }
        }
    
    def validate_response(self, service_name: str, endpoint: str, 
                         response_data: Dict[str, Any]) -> ValidationResult:
        """Validate API response against expected schema"""
        
        if service_name not in self.service_schemas:
            return ValidationResult(
                is_valid=False,
                errors=[f"No schema defined for service: {service_name}"],
                warnings=[],
                service_name=service_name,
                endpoint=endpoint
            )
        
        # Find matching endpoint schema
        schema_model = self._find_endpoint_schema(service_name, endpoint)
        if not schema_model:
            return ValidationResult(
                is_valid=False,
                errors=[f"No schema defined for endpoint: {endpoint}"],
                warnings=[],
                service_name=service_name,
                endpoint=endpoint
            )
        
        # Validate against schema
        try:
            schema_model(**response_data)
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                service_name=service_name,
                endpoint=endpoint
            )
        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(error) for error in e.errors()],
                warnings=[],
                service_name=service_name,
                endpoint=endpoint
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                service_name=service_name,
                endpoint=endpoint
            )
    
    def _find_endpoint_schema(self, service_name: str, endpoint: str) -> Optional[Type[BaseModel]]:
        """Find the appropriate schema for an endpoint"""
        service_schemas = self.service_schemas.get(service_name, {})
        
        # Exact match first
        if endpoint in service_schemas:
            return service_schemas[endpoint]
        
        # Pattern matching for dynamic endpoints
        for pattern, schema in service_schemas.items():
            if "*" in pattern:
                pattern_parts = pattern.split("*")
                if len(pattern_parts) == 2:
                    prefix, suffix = pattern_parts
                    if endpoint.startswith(prefix) and endpoint.endswith(suffix):
                        return schema
        
        return None
    
    def validate_service_compliance(self, service_name: str) -> Dict[str, Any]:
        """Validate all known endpoints for a service"""
        results = {
            "service": service_name,
            "total_endpoints": 0,
            "valid_endpoints": 0,
            "failed_endpoints": [],
            "compliance_score": 0.0
        }
        
        if service_name not in self.service_schemas:
            results["error"] = f"No schemas defined for {service_name}"
            return results
        
        # This would be called by the actual testing framework
        # For now, return placeholder structure
        results["total_endpoints"] = len(self.service_schemas[service_name])
        results["compliance_score"] = 100.0  # Will be calculated during actual testing
        
        return results
    
    def generate_schema_docs(self) -> str:
        """Generate documentation for all API schemas"""
        docs = "# API Schema Documentation\n\n"
        docs += "This document defines the standardized API response schemas for all services.\n\n"
        
        for service_name, endpoints in self.service_schemas.items():
            docs += f"## {service_name.title()} Service\n\n"
            
            for endpoint, schema in endpoints.items():
                docs += f"### `{endpoint}`\n"
                docs += f"**Schema**: `{schema.__name__}`\n\n"
                
                # Add schema fields
                if hasattr(schema, 'model_fields'):
                    docs += "**Fields**:\n"
                    for field_name, field_info in schema.model_fields.items():
                        docs += f"- `{field_name}`: {field_info.annotation}\n"
                docs += "\n"
        
        return docs


class ResponseSchemaEnforcer:
    """Decorator and middleware for enforcing response schemas"""
    
    def __init__(self, validator: APISchemaValidator):
        self.validator = validator
        
    def enforce_schema(self, service_name: str, endpoint: str):
        """Decorator to enforce response schema validation"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    
                    # Validate response
                    if isinstance(result, dict):
                        validation_result = self.validator.validate_response(
                            service_name, endpoint, result
                        )
                        
                        if not validation_result.is_valid:
                            logger.error(f"Schema validation failed for {service_name}{endpoint}: {validation_result.errors}")
                            # Log but don't break - return standardized error
                            return {
                                "success": False,
                                "message": "Internal server error - response validation failed",
                                "error_code": "SCHEMA_VALIDATION_ERROR",
                                "timestamp": "2025-09-18T16:00:00Z"
                            }
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Schema enforcement error for {service_name}{endpoint}: {str(e)}")
                    return {
                        "success": False,
                        "message": "Internal server error",
                        "error_code": "SCHEMA_ENFORCEMENT_ERROR", 
                        "timestamp": "2025-09-18T16:00:00Z"
                    }
            return wrapper
        return decorator


# Usage examples and testing functions
def test_doc_store_response():
    """Test doc_store response validation"""
    validator = APISchemaValidator()
    
    # Test invalid response (the one we found in audit)
    invalid_response = {
        "success": True,
        "message": "Documents listed successfully",
        "timestamp": "2025-09-18T16:15:57.892780Z",
        "data": {
            "items": [{"id": "test", "content": "test"}],
            "total": 1,
            "has_more": False
        }
        # Missing required fields for ListResponseModel
    }
    
    result = validator.validate_response("doc_store", "/api/v1/documents", invalid_response)
    print(f"Validation Result: {result}")
    
    # Test valid response
    valid_response = {
        "success": True,
        "message": "Documents listed successfully", 
        "timestamp": "2025-09-18T16:15:57.892780Z",
        "data": {
            "items": [{"id": "test", "content": "test"}],
            "total": 1,
            "has_more": False
        },
        "total": 1,
        "has_more": False,
        "limit": 50,
        "offset": 0
    }
    
    result = validator.validate_response("doc_store", "/api/v1/documents", valid_response)
    print(f"Valid Response Result: {result}")


if __name__ == "__main__":
    # Run validation tests
    test_doc_store_response()
    
    # Generate schema documentation
    validator = APISchemaValidator()
    docs = validator.generate_schema_docs()
    
    with open("/Users/mykalthomas/Documents/work/Hackathon/docs/API_SCHEMA_STANDARDS.md", "w") as f:
        f.write(docs)
    
    print("✅ API Schema Validation Framework created")
    print("✅ Schema documentation generated")
