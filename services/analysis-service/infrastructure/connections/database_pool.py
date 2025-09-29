"""Database Connection Pool - Database-specific connection pooling implementations."""

import asyncio
import sqlite3
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .connection_pool import ConnectionPool, ConnectionPoolConfig, PooledConnection


class DatabaseConnectionPool(ConnectionPool):
    """Base class for database connection pools."""

    def __init__(self, config: ConnectionPoolConfig, connection_string: str):
        """Initialize database connection pool."""
        super().__init__(config)
        self.connection_string = connection_string

    @abstractmethod
    async def create_connection(self) -> Any:
        """Create a database connection."""
        pass

    @abstractmethod
    async def validate_connection(self, connection: Any) -> bool:
        """Validate database connection."""
        pass

    @abstractmethod
    async def close_connection(self, connection: Any) -> None:
        """Close database connection."""
        pass


class SQLiteConnectionPool(DatabaseConnectionPool):
    """SQLite connection pool implementation."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        database_path: str,
        pragmas: Optional[Dict[str, Any]] = None
    ):
        """Initialize SQLite connection pool."""
        connection_string = f"sqlite:///{database_path}"
        super().__init__(config, connection_string)
        self.database_path = database_path
        self.pragmas = pragmas or {
            'foreign_keys': 'ON',
            'journal_mode': 'WAL',
            'synchronous': 'NORMAL',
            'cache_size': '-64000',  # 64MB cache
            'temp_store': 'MEMORY'
        }

    async def create_connection(self) -> sqlite3.Connection:
        """Create SQLite connection."""
        # SQLite connections are not async, so we run in thread pool
        loop = asyncio.get_event_loop()

        def _create_conn():
            conn = sqlite3.connect(
                self.database_path,
                isolation_level=None,  # We'll manage transactions manually
                check_same_thread=False
            )

            # Apply pragmas
            cursor = conn.cursor()
            for pragma, value in self.pragmas.items():
                cursor.execute(f"PRAGMA {pragma} = {value}")
            cursor.close()

            return conn

        return await loop.run_in_executor(None, _create_conn)

    async def validate_connection(self, connection: sqlite3.Connection) -> bool:
        """Validate SQLite connection."""
        try:
            loop = asyncio.get_event_loop()

            def _validate():
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True

            return await loop.run_in_executor(None, _validate)
        except Exception:
            return False

    async def close_connection(self, connection: sqlite3.Connection) -> None:
        """Close SQLite connection."""
        loop = asyncio.get_event_loop()

        def _close():
            try:
                connection.close()
            except Exception:
                pass  # Ignore errors during cleanup

        await loop.run_in_executor(None, _close)

    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a query using a pooled connection."""
        async with self.acquire() as pooled_conn:
            loop = asyncio.get_event_loop()

            def _execute():
                cursor = pooled_conn.connection.cursor()
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                        return cursor.fetchall()
                    else:
                        pooled_conn.connection.commit()
                        return [(cursor.rowcount,)]

                finally:
                    cursor.close()

            return await loop.run_in_executor(None, _execute)

    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets."""
        async with self.acquire() as pooled_conn:
            loop = asyncio.get_event_loop()

            def _execute_many():
                cursor = pooled_conn.connection.cursor()
                try:
                    cursor.executemany(query, params_list)
                    pooled_conn.connection.commit()
                    return cursor.rowcount
                finally:
                    cursor.close()

            return await loop.run_in_executor(None, _execute_many)


class PostgreSQLConnectionPool(DatabaseConnectionPool):
    """PostgreSQL connection pool implementation."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        host: str,
        port: int = 5432,
        database: str = "",
        user: str = "",
        password: str = "",
        ssl_mode: str = "prefer",
        connection_timeout: int = 30
    ):
        """Initialize PostgreSQL connection pool."""
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        super().__init__(config, connection_string)

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.ssl_mode = ssl_mode
        self.connection_timeout = connection_timeout

        # Import psycopg2 here to make it optional
        try:
            import psycopg2
            self.psycopg2 = psycopg2
        except ImportError:
            raise ImportError("psycopg2 is required for PostgreSQL connection pooling")

    async def create_connection(self) -> Any:
        """Create PostgreSQL connection."""
        loop = asyncio.get_event_loop()

        def _create_conn():
            return self.psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                sslmode=self.ssl_mode,
                connect_timeout=self.connection_timeout
            )

        return await loop.run_in_executor(None, _create_conn)

    async def validate_connection(self, connection: Any) -> bool:
        """Validate PostgreSQL connection."""
        try:
            loop = asyncio.get_event_loop()

            def _validate():
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True

            return await loop.run_in_executor(None, _validate)
        except Exception:
            return False

    async def close_connection(self, connection: Any) -> None:
        """Close PostgreSQL connection."""
        loop = asyncio.get_event_loop()

        def _close():
            try:
                connection.close()
            except Exception:
                pass  # Ignore errors during cleanup

        await loop.run_in_executor(None, _close)

    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a query using a pooled connection."""
        async with self.acquire() as pooled_conn:
            loop = asyncio.get_event_loop()

            def _execute():
                cursor = pooled_conn.connection.cursor()
                try:
                    cursor.execute(query, params or ())
                    if query.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    else:
                        pooled_conn.connection.commit()
                        return [(cursor.rowcount,)]

                finally:
                    cursor.close()

            return await loop.run_in_executor(None, _execute)

    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets."""
        async with self.acquire() as pooled_conn:
            loop = asyncio.get_event_loop()

            def _execute_many():
                cursor = pooled_conn.connection.cursor()
                try:
                    cursor.executemany(query, params_list)
                    pooled_conn.connection.commit()
                    return cursor.rowcount
                finally:
                    cursor.close()

            return await loop.run_in_executor(None, _execute_many)


