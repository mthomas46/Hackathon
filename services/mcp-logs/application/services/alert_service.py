"""Alert Management Application Service."""

from typing import List, Optional

from ...domain.entities.alert import Alert
from ...domain.repositories.alert_repository import AlertRepository


class AlertService:
    """Application service for alert management."""
    
    def __init__(self, alert_repo: AlertRepository):
        """Initialize alert service."""
        self.alert_repo = alert_repo
    
    async def create_alert(
        self,
        name: str,
        service: str,
        severity: str,
        category: str,
        trigger_condition: str,
        description: str = "",
        **kwargs,
    ) -> Alert:
        """Create alert."""
        alert = Alert(
            name=name,
            service=service,
            severity=severity,
            category=category,
            trigger_condition=trigger_condition,
            description=description,
            **kwargs,
        )
        
        await self.alert_repo.add(alert)
        return alert
    
    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return await self.alert_repo.get_by_id(alert_id)
    
    async def acknowledge_alert(self, alert_id: str, user: str) -> Alert:
        """Acknowledge alert."""
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")
        
        alert.acknowledge(user)
        await self.alert_repo.update(alert)
        return alert
    
    async def resolve_alert(self, alert_id: str, notes: str) -> Alert:
        """Resolve alert."""
        alert = await self.alert_repo.get_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")
        
        alert.resolve(notes)
        await self.alert_repo.update(alert)
        return alert
    
    async def list_active_alerts(self) -> List[Alert]:
        """List active alerts."""
        return await self.alert_repo.list_active()
    
    async def list_critical_alerts(self) -> List[Alert]:
        """List critical alerts."""
        return await self.alert_repo.list_by_severity("critical")

