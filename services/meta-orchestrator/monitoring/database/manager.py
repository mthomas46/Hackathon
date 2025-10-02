"""SQLite database manager for configuration monitoring"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .models import (
    ConfigurationSnapshot, ConfigurationDrift, ServiceHealth,
    Alert, DriftPattern
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite database manager for configuration monitoring"""

    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Configuration snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuration_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    UNIQUE(service_name, config_hash)
                )
            ''')

            # Configuration drift table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuration_drift (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    drift_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expected_value TEXT,
                    actual_value TEXT,
                    timestamp TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT,
                    resolution_action TEXT
                )
            ''')

            # Service health table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    health_status TEXT NOT NULL,
                    response_time REAL,
                    error_message TEXT,
                    timestamp TEXT NOT NULL,
                    endpoint TEXT,
                    status_code INTEGER
                )
            ''')

            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at TEXT,
                    acknowledged_by TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT,
                    metadata TEXT
                )
            ''')

            # Drift patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS drift_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    description TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 0,
                    affected_configs TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    UNIQUE(service_name, pattern_type)
                )
            ''')

            conn.commit()
            logger.info(f"✅ Database initialized at {self.db_path}")

    # Configuration Snapshot Methods
    def save_configuration_snapshot(self, snapshot: ConfigurationSnapshot) -> int:
        """Save a configuration snapshot"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO configuration_snapshots
                (service_name, config_hash, config_data, timestamp, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                snapshot.service_name,
                snapshot.config_hash,
                json.dumps(snapshot.config_data),
                snapshot.timestamp.isoformat(),
                snapshot.source
            ))

            snapshot_id = cursor.lastrowid
            conn.commit()
            return snapshot_id

    def get_configuration_snapshots(self, service_name: str, limit: int = 50) -> List[ConfigurationSnapshot]:
        """Get configuration snapshots for a service"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, service_name, config_hash, config_data, timestamp, source
                FROM configuration_snapshots
                WHERE service_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (service_name, limit))

            snapshots = []
            for row in cursor.fetchall():
                snapshot = ConfigurationSnapshot(
                    id=row[0],
                    service_name=row[1],
                    config_hash=row[2],
                    config_data=json.loads(row[3]),
                    timestamp=datetime.fromisoformat(row[4]),
                    source=row[5]
                )
                snapshots.append(snapshot)

            return snapshots

    def get_latest_snapshot(self, service_name: str) -> Optional[ConfigurationSnapshot]:
        """Get the latest configuration snapshot for a service"""
        snapshots = self.get_configuration_snapshots(service_name, limit=1)
        return snapshots[0] if snapshots else None

    # Configuration Drift Methods
    def save_configuration_drift(self, drift: ConfigurationDrift) -> int:
        """Save a configuration drift record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO configuration_drift
                (service_name, drift_type, severity, description, expected_value,
                 actual_value, timestamp, resolved, resolved_at, resolution_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                drift.service_name,
                drift.drift_type,
                drift.severity,
                drift.description,
                json.dumps(drift.expected_value) if drift.expected_value else None,
                json.dumps(drift.actual_value) if drift.actual_value else None,
                drift.timestamp.isoformat(),
                drift.resolved,
                drift.resolved_at.isoformat() if drift.resolved_at else None,
                drift.resolution_action
            ))

            drift_id = cursor.lastrowid
            conn.commit()
            return drift_id

    def get_configuration_drift(self, service_name: Optional[str] = None,
                               resolved: Optional[bool] = None,
                               limit: int = 100) -> List[ConfigurationDrift]:
        """Get configuration drift records"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = '''
                SELECT id, service_name, drift_type, severity, description,
                       expected_value, actual_value, timestamp, resolved,
                       resolved_at, resolution_action
                FROM configuration_drift
                WHERE 1=1
            '''
            params = []

            if service_name:
                query += ' AND service_name = ?'
                params.append(service_name)

            if resolved is not None:
                query += ' AND resolved = ?'
                params.append(resolved)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            drifts = []
            for row in cursor.fetchall():
                drift = ConfigurationDrift(
                    id=row[0],
                    service_name=row[1],
                    drift_type=row[2],
                    severity=row[3],
                    description=row[4],
                    expected_value=json.loads(row[5]) if row[5] else None,
                    actual_value=json.loads(row[6]) if row[6] else None,
                    timestamp=datetime.fromisoformat(row[7]),
                    resolved=bool(row[8]),
                    resolved_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    resolution_action=row[10]
                )
                drifts.append(drift)

            return drifts

    def resolve_drift(self, drift_id: int, resolution_action: str) -> bool:
        """Mark a drift as resolved"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE configuration_drift
                SET resolved = TRUE, resolved_at = ?, resolution_action = ?
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), resolution_action, drift_id))

            success = cursor.rowcount > 0
            conn.commit()
            return success

    # Service Health Methods
    def save_service_health(self, health: ServiceHealth) -> int:
        """Save a service health record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO service_health
                (service_name, health_status, response_time, error_message,
                 timestamp, endpoint, status_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                health.service_name,
                health.health_status,
                health.response_time,
                health.error_message,
                health.timestamp.isoformat(),
                health.endpoint,
                health.status_code
            ))

            health_id = cursor.lastrowid
            conn.commit()
            return health_id

    def get_service_health_history(self, service_name: str,
                                  hours: int = 24) -> List[ServiceHealth]:
        """Get service health history for the last N hours"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            cursor.execute('''
                SELECT id, service_name, health_status, response_time,
                       error_message, timestamp, endpoint, status_code
                FROM service_health
                WHERE service_name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (service_name, cutoff_time.isoformat()))

            health_records = []
            for row in cursor.fetchall():
                health = ServiceHealth(
                    id=row[0],
                    service_name=row[1],
                    health_status=row[2],
                    response_time=row[3],
                    error_message=row[4],
                    timestamp=datetime.fromisoformat(row[5]),
                    endpoint=row[6],
                    status_code=row[7]
                )
                health_records.append(health)

            return health_records

    def get_current_health_status(self, service_name: Optional[str] = None) -> Dict[str, ServiceHealth]:
        """Get current health status for services"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if service_name:
                cursor.execute('''
                    SELECT id, service_name, health_status, response_time,
                           error_message, timestamp, endpoint, status_code
                    FROM service_health
                    WHERE service_name = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (service_name,))
            else:
                # Get latest health for each service
                cursor.execute('''
                    SELECT h1.id, h1.service_name, h1.health_status, h1.response_time,
                           h1.error_message, h1.timestamp, h1.endpoint, h1.status_code
                    FROM service_health h1
                    INNER JOIN (
                        SELECT service_name, MAX(timestamp) as max_timestamp
                        FROM service_health
                        GROUP BY service_name
                    ) h2 ON h1.service_name = h2.service_name
                        AND h1.timestamp = h2.max_timestamp
                ''')

            health_status = {}
            for row in cursor.fetchall():
                health = ServiceHealth(
                    id=row[0],
                    service_name=row[1],
                    health_status=row[2],
                    response_time=row[3],
                    error_message=row[4],
                    timestamp=datetime.fromisoformat(row[5]),
                    endpoint=row[6],
                    status_code=row[7]
                )
                health_status[health.service_name] = health

            return health_status

    # Alert Methods
    def save_alert(self, alert: Alert) -> int:
        """Save an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO alerts
                (alert_type, severity, service_name, title, message, timestamp,
                 acknowledged, acknowledged_at, acknowledged_by, resolved,
                 resolved_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_type,
                alert.severity,
                alert.service_name,
                alert.title,
                alert.message,
                alert.timestamp.isoformat(),
                alert.acknowledged,
                alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                alert.acknowledged_by,
                alert.resolved,
                alert.resolved_at.isoformat() if alert.resolved_at else None,
                json.dumps(alert.metadata)
            ))

            alert_id = cursor.lastrowid
            conn.commit()
            return alert_id

    def get_alerts(self, service_name: Optional[str] = None,
                  resolved: Optional[bool] = None,
                  acknowledged: Optional[bool] = None,
                  limit: int = 50) -> List[Alert]:
        """Get alerts with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = '''
                SELECT id, alert_type, severity, service_name, title, message,
                       timestamp, acknowledged, acknowledged_at, acknowledged_by,
                       resolved, resolved_at, metadata
                FROM alerts
                WHERE 1=1
            '''
            params = []

            if service_name:
                query += ' AND service_name = ?'
                params.append(service_name)

            if resolved is not None:
                query += ' AND resolved = ?'
                params.append(resolved)

            if acknowledged is not None:
                query += ' AND acknowledged = ?'
                params.append(acknowledged)

            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            alerts = []
            for row in cursor.fetchall():
                alert = Alert(
                    id=row[0],
                    alert_type=row[1],
                    severity=row[2],
                    service_name=row[3],
                    title=row[4],
                    message=row[5],
                    timestamp=datetime.fromisoformat(row[6]),
                    acknowledged=bool(row[7]),
                    acknowledged_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    acknowledged_by=row[9],
                    resolved=bool(row[10]),
                    resolved_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    metadata=json.loads(row[12]) if row[12] else {}
                )
                alerts.append(alert)

            return alerts

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE alerts
                SET acknowledged = TRUE, acknowledged_at = ?, acknowledged_by = ?
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), acknowledged_by, alert_id))

            success = cursor.rowcount > 0
            conn.commit()
            return success

    def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE alerts
                SET resolved = TRUE, resolved_at = ?
                WHERE id = ?
            ''', (datetime.utcnow().isoformat(), alert_id))

            success = cursor.rowcount > 0
            conn.commit()
            return success

    # Drift Pattern Methods
    def save_drift_pattern(self, pattern: DriftPattern) -> int:
        """Save or update a drift pattern"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO drift_patterns
                (service_name, pattern_type, frequency, impact, description,
                 first_seen, last_seen, occurrence_count, affected_configs, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.service_name,
                pattern.pattern_type,
                pattern.frequency,
                pattern.impact,
                pattern.description,
                pattern.first_seen.isoformat(),
                pattern.last_seen.isoformat(),
                pattern.occurrence_count,
                json.dumps(pattern.affected_configs),
                json.dumps(pattern.recommendations)
            ))

            pattern_id = cursor.lastrowid
            conn.commit()
            return pattern_id

    def get_drift_patterns(self, service_name: Optional[str] = None) -> List[DriftPattern]:
        """Get drift patterns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if service_name:
                cursor.execute('''
                    SELECT id, service_name, pattern_type, frequency, impact, description,
                           first_seen, last_seen, occurrence_count, affected_configs, recommendations
                    FROM drift_patterns
                    WHERE service_name = ?
                    ORDER BY last_seen DESC
                ''', (service_name,))
            else:
                cursor.execute('''
                    SELECT id, service_name, pattern_type, frequency, impact, description,
                           first_seen, last_seen, occurrence_count, affected_configs, recommendations
                    FROM drift_patterns
                    ORDER BY last_seen DESC
                ''')

            patterns = []
            for row in cursor.fetchall():
                pattern = DriftPattern(
                    id=row[0],
                    service_name=row[1],
                    pattern_type=row[2],
                    frequency=row[3],
                    impact=row[4],
                    description=row[5],
                    first_seen=datetime.fromisoformat(row[6]),
                    last_seen=datetime.fromisoformat(row[7]),
                    occurrence_count=row[8],
                    affected_configs=json.loads(row[9]),
                    recommendations=json.loads(row[10])
                )
                patterns.append(pattern)

            return patterns

    # Analytics Methods
    def get_drift_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get drift statistics for analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Total drift incidents
            cursor.execute('''
                SELECT COUNT(*) FROM configuration_drift
                WHERE timestamp >= ?
            ''', (cutoff_date.isoformat(),))
            total_drift = cursor.fetchone()[0]

            # Drift by severity
            cursor.execute('''
                SELECT severity, COUNT(*) FROM configuration_drift
                WHERE timestamp >= ?
                GROUP BY severity
            ''', (cutoff_date.isoformat(),))
            severity_counts = dict(cursor.fetchall())

            # Drift by service
            cursor.execute('''
                SELECT service_name, COUNT(*) FROM configuration_drift
                WHERE timestamp >= ?
                GROUP BY service_name
                ORDER BY COUNT(*) DESC
            ''', (cutoff_date.isoformat(),))
            service_counts = dict(cursor.fetchall())

            # Unresolved drift
            cursor.execute('''
                SELECT COUNT(*) FROM configuration_drift
                WHERE resolved = FALSE AND timestamp >= ?
            ''', (cutoff_date.isoformat(),))
            unresolved_drift = cursor.fetchone()[0]

            return {
                'total_drift_incidents': total_drift,
                'severity_breakdown': severity_counts,
                'service_breakdown': service_counts,
                'unresolved_drift': unresolved_drift,
                'analysis_period_days': days
            }

    def get_health_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get health statistics for analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Health status distribution
            cursor.execute('''
                SELECT health_status, COUNT(*) FROM service_health
                WHERE timestamp >= ?
                GROUP BY health_status
            ''', (cutoff_time.isoformat(),))
            health_distribution = dict(cursor.fetchall())

            # Average response times by service
            cursor.execute('''
                SELECT service_name, AVG(response_time) as avg_response
                FROM service_health
                WHERE timestamp >= ? AND response_time IS NOT NULL
                GROUP BY service_name
                ORDER BY avg_response DESC
            ''', (cutoff_time.isoformat(),))
            response_times = dict(cursor.fetchall())

            # Service availability (percentage of healthy checks)
            cursor.execute('''
                SELECT
                    service_name,
                    ROUND(
                        (SUM(CASE WHEN health_status = 'healthy' THEN 1 ELSE 0 END) * 100.0) /
                        COUNT(*), 2
                    ) as availability_percentage
                FROM service_health
                WHERE timestamp >= ?
                GROUP BY service_name
                ORDER BY availability_percentage DESC
            ''', (cutoff_time.isoformat(),))
            availability = dict(cursor.fetchall())

            return {
                'health_distribution': health_distribution,
                'average_response_times': response_times,
                'service_availability': availability,
                'analysis_period_hours': hours
            }

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old monitoring data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old snapshots (keep last 10 per service)
            cursor.execute('''
                DELETE FROM configuration_snapshots
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY service_name ORDER BY timestamp DESC
                        ) as rn
                        FROM configuration_snapshots
                    ) WHERE rn <= 10
                ) AND timestamp < ?
            ''', (cutoff_date.isoformat(),))

            # Delete old health records
            cursor.execute('''
                DELETE FROM service_health
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))

            # Delete old resolved alerts
            cursor.execute('''
                DELETE FROM alerts
                WHERE resolved = TRUE AND timestamp < ?
            ''', (cutoff_date.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"🧹 Cleaned up {deleted_count} old monitoring records")
            return deleted_count
