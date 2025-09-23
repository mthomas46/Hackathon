"""
CDN Integration and Static Asset Optimization

Features:
- CDN integration for static assets
- Asset optimization and minification
- Cache invalidation strategies
- Geographic distribution
- Performance monitoring
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CDNConfig:
    """CDN configuration settings."""

    provider: str = "cloudflare"  # cloudflare, cloudfront, fastly, akamai
    base_url: str = ""
    api_token: str = ""
    zone_id: str = ""
    enabled: bool = True
    cache_ttl: int = 86400  # 24 hours
    purge_on_deploy: bool = True


@dataclass
class AssetMetadata:
    """Metadata for static assets."""

    path: str
    content_hash: str
    size_bytes: int
    content_type: str
    last_modified: datetime
    cache_control: str
    etag: str


class CDNManager:
    """
    CDN management and optimization system.

    Features:
    - Multi-provider CDN support
    - Asset uploading and management
    - Cache purging and invalidation
    - Performance monitoring
    - Geographic distribution optimization
    """

    def __init__(self, config: CDNConfig):
        self.config = config
        self.assets: Dict[str, AssetMetadata] = {}
        self.performance_metrics: Dict[str, Any] = {}

    async def upload_asset(
        self, local_path: str, remote_path: str, content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload asset to CDN."""

        try:
            # Read file content
            with open(local_path, "rb") as f:
                content = f.read()

            # Calculate metadata
            content_hash = hashlib.sha256(content).hexdigest()
            etag = f'"{content_hash}"'

            metadata = AssetMetadata(
                path=remote_path,
                content_hash=content_hash,
                size_bytes=len(content),
                content_type=content_type,
                last_modified=datetime.now(),
                cache_control=f"public, max-age={self.config.cache_ttl}, immutable",
                etag=etag,
            )

            # Upload based on provider
            success = await self._upload_to_provider(content, metadata)

            if success:
                self.assets[remote_path] = metadata
                logger.info(f"Uploaded asset: {remote_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to upload asset {remote_path}: {e}")
            return False

        return False

    async def get_asset_url(self, path: str, with_version: bool = True) -> str:
        """Get CDN URL for asset."""

        if not self.config.enabled:
            return f"/static/{path}"

        base_url = self.config.base_url.rstrip("/")

        if with_version and path in self.assets:
            metadata = self.assets[path]
            versioned_path = f"{path}?v={metadata.content_hash[:8]}"
            return f"{base_url}/{versioned_path}"

        return f"{base_url}/{path}"

    async def purge_cache(self, paths: List[str] = None) -> bool:
        """Purge CDN cache for specified paths."""

        if not self.config.enabled:
            return True

        try:
            if paths is None:
                # Purge all
                success = await self._purge_all_cache()
            else:
                # Purge specific paths
                success = await self._purge_cache_paths(paths)

            if success:
                logger.info(f"CDN cache purged for paths: {paths or ['all']}")
                return True

        except Exception as e:
            logger.error(f"Failed to purge CDN cache: {e}")
            return False

        return False

    async def optimize_asset(self, content: bytes, content_type: str) -> bytes:
        """Optimize asset content."""

        # Minification based on content type
        if content_type == "application/javascript":
            return await self._minify_javascript(content)
        elif content_type == "text/css":
            return await self._minify_css(content)
        elif content_type.startswith("image/"):
            return await self._optimize_image(content, content_type)
        else:
            return content

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get CDN performance metrics."""

        return {
            "provider": self.config.provider,
            "enabled": self.config.enabled,
            "assets_count": len(self.assets),
            "total_size_bytes": sum(meta.size_bytes for meta in self.assets.values()),
            "performance_metrics": self.performance_metrics,
            "cache_ttl_seconds": self.config.cache_ttl,
        }

    async def _upload_to_provider(self, content: bytes, metadata: AssetMetadata) -> bool:
        """Upload to specific CDN provider."""

        if self.config.provider == "cloudflare":
            return await self._upload_cloudflare(content, metadata)
        elif self.config.provider == "cloudfront":
            return await self._upload_cloudfront(content, metadata)
        else:
            logger.warning(f"Unsupported CDN provider: {self.config.provider}")
            return False

    async def _upload_cloudflare(self, content: bytes, metadata: AssetMetadata) -> bool:
        """Upload to Cloudflare R2 or Pages."""
        # Implementation would use Cloudflare API
        # This is a placeholder
        logger.info(f"Would upload {metadata.path} to Cloudflare")
        return True

    async def _upload_cloudfront(self, content: bytes, metadata: AssetMetadata) -> bool:
        """Upload to AWS CloudFront."""
        # Implementation would use AWS SDK
        logger.info(f"Would upload {metadata.path} to CloudFront")
        return True

    async def _purge_all_cache(self) -> bool:
        """Purge entire CDN cache."""
        if self.config.provider == "cloudflare":
            # Cloudflare API call to purge everything
            return True
        return False

    async def _purge_cache_paths(self, paths: List[str]) -> bool:
        """Purge specific paths from CDN cache."""
        if self.config.provider == "cloudflare":
            # Cloudflare API call to purge specific files
            return True
        return False

    async def _minify_javascript(self, content: bytes) -> bytes:
        """Minify JavaScript content."""
        # This would use a JS minifier like terser
        # Placeholder implementation
        return content

    async def _minify_css(self, content: bytes) -> bytes:
        """Minify CSS content."""
        # This would use a CSS minifier
        # Placeholder implementation
        return content

    async def _optimize_image(self, content: bytes, content_type: str) -> bytes:
        """Optimize image content."""
        # This would use image optimization libraries
        # Placeholder implementation
        return content


class AssetOptimizer:
    """
    Static asset optimization system.

    Features:
    - Bundle optimization
    - Code splitting
    - Tree shaking
    - Asset fingerprinting
    - Critical CSS extraction
    """

    def __init__(self, cdn_manager: CDNManager):
        self.cdn_manager = cdn_manager
        self.asset_bundles: Dict[str, List[str]] = {}
        self.optimization_stats: Dict[str, Any] = {}

    async def create_asset_bundle(
        self, bundle_name: str, asset_paths: List[str], bundle_type: str = "javascript"
    ) -> str:
        """Create optimized asset bundle."""

        start_time = time.time()

        # Read all assets
        bundle_content = b""
        total_original_size = 0

        for path in asset_paths:
            try:
                with open(path, "rb") as f:
                    content = f.read()
                    total_original_size += len(content)

                    # Optimize individual asset
                    content_type = self._get_content_type(path)
                    optimized = await self.cdn_manager.optimize_asset(content, content_type)

                    bundle_content += optimized + b"\n"
            except Exception as e:
                logger.error(f"Failed to read asset {path}: {e}")
                continue

        # Create bundle filename with hash
        bundle_hash = hashlib.sha256(bundle_content).hexdigest()[:12]
        bundle_filename = f"{bundle_name}.{bundle_hash}.{'js' if bundle_type == 'javascript' else 'css'}"

        # Save bundle locally (would be uploaded to CDN in production)
        bundle_path = f"/tmp/{bundle_filename}"
        with open(bundle_path, "wb") as f:
            f.write(bundle_content)

        # Upload to CDN
        remote_path = f"bundles/{bundle_filename}"
        success = await self.cdn_manager.upload_asset(bundle_path, remote_path, f"application/{bundle_type}")

        if success:
            # Record bundle metadata
            processing_time = time.time() - start_time
            compression_ratio = len(bundle_content) / total_original_size if total_original_size > 0 else 1

            self.asset_bundles[bundle_name] = asset_paths
            self.optimization_stats[bundle_name] = {
                "original_size": total_original_size,
                "optimized_size": len(bundle_content),
                "compression_ratio": compression_ratio,
                "processing_time": processing_time,
                "assets_count": len(asset_paths),
            }

            cdn_url = await self.cdn_manager.get_asset_url(remote_path)
            logger.info(f"Created asset bundle: {bundle_name} -> {cdn_url}")

            return cdn_url

        return ""

    async def extract_critical_css(self, html_content: str, css_files: List[str]) -> tuple[str, str]:
        """Extract critical CSS for above-the-fold content."""

        # This would analyze HTML and extract critical CSS
        # Placeholder implementation
        critical_css = "/* Critical CSS would be extracted here */"
        remaining_css_files = css_files  # Would filter out critical parts

        return critical_css, remaining_css_files

    async def optimize_html(self, html_content: str) -> str:
        """Optimize HTML content."""

        # Minify HTML, inline critical CSS, defer non-critical JS, etc.
        # Placeholder implementation
        return html_content

    async def get_optimization_report(self) -> Dict[str, Any]:
        """Generate asset optimization report."""

        total_original = sum(stats["original_size"] for stats in self.optimization_stats.values())
        total_optimized = sum(stats["optimized_size"] for stats in self.optimization_stats.values())
        avg_compression = total_optimized / total_original if total_original > 0 else 1

        return {
            "bundles_count": len(self.asset_bundles),
            "total_original_size": total_original,
            "total_optimized_size": total_optimized,
            "average_compression_ratio": avg_compression,
            "space_saved_bytes": total_original - total_optimized,
            "space_saved_percent": (1 - avg_compression) * 100,
            "bundle_details": self.optimization_stats,
        }

    def _get_content_type(self, path: str) -> str:
        """Determine content type from file path."""

        if path.endswith(".js"):
            return "application/javascript"
        elif path.endswith(".css"):
            return "text/css"
        elif path.endswith(".png"):
            return "image/png"
        elif path.endswith(".jpg") or path.endswith(".jpeg"):
            return "image/jpeg"
        elif path.endswith(".svg"):
            return "image/svg+xml"
        else:
            return "application/octet-stream"
