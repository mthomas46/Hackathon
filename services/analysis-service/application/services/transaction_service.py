"""Application Transaction Service - Database transaction management and consistency."""

import asyncio
import sqlite3
from typing import Any, Dict, Optional, List, Callable, TypeVar, Generic
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

from .application_service import ApplicationService, ServiceContext


T = TypeVar('T')


class TransactionContext:
    """Transaction context for managing database transactions."""

    def __init__(self, connection=None, isolation_level: str = "DEFERRED"):
        """Initialize transaction context."""
        self.connection = connection
        self.isolation_level = isolation_level
        self.is_active = False
        self.savepoints: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def is_in_transaction(self) -> bool:
        """Check if currently in a transaction."""
        return self.is_active

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to transaction context."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from transaction context."""
        return self.metadata.get(key, default)


class TransactionManager(ABC):
    """Abstract base class for transaction managers."""

    @abstractmethod
    async def begin_transaction(self, isolation_level: str = "DEFERRED") -> TransactionContext:
        """Begin a new transaction."""
        pass

    @abstractmethod
    async def commit_transaction(self, context: TransactionContext) -> None:
        """Commit a transaction."""
        pass

    @abstractmethod
    async def rollback_transaction(self, context: TransactionContext) -> None:
        """Rollback a transaction."""
        pass

    @abstractmethod
    async def create_savepoint(self, context: TransactionContext, name: str) -> None:
        """Create a savepoint in the transaction."""
        pass

    @abstractmethod
    async def rollback_to_savepoint(self, context: TransactionContext, name: str) -> None:
        """Rollback to a savepoint."""
        pass

    @abstractmethod
    async def execute_in_transaction(
        self,
        operation: Callable[[TransactionContext], Any],
        isolation_level: str = "DEFERRED"
    ) -> Any:
        """Execute operation within a transaction."""
        pass


class SQLiteTransactionManager(TransactionManager):
    """SQLite-specific transaction manager."""

    def __init__(self, database_path: str):
        """Initialize SQLite transaction manager."""
        self.database_path = database_path
        self._connection_pool: Dict[int, sqlite3.Connection] = {}

    def _get_connection(self, task_id: Optional[int] = None) -> sqlite3.Connection:
        """Get database connection for current task."""
        if task_id is None:
            task_id = asyncio.current_task().get_loop()._task_id if asyncio.current_task() else 0

        if task_id not in self._connection_pool:
            conn = sqlite3.connect(
                self.database_path,
                isolation_level=None,  # We'll manage isolation manually
                check_same_thread=False
            )
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            self._connection_pool[task_id] = conn

        return self._connection_pool[task_id]

    def _close_connection(self, task_id: Optional[int] = None) -> None:
        """Close database connection for current task."""
        if task_id is None:
            task_id = asyncio.current_task().get_loop()._task_id if asyncio.current_task() else 0

        if task_id in self._connection_pool:
            conn = self._connection_pool[task_id]
            conn.close()
            del self._connection_pool[task_id]

    async def begin_transaction(self, isolation_level: str = "DEFERRED") -> TransactionContext:
        """Begin a new transaction."""
        conn = self._get_connection()
        context = TransactionContext(conn, isolation_level)

        try:
            # Set isolation level and begin transaction
            if isolation_level == "IMMEDIATE":
                conn.execute("BEGIN IMMEDIATE TRANSACTION")
            elif isolation_level == "EXCLUSIVE":
                conn.execute("BEGIN EXCLUSIVE TRANSACTION")
            else:  # DEFERRED (default)
                conn.execute("BEGIN DEFERRED TRANSACTION")

            context.is_active = True
            return context

        except Exception as e:
            self._close_connection()
            raise e

    async def commit_transaction(self, context: TransactionContext) -> None:
        """Commit a transaction."""
        if not context.is_active:
            raise ValueError("No active transaction to commit")

        try:
            context.connection.commit()
            context.is_active = False
        except Exception as e:
            await self.rollback_transaction(context)
            raise e
        finally:
            self._close_connection()

    async def rollback_transaction(self, context: TransactionContext) -> None:
        """Rollback a transaction."""
        if not context.is_active:
            return

        try:
            context.connection.rollback()
            context.is_active = False
        except Exception as e:
            # Log error but don't raise - rollback should be safe
            print(f"Error during rollback: {e}")
        finally:
            self._close_connection()

    async def create_savepoint(self, context: TransactionContext, name: str) -> None:
        """Create a savepoint in the transaction."""
        if not context.is_active:
            raise ValueError("No active transaction for savepoint")

        context.connection.execute(f"SAVEPOINT {name}")
        context.savepoints.append(name)

    async def rollback_to_savepoint(self, context: TransactionContext, name: str) -> None:
        """Rollback to a savepoint."""
        if not context.is_active:
            raise ValueError("No active transaction for savepoint rollback")

        if name not in context.savepoints:
            raise ValueError(f"Savepoint {name} does not exist")

        context.connection.execute(f"ROLLBACK TO SAVEPOINT {name}")

        # Remove savepoint and all subsequent savepoints
        idx = context.savepoints.index(name)
        context.savepoints[:] = context.savepoints[:idx]

    async def execute_in_transaction(
        self,
        operation: Callable[[TransactionContext], Any],
        isolation_level: str = "DEFERRED"
    ) -> Any:
        """Execute operation within a transaction."""
        context = await self.begin_transaction(isolation_level)

        try:
            result = await operation(context)
            await self.commit_transaction(context)
            return result
        except Exception as e:
            await self.rollback_transaction(context)
            raise e


