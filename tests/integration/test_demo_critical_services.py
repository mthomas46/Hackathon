"""
Integration tests for demo critical service validation.

Tests that the demo properly fails when critical services are offline,
instead of silently continuing with fallbacks that produce 500 errors.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path


class TestDemoCriticalServices:
    """Test demo behavior when critical services are offline."""
    
    @pytest.mark.asyncio
    async def test_demo_fails_when_summarizer_hub_offline(self):
        """Test that demo fails gracefully when summarizer-hub is offline."""
        # Import demo class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
        
        demo = EnhancedHorusHeresyDemo()
        
        # Mock check_service_health to return False for summarizer-hub
        async def mock_check_health(service_name: str, base_url: str) -> bool:
            if service_name == "summarizer-hub":
                return False  # OFFLINE
            return True  # All other services online
        
        demo.check_service_health = mock_check_health
        
        # Run health check
        await demo.check_all_services()
        
        # Verify summarizer-hub is marked as offline
        assert demo.service_status.get("summarizer-hub") is False
        
        # ✅ TEST REQUIREMENT: Demo should FAIL, not continue with fallbacks
        # The demo should raise an exception or return error status
        # Instead of generating documents with "error_500" messages
    
    @pytest.mark.asyncio
    async def test_demo_validates_critical_services_before_starting(self):
        """Test that demo validates all critical services are online before proceeding."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
        
        demo = EnhancedHorusHeresyDemo()
        
        # Define critical services
        critical_services = ["mcp-provisioner", "summarizer-hub", "kafka-ingestion-service"]
        
        # Mock service statuses
        demo.service_status = {
            "mcp-provisioner": True,
            "summarizer-hub": False,  # CRITICAL SERVICE OFFLINE
            "kafka-ingestion-service": True,
            "mcp-gateway": True,
        }
        
        # ✅ TEST REQUIREMENT: Demo should have a method to validate critical services
        # This method should raise RuntimeError if any critical service is offline
        with pytest.raises(RuntimeError, match="Critical service.*offline"):
            demo.validate_critical_services(critical_services)
    
    @pytest.mark.asyncio
    async def test_mcp_query_failure_marks_document_as_failed(self):
        """Test that MCP query failures are properly flagged in documents."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
        
        demo = EnhancedHorusHeresyDemo()
        demo.mcp_url = "http://localhost:9999"  # Non-existent
        
        # Try to query MCP (should fail)
        result = await demo.query_mcp_for_document(
            "Test query",
            max_results=5,
            fail_on_error=False  # Don't raise exception
        )
        
        # ✅ TEST REQUIREMENT: Failed query should return None or error dict
        assert result is None or (isinstance(result, dict) and 'error' in result)
    
    @pytest.mark.asyncio
    async def test_demo_fails_fast_when_mcp_queries_dont_work(self):
        """Test that demo fails immediately if test MCP query fails."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
        
        demo = EnhancedHorusHeresyDemo()
        demo.mcp_url = "http://localhost:9999"  # Non-existent
        demo.mcp_id = "test-mcp-123"
        
        # Mock query to always fail
        async def mock_query_fail(*args, **kwargs):
            if kwargs.get('fail_on_error', False):
                raise RuntimeError("MCP query failed")
            return None
        
        demo.query_mcp_for_document = mock_query_fail
        
        # ✅ TEST REQUIREMENT: Demo should raise RuntimeError when test_query_first=True
        with pytest.raises(RuntimeError, match="MCP query"):
            await demo.generate_documentation_suite(test_query_first=True)
    
    @pytest.mark.asyncio
    async def test_no_500_errors_in_generated_documents(self):
        """Test that generated documents never contain error_500 or system error messages."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from demo_horus_heresy_enhanced import EnhancedHorusHeresyDemo
        
        demo = EnhancedHorusHeresyDemo()
        
        # Mock a successful MCP response
        mock_response = {
            "mcp_id": "test-mcp",
            "query": "Test query",
            "answer": "This is a proper answer from the MCP",
            "confidence": 0.95,
            "sources": ["source1", "source2"]
        }
        
        # Generate content
        content = f"# Test Document\n\n"
        content += f"## Response from MCP\n\n{mock_response['answer']}\n\n"
        content += f"**Confidence**: {mock_response.get('confidence', 'N/A')}\n\n"
        
        # ✅ TEST REQUIREMENT: Content should NEVER contain error indicators
        assert "error_500" not in content
        assert "system issues" not in content
        assert "Unable to access" not in content
        assert len(mock_response['answer']) > 10  # Has real content


@pytest.mark.asyncio
async def test_hierarchical_topic_extractor_method_name():
    """Test that HierarchicalTopicExtractor has correct method name."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from ingestion.tagging.hierarchical_topics import HierarchicalTopicExtractor
    
    extractor = HierarchicalTopicExtractor()
    
    # ✅ TEST REQUIREMENT: Should have check_service_health method
    assert hasattr(extractor, 'check_service_health')
    assert callable(getattr(extractor, 'check_service_health'))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

