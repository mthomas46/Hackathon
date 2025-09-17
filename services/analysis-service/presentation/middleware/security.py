"""Security middleware for adding security headers and protection."""

import re
from typing import Dict, List, Optional, Set
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...presentation.models.base import ErrorResponse, ErrorCode


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and basic security measures."""

    def __init__(self, app, allowed_origins: Optional[List[str]] = None):
        """Initialize security middleware."""
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]

        # Security headers
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin'
        }

        # Suspicious patterns to block
        self.suspicious_patterns = [
            r'\.\./',  # Directory traversal
            r'<script',  # XSS attempts
            r'union.*select',  # SQL injection attempts
            r'1=1',  # SQL injection attempts
            r'eval\(',  # Code injection attempts
        ]

        # Compile regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with security checks."""
        # Perform security checks
        await self._perform_security_checks(request)

        # Process the request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    async def _perform_security_checks(self, request: Request):
        """Perform security checks on the request."""
        # Check for suspicious patterns in URL
        url_path = str(request.url.path)
        query_string = str(request.query_params)

        for pattern in self.compiled_patterns:
            if pattern.search(url_path) or pattern.search(query_string):
                await self._block_request(request, "Suspicious request pattern detected")

        # Check request size
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > 10 * 1024 * 1024:  # 10MB limit
                    await self._block_request(request, "Request too large")
            except ValueError:
                pass

        # Check user agent
        user_agent = request.headers.get('user-agent', '').lower()
        suspicious_agents = ['sqlmap', 'nmap', 'nikto', 'dirbuster']
        for agent in suspicious_agents:
            if agent in user_agent:
                await self._block_request(request, "Suspicious user agent detected")

        # Rate limiting for suspicious IPs can be added here
        client_ip = self._get_client_ip(request)
        # Could integrate with a reputation service here

    async def _block_request(self, request: Request, reason: str):
        """Block a suspicious request."""
        error_response = ErrorResponse(
            error={
                "field": None,
                "message": "Request blocked for security reasons",
                "code": ErrorCode.FORBIDDEN
            },
            request_id=getattr(request.state, 'request_id', None)
        )

        raise HTTPException(
            status_code=403,
            detail=error_response.dict()
        )

    def _add_security_headers(self, response: Response):
        """Add security headers to the response."""
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Add CSP header if not present
        if 'Content-Security-Policy' not in response.headers:
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        client = request.client
        return client.host if client else "unknown"


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware for cross-origin requests."""

    def __init__(self, app, allow_origins: List[str] = None, allow_credentials: bool = True):
        """Initialize CORS middleware."""
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With"
        ]
        self.max_age = 86400  # 24 hours

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process CORS request."""
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)

        # Get origin
        origin = request.headers.get('origin')

        # Check if origin is allowed
        if origin and self._is_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
        elif self.allow_origins == ["*"]:
            response.headers['Access-Control-Allow-Origin'] = "*"

        # Add other CORS headers
        if self.allow_credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'

        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.allow_methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.allow_headers)
        response.headers['Access-Control-Max-Age'] = str(self.max_age)

        return response

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed list."""
        for allowed in self.allow_origins:
            if allowed == "*" or origin == allowed:
                return True
            # Support for wildcard patterns
            if allowed.startswith("*."):
                domain = allowed[2:]
                if origin.endswith(f".{domain}"):
                    return True
        return False


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request IDs to all requests."""

    def __init__(self, app):
        """Initialize request ID middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add request ID to request state."""
        import uuid

        # Generate request ID if not present
        if not hasattr(request.state, 'request_id'):
            request.state.request_id = str(uuid.uuid4())

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers['X-Request-ID'] = request.state.request_id

        return response


class SanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware for sanitizing request inputs."""

    def __init__(self, app):
        """Initialize sanitization middleware."""
        super().__init__(app)

        # Patterns for sanitization
        self.sql_injection_patterns = [
            r'union.*select',
            r'1=1',
            r'drop table',
            r'--',
            r'/*',
            r'*/'
        ]

        self.xss_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed'
        ]

        # Compile patterns
        self.all_patterns = [
            (re.compile(pattern, re.IGNORECASE), 'sql_injection')
            for pattern in self.sql_injection_patterns
        ] + [
            (re.compile(pattern, re.IGNORECASE), 'xss')
            for pattern in self.xss_patterns
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Sanitize request inputs."""
        # Sanitize query parameters
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if isinstance(value, str):
                sanitized = self._sanitize_input(value)
                if sanitized != value:
                    # Log potential attack attempt
                    print(f"Potential attack detected in query param {key}: {value}")

        # Note: Body sanitization would require reading and potentially modifying the body
        # This is more complex and might not be suitable for all endpoints

        return await call_next(request)

    def _sanitize_input(self, input_str: str) -> str:
        """Sanitize input string."""
        # Basic HTML escaping
        input_str = input_str.replace('&', '&amp;')
        input_str = input_str.replace('<', '&lt;')
        input_str = input_str.replace('>', '&gt;')
        input_str = input_str.replace('"', '&quot;')
        input_str = input_str.replace("'", '&#x27;')

        return input_str

    def _detect_threats(self, input_str: str) -> List[str]:
        """Detect potential threats in input."""
        threats = []
        for pattern, threat_type in self.all_patterns:
            if pattern.search(input_str):
                threats.append(threat_type)
        return threats
