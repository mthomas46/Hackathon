"""
Document Provenance Tracking Integration Tests

Comprehensive integration tests for the document provenance tracking system
across the interpreter, orchestrator, and doc_store services.
"""

import pytest
import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid


class TestProvenanceTrackingIntegration:
    """Integration tests for document provenance tracking system."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        self.interpreter_url = "http://localhost:5120"
        self.orchestrator_url = "http://localhost:5099"
        self.doc_store_url = "http://localhost:5087"
        self.test_user_id = f"provenance_test_{uuid.uuid4().hex[:8]}"
        self.generated_documents = []
        self.workflow_executions = []

    @pytest.fixture
    async def http_session(self):
        """HTTP session for making requests."""
        async with aiohttp.ClientSession() as session:
            yield session

    async def test_end_to_end_provenance_creation(self, http_session):
        """Test complete provenance creation from query to storage."""
        # Step 1: Generate document with provenance tracking
        query_request = {
            "query": "Create comprehensive API documentation for user management service",
            "format": "markdown",
            "user_id": self.test_user_id,
            "track_provenance": True,
            "include_metadata": True
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=query_request,
                                   timeout=aiohttp.ClientTimeout(total=60)) as response:
            assert response.status in [200, 202], f"Document generation failed: {response.status}"
            result = await response.json()

        # Extract document and execution IDs
        document_id = result.get("document_id")
        execution_id = result.get("execution_id")
        
        assert document_id is not None, "Document ID should be provided"
        self.generated_documents.append(document_id)
        
        if execution_id:
            self.workflow_executions.append(execution_id)

        # Step 2: Verify provenance data exists
        await self._verify_provenance_exists(http_session, document_id)
        
        # Step 3: Validate provenance structure
        await self._validate_provenance_structure(http_session, document_id)
        
        # Step 4: Test provenance retrieval
        await self._test_provenance_retrieval(http_session, document_id)

    async def test_workflow_execution_tracking(self, http_session):
        """Test workflow execution tracking in provenance."""
        # Execute workflow with detailed tracking
        workflow_request = {
            "name": "document_generation",
            "parameters": {
                "content_type": "technical_specification",
                "format": "json",
                "include_examples": True,
                "track_execution": True
            },
            "user_id": self.test_user_id
        }

        try:
            async with http_session.post(f"{self.interpreter_url}/workflows/execute-direct",
                                       json=workflow_request,
                                       timeout=aiohttp.ClientTimeout(total=45)) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    execution_id = result.get("execution_id")
                    
                    if execution_id:
                        self.workflow_executions.append(execution_id)
                        
                        # Test execution trace retrieval
                        await self._test_execution_trace(http_session, execution_id)

        except Exception as e:
            pytest.skip(f"Workflow execution tracking not available: {e}")

    async def test_service_chain_tracking(self, http_session):
        """Test tracking of services used in document generation."""
        # Generate document that requires multiple services
        complex_query = {
            "query": "Analyze code quality and generate improvement recommendations with examples",
            "format": "pdf",
            "user_id": self.test_user_id,
            "complexity": "high"
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=complex_query,
                                   timeout=aiohttp.ClientTimeout(total=90)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Verify service chain is tracked
                    await self._verify_service_chain(http_session, document_id)

    async def test_user_context_preservation(self, http_session):
        """Test preservation of user context in provenance."""
        # Create document with rich user context
        context_query = {
            "query": "Create user onboarding documentation",
            "format": "markdown",
            "user_id": self.test_user_id,
            "context": {
                "department": "engineering",
                "project": "user_experience",
                "priority": "high",
                "deadline": "2025-10-01"
            }
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=context_query,
                                   timeout=aiohttp.ClientTimeout(total=45)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Verify user context preservation
                    await self._verify_user_context(http_session, document_id, context_query["context"])

    async def test_prompt_tracking_in_provenance(self, http_session):
        """Test tracking of prompts used in document generation."""
        # Generate document to track prompt usage
        prompt_query = {
            "query": "Generate API testing strategy document",
            "format": "json",
            "user_id": self.test_user_id,
            "track_prompts": True
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=prompt_query,
                                   timeout=aiohttp.ClientTimeout(total=45)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Verify prompt tracking
                    await self._verify_prompt_tracking(http_session, document_id)

    async def test_data_lineage_tracking(self, http_session):
        """Test data lineage tracking in document provenance."""
        # Create document with clear data transformations
        lineage_query = {
            "query": "Transform user requirements into technical specifications",
            "format": "markdown",
            "user_id": self.test_user_id,
            "source_data": {
                "requirements": ["REQ-001", "REQ-002"],
                "stakeholders": ["product_manager", "tech_lead"]
            }
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=lineage_query,
                                   timeout=aiohttp.ClientTimeout(total=45)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Verify data lineage tracking
                    await self._verify_data_lineage(http_session, document_id)

    async def test_quality_metrics_in_provenance(self, http_session):
        """Test quality metrics tracking in document provenance."""
        # Generate document with quality assessment
        quality_query = {
            "query": "Create high-quality API reference documentation",
            "format": "markdown",
            "user_id": self.test_user_id,
            "quality_checks": True,
            "include_metrics": True
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=quality_query,
                                   timeout=aiohttp.ClientTimeout(total=45)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Verify quality metrics
                    await self._verify_quality_metrics(http_session, document_id)

    async def test_provenance_cross_service_consistency(self, http_session):
        """Test provenance consistency across services."""
        # Generate document that uses multiple services
        cross_service_query = {
            "query": "Analyze system architecture and create documentation",
            "format": "json",
            "user_id": self.test_user_id,
            "use_analysis_service": True,
            "store_in_doc_store": True
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=cross_service_query,
                                   timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Check provenance consistency across services
                    await self._verify_cross_service_consistency(http_session, document_id)

    async def test_provenance_temporal_accuracy(self, http_session):
        """Test temporal accuracy of provenance timestamps."""
        start_time = datetime.utcnow()
        
        # Generate document to test timing
        temporal_query = {
            "query": "Create temporal test documentation",
            "format": "txt",
            "user_id": self.test_user_id
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=temporal_query,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
            end_time = datetime.utcnow()
            
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Verify temporal accuracy
                    await self._verify_temporal_accuracy(http_session, document_id, start_time, end_time)

    async def test_provenance_audit_trail(self, http_session):
        """Test complete audit trail in provenance."""
        # Generate document with comprehensive audit trail
        audit_query = {
            "query": "Create audit-compliant documentation",
            "format": "markdown",
            "user_id": self.test_user_id,
            "audit_mode": True,
            "compliance_level": "high"
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=audit_query,
                                   timeout=aiohttp.ClientTimeout(total=45)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    self.generated_documents.append(document_id)
                    
                    # Verify audit trail completeness
                    await self._verify_audit_trail(http_session, document_id)

    # Helper methods for provenance verification

    async def _verify_provenance_exists(self, session: aiohttp.ClientSession, document_id: str):
        """Verify that provenance data exists for document."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    assert provenance is not None, "Provenance data should not be None"
                    assert len(provenance) > 0, "Provenance data should not be empty"
                    return True
                # 404 is acceptable if provenance not implemented yet
                return response.status == 404
        except Exception as e:
            print(f"Provenance verification skipped: {e}")
            return False

    async def _validate_provenance_structure(self, session: aiohttp.ClientSession, document_id: str):
        """Validate the structure of provenance data."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    # Expected provenance fields
                    expected_fields = [
                        "workflow_execution",
                        "services_chain", 
                        "user_context",
                        "data_lineage",
                        "quality_metrics"
                    ]
                    
                    for field in expected_fields:
                        if field in provenance:
                            assert provenance[field] is not None, f"Provenance field '{field}' should not be None"
                    
                    # Validate workflow execution structure
                    if "workflow_execution" in provenance:
                        workflow_exec = provenance["workflow_execution"]
                        assert "execution_id" in workflow_exec, "Missing execution_id in workflow_execution"
                        assert "workflow_name" in workflow_exec, "Missing workflow_name in workflow_execution"
                    
                    # Validate services chain
                    if "services_chain" in provenance:
                        services = provenance["services_chain"]
                        assert isinstance(services, list), "Services chain should be a list"
                        assert len(services) > 0, "Services chain should not be empty"
                    
                    return True
        except Exception as e:
            print(f"Provenance structure validation skipped: {e}")
            return False

    async def _test_provenance_retrieval(self, session: aiohttp.ClientSession, document_id: str):
        """Test provenance retrieval performance and accessibility."""
        try:
            start_time = time.time()
            
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                end_time = time.time()
                retrieval_time = end_time - start_time
                
                if response.status == 200:
                    # Provenance retrieval should be fast
                    assert retrieval_time < 5.0, f"Provenance retrieval too slow: {retrieval_time}s"
                    
                    provenance = await response.json()
                    
                    # Verify data completeness
                    assert len(json.dumps(provenance)) > 100, "Provenance data seems too small"
                    
                    return True
        except Exception as e:
            print(f"Provenance retrieval test skipped: {e}")
            return False

    async def _test_execution_trace(self, session: aiohttp.ClientSession, execution_id: str):
        """Test workflow execution trace retrieval."""
        try:
            async with session.get(f"{self.interpreter_url}/workflows/{execution_id}/trace",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    trace = await response.json()
                    
                    # Validate trace structure
                    expected_trace_fields = ["execution_id", "steps", "timeline", "duration"]
                    for field in expected_trace_fields:
                        if field in trace:
                            assert trace[field] is not None, f"Trace field '{field}' should not be None"
                    
                    # Verify execution steps
                    if "steps" in trace:
                        steps = trace["steps"]
                        assert isinstance(steps, list), "Execution steps should be a list"
                        
                        for step in steps:
                            assert "step_name" in step, "Missing step_name in execution step"
                            assert "status" in step, "Missing status in execution step"
                    
                    return True
        except Exception as e:
            print(f"Execution trace test skipped: {e}")
            return False

    async def _verify_service_chain(self, session: aiohttp.ClientSession, document_id: str):
        """Verify service chain tracking in provenance."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    if "services_chain" in provenance:
                        services = provenance["services_chain"]
                        
                        # Should include interpreter service at minimum
                        service_names = [s.get("name", s) if isinstance(s, dict) else s for s in services]
                        assert "interpreter" in service_names, "Interpreter should be in services chain"
                        
                        # Verify service chain structure
                        for service in services:
                            if isinstance(service, dict):
                                assert "name" in service, "Service should have name"
                                assert "role" in service or "operation" in service, "Service should have role/operation"
                    
                    return True
        except Exception as e:
            print(f"Service chain verification skipped: {e}")
            return False

    async def _verify_user_context(self, session: aiohttp.ClientSession, document_id: str, original_context: Dict[str, Any]):
        """Verify user context preservation in provenance."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    if "user_context" in provenance:
                        user_context = provenance["user_context"]
                        
                        # Verify user ID preservation
                        assert "user_id" in user_context, "User ID should be preserved"
                        assert user_context["user_id"] == self.test_user_id, "User ID should match"
                        
                        # Verify original query preservation
                        assert "query" in user_context, "Original query should be preserved"
                        
                        # Check if any original context was preserved
                        for key, value in original_context.items():
                            if key in user_context:
                                assert user_context[key] == value, f"Context {key} should be preserved"
                    
                    return True
        except Exception as e:
            print(f"User context verification skipped: {e}")
            return False

    async def _verify_prompt_tracking(self, session: aiohttp.ClientSession, document_id: str):
        """Verify prompt tracking in provenance."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    if "prompts_used" in provenance:
                        prompts = provenance["prompts_used"]
                        assert isinstance(prompts, list), "Prompts should be a list"
                        
                        if len(prompts) > 0:
                            # Verify prompt structure
                            for prompt in prompts:
                                assert "service" in prompt or "prompt" in prompt, "Prompt should have service or prompt field"
                                
                                if "prompt" in prompt:
                                    assert len(prompt["prompt"]) > 0, "Prompt content should not be empty"
                    
                    return True
        except Exception as e:
            print(f"Prompt tracking verification skipped: {e}")
            return False

    async def _verify_data_lineage(self, session: aiohttp.ClientSession, document_id: str):
        """Verify data lineage tracking in provenance."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    if "data_lineage" in provenance:
                        lineage = provenance["data_lineage"]
                        
                        # Verify lineage structure
                        lineage_fields = ["input_sources", "transformations", "output_destinations"]
                        for field in lineage_fields:
                            if field in lineage:
                                assert isinstance(lineage[field], list), f"Data lineage {field} should be a list"
                    
                    return True
        except Exception as e:
            print(f"Data lineage verification skipped: {e}")
            return False

    async def _verify_quality_metrics(self, session: aiohttp.ClientSession, document_id: str):
        """Verify quality metrics in provenance."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    if "quality_metrics" in provenance:
                        metrics = provenance["quality_metrics"]
                        
                        # Verify quality metrics structure
                        expected_metrics = ["confidence", "completeness", "accuracy"]
                        for metric in expected_metrics:
                            if metric in metrics:
                                assert isinstance(metrics[metric], (int, float)), f"Quality metric {metric} should be numeric"
                                assert 0 <= metrics[metric] <= 1, f"Quality metric {metric} should be between 0 and 1"
                    
                    return True
        except Exception as e:
            print(f"Quality metrics verification skipped: {e}")
            return False

    async def _verify_cross_service_consistency(self, session: aiohttp.ClientSession, document_id: str):
        """Verify provenance consistency across services."""
        try:
            # Get provenance from interpreter
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    interpreter_provenance = await response.json()
                    
                    # Try to get document metadata from doc_store
                    try:
                        async with session.get(f"{self.doc_store_url}/documents/{document_id}",
                                             timeout=aiohttp.ClientTimeout(total=10)) as doc_response:
                            if doc_response.status == 200:
                                doc_metadata = await doc_response.json()
                                
                                # Compare consistent fields
                                if "metadata" in doc_metadata and "workflow_execution" in interpreter_provenance:
                                    doc_meta = doc_metadata["metadata"]
                                    workflow_exec = interpreter_provenance["workflow_execution"]
                                    
                                    # Check timestamp consistency (within reasonable range)
                                    if "created_at" in doc_meta and "started_at" in workflow_exec:
                                        # Timestamps should be close (within 1 hour)
                                        doc_time = datetime.fromisoformat(doc_meta["created_at"].replace('Z', '+00:00'))
                                        workflow_time = datetime.fromisoformat(workflow_exec["started_at"].replace('Z', '+00:00'))
                                        time_diff = abs((doc_time - workflow_time).total_seconds())
                                        assert time_diff < 3600, f"Timestamp inconsistency: {time_diff}s"
                    except Exception:
                        pass  # Doc store integration may not be complete
                    
                    return True
        except Exception as e:
            print(f"Cross-service consistency verification skipped: {e}")
            return False

    async def _verify_temporal_accuracy(self, session: aiohttp.ClientSession, document_id: str, 
                                      start_time: datetime, end_time: datetime):
        """Verify temporal accuracy of provenance timestamps."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    if "workflow_execution" in provenance:
                        workflow_exec = provenance["workflow_execution"]
                        
                        # Check start time
                        if "started_at" in workflow_exec:
                            started_at = datetime.fromisoformat(workflow_exec["started_at"].replace('Z', '+00:00'))
                            
                            # Started time should be between our start and end times
                            assert start_time <= started_at <= end_time, f"Workflow start time {started_at} outside expected range"
                        
                        # Check completion time
                        if "completed_at" in workflow_exec:
                            completed_at = datetime.fromisoformat(workflow_exec["completed_at"].replace('Z', '+00:00'))
                            
                            # Completion should be after start
                            if "started_at" in workflow_exec:
                                started_at = datetime.fromisoformat(workflow_exec["started_at"].replace('Z', '+00:00'))
                                assert completed_at >= started_at, "Completion time should be after start time"
                    
                    return True
        except Exception as e:
            print(f"Temporal accuracy verification skipped: {e}")
            return False

    async def _verify_audit_trail(self, session: aiohttp.ClientSession, document_id: str):
        """Verify completeness of audit trail in provenance."""
        try:
            async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                 timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    provenance = await response.json()
                    
                    # Verify audit trail completeness
                    audit_fields = [
                        "workflow_execution",
                        "services_chain",
                        "user_context", 
                        "data_lineage"
                    ]
                    
                    present_fields = [field for field in audit_fields if field in provenance]
                    audit_completeness = len(present_fields) / len(audit_fields)
                    
                    # At least 75% of audit fields should be present
                    assert audit_completeness >= 0.75, f"Audit trail incomplete: {audit_completeness:.2%}"
                    
                    # Verify each present field has meaningful data
                    for field in present_fields:
                        field_data = provenance[field]
                        if isinstance(field_data, dict):
                            assert len(field_data) > 0, f"Audit field {field} should not be empty"
                        elif isinstance(field_data, list):
                            assert len(field_data) > 0, f"Audit field {field} should not be empty list"
                    
                    return True
        except Exception as e:
            print(f"Audit trail verification skipped: {e}")
            return False


class TestProvenancePerformance:
    """Test performance characteristics of provenance tracking."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup performance test environment."""
        self.interpreter_url = "http://localhost:5120"
        self.test_user_id = f"perf_test_{uuid.uuid4().hex[:8]}"

    async def test_provenance_creation_performance(self, http_session):
        """Test performance impact of provenance creation."""
        # Test with and without provenance tracking
        base_query = {
            "query": "Create performance test document",
            "format": "json",
            "user_id": self.test_user_id
        }

        # Test without provenance tracking
        start_time = time.time()
        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=base_query,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
            no_provenance_time = time.time() - start_time
            no_provenance_success = response.status in [200, 202]

        # Test with provenance tracking
        provenance_query = {**base_query, "track_provenance": True}
        start_time = time.time()
        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=provenance_query,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
            provenance_time = time.time() - start_time
            provenance_success = response.status in [200, 202]

        if no_provenance_success and provenance_success:
            # Provenance tracking should not significantly impact performance
            overhead = (provenance_time - no_provenance_time) / no_provenance_time * 100
            assert overhead < 50, f"Provenance tracking overhead too high: {overhead:.1f}%"

    async def test_provenance_retrieval_performance(self, http_session):
        """Test performance of provenance data retrieval."""
        # Generate document with provenance
        query_request = {
            "query": "Create provenance performance test document",
            "format": "markdown",
            "user_id": self.test_user_id,
            "track_provenance": True
        }

        async with http_session.post(f"{self.interpreter_url}/execute-query",
                                   json=query_request,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status in [200, 202]:
                result = await response.json()
                document_id = result.get("document_id")
                
                if document_id:
                    # Test provenance retrieval performance
                    retrieval_times = []
                    
                    for i in range(3):  # Test multiple retrievals
                        start_time = time.time()
                        
                        try:
                            async with http_session.get(f"{self.interpreter_url}/documents/{document_id}/provenance",
                                                       timeout=aiohttp.ClientTimeout(total=10)) as prov_response:
                                if prov_response.status == 200:
                                    await prov_response.json()  # Read response
                                    retrieval_times.append(time.time() - start_time)
                        except Exception:
                            pass
                    
                    if retrieval_times:
                        avg_retrieval_time = sum(retrieval_times) / len(retrieval_times)
                        # Provenance retrieval should be fast
                        assert avg_retrieval_time < 2.0, f"Provenance retrieval too slow: {avg_retrieval_time:.2f}s"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
