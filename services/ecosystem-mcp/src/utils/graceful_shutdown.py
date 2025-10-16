"""
Graceful Shutdown Handler

Handles SIGTERM/SIGINT signals to allow workers to:
1. Finish processing current file
2. Save checkpoint
3. Update job status
4. Clean exit

Prevents data loss on container restarts.
"""

import signal
import logging
import asyncio
from typing import Optional, Callable, Awaitable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ShutdownState(Enum):
    """Current state of shutdown process."""
    RUNNING = "running"
    SHUTDOWN_REQUESTED = "shutdown_requested"
    FINISHING_CURRENT_WORK = "finishing_current_work"
    SAVING_CHECKPOINT = "saving_checkpoint"
    CLEANUP = "cleanup"
    COMPLETED = "completed"


class GracefulShutdownHandler:
    """
    Handles graceful shutdown of worker processes.
    
    Features:
    - Signal handlers for SIGTERM/SIGINT
    - Finish current file before exit
    - Save checkpoint
    - Configurable timeout
    - Status tracking
    """
    
    def __init__(
        self,
        max_shutdown_time: int = 60,
        checkpoint_callback: Optional[Callable[[], Awaitable[None]]] = None,
        cleanup_callback: Optional[Callable[[], Awaitable[None]]] = None
    ):
        """
        Initialize the shutdown handler.
        
        Args:
            max_shutdown_time: Maximum seconds to wait for graceful shutdown
            checkpoint_callback: Async function to save checkpoint
            cleanup_callback: Async function for cleanup tasks
        """
        self.max_shutdown_time = max_shutdown_time
        self.checkpoint_callback = checkpoint_callback
        self.cleanup_callback = cleanup_callback
        
        self.shutdown_requested = False
        self.state = ShutdownState.RUNNING
        self.shutdown_start_time: Optional[datetime] = None
        self.current_task: Optional[str] = None
        
        # Signal handler references
        self._original_handlers = {}
        
        logger.info(
            f"GracefulShutdownHandler initialized "
            f"(max_shutdown_time={max_shutdown_time}s)"
        )
    
    def setup_signal_handlers(self):
        """
        Install signal handlers for graceful shutdown.
        
        Handles:
        - SIGTERM (Docker stop, systemd)
        - SIGINT (Ctrl+C)
        """
        try:
            # Save original handlers
            self._original_handlers['SIGTERM'] = signal.getsignal(signal.SIGTERM)
            self._original_handlers['SIGINT'] = signal.getsignal(signal.SIGINT)
            
            # Install new handlers
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
            
            logger.info("✅ Signal handlers installed (SIGTERM, SIGINT)")
        
        except Exception as e:
            logger.error(f"Failed to setup signal handlers: {e}")
    
    def _handle_signal(self, signum, frame):
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.warning(f"🛑 Received {signal_name}, initiating graceful shutdown...")
        
        if self.shutdown_requested:
            logger.warning("⚠️  Shutdown already in progress")
            return
        
        self.shutdown_requested = True
        self.shutdown_start_time = datetime.utcnow()
        self.state = ShutdownState.SHUTDOWN_REQUESTED
        
        logger.info(
            f"Graceful shutdown initiated: "
            f"max_wait={self.max_shutdown_time}s, "
            f"current_task={self.current_task or 'none'}"
        )
    
    def should_stop(self) -> bool:
        """
        Check if worker should stop processing.
        
        Call this periodically in worker loops.
        
        Returns:
            True if shutdown requested, False otherwise
        """
        if self.shutdown_requested:
            # Check if we've exceeded max shutdown time
            if self.shutdown_start_time:
                elapsed = (datetime.utcnow() - self.shutdown_start_time).total_seconds()
                if elapsed > self.max_shutdown_time:
                    logger.error(
                        f"❌ Graceful shutdown timeout exceeded ({elapsed}s > {self.max_shutdown_time}s). "
                        f"Forcing exit..."
                    )
                    self.state = ShutdownState.COMPLETED
                    return True
            
            return True
        
        return False
    
    async def finish_current_work(self, task_name: str = "current task"):
        """
        Mark that worker is finishing current work.
        
        Args:
            task_name: Name of current task for logging
        """
        self.current_task = task_name
        self.state = ShutdownState.FINISHING_CURRENT_WORK
        
        logger.info(f"📝 Finishing current work: {task_name}")
    
    async def save_checkpoint(self):
        """
        Save checkpoint before shutdown.
        
        Calls the checkpoint_callback if provided.
        """
        self.state = ShutdownState.SAVING_CHECKPOINT
        logger.info("💾 Saving checkpoint...")
        
        try:
            if self.checkpoint_callback:
                await self.checkpoint_callback()
                logger.info("✅ Checkpoint saved successfully")
            else:
                logger.debug("No checkpoint callback configured")
        
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
    
    async def cleanup(self):
        """
        Run cleanup tasks before exit.
        
        Calls the cleanup_callback if provided.
        """
        self.state = ShutdownState.CLEANUP
        logger.info("🧹 Running cleanup tasks...")
        
        try:
            if self.cleanup_callback:
                await self.cleanup_callback()
                logger.info("✅ Cleanup completed")
            else:
                logger.debug("No cleanup callback configured")
        
        except Exception as e:
            logger.error(f"Failed to run cleanup: {e}", exc_info=True)
    
    async def shutdown(self):
        """
        Execute graceful shutdown sequence.
        
        Call this when shutdown is requested.
        """
        if not self.shutdown_requested:
            logger.warning("Shutdown called but not requested. Ignoring.")
            return
        
        logger.info("🛑 Starting graceful shutdown sequence...")
        
        # 1. Finish current work (handled by caller)
        if self.state == ShutdownState.SHUTDOWN_REQUESTED:
            logger.info("⏳ Waiting for current work to finish...")
            # Caller should call finish_current_work()
        
        # 2. Save checkpoint
        await self.save_checkpoint()
        
        # 3. Cleanup
        await self.cleanup()
        
        # 4. Mark as completed
        self.state = ShutdownState.COMPLETED
        
        elapsed = 0
        if self.shutdown_start_time:
            elapsed = (datetime.utcnow() - self.shutdown_start_time).total_seconds()
        
        logger.info(
            f"✅ Graceful shutdown completed in {elapsed:.1f}s "
            f"(max: {self.max_shutdown_time}s)"
        )
    
    def restore_signal_handlers(self):
        """Restore original signal handlers."""
        try:
            for sig_name, handler in self._original_handlers.items():
                if handler is not None:
                    signal.signal(getattr(signal, sig_name), handler)
            
            logger.debug("Original signal handlers restored")
        
        except Exception as e:
            logger.error(f"Failed to restore signal handlers: {e}")
    
    def get_status(self) -> dict:
        """
        Get current shutdown status.
        
        Returns:
            Dict with status information
        """
        status = {
            "shutdown_requested": self.shutdown_requested,
            "state": self.state.value,
            "current_task": self.current_task,
            "max_shutdown_time": self.max_shutdown_time
        }
        
        if self.shutdown_start_time:
            elapsed = (datetime.utcnow() - self.shutdown_start_time).total_seconds()
            remaining = max(0, self.max_shutdown_time - elapsed)
            status.update({
                "shutdown_start_time": self.shutdown_start_time.isoformat(),
                "elapsed_seconds": round(elapsed, 1),
                "remaining_seconds": round(remaining, 1)
            })
        
        return status


