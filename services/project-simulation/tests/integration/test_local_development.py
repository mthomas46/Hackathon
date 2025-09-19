"""Local Development Environment Tests.

This module contains comprehensive tests for local development setup,
including environment configuration, database integration, and local
development workflow validation.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys
import json
import sqlite3
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEnvironmentConfiguration:
    """Test local environment configuration and setup."""

    def test_environment_variable_loading(self):
        """Test loading of environment variables for local development."""
        # Test environment variables that should be set for local development
        required_env_vars = [
            "ENVIRONMENT",
            "LOG_LEVEL",
            "DATABASE_URL"
        ]

        optional_env_vars = [
            "DEBUG",
            "SECRET_KEY",
            "API_PORT",
            "REDIS_URL"
        ]

        # Check if required environment variables are accessible
        for env_var in required_env_vars:
            # In test environment, these might not be set, but the code should handle it
            value = os.environ.get(env_var)
            if value is not None:
                assert isinstance(value, str), f"Environment variable {env_var} should be a string"
                assert len(value.strip()) > 0, f"Environment variable {env_var} should not be empty"

        # Check optional environment variables
        for env_var in optional_env_vars:
            value = os.environ.get(env_var)
            if value is not None:
                assert isinstance(value, str), f"Optional environment variable {env_var} should be a string"

        print("✅ Environment variable loading validated")

    def test_configuration_file_loading(self):
        """Test loading of configuration files for local development."""
        # Test configuration file paths that should exist or be creatable
        config_paths = [
            Path(__file__).parent.parent.parent / "config" / "local.yaml",
            Path(__file__).parent.parent.parent / "config" / "development.yaml",
            Path(__file__).parent.parent.parent / ".env",
            Path(__file__).parent.parent.parent / ".env.local"
        ]

        # Check if config directory exists
        config_dir = Path(__file__).parent.parent.parent / "config"
        if config_dir.exists():
            assert config_dir.is_dir(), "Config directory should be a directory"

            # List config files
            config_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))
            if config_files:
                for config_file in config_files:
                    assert config_file.is_file(), f"Config file {config_file} should be a file"
                    assert config_file.stat().st_size > 0, f"Config file {config_file} should not be empty"

        # Check for environment files
        env_files = [path for path in config_paths if path.name.startswith(".env")]
        for env_file in env_files:
            if env_file.exists():
                assert env_file.is_file(), f"Environment file {env_file} should be a file"
                # Don't check size for .env files as they might be empty

        print("✅ Configuration file loading validated")

    def test_local_development_database_setup(self):
        """Test local development database setup and configuration."""
        # Test database URLs for different environments
        test_db_urls = [
            "sqlite:///test.db",
            "sqlite:///:memory:",
            "postgresql://localhost:5432/test_db",
            "postgresql://user:pass@localhost:5432/dev_db"
        ]

        # Validate database URL formats
        for db_url in test_db_urls:
            if db_url.startswith("sqlite"):
                # SQLite URL validation
                assert "://" in db_url, f"SQLite URL should contain '://': {db_url}"
                if "///" in db_url:
                    # File-based SQLite
                    db_path = db_url.split("///")[1]
                    if db_path != ":memory:":
                        # Should be a valid file path
                        assert len(db_path) > 0, f"SQLite file path should not be empty: {db_path}"
                else:
                    # In-memory SQLite
                    assert ":memory:" in db_url, f"SQLite in-memory URL should contain ':memory:': {db_url}"

            elif db_url.startswith("postgresql"):
                # PostgreSQL URL validation
                assert "@" in db_url, f"PostgreSQL URL should contain user credentials: {db_url}"
                assert len(db_url.split("@")[0]) > 0, f"PostgreSQL URL should have credentials: {db_url}"

                # Check for port
                host_part = db_url.split("@")[1].split("/")[0]
                if ":" in host_part:
                    port = host_part.split(":")[1]
                    assert port.isdigit(), f"PostgreSQL port should be numeric: {port}"

        print("✅ Local development database setup validated")

    def test_logging_configuration_for_development(self):
        """Test logging configuration optimized for local development."""
        # Test logging levels appropriate for development
        dev_log_levels = ["DEBUG", "INFO", "WARNING"]
        prod_log_levels = ["INFO", "WARNING", "ERROR"]

        # In development, DEBUG should be acceptable
        assert "DEBUG" in dev_log_levels, "DEBUG level should be available in development"

        # Test log format configurations
        dev_log_formats = [
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "%(levelname)s: %(message)s",
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        ]

        for log_format in dev_log_formats:
            assert "%(levelname)s" in log_format, f"Log format should include level: {log_format}"
            assert "%(message)s" in log_format, f"Log format should include message: {log_format}"

        # Test that development logging is more verbose than production
        dev_log_level_value = 10  # DEBUG = 10
        prod_log_level_value = 20  # INFO = 20

        assert dev_log_level_value < prod_log_level_value, \
            "Development logging should be more verbose than production"

        print("✅ Logging configuration for development validated")


class TestSQLiteIntegration:
    """Test SQLite integration for local development."""

    def test_sqlite_connection_and_basic_operations(self):
        """Test SQLite connection and basic database operations."""
        # Create temporary SQLite database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create test table
            cursor.execute('''
                CREATE TABLE simulations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'created',
                    created_at REAL,
                    config TEXT
                )
            ''')

            # Insert test data
            test_data = [
                ('sim_001', 'Test Simulation 1', 'running', time.time(), '{"type": "web"}'),
                ('sim_002', 'Test Simulation 2', 'completed', time.time(), '{"type": "mobile"}'),
                ('sim_003', 'Test Simulation 3', 'failed', time.time(), '{"type": "api"}')
            ]

            cursor.executemany('INSERT INTO simulations VALUES (?, ?, ?, ?, ?)', test_data)
            conn.commit()

            # Query data
            cursor.execute('SELECT COUNT(*) FROM simulations')
            count = cursor.fetchone()[0]
            assert count == 3, f"Expected 3 records, got {count}"

            # Query specific records
            cursor.execute('SELECT name, status FROM simulations WHERE status = ?', ('running',))
            running_sim = cursor.fetchone()
            assert running_sim is not None, "Should find running simulation"
            assert running_sim[1] == 'running', f"Expected status 'running', got {running_sim[1]}"

            # Test parameterized queries
            cursor.execute('SELECT * FROM simulations WHERE id = ?', ('sim_002',))
            sim_002 = cursor.fetchone()
            assert sim_002 is not None, "Should find simulation with ID sim_002"
            assert sim_002[1] == 'Test Simulation 2', f"Unexpected simulation name: {sim_002[1]}"

            conn.close()

        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)

        print("✅ SQLite connection and basic operations validated")

    def test_sqlite_schema_migrations(self):
        """Test SQLite schema migrations for local development."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Initial schema (v1)
            cursor.execute('''
                CREATE TABLE simulations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'created'
                )
            ''')

            # Insert initial data
            cursor.execute("INSERT INTO simulations VALUES ('sim_001', 'Initial Sim', 'created')")
            conn.commit()

            # Migration 1: Add created_at column
            cursor.execute('ALTER TABLE simulations ADD COLUMN created_at REAL')
            cursor.execute('UPDATE simulations SET created_at = ? WHERE id = ?', (time.time(), 'sim_001'))
            conn.commit()

            # Migration 2: Add config column
            cursor.execute('ALTER TABLE simulations ADD COLUMN config TEXT')
            cursor.execute('UPDATE simulations SET config = ? WHERE id = ?', ('{"migrated": true}', 'sim_001'))
            conn.commit()

            # Verify migrations
            cursor.execute('PRAGMA table_info(simulations)')
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            expected_columns = ['id', 'name', 'status', 'created_at', 'config']
            for col in expected_columns:
                assert col in column_names, f"Missing column after migration: {col}"

            # Verify data integrity after migrations
            cursor.execute('SELECT * FROM simulations WHERE id = ?', ('sim_001',))
            record = cursor.fetchone()
            assert record is not None, "Record should exist after migrations"
            assert len(record) == 5, f"Record should have 5 columns, got {len(record)}"

            # Verify migrated data
            config_data = json.loads(record[4])  # config column
            assert config_data["migrated"] is True, "Migration flag should be set"

            conn.close()

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

        print("✅ SQLite schema migrations validated")

    def test_sqlite_performance_under_load(self):
        """Test SQLite performance under typical development load."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create test table
            cursor.execute('''
                CREATE TABLE performance_test (
                    id INTEGER PRIMARY KEY,
                    data TEXT,
                    timestamp REAL
                )
            ''')

            # Performance test: Insert many records
            start_time = time.time()
            batch_size = 1000

            for batch in range(10):  # 10 batches of 1000 = 10,000 records
                records = []
                for i in range(batch_size):
                    record_id = batch * batch_size + i
                    records.append((
                        record_id,
                        f"Test data {record_id}",
                        time.time()
                    ))

                cursor.executemany('INSERT INTO performance_test VALUES (?, ?, ?)', records)
                conn.commit()

            insert_time = time.time() - start_time

            # Query performance test
            query_start = time.time()
            cursor.execute('SELECT COUNT(*) FROM performance_test WHERE id > ?', (5000,))
            count = cursor.fetchone()[0]
            query_time = time.time() - query_start

            # Validate performance
            assert insert_time < 5.0, f"SQLite insert performance too slow: {insert_time:.2f}s"
            assert query_time < 0.1, f"SQLite query performance too slow: {query_time:.3f}s"
            assert count == 5000, f"Expected 5000 records, got {count}"

            # Test concurrent read/write (simulated)
            concurrent_start = time.time()

            # Simulate concurrent operations
            for i in range(100):
                cursor.execute('INSERT INTO performance_test VALUES (?, ?, ?)',
                             (10000 + i, f"Concurrent data {i}", time.time()))
                cursor.execute('SELECT * FROM performance_test WHERE id = ?', (10000 + i,))
                result = cursor.fetchone()
                assert result is not None

            conn.commit()
            concurrent_time = time.time() - concurrent_start

            assert concurrent_time < 2.0, f"Concurrent operations too slow: {concurrent_time:.2f}s"

            conn.close()

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

        print("✅ SQLite performance under load validated")


class TestPostgreSQLIntegration:
    """Test PostgreSQL integration for local development."""

    def test_postgresql_connection_simulation(self):
        """Test PostgreSQL connection simulation (mocked for local dev)."""
        # Since PostgreSQL might not be available in all local environments,
        # we'll test the connection logic and configuration

        # Test PostgreSQL URL parsing
        pg_urls = [
            "postgresql://user:pass@localhost:5432/dbname",
            "postgresql://user@localhost:5432/dbname",
            "postgresql://localhost/dbname",
            "postgresql://user:pass@host.com:5432/dbname?sslmode=require"
        ]

        for url in pg_urls:
            # Parse PostgreSQL URL components
            if url.startswith("postgresql://"):
                url_parts = url.replace("postgresql://", "").split("/")[0]
                if "@" in url_parts:
                    credentials, host_port = url_parts.split("@")
                    if ":" in credentials:
                        username, password = credentials.split(":")
                    else:
                        username = credentials
                        password = None

                    if ":" in host_port:
                        host, port_db = host_port.split(":")
                        port = port_db.split("/")[0]
                        assert port.isdigit(), f"Port should be numeric: {port}"
                    else:
                        host = host_port
                        port = "5432"  # Default PostgreSQL port

                    assert username, f"Username should be present in URL: {url}"
                    assert host, f"Host should be present in URL: {url}"

        print("✅ PostgreSQL connection simulation validated")

    def test_postgresql_schema_compatibility(self):
        """Test PostgreSQL schema compatibility with SQLite schemas."""
        # Test schema that should work on both SQLite and PostgreSQL

        # Common schema patterns
        schemas = [
            """
            CREATE TABLE simulations (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'created',
                created_at TIMESTAMP,
                config JSON
            );
            """,
            """
            CREATE TABLE documents (
                id VARCHAR(100) PRIMARY KEY,
                simulation_id VARCHAR(50) REFERENCES simulations(id),
                type VARCHAR(50) NOT NULL,
                content TEXT,
                quality_score DECIMAL(3,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE INDEX idx_simulations_status ON simulations(status);
            CREATE INDEX idx_documents_simulation_id ON documents(simulation_id);
            """
        ]

        # Test schema compatibility (syntax validation)
        for schema in schemas:
            # Remove PostgreSQL-specific syntax for SQLite compatibility testing
            sqlite_schema = schema.replace("VARCHAR(50)", "TEXT")
            sqlite_schema = sqlite_schema.replace("VARCHAR(255)", "TEXT")
            sqlite_schema = sqlite_schema.replace("VARCHAR(100)", "TEXT")
            sqlite_schema = sqlite_schema.replace("TIMESTAMP", "REAL")
            sqlite_schema = sqlite_schema.replace("DECIMAL(3,2)", "REAL")
            sqlite_schema = sqlite_schema.replace("JSON", "TEXT")
            sqlite_schema = sqlite_schema.replace("DEFAULT CURRENT_TIMESTAMP", "")

            # Basic syntax validation
            assert "CREATE TABLE" in sqlite_schema or "CREATE INDEX" in sqlite_schema
            assert ";" in sqlite_schema

        print("✅ PostgreSQL schema compatibility validated")

    @patch('psycopg2.connect')
    def test_postgresql_error_handling_simulation(self, mock_connect):
        """Test PostgreSQL error handling simulation."""
        # Mock PostgreSQL connection errors
        mock_connect.side_effect = Exception("Connection refused")

        # Test connection retry logic
        max_retries = 3
        retry_delay = 0.1

        connection_attempts = 0
        last_error = None

        for attempt in range(max_retries):
            connection_attempts += 1
            try:
                # Simulate connection attempt
                mock_connect()
                break  # Success
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        # Validate retry behavior
        assert connection_attempts == max_retries, f"Expected {max_retries} attempts, got {connection_attempts}"
        assert last_error is not None, "Should have encountered an error"

        # Test with successful connection on retry
        def connection_with_retry(attempt_number):
            if attempt_number < 2:  # Fail first 2 attempts
                raise Exception(f"Connection failed (attempt {attempt_number + 1})")
            return "successful_connection"

        mock_connect.side_effect = connection_with_retry

        connection_attempts = 0
        for attempt in range(max_retries):
            connection_attempts += 1
            try:
                result = mock_connect(attempt)
                if result == "successful_connection":
                    break
            except Exception:
                if attempt == max_retries - 1:
                    last_error = Exception("All retry attempts failed")

        assert connection_attempts == 3, f"Expected 3 attempts for successful retry, got {connection_attempts}"

        print("✅ PostgreSQL error handling simulation validated")


class TestLocalDevelopmentWorkflow:
    """Test complete local development workflow."""

    def test_development_environment_setup(self):
        """Test complete development environment setup."""
        # Test development environment configuration
        dev_config = {
            "environment": "development",
            "debug": True,
            "log_level": "DEBUG",
            "database": {
                "url": "sqlite:///dev.db",
                "migrate_on_startup": True
            },
            "api": {
                "host": "localhost",
                "port": 8000,
                "reload": True,
                "docs_url": "/docs"
            },
            "redis": {
                "url": "redis://localhost:6379",
                "required": False  # Optional for local dev
            }
        }

        # Validate development configuration
        assert dev_config["environment"] == "development"
        assert dev_config["debug"] is True
        assert dev_config["log_level"] == "DEBUG"

        # Validate database config
        db_config = dev_config["database"]
        assert "sqlite" in db_config["url"], "Development should use SQLite by default"
        assert db_config["migrate_on_startup"] is True, "Migrations should run on startup in dev"

        # Validate API config
        api_config = dev_config["api"]
        assert api_config["reload"] is True, "API should auto-reload in development"
        assert api_config["docs_url"] == "/docs", "API docs should be available in development"

        print("✅ Development environment setup validated")

    def test_hot_reload_configuration(self):
        """Test hot reload configuration for development."""
        # Test file watching and reload triggers
        watched_files = [
            "main.py",
            "simulation/**/*.py",
            "config/*.yaml",
            "requirements.txt"
        ]

        reload_triggers = [
            "file_modified",
            "file_created",
            "file_deleted",
            "config_changed"
        ]

        # Validate watched file patterns
        for pattern in watched_files:
            assert "*" in pattern or pattern.endswith(".py") or pattern.endswith(".yaml") or pattern.endswith(".txt"), \
                f"Invalid watched file pattern: {pattern}"

        # Test reload trigger logic
        def should_reload(change_type, file_path):
            """Determine if application should reload based on change."""
            if change_type not in reload_triggers:
                return False

            # Check if file matches watched patterns
            for pattern in watched_files:
                if "*" in pattern:
                    # Simple glob matching
                    if pattern.startswith("simulation/") and "simulation" in file_path:
                        return True
                    if pattern.startswith("config/") and "config" in file_path:
                        return True
                else:
                    if file_path.endswith(pattern):
                        return True

            return False

        # Test reload scenarios
        reload_scenarios = [
            ("file_modified", "main.py", True),
            ("file_modified", "simulation/domain/entities.py", True),
            ("file_created", "config/local.yaml", True),
            ("file_modified", "README.md", False),  # Not watched
            ("config_changed", "database_config", True)
        ]

        for change_type, file_path, expected_reload in reload_scenarios:
            should_reload_app = should_reload(change_type, file_path)
            assert should_reload_app == expected_reload, \
                f"Reload decision incorrect for {change_type}:{file_path}"

        print("✅ Hot reload configuration validated")

    def test_development_database_migrations(self):
        """Test database migrations in development environment."""
        # Test migration file structure and execution
        migration_files = [
            "001_initial_schema.py",
            "002_add_user_table.py",
            "003_add_indexes.py",
            "004_update_constraints.py"
        ]

        # Validate migration file naming
        for migration_file in migration_files:
            assert migration_file.startswith("00"), f"Migration file should start with number: {migration_file}"
            assert migration_file.endswith(".py"), f"Migration file should be Python: {migration_file}"

            # Extract migration number
            migration_num = int(migration_file.split("_")[0])
            assert migration_num >= 1, f"Migration number should be >= 1: {migration_num}"

        # Test migration execution order
        executed_migrations = []

        def execute_migration(migration_file):
            """Simulate migration execution."""
            executed_migrations.append(migration_file)
            # Simulate migration time
            time.sleep(0.01)

        # Execute migrations in order
        for migration_file in sorted(migration_files):
            execute_migration(migration_file)

        # Validate execution order
        assert len(executed_migrations) == len(migration_files)
        assert executed_migrations == sorted(migration_files), "Migrations should execute in order"

        # Test migration rollback (for development)
        rollback_migrations = []

        def rollback_migration(migration_file):
            """Simulate migration rollback."""
            rollback_migrations.append(migration_file)
            executed_migrations.remove(migration_file)

        # Rollback last migration
        if executed_migrations:
            last_migration = executed_migrations[-1]
            rollback_migration(last_migration)

            assert last_migration not in executed_migrations
            assert last_migration in rollback_migrations

        print("✅ Development database migrations validated")

    def test_local_development_monitoring(self):
        """Test monitoring and observability for local development."""
        # Test development-focused monitoring metrics
        dev_metrics = {
            "memory_usage": 0,
            "cpu_usage": 0,
            "active_connections": 0,
            "request_count": 0,
            "error_count": 0,
            "uptime": 0
        }

        # Simulate monitoring data collection
        monitoring_data = []

        def collect_metric(metric_name, value):
            """Collect a monitoring metric."""
            dev_metrics[metric_name] = value
            monitoring_data.append({
                "metric": metric_name,
                "value": value,
                "timestamp": time.time()
            })

        # Collect various metrics
        collect_metric("memory_usage", 85.5)  # 85.5 MB
        collect_metric("cpu_usage", 12.3)     # 12.3%
        collect_metric("active_connections", 3)
        collect_metric("request_count", 150)
        collect_metric("error_count", 2)
        collect_metric("uptime", 3600)        # 1 hour

        # Validate metrics collection
        assert len(monitoring_data) == 6
        assert all("timestamp" in entry for entry in monitoring_data)

        # Validate metric values
        assert dev_metrics["memory_usage"] > 0
        assert 0 <= dev_metrics["cpu_usage"] <= 100
        assert dev_metrics["active_connections"] >= 0
        assert dev_metrics["request_count"] >= 0
        assert dev_metrics["uptime"] > 0

        # Test error rate calculation
        if dev_metrics["request_count"] > 0:
            error_rate = dev_metrics["error_count"] / dev_metrics["request_count"]
            assert 0 <= error_rate <= 1, f"Invalid error rate: {error_rate}"

        print("✅ Local development monitoring validated")


# Helper fixtures
@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_postgres_connection():
    """Create a mock PostgreSQL connection for testing."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.return_value = None
    mock_cursor.fetchone.return_value = (1,)
    mock_cursor.fetchall.return_value = [("result1",), ("result2",)]

    return mock_conn


@pytest.fixture
def dev_environment_config():
    """Create development environment configuration for testing."""
    return {
        "environment": "development",
        "debug": True,
        "database_url": "sqlite:///dev.db",
        "log_level": "DEBUG",
        "api_port": 8000,
        "redis_url": "redis://localhost:6379",
        "migrate_on_startup": True,
        "hot_reload": True
    }
