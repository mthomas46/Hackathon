#!/usr/bin/env python3
"""
Workflow Management Repository

Data access layer for workflow definitions and executions.
Handles storage, retrieval, and search operations.
"""

import json
import sqlite3
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

from services.orchestrator.modules.workflow_management.models import (
    WorkflowDefinition, WorkflowExecution, WorkflowStatus, WorkflowExecutionStatus
)
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class WorkflowRepository:
    """Repository for workflow data operations."""

    def __init__(self, db_path: str = None):
        """Initialize repository with database path."""
        if db_path is None:
            # Default to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            db_path = os.path.join(project_root, "orchestrator_workflows.db")

        self.db_path = db_path
        self._initialize_database()

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Workflow definitions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_definitions (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    status TEXT NOT NULL DEFAULT 'draft',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags TEXT,  -- JSON array
                    parameters TEXT,  -- JSON array
                    actions TEXT,  -- JSON array
                    timeout_seconds INTEGER DEFAULT 300,
                    max_concurrent_actions INTEGER DEFAULT 5,
                    notify_on_completion BOOLEAN DEFAULT 0,
                    notification_channels TEXT,  -- JSON array
                    total_executions INTEGER DEFAULT 0,
                    successful_executions INTEGER DEFAULT 0,
                    failed_executions INTEGER DEFAULT 0,
                    average_execution_time REAL DEFAULT 0.0
                )
            ''')

            # Workflow executions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    initiated_by TEXT NOT NULL,
                    input_parameters TEXT,  -- JSON object
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    execution_time_seconds REAL DEFAULT 0.0,
                    action_results TEXT,  -- JSON object
                    output_data TEXT,  -- JSON object
                    error_message TEXT,
                    current_action TEXT,
                    completed_actions TEXT,  -- JSON array
                    failed_actions TEXT,  -- JSON array
                    FOREIGN KEY (workflow_id) REFERENCES workflow_definitions (workflow_id)
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_definitions(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_created_by ON workflow_definitions(created_by)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_workflow_id ON workflow_executions(workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_status ON workflow_executions(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_initiated_by ON workflow_executions(initiated_by)')

            conn.commit()

            fire_and_forget("info", "Workflow database initialized", ServiceNames.ORCHESTRATOR)

    # Workflow Definition Operations

    def save_workflow_definition(self, workflow: WorkflowDefinition) -> bool:
        """Save or update a workflow definition."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Convert workflow to database format
                workflow_data = workflow.to_dict()

                cursor.execute('''
                    INSERT OR REPLACE INTO workflow_definitions (
                        workflow_id, name, description, version, status, created_by,
                        created_at, updated_at, tags, parameters, actions,
                        timeout_seconds, max_concurrent_actions, notify_on_completion,
                        notification_channels, total_executions, successful_executions,
                        failed_executions, average_execution_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    workflow_data['workflow_id'],
                    workflow_data['name'],
                    workflow_data['description'],
                    workflow_data['version'],
                    workflow_data['status'],
                    workflow_data['created_by'],
                    workflow_data['created_at'],
                    workflow_data['updated_at'],
                    json.dumps(workflow_data['tags']),
                    json.dumps(workflow_data['parameters']),
                    json.dumps(workflow_data['actions']),
                    workflow_data['timeout_seconds'],
                    workflow_data['max_concurrent_actions'],
                    workflow_data['notify_on_completion'],
                    json.dumps(workflow_data['notification_channels']),
                    workflow_data['total_executions'],
                    workflow_data['successful_executions'],
                    workflow_data['failed_executions'],
                    workflow_data['average_execution_time']
                ))

                conn.commit()

                fire_and_forget("info", f"Saved workflow definition: {workflow.workflow_id}", ServiceNames.ORCHESTRATOR)
                return True

        except Exception as e:
            fire_and_forget("error", f"Failed to save workflow definition: {e}", ServiceNames.ORCHESTRATOR)
            return False

    def get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM workflow_definitions WHERE workflow_id = ?', (workflow_id,))
                row = cursor.fetchone()

                if row:
                    # Convert database row to dictionary
                    workflow_data = dict(row)

                    # Parse JSON fields
                    workflow_data['tags'] = json.loads(workflow_data['tags'] or '[]')
                    workflow_data['parameters'] = json.loads(workflow_data['parameters'] or '[]')
                    workflow_data['actions'] = json.loads(workflow_data['actions'] or '[]')
                    workflow_data['notification_channels'] = json.loads(workflow_data['notification_channels'] or '[]')

                    return WorkflowDefinition.from_dict(workflow_data)

        except Exception as e:
            fire_and_forget("error", f"Failed to get workflow definition: {e}", ServiceNames.ORCHESTRATOR)

        return None

    def list_workflow_definitions(self, filters: Dict[str, Any] = None) -> List[WorkflowDefinition]:
        """List workflow definitions with optional filters."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = 'SELECT * FROM workflow_definitions'
                params = []

                # Apply filters
                where_clauses = []
                if filters:
                    if 'status' in filters:
                        where_clauses.append('status = ?')
                        params.append(filters['status'])

                    if 'created_by' in filters:
                        where_clauses.append('created_by = ?')
                        params.append(filters['created_by'])

                    if 'name_contains' in filters:
                        where_clauses.append('name LIKE ?')
                        params.append(f"%{filters['name_contains']}%")

                    if 'tags' in filters:
                        # Check if any of the provided tags are in the workflow's tags
                        tag_conditions = []
                        for tag in filters['tags']:
                            tag_conditions.append('tags LIKE ?')
                            params.append(f'%"{tag}"%')
                        if tag_conditions:
                            where_clauses.append('(' + ' OR '.join(tag_conditions) + ')')

                if where_clauses:
                    query += ' WHERE ' + ' AND '.join(where_clauses)

                # Add ordering
                query += ' ORDER BY updated_at DESC'

                cursor.execute(query, params)
                rows = cursor.fetchall()

                workflows = []
                for row in rows:
                    workflow_data = dict(row)

                    # Parse JSON fields
                    workflow_data['tags'] = json.loads(workflow_data['tags'] or '[]')
                    workflow_data['parameters'] = json.loads(workflow_data['parameters'] or '[]')
                    workflow_data['actions'] = json.loads(workflow_data['actions'] or '[]')
                    workflow_data['notification_channels'] = json.loads(workflow_data['notification_channels'] or '[]')

                    workflows.append(WorkflowDefinition.from_dict(workflow_data))

                return workflows

        except Exception as e:
            fire_and_forget("error", f"Failed to list workflow definitions: {e}", ServiceNames.ORCHESTRATOR)
            return []

    def delete_workflow_definition(self, workflow_id: str) -> bool:
        """Delete a workflow definition."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if workflow has executions
                cursor.execute('SELECT COUNT(*) FROM workflow_executions WHERE workflow_id = ?', (workflow_id,))
                execution_count = cursor.fetchone()[0]

                if execution_count > 0:
                    # Soft delete - mark as archived instead
                    cursor.execute(
                        'UPDATE workflow_definitions SET status = ? WHERE workflow_id = ?',
                        (WorkflowStatus.ARCHIVED.value, workflow_id)
                    )
                else:
                    # Hard delete
                    cursor.execute('DELETE FROM workflow_definitions WHERE workflow_id = ?', (workflow_id,))

                conn.commit()

                fire_and_forget("info", f"Deleted/archived workflow: {workflow_id}", ServiceNames.ORCHESTRATOR)
                return True

        except Exception as e:
            fire_and_forget("error", f"Failed to delete workflow definition: {e}", ServiceNames.ORCHESTRATOR)
            return False

    def search_workflow_definitions(self, query: str, limit: int = 50) -> List[WorkflowDefinition]:
        """Search workflow definitions by name, description, or tags."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                search_pattern = f"%{query}%"

                cursor.execute('''
                    SELECT * FROM workflow_definitions
                    WHERE name LIKE ? OR description LIKE ? OR tags LIKE ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (search_pattern, search_pattern, search_pattern, limit))

                rows = cursor.fetchall()

                workflows = []
                for row in rows:
                    workflow_data = dict(row)

                    # Parse JSON fields
                    workflow_data['tags'] = json.loads(workflow_data['tags'] or '[]')
                    workflow_data['parameters'] = json.loads(workflow_data['parameters'] or '[]')
                    workflow_data['actions'] = json.loads(workflow_data['actions'] or '[]')
                    workflow_data['notification_channels'] = json.loads(workflow_data['notification_channels'] or '[]')

                    workflows.append(WorkflowDefinition.from_dict(workflow_data))

                return workflows

        except Exception as e:
            fire_and_forget("error", f"Failed to search workflow definitions: {e}", ServiceNames.ORCHESTRATOR)
            return []

    # Workflow Execution Operations

    def save_workflow_execution(self, execution: WorkflowExecution) -> bool:
        """Save or update a workflow execution."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                execution_data = execution.to_dict()

                cursor.execute('''
                    INSERT OR REPLACE INTO workflow_executions (
                        execution_id, workflow_id, initiated_by, input_parameters,
                        status, started_at, completed_at, execution_time_seconds,
                        action_results, output_data, error_message, current_action,
                        completed_actions, failed_actions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution_data['execution_id'],
                    execution_data['workflow_id'],
                    execution_data['initiated_by'],
                    json.dumps(execution_data['input_parameters']),
                    execution_data['status'],
                    execution_data['started_at'],
                    execution_data['completed_at'],
                    execution_data['execution_time_seconds'],
                    json.dumps(execution_data['action_results']),
                    json.dumps(execution_data['output_data']),
                    execution_data['error_message'],
                    execution_data['current_action'],
                    json.dumps(execution_data['completed_actions']),
                    json.dumps(execution_data['failed_actions'])
                ))

                conn.commit()

                fire_and_forget("info", f"Saved workflow execution: {execution.execution_id}", ServiceNames.ORCHESTRATOR)
                return True

        except Exception as e:
            fire_and_forget("error", f"Failed to save workflow execution: {e}", ServiceNames.ORCHESTRATOR)
            return False

    def get_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM workflow_executions WHERE execution_id = ?', (execution_id,))
                row = cursor.fetchone()

                if row:
                    execution_data = dict(row)

                    # Parse JSON fields
                    execution_data['input_parameters'] = json.loads(execution_data['input_parameters'] or '{}')
                    execution_data['action_results'] = json.loads(execution_data['action_results'] or '{}')
                    execution_data['output_data'] = json.loads(execution_data['output_data'] or '{}')
                    execution_data['completed_actions'] = json.loads(execution_data['completed_actions'] or '[]')
                    execution_data['failed_actions'] = json.loads(execution_data['failed_actions'] or '[]')

                    # Parse timestamps
                    if execution_data['started_at']:
                        execution_data['started_at'] = datetime.fromisoformat(execution_data['started_at'])
                    if execution_data['completed_at']:
                        execution_data['completed_at'] = datetime.fromisoformat(execution_data['completed_at'])

                    return WorkflowExecution(**execution_data)

        except Exception as e:
            fire_and_forget("error", f"Failed to get workflow execution: {e}", ServiceNames.ORCHESTRATOR)

        return None

    def list_workflow_executions(self, workflow_id: str = None, status: WorkflowExecutionStatus = None,
                               limit: int = 100) -> List[WorkflowExecution]:
        """List workflow executions with optional filters."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = 'SELECT * FROM workflow_executions'
                params = []

                where_clauses = []
                if workflow_id:
                    where_clauses.append('workflow_id = ?')
                    params.append(workflow_id)

                if status:
                    where_clauses.append('status = ?')
                    params.append(status.value)

                if where_clauses:
                    query += ' WHERE ' + ' AND '.join(where_clauses)

                query += ' ORDER BY started_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                executions = []
                for row in rows:
                    execution_data = dict(row)

                    # Parse JSON fields
                    execution_data['input_parameters'] = json.loads(execution_data['input_parameters'] or '{}')
                    execution_data['action_results'] = json.loads(execution_data['action_results'] or '{}')
                    execution_data['output_data'] = json.loads(execution_data['output_data'] or '{}')
                    execution_data['completed_actions'] = json.loads(execution_data['completed_actions'] or '[]')
                    execution_data['failed_actions'] = json.loads(execution_data['failed_actions'] or '[]')

                    # Parse timestamps
                    if execution_data['started_at']:
                        execution_data['started_at'] = datetime.fromisoformat(execution_data['started_at'])
                    if execution_data['completed_at']:
                        execution_data['completed_at'] = datetime.fromisoformat(execution_data['completed_at'])

                    executions.append(WorkflowExecution(**execution_data))

                return executions

        except Exception as e:
            fire_and_forget("error", f"Failed to list workflow executions: {e}", ServiceNames.ORCHESTRATOR)
            return []

    def delete_workflow_execution(self, execution_id: str) -> bool:
        """Delete a workflow execution."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('DELETE FROM workflow_executions WHERE execution_id = ?', (execution_id,))
                conn.commit()

                fire_and_forget("info", f"Deleted workflow execution: {execution_id}", ServiceNames.ORCHESTRATOR)
                return True

        except Exception as e:
            fire_and_forget("error", f"Failed to delete workflow execution: {e}", ServiceNames.ORCHESTRATOR)
            return False

    # Statistics and Analytics

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get comprehensive workflow statistics."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Workflow definitions stats
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_workflows,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_workflows,
                        COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_workflows,
                        AVG(total_executions) as avg_executions_per_workflow
                    FROM workflow_definitions
                ''')
                workflow_stats = dict(cursor.fetchone())

                # Execution stats
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_executions,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_executions,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
                        COUNT(CASE WHEN status = 'running' THEN 1 END) as running_executions,
                        AVG(execution_time_seconds) as avg_execution_time
                    FROM workflow_executions
                ''')
                execution_stats = dict(cursor.fetchone())

                # Success rate
                total_executions = execution_stats.get('total_executions', 0)
                completed_executions = execution_stats.get('completed_executions', 0)

                success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0

                # Most active workflows
                cursor.execute('''
                    SELECT workflow_id, COUNT(*) as execution_count
                    FROM workflow_executions
                    GROUP BY workflow_id
                    ORDER BY execution_count DESC
                    LIMIT 10
                ''')
                most_active = cursor.fetchall()

                return {
                    "workflows": workflow_stats,
                    "executions": execution_stats,
                    "success_rate": success_rate,
                    "most_active_workflows": [dict(row) for row in most_active]
                }

        except Exception as e:
            fire_and_forget("error", f"Failed to get workflow statistics: {e}", ServiceNames.ORCHESTRATOR)
            return {}

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent workflow activity."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT
                        we.execution_id,
                        we.workflow_id,
                        wd.name as workflow_name,
                        we.status,
                        we.started_at,
                        we.completed_at,
                        we.execution_time_seconds,
                        we.initiated_by
                    FROM workflow_executions we
                    LEFT JOIN workflow_definitions wd ON we.workflow_id = wd.workflow_id
                    ORDER BY we.started_at DESC
                    LIMIT ?
                ''', (limit,))

                activity = []
                for row in cursor.fetchall():
                    activity_data = dict(row)
                    if activity_data['started_at']:
                        activity_data['started_at'] = datetime.fromisoformat(activity_data['started_at'])
                    if activity_data['completed_at']:
                        activity_data['completed_at'] = datetime.fromisoformat(activity_data['completed_at'])
                    activity.append(activity_data)

                return activity

        except Exception as e:
            fire_and_forget("error", f"Failed to get recent activity: {e}", ServiceNames.ORCHESTRATOR)
            return []

    # Maintenance operations

    def cleanup_old_executions(self, days_to_keep: int = 30) -> int:
        """Clean up old workflow executions."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

                cursor.execute(
                    'DELETE FROM workflow_executions WHERE started_at < ?',
                    (datetime.fromtimestamp(cutoff_date).isoformat(),)
                )

                deleted_count = cursor.rowcount
                conn.commit()

                fire_and_forget("info", f"Cleaned up {deleted_count} old workflow executions", ServiceNames.ORCHESTRATOR)
                return deleted_count

        except Exception as e:
            fire_and_forget("error", f"Failed to cleanup old executions: {e}", ServiceNames.ORCHESTRATOR)
            return 0

    def optimize_database(self) -> bool:
        """Optimize database performance."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Vacuum database to reclaim space
                cursor.execute('VACUUM')

                # Analyze tables for query optimization
                cursor.execute('ANALYZE workflow_definitions')
                cursor.execute('ANALYZE workflow_executions')

                conn.commit()

                fire_and_forget("info", "Database optimization completed", ServiceNames.ORCHESTRATOR)
                return True

        except Exception as e:
            fire_and_forget("error", f"Failed to optimize database: {e}", ServiceNames.ORCHESTRATOR)
            return False
