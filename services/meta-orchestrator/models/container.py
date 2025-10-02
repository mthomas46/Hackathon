"""Container-related models"""

from typing import Optional
from pydantic import BaseModel


class ContainerInfo(BaseModel):
    """Information about a Docker container"""
    id: str
    name: str
    image: str
    status: str
    ports: str = ""

    @property
    def is_running(self) -> bool:
        """Check if container is running"""
        return "Up" in self.status or "running" in self.status.lower()

    @property
    def short_id(self) -> str:
        """Get short container ID"""
        return self.id[:12] if len(self.id) > 12 else self.id
