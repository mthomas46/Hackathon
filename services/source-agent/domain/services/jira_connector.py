"""
Jira Connector - Multi-platform document ingestion
==================================================

Integrates with Jira to fetch tickets, analyze patterns, and provide
planning insights based on historical data.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import statistics

try:
    from jira import JIRA
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    JIRA = None


@dataclass
class JiraTicket:
    """Represents a Jira ticket with planning-relevant data."""
    key: str
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    story_points: Optional[float]
    created: datetime
    updated: datetime
    resolved: Optional[datetime]
    assignee: Optional[str]
    labels: List[str]
    components: List[str]
    sprint: Optional[str]


@dataclass
class JiraAnalytics:
    """Analytics derived from Jira tickets."""
    total_tickets: int
    avg_ticket_size: float
    completion_rate: float
    avg_cycle_time_days: float
    velocity: float  # Story points per sprint
    bottlenecks: List[str]
    common_labels: List[str]
    status_distribution: Dict[str, int]


class JiraConnector:
    """
    Jira API integration with intelligent ticket analysis.
    
    Provides:
    - Ticket fetching with field mapping
    - Pattern analysis for planning insights
    - Historical data analysis
    - Sprint metrics extraction
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, log_client=None):
        """
        Initialize Jira connector.
        
        Args:
            config: Jira configuration with server, username, api_token
            log_client: Optional log collector client
        """
        self.config = config or self._get_config_from_env()
        self.log_client = log_client
        self.jira_client = None
        
        if JIRA_AVAILABLE and self.config.get('server'):
            try:
                self.jira_client = JIRA(
                    server=self.config['server'],
                    basic_auth=(
                        self.config.get('username'),
                        self.config.get('api_token')
                    )
                )
            except Exception as e:
                if self.log_client:
                    asyncio.create_task(self.log_client.log_error(
                        f"Failed to initialize Jira client: {str(e)}",
                        context={"config": self.config}
                    ))
    
    def _get_config_from_env(self) -> Dict[str, str]:
        """Get Jira configuration from environment variables."""
        return {
            'server': os.getenv('JIRA_SERVER', ''),
            'username': os.getenv('JIRA_USERNAME', ''),
            'api_token': os.getenv('JIRA_API_TOKEN', ''),
            'project_key': os.getenv('JIRA_PROJECT_KEY', '')
        }
    
    async def fetch_tickets(
        self,
        project_key: str,
        days_back: int = 90,
        max_results: int = 1000
    ) -> List[JiraTicket]:
        """
        Fetch Jira tickets with planning-relevant data.
        
        Args:
            project_key: Jira project key
            days_back: Number of days of history to fetch
            max_results: Maximum number of tickets to fetch
            
        Returns:
            List of JiraTicket objects
        """
        if not self.jira_client:
            if self.log_client:
                await self.log_client.log_warning(
                    "Jira client not initialized, returning mock data",
                    context={"project_key": project_key}
                )
            return self._generate_mock_tickets(project_key, 50)
        
        try:
            # Calculate date range
            start_date = datetime.now() - timedelta(days=days_back)
            jql = f'project = {project_key} AND created >= "{start_date.strftime("%Y-%m-%d")}" ORDER BY created DESC'
            
            # Fetch issues
            issues = self.jira_client.search_issues(
                jql,
                maxResults=max_results,
                expand='changelog'
            )
            
            # Convert to JiraTicket objects
            tickets = []
            for issue in issues:
                ticket = self._issue_to_ticket(issue)
                if ticket:
                    tickets.append(ticket)
            
            if self.log_client:
                await self.log_client.log_info(
                    f"Fetched {len(tickets)} tickets from Jira",
                    context={
                        "project_key": project_key,
                        "days_back": days_back,
                        "ticket_count": len(tickets)
                    }
                )
            
            return tickets
            
        except Exception as e:
            if self.log_client:
                await self.log_client.log_error(
                    f"Failed to fetch Jira tickets: {str(e)}",
                    context={"project_key": project_key}
                )
            return []
    
    def _issue_to_ticket(self, issue) -> Optional[JiraTicket]:
        """Convert Jira issue to JiraTicket object."""
        try:
            fields = issue.fields
            
            # Extract story points (common custom field IDs)
            story_points = None
            for field_id in ['customfield_10002', 'customfield_10016', 'customfield_10026']:
                if hasattr(fields, field_id):
                    story_points = getattr(fields, field_id)
                    if story_points:
                        break
            
            # Parse dates
            created = datetime.fromisoformat(fields.created.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(fields.updated.replace('Z', '+00:00'))
            resolved = None
            if fields.resolutiondate:
                resolved = datetime.fromisoformat(fields.resolutiondate.replace('Z', '+00:00'))
            
            return JiraTicket(
                key=issue.key,
                summary=fields.summary,
                description=fields.description or '',
                issue_type=fields.issuetype.name,
                status=fields.status.name,
                priority=fields.priority.name if fields.priority else 'Medium',
                story_points=float(story_points) if story_points else None,
                created=created,
                updated=updated,
                resolved=resolved,
                assignee=fields.assignee.displayName if fields.assignee else None,
                labels=fields.labels or [],
                components=[c.name for c in fields.components] if fields.components else [],
                sprint=self._extract_sprint_name(fields)
            )
            
        except Exception as e:
            if self.log_client:
                asyncio.create_task(self.log_client.log_error(
                    f"Failed to parse Jira issue: {str(e)}",
                    context={"issue_key": issue.key if hasattr(issue, 'key') else 'unknown'}
                ))
            return None
    
    def _extract_sprint_name(self, fields) -> Optional[str]:
        """Extract sprint name from custom fields."""
        # Sprint is often in customfield_10020 or similar
        for field_id in ['customfield_10020', 'customfield_10010']:
            if hasattr(fields, field_id):
                sprint_data = getattr(fields, field_id)
                if sprint_data:
                    if isinstance(sprint_data, list) and len(sprint_data) > 0:
                        # Parse sprint string
                        sprint_str = str(sprint_data[0])
                        if 'name=' in sprint_str:
                            name_part = sprint_str.split('name=')[1]
                            return name_part.split(',')[0]
                    return str(sprint_data)
        return None
    
    async def analyze_ticket_patterns(self, tickets: List[JiraTicket]) -> JiraAnalytics:
        """
        Analyze ticket patterns for planning insights.
        
        Args:
            tickets: List of JiraTicket objects
            
        Returns:
            JiraAnalytics with metrics and insights
        """
        if not tickets:
            return JiraAnalytics(
                total_tickets=0,
                avg_ticket_size=0.0,
                completion_rate=0.0,
                avg_cycle_time_days=0.0,
                velocity=0.0,
                bottlenecks=[],
                common_labels=[],
                status_distribution={}
            )
        
        # Calculate metrics
        total_tickets = len(tickets)
        
        # Average ticket size (story points)
        tickets_with_points = [t for t in tickets if t.story_points is not None]
        avg_ticket_size = (
            statistics.mean([t.story_points for t in tickets_with_points])
            if tickets_with_points else 0.0
        )
        
        # Completion rate
        completed_tickets = [t for t in tickets if t.resolved is not None]
        completion_rate = len(completed_tickets) / total_tickets if total_tickets > 0 else 0.0
        
        # Average cycle time (days from created to resolved)
        cycle_times = [
            (t.resolved - t.created).days
            for t in completed_tickets
            if t.resolved
        ]
        avg_cycle_time = statistics.mean(cycle_times) if cycle_times else 0.0
        
        # Velocity (story points per sprint)
        sprint_points = {}
        for ticket in tickets:
            if ticket.sprint and ticket.story_points:
                if ticket.sprint not in sprint_points:
                    sprint_points[ticket.sprint] = 0.0
                sprint_points[ticket.sprint] += ticket.story_points
        
        velocity = statistics.mean(sprint_points.values()) if sprint_points else 0.0
        
        # Identify bottlenecks (statuses with many tickets)
        status_distribution = {}
        for ticket in tickets:
            status_distribution[ticket.status] = status_distribution.get(ticket.status, 0) + 1
        
        # Find statuses with > 20% of tickets
        bottlenecks = [
            status for status, count in status_distribution.items()
            if count / total_tickets > 0.2 and status not in ['Done', 'Closed', 'Resolved']
        ]
        
        # Common labels
        label_counts = {}
        for ticket in tickets:
            for label in ticket.labels:
                label_counts[label] = label_counts.get(label, 0) + 1
        
        common_labels = sorted(
            label_counts.keys(),
            key=lambda x: label_counts[x],
            reverse=True
        )[:10]
        
        if self.log_client:
            await self.log_client.log_business_event(
                "jira_analysis_completed",
                {
                    "total_tickets": total_tickets,
                    "avg_ticket_size": avg_ticket_size,
                    "completion_rate": completion_rate,
                    "velocity": velocity
                }
            )
        
        return JiraAnalytics(
            total_tickets=total_tickets,
            avg_ticket_size=round(avg_ticket_size, 2),
            completion_rate=round(completion_rate, 2),
            avg_cycle_time_days=round(avg_cycle_time, 2),
            velocity=round(velocity, 2),
            bottlenecks=bottlenecks,
            common_labels=common_labels,
            status_distribution=status_distribution
        )
    
    def _generate_mock_tickets(self, project_key: str, count: int) -> List[JiraTicket]:
        """Generate mock Jira tickets for testing."""
        tickets = []
        statuses = ['To Do', 'In Progress', 'In Review', 'Done']
        issue_types = ['Story', 'Task', 'Bug', 'Epic']
        priorities = ['High', 'Medium', 'Low']
        
        for i in range(count):
            created = datetime.now() - timedelta(days=count - i)
            resolved = created + timedelta(days=5) if i % 3 == 0 else None
            
            ticket = JiraTicket(
                key=f"{project_key}-{1000 + i}",
                summary=f"Mock ticket {i}: Implement feature X",
                description=f"This is a mock ticket for testing purposes",
                issue_type=issue_types[i % len(issue_types)],
                status=statuses[i % len(statuses)],
                priority=priorities[i % len(priorities)],
                story_points=float((i % 8) + 1),  # 1-8 story points
                created=created,
                updated=datetime.now() - timedelta(days=1),
                resolved=resolved,
                assignee=f"user-{i % 5}",
                labels=[f"label-{i % 3}", "mock"],
                components=[f"component-{i % 4}"],
                sprint=f"Sprint {(i // 10) + 1}"
            )
            tickets.append(ticket)
        
        return tickets
    
    async def get_sprint_metrics(
        self,
        project_key: str,
        sprint_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific sprint.
        
        Args:
            project_key: Jira project key
            sprint_name: Optional sprint name (defaults to current sprint)
            
        Returns:
            Dictionary with sprint metrics
        """
        tickets = await self.fetch_tickets(project_key, days_back=30)
        
        # Filter by sprint if specified
        if sprint_name:
            tickets = [t for t in tickets if t.sprint == sprint_name]
        
        analytics = await self.analyze_ticket_patterns(tickets)
        
        return {
            "sprint": sprint_name or "Current",
            "total_tickets": analytics.total_tickets,
            "story_points_completed": sum(
                t.story_points for t in tickets
                if t.story_points and t.resolved
            ),
            "story_points_planned": sum(
                t.story_points for t in tickets
                if t.story_points
            ),
            "completion_rate": analytics.completion_rate,
            "avg_cycle_time_days": analytics.avg_cycle_time_days,
            "bottlenecks": analytics.bottlenecks
        }

