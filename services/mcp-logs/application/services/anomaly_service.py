"""Anomaly Detection Application Service."""

from typing import List, Optional

from ...domain.entities.anomaly import Anomaly
from ...domain.repositories.anomaly_repository import AnomalyRepository


class AnomalyService:
    """Application service for anomaly detection."""
    
    def __init__(self, anomaly_repo: AnomalyRepository):
        """Initialize anomaly service."""
        self.anomaly_repo = anomaly_repo
    
    async def report_anomaly(
        self,
        service: str,
        anomaly_type: str,
        severity: str,
        description: str,
        confidence: float,
        **kwargs,
    ) -> Anomaly:
        """Report anomaly."""
        anomaly = Anomaly(
            service=service,
            type=anomaly_type,
            severity=severity,
            description=description,
            confidence=confidence,
            **kwargs,
        )
        
        await self.anomaly_repo.add(anomaly)
        return anomaly
    
    async def get_anomaly(self, anomaly_id: str) -> Optional[Anomaly]:
        """Get anomaly by ID."""
        return await self.anomaly_repo.get_by_id(anomaly_id)
    
    async def acknowledge_anomaly(self, anomaly_id: str, user: str) -> Anomaly:
        """Acknowledge anomaly."""
        anomaly = await self.anomaly_repo.get_by_id(anomaly_id)
        if not anomaly:
            raise ValueError(f"Anomaly not found: {anomaly_id}")
        
        anomaly.acknowledge(user)
        await self.anomaly_repo.update(anomaly)
        return anomaly
    
    async def resolve_anomaly(self, anomaly_id: str, notes: str) -> Anomaly:
        """Resolve anomaly."""
        anomaly = await self.anomaly_repo.get_by_id(anomaly_id)
        if not anomaly:
            raise ValueError(f"Anomaly not found: {anomaly_id}")
        
        anomaly.resolve(notes)
        await self.anomaly_repo.update(anomaly)
        return anomaly
    
    async def list_active_anomalies(self) -> List[Anomaly]:
        """List active anomalies."""
        return await self.anomaly_repo.list_active()

