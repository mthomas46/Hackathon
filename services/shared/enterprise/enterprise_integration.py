#!/usr/bin/env python3
"""
Enterprise Integration Framework

This module provides standardized API patterns, workflow context propagation,
and service mesh compatibility for the entire ecosystem.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Callable, Type, Union, TypeVar
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import hmac
import base64
from contextvars import ContextVar
import aiohttp
from aiohttp import web
import redis.asyncio as redis
from pydantic import BaseModel, Field, validator
# import jwt  # Optional dependency for JWT token validation
from functools import wraps

from ..core.constants_new import ServiceNames
from ..monitoring.logging import fire_and_forget
from ..caching.intelligent_caching import get_service_cache
from .error_handling.error_handling import enterprise_error_handler, ErrorContext, ErrorSeverity, ErrorCategory


# Context variables for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
workflow_id_context: ContextVar[Optional[str]] = ContextVar('workflow_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class APIVersion(Enum):
    """API version enumeration."""
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


class ContentType(Enum):
    """Content type enumeration."""
    JSON = "application/json"
    XML = "application/xml"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"


class WorkflowContext(BaseModel):
    """Standardized workflow context for propagation."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    user_id: Optional[str] = Field(None, description="User initiating the workflow")
    correlation_id: str = Field(..., description="Request correlation identifier")
    request_id: str = Field(..., description="Unique request identifier")
    parent_workflow_id: Optional[str] = Field(None, description="Parent workflow if nested")
    step_id: Optional[str] = Field(None, description="Current workflow step")
    step_name: Optional[str] = Field(None, description="Current step name")
    total_steps: Optional[int] = Field(None, description="Total workflow steps")
    current_step: Optional[int] = Field(None, description="Current step number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Workflow creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    @validator('workflow_id', 'correlation_id', 'request_id')
    def validate_ids(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("ID must be a non-empty string")
        return v

    def to_headers(self) -> Dict[str, str]:
        """Convert context to HTTP headers."""
        return {
            'X-Workflow-ID': self.workflow_id,
            'X-Correlation-ID': self.correlation_id,
            'X-Request-ID': self.request_id,
            'X-User-ID': self.user_id or '',
            'X-Step-ID': self.step_id or '',
            'X-Step-Name': self.step_name or '',
            'X-Total-Steps': str(self.total_steps) if self.total_steps else '',
            'X-Current-Step': str(self.current_step) if self.current_step else '',
            'X-Workflow-Metadata': json.dumps(self.metadata),
            'X-Workflow-Created': self.created_at.isoformat(),
            'X-Workflow-Updated': self.updated_at.isoformat()
        }

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> Optional['WorkflowContext']:
        """Create context from HTTP headers."""
        try:
            workflow_id = headers.get('X-Workflow-ID')
            if not workflow_id:
                return None

            return cls(
                workflow_id=workflow_id,
                user_id=headers.get('X-User-ID') or None,
                correlation_id=headers.get('X-Correlation-ID', str(uuid.uuid4())),
                request_id=headers.get('X-Request-ID', str(uuid.uuid4())),
                parent_workflow_id=headers.get('X-Parent-Workflow-ID'),
                step_id=headers.get('X-Step-ID'),
                step_name=headers.get('X-Step-Name'),
                total_steps=int(headers.get('X-Total-Steps')) if headers.get('X-Total-Steps') else None,
                current_step=int(headers.get('X-Current-Step')) if headers.get('X-Current-Step') else None,
                metadata=json.loads(headers.get('X-Workflow-Metadata', '{}')),
                created_at=datetime.fromisoformat(headers.get('X-Workflow-Created', datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(headers.get('X-Workflow-Updated', datetime.now().isoformat()))
            )
        except (ValueError, json.JSONDecodeError):
            return None


class ServiceMeshClient:
    """Service mesh compatible HTTP client."""

    def __init__(self, service_name: str, timeout: float = 30.0, retries: int = 3):
        self.service_name = service_name
        self.timeout = timeout
        self.retries = retries
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = get_service_cache(service_name)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': f'Hackathon-Service/{self.service_name}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with service mesh features."""
        workflow_context = self._get_current_workflow_context()

        # Add workflow context to headers
        if workflow_context:
            headers = kwargs.get('headers', {})
            headers.update(workflow_context.to_headers())
            kwargs['headers'] = headers

        # Add correlation ID if not present
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        if 'X-Correlation-ID' not in kwargs['headers']:
            correlation_id = correlation_id_context.get()
            if correlation_id:
                kwargs['headers']['X-Correlation-ID'] = correlation_id
            else:
                kwargs['headers']['X-Correlation-ID'] = str(uuid.uuid4())

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.retries):
            try:
                if not self.session:
                    raise RuntimeError("Client session not initialized")

                async with self.session.request(method, url, **kwargs) as response:
                    result = await self._handle_response(response)

                    # Cache successful GET requests
                    if method.upper() == 'GET' and response.status == 200:
                        cache_key = self._generate_cache_key(method, url, kwargs)
                        await self.cache.set(cache_key, result, ttl_seconds=300)  # 5 minute TTL

                    return result

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < self.retries - 1:
                    delay = (2 ** attempt) * 0.1  # Exponential backoff
                    await asyncio.sleep(delay)
                else:
                    # Create error context for enterprise error handler
                    error_context = ErrorContext(
                        service_name=self.service_name,
                        operation=f"http_{method.lower()}_request",
                        workflow_id=workflow_context.workflow_id if workflow_context else None,
                        user_id=workflow_context.user_id if workflow_context else None,
                        severity=ErrorSeverity.HIGH if attempt == self.retries - 1 else ErrorSeverity.MEDIUM,
                        category=ErrorCategory.NETWORK
                    )

                    await enterprise_error_handler.handle_error(e, error_context)

        raise last_exception or RuntimeError("Request failed after all retries")

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET request with caching."""
        cache_key = self._generate_cache_key('GET', url, kwargs)
        cached_result = await self.cache.get(cache_key)

        if cached_result is not None:
            return cached_result

        return await self.request('GET', url, **kwargs)

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """POST request."""
        return await self.request('POST', url, **kwargs)

    async def put(self, url: str, **kwargs) -> Dict[str, Any]:
        """PUT request."""
        return await self.request('PUT', url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """DELETE request."""
        return await self.request('DELETE', url, **kwargs)

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle HTTP response with standardized error handling."""
        if response.status >= 400:
            error_text = await response.text()
            error_data = {
                'status_code': response.status,
                'url': str(response.url),
                'method': response.method,
                'headers': dict(response.headers),
                'error_body': error_text
            }

            if response.status >= 500:
                raise aiohttp.ClientResponseError(
                    response.request_info,
                    response.history,
                    status=response.status,
                    message=f"Server error: {error_text}",
                    headers=response.headers
                )
            elif response.status >= 400:
                raise aiohttp.ClientResponseError(
                    response.request_info,
                    response.history,
                    status=response.status,
                    message=f"Client error: {error_text}",
                    headers=response.headers
                )

        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return await response.json()
        else:
            return {'text': await response.text(), 'status_code': response.status}

    def _generate_cache_key(self, method: str, url: str, kwargs: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        key_data = {
            'method': method,
            'url': url,
            'params': kwargs.get('params', {}),
            'data': kwargs.get('json', kwargs.get('data', {}))
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_current_workflow_context(self) -> Optional[WorkflowContext]:
        """Get current workflow context from context variables."""
        workflow_id = workflow_id_context.get()
        if not workflow_id:
            return None

        return WorkflowContext(
            workflow_id=workflow_id,
            user_id=user_id_context.get(),
            correlation_id=correlation_id_context.get() or str(uuid.uuid4()),
            request_id=request_id_context.get() or str(uuid.uuid4())
        )


class StandardizedAPIResponse(BaseModel):
    """Standardized API response model."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field("", description="Human-readable message")
    data: Optional[Any] = Field(None, description="Response data")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    version: str = Field("v1", description="API version")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

    def add_error(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the response."""
        self.errors.append({
            'code': code,
            'message': message,
            'details': details or {}
        })
        self.success = False

    def set_processing_time(self, start_time: float):
        """Set processing time from start time."""
        self.processing_time_ms = (time.time() - start_time) * 1000


class StandardizedAPIRequest(BaseModel):
    """Standardized API request model."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Request identifier")
    workflow_context: Optional[WorkflowContext] = Field(None, description="Workflow context")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Request parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Request metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")

    @classmethod
    def from_request(cls, request: web.Request) -> 'StandardizedAPIRequest':
        """Create from aiohttp web request."""
        workflow_context = WorkflowContext.from_headers(dict(request.headers))

        return cls(
            request_id=request.headers.get('X-Request-ID', str(uuid.uuid4())),
            workflow_context=workflow_context,
            parameters=dict(request.query) if request.query else {},
            metadata={
                'method': request.method,
                'path': request.path,
                'remote': request.remote,
                'user_agent': request.headers.get('User-Agent', ''),
                'content_type': request.headers.get('Content-Type', ''),
                'content_length': request.headers.get('Content-Length', '')
            }
        )


class ServiceRegistry:
    """Service registry for service mesh discovery."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.service_endpoints: Dict[str, Dict[str, Any]] = {}
        self.health_checks: Dict[str, Dict[str, Any]] = {}

    async def connect(self):
        """Connect to Redis for service registry."""
        self.redis = redis.from_url(self.redis_url)

    async def register_service(self, service_name: str, endpoints: Dict[str, Any],
                             metadata: Optional[Dict[str, Any]] = None):
        """Register a service with its endpoints."""
        service_info = {
            'service_name': service_name,
            'endpoints': endpoints,
            'metadata': metadata or {},
            'registered_at': datetime.now().isoformat(),
            'status': 'healthy'
        }

        self.service_endpoints[service_name] = service_info

        if self.redis:
            await self.redis.setex(
                f"service:{service_name}",
                300,  # 5 minute TTL
                json.dumps(service_info)
            )

    async def discover_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Discover a service endpoint."""
        # Try local cache first
        if service_name in self.service_endpoints:
            return self.service_endpoints[service_name]

        # Try Redis
        if self.redis:
            service_data = await self.redis.get(f"service:{service_name}")
            if service_data:
                service_info = json.loads(service_data)
                self.service_endpoints[service_name] = service_info
                return service_info

        return None

    async def update_health_status(self, service_name: str, status: str, details: Dict[str, Any]):
        """Update service health status."""
        self.health_checks[service_name] = {
            'status': status,
            'details': details,
            'last_check': datetime.now().isoformat()
        }

        if self.redis:
            await self.redis.setex(
                f"health:{service_name}",
                60,  # 1 minute TTL
                json.dumps(self.health_checks[service_name])
            )

    async def get_service_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service health status."""
        if service_name in self.health_checks:
            return self.health_checks[service_name]

        if self.redis:
            health_data = await self.redis.get(f"health:{service_name}")
            if health_data:
                return json.loads(health_data)

        return None


# Global service registry instance
service_registry = ServiceRegistry()


def standardized_api_handler(api_version: APIVersion = APIVersion.V1):
    """Decorator for standardized API handlers."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: web.Request) -> web.Response:
            start_time = time.time()

            try:
                # Create standardized request
                std_request = StandardizedAPIRequest.from_request(request)

                # Set context variables
                request_token = request_id_context.set(std_request.request_id)
                if std_request.workflow_context:
                    workflow_token = workflow_id_context.set(std_request.workflow_context.workflow_id)
                    user_token = user_id_context.set(std_request.workflow_context.user_id)
                    correlation_token = correlation_id_context.set(std_request.workflow_context.correlation_id)

                # Call the actual handler
                result = await func(request, std_request)

                # Create standardized response
                if isinstance(result, dict):
                    response = StandardizedAPIResponse(**result)
                elif isinstance(result, StandardizedAPIResponse):
                    response = result
                else:
                    response = StandardizedAPIResponse(
                        success=True,
                        data=result,
                        message="Operation completed successfully"
                    )

                response.version = api_version.value
                response.set_processing_time(start_time)

                # Return JSON response
                return web.json_response(
                    asdict(response),
                    status=200 if response.success else 400,
                    headers={
                        'X-API-Version': api_version.value,
                        'X-Request-ID': std_request.request_id,
                        'X-Processing-Time': f"{response.processing_time_ms:.2f}ms"
                    }
                )

            except Exception as e:
                # Create error response
                error_response = StandardizedAPIResponse(
                    success=False,
                    message="Internal server error",
                    errors=[{
                        'code': 'INTERNAL_ERROR',
                        'message': str(e),
                        'details': {}
                    }]
                )
                error_response.set_processing_time(start_time)

                # Handle error through enterprise error handler
                error_context = ErrorContext(
                    service_name=request.app.get('service_name', 'unknown'),
                    operation=f"{request.method} {request.path}",
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.INTERNAL
                )

                await enterprise_error_handler.handle_error(e, error_context)

                return web.json_response(
                    asdict(error_response),
                    status=500,
                    headers={
                        'X-API-Version': api_version.value,
                        'X-Request-ID': request.headers.get('X-Request-ID', str(uuid.uuid4())),
                        'X-Processing-Time': f"{error_response.processing_time_ms:.2f}ms"
                    }
                )

        return wrapper
    return decorator


def workflow_context_middleware(service_name: str):
    """Middleware for workflow context propagation."""
    @web.middleware
    async def middleware(request: web.Request, handler):
        # Extract workflow context from headers
        workflow_context = WorkflowContext.from_headers(dict(request.headers))

        # Set context variables
        tokens = []
        if workflow_context:
            tokens.append(workflow_id_context.set(workflow_context.workflow_id))
            tokens.append(user_id_context.set(workflow_context.user_id))
            tokens.append(correlation_id_context.set(workflow_context.correlation_id))
            tokens.append(request_id_context.set(workflow_context.request_id))

        try:
            # Add service name to app for error handling
            request.app['service_name'] = service_name

            # Call handler
            response = await handler(request)

            # Add workflow context to response headers
            if workflow_context:
                for header, value in workflow_context.to_headers().items():
                    response.headers[header] = value

            return response

        finally:
            # Reset context variables
            for token in tokens:
                token.reset()

    return middleware


def service_mesh_middleware():
    """Middleware for service mesh compatibility."""
    @web.middleware
    async def middleware(request: web.Request, handler):
        # Add service mesh headers
        request.headers = dict(request.headers)  # Make headers mutable

        # Ensure correlation ID
        if 'X-Correlation-ID' not in request.headers:
            request.headers['X-Correlation-ID'] = str(uuid.uuid4())

        # Add tracing headers for service mesh
        if 'X-Trace-ID' not in request.headers:
            request.headers['X-Trace-ID'] = str(uuid.uuid4())

        # Add service mesh routing headers
        request.headers['X-Service-Mesh-Version'] = '1.0'

        response = await handler(request)

        # Add service mesh response headers
        response.headers['X-Service-Mesh-Version'] = '1.0'
        response.headers['X-Correlation-ID'] = request.headers.get('X-Correlation-ID')

        return response

    return middleware


async def initialize_enterprise_integration():
    """Initialize enterprise integration components."""
    # Connect to service registry
    await service_registry.connect()

    # Register core services
    core_services = [
        ServiceNames.DOCUMENT_STORE,
        ServiceNames.PROMPT_STORE,
        ServiceNames.ANALYSIS_SERVICE,
        ServiceNames.INTERPRETER,
        ServiceNames.SUMMARIZER_HUB,
        ServiceNames.SOURCE_AGENT,
        ServiceNames.DISCOVERY_AGENT
    ]

    for service_name in core_services:
        await service_registry.register_service(
            service_name,
            {
                'base_url': f'http://{service_name}:8000',
                'health_endpoint': '/health',
                'api_endpoints': {
                    'v1': f'/api/v1',
                    'docs': '/docs'
                }
            },
            {
                'type': 'microservice',
                'framework': 'fastapi',
                'language': 'python',
                'version': '1.0.0'
            }
        )

    fire_and_forget("info", "Enterprise integration initialized successfully", "system")


@dataclass
class RequestContext:
    """Request context for tracking API calls."""
    request_id: str
    user_id: Optional[str] = None
    service_name: str = "unknown"
    operation: str = "unknown"
    started_at: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


class StandardizedAPIManager:
    """Manager for standardized API responses and patterns."""

    def __init__(self):
        self.response_format = "json"

    async def initialize(self):
        """Initialize API manager."""
        pass

    def create_response(self, success: bool, message: str, data: Any = None, **kwargs) -> StandardizedAPIResponse:
        """Create standardized API response."""
        return StandardizedAPIResponse(
            success=success,
            message=message,
            data=data,
            metadata=kwargs
        )


class ContextPropagationManager:
    """Manager for context propagation across services."""

    def __init__(self):
        self.context_stack = []

    async def initialize(self):
        """Initialize context manager."""
        pass

    def get_current_context(self) -> Optional[RequestContext]:
        """Get current request context."""
        return RequestContext(request_id=str(uuid.uuid4())) if self.context_stack else None


class ServiceDiscoveryManager:
    """Service discovery and endpoint management."""

    def __init__(self):
        self.services = {}
        self.endpoints = {}

    async def initialize(self):
        """Initialize service discovery."""
        # Initialize with known services
        self.services = {
            "workflow_service": {"host": "localhost", "port": 5080, "version": "1.0.0"},
            "doc_store": {"host": "localhost", "port": 5090, "version": "1.0.0"},
            "analysis_service": {"host": "localhost", "port": 5100, "version": "1.0.0"}
        }

    async def get_service_endpoint(self, service_name: str, operation: str) -> Optional[str]:
        """Get service endpoint for operation."""
        if service_name in self.services:
            service = self.services[service_name]
            return f"http://{service['host']}:{service['port']}"
        return None


class EnterpriseIntegrationManager:
    """Main manager for enterprise integration features."""

    def __init__(self):
        self.initialized = False
        self.service_discovery = ServiceDiscoveryManager()
        self.api_manager = StandardizedAPIManager()
        self.context_manager = ContextPropagationManager()

    async def initialize(self):
        """Initialize enterprise integration components."""
        if not self.initialized:
            await self.service_discovery.initialize()
            await self.api_manager.initialize()
            await self.context_manager.initialize()
            self.initialized = True
            fire_and_forget("info", "Enterprise integration manager initialized", "system")

    async def get_service_endpoint(self, service_name: str, operation: str) -> Optional[str]:
        """Get service endpoint for operation."""
        return await self.service_discovery.get_service_endpoint(service_name, operation)

    def create_standardized_response(self, success: bool, message: str,
                                   data: Any = None, **kwargs) -> StandardizedAPIResponse:
        """Create standardized API response."""
        return self.api_manager.create_response(success, message, data, **kwargs)

    def get_request_context(self) -> Optional[RequestContext]:
        """Get current request context."""
        return self.context_manager.get_current_context()


# Utility functions
def create_workflow_context(workflow_id: Optional[str] = None,
                          user_id: Optional[str] = None) -> WorkflowContext:
    """Create a new workflow context."""
    return WorkflowContext(
        workflow_id=workflow_id or str(uuid.uuid4()),
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4())
    )


def get_current_workflow_context() -> Optional[WorkflowContext]:
    """Get current workflow context from context variables."""
    workflow_id = workflow_id_context.get()
    if not workflow_id:
        return None

    return WorkflowContext(
        workflow_id=workflow_id,
        user_id=user_id_context.get(),
        correlation_id=correlation_id_context.get(),
        request_id=request_id_context.get()
    )


# Import time for processing time calculation
import time