class MySQLConnectionPool(DatabaseConnectionPool):
    """MySQL connection pool implementation."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        host: str,
        port: int = 3306,
        database: str = "",
        user: str = "",
        password: str = "",
        charset: str = "utf8mb4",
        autocommit: bool = False
    ):
        """Initialize MySQL connection pool."""
        connection_string = f"mysql://{user}:{password}@{host}:{port}/{database}"
        super().__init__(config, connection_string)

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.charset = charset
        self.autocommit = autocommit

        # Import pymysql here to make it optional
        try:
            import pymysql
            self.pymysql = pymysql
        except ImportError:
            raise ImportError("pymysql is required for MySQL connection pooling")

    async def create_connection(self) -> Any:
        """Create MySQL connection."""
        loop = asyncio.get_event_loop()

        def _create_conn():
            return self.pymysql.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                charset=self.charset,
                autocommit=self.autocommit
            )

        return await loop.run_in_executor(None, _create_conn)

    async def validate_connection(self, connection: Any) -> bool:
        """Validate MySQL connection."""
        try:
            loop = asyncio.get_event_loop()

            def _validate():
                connection.ping(reconnect=True)
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True

            return await loop.run_in_executor(None, _validate)
        except Exception:
            return False

    async def close_connection(self, connection: Any) -> None:
        """Close MySQL connection."""
        loop = asyncio.get_event_loop()

        def _close():
            try:
                connection.close()
            except Exception:
                pass  # Ignore errors during cleanup

        await loop.run_in_executor(None, _close)

    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a query using a pooled connection."""
        async with self.acquire() as pooled_conn:
            loop = asyncio.get_event_loop()

            def _execute():
                cursor = pooled_conn.connection.cursor()
                try:
                    cursor.execute(query, params or ())
                    if query.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    else:
                        pooled_conn.connection.commit()
                        return [(cursor.rowcount,)]

                finally:
                    cursor.close()

            return await loop.run_in_executor(None, _execute)

    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets."""
        async with self.acquire() as pooled_conn:
            loop = asyncio.get_event_loop()

            def _execute_many():
                cursor = pooled_conn.connection.cursor()
                try:
                    cursor.executemany(query, params_list)
                    pooled_conn.connection.commit()
                    return cursor.rowcount
                finally:
                    cursor.close()

            return await loop.run_in_executor(None, _execute_many)


class DatabasePoolFactory:
    """Factory for creating database connection pools."""

    @staticmethod
    def create_sqlite_pool(
        database_path: str,
        config: Optional[ConnectionPoolConfig] = None,
        **kwargs
    ) -> SQLiteConnectionPool:
        """Create SQLite connection pool."""
        if config is None:
            config = ConnectionPoolConfig()
        return SQLiteConnectionPool(config, database_path, **kwargs)

    @staticmethod
    def create_postgresql_pool(
        host: str,
        database: str,
        user: str,
        password: str,
        config: Optional[ConnectionPoolConfig] = None,
        **kwargs
    ) -> PostgreSQLConnectionPool:
        """Create PostgreSQL connection pool."""
        if config is None:
            config = ConnectionPoolConfig()
        return PostgreSQLConnectionPool(
            config, host, database=database, user=user, password=password, **kwargs
        )

    @staticmethod
    def create_mysql_pool(
        host: str,
        database: str,
        user: str,
        password: str,
        config: Optional[ConnectionPoolConfig] = None,
        **kwargs
    ) -> MySQLConnectionPool:
        """Create MySQL connection pool."""
        if config is None:
            config = ConnectionPoolConfig()
        return MySQLConnectionPool(
            config, host, database=database, user=user, password=password, **kwargs
        )

    @staticmethod
    def create_pool_from_url(
        connection_url: str,
        config: Optional[ConnectionPoolConfig] = None
    ) -> DatabaseConnectionPool:
        """Create database pool from connection URL."""
        if config is None:
            config = ConnectionPoolConfig()

        # Parse connection URL
        if connection_url.startswith('sqlite:///'):
            database_path = connection_url.replace('sqlite:///', '')
            return SQLiteConnectionPool(config, database_path)

        elif connection_url.startswith('postgresql://') or connection_url.startswith('postgres://'):
            # Simple URL parsing (in production, use a proper URL parser)
            # postgres://user:password@host:port/database
            url_parts = connection_url.replace('postgresql://', '').replace('postgres://', '')
            if '@' in url_parts:
                auth_part, rest = url_parts.split('@', 1)
                user, password = auth_part.split(':', 1)
                if ':' in rest:
                    host_port, database = rest.split('/', 1)
                    host, port = host_port.split(':', 1)
                    return PostgreSQLConnectionPool(
                        config, host, int(port), database, user, password
                    )

        elif connection_url.startswith('mysql://'):
            # mysql://user:password@host:port/database
            url_parts = connection_url.replace('mysql://', '')
            if '@' in url_parts:
                auth_part, rest = url_parts.split('@', 1)
                user, password = auth_part.split(':', 1)
                if ':' in rest:
                    host_port, database = rest.split('/', 1)
                    host, port = host_port.split(':', 1)
                    return MySQLConnectionPool(
                        config, host, int(port), database, user, password
                    )

        raise ValueError(f"Unsupported database URL: {connection_url}")
