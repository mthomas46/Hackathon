"""
Generic Ticket Entity for PM Tool Integration
==============================================

Normalized ticket representation across different PM tools.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class TicketType(Enum):
    """Type of ticket/issue."""
    STORY = "story"
    TASK = "task"
    BUG = "bug"
    EPIC = "epic"
    SUBTASK = "subtask"


class TicketStatus(Enum):
    """Normalized ticket status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TicketPriority(Enum):
    """Ticket priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Ticket:
    """
    Normalized ticket entity for cross-platform integration.
    
    This entity provides a common representation for tickets/issues
    across Jira, Linear, Asana, and other PM tools.
    """
    
    # Identity
    id: str
    external_id: str  # ID in source system (e.g., "PROJ-123")
    source: str  # "jira", "linear", "asana"
    
    # Core fields
    title: str
    description: str = ""
    ticket_type: TicketType = TicketType.TASK
    status: TicketStatus = TicketStatus.TODO
    priority: TicketPriority = TicketPriority.MEDIUM
    
    # Assignment
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    reporter_id: Optional[str] = None
    reporter_name: Optional[str] = None
    
    # Estimation
    story_points: Optional[float] = None
    estimated_hours: Optional[float] = None
    time_spent_hours: Optional[float] = None
    
    # Relationships
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    
    # Source-specific data
    source_data: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    # Sync metadata
    last_synced_at: Optional[datetime] = None
    sync_status: str = "pending"  # pending, synced, error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'source': self.source,
            'title': self.title,
            'description': self.description,
            'ticket_type': self.ticket_type.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'assignee_id': self.assignee_id,
            'assignee_name': self.assignee_name,
            'story_points': self.story_points,
            'estimated_hours': self.estimated_hours,
            'labels': self.labels,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None
        }


@dataclass
class FieldMapping:
    """
    Field mapping configuration between internal and external systems.
    """
    source: str  # "jira", "linear", "asana"
    internal_field: str
    external_field: str
    transform: Optional[str] = None  # Optional transformation function name
    
    def apply_transform(self, value: Any) -> Any:
        """Apply transformation to value."""
        if not self.transform:
            return value
        
        # Built-in transformations
        if self.transform == "status_to_internal":
            return self._status_to_internal(value)
        elif self.transform == "status_to_external":
            return self._status_to_external(value)
        elif self.transform == "priority_to_internal":
            return self._priority_to_internal(value)
        elif self.transform == "priority_to_external":
            return self._priority_to_external(value)
        
        return value
    
    def _status_to_internal(self, external_status: str) -> TicketStatus:
        """Map external status to internal status."""
        status_map = {
            # Jira
            'To Do': TicketStatus.TODO,
            'In Progress': TicketStatus.IN_PROGRESS,
            'In Review': TicketStatus.IN_REVIEW,
            'Done': TicketStatus.DONE,
            'Blocked': TicketStatus.BLOCKED,
            'Cancelled': TicketStatus.CANCELLED,
            # Linear
            'Backlog': TicketStatus.TODO,
            'Started': TicketStatus.IN_PROGRESS,
            'Completed': TicketStatus.DONE,
            'Canceled': TicketStatus.CANCELLED,
            # Asana
            'incomplete': TicketStatus.TODO,
            'complete': TicketStatus.DONE
        }
        return status_map.get(external_status, TicketStatus.TODO)
    
    def _status_to_external(self, internal_status: TicketStatus) -> str:
        """Map internal status to external status based on source."""
        if self.source == "jira":
            return {
                TicketStatus.TODO: 'To Do',
                TicketStatus.IN_PROGRESS: 'In Progress',
                TicketStatus.IN_REVIEW: 'In Review',
                TicketStatus.DONE: 'Done',
                TicketStatus.BLOCKED: 'Blocked',
                TicketStatus.CANCELLED: 'Cancelled'
            }.get(internal_status, 'To Do')
        elif self.source == "linear":
            return {
                TicketStatus.TODO: 'Backlog',
                TicketStatus.IN_PROGRESS: 'Started',
                TicketStatus.DONE: 'Completed',
                TicketStatus.CANCELLED: 'Canceled'
            }.get(internal_status, 'Backlog')
        elif self.source == "asana":
            return 'complete' if internal_status == TicketStatus.DONE else 'incomplete'
        
        return str(internal_status.value)
    
    def _priority_to_internal(self, external_priority: str) -> TicketPriority:
        """Map external priority to internal priority."""
        priority_map = {
            # Jira
            'Lowest': TicketPriority.LOW,
            'Low': TicketPriority.LOW,
            'Medium': TicketPriority.MEDIUM,
            'High': TicketPriority.HIGH,
            'Highest': TicketPriority.URGENT,
            # Linear
            '1': TicketPriority.URGENT,
            '2': TicketPriority.HIGH,
            '3': TicketPriority.MEDIUM,
            '4': TicketPriority.LOW,
            # Asana (no native priority, using custom fields)
            'urgent': TicketPriority.URGENT,
            'high': TicketPriority.HIGH,
            'medium': TicketPriority.MEDIUM,
            'low': TicketPriority.LOW
        }
        return priority_map.get(external_priority, TicketPriority.MEDIUM)
    
    def _priority_to_external(self, internal_priority: TicketPriority) -> str:
        """Map internal priority to external priority."""
        if self.source == "jira":
            return {
                TicketPriority.LOW: 'Low',
                TicketPriority.MEDIUM: 'Medium',
                TicketPriority.HIGH: 'High',
                TicketPriority.URGENT: 'Highest'
            }.get(internal_priority, 'Medium')
        elif self.source == "linear":
            return {
                TicketPriority.URGENT: '1',
                TicketPriority.HIGH: '2',
                TicketPriority.MEDIUM: '3',
                TicketPriority.LOW: '4'
            }.get(internal_priority, '3')
        elif self.source == "asana":
            return internal_priority.value
        
        return str(internal_priority.value)


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    tickets_synced: int = 0
    tickets_created: int = 0
    tickets_updated: int = 0
    tickets_failed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'tickets_synced': self.tickets_synced,
            'tickets_created': self.tickets_created,
            'tickets_updated': self.tickets_updated,
            'tickets_failed': self.tickets_failed,
            'errors': self.errors,
            'warnings': self.warnings,
            'duration_seconds': self.duration_seconds
        }

