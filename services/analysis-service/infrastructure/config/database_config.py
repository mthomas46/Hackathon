"""Database configuration management."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""

    # SQLite configuration
    sqlite_path: str = ":memory:"

    # PostgreSQL configuration (for future use)
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_database: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None

    # Connection pool settings
    max_connections: int = 10
    min_connections: int = 1
    connection_timeout: int = 30

    # Migration settings
    enable_migrations: bool = True
    migration_table: str = "schema_migrations"

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables."""
        return cls(
            sqlite_path=os.getenv('ANALYSIS_DB_PATH', ':memory:'),
            postgres_host=os.getenv('POSTGRES_HOST'),
            postgres_port=int(os.getenv('POSTGRES_PORT', '5432')),
            postgres_database=os.getenv('POSTGRES_DB'),
            postgres_user=os.getenv('POSTGRES_USER'),
            postgres_password=os.getenv('POSTGRES_PASSWORD'),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '10')),
            min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '1')),
            connection_timeout=int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            enable_migrations=os.getenv('DB_ENABLE_MIGRATIONS', 'true').lower() == 'true'
        )

    def get_connection_string(self, db_type: str = 'sqlite') -> str:
        """Get database connection string."""
        if db_type == 'sqlite':
            return f"sqlite:///{self.sqlite_path}"
        elif db_type == 'postgresql':
            if not all([self.postgres_host, self.postgres_database, self.postgres_user]):
                raise ValueError("PostgreSQL configuration incomplete")
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.sqlite_path != ":memory:" or not self.postgres_host

    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL."""
        return self.postgres_host is not None

    def get_pool_config(self) -> dict:
        """Get connection pool configuration."""
        return {
            'max_connections': self.max_connections,
            'min_connections': self.min_connections,
            'connection_timeout': self.connection_timeout
        }

    def validate(self) -> list[str]:
        """Validate configuration."""
        errors = []

        if self.is_sqlite():
            if not self.sqlite_path:
                errors.append("SQLite path must be specified")
        elif self.is_postgresql():
            if not self.postgres_host:
                errors.append("PostgreSQL host must be specified")
            if not self.postgres_database:
                errors.append("PostgreSQL database must be specified")
            if not self.postgres_user:
                errors.append("PostgreSQL user must be specified")
        else:
            errors.append("Either SQLite path or PostgreSQL configuration must be provided")

        if self.max_connections < self.min_connections:
            errors.append("Max connections must be >= min connections")

        if self.connection_timeout < 1:
            errors.append("Connection timeout must be >= 1 second")

        return errors
