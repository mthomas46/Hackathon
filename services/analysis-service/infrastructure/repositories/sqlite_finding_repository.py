"""SQLite implementation of finding repository."""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities import Finding, FindingId, DocumentId, Severity
from .finding_repository import FindingRepository


class SQLiteFindingRepository(FindingRepository):
    """SQLite implementation of finding repository."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize SQLite repository."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    location TEXT,  -- JSON
                    suggestion TEXT,
                    confidence REAL NOT NULL,
                    metadata TEXT,  -- JSON
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_document ON findings(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_analysis ON findings(analysis_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_category ON findings(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_resolved ON findings(resolved_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_created ON findings(created_at)")

    async def save(self, finding: Finding) -> None:
        """Save a finding to SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO findings
                (id, document_id, analysis_id, title, description, severity, category,
                 location, suggestion, confidence, metadata, created_at, resolved_at, resolved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                finding.id.value,
                finding.document_id.value,
                finding.analysis_id,
                finding.title,
                finding.description,
                finding.severity.value,
                finding.category,
                json.dumps(finding.location) if finding.location else None,
                finding.suggestion,
                finding.confidence,
                json.dumps(finding.metadata) if finding.metadata else None,
                finding.created_at.isoformat(),
                finding.resolved_at.isoformat() if finding.resolved_at else None,
                finding.resolved_by
            ))

    async def get_by_id(self, finding_id: str) -> Optional[Finding]:
        """Get finding by ID from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_id, title, description, severity, category,
                       location, suggestion, confidence, metadata, created_at, resolved_at, resolved_by
                FROM findings WHERE id = ?
            """, (finding_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_finding(row)

    async def get_by_document_id(self, document_id: str) -> List[Finding]:
        """Get all findings for a document from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_id, title, description, severity, category,
                       location, suggestion, confidence, metadata, created_at, resolved_at, resolved_by
                FROM findings WHERE document_id = ? ORDER BY created_at DESC
            """, (document_id,))

            return [self._row_to_finding(row) for row in cursor.fetchall()]

    async def get_all(self) -> List[Finding]:
        """Get all findings from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_id, title, description, severity, category,
                       location, suggestion, confidence, metadata, created_at, resolved_at, resolved_by
                FROM findings ORDER BY created_at DESC
            """)

            return [self._row_to_finding(row) for row in cursor.fetchall()]

    async def get_by_category(self, category: str) -> List[Finding]:
        """Get findings by category from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_id, title, description, severity, category,
                       location, suggestion, confidence, metadata, created_at, resolved_at, resolved_by
                FROM findings WHERE category = ? ORDER BY created_at DESC
            """, (category,))

            return [self._row_to_finding(row) for row in cursor.fetchall()]

    async def get_unresolved(self) -> List[Finding]:
        """Get all unresolved findings from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_id, title, description, severity, category,
                       location, suggestion, confidence, metadata, created_at, resolved_at, resolved_by
                FROM findings WHERE resolved_at IS NULL ORDER BY created_at DESC
            """)

            return [self._row_to_finding(row) for row in cursor.fetchall()]

    async def delete(self, finding_id: str) -> bool:
        """Delete a finding from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM findings WHERE id = ?", (finding_id,))
            return cursor.rowcount > 0

    def _row_to_finding(self, row) -> Finding:
        """Convert database row to Finding entity."""
        id, document_id, analysis_id, title, description, severity, category, \
        location_json, suggestion, confidence, metadata_json, created_at_str, \
        resolved_at_str, resolved_by = row

        # Parse dates
        created_at = datetime.fromisoformat(created_at_str)
        resolved_at = datetime.fromisoformat(resolved_at_str) if resolved_at_str else None

        # Parse JSON fields
        location = json.loads(location_json) if location_json else None
        metadata = json.loads(metadata_json) if metadata_json else {}

        # Create value objects
        finding_id = FindingId(id)
        doc_id = DocumentId(document_id)
        severity_enum = Severity(severity)

        return Finding(
            id=finding_id,
            document_id=doc_id,
            analysis_id=analysis_id,
            title=title,
            description=description,
            severity=severity_enum,
            category=category,
            location=location,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata,
            created_at=created_at,
            resolved_at=resolved_at,
            resolved_by=resolved_by
        )
