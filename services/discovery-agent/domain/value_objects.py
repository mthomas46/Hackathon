"""Value Objects for Service Discovery Domain.

This module defines value objects that represent concepts in the service discovery domain.
Value objects are immutable and compared by value rather than identity.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlparse

try:
    from services.shared.domain.entities.value_objects import ValueObject
except ImportError:
    # Fallback for test environments or different working directories
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    while current_dir.parent != current_dir:
        shared_path = current_dir.parent / "shared" / "domain" / "entities" / "value_objects.py"
        if shared_path.exists():
            sys.path.insert(0, str(shared_path.parent.parent.parent.parent))
            break
        current_dir = current_dir.parent
    from services.shared.domain.entities.value_objects import ValueObject


@dataclass(frozen=True)
class DiscoverySpec(ValueObject):
    """Value object representing an OpenAPI specification for discovery."""

    url: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    version: str = "3.0.0"

    def __post_init__(self):
        """Validate the discovery specification."""
        if not self.url and not self.content:
            from .exceptions import DiscoveryConfigurationError
            raise DiscoveryConfigurationError("Either URL or content must be provided")

        if self.url:
            self._validate_url(self.url)

        if self.content:
            self._validate_openapi_content(self.content)

    def _validate_url(self, url: str) -> None:
        """Validate URL format."""
        parsed = urlparse(url)
        from .exceptions import MalformedUrlError
        if not parsed.scheme or not parsed.netloc:
            raise MalformedUrlError(f"Invalid URL format: {url}")

    def _validate_openapi_content(self, content: Dict[str, Any]) -> None:
        """Validate OpenAPI content structure."""
        from .exceptions import InvalidOpenApiSpecError, UnsupportedApiVersionError

        if not isinstance(content, dict):
            raise InvalidOpenApiSpecError("OpenAPI content must be a dictionary")

        if "paths" not in content:
            raise InvalidOpenApiSpecError("OpenAPI spec must contain 'paths'")

        if "info" not in content:
            raise InvalidOpenApiSpecError("OpenAPI spec must contain 'info'")

        # Check version
        openapi_version = content.get("openapi", "").split(".")[0]
        if openapi_version and openapi_version not in ["3"]:
            raise UnsupportedApiVersionError(f"Unsupported OpenAPI version: {openapi_version}")

    @property
    def has_content(self) -> bool:
        """Check if spec has inline content."""
        return self.content is not None

    @property
    def has_url(self) -> bool:
        """Check if spec has URL reference."""
        return self.url is not None


@dataclass(frozen=True)
class EndpointMetadata(ValueObject):
    """Value object for endpoint metadata."""

    operation_id: Optional[str] = None
    deprecated: bool = False
    security_requirements: Optional[list] = None
    request_body_schema: Optional[Dict[str, Any]] = None
    response_schemas: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def from_openapi_operation(cls, operation: Dict[str, Any]) -> 'EndpointMetadata':
        """Create metadata from OpenAPI operation definition."""
        return cls(
            operation_id=operation.get("operationId"),
            deprecated=operation.get("deprecated", False),
            security_requirements=operation.get("security"),
            request_body_schema=operation.get("requestBody", {}).get("content", {}),
            response_schemas=operation.get("responses", {})
        )


@dataclass(frozen=True)
class ServiceMetadata(ValueObject):
    """Value object for service metadata."""

    title: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    license: Optional[Dict[str, str]] = None
    terms_of_service: Optional[str] = None

    @classmethod
    def from_openapi_info(cls, info: Dict[str, Any]) -> 'ServiceMetadata':
        """Create metadata from OpenAPI info section."""
        return cls(
            title=info.get("title"),
            description=info.get("description"),
            version=info.get("version"),
            contact=info.get("contact"),
            license=info.get("license"),
            terms_of_service=info.get("termsOfService")
        )


@dataclass(frozen=True)
class HttpMethod(ValueObject):
    """Value object representing HTTP methods."""

    method: str

    VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

    def __post_init__(self):
        """Validate HTTP method."""
        from .exceptions import ValidationError
        if self.method.upper() not in self.VALID_METHODS:
            raise ValidationError(f"Invalid HTTP method: {self.method}")

    @property
    def is_safe(self) -> bool:
        """Check if method is safe (read-only)."""
        return self.method.upper() in {"GET", "HEAD", "OPTIONS"}

    @property
    def is_idempotent(self) -> bool:
        """Check if method is idempotent."""
        return self.method.upper() in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}


@dataclass(frozen=True)
class ApiPath(ValueObject):
    """Value object representing API paths."""

    path: str

    def __post_init__(self):
        """Validate API path."""
        from .exceptions import ValidationError
        if not self.path.startswith("/"):
            raise ValidationError(f"API path must start with '/': {self.path}")

        # Basic validation - no spaces, proper encoding, etc.
        if " " in self.path:
            raise ValidationError(f"API path cannot contain spaces: {self.path}")

    @property
    def path_segments(self) -> list[str]:
        """Get path segments (split by '/')."""
        return [segment for segment in self.path.split("/") if segment]

    @property
    def has_parameters(self) -> bool:
        """Check if path contains parameters."""
        return "{" in self.path and "}" in self.path