class TransactionService(ApplicationService):
    """Application transaction service for managing database transactions."""

    def __init__(self, transaction_manager: TransactionManager):
        """Initialize transaction service."""
        super().__init__("transaction_service")
        self.transaction_manager = transaction_manager
        self.active_transactions: Dict[int, TransactionContext] = {}

    @asynccontextmanager
    async def transaction(
        self,
        isolation_level: str = "DEFERRED",
        context: Optional[ServiceContext] = None
    ):
        """Context manager for transactions."""
        async with self.operation_context("transaction", context):
            transaction_context = await self.transaction_manager.begin_transaction(isolation_level)

            # Store transaction context for current task
            task_id = id(asyncio.current_task())
            self.active_transactions[task_id] = transaction_context

            try:
                yield transaction_context
                await self.transaction_manager.commit_transaction(transaction_context)
                self.logger.info("Transaction committed successfully")
            except Exception as e:
                await self.transaction_manager.rollback_transaction(transaction_context)
                self.logger.error(f"Transaction rolled back: {e}", exc_info=True)
                raise e
            finally:
                # Clean up
                self.active_transactions.pop(task_id, None)

    async def execute_in_transaction(
        self,
        operation: Callable[[TransactionContext], Any],
        isolation_level: str = "DEFERRED",
        context: Optional[ServiceContext] = None
    ) -> Any:
        """Execute operation within a transaction."""
        async with self.operation_context("execute_in_transaction", context):
            return await self.transaction_manager.execute_in_transaction(operation, isolation_level)

    async def create_savepoint(
        self,
        name: str,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Create a transaction savepoint."""
        async with self.operation_context("create_savepoint", context):
            task_id = id(asyncio.current_task())
            transaction_context = self.active_transactions.get(task_id)

            if not transaction_context:
                raise ValueError("No active transaction for savepoint")

            await self.transaction_manager.create_savepoint(transaction_context, name)

    async def rollback_to_savepoint(
        self,
        name: str,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Rollback to a transaction savepoint."""
        async with self.operation_context("rollback_to_savepoint", context):
            task_id = id(asyncio.current_task())
            transaction_context = self.active_transactions.get(task_id)

            if not transaction_context:
                raise ValueError("No active transaction for savepoint rollback")

            await self.transaction_manager.rollback_to_savepoint(transaction_context, name)

    async def get_transaction_status(self) -> Dict[str, Any]:
        """Get current transaction status."""
        task_id = id(asyncio.current_task())
        transaction_context = self.active_transactions.get(task_id)

        if transaction_context:
            return {
                'active': transaction_context.is_active,
                'isolation_level': transaction_context.isolation_level,
                'savepoints': transaction_context.savepoints.copy(),
                'metadata': transaction_context.metadata.copy()
            }
        else:
            return {'active': False}

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add transaction-specific health info
        try:
            status = await self.get_transaction_status()
            health['transaction_service'] = {
                'active_transactions': len(self.active_transactions),
                'current_transaction_active': status['active'],
                'transaction_manager_type': type(self.transaction_manager).__name__
            }

            # Test transaction functionality
            test_result = await self._test_transaction_functionality()
            health['transaction_service']['test_result'] = test_result

        except Exception as e:
            health['transaction_service'] = {'error': str(e)}

        return health

    async def _test_transaction_functionality(self) -> bool:
        """Test basic transaction functionality."""
        try:
            # Simple test operation
            async def test_operation(ctx: TransactionContext) -> str:
                # In a real implementation, this would perform actual database operations
                return "test_success"

            result = await self.execute_in_transaction(test_operation)
            return result == "test_success"

        except Exception as e:
            self.logger.error(f"Transaction functionality test failed: {e}")
            return False


class UnitOfWork:
    """Unit of Work pattern implementation for managing transactions and domain object state."""

    def __init__(self, transaction_service: TransactionService):
        """Initialize unit of work."""
        self.transaction_service = transaction_service
        self.new_objects: List[Any] = []
        self.dirty_objects: List[Any] = []
        self.removed_objects: List[Any] = []

    def register_new(self, obj: Any) -> None:
        """Register a new object."""
        self.new_objects.append(obj)

    def register_dirty(self, obj: Any) -> None:
        """Register a modified object."""
        if obj not in self.dirty_objects:
            self.dirty_objects.append(obj)

    def register_removed(self, obj: Any) -> None:
        """Register a removed object."""
        self.removed_objects.append(obj)

    async def commit(self) -> None:
        """Commit all changes within a transaction."""
        async with self.transaction_service.transaction() as ctx:
            # Insert new objects
            for obj in self.new_objects:
                await self._insert_object(obj, ctx)

            # Update dirty objects
            for obj in self.dirty_objects:
                await self._update_object(obj, ctx)

            # Delete removed objects
            for obj in self.removed_objects:
                await self._delete_object(obj, ctx)

        # Clear tracking lists
        self.new_objects.clear()
        self.dirty_objects.clear()
        self.removed_objects.clear()

    async def rollback(self) -> None:
        """Rollback all changes."""
        self.new_objects.clear()
        self.dirty_objects.clear()
        self.removed_objects.clear()

    async def _insert_object(self, obj: Any, ctx: TransactionContext) -> None:
        """Insert a new object."""
        # This would be implemented by specific repositories
        # For now, just log the operation
        print(f"Inserting object: {obj}")

    async def _update_object(self, obj: Any, ctx: TransactionContext) -> None:
        """Update an existing object."""
        # This would be implemented by specific repositories
        print(f"Updating object: {obj}")

    async def _delete_object(self, obj: Any, ctx: TransactionContext) -> None:
        """Delete an object."""
        # This would be implemented by specific repositories
        print(f"Deleting object: {obj}")


# Global transaction service instance
# This would be initialized with the appropriate transaction manager
transaction_service = None  # Will be set during application startup
