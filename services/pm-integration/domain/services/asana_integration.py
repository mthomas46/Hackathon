"""
Asana Integration Service
==========================

Bidirectional integration with Asana for task synchronization.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..entities import Ticket, TicketType, TicketStatus, TicketPriority, SyncResult


class AsanaIntegrationService:
    """
    Asana integration service for bidirectional task sync.
    
    Asana organizes work into projects and sections, with a focus
    on task management and team collaboration.
    """
    
    def __init__(self, access_token: str):
        """
        Initialize Asana integration.
        
        Args:
            access_token: Asana personal access token
        """
        self.access_token = access_token
        self.api_base = "https://app.asana.com/api/1.0"
    
    async def fetch_tasks(
        self,
        project_id: str,
        completed: Optional[bool] = None,
        limit: int = 100
    ) -> List[Ticket]:
        """
        Fetch tasks from Asana project.
        
        Args:
            project_id: Asana project GID
            completed: Filter by completion status
            limit: Maximum number of tasks to fetch
            
        Returns:
            List of normalized tickets
        """
        # Mock implementation
        mock_tickets = []
        for i in range(min(5, limit)):
            ticket = Ticket(
                id=str(uuid.uuid4()),
                external_id=str(1000000000000 + i),  # Asana uses GIDs
                source="asana",
                title=f"Sample Asana Task {i+1}",
                description=f"Description for task {i+1}",
                ticket_type=TicketType.TASK,
                status=TicketStatus.TODO if not completed else TicketStatus.DONE,
                priority=TicketPriority.MEDIUM,
                source_data={
                    'project_id': project_id,
                    'gid': str(1000000000000 + i)
                }
            )
            mock_tickets.append(ticket)
        
        return mock_tickets
    
    async def create_task(
        self,
        project_id: str,
        ticket: Ticket
    ) -> str:
        """
        Create a task in Asana.
        
        Args:
            project_id: Asana project GID
            ticket: Ticket to create
            
        Returns:
            External task GID
        """
        external_id = str(1000000000000 + uuid.uuid4().int % 1000000)
        return external_id
    
    async def update_task(
        self,
        task_gid: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a task in Asana.
        
        Args:
            task_gid: Asana task GID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        return True
    
    async def sync_tasks(
        self,
        project_id: str,
        tickets: List[Ticket]
    ) -> SyncResult:
        """
        Sync tickets to Asana.
        
        Args:
            project_id: Asana project GID
            tickets: Tickets to sync
            
        Returns:
            Sync result with statistics
        """
        start_time = datetime.now()
        result = SyncResult(success=True)
        
        for ticket in tickets:
            try:
                if ticket.external_id:
                    await self.update_task(ticket.external_id, ticket.to_dict())
                    result.tickets_updated += 1
                else:
                    external_id = await self.create_task(project_id, ticket)
                    ticket.external_id = external_id
                    result.tickets_created += 1
                
                result.tickets_synced += 1
            except Exception as e:
                result.tickets_failed += 1
                result.errors.append(f"Failed to sync {ticket.id}: {str(e)}")
        
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        result.success = result.tickets_failed == 0
        
        return result

