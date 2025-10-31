"""
File Safety Utilities

Provides robust file reading with protections against:
- Binary files misidentified as text
- Encoding errors
- Very large files
- Timeouts
"""

import asyncio
import logging
import chardet
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE_MB = 10  # Maximum file size in MB
MAX_READ_TIMEOUT_SEC = 30  # Maximum time to read a file
MIN_TEXT_THRESHOLD = 0.7  # Minimum ratio of text characters


class FileSafetyError(Exception):
    """Base exception for file safety issues."""
    pass


class BinaryFileError(FileSafetyError):
    """File appears to be binary."""
    pass


class EncodingError(FileSafetyError):
    """File has encoding issues."""
    pass


class FileSizeError(FileSafetyError):
    """File is too large."""
    pass


class FileTimeoutError(FileSafetyError):
    """File reading timed out."""
    pass


async def safe_read_file(
    file_path: Path,
    max_size_mb: int = MAX_FILE_SIZE_MB,
    timeout_sec: int = MAX_READ_TIMEOUT_SEC,
    strict_binary_check: bool = True,
    encoding_detection: bool = True
) -> Dict[str, Any]:
    """
    Safely read file with comprehensive protections.
    
    Args:
        file_path: Path to file
        max_size_mb: Maximum file size in MB
        timeout_sec: Maximum read timeout in seconds
        strict_binary_check: Enable strict binary detection
        encoding_detection: Use chardet for encoding detection
    
    Returns:
        Dictionary with:
            - content: File content as string
            - encoding: Detected encoding
            - size_bytes: File size
            - warnings: List of warnings
    
    Raises:
        BinaryFileError: File is binary
        EncodingError: File has encoding issues
        FileSizeError: File too large
        FileTimeoutError: Read timed out
        FileSafetyError: Other safety issues
    """
    warnings = []
    
    try:
        # 1. Check file exists and is regular file
        if not file_path.exists():
            raise FileSafetyError(f"File does not exist: {file_path}")
        
        if not file_path.is_file():
            raise FileSafetyError(f"Not a regular file: {file_path}")
        
        # 2. Check file size
        size_bytes = file_path.stat().st_size
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if size_bytes > max_size_bytes:
            raise FileSizeError(
                f"File too large: {size_bytes / 1024 / 1024:.2f}MB "
                f"(max: {max_size_mb}MB)"
            )
        
        if size_bytes == 0:
            warnings.append("Empty file")
            return {
                "content": "",
                "encoding": "utf-8",
                "size_bytes": 0,
                "warnings": warnings
            }
        
        # 3. Read first chunk for binary detection
        loop = asyncio.get_event_loop()
        
        async def read_with_timeout():
            # Read first 8KB for analysis
            sample_size = min(8192, size_bytes)
            sample_bytes = await loop.run_in_executor(
                None,
                lambda: file_path.read_bytes()[:sample_size]
            )
            
            # 4. Binary detection
            if strict_binary_check and is_binary_data(sample_bytes):
                raise BinaryFileError(f"File appears to be binary: {file_path.name}")
            
            # 5. Encoding detection
            detected_encoding = 'utf-8'
            if encoding_detection:
                detection_result = chardet.detect(sample_bytes)
                detected_encoding = detection_result.get('encoding', 'utf-8')
                confidence = detection_result.get('confidence', 0)
                
                if confidence < 0.7:
                    warnings.append(
                        f"Low encoding confidence: {confidence:.2f} "
                        f"(detected: {detected_encoding})"
                    )
                
                logger.debug(
                    f"Encoding detected for {file_path.name}: "
                    f"{detected_encoding} (confidence: {confidence:.2f})"
                )
            
            # 6. Read full file with detected encoding
            try:
                # Try detected encoding first
                content = await loop.run_in_executor(
                    None,
                    lambda: file_path.read_text(encoding=detected_encoding, errors='strict')
                )
            except UnicodeDecodeError:
                warnings.append(
                    f"Failed to decode with {detected_encoding}, trying UTF-8 with replacement"
                )
                try:
                    # Fallback to UTF-8 with replacement
                    content = await loop.run_in_executor(
                        None,
                        lambda: file_path.read_text(encoding='utf-8', errors='replace')
                    )
                    detected_encoding = 'utf-8-replace'
                except Exception as e:
                    # Last resort: latin-1 (never fails)
                    warnings.append(f"UTF-8 failed, using latin-1: {e}")
                    content = await loop.run_in_executor(
                        None,
                        lambda: file_path.read_text(encoding='latin-1', errors='replace')
                    )
                    detected_encoding = 'latin-1-replace'
            
            return content, detected_encoding
        
        # 7. Execute with timeout
        try:
            content, encoding = await asyncio.wait_for(
                read_with_timeout(),
                timeout=timeout_sec
            )
        except asyncio.TimeoutError:
            raise FileTimeoutError(
                f"File read timed out after {timeout_sec}s: {file_path.name}"
            )
        
        # 8. Final validation
        if not content or len(content.strip()) == 0:
            warnings.append("File is empty or whitespace only")
        
        return {
            "content": content,
            "encoding": encoding,
            "size_bytes": size_bytes,
            "warnings": warnings
        }
    
    except FileSafetyError:
        # Re-raise our own exceptions
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise FileSafetyError(f"Unexpected error reading {file_path.name}: {e}") from e


