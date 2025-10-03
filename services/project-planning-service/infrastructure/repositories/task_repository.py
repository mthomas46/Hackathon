"""
Task Repository - Data access layer for tasks
==============================================

Provides CRUD operations and queries for task entities.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid

from ...domain.entities.task import Task, TaskStatus, TaskType
from ..database.models import TaskModel


class TaskRepository:
    """Repository for Task entity persistence."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create(self, task: Task) -> Task:
        """Create a new task in the database."""
        task_model = TaskModel(
            id=task.id or str(uuid.uuid4()),
            title=task.title,
            description=task.description,
            task_type=task.task_type.value if isinstance(task.task_type, TaskType) else task.task_type,
            status=task.status.value if isinstance(task.status, TaskStatus) else task.status,
            assigned_to=task.assigned_to,
            assigned_by=task.assigned_by,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            story_points=task.story_points,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            feature_id=task.feature_id,
            depends_on=task.depends_on,
            blocks=task.blocks,
            created_by=task.created_by,
            tags=task.tags,
            attachments=task.attachments,
            comments=task.comments
        )
        
        self.session.add(task_model)
        self.session.flush()
        
        task.id = task_model.id
        return task
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Retrieve task by ID."""
        task_model = self.session.query(TaskModel).filter(
            TaskModel.id == task_id
        ).first()
        
        if not task_model:
            return None
        
        return self._model_to_entity(task_model)
    
    def update(self, task: Task) -> Task:
        """Update existing task."""
        task_model = self.session.query(TaskModel).filter(
            TaskModel.id == task.id
        ).first()
        
        if not task_model:
            raise ValueError(f"Task with ID {task.id} not found")
        
        # Update fields
        task_model.title = task.title
        task_model.description = task.description
        task_model.task_type = task.task_type.value if isinstance(task.task_type, TaskType) else task.task_type
        task_model.status = task.status.value if isinstance(task.status, TaskStatus) else task.status
        task_model.assigned_to = task.assigned_to
        task_model.assigned_by = task.assigned_by
        task_model.estimated_hours = task.estimated_hours
        task_model.actual_hours = task.actual_hours
        task_model.story_points = task.story_points
        task_model.planned_start = task.planned_start
        task_model.planned_end = task.planned_end
        task_model.actual_start = task.actual_start
        task_model.actual_end = task.actual_end
        task_model.depends_on = task.depends_on
        task_model.blocks = task.blocks
        task_model.tags = task.tags
        task_model.attachments = task.attachments
        task_model.comments = task.comments
        
        self.session.flush()
        return task
    
    def delete(self, task_id: str) -> bool:
        """Delete task by ID."""
        task_model = self.session.query(TaskModel).filter(
            TaskModel.id == task_id
        ).first()
        
        if not task_model:
            return False
        
        self.session.delete(task_model)
        self.session.flush()
        return True
    
    def find_by_feature(self, feature_id: str) -> List[Task]:
        """Find all tasks for a feature."""
        task_models = self.session.query(TaskModel).filter(
            TaskModel.feature_id == feature_id
        ).all()
        return [self._model_to_entity(tm) for tm in task_models]
    
    def find_by_assignee(self, user_id: str) -> List[Task]:
        """Find all tasks assigned to a user."""
        task_models = self.session.query(TaskModel).filter(
            TaskModel.assigned_to == user_id
        ).all()
        return [self._model_to_entity(tm) for tm in task_models]
    
    def find_by_status(self, status: TaskStatus) -> List[Task]:
        """Find tasks by status."""
        status_value = status.value if isinstance(status, TaskStatus) else status
        task_models = self.session.query(TaskModel).filter(
            TaskModel.status == status_value
        ).all()
        return [self._model_to_entity(tm) for tm in task_models]
    
    def find_overdue(self) -> List[Task]:
        """Find overdue tasks."""
        from datetime import datetime
        task_models = self.session.query(TaskModel).filter(
            and_(
                TaskModel.planned_end < datetime.now(),
                TaskModel.status.notin_(['done', 'cancelled'])
            )
        ).all()
        return [self._model_to_entity(tm) for tm in task_models]
    
    def _model_to_entity(self, model: TaskModel) -> Task:
        """Convert database model to domain entity."""
        return Task(
            id=model.id,
            title=model.title,
            description=model.description,
            task_type=TaskType(model.task_type) if isinstance(model.task_type, str) else model.task_type,
            status=TaskStatus(model.status) if isinstance(model.status, str) else model.status,
            assigned_to=model.assigned_to,
            assigned_by=model.assigned_by,
            estimated_hours=model.estimated_hours,
            actual_hours=model.actual_hours,
            story_points=model.story_points,
            planned_start=model.planned_start,
            planned_end=model.planned_end,
            actual_start=model.actual_start,
            actual_end=model.actual_end,
            feature_id=model.feature_id,
            depends_on=model.depends_on or [],
            blocks=model.blocks or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            tags=model.tags or [],
            attachments=model.attachments or [],
            comments=model.comments or []
        )

