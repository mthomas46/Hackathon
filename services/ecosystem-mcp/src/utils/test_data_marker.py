"""
Test data marking and identification utilities.

This module provides utilities to mark and identify test data,
acting as a safety net to prevent test data from contaminating
production environments.
"""

from datetime import datetime
import uuid
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TestDataMarker:
    """
    Mark and identify test data.
    
    All test data should be marked with metadata to:
    1. Identify it as test data
    2. Track which test session created it
    3. Enable filtering in production
    4. Facilitate cleanup if needed
    """
    
    # Metadata keys for test data markers
    TEST_MARKER_KEY = "_test_data_marker"
    TEST_SESSION_KEY = "_test_session_id"
    TEST_CREATED_KEY = "_test_created_at"
    TEST_CREATED_BY_KEY = "_test_created_by"
    
    @staticmethod
    def mark_as_test_data(
        data: Dict[str, Any],
        session_id: Optional[str] = None,
        test_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add test data markers to any data dictionary.
        
        This acts as a safety net if test data somehow
        ends up in production database.
        
        Args:
            data: Data dictionary to mark
            session_id: Optional test session ID
            test_name: Optional test function name
            
        Returns:
            Dict[str, Any]: Data with test markers added
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Ensure metadata exists
        if "metadata" not in data:
            data["metadata"] = {}
        elif data["metadata"] is None:
            data["metadata"] = {}
        
        # Add test markers
        data["metadata"][TestDataMarker.TEST_MARKER_KEY] = True
        data["metadata"][TestDataMarker.TEST_SESSION_KEY] = session_id
        data["metadata"][TestDataMarker.TEST_CREATED_KEY] = datetime.utcnow().isoformat()
        
        if test_name:
            data["metadata"][TestDataMarker.TEST_CREATED_BY_KEY] = test_name
        
        logger.debug(f"Marked data as test data (session: {session_id[:8]}...)")
        
        return data
    
    @staticmethod
    def is_test_data(data: Dict[str, Any]) -> bool:
        """
        Check if data is marked as test data.
        
        Args:
            data: Data dictionary to check
            
        Returns:
            bool: True if data is marked as test data
        """
        if not data:
            return False
        
        metadata = data.get("metadata")
        if not metadata:
            return False
        
        return metadata.get(TestDataMarker.TEST_MARKER_KEY, False)
    
    @staticmethod
    def get_test_session(data: Dict[str, Any]) -> Optional[str]:
        """
        Get test session ID from data.
        
        Args:
            data: Data dictionary
            
        Returns:
            Optional[str]: Test session ID if present
        """
        if not data:
            return None
        
        metadata = data.get("metadata")
        if not metadata:
            return None
        
        return metadata.get(TestDataMarker.TEST_SESSION_KEY)
    
    @staticmethod
    def get_test_created_at(data: Dict[str, Any]) -> Optional[str]:
        """
        Get test data creation timestamp.
        
        Args:
            data: Data dictionary
            
        Returns:
            Optional[str]: ISO timestamp if present
        """
        if not data:
            return None
        
        metadata = data.get("metadata")
        if not metadata:
            return None
        
        return metadata.get(TestDataMarker.TEST_CREATED_KEY)
    
    @staticmethod
    def get_test_created_by(data: Dict[str, Any]) -> Optional[str]:
        """
        Get test name that created this data.
        
        Args:
            data: Data dictionary
            
        Returns:
            Optional[str]: Test name if present
        """
        if not data:
            return None
        
        metadata = data.get("metadata")
        if not metadata:
            return None
        
        return metadata.get(TestDataMarker.TEST_CREATED_BY_KEY)
    
    @staticmethod
    def remove_test_markers(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove test markers from data.
        
        Useful for cleanup or data migration.
        
        Args:
            data: Data dictionary
            
        Returns:
            Dict[str, Any]: Data with test markers removed
        """
        if not data or "metadata" not in data:
            return data
        
        metadata = data["metadata"]
        if not metadata:
            return data
        
        # Remove all test marker keys
        for key in [
            TestDataMarker.TEST_MARKER_KEY,
            TestDataMarker.TEST_SESSION_KEY,
            TestDataMarker.TEST_CREATED_KEY,
            TestDataMarker.TEST_CREATED_BY_KEY,
        ]:
            metadata.pop(key, None)
        
        return data


def create_test_session_id() -> str:
    """
    Create a unique test session ID.
    
    Returns:
        str: UUID for test session
    """
    return str(uuid.uuid4())


def get_current_test_name() -> Optional[str]:
    """
    Get the name of the currently running test.
    
    Returns:
        Optional[str]: Test name if running in test context
    """
    import os
    test_name = os.getenv("PYTEST_CURRENT_TEST")
    if test_name:
        # Extract test function name from full test path
        # Format: "path/to/test.py::TestClass::test_function (call)"
        if "::" in test_name:
            test_name = test_name.split("::")[-1]
            if " " in test_name:
                test_name = test_name.split(" ")[0]
    return test_name

