"""SQLite implementation of analysis repository."""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities import Analysis, AnalysisId, DocumentId
from ...domain.entities.value_objects import AnalysisType, AnalysisConfiguration
from .analysis_repository import AnalysisRepository


class SQLiteAnalysisRepository(AnalysisRepository):
    """SQLite implementation of analysis repository."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize SQLite repository."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    configuration TEXT NOT NULL,  -- JSON
                    started_at TEXT,
                    completed_at TEXT,
                    result TEXT,  -- JSON
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_document ON analyses(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_type ON analyses(analysis_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at)")

    async def save(self, analysis: Analysis) -> None:
        """Save an analysis to SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO analyses
                (id, document_id, analysis_type, status, configuration,
                 started_at, completed_at, result, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.id.value,
                analysis.document_id.value,
                analysis.analysis_type,
                analysis.status.value,
                json.dumps(analysis.configuration),
                analysis.started_at.isoformat() if analysis.started_at else None,
                analysis.completed_at.isoformat() if analysis.completed_at else None,
                json.dumps(analysis.result) if analysis.result else None,
                analysis.error_message,
                analysis.created_at.isoformat()
            ))

    async def get_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_type, status, configuration,
                       started_at, completed_at, result, error_message, created_at
                FROM analyses WHERE id = ?
            """, (analysis_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_analysis(row)

    async def get_by_document_id(self, document_id: str) -> List[Analysis]:
        """Get all analyses for a document from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_type, status, configuration,
                       started_at, completed_at, result, error_message, created_at
                FROM analyses WHERE document_id = ? ORDER BY created_at DESC
            """, (document_id,))

            return [self._row_to_analysis(row) for row in cursor.fetchall()]

    async def get_all(self) -> List[Analysis]:
        """Get all analyses from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_type, status, configuration,
                       started_at, completed_at, result, error_message, created_at
                FROM analyses ORDER BY created_at DESC
            """)

            return [self._row_to_analysis(row) for row in cursor.fetchall()]

    async def get_by_status(self, status: str) -> List[Analysis]:
        """Get analyses by status from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, document_id, analysis_type, status, configuration,
                       started_at, completed_at, result, error_message, created_at
                FROM analyses WHERE status = ? ORDER BY created_at DESC
            """, (status,))

            return [self._row_to_analysis(row) for row in cursor.fetchall()]

    async def delete(self, analysis_id: str) -> bool:
        """Delete an analysis from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
            return cursor.rowcount > 0

    def _row_to_analysis(self, row) -> Analysis:
        """Convert database row to Analysis entity."""
        id, document_id, analysis_type, status, configuration_json, \
        started_at_str, completed_at_str, result_json, error_message, created_at_str = row

        # Parse dates
        started_at = datetime.fromisoformat(started_at_str) if started_at_str else None
        completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
        created_at = datetime.fromisoformat(created_at_str)

        # Parse JSON fields
        configuration = json.loads(configuration_json) if configuration_json else {}
        result = json.loads(result_json) if result_json else None

        # Create value objects
        analysis_id = AnalysisId(id)
        doc_id = DocumentId(document_id)

        return Analysis(
            id=analysis_id,
            document_id=doc_id,
            analysis_type=analysis_type,
            status=status,
            configuration=configuration,
            started_at=started_at,
            completed_at=completed_at,
            result=result,
            error_message=error_message,
            created_at=created_at
        )
