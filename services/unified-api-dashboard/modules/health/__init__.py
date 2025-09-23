class HealthMonitor:
    def __init__(self, discovery_client=None):
        self.discovery_client = discovery_client

    async def get_health_overview(self):
        return []


__all__ = ["HealthMonitor"]
