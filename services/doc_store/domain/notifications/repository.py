"""Notifications repository for data access operations.

Handles notification and webhook data operations.
"""
from typing import List, Optional, Dict, Any
from ...core.repository import BaseRepository
from ...db.queries import execute_query
from ...core.entities import NotificationEvent, Webhook, WebhookDelivery


class NotificationsRepository(BaseRepository[NotificationEvent]):
    """Repository for notification data access."""

    def __init__(self):
        super().__init__("notification_events")

    def _row_to_entity(self, row: Dict[str, Any]) -> NotificationEvent:
        """Convert database row to NotificationEvent entity."""
        return NotificationEvent(
            id=row['id'],
            event_type=row['event_type'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            user_id=row.get('user_id'),
            metadata=row.get('metadata', {}),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def _entity_to_row(self, entity: NotificationEvent) -> Dict[str, Any]:
        """Convert NotificationEvent entity to database row."""
        return {
            'id': entity.id,
            'event_type': entity.event_type,
            'entity_type': entity.entity_type,
            'entity_id': entity.entity_id,
            'user_id': entity.user_id,
            'metadata': entity.metadata,
            'created_at': entity.created_at.isoformat(),
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None
        }

    def get_webhooks_for_event(self, event_type: str) -> List[Webhook]:
        """Get webhooks that should receive a specific event type."""
        rows = execute_query("""
            SELECT * FROM webhooks
            WHERE is_active = 1 AND events LIKE ?
        """, (f'%{event_type}%',), fetch_all=True)

        return [self._webhook_row_to_entity(row) for row in rows]

    def _webhook_row_to_entity(self, row: Dict[str, Any]) -> Webhook:
        """Convert webhook database row to entity."""
        return Webhook(
            id=row['id'],
            name=row['name'],
            url=row['url'],
            secret=row.get('secret'),
            events=row.get('events', []),
            headers=row.get('headers', {}),
            is_active=row.get('is_active', True),
            retry_count=row.get('retry_count', 3),
            timeout_seconds=row.get('timeout_seconds', 30),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def get_event_history(self, event_type: Optional[str] = None, entity_type: Optional[str] = None,
                         entity_id: Optional[str] = None, limit: int = 100) -> List[NotificationEvent]:
        """Get notification event history with filtering."""
        conditions = []
        params = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)

        if entity_id:
            conditions.append("entity_id = ?")
            params.append(entity_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)

        rows = execute_query(query, params, fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_notification_stats(self, days_back: int = 7) -> Dict[str, Any]:
        """Get notification statistics."""
        from datetime import datetime, timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        # Event counts by type
        event_rows = execute_query("""
            SELECT event_type, COUNT(*) as count
            FROM notification_events
            WHERE created_at >= ?
            GROUP BY event_type
        """, (cutoff_date,), fetch_all=True)

        event_stats = {row['event_type']: row['count'] for row in event_rows}

        # Webhook delivery stats
        delivery_rows = execute_query("""
            SELECT status, COUNT(*) as count
            FROM webhook_deliveries
            WHERE created_at >= ?
            GROUP BY status
        """, (cutoff_date,), fetch_all=True)

        delivery_stats = {row['status']: row['count'] for row in delivery_rows}

        return {
            "period_days": days_back,
            "events_by_type": event_stats,
            "deliveries_by_status": delivery_stats,
            "total_events": sum(event_stats.values()),
            "total_deliveries": sum(delivery_stats.values())
        }
