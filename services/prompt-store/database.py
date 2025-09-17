"""Database management for Prompt Store service."""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import hashlib
import json

# Import models - handle both relative and absolute imports for different loading contexts
try:
    from .models import (
        Prompt, PromptVersion, ABTest, ABTestResult, PromptUsage,
        PromptAnalytics, PromptTemplate, UserSession
    )
except ImportError:
    try:
        from models import (
            Prompt, PromptVersion, ABTest, ABTestResult, PromptUsage,
            PromptAnalytics, PromptTemplate, UserSession
        )
    except ImportError:
        # Fallback for when loaded via importlib
        import sys
        import os
        current_dir = os.path.dirname(__file__)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from models import (
            Prompt, PromptVersion, ABTest, ABTestResult, PromptUsage,
            PromptAnalytics, PromptTemplate, UserSession
        )


class PromptStoreDatabase:
    """SQLite database manager for Prompt Store."""

    def __init__(self, db_path: str = "prompt_store.db"):
        """Initialize database connection and create tables."""
        self.db_path = db_path
        self._init_database()
        self._create_indexes()

    def _init_database(self):
        """Create all database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    content TEXT NOT NULL,
                    variables TEXT,  -- JSON array
                    tags TEXT,      -- JSON array
                    is_active BOOLEAN DEFAULT 1,
                    is_template BOOLEAN DEFAULT 0,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    parent_id TEXT,
                    FOREIGN KEY (parent_id) REFERENCES prompts(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    variables TEXT,
                    change_summary TEXT,
                    change_type TEXT DEFAULT 'update',
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_tests (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    prompt_a_id TEXT NOT NULL,
                    prompt_b_id TEXT NOT NULL,
                    test_metric TEXT DEFAULT 'response_quality',
                    is_active BOOLEAN DEFAULT 1,
                    traffic_split REAL DEFAULT 0.5,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    target_audience TEXT,  -- JSON
                    created_by TEXT NOT NULL,
                    FOREIGN KEY (prompt_a_id) REFERENCES prompts(id),
                    FOREIGN KEY (prompt_b_id) REFERENCES prompts(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    id TEXT PRIMARY KEY,
                    test_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    sample_size INTEGER NOT NULL,
                    confidence_level REAL DEFAULT 0.0,
                    statistical_significance BOOLEAN DEFAULT 0,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES ab_tests(id),
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_usage (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    session_id TEXT,
                    user_id TEXT,
                    service_name TEXT NOT NULL,
                    operation TEXT DEFAULT 'generate',
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    response_time_ms REAL,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_analytics (
                    prompt_id TEXT PRIMARY KEY,
                    total_usage INTEGER DEFAULT 0,
                    avg_response_time_ms REAL DEFAULT 0.0,
                    avg_input_tokens REAL DEFAULT 0.0,
                    avg_output_tokens REAL DEFAULT 0.0,
                    success_rate REAL DEFAULT 0.0,
                    last_used TIMESTAMP,
                    performance_score REAL DEFAULT 0.0,
                    user_satisfaction REAL DEFAULT 0.0,
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    template_content TEXT NOT NULL,
                    required_variables TEXT,  -- JSON array
                    optional_variables TEXT,  -- JSON array
                    tags TEXT,      -- JSON array
                    is_active BOOLEAN DEFAULT 1,
                    usage_count INTEGER DEFAULT 0,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    session_id TEXT NOT NULL,
                    ab_assignments TEXT,  -- JSON
                    preferences TEXT,     -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _create_indexes(self):
        """Create database indexes for performance."""
        with sqlite3.connect(self.db_path) as conn:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category)",
                "CREATE INDEX IF NOT EXISTS idx_prompts_active ON prompts(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_prompts_created_by ON prompts(created_by)",
                "CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt_id ON prompt_versions(prompt_id)",
                "CREATE INDEX IF NOT EXISTS idx_ab_tests_active ON ab_tests(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_ab_test_results_test_id ON ab_test_results(test_id)",
                "CREATE INDEX IF NOT EXISTS idx_prompt_usage_prompt_id ON prompt_usage(prompt_id)",
                "CREATE INDEX IF NOT EXISTS idx_prompt_usage_created_at ON prompt_usage(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)"
            ]

            for index in indexes:
                conn.execute(index)

    def _generate_id(self) -> str:
        """Generate unique ID."""
        return hashlib.md5(f"{datetime.now(timezone.utc).isoformat()}{os.urandom(8).hex()}".encode()).hexdigest()[:12]

    # ============================================================================
    # SHARED DATABASE UTILITIES - Eliminating redundant patterns
    # ============================================================================

    def _get_connection(self):
        """Shared database connection - eliminates repeated sqlite3.connect calls."""
        return sqlite3.connect(self.db_path)

    def _serialize_json(self, data):
        """Shared JSON serialization - eliminates repeated json.dumps calls."""
        return json.dumps(data) if data is not None else None

    def _deserialize_json(self, data):
        """Shared JSON deserialization - eliminates repeated json.loads calls."""
        return json.loads(data) if data else []

    def _get_prompt_columns(self):
        """Shared column list - eliminates repeated column definitions."""
        return "id, name, category, description, content, variables, tags, is_active, is_template, created_by, created_at, updated_at, version, parent_id"

    # ============================================================================
    # PROMPT CRUD OPERATIONS
    # ============================================================================

    def create_prompt(self, prompt: Prompt) -> Prompt:
        """Create a new prompt."""
        prompt.id = self._generate_id()  # FURTHER OPTIMIZED: Using shared ID generation
        prompt.created_at = datetime.now(timezone.utc)
        prompt.updated_at = datetime.now(timezone.utc)

        with self._get_connection() as conn:  # FURTHER OPTIMIZED: Using shared connection
            conn.execute(f"""
                INSERT INTO prompts ({self._get_prompt_columns()})  # FURTHER OPTIMIZED: Using shared columns
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt.id,
                prompt.name,
                prompt.category,
                prompt.description,
                prompt.content,
                self._serialize_json(prompt.variables),  # FURTHER OPTIMIZED: Using shared JSON serialization
                self._serialize_json(prompt.tags),  # FURTHER OPTIMIZED: Using shared JSON serialization
                prompt.is_active,
                prompt.is_template,
                prompt.created_by,
                prompt.created_at.isoformat(),
                prompt.updated_at.isoformat(),
                prompt.version,
                prompt.parent_id
            ))

            # Create initial version
            self._create_version(prompt.id, prompt.version, prompt.content,
                               prompt.variables, "Initial version", prompt.created_by,
                               "create")

        return prompt

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get prompt by ID."""
        with self._get_connection() as conn:  # FURTHER OPTIMIZED: Using shared connection
            row = conn.execute(f"""
                SELECT {self._get_prompt_columns()}  # FURTHER OPTIMIZED: Using shared columns
                FROM prompts WHERE id = ?
            """, (prompt_id,)).fetchone()

            if row:
                return Prompt(
                    id=row[0],
                    name=row[1],
                    category=row[2],
                    description=row[3],
                    content=row[4],
                    variables=self._deserialize_json(row[5]),  # FURTHER OPTIMIZED: Using shared JSON deserialization
                    tags=self._deserialize_json(row[6]),  # FURTHER OPTIMIZED: Using shared JSON deserialization
                    is_active=bool(row[7]),
                    is_template=bool(row[8]),
                    created_by=row[9],
                    created_at=datetime.fromisoformat(row[10]),
                    updated_at=datetime.fromisoformat(row[11]),
                    version=row[12],
                    parent_id=row[13]
                )
        return None

    def get_prompt_by_name(self, category: str, name: str) -> Optional[Prompt]:
        """Get prompt by category and name."""
        with self._get_connection() as conn:  # FURTHER OPTIMIZED: Using shared connection
            row = conn.execute(f"""
                SELECT {self._get_prompt_columns()}  # FURTHER OPTIMIZED: Using shared columns
                FROM prompts WHERE category = ? AND name = ? AND is_active = 1
            """, (category, name)).fetchone()

            if row:
                return Prompt(
                    id=row[0],
                    name=row[1],
                    category=row[2],
                    description=row[3],
                    content=row[4],
                    variables=self._deserialize_json(row[5]),  # FURTHER OPTIMIZED: Using shared JSON deserialization
                    tags=self._deserialize_json(row[6]),  # FURTHER OPTIMIZED: Using shared JSON deserialization
                    is_active=bool(row[7]),
                    is_template=bool(row[8]),
                    created_by=row[9],
                    created_at=datetime.fromisoformat(row[10]),
                    updated_at=datetime.fromisoformat(row[11]),
                    version=row[12],
                    parent_id=row[13]
                )
        return None

    def list_prompts(self, filters: Optional[Dict[str, Any]] = None,
                    limit: int = 50, offset: int = 0) -> Tuple[List[Prompt], int]:
        """List prompts with optional filters."""
        query = f"""
            SELECT {self._get_prompt_columns()}  # FURTHER OPTIMIZED: Using shared columns
            FROM prompts WHERE 1=1
        """
        params = []
        total_count = 0

        # Apply filters
        if filters:
            if 'category' in filters:
                query += " AND category = ?"
                params.append(filters['category'])

            if 'tags' in filters and filters['tags']:
                tag_conditions = " OR ".join(["tags LIKE ?" for _ in filters['tags']])
                query += f" AND ({tag_conditions})"
                params.extend([f"%{tag}%" for tag in filters['tags']])

            if 'author' in filters:
                query += " AND created_by = ?"
                params.append(filters['author'])

            if 'is_active' in filters:
                query += " AND is_active = ?"
                params.append(filters['is_active'])

            if 'min_performance' in filters:
                query += """
                    AND id IN (
                        SELECT prompt_id FROM prompt_analytics
                        WHERE performance_score >= ?
                    )
                """
                params.append(filters['min_performance'])

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query})"
        with self._get_connection() as conn:  # FURTHER OPTIMIZED: Using shared connection
            total_count = conn.execute(count_query, params).fetchone()[0]

        # Apply pagination
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # Execute query
        with self._get_connection() as conn:  # FURTHER OPTIMIZED: Using shared connection
            rows = conn.execute(query, params).fetchall()

        prompts = []
        for row in rows:
            prompts.append(Prompt(
                id=row[0],
                name=row[1],
                category=row[2],
                description=row[3],
                content=row[4],
                variables=self._deserialize_json(row[5]),  # FURTHER OPTIMIZED: Using shared JSON deserialization
                tags=self._deserialize_json(row[6]),  # FURTHER OPTIMIZED: Using shared JSON deserialization
                is_active=bool(row[7]),
                is_template=bool(row[8]),
                created_by=row[9],
                created_at=datetime.fromisoformat(row[10]),
                updated_at=datetime.fromisoformat(row[11]),
                version=row[12],
                parent_id=row[13]
            ))

        return prompts, total_count

    def update_prompt(self, prompt_id: str, updates: Dict[str, Any], updated_by: str) -> Optional[Prompt]:
        """Update an existing prompt."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        # Create version before updating
        change_summary = updates.get('change_summary', 'Updated prompt')
        self._create_version(prompt_id, prompt.version, prompt.content,
                           prompt.variables, change_summary, updated_by, "update")

        # Apply updates
        update_fields = ["updated_at = ?", "version = version + 1"]
        update_values = [datetime.now(timezone.utc).isoformat(), prompt_id]

        update_map = {
            'name': 'name = ?',
            'category': 'category = ?',
            'description': 'description = ?',
            'content': 'content = ?',
            'variables': 'variables = ?',
            'tags': 'tags = ?',
            'is_active': 'is_active = ?',
            'is_template': 'is_template = ?'
        }

        for field, sql in update_map.items():
            if field in updates:
                update_fields.append(sql)
                if field in ['variables', 'tags']:
                    update_values.append(json.dumps(updates[field]))
                else:
                    update_values.append(updates[field])

                # Update the prompt object
                setattr(prompt, field, updates[field])

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                UPDATE prompts
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, update_values)

        prompt.version += 1
        prompt.updated_at = datetime.now(timezone.utc)
        return prompt

    def delete_prompt(self, prompt_id: str, deleted_by: str) -> bool:
        """Soft delete a prompt."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return False

        # Create final version
        self._create_version(prompt_id, prompt.version, prompt.content,
                           prompt.variables, "Prompt deleted", deleted_by, "delete")

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("UPDATE prompts SET is_active = 0 WHERE id = ?", (prompt_id,))
            return result.rowcount > 0


    # ============================================================================
    # VERSION MANAGEMENT
    # ============================================================================

    def _create_version(self, prompt_id: str, version: int, content: str,
                       variables: List[str], change_summary: str, created_by: str,
                       change_type: str = "update"):
        """Create a new version record."""
        version_id = self._generate_id()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO prompt_versions (
                    id, prompt_id, version, content, variables,
                    change_summary, change_type, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (version_id, prompt_id, version, content, json.dumps(variables),
                  change_summary, change_type, created_by))



    # ============================================================================
    # A/B TESTING
    # ============================================================================

    def create_ab_test(self, test: ABTest) -> ABTest:
        """Create a new A/B test."""
        test.id = self._generate_id()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ab_tests (
                    id, name, description, prompt_a_id, prompt_b_id, test_metric,
                    is_active, traffic_split, start_date, end_date, target_audience, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test.id,
                test.name,
                test.description,
                test.prompt_a_id,
                test.prompt_b_id,
                test.test_metric,
                test.is_active,
                test.traffic_split,
                test.start_date.isoformat(),
                test.end_date.isoformat() if test.end_date else None,
                json.dumps(test.target_audience) if test.target_audience else None,
                test.created_by
            ))

        return test

    def get_ab_test(self, test_id: str) -> Optional[ABTest]:
        """Get A/B test by ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT id, name, description, prompt_a_id, prompt_b_id, test_metric,
                       is_active, traffic_split, start_date, end_date, target_audience, created_by
                FROM ab_tests WHERE id = ?
            """, (test_id,)).fetchone()

            if row:
                return ABTest(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    prompt_a_id=row[3],
                    prompt_b_id=row[4],
                    test_metric=row[5],
                    is_active=bool(row[6]),
                    traffic_split=row[7],
                    start_date=datetime.fromisoformat(row[8]),
                    end_date=datetime.fromisoformat(row[9]) if row[9] else None,
                    target_audience=json.loads(row[10]) if row[10] else None,
                    created_by=row[11]
                )
        return None

    def list_ab_tests(self, active_only: bool = True) -> List[ABTest]:
        """List A/B tests."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT id, name, description, prompt_a_id, prompt_b_id, test_metric, is_active, traffic_split, start_date, end_date, target_audience, created_by FROM ab_tests"
            if active_only:
                query += " WHERE is_active = 1"

            rows = conn.execute(query).fetchall()

        tests = []
        for row in rows:
            tests.append(ABTest(
                id=row[0],
                name=row[1],
                description=row[2],
                prompt_a_id=row[3],
                prompt_b_id=row[4],
                test_metric=row[5],
                is_active=bool(row[6]),
                traffic_split=row[7],
                start_date=datetime.fromisoformat(row[8]),
                end_date=datetime.fromisoformat(row[9]) if row[9] else None,
                target_audience=json.loads(row[10]) if row[10] else None,
                created_by=row[11]
            ))

        return tests

    def select_prompt_for_test(self, test_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """Select a prompt for A/B testing."""
        import random

        test = self.get_ab_test(test_id)
        if not test or not test.is_active:
            return None

        # For now, simple random selection (could be enhanced with user segmentation)
        return test.prompt_b_id if random.random() < test.traffic_split else test.prompt_a_id


    # ============================================================================
    # ANALYTICS AND MONITORING
    # ============================================================================

    def log_prompt_usage(self, usage: PromptUsage):
        """Log prompt usage for analytics."""
        usage.id = self._generate_id()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO prompt_usage (
                    id, prompt_id, session_id, user_id, service_name, operation,
                    input_tokens, output_tokens, response_time_ms, success,
                    error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage.id,
                usage.prompt_id,
                usage.session_id,
                usage.user_id,
                usage.service_name,
                usage.operation,
                usage.input_tokens,
                usage.output_tokens,
                usage.response_time_ms,
                usage.success,
                usage.error_message,
                json.dumps(usage.metadata) if usage.metadata else None
            ))

            # Update analytics summary
            conn.execute("""
                INSERT OR REPLACE INTO prompt_analytics (
                    prompt_id, total_usage, avg_response_time_ms, avg_input_tokens,
                    avg_output_tokens, success_rate, last_used, performance_score
                )
                SELECT
                    prompt_id,
                    COUNT(*) as total_usage,
                    AVG(response_time_ms) as avg_response_time_ms,
                    AVG(input_tokens) as avg_input_tokens,
                    AVG(output_tokens) as avg_output_tokens,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                    MAX(created_at) as last_used,
                    CASE
                        WHEN AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) > 0.9 THEN 0.9
                        ELSE AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) * 0.9
                    END as performance_score
                FROM prompt_usage
                WHERE prompt_id = ?
                GROUP BY prompt_id
            """, (usage.prompt_id,))

    def get_prompt_analytics(self, prompt_id: str) -> Optional[PromptAnalytics]:
        """Get analytics for a specific prompt."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT prompt_id, total_usage, avg_response_time_ms, avg_input_tokens,
                       avg_output_tokens, success_rate, last_used, performance_score, user_satisfaction
                FROM prompt_analytics WHERE prompt_id = ?
            """, (prompt_id,)).fetchone()

            if row:
                return PromptAnalytics(
                    prompt_id=row[0],
                    total_usage=row[1],
                    avg_response_time_ms=row[2],
                    avg_input_tokens=row[3],
                    avg_output_tokens=row[4],
                    success_rate=row[5],
                    last_used=datetime.fromisoformat(row[6]) if row[6] else None,
                    performance_score=row[7],
                    user_satisfaction=row[8]
                )
        return None

    def get_total_prompts(self) -> int:
        """Get total number of active prompts."""
        with self._get_connection() as conn:  # FURTHER OPTIMIZED: Using shared connection
            result = conn.execute("SELECT COUNT(*) FROM prompts WHERE is_active = 1").fetchone()
            return result[0] if result else 0

    def get_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get overall usage statistics."""
        since_date = datetime.now(timezone.utc) - timedelta(days=days)

        with self._get_connection() as conn:  # FURTHER OPTIMIZED: Using shared connection
            # Total usage
            total_usage = conn.execute("""
                SELECT COUNT(*) FROM prompt_usage
                WHERE created_at >= ?
            """, (since_date.isoformat(),)).fetchone()[0]

            # Top prompts
            top_prompts = conn.execute("""
                SELECT p.name, p.category, COUNT(u.id) as usage_count
                FROM prompt_usage u
                JOIN prompts p ON u.prompt_id = p.id
                WHERE u.created_at >= ?
                GROUP BY u.prompt_id
                ORDER BY usage_count DESC
                LIMIT 10
            """, (since_date.isoformat(),)).fetchall()

            # Success rate
            success_stats = conn.execute("""
                SELECT
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                    COUNT(*) as total_requests
                FROM prompt_usage
                WHERE created_at >= ?
            """, (since_date.isoformat(),)).fetchone()

            return {
                'total_usage': total_usage,
                'success_rate': success_stats[0] or 0.0,
                'total_requests': success_stats[1] or 0,
                'top_prompts': [
                    {'name': row[0], 'category': row[1], 'usage_count': row[2]}
                    for row in top_prompts
                ],
                'period_days': days
            }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def migrate_from_yaml(self, yaml_path: str, migrated_by: str = "system"):
        """Migrate prompts from YAML configuration to database."""
        try:
            import yaml
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)

            migrated_count = 0

            # Process prompts by category
            for category, prompts in config.items():
                if category.startswith('_'):  # Skip special sections
                    continue

                if not isinstance(prompts, dict):
                    continue

                for prompt_name, prompt_data in prompts.items():
                    # Check if prompt already exists
                    existing = self.get_prompt_by_name(category, prompt_name)
                    if existing:
                        continue

                    # Create new prompt from YAML data
                    if isinstance(prompt_data, str):
                        content = prompt_data
                        variables = self._extract_variables(content)
                        description = ""
                    else:
                        content = prompt_data.get('content', '')
                        variables = prompt_data.get('variables', self._extract_variables(content))
                        description = prompt_data.get('description', '')

                    prompt = Prompt(
                        name=prompt_name,
                        category=category,
                        description=description,
                        content=content,
                        variables=variables,
                        tags=[category],
                        created_by=migrated_by
                    )

                    self.create_prompt(prompt)
                    migrated_count += 1

            return migrated_count

        except Exception as e:
            from services.shared.monitoring.logging import fire_and_forget
            from services.shared.core.constants_new import ServiceNames
            fire_and_forget("error", f"Migration error: {e}", ServiceNames.PROMPT_STORE)
            return 0

    def _extract_variables(self, content: str) -> List[str]:
        """Extract template variables from prompt content."""
        from services.shared.utilities import extract_variables
        return extract_variables(content)

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old usage data."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        with sqlite3.connect(self.db_path) as conn:
            deleted_count = conn.execute("""
                DELETE FROM prompt_usage
                WHERE created_at < ?
            """, (cutoff_date.isoformat(),)).rowcount

        return deleted_count
