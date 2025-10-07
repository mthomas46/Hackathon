"""Alert Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.alert import Alert


class AlertRepository(ABC):
    """Abstract repository for Alert entities."""
    
    @abstractmethod
    async def add(self, alert: Alert) -> None:
        """Add alert."""
        pass
    
    @abstractmethod
    async def get_by_id(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        pass
    
    @abstractmethod
    async def update(self, alert: Alert) -> None:
        """Update alert."""
        pass
    
    @abstractmethod
    async def delete(self, alert_id: str) -> None:
        """Delete alert."""
        pass
    
    @abstractmethod
    async def list_by_service(self, service: str) -> List[Alert]:
        """List alerts by service."""
        pass
    
    @abstractmethod
    async def list_by_severity(self, severity: str) -> List[Alert]:
        """List alerts by severity."""
        pass
    
    @abstractmethod
    async def list_active(self) -> List[Alert]:
        """List active alerts."""
        pass
    
    @abstractmethod
    async def list_unacknowledged(self) -> List[Alert]:
        """List unacknowledged alerts."""
        pass

