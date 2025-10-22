"""
Enhanced Logging Utilities for Document Generation Pipeline

Provides structured logging with context, timing, and error tracking.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager


class PipelineLogger:
    """Enhanced logger for pipeline operations."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.operation_stack = []
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation with context."""
        self.logger.info("=" * 70)
        self.logger.info(f"🚀 STARTING: {operation}")
        if kwargs:
            self.logger.info(f"📋 Context:")
            for key, value in kwargs.items():
                # Truncate long values
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                self.logger.info(f"   {key}: {value}")
        self.logger.info("=" * 70)
        
        return time.time()
    
    def log_operation_complete(self, operation: str, start_time: float, **kwargs):
        """Log the completion of an operation."""
        duration = time.time() - start_time
        self.logger.info("=" * 70)
        self.logger.info(f"✅ COMPLETED: {operation}")
        self.logger.info(f"⏱️  Duration: {duration:.3f}s")
        if kwargs:
            self.logger.info(f"📊 Results:")
            for key, value in kwargs.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                self.logger.info(f"   {key}: {value}")
        self.logger.info("=" * 70)
    
    def log_operation_error(self, operation: str, error: Exception, **kwargs):
        """Log an operation error with full context."""
        self.logger.error("=" * 70)
        self.logger.error(f"❌ ERROR in {operation}")
        self.logger.error(f"Type: {type(error).__name__}")
        self.logger.error(f"Message: {str(error)}")
        if kwargs:
            self.logger.error(f"🔍 Context:")
            for key, value in kwargs.items():
                self.logger.error(f"   {key}: {value}")
        self.logger.error("=" * 70)
    
    def log_step(self, step: str, **kwargs):
        """Log a pipeline step."""
        self.logger.info(f"📍 Step: {step}")
        if kwargs:
            for key, value in kwargs.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                self.logger.info(f"   {key}: {value}")
    
    def log_checkpoint(self, message: str, **kwargs):
        """Log a checkpoint in processing."""
        self.logger.info(f"✓ Checkpoint: {message}")
        if kwargs:
            for key, value in kwargs.items():
                self.logger.info(f"     {key}: {value}")
    
    def log_warning(self, message: str, **kwargs):
        """Log a warning."""
        self.logger.warning(f"⚠️  WARNING: {message}")
        if kwargs:
            for key, value in kwargs.items():
                self.logger.warning(f"   {key}: {value}")
    
    def log_model_access(self, model_name: str, attributes: list):
        """Log database model access patterns."""
        self.logger.debug(f"🗄️  Accessing {model_name}")
        self.logger.debug(f"   Attributes: {', '.join(attributes)}")
    
    def log_relationship_load(self, model_name: str, relationship: str, eager: bool = False):
        """Log relationship loading."""
        load_type = "eager" if eager else "lazy"
        self.logger.debug(f"🔗 Loading {model_name}.{relationship} ({load_type})")
    
    def log_method_call(self, class_name: str, method_name: str, **kwargs):
        """Log method calls for debugging."""
        self.logger.debug(f"🔧 Calling {class_name}.{method_name}()")
        if kwargs:
            for key, value in kwargs.items():
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                self.logger.debug(f"   {key}={value}")


def log_execution_time(operation_name: str):
    """Decorator to log execution time."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            start = time.time()
            
            logger.info(f"⏱️  Starting: {operation_name}")
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"✅ Completed: {operation_name} ({duration:.3f}s)")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"❌ Failed: {operation_name} ({duration:.3f}s) - {str(e)}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            start = time.time()
            
            logger.info(f"⏱️  Starting: {operation_name}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"✅ Completed: {operation_name} ({duration:.3f}s)")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"❌ Failed: {operation_name} ({duration:.3f}s) - {str(e)}")
                raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def log_context(logger: logging.Logger, operation: str, **kwargs):
    """Context manager for logging operations."""
    start = time.time()
    logger.info("=" * 70)
    logger.info(f"🚀 STARTING: {operation}")
    if kwargs:
        for key, value in kwargs.items():
            logger.info(f"   {key}: {value}")
    logger.info("=" * 70)
    
    try:
        yield
        duration = time.time() - start
        logger.info("=" * 70)
        logger.info(f"✅ COMPLETED: {operation}")
        logger.info(f"⏱️  Duration: {duration:.3f}s")
        logger.info("=" * 70)
    except Exception as e:
        duration = time.time() - start
        logger.error("=" * 70)
        logger.error(f"❌ FAILED: {operation}")
        logger.error(f"⏱️  Duration: {duration:.3f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 70)
        raise


def log_database_query(query_description: str):
    """Log database query execution."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            start = time.time()
            
            logger.debug(f"🗄️  DB Query: {query_description}")
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(f"✅ Query complete ({duration:.3f}s)")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"❌ Query failed ({duration:.3f}s): {str(e)}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            start = time.time()
            
            logger.debug(f"🗄️  DB Query: {query_description}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(f"✅ Query complete ({duration:.3f}s)")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"❌ Query failed ({duration:.3f}s): {str(e)}")
                raise
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class StructuredLogger:
    """Logger that outputs structured JSON logs for analysis."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"{name}.structured")
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type: str, **data):
        """Log a structured event."""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            **data
        }
        self.logger.info(json.dumps(event))
    
    def log_metric(self, metric_name: str, value: float, **tags):
        """Log a metric with tags."""
        metric = {
            "timestamp": time.time(),
            "metric": metric_name,
            "value": value,
            "tags": tags
        }
        self.logger.info(json.dumps(metric))


def create_pipeline_logger(name: str) -> PipelineLogger:
    """Factory function to create a pipeline logger."""
    return PipelineLogger(name)