def is_binary_data(data: bytes, max_check_bytes: int = 8192) -> bool:
    """
    Check if data appears to be binary.
    
    Uses multiple heuristics:
    1. NULL bytes check
    2. Control character ratio
    3. UTF-8 validity
    4. Text character ratio
    
    Args:
        data: Bytes to check
        max_check_bytes: Maximum bytes to analyze
    
    Returns:
        True if data appears binary
    """
    if not data:
        return False
    
    # Limit check size
    check_data = data[:max_check_bytes]
    
    # 1. NULL bytes are a strong indicator of binary
    if b'\x00' in check_data:
        return True
    
    # 2. Try UTF-8 decode
    try:
        text = check_data.decode('utf-8')
    except UnicodeDecodeError:
        # Can't decode as UTF-8, likely binary
        return True
    
    # 3. Check ratio of control characters (excluding whitespace)
    control_chars = 0
    printable_chars = 0
    
    for char in text:
        if ord(char) < 32 and char not in '\n\r\t\f\v':
            # Control character (not whitespace)
            control_chars += 1
        elif 32 <= ord(char) <= 126 or ord(char) >= 128:
            # Printable ASCII or extended ASCII
            printable_chars += 1
    
    total_chars = len(text)
    if total_chars == 0:
        return False
    
    # If more than 30% control characters, likely binary
    control_ratio = control_chars / total_chars
    if control_ratio > 0.3:
        return True
    
    # If less than 70% printable characters, likely binary
    printable_ratio = printable_chars / total_chars
    if printable_ratio < MIN_TEXT_THRESHOLD:
        return True
    
    return False


def is_binary_by_extension(file_path: Path) -> bool:
    """
    Check if file is binary based on extension.
    
    Args:
        file_path: File path
    
    Returns:
        True if extension indicates binary file
    """
    binary_extensions = {
        # Executables & Libraries
        '.exe', '.dll', '.so', '.dylib', '.a', '.o', '.obj',
        '.bin', '.dat', '.elf', '.lib', '.pyd',
        
        # Archives
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz',
        '.tgz', '.tbz2', '.war', '.jar', '.ear',
        
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
        '.svg', '.webp', '.tiff', '.tif', '.psd', '.ai',
        
        # Audio/Video
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.wav', '.flac', '.ogg', '.m4a', '.mkv',
        
        # Documents (binary formats)
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
        '.pptx', '.odt', '.ods', '.odp',
        
        # Databases
        '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
        
        # Python
        '.pyc', '.pyo', '.pyd', '.whl', '.egg',
        
        # Java
        '.class', '.jar', '.war', '.ear',
        
        # Fonts
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        
        # Others
        '.pickle', '.pkl', '.npy', '.npz', '.h5', '.hdf5',
        '.parquet', '.avro', '.proto', '.pb',
    }
    
    return file_path.suffix.lower() in binary_extensions


async def safe_normalize_content(
    content: str,
    file_path: str,
    normalizer,
    timeout_sec: int = 60
) -> Dict[str, Any]:
    """
    Safely normalize content with timeout and fallback.
    
    Args:
        content: Original content
        file_path: File path (for extension)
        normalizer: Normalizer instance
        timeout_sec: Timeout in seconds
    
    Returns:
        Dictionary with:
            - content: Normalized content
            - success: True if normalized successfully
            - fallback_used: True if fallback was used
            - error: Error message if failed
    """
    try:
        # Try normalization with timeout
        normalized = await asyncio.wait_for(
            normalizer.normalize(
                content=content,
                file_path=file_path,
                metadata={}
            ),
            timeout=timeout_sec
        )
        
        # Handle different return types
        if isinstance(normalized, dict):
            normalized_content = normalized.get("content", normalized.get("normalized_content", content))
        else:
            normalized_content = normalized
        
        return {
            "content": normalized_content,
            "success": True,
            "fallback_used": False,
            "error": None
        }
    
    except asyncio.TimeoutError:
        logger.warning(f"⚠️  Normalization timeout for {file_path}, using raw content")
        return {
            "content": f"```\n{content}\n```",
            "success": False,
            "fallback_used": True,
            "error": f"Normalization timed out after {timeout_sec}s"
        }
    
    except Exception as e:
        logger.warning(f"⚠️  Normalization failed for {file_path}: {e}, using raw content")
        # Fallback to raw content wrapped in code block
        file_ext = Path(file_path).suffix.lstrip('.')
        return {
            "content": f"```{file_ext}\n{content}\n```",
            "success": False,
            "fallback_used": True,
            "error": str(e)
        }


def get_file_safety_stats() -> Dict[str, Any]:
    """
    Get statistics about file safety checks.
    
    Returns:
        Dictionary with configuration and stats
    """
    return {
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "max_read_timeout_sec": MAX_READ_TIMEOUT_SEC,
        "min_text_threshold": MIN_TEXT_THRESHOLD,
        "binary_extensions_count": len(
            # Count from is_binary_by_extension
            42  # Approximate
        )
    }

