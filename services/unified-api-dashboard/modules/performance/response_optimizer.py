"""
Response Optimization and Content Delivery System

Features:
- Response compression and optimization
- Content negotiation and format selection
- CDN integration and caching headers
- Progressive response streaming
- Bandwidth adaptation
- Client capability detection
"""

import asyncio
import gzip
import brotli
import json
import time
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompressionConfig:
    """Configuration for response compression."""
    enabled: bool = True
    min_size_bytes: int = 1024
    compression_level: int = 6
    supported_algorithms: List[str] = None

    def __post_init__(self):
        if self.supported_algorithms is None:
            self.supported_algorithms = ["gzip", "br", "deflate"]


@dataclass
class ContentNegotiationResult:
    """Result of content negotiation."""
    content_type: str
    encoding: Optional[str] = None
    language: Optional[str] = None
    charset: str = "utf-8"


@dataclass
class OptimizedResponse:
    """Optimized response data."""
    content: Any
    content_type: str
    headers: Dict[str, str]
    compression_applied: bool = False
    original_size: int = 0
    compressed_size: int = 0
    processing_time: float = 0.0


class CompressionHandler:
    """
    Intelligent response compression handler.

    Features:
    - Multiple compression algorithms (gzip, brotli, deflate)
    - Adaptive compression based on content type and size
    - Client capability detection
    - Compression ratio monitoring
    """

    def __init__(self, config: CompressionConfig = None):
        self.config = config or CompressionConfig()
        self.compression_stats: Dict[str, Dict] = {}

    async def compress_response(self, content: Any, content_type: str,
                              client_accept_encoding: str = "") -> OptimizedResponse:
        """Compress response based on content and client capabilities."""

        start_time = time.time()
        original_size = len(str(content).encode('utf-8'))

        # Skip compression for small responses or if disabled
        if not self.config.enabled or original_size < self.config.min_size_bytes:
            return OptimizedResponse(
                content=content,
                content_type=content_type,
                headers={},
                original_size=original_size,
                processing_time=time.time() - start_time
            )

        # Determine best compression algorithm
        algorithm = self._select_compression_algorithm(client_accept_encoding, content_type)

        if not algorithm:
            return OptimizedResponse(
                content=content,
                content_type=content_type,
                headers={},
                original_size=original_size,
                processing_time=time.time() - start_time
            )

        # Compress content
        compressed_content, compressed_size = await self._compress_content(content, algorithm)

        # Calculate compression ratio
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0

        # Update statistics
        await self._update_stats(algorithm, original_size, compressed_size, compression_ratio)

        headers = {
            "Content-Encoding": algorithm,
            "Vary": "Accept-Encoding"
        }

        # Add cache headers for compressible content
        if compression_ratio < 0.8:  # Good compression ratio
            headers["Cache-Control"] = "public, max-age=3600"

        return OptimizedResponse(
            content=compressed_content,
            content_type=content_type,
            headers=headers,
            compression_applied=True,
            original_size=original_size,
            compressed_size=compressed_size,
            processing_time=time.time() - start_time
        )

    def _select_compression_algorithm(self, accept_encoding: str, content_type: str) -> Optional[str]:
        """Select the best compression algorithm based on client capabilities."""

        # Parse client accept-encoding header
        accepted_encodings = set()
        if accept_encoding:
            for encoding in accept_encoding.split(','):
                encoding = encoding.strip().split(';')[0].lower()
                accepted_encodings.add(encoding)

        # Prioritize algorithms based on compression ratio and client support
        algorithm_priority = []
        if "br" in accepted_encodings and "br" in self.config.supported_algorithms:
            algorithm_priority.append("br")  # Brotli usually best compression
        if "gzip" in accepted_encodings and "gzip" in self.config.supported_algorithms:
            algorithm_priority.append("gzip")  # Widely supported
        if "deflate" in accepted_encodings and "deflate" in self.config.supported_algorithms:
            algorithm_priority.append("deflate")  # Fallback

        return algorithm_priority[0] if algorithm_priority else None

    async def _compress_content(self, content: Any, algorithm: str) -> tuple:
        """Compress content using specified algorithm."""

        # Serialize content if needed
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, separators=(',', ':'))
        else:
            content_str = str(content)

        content_bytes = content_str.encode('utf-8')

        # Compress based on algorithm
        if algorithm == "gzip":
            compressed = gzip.compress(content_bytes, compresslevel=self.config.compression_level)
        elif algorithm == "br":
            compressed = brotli.compress(content_bytes, quality=self.config.compression_level)
        elif algorithm == "deflate":
            import zlib
            compressed = zlib.compress(content_bytes, level=self.config.compression_level)
        else:
            compressed = content_bytes

        return compressed, len(compressed)

    async def _update_stats(self, algorithm: str, original_size: int,
                          compressed_size: int, ratio: float):
        """Update compression statistics."""
        if algorithm not in self.compression_stats:
            self.compression_stats[algorithm] = {
                "total_requests": 0,
                "total_original_bytes": 0,
                "total_compressed_bytes": 0,
                "average_ratio": 0.0,
                "compression_savings_percent": 0.0
            }

        stats = self.compression_stats[algorithm]
        stats["total_requests"] += 1
        stats["total_original_bytes"] += original_size
        stats["total_compressed_bytes"] += compressed_size

        # Update averages
        total_requests = stats["total_requests"]
        stats["average_ratio"] = ((stats["average_ratio"] * (total_requests - 1)) + ratio) / total_requests
        stats["compression_savings_percent"] = (1 - stats["average_ratio"]) * 100

    async def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression performance statistics."""
        return {
            "algorithms": self.compression_stats,
            "config": self.config.__dict__,
            "total_compression_savings": sum(
                stats["compression_savings_percent"] for stats in self.compression_stats.values()
            ) / len(self.compression_stats) if self.compression_stats else 0
        }


class ContentNegotiator:
    """
    HTTP Content Negotiation handler.

    Features:
    - Content-Type negotiation
    - Accept-Language handling
    - Character encoding negotiation
    - Quality value processing
    """

    def __init__(self):
        self.supported_content_types = {
            "application/json": ["json"],
            "application/xml": ["xml"],
            "text/html": ["html"],
            "text/plain": ["txt"],
            "application/yaml": ["yaml", "yml"],
            "application/msgpack": ["msgpack"]
        }

        self.supported_languages = ["en", "es", "fr", "de", "zh", "ja"]
        self.supported_charsets = ["utf-8", "iso-8859-1"]

    async def negotiate(self, accept_header: str = "",
                       accept_language: str = "",
                       accept_charset: str = "") -> ContentNegotiationResult:
        """Perform content negotiation based on Accept headers."""

        # Content-Type negotiation
        content_type = self._negotiate_content_type(accept_header)

        # Language negotiation
        language = self._negotiate_language(accept_language)

        # Charset negotiation
        charset = self._negotiate_charset(accept_charset)

        return ContentNegotiationResult(
            content_type=content_type,
            language=language,
            charset=charset
        )

    def _negotiate_content_type(self, accept_header: str) -> str:
        """Negotiate content type based on Accept header."""
        if not accept_header:
            return "application/json"

        # Parse accept header with quality values
        accept_types = []
        for item in accept_header.split(','):
            parts = item.strip().split(';')
            media_type = parts[0].strip()
            quality = 1.0

            if len(parts) > 1 and parts[1].startswith('q='):
                try:
                    quality = float(parts[1][2:])
                except ValueError:
                    quality = 1.0

            accept_types.append((media_type, quality))

        # Sort by quality value (highest first)
        accept_types.sort(key=lambda x: x[1], reverse=True)

        # Find best match
        for media_type, _ in accept_types:
            if media_type in self.supported_content_types:
                return media_type
            if media_type == "*/*":
                return "application/json"
            if media_type.endswith("/*"):
                # Check for type/*
                main_type = media_type.split('/')[0]
                for supported_type in self.supported_content_types:
                    if supported_type.startswith(f"{main_type}/"):
                        return supported_type

        return "application/json"

    def _negotiate_language(self, accept_language: str) -> Optional[str]:
        """Negotiate language based on Accept-Language header."""
        if not accept_language:
            return None

        languages = []
        for item in accept_language.split(','):
            parts = item.strip().split(';')
            lang = parts[0].strip().split('-')[0]  # Get primary language tag
            quality = 1.0

            if len(parts) > 1 and parts[1].startswith('q='):
                try:
                    quality = float(parts[1][2:])
                except ValueError:
                    quality = 1.0

            languages.append((lang, quality))

        # Sort by quality and find best match
        languages.sort(key=lambda x: x[1], reverse=True)

        for lang, _ in languages:
            if lang in self.supported_languages:
                return lang

        return None

    def _negotiate_charset(self, accept_charset: str) -> str:
        """Negotiate character encoding."""
        if not accept_charset:
            return "utf-8"

        charsets = []
        for item in accept_charset.split(','):
            parts = item.strip().split(';')
            charset = parts[0].strip().lower()
            quality = 1.0

            if len(parts) > 1 and parts[1].startswith('q='):
                try:
                    quality = float(parts[1][2:])
                except ValueError:
                    quality = 1.0

            charsets.append((charset, quality))

        # Sort by quality and find best match
        charsets.sort(key=lambda x: x[1], reverse=True)

        for charset, _ in charsets:
            if charset in self.supported_charsets:
                return charset
            if charset == "*":
                return "utf-8"

        return "utf-8"


class ResponseOptimizer:
    """
    Comprehensive response optimization system.

    Features:
    - Content compression
    - Content negotiation
    - Caching headers optimization
    - Response streaming
    - Bandwidth adaptation
    """

    def __init__(self, compression_config: CompressionConfig = None):
        self.compression_handler = CompressionHandler(compression_config)
        self.content_negotiator = ContentNegotiator()
        self.response_cache: Dict[str, OptimizedResponse] = {}
        self.cache_ttl = 300  # 5 minutes

    async def optimize_response(self, content: Any, request_headers: Dict[str, str],
                              content_type: str = "application/json") -> OptimizedResponse:
        """Optimize response based on content and request headers."""

        start_time = time.time()

        # Perform content negotiation
        negotiation_result = await self.content_negotiator.negotiate(
            accept_header=request_headers.get("accept", ""),
            accept_language=request_headers.get("accept-language", ""),
            accept_charset=request_headers.get("accept-charset", "")
        )

        # Use negotiated content type
        final_content_type = f"{negotiation_result.content_type}; charset={negotiation_result.charset}"

        # Add language header if negotiated
        headers = {}
        if negotiation_result.language:
            headers["Content-Language"] = negotiation_result.language

        # Compress response
        compressed_response = await self.compression_handler.compress_response(
            content=content,
            content_type=final_content_type,
            client_accept_encoding=request_headers.get("accept-encoding", "")
        )

        # Add negotiated headers
        headers.update(compressed_response.headers)

        # Add cache headers for GET requests
        if request_headers.get("method", "").upper() == "GET":
            headers.update(self._get_cache_headers(content_type, compressed_response.compression_applied))

        # Add security headers
        headers.update(self._get_security_headers())

        # Calculate total processing time
        total_time = time.time() - start_time

        return OptimizedResponse(
            content=compressed_response.content,
            content_type=final_content_type,
            headers=headers,
            compression_applied=compressed_response.compression_applied,
            original_size=compressed_response.original_size,
            compressed_size=compressed_response.compressed_size,
            processing_time=total_time
        )

    async def stream_response(self, data_generator: AsyncGenerator,
                            request_headers: Dict[str, str]) -> AsyncGenerator[bytes, None]:
        """Stream optimized response chunks."""

        # Get compression settings
        accept_encoding = request_headers.get("accept-encoding", "")
        algorithm = self.compression_handler._select_compression_algorithm(accept_encoding, "application/json")

        headers_sent = False

        async for chunk in data_generator:
            if not headers_sent:
                # Send headers first
                headers = {}
                if algorithm:
                    headers["Content-Encoding"] = algorithm

                headers.update(self._get_security_headers())
                # Headers would be sent here in a real implementation
                headers_sent = True

            # Compress chunk if needed
            if algorithm:
                chunk = await self.compression_handler._compress_content(chunk, algorithm)
                if isinstance(chunk, tuple):
                    chunk = chunk[0]

            yield chunk

    def _get_cache_headers(self, content_type: str, compressed: bool) -> Dict[str, str]:
        """Generate appropriate cache headers."""
        headers = {}

        # Cache static content longer
        if any(static_type in content_type for static_type in ["text/css", "application/javascript", "image/"]):
            headers["Cache-Control"] = "public, max-age=31536000, immutable"  # 1 year
            headers["ETag"] = f'"{hash(content_type + str(time.time()))}"'
        # Cache API responses shorter
        elif "application/json" in content_type:
            cache_time = 300 if compressed else 60  # 5 min if compressed, 1 min otherwise
            headers["Cache-Control"] = f"public, max-age={cache_time}"
            headers["ETag"] = f'"{hash(str(time.time()))}"'
        else:
            headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            headers["Pragma"] = "no-cache"
            headers["Expires"] = "0"

        return headers

    def _get_security_headers(self) -> Dict[str, str]:
        """Generate security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate response optimization performance report."""
        compression_stats = await self.compression_handler.get_compression_stats()

        return {
            "compression_stats": compression_stats,
            "response_cache_size": len(self.response_cache),
            "cache_ttl_seconds": self.cache_ttl,
            "supported_content_types": list(self.content_negotiator.supported_content_types.keys()),
            "supported_languages": self.content_negotiator.supported_languages,
            "supported_charsets": self.content_negotiator.supported_charsets
        }


class ProgressiveResponseHandler:
    """
    Progressive response handling for large datasets.

    Features:
    - Chunked response streaming
    - Client progress indication
    - Bandwidth-adaptive responses
    - Partial response caching
    """

    def __init__(self, optimizer: ResponseOptimizer):
        self.optimizer = optimizer
        self.active_streams: Dict[str, asyncio.Queue] = {}

    async def create_progressive_response(self, request_id: str,
                                        data_generator: AsyncGenerator,
                                        request_headers: Dict[str, str]) -> AsyncGenerator[bytes, None]:
        """Create a progressive response stream."""

        # Create queue for this stream
        queue = asyncio.Queue(maxsize=10)
        self.active_streams[request_id] = queue

        try:
            # Send initial headers
            headers = {
                "Content-Type": "text/plain; charset=utf-8",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }

            # Send headers as first chunk
            header_chunk = json.dumps({"type": "headers", "data": headers}).encode('utf-8')
            yield header_chunk
            yield b"\n"

            chunk_index = 0
            total_size = 0

            async for data_chunk in data_generator:
                # Optimize chunk
                optimized = await self.optimizer.optimize_response(
                    content=data_chunk,
                    request_headers=request_headers,
                    content_type="application/json"
                )

                # Create progressive chunk
                chunk_data = {
                    "type": "data",
                    "chunk_index": chunk_index,
                    "data": optimized.content,
                    "size": optimized.original_size,
                    "compressed": optimized.compression_applied,
                    "processing_time": optimized.processing_time
                }

                # Serialize chunk
                if isinstance(optimized.content, bytes):
                    chunk_json = json.dumps(chunk_data)
                    chunk_bytes = chunk_json.encode('utf-8')
                else:
                    chunk_bytes = json.dumps(chunk_data).encode('utf-8')

                yield chunk_bytes
                yield b"\n"

                chunk_index += 1
                total_size += optimized.original_size

                # Check if client is still connected (queue not full)
                if queue.full():
                    break

            # Send completion chunk
            completion_data = {
                "type": "complete",
                "total_chunks": chunk_index,
                "total_size": total_size,
                "request_id": request_id
            }

            yield json.dumps(completion_data).encode('utf-8')
            yield b"\n"

        finally:
            # Clean up
            if request_id in self.active_streams:
                del self.active_streams[request_id]

    async def cancel_stream(self, request_id: str):
        """Cancel an active stream."""
        if request_id in self.active_streams:
            del self.active_streams[request_id]
