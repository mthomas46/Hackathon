"""Port Allocator - Infrastructure Layer.

Manages dynamic port allocation for MCP instances.
"""

import logging
from typing import Set, Optional
import random

from services.mcp_provisioner.infrastructure.config.settings import Settings


logger = logging.getLogger(__name__)


class PortAllocationError(Exception):
    """Raised when port allocation fails."""
    pass


class PortAllocator:
    """
    Manages port allocation for MCP containers.
    
    Allocates ports from a configurable range, tracks allocations,
    and supports deallocation.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize port allocator.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.start_port = settings.mcp_port_range_start
        self.end_port = settings.mcp_port_range_end
        self.allocated_ports: Set[int] = set()
        
        logger.info(
            f"Port allocator initialized: range {self.start_port}-{self.end_port}"
        )
    
    def allocate_port(self) -> int:
        """
        Allocate an available port.
        
        Returns:
            Allocated port number
        
        Raises:
            PortAllocationError: If no ports available
        """
        # Get available ports
        available_ports = set(range(self.start_port, self.end_port + 1)) - self.allocated_ports
        
        if not available_ports:
            logger.error("No available ports in range")
            raise PortAllocationError(
                f"No available ports in range {self.start_port}-{self.end_port}"
            )
        
        # Allocate random port from available
        port = random.choice(list(available_ports))
        self.allocated_ports.add(port)
        
        logger.info(f"Allocated port: {port} ({len(self.allocated_ports)} allocated)")
        return port
    
    def deallocate_port(self, port: int) -> None:
        """
        Deallocate a port.
        
        Args:
            port: Port to deallocate
        """
        if port in self.allocated_ports:
            self.allocated_ports.remove(port)
            logger.info(f"Deallocated port: {port}")
        else:
            logger.warning(f"Port not allocated: {port}")
    
    def is_allocated(self, port: int) -> bool:
        """Check if a port is allocated."""
        return port in self.allocated_ports
    
    def get_allocated_count(self) -> int:
        """Get number of allocated ports."""
        return len(self.allocated_ports)
    
    def get_available_count(self) -> int:
        """Get number of available ports."""
        total_ports = self.end_port - self.start_port + 1
        return total_ports - len(self.allocated_ports)
    
    def reset(self) -> None:
        """Reset all allocations (for testing)."""
        count = len(self.allocated_ports)
        self.allocated_ports.clear()
        logger.warning(f"Reset port allocations: {count} ports deallocated")

