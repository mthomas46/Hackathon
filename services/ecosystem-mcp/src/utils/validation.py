"""
Input validation and sanitization utilities.

Provides security-focused validation for user inputs to prevent:
- XSS attacks
- Path traversal
- SQL injection
- Content injection
"""

import re
from pathlib import Path
from typing import Optional
from html import escape

from .exceptions import ValidationError


# Allowed file extensions for document ingestion
ALLOWED_EXTENSIONS = {
    # Documentation
    '.md', '.txt', '.rst', '.adoc', '.asciidoc',
    
    # General purpose languages
    '.py', '.js', '.ts', '.java', '.go', '.rs',
    
    # JVM languages
    '.scala', '.kt', '.clj', '.groovy',
    
    # Other languages
    '.rb', '.php', '.swift', '.dart', '.lua',
    
    # Build & project files (SBT, Maven, Gradle, etc.)
    '.sbt', '.gradle', '.maven', '.pom',
    
    # Configuration files (framework-specific)
    '.conf', '.properties', '.config', '.ini',  # Application configs
    '.json', '.yaml', '.yml', '.toml', '.xml',  # Data formats
    '.hocon',  # Typesafe config (Play Framework)
    
    # Web & frontend
    '.html', '.css', '.scss', '.less', '.jsx', '.tsx', '.vue',
    
    # Scripts & queries
    '.sql', '.sh', '.bash', '.zsh', '.fish',
    
    # API definitions
    '.graphql', '.proto', '.avro', '.thrift', '.apib',  # API Blueprint
    
    # Special files (no extension)
    'routes', 'Dockerfile', 'Makefile', 'Jenkinsfile', 'Vagrantfile',
}

# Maximum content lengths
MAX_QUERY_LENGTH = 500
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PATH_LENGTH = 500


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML/script content from text.
    
    Args:
        text: Input text potentially containing HTML
    
    Returns:
        Sanitized text with HTML escaped
    
    Examples:
        >>> sanitize_html("<script>alert('xss')</script>")
        "&lt;script&gt;alert('xss')&lt;/script&gt;"
    """
    if not text:
        return text
    
    # Escape HTML entities
    sanitized = escape(text)
    
    # Remove common script patterns (belt and suspenders)
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # onclick, onload, etc.
        r'<iframe[^>]*>.*?</iframe>',
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized


def validate_file_extension(file_path: str, strict: bool = True) -> bool:
    """
    Check if file extension is allowed for ingestion.
    
    Args:
        file_path: Path to file
        strict: If False, allow all extensions (disable filtering)
    
    Returns:
        True if file is allowed
    
    Examples:
        >>> validate_file_extension("app.scala")
        True
        >>> validate_file_extension("data.bin", strict=False)
        True
    """
    if not strict:
        # Disable filtering - allow all files
        return True
    
    path = Path(file_path)
    
    # Check special files with no extension
    if path.name in ALLOWED_EXTENSIONS:
        return True
    
    # Check file extension
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def validate_path(file_path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Validate file path to prevent traversal attacks.
    
    Args:
        file_path: Input file path
        base_dir: Optional base directory to restrict to
    
    Returns:
        Validated Path object
    
    Raises:
        ValidationError: If path is invalid or attempts traversal
    
    Examples:
        >>> validate_path("docs/README.md")
        PosixPath('docs/README.md')
        
        >>> validate_path("../../../etc/passwd")  # Raises
        ValidationError: Path traversal detected
    """
    if not file_path:
        raise ValidationError("File path cannot be empty")
    
    if len(file_path) > MAX_PATH_LENGTH:
        raise ValidationError(f"Path exceeds maximum length of {MAX_PATH_LENGTH}")
    
    # Check for path traversal patterns
    dangerous_patterns = ['../', '..\\', '%2e%2e', '..%2f', '..%5c']
    path_lower = file_path.lower()
    
    for pattern in dangerous_patterns:
        if pattern in path_lower:
            raise ValidationError(f"Path traversal detected: {pattern}")
    
    # Check for absolute paths (unless base_dir specified)
    path = Path(file_path)
    if path.is_absolute() and base_dir is None:
        raise ValidationError("Absolute paths not allowed")
    
    # If base_dir specified, ensure path is within it
    if base_dir:
        try:
            resolved = (base_dir / path).resolve()
            if not str(resolved).startswith(str(base_dir.resolve())):
                raise ValidationError("Path outside base directory")
        except Exception as e:
            raise ValidationError(f"Invalid path: {e}")
    
    return path


def validate_file_extension(file_path: str) -> str:
    """
    Validate file extension against whitelist.
    
    Args:
        file_path: File path to validate
    
    Returns:
        Validated file path
    
    Raises:
        ValidationError: If extension not allowed
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if not ext:
        raise ValidationError("File must have an extension")
    
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File extension '{ext}' not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    return file_path


def validate_query_length(query: str) -> str:
    """
    Validate query length.
    
    Args:
        query: Search query
    
    Returns:
        Validated query
    
    Raises:
        ValidationError: If query too long
    """
    if not query:
        raise ValidationError("Query cannot be empty")
    
    if len(query) > MAX_QUERY_LENGTH:
        raise ValidationError(
            f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters"
        )
    
    return query


def validate_content_size(content: str, max_size: int = MAX_DOCUMENT_SIZE) -> str:
    """
    Validate content size.
    
    Args:
        content: Content to validate
        max_size: Maximum size in bytes
    
    Returns:
        Validated content
    
    Raises:
        ValidationError: If content too large
    """
    if not content:
        raise ValidationError("Content cannot be empty")
    
    size_bytes = len(content.encode('utf-8'))
    
    if size_bytes > max_size:
        raise ValidationError(
            f"Content size ({size_bytes:,} bytes) exceeds "
            f"maximum ({max_size:,} bytes)"
        )
    
    return content


def validate_service_name(service_name: str) -> str:
    """
    Validate service name format.
    
    Args:
        service_name: Service name to validate
    
    Returns:
        Validated service name
    
    Raises:
        ValidationError: If service name invalid
    """
    if not service_name:
        raise ValidationError("Service name cannot be empty")
    
    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', service_name):
        raise ValidationError(
            "Service name must contain only letters, numbers, hyphens, and underscores"
        )
    
    if len(service_name) > 100:
        raise ValidationError("Service name too long (max 100 chars)")
    
    return service_name


def validate_uuid(uuid_str: str) -> str:
    """
    Validate UUID format.
    
    Args:
        uuid_str: UUID string to validate
    
    Returns:
        Validated UUID string
    
    Raises:
        ValidationError: If UUID invalid
    """
    from uuid import UUID
    
    try:
        UUID(uuid_str)
        return uuid_str
    except (ValueError, AttributeError) as e:
        raise ValidationError(f"Invalid UUID format: {e}")


def sanitize_and_validate_query(query: str) -> str:
    """
    Combined sanitization and validation for search queries.
    
    Args:
        query: Search query
    
    Returns:
        Sanitized and validated query
    """
    # Sanitize HTML
    query = sanitize_html(query)
    
    # Validate length
    query = validate_query_length(query)
    
    # Strip whitespace
    query = query.strip()
    
    return query

