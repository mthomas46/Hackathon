"""Service Endpoint Value Object"""

from typing import Optional


class ServiceEndpoint:
    """Value object representing a service endpoint."""

    def __init__(self, method: str, path: str, description: Optional[str] = None):
        self._method = method.upper().strip()
        self._path = path.strip()
        self._description = description.strip() if description else None

        self._validate()

    def _validate(self):
        """Validate endpoint data."""
        if not self._method:
            raise ValueError("HTTP method cannot be empty")

        if not self._path or not self._path.startswith('/'):
            raise ValueError("Path must be non-empty and start with '/'")

        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if self._method not in valid_methods:
            raise ValueError(f"Invalid HTTP method: {self._method}")

    @property
    def method(self) -> str:
        """Get the HTTP method."""
        return self._method

    @property
    def path(self) -> str:
        """Get the endpoint path."""
        return self._path

    @property
    def description(self) -> Optional[str]:
        """Get the endpoint description."""
        return self._description

    @property
    def full_path(self) -> str:
        """Get the full endpoint path with method."""
        return f"{self._method} {self._path}"

    def __str__(self) -> str:
        return self.full_path

    def __repr__(self) -> str:
        return f"ServiceEndpoint({self._method}, {self._path})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ServiceEndpoint):
            return NotImplemented
        return (self._method == other._method and
                self._path == other._path and
                self._description == other._description)

    def __hash__(self) -> int:
        return hash((self._method, self._path, self._description))
