"""
Jira Integration Service
=========================

Bidirectional integration with Jira for ticket synchronization.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..entities import Ticket, TicketType, TicketStatus, TicketPriority, SyncResult, FieldMapping


class JiraIntegrationService:
    """
    Jira integration service for bidirectional ticket sync.
    
    Features:
    - Fetch tickets from Jira projects
    - Create tickets in Jira
    - Update ticket status and fields
    - Sync comments and attachments
    - Handle custom fields
    """
    
    def __init__(self, jira_url: str, api_token: str, email: str):
        """
        Initialize Jira integration.
        
        Args:
            jira_url: Jira instance URL (e.g., https://company.atlassian.net)
            api_token: Jira API token
            email: User email for authentication
        """
        self.jira_url = jira_url
        self.api_token = api_token
        self.email = email
        self._field_mappings = self._create_default_mappings()
    
    def _create_default_mappings(self) -> List[FieldMapping]:
        """Create default field mappings for Jira."""
        return [
            FieldMapping("jira", "status", "status", "status_to_internal"),
            FieldMapping("jira", "priority", "priority", "priority_to_internal"),
            FieldMapping("jira", "story_points", "customfield_10016"),  # Common story points field
            FieldMapping("jira", "estimated_hours", "timeoriginalestimate"),
            FieldMapping("jira", "time_spent_hours", "timespent")
        ]
    
    async def fetch_tickets(
        self,
        project_key: str,
        jql_filter: Optional[str] = None,
        max_results: int = 100
    ) -> List[Ticket]:
        """
        Fetch tickets from Jira project.
        
        Args:
            project_key: Jira project key (e.g., "PROJ")
            jql_filter: Optional JQL filter
            max_results: Maximum number of tickets to fetch
            
        Returns:
            List of normalized tickets
        """
        # In production, this would make actual API calls
        # For now, return mock data
        
        mock_tickets = []
        for i in range(min(5, max_results)):
            ticket = Ticket(
                id=str(uuid.uuid4()),
                external_id=f"{project_key}-{i+1}",
                source="jira",
                title=f"Sample Jira Ticket {i+1}",
                description=f"Description for ticket {i+1}",
                ticket_type=TicketType.STORY,
                status=TicketStatus.TODO,
                priority=TicketPriority.MEDIUM,
                story_points=float(i % 8 + 1),
                source_data={
                    'project_key': project_key,
                    'issue_type': 'Story'
                }
            )
            mock_tickets.append(ticket)
        
        return mock_tickets
    
    async def create_ticket(
        self,
        project_key: str,
        ticket: Ticket
    ) -> str:
        """
        Create a ticket in Jira.
        
        Args:
            project_key: Jira project key
            ticket: Ticket to create
            
        Returns:
            External ticket ID (e.g., "PROJ-123")
        """
        # In production, this would make actual API call to create issue
        external_id = f"{project_key}-{uuid.uuid4().hex[:6].upper()}"
        
        return external_id
    
    async def update_ticket(
        self,
        external_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a ticket in Jira.
        
        Args:
            external_id: Jira issue key (e.g., "PROJ-123")
            updates: Fields to update
            
        Returns:
            True if successful
        """
        # In production, this would make actual API call
        return True
    
    async def sync_tickets(
        self,
        project_key: str,
        tickets: List[Ticket]
    ) -> SyncResult:
        """
        Sync tickets to Jira.
        
        Args:
            project_key: Jira project key
            tickets: Tickets to sync
            
        Returns:
            Sync result with statistics
        """
        start_time = datetime.now()
        result = SyncResult(success=True)
        
        for ticket in tickets:
            try:
                if ticket.external_id:
                    # Update existing
                    await self.update_ticket(ticket.external_id, ticket.to_dict())
                    result.tickets_updated += 1
                else:
                    # Create new
                    external_id = await self.create_ticket(project_key, ticket)
                    ticket.external_id = external_id
                    result.tickets_created += 1
                
                result.tickets_synced += 1
            except Exception as e:
                result.tickets_failed += 1
                result.errors.append(f"Failed to sync {ticket.id}: {str(e)}")
        
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        result.success = result.tickets_failed == 0
        
        return result
    
    async def fetch_comments(self, external_id: str) -> List[Dict[str, Any]]:
        """Fetch comments for a Jira issue."""
        # Mock implementation
        return [
            {
                'author': 'user@example.com',
                'body': 'Sample comment',
                'created': datetime.now().isoformat()
            }
        ]
    
    async def add_comment(self, external_id: str, comment: str) -> bool:
        """Add a comment to a Jira issue."""
        # Mock implementation
        return True
    
    async def get_project_metadata(self, project_key: str) -> Dict[str, Any]:
        """Get Jira project metadata."""
        return {
            'key': project_key,
            'name': f'Project {project_key}',
            'issue_types': ['Story', 'Task', 'Bug', 'Epic'],
            'statuses': ['To Do', 'In Progress', 'In Review', 'Done'],
            'priorities': ['Lowest', 'Low', 'Medium', 'High', 'Highest']
        }

