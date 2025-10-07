"""Bi-directional Sync Engine for Evergreen Documentation."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio


class SyncDirection(Enum):
    """Synchronization direction."""
    MCP_TO_CONFLUENCE = "mcp_to_confluence"
    CONFLUENCE_TO_MCP = "confluence_to_mcp"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LAST_MODIFIED_WINS = "last_modified_wins"
    MCP_WINS = "mcp_wins"
    CONFLUENCE_WINS = "confluence_wins"
    MANUAL = "manual"


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    direction: SyncDirection
    pages_updated: int = 0
    pages_synced: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    content: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SyncSchedule:
    """Sync schedule configuration."""
    interval_minutes: int
    spaces: List[str]
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    conflict_resolution: ConflictResolution = ConflictResolution.LAST_MODIFIED_WINS
    enabled: bool = True


class SyncEngine:
    """Bi-directional synchronization engine."""
    
    def __init__(
        self,
        confluence_url: str,
        api_token: str,
        user_email: Optional[str] = None
    ):
        """
        Initialize sync engine.
        
        Args:
            confluence_url: Confluence instance URL
            api_token: API token for authentication
            user_email: User email for API calls
        """
        self.confluence_url = confluence_url.rstrip('/')
        self.api_token = api_token
        self.user_email = user_email
        self._configured = bool(confluence_url and api_token)
    
    @property
    def is_configured(self) -> bool:
        """Check if engine is properly configured."""
        return self._configured
    
    async def sync_to_confluence(
        self,
        mcp_docs: Dict[str, Any],
        space_key: str,
        page_title: str,
        parent_id: Optional[str] = None
    ) -> SyncResult:
        """
        Sync MCP documentation to Confluence.
        
        Args:
            mcp_docs: MCP documentation dict with 'content', 'version', etc.
            space_key: Confluence space key
            page_title: Page title in Confluence
            parent_id: Optional parent page ID
        
        Returns:
            SyncResult
        """
        try:
            # Extract content
            content = mcp_docs.get('content', '')
            version = mcp_docs.get('version', '1.0.0')
            
            # Here we would use ConfluenceClient to update the page
            # For now, simulate success
            
            return SyncResult(
                success=True,
                direction=SyncDirection.MCP_TO_CONFLUENCE,
                pages_updated=1,
                pages_synced=1
            )
        
        except Exception as e:
            return SyncResult(
                success=False,
                direction=SyncDirection.MCP_TO_CONFLUENCE,
                errors=[str(e)]
            )
    
    async def sync_from_confluence(
        self,
        space_key: str,
        page_title: str
    ) -> SyncResult:
        """
        Sync documentation from Confluence to MCP.
        
        Args:
            space_key: Confluence space key
            page_title: Page title to sync
        
        Returns:
            SyncResult with content
        """
        try:
            # Here we would use ConfluenceClient to fetch the page
            # For now, simulate success
            
            content = f"# {page_title}\n\nContent from Confluence"
            
            return SyncResult(
                success=True,
                direction=SyncDirection.CONFLUENCE_TO_MCP,
                pages_synced=1,
                content=content
            )
        
        except Exception as e:
            return SyncResult(
                success=False,
                direction=SyncDirection.CONFLUENCE_TO_MCP,
                errors=[str(e)]
            )
    
    async def sync_bidirectional(
        self,
        space_key: str,
        pages: List[str],
        conflict_resolution: str = "last_modified_wins"
    ) -> SyncResult:
        """
        Perform bidirectional synchronization.
        
        Args:
            space_key: Confluence space key
            pages: List of page titles to sync
            conflict_resolution: Strategy for resolving conflicts
        
        Returns:
            SyncResult
        """
        try:
            pages_synced = 0
            conflicts_detected = 0
            conflicts_resolved = 0
            
            for page_title in pages:
                # Get both versions
                mcp_version = await self._get_mcp_version(page_title)
                confluence_version = await self._get_confluence_version(space_key, page_title)
                
                # Check for conflicts
                if self._has_conflict(mcp_version, confluence_version):
                    conflicts_detected += 1
                    
                    # Resolve conflict
                    if conflict_resolution == "last_modified_wins":
                        await self._resolve_by_last_modified(
                            mcp_version,
                            confluence_version,
                            space_key,
                            page_title
                        )
                        conflicts_resolved += 1
                else:
                    # No conflict, sync normally
                    if mcp_version.get('modified_at', datetime.min) > confluence_version.get('modified_at', datetime.min):
                        await self.sync_to_confluence(
                            mcp_version,
                            space_key,
                            page_title
                        )
                    else:
                        await self.sync_from_confluence(space_key, page_title)
                
                pages_synced += 1
            
            return SyncResult(
                success=True,
                direction=SyncDirection.BIDIRECTIONAL,
                pages_synced=pages_synced,
                conflicts_detected=conflicts_detected,
                conflicts_resolved=conflicts_resolved
            )
        
        except Exception as e:
            return SyncResult(
                success=False,
                direction=SyncDirection.BIDIRECTIONAL,
                errors=[str(e)]
            )
    
    def create_schedule(
        self,
        interval_minutes: int,
        spaces: List[str],
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> SyncSchedule:
        """
        Create a synchronization schedule.
        
        Args:
            interval_minutes: Sync interval in minutes
            spaces: List of Confluence spaces to sync
            direction: Sync direction
        
        Returns:
            SyncSchedule
        """
        return SyncSchedule(
            interval_minutes=interval_minutes,
            spaces=spaces,
            direction=direction
        )
    
    async def run_scheduled_sync(self, schedule: SyncSchedule) -> SyncResult:
        """
        Run a scheduled synchronization.
        
        Args:
            schedule: Sync schedule configuration
        
        Returns:
            SyncResult
        """
        if not schedule.enabled:
            return SyncResult(
                success=False,
                direction=schedule.direction,
                errors=["Schedule is disabled"]
            )
        
        total_pages = 0
        
        for space_key in schedule.spaces:
            # Get all pages in space
            pages = await self._get_space_pages(space_key)
            
            if schedule.direction == SyncDirection.BIDIRECTIONAL:
                result = await self.sync_bidirectional(
                    space_key,
                    pages,
                    conflict_resolution=schedule.conflict_resolution.value
                )
                total_pages += result.pages_synced
        
        return SyncResult(
            success=True,
            direction=schedule.direction,
            pages_synced=total_pages
        )
    
    async def _get_mcp_version(self, page_title: str) -> Dict[str, Any]:
        """Get MCP version of a document."""
        # Placeholder - would fetch from MCP Store
        return {
            "title": page_title,
            "content": f"# {page_title}\n\nMCP content",
            "modified_at": datetime.now()
        }
    
    async def _get_confluence_version(self, space_key: str, page_title: str) -> Dict[str, Any]:
        """Get Confluence version of a page."""
        # Placeholder - would fetch from Confluence
        return {
            "title": page_title,
            "content": f"# {page_title}\n\nConfluence content",
            "modified_at": datetime.now()
        }
    
    def _has_conflict(self, mcp_version: Dict[str, Any], confluence_version: Dict[str, Any]) -> bool:
        """Check if versions have conflicting changes."""
        # Simplified conflict detection
        mcp_modified = mcp_version.get('modified_at', datetime.min)
        confluence_modified = confluence_version.get('modified_at', datetime.min)
        
        # If both modified recently (within 1 hour), consider it a conflict
        time_diff = abs((mcp_modified - confluence_modified).total_seconds())
        return time_diff < 3600 and mcp_version.get('content') != confluence_version.get('content')
    
    async def _resolve_by_last_modified(
        self,
        mcp_version: Dict[str, Any],
        confluence_version: Dict[str, Any],
        space_key: str,
        page_title: str
    ) -> None:
        """Resolve conflict by choosing last modified version."""
        if mcp_version.get('modified_at', datetime.min) > confluence_version.get('modified_at', datetime.min):
            await self.sync_to_confluence(mcp_version, space_key, page_title)
        else:
            await self.sync_from_confluence(space_key, page_title)
    
    async def _get_space_pages(self, space_key: str) -> List[str]:
        """Get all pages in a Confluence space."""
        # Placeholder - would query Confluence API
        return ["MCP Gateway", "MCP Store", "MCP Orchestrator"]

