"""Graceful Shutdown Service with connection draining, cleanup hooks, and resource management.

Provides comprehensive shutdown procedures that ensure:
- Connection draining (finish active requests)
- Resource cleanup and state persistence
- Proper signal handling
- Timeout-based forced shutdown
- Lifecycle management
"""

import asyncio
import atexit
import logging
import signal
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Shutdown phases for orderly shutdown."""

    NORMAL = "normal"  # Graceful shutdown
    FAST = "fast"  # Quick shutdown (less graceful)
    FORCE = "force"  # Immediate shutdown


@dataclass
class ShutdownHook:
    """A shutdown hook with priority and timeout."""

    name: str
    callback: Callable[[], Awaitable[None]]
    priority: int = 100  # Lower numbers execute first
    timeout: float = 10.0  # seconds
    required: bool = True  # If True, failure blocks shutdown


@dataclass
class ShutdownMetrics:
    """Metrics for shutdown process."""

    start_time: float = field(default_factory=time.time)
    phase_start_time: float = field(default_factory=time.time)
    total_duration: float = 0.0
    hooks_executed: int = 0
    hooks_failed: int = 0
    connections_drained: int = 0
    resources_cleaned: int = 0
    phase: ShutdownPhase = ShutdownPhase.NORMAL


class ConnectionDrainer:
    """Manages connection draining during shutdown."""

    def __init__(self, max_drain_time: float = 30.0):
        self.max_drain_time = max_drain_time
        self._active_connections = 0
        self._drain_event = asyncio.Event()
        self._lock = threading.Lock()

    def register_connection(self) -> None:
        """Register a new active connection."""
        with self._lock:
            self._active_connections += 1

    def unregister_connection(self) -> None:
        """Unregister a completed connection."""
        with self._lock:
            self._active_connections = max(0, self._active_connections - 1)
            if self._active_connections == 0:
                self._drain_event.set()

    async def wait_for_drain(self) -> bool:
        """Wait for all connections to drain or timeout."""
        try:
            await asyncio.wait_for(self._drain_event.wait(), timeout=self.max_drain_time)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Connection drain timed out after {self.max_drain_time}s")
            return False

    @property
    def active_connections(self) -> int:
        """Get count of active connections."""
        with self._lock:
            return self._active_connections


class GracefulShutdownService:
    """Centralized service for managing graceful shutdown procedures."""

    def __init__(self):
        self._hooks: List[ShutdownHook] = []
        self._connection_drainer = ConnectionDrainer()
        self._shutdown_event = asyncio.Event()
        self._shutdown_started = False
        self._metrics = ShutdownMetrics()
        self._cleanup_functions: List[Callable[[], None]] = []
        self._lock = threading.Lock()

        # Register signal handlers
        self._setup_signal_handlers()

        # Register atexit handler
        atexit.register(self._atexit_handler)

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            # Handle common termination signals
            for sig in [signal.SIGTERM, signal.SIGINT]:
                signal.signal(sig, self._signal_handler)

            # Handle SIGHUP for reload (graceful restart)
            signal.signal(signal.SIGHUP, self._reload_handler)

        except (OSError, ValueError) as e:
            logger.warning(f"Could not setup signal handlers: {e}")

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        logger.info(f"Received shutdown signal: {signal_name}")

        # Determine shutdown phase based on signal
        if signum == signal.SIGTERM:
            phase = ShutdownPhase.NORMAL
        elif signum == signal.SIGINT:
            phase = ShutdownPhase.FAST
        else:
            phase = ShutdownPhase.FORCE

        # Start shutdown in background thread to avoid blocking signal handler
        threading.Thread(target=self._start_shutdown_sync, args=(phase,), daemon=True).start()

    def _reload_handler(self, signum, frame) -> None:
        """Handle reload signals."""
        logger.info("Received reload signal, triggering graceful restart")
        # For now, treat as normal shutdown
        threading.Thread(target=self._start_shutdown_sync, args=(ShutdownPhase.NORMAL,), daemon=True).start()

    def _atexit_handler(self) -> None:
        """Handle process exit."""
        if not self._shutdown_started:
            logger.warning("Process exiting without graceful shutdown")
            self._force_shutdown()

    def _start_shutdown_sync(self, phase: ShutdownPhase) -> None:
        """Start shutdown process synchronously."""
        try:
            # Create event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run shutdown
            loop.run_until_complete(self.initiate_shutdown(phase))
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self._force_shutdown()

    async def initiate_shutdown(self, phase: ShutdownPhase = ShutdownPhase.NORMAL) -> None:
        """Initiate graceful shutdown process."""
        with self._lock:
            if self._shutdown_started:
                logger.warning("Shutdown already in progress")
                return

            self._shutdown_started = True
            self._metrics.start_time = time.time()
            self._metrics.phase = phase

        logger.info(f"Initiating {phase.value} shutdown")

        try:
            # Phase 1: Stop accepting new connections/work
            await self._stop_accepting_work()

            # Phase 2: Wait for active work to complete
            if phase == ShutdownPhase.NORMAL:
                await self._wait_for_active_work()

            # Phase 3: Execute shutdown hooks
            await self._execute_shutdown_hooks(phase)

            # Phase 4: Cleanup resources
            await self._cleanup_resources()

            # Phase 5: Final cleanup
            self._final_cleanup()

            self._metrics.total_duration = time.time() - self._metrics.start_time
            logger.info(f"Shutdown completed in {self._metrics.total_duration:.2f}s")

        except Exception as e:
            logger.error(f"Error during shutdown process: {e}")
            self._force_shutdown()
        finally:
            self._shutdown_event.set()

    async def _stop_accepting_work(self) -> None:
        """Stop accepting new connections/work."""
        logger.info("Stopping acceptance of new work")
        # This would be implemented by individual services
        # For example: server.should_accept = False

    async def _wait_for_active_work(self) -> None:
        """Wait for active connections/work to complete."""
        logger.info("Waiting for active work to complete")

        # Wait for connections to drain
        drain_success = await self._connection_drainer.wait_for_drain()
        self._metrics.connections_drained = 0 if drain_success else self._connection_drainer.active_connections

        if not drain_success:
            logger.warning(
                f"Could not drain all connections ({self._connection_drainer.active_connections} still active)"
            )

    async def _execute_shutdown_hooks(self, phase: ShutdownPhase) -> None:
        """Execute shutdown hooks in priority order."""
        # Sort hooks by priority (lower numbers first)
        sorted_hooks = sorted(self._hooks, key=lambda h: h.priority)

        logger.info(f"Executing {len(sorted_hooks)} shutdown hooks")

        for hook in sorted_hooks:
            # Skip non-critical hooks in fast/force shutdown
            if phase != ShutdownPhase.NORMAL and not hook.required:
                logger.debug(f"Skipping non-required hook: {hook.name}")
                continue

            try:
                logger.debug(f"Executing shutdown hook: {hook.name}")
                await asyncio.wait_for(hook.callback(), timeout=hook.timeout)
                self._metrics.hooks_executed += 1
            except asyncio.TimeoutError:
                logger.error(f"Shutdown hook {hook.name} timed out after {hook.timeout}s")
                self._metrics.hooks_failed += 1
                if hook.required and phase == ShutdownPhase.NORMAL:
                    logger.warning(f"Required hook {hook.name} failed, continuing with shutdown")
            except Exception as e:
                logger.error(f"Shutdown hook {hook.name} failed: {e}")
                self._metrics.hooks_failed += 1

    async def _cleanup_resources(self) -> None:
        """Cleanup system resources."""
        logger.info("Cleaning up resources")

        # Execute synchronous cleanup functions
        for cleanup_func in self._cleanup_functions:
            try:
                cleanup_func()
                self._metrics.resources_cleaned += 1
            except Exception as e:
                logger.error(f"Resource cleanup failed: {e}")

    def _final_cleanup(self) -> None:
        """Final cleanup before exit."""
        logger.info("Performing final cleanup")

        # Close any remaining resources
        try:
            # This is where you might close database connections, file handles, etc.
            pass
        except Exception as e:
            logger.error(f"Final cleanup failed: {e}")

    def _force_shutdown(self) -> None:
        """Force immediate shutdown."""
        logger.warning("Performing force shutdown")
        self._metrics.phase = ShutdownPhase.FORCE

        # Execute only critical cleanup
        for cleanup_func in self._cleanup_functions[:5]:  # Only first 5
            try:
                cleanup_func()
            except Exception as e:
                logger.error(f"Force cleanup failed: {e}")

        # Exit immediately
        import sys

        sys.exit(1)

    def register_shutdown_hook(
        self,
        name: str,
        callback: Callable[[], Awaitable[None]],
        priority: int = 100,
        timeout: float = 10.0,
        required: bool = True,
    ) -> None:
        """Register a shutdown hook."""
        hook = ShutdownHook(name=name, callback=callback, priority=priority, timeout=timeout, required=required)
        self._hooks.append(hook)
        logger.debug(f"Registered shutdown hook: {name} (priority: {priority})")

    def register_cleanup_function(self, cleanup_func: Callable[[], None]) -> None:
        """Register a synchronous cleanup function."""
        self._cleanup_functions.append(cleanup_func)

    def register_connection(self) -> None:
        """Register an active connection for draining."""
        self._connection_drainer.register_connection()

    def unregister_connection(self) -> None:
        """Unregister a completed connection."""
        self._connection_drainer.unregister_connection()

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown to complete."""
        await self._shutdown_event.wait()

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._shutdown_started

    def get_shutdown_metrics(self) -> Dict[str, Any]:
        """Get shutdown metrics."""
        return {
            "shutdown_started": self._shutdown_started,
            "phase": self._metrics.phase.value,
            "total_duration": self._metrics.total_duration,
            "hooks_executed": self._metrics.hooks_executed,
            "hooks_failed": self._metrics.hooks_failed,
            "connections_drained": self._metrics.connections_drained,
            "resources_cleaned": self._metrics.resources_cleaned,
            "active_connections": self._connection_drainer.active_connections,
        }


# Global instance
_shutdown_service: Optional[GracefulShutdownService] = None


def get_shutdown_service() -> GracefulShutdownService:
    """Get the global shutdown service instance."""
    global _shutdown_service
    if _shutdown_service is None:
        _shutdown_service = GracefulShutdownService()
    return _shutdown_service


async def graceful_shutdown(phase: ShutdownPhase = ShutdownPhase.NORMAL) -> None:
    """Convenience function to initiate graceful shutdown."""
    service = get_shutdown_service()
    await service.initiate_shutdown(phase)


def register_shutdown_hook(
    name: str,
    callback: Callable[[], Awaitable[None]],
    priority: int = 100,
    timeout: float = 10.0,
    required: bool = True,
) -> None:
    """Convenience function to register shutdown hook."""
    service = get_shutdown_service()
    service.register_shutdown_hook(name, callback, priority, timeout, required)


def register_cleanup_function(cleanup_func: Callable[[], None]) -> None:
    """Convenience function to register cleanup function."""
    service = get_shutdown_service()
    service.register_cleanup_function(cleanup_func)