# Global singleton instance
_shutdown_handler: Optional[GracefulShutdownHandler] = None


def get_shutdown_handler(
    max_shutdown_time: int = 60,
    checkpoint_callback: Optional[Callable[[], Awaitable[None]]] = None,
    cleanup_callback: Optional[Callable[[], Awaitable[None]]] = None
) -> GracefulShutdownHandler:
    """
    Get or create the global shutdown handler.
    
    Args:
        max_shutdown_time: Maximum seconds for graceful shutdown
        checkpoint_callback: Async function to save checkpoint
        cleanup_callback: Async function for cleanup
    
    Returns:
        GracefulShutdownHandler instance
    """
    global _shutdown_handler
    
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdownHandler(
            max_shutdown_time=max_shutdown_time,
            checkpoint_callback=checkpoint_callback,
            cleanup_callback=cleanup_callback
        )
        _shutdown_handler.setup_signal_handlers()
    
    return _shutdown_handler


def is_shutdown_requested() -> bool:
    """
    Check if shutdown has been requested.
    
    Convenience function for workers.
    
    Returns:
        True if shutdown requested, False otherwise
    """
    global _shutdown_handler
    
    if _shutdown_handler is None:
        return False
    
    return _shutdown_handler.should_stop()


async def execute_graceful_shutdown():
    """
    Execute graceful shutdown sequence.
    
    Convenience function for workers.
    """
    global _shutdown_handler
    
    if _shutdown_handler is not None:
        await _shutdown_handler.shutdown()

