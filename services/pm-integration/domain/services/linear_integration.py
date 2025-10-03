"""
Linear Integration Service
===========================

Bidirectional integration with Linear for issue synchronization.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..entities import Ticket, TicketType, TicketStatus, TicketPriority, SyncResult


class LinearIntegrationService:
    """
    Linear integration service for bidirectional issue sync.
    
    Linear uses a GraphQL API and has a more streamlined structure
    than Jira, with built-in project management features.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Linear integration.
        
        Args:
            api_key: Linear API key
        """
        self.api_key = api_key
        self.graphql_endpoint = "https://api.linear.app/graphql"
    
    async def fetch_issues(
        self,
        team_id: str,
        state_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Ticket]:
        """
        Fetch issues from Linear team.
        
        Args:
            team_id: Linear team ID
            state_filter: Optional state filter (e.g., "started", "completed")
            limit: Maximum number of issues to fetch
            
        Returns:
            List of normalized tickets
        """
        # Mock implementation
        mock_tickets = []
        for i in range(min(5, limit)):
            ticket = Ticket(
                id=str(uuid.uuid4()),
                external_id=f"LIN-{i+1}",
                source="linear",
                title=f"Sample Linear Issue {i+1}",
                description=f"Description for issue {i+1}",
                ticket_type=TicketType.TASK,
                status=TicketStatus.TODO,
                priority=TicketPriority.MEDIUM,
                story_points=float(i % 5 + 1),
                source_data={
                    'team_id': team_id,
                    'identifier': f"LIN-{i+1}"
                }
            )
            mock_tickets.append(ticket)
        
        return mock_tickets
    
    async def create_issue(
        self,
        team_id: str,
        ticket: Ticket
    ) -> str:
        """
        Create an issue in Linear.
        
        Args:
            team_id: Linear team ID
            ticket: Ticket to create
            
        Returns:
            External issue ID
        """
        external_id = f"LIN-{uuid.uuid4().hex[:6].upper()}"
        return external_id
    
    async def update_issue(
        self,
        issue_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an issue in Linear.
        
        Args:
            issue_id: Linear issue ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        return True
    
    async def sync_issues(
        self,
        team_id: str,
        tickets: List[Ticket]
    ) -> SyncResult:
        """
        Sync tickets to Linear.
        
        Args:
            team_id: Linear team ID
            tickets: Tickets to sync
            
        Returns:
            Sync result with statistics
        """
        start_time = datetime.now()
        result = SyncResult(success=True)
        
        for ticket in tickets:
            try:
                if ticket.external_id:
                    await self.update_issue(ticket.external_id, ticket.to_dict())
                    result.tickets_updated += 1
                else:
                    external_id = await self.create_issue(team_id, ticket)
                    ticket.external_id = external_id
                    result.tickets_created += 1
                
                result.tickets_synced += 1
            except Exception as e:
                result.tickets_failed += 1
                result.errors.append(f"Failed to sync {ticket.id}: {str(e)}")
        
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        result.success = result.tickets_failed == 0
        
        return result

