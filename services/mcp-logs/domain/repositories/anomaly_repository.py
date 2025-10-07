"""Anomaly Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.anomaly import Anomaly


class AnomalyRepository(ABC):
    """Abstract repository for Anomaly entities."""
    
    @abstractmethod
    async def add(self, anomaly: Anomaly) -> None:
        """Add anomaly."""
        pass
    
    @abstractmethod
    async def get_by_id(self, anomaly_id: str) -> Optional[Anomaly]:
        """Get anomaly by ID."""
        pass
    
    @abstractmethod
    async def update(self, anomaly: Anomaly) -> None:
        """Update anomaly."""
        pass
    
    @abstractmethod
    async def delete(self, anomaly_id: str) -> None:
        """Delete anomaly."""
        pass
    
    @abstractmethod
    async def list_by_service(self, service: str) -> List[Anomaly]:
        """List anomalies by service."""
        pass
    
    @abstractmethod
    async def list_by_severity(self, severity: str) -> List[Anomaly]:
        """List anomalies by severity."""
        pass
    
    @abstractmethod
    async def list_active(self) -> List[Anomaly]:
        """List active anomalies."""
        pass
    
    @abstractmethod
    async def list_unacknowledged(self) -> List[Anomaly]:
        """List unacknowledged anomalies."""
        pass

