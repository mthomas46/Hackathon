#!/usr/bin/env python3
"""
End-to-End Document Persistence Pipeline Validation

This comprehensive validation script tests the complete document persistence pipeline
across the LLM Documentation Ecosystem, including:

1. Natural language query processing (Interpreter Service)
2. Workflow orchestration and execution (Orchestrator Service)
3. Document generation with multiple formats (Output Generator)
4. Persistent storage with metadata (Doc Store Service)
5. Provenance tracking and audit trails (Complete ecosystem)
6. Document retrieval and download capabilities
7. Cross-service integration validation
8. Performance and reliability testing

Usage:
    python scripts/validation/e2e_document_persistence_validation.py
    python scripts/validation/e2e_document_persistence_validation.py --comprehensive
    python scripts/validation/e2e_document_persistence_validation.py --format json
    python scripts/validation/e2e_document_persistence_validation.py --quick
"""

import asyncio
import aiohttp
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

@dataclass
class ValidationResult:
    """Result of a single validation test."""
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    warnings: List[str] = None

@dataclass
class E2EValidationSuite:
    """Complete validation suite results."""
    total_tests: int
    successful_tests: int
    failed_tests: int
    total_duration: float
    success_rate: float
    results: List[ValidationResult]
    summary: Dict[str, Any]

class DocumentPersistenceValidator:
    """Comprehensive validator for the document persistence pipeline."""
    
    def __init__(self, base_url: str = "http://localhost"):
        """Initialize the validator with service URLs."""
        self.base_url = base_url
        self.console = Console()
        
        # Service endpoints
        self.services = {
            "interpreter": f"{base_url}:5120",
            "orchestrator": f"{base_url}:5099", 
            "doc_store": f"{base_url}:5087",
            "prompt_store": f"{base_url}:5110",
            "llm_gateway": f"{base_url}:5055",
            "frontend": f"{base_url}:3000"
        }
        
        # Test data and configurations
        self.test_queries = [
            {
                "query": "Create a technical specification for a REST API authentication system",
                "expected_sections": ["authentication", "api", "security", "endpoints"],
                "formats": ["json", "markdown", "pdf"]
            },
            {
                "query": "Generate documentation for a microservices deployment guide",
                "expected_sections": ["microservices", "deployment", "docker", "kubernetes"],
                "formats": ["markdown", "txt"]
            },
            {
                "query": "Create user manual for document management system",
                "expected_sections": ["user", "manual", "document", "management"],
                "formats": ["pdf", "markdown"]
            }
        ]
        
        # Validation results storage
        self.results: List[ValidationResult] = []
        self.generated_documents: List[Dict[str, Any]] = []
        
    async def run_comprehensive_validation(self) -> E2EValidationSuite:
        """Run the complete end-to-end validation suite."""
        start_time = time.time()
        
        console.print("[bold blue]🧪 Starting Comprehensive E2E Document Persistence Validation[/bold blue]")
        console.print("=" * 80)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # Define validation phases
            phases = [
                ("🏥 Service Health Validation", self._validate_service_health),
                ("🔌 Service Integration Validation", self._validate_service_integration),
                ("🧠 Query Processing Validation", self._validate_query_processing),
                ("⚙️ Workflow Execution Validation", self._validate_workflow_execution),
                ("📄 Document Generation Validation", self._validate_document_generation),
                ("💾 Persistent Storage Validation", self._validate_persistent_storage),
                ("🔍 Provenance Tracking Validation", self._validate_provenance_tracking),
                ("📥 Document Retrieval Validation", self._validate_document_retrieval),
                ("🔄 End-to-End Integration Validation", self._validate_e2e_integration),
                ("⚡ Performance & Reliability Validation", self._validate_performance_reliability)
            ]
            
            main_task = progress.add_task("Overall Validation Progress", total=len(phases))
            
            for phase_name, phase_func in phases:
                phase_task = progress.add_task(f"Running {phase_name}", total=1)
                
                try:
                    phase_results = await phase_func()
                    self.results.extend(phase_results)
                    
                    success_count = sum(1 for r in phase_results if r.success)
                    console.print(f"✅ {phase_name}: {success_count}/{len(phase_results)} tests passed")
                    
                except Exception as e:
                    console.print(f"❌ {phase_name}: Failed with error: {str(e)}")
                    self.results.append(ValidationResult(
                        test_name=f"{phase_name} (Phase Failure)",
                        success=False,
                        duration=0.0,
                        details={},
                        error_message=str(e)
                    ))
                
                progress.update(phase_task, completed=1)
                progress.update(main_task, advance=1)
        
        # Calculate final results
        total_duration = time.time() - start_time
        successful_tests = sum(1 for r in self.results if r.success)
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate summary
        summary = self._generate_validation_summary()
        
        return E2EValidationSuite(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=total_tests - successful_tests,
            total_duration=total_duration,
            success_rate=success_rate,
            results=self.results,
            summary=summary
        )

    async def _validate_service_health(self) -> List[ValidationResult]:
        """Validate that all required services are healthy."""
        results = []
        
        async with aiohttp.ClientSession() as session:
            for service_name, service_url in self.services.items():
                start_time = time.time()
                
                try:
                    async with session.get(f"{service_url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                        duration = time.time() - start_time
                        
                        if response.status == 200:
                            health_data = await response.json()
                            results.append(ValidationResult(
                                test_name=f"Service Health: {service_name}",
                                success=True,
                                duration=duration,
                                details={
                                    "status": health_data.get("status", "unknown"),
                                    "version": health_data.get("version", "unknown"),
                                    "uptime": health_data.get("uptime_seconds", 0),
                                    "response_time": duration
                                }
                            ))
                        else:
                            results.append(ValidationResult(
                                test_name=f"Service Health: {service_name}",
                                success=False,
                                duration=duration,
                                details={"status_code": response.status},
                                error_message=f"HTTP {response.status}"
                            ))
                
                except Exception as e:
                    duration = time.time() - start_time
                    results.append(ValidationResult(
                        test_name=f"Service Health: {service_name}",
                        success=False,
                        duration=duration,
                        details={},
                        error_message=str(e)
                    ))
        
        return results

    async def _validate_service_integration(self) -> List[ValidationResult]:
        """Validate inter-service communication and dependencies."""
        results = []
        
        async with aiohttp.ClientSession() as session:
            # Test Interpreter -> Orchestrator communication
            start_time = time.time()
            try:
                # Check if interpreter can access orchestrator
                test_query = {
                    "query": "test integration query",
                    "format": "json"
                }
                
                async with session.post(f"{self.services['interpreter']}/execute-query", 
                                      json=test_query, 
                                      timeout=aiohttp.ClientTimeout(total=30)) as response:
                    duration = time.time() - start_time
                    
                    if response.status in [200, 202]:  # Accept both sync and async responses
                        data = await response.json()
                        results.append(ValidationResult(
                            test_name="Inter-service Communication: Interpreter -> Orchestrator",
                            success=True,
                            duration=duration,
                            details={
                                "response_status": response.status,
                                "execution_id": data.get("execution_id"),
                                "workflow_name": data.get("workflow_name")
                            }
                        ))
                    else:
                        results.append(ValidationResult(
                            test_name="Inter-service Communication: Interpreter -> Orchestrator",
                            success=False,
                            duration=duration,
                            details={"status_code": response.status},
                            error_message=f"Unexpected status: {response.status}"
                        ))
            
            except Exception as e:
                duration = time.time() - start_time
                results.append(ValidationResult(
                    test_name="Inter-service Communication: Interpreter -> Orchestrator",
                    success=False,
                    duration=duration,
                    details={},
                    error_message=str(e)
                ))
            
            # Test LLM Gateway connectivity
            start_time = time.time()
            try:
                test_llm_query = {
                    "prompt": "Hello, this is a test query",
                    "max_tokens": 50
                }
                
                async with session.post(f"{self.services['llm_gateway']}/query",
                                      json=test_llm_query,
                                      timeout=aiohttp.ClientTimeout(total=20)) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        results.append(ValidationResult(
                            test_name="LLM Gateway Connectivity",
                            success=True,
                            duration=duration,
                            details={
                                "provider": data.get("provider"),
                                "tokens_used": data.get("tokens_used"),
                                "response_length": len(data.get("response", ""))
                            }
                        ))
                    else:
                        results.append(ValidationResult(
                            test_name="LLM Gateway Connectivity",
                            success=False,
                            duration=duration,
                            details={"status_code": response.status},
                            error_message=f"LLM Gateway error: {response.status}"
                        ))
            
            except Exception as e:
                duration = time.time() - start_time
                results.append(ValidationResult(
                    test_name="LLM Gateway Connectivity",
                    success=False,
                    duration=duration,
                    details={},
                    error_message=str(e)
                ))
        
        return results

    async def _validate_query_processing(self) -> List[ValidationResult]:
        """Validate natural language query processing capabilities."""
        results = []
        
        async with aiohttp.ClientSession() as session:
            for i, test_case in enumerate(self.test_queries[:2]):  # Test first 2 queries
                start_time = time.time()
                
                try:
                    # Test query interpretation
                    interpret_payload = {
                        "query": test_case["query"],
                        "user_id": f"test_user_{i}"
                    }
                    
                    async with session.post(f"{self.services['interpreter']}/interpret-query",
                                          json=interpret_payload,
                                          timeout=aiohttp.ClientTimeout(total=15)) as response:
                        duration = time.time() - start_time
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            # Validate response structure
                            has_intent = "intent" in data
                            has_entities = "entities" in data
                            has_confidence = "confidence" in data
                            
                            results.append(ValidationResult(
                                test_name=f"Query Processing: Test Case {i+1}",
                                success=has_intent and has_entities and has_confidence,
                                duration=duration,
                                details={
                                    "query": test_case["query"],
                                    "intent": data.get("intent"),
                                    "entities": data.get("entities", {}),
                                    "confidence": data.get("confidence", 0),
                                    "response_structure_valid": has_intent and has_entities and has_confidence
                                },
                                warnings=[] if (has_intent and has_entities and has_confidence) else ["Missing required response fields"]
                            ))
                        else:
                            results.append(ValidationResult(
                                test_name=f"Query Processing: Test Case {i+1}",
                                success=False,
                                duration=duration,
                                details={"status_code": response.status},
                                error_message=f"Query processing failed: {response.status}"
                            ))
                
                except Exception as e:
                    duration = time.time() - start_time
                    results.append(ValidationResult(
                        test_name=f"Query Processing: Test Case {i+1}",
                        success=False,
                        duration=duration,
                        details={"query": test_case["query"]},
                        error_message=str(e)
                    ))
        
        return results

    async def _validate_workflow_execution(self) -> List[ValidationResult]:
        """Validate workflow orchestration and execution."""
        results = []
        
        async with aiohttp.ClientSession() as session:
            # Test workflow template availability
            start_time = time.time()
            try:
                async with session.get(f"{self.services['interpreter']}/workflows/templates",
                                     timeout=aiohttp.ClientTimeout(total=10)) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        templates = await response.json()
                        template_count = len(templates.get("templates", []))
                        
                        results.append(ValidationResult(
                            test_name="Workflow Templates Availability",
                            success=template_count > 0,
                            duration=duration,
                            details={
                                "template_count": template_count,
                                "available_templates": [t.get("name") for t in templates.get("templates", [])]
                            }
                        ))
                    else:
                        results.append(ValidationResult(
                            test_name="Workflow Templates Availability",
                            success=False,
                            duration=duration,
                            details={"status_code": response.status},
                            error_message=f"Failed to get templates: {response.status}"
                        ))
            
            except Exception as e:
                duration = time.time() - start_time
                results.append(ValidationResult(
                    test_name="Workflow Templates Availability",
                    success=False,
                    duration=duration,
                    details={},
                    error_message=str(e)
                ))
            
            # Test direct workflow execution
            start_time = time.time()
            try:
                workflow_payload = {
                    "name": "document_generation",
                    "parameters": {
                        "content_type": "technical_specification",
                        "format": "json",
                        "user_id": "test_validator"
                    }
                }
                
                async with session.post(f"{self.services['interpreter']}/workflows/execute-direct",
                                      json=workflow_payload,
                                      timeout=aiohttp.ClientTimeout(total=30)) as response:
                    duration = time.time() - start_time
                    
                    if response.status in [200, 202]:
                        data = await response.json()
                        results.append(ValidationResult(
                            test_name="Direct Workflow Execution",
                            success=True,
                            duration=duration,
                            details={
                                "execution_id": data.get("execution_id"),
                                "workflow_name": data.get("workflow_name"),
                                "status": data.get("status"),
                                "response_type": "async" if response.status == 202 else "sync"
                            }
                        ))
                    else:
                        results.append(ValidationResult(
                            test_name="Direct Workflow Execution",
                            success=False,
                            duration=duration,
                            details={"status_code": response.status},
                            error_message=f"Workflow execution failed: {response.status}"
                        ))
            
            except Exception as e:
                duration = time.time() - start_time
                results.append(ValidationResult(
                    test_name="Direct Workflow Execution",
                    success=False,
                    duration=duration,
                    details={},
                    error_message=str(e)
                ))
        
        return results

    async def _validate_document_generation(self) -> List[ValidationResult]:
        """Validate document generation in multiple formats."""
        results = []
        
        async with aiohttp.ClientSession() as session:
            # Test supported formats
            start_time = time.time()
            try:
                async with session.get(f"{self.services['interpreter']}/outputs/formats",
                                     timeout=aiohttp.ClientTimeout(total=5)) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        formats_data = await response.json()
                        supported_formats = formats_data.get("supported_formats", [])
                        
                        results.append(ValidationResult(
                            test_name="Supported Output Formats",
                            success=len(supported_formats) >= 3,  # Expect at least 3 formats
                            duration=duration,
                            details={
                                "supported_formats": supported_formats,
                                "format_count": len(supported_formats)
                            }
                        ))
                    else:
                        results.append(ValidationResult(
                            test_name="Supported Output Formats",
                            success=False,
                            duration=duration,
                            details={"status_code": response.status},
                            error_message=f"Failed to get formats: {response.status}"
                        ))
            
            except Exception as e:
                duration = time.time() - start_time
                results.append(ValidationResult(
                    test_name="Supported Output Formats",
                    success=False,
                    duration=duration,
                    details={},
                    error_message=str(e)
                ))
            
            # Test document generation in different formats
            for format_type in ["json", "markdown"]:  # Test core formats
                start_time = time.time()
                
                try:
                    generation_payload = {
                        "query": f"Generate a {format_type} document about API testing",
                        "format": format_type,
                        "user_id": "validator"
                    }
                    
                    async with session.post(f"{self.services['interpreter']}/execute-query",
                                          json=generation_payload,
                                          timeout=aiohttp.ClientTimeout(total=45)) as response:
                        duration = time.time() - start_time
                        
                        if response.status in [200, 202]:
                            data = await response.json()
                            
                            # Store generated document info for later validation
                            self.generated_documents.append({
                                "format": format_type,
                                "execution_id": data.get("execution_id"),
                                "document_id": data.get("document_id"),
                                "file_id": data.get("file_id"),
                                "download_url": data.get("download_url")
                            })
                            
                            results.append(ValidationResult(
                                test_name=f"Document Generation: {format_type.upper()}",
                                success=True,
                                duration=duration,
                                details={
                                    "format": format_type,
                                    "execution_id": data.get("execution_id"),
                                    "document_id": data.get("document_id"),
                                    "file_size": data.get("size_bytes", 0),
                                    "status": data.get("status")
                                }
                            ))
                        else:
                            results.append(ValidationResult(
                                test_name=f"Document Generation: {format_type.upper()}",
                                success=False,
                                duration=duration,
                                details={"status_code": response.status},
                                error_message=f"Generation failed: {response.status}"
                            ))
                
                except Exception as e:
                    duration = time.time() - start_time
                    results.append(ValidationResult(
                        test_name=f"Document Generation: {format_type.upper()}",
                        success=False,
                        duration=duration,
                        details={"format": format_type},
                        error_message=str(e)
                    ))
        
        return results

    async def _validate_persistent_storage(self) -> List[ValidationResult]:
        """Validate document storage in doc_store with metadata."""
        results = []
        
        if not self.generated_documents:
            results.append(ValidationResult(
                test_name="Persistent Storage Validation",
                success=False,
                duration=0.0,
                details={},
                error_message="No generated documents available for storage validation"
            ))
            return results
        
        async with aiohttp.ClientSession() as session:
            for doc_info in self.generated_documents:
                document_id = doc_info.get("document_id")
                if not document_id:
                    continue
                
                start_time = time.time()
                
                try:
                    # Check if document exists in doc_store
                    async with session.get(f"{self.services['doc_store']}/documents/{document_id}",
                                         timeout=aiohttp.ClientTimeout(total=10)) as response:
                        duration = time.time() - start_time
                        
                        if response.status == 200:
                            doc_data = await response.json()
                            
                            # Validate document metadata
                            has_content = "content" in doc_data or "content_url" in doc_data
                            has_metadata = "metadata" in doc_data
                            has_timestamp = "created_at" in doc_data.get("metadata", {})
                            
                            results.append(ValidationResult(
                                test_name=f"Persistent Storage: {doc_info['format']}",
                                success=has_content and has_metadata,
                                duration=duration,
                                details={
                                    "document_id": document_id,
                                    "format": doc_info["format"],
                                    "has_content": has_content,
                                    "has_metadata": has_metadata,
                                    "has_timestamp": has_timestamp,
                                    "content_type": doc_data.get("metadata", {}).get("content_type"),
                                    "file_size": doc_data.get("metadata", {}).get("size_bytes", 0)
                                }
                            ))
                        else:
                            results.append(ValidationResult(
                                test_name=f"Persistent Storage: {doc_info['format']}",
                                success=False,
                                duration=duration,
                                details={"document_id": document_id, "status_code": response.status},
                                error_message=f"Document not found in storage: {response.status}"
                            ))
                
                except Exception as e:
                    duration = time.time() - start_time
                    results.append(ValidationResult(
                        test_name=f"Persistent Storage: {doc_info['format']}",
                        success=False,
                        duration=duration,
                        details={"document_id": document_id},
                        error_message=str(e)
                    ))
        
        return results

    async def _validate_provenance_tracking(self) -> List[ValidationResult]:
        """Validate document provenance and audit trail capabilities."""
        results = []
        
        if not self.generated_documents:
            results.append(ValidationResult(
                test_name="Provenance Tracking Validation",
                success=False,
                duration=0.0,
                details={},
                error_message="No generated documents available for provenance validation"
            ))
            return results
        
        async with aiohttp.ClientSession() as session:
            for doc_info in self.generated_documents:
                document_id = doc_info.get("document_id")
                if not document_id:
                    continue
                
                start_time = time.time()
                
                try:
                    # Get document provenance
                    async with session.get(f"{self.services['interpreter']}/documents/{document_id}/provenance",
                                         timeout=aiohttp.ClientTimeout(total=10)) as response:
                        duration = time.time() - start_time
                        
                        if response.status == 200:
                            provenance_data = await response.json()
                            
                            # Validate provenance structure
                            has_workflow_info = "workflow_execution" in provenance_data
                            has_services_chain = "services_chain" in provenance_data
                            has_user_context = "user_context" in provenance_data
                            has_timestamps = "creation_timestamp" in provenance_data
                            
                            # Check for data lineage
                            has_data_lineage = "data_lineage" in provenance_data
                            
                            results.append(ValidationResult(
                                test_name=f"Provenance Tracking: {doc_info['format']}",
                                success=has_workflow_info and has_services_chain and has_user_context,
                                duration=duration,
                                details={
                                    "document_id": document_id,
                                    "format": doc_info["format"],
                                    "has_workflow_info": has_workflow_info,
                                    "has_services_chain": has_services_chain,
                                    "has_user_context": has_user_context,
                                    "has_timestamps": has_timestamps,
                                    "has_data_lineage": has_data_lineage,
                                    "services_used": len(provenance_data.get("services_chain", [])),
                                    "execution_id": provenance_data.get("workflow_execution", {}).get("execution_id")
                                }
                            ))
                        else:
                            results.append(ValidationResult(
                                test_name=f"Provenance Tracking: {doc_info['format']}",
                                success=False,
                                duration=duration,
                                details={"document_id": document_id, "status_code": response.status},
                                error_message=f"Provenance data not available: {response.status}"
                            ))
                
                except Exception as e:
                    duration = time.time() - start_time
                    results.append(ValidationResult(
                        test_name=f"Provenance Tracking: {doc_info['format']}",
                        success=False,
                        duration=duration,
                        details={"document_id": document_id},
                        error_message=str(e)
                    ))
        
        return results

    async def _validate_document_retrieval(self) -> List[ValidationResult]:
        """Validate document download and retrieval capabilities."""
        results = []
        
        if not self.generated_documents:
            results.append(ValidationResult(
                test_name="Document Retrieval Validation",
                success=False,
                duration=0.0,
                details={},
                error_message="No generated documents available for retrieval validation"
            ))
            return results
        
        async with aiohttp.ClientSession() as session:
            for doc_info in self.generated_documents:
                document_id = doc_info.get("document_id")
                if not document_id:
                    continue
                
                start_time = time.time()
                
                try:
                    # Test document download
                    async with session.get(f"{self.services['doc_store']}/documents/{document_id}/download",
                                         timeout=aiohttp.ClientTimeout(total=15)) as response:
                        duration = time.time() - start_time
                        
                        if response.status == 200:
                            content = await response.read()
                            content_length = len(content)
                            
                            results.append(ValidationResult(
                                test_name=f"Document Retrieval: {doc_info['format']}",
                                success=content_length > 0,
                                duration=duration,
                                details={
                                    "document_id": document_id,
                                    "format": doc_info["format"],
                                    "content_length": content_length,
                                    "content_type": response.headers.get("content-type", "unknown"),
                                    "has_content": content_length > 0
                                }
                            ))
                        else:
                            results.append(ValidationResult(
                                test_name=f"Document Retrieval: {doc_info['format']}",
                                success=False,
                                duration=duration,
                                details={"document_id": document_id, "status_code": response.status},
                                error_message=f"Download failed: {response.status}"
                            ))
                
                except Exception as e:
                    duration = time.time() - start_time
                    results.append(ValidationResult(
                        test_name=f"Document Retrieval: {doc_info['format']}",
                        success=False,
                        duration=duration,
                        details={"document_id": document_id},
                        error_message=str(e)
                    ))
        
        return results

    async def _validate_e2e_integration(self) -> List[ValidationResult]:
        """Validate complete end-to-end integration flow."""
        results = []
        
        # Test complete workflow: Query → Generation → Storage → Retrieval
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Execute complete E2E query
                e2e_payload = {
                    "query": "Create a comprehensive API testing guide with examples",
                    "format": "markdown",
                    "user_id": "e2e_validator"
                }
                
                async with session.post(f"{self.services['interpreter']}/execute-query",
                                      json=e2e_payload,
                                      timeout=aiohttp.ClientTimeout(total=60)) as response:
                    
                    if response.status in [200, 202]:
                        e2e_data = await response.json()
                        execution_id = e2e_data.get("execution_id")
                        document_id = e2e_data.get("document_id")
                        
                        # Step 2: Verify execution trace
                        if execution_id:
                            async with session.get(f"{self.services['interpreter']}/workflows/{execution_id}/trace",
                                                 timeout=aiohttp.ClientTimeout(total=10)) as trace_response:
                                trace_available = trace_response.status == 200
                        else:
                            trace_available = False
                        
                        # Step 3: Verify document in storage
                        if document_id:
                            async with session.get(f"{self.services['doc_store']}/documents/{document_id}",
                                                 timeout=aiohttp.ClientTimeout(total=10)) as doc_response:
                                doc_stored = doc_response.status == 200
                        else:
                            doc_stored = False
                        
                        # Step 4: Verify provenance
                        if document_id:
                            async with session.get(f"{self.services['interpreter']}/documents/{document_id}/provenance",
                                                 timeout=aiohttp.ClientTimeout(total=10)) as prov_response:
                                provenance_available = prov_response.status == 200
                        else:
                            provenance_available = False
                        
                        duration = time.time() - start_time
                        
                        # Overall E2E success requires all steps to work
                        e2e_success = all([
                            execution_id is not None,
                            document_id is not None,
                            trace_available,
                            doc_stored,
                            provenance_available
                        ])
                        
                        results.append(ValidationResult(
                            test_name="Complete E2E Integration Flow",
                            success=e2e_success,
                            duration=duration,
                            details={
                                "execution_id": execution_id,
                                "document_id": document_id,
                                "trace_available": trace_available,
                                "document_stored": doc_stored,
                                "provenance_available": provenance_available,
                                "steps_completed": sum([execution_id is not None, document_id is not None, 
                                                      trace_available, doc_stored, provenance_available]),
                                "total_steps": 5
                            },
                            warnings=[] if e2e_success else ["One or more E2E steps failed"]
                        ))
                    else:
                        duration = time.time() - start_time
                        results.append(ValidationResult(
                            test_name="Complete E2E Integration Flow",
                            success=False,
                            duration=duration,
                            details={"status_code": response.status},
                            error_message=f"E2E query failed: {response.status}"
                        ))
        
        except Exception as e:
            duration = time.time() - start_time
            results.append(ValidationResult(
                test_name="Complete E2E Integration Flow",
                success=False,
                duration=duration,
                details={},
                error_message=str(e)
            ))
        
        return results

    async def _validate_performance_reliability(self) -> List[ValidationResult]:
        """Validate performance and reliability characteristics."""
        results = []
        
        # Test response time performance
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            # Measure response times for health checks
            for i in range(5):
                start_time = time.time()
                try:
                    async with session.get(f"{self.services['interpreter']}/health",
                                         timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            response_times.append(time.time() - start_time)
                except:
                    pass  # Skip failed requests for performance measurement
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                results.append(ValidationResult(
                    test_name="Response Time Performance",
                    success=avg_response_time < 1.0,  # Average should be under 1 second
                    duration=avg_response_time,
                    details={
                        "average_response_time": avg_response_time,
                        "max_response_time": max_response_time,
                        "samples": len(response_times),
                        "performance_threshold": "1.0s"
                    },
                    warnings=[] if avg_response_time < 1.0 else ["Response time above threshold"]
                ))
            
            # Test concurrent request handling
            start_time = time.time()
            try:
                # Make 3 concurrent requests
                tasks = []
                for i in range(3):
                    tasks.append(session.get(f"{self.services['interpreter']}/intents",
                                           timeout=aiohttp.ClientTimeout(total=10)))
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                successful_requests = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
                
                duration = time.time() - start_time
                
                results.append(ValidationResult(
                    test_name="Concurrent Request Handling",
                    success=successful_requests >= 2,  # At least 2/3 should succeed
                    duration=duration,
                    details={
                        "concurrent_requests": 3,
                        "successful_requests": successful_requests,
                        "success_rate": (successful_requests / 3) * 100,
                        "total_duration": duration
                    }
                ))
                
                # Close responses
                for response in responses:
                    if not isinstance(response, Exception):
                        response.close()
            
            except Exception as e:
                duration = time.time() - start_time
                results.append(ValidationResult(
                    test_name="Concurrent Request Handling",
                    success=False,
                    duration=duration,
                    details={},
                    error_message=str(e)
                ))
        
        return results

    def _generate_validation_summary(self) -> Dict[str, Any]:
        """Generate comprehensive validation summary."""
        if not self.results:
            return {}
        
        # Categorize results by test type
        categories = {}
        for result in self.results:
            category = result.test_name.split(":")[0]
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0, "avg_duration": 0}
            
            categories[category]["total"] += 1
            if result.success:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
        
        # Calculate average durations
        for category in categories:
            category_results = [r for r in self.results if r.test_name.startswith(category)]
            if category_results:
                categories[category]["avg_duration"] = sum(r.duration for r in category_results) / len(category_results)
        
        # Generate recommendations
        recommendations = []
        failed_results = [r for r in self.results if not r.success]
        
        if failed_results:
            recommendations.append(f"Address {len(failed_results)} failed tests to improve system reliability")
        
        # Performance recommendations
        slow_tests = [r for r in self.results if r.duration > 5.0]
        if slow_tests:
            recommendations.append(f"Optimize performance for {len(slow_tests)} slow operations")
        
        # Service-specific recommendations
        service_failures = {}
        for result in failed_results:
            for service_name in self.services.keys():
                if service_name in result.test_name.lower():
                    service_failures[service_name] = service_failures.get(service_name, 0) + 1
        
        for service, failure_count in service_failures.items():
            if failure_count > 1:
                recommendations.append(f"Investigate {service} service - {failure_count} test failures")
        
        return {
            "test_categories": categories,
            "failed_tests": len(failed_results),
            "critical_failures": len([r for r in failed_results if "critical" in r.test_name.lower()]),
            "performance_issues": len(slow_tests),
            "generated_documents": len(self.generated_documents),
            "recommendations": recommendations,
            "validation_timestamp": datetime.now().isoformat()
        }

    def display_results(self, suite: E2EValidationSuite, format_type: str = "table"):
        """Display validation results in specified format."""
        if format_type == "json":
            print(json.dumps(asdict(suite), indent=2, default=str))
            return
        
        # Display summary
        console.print("\n")
        console.print("🎯 E2E Document Persistence Validation Results", style="bold blue")
        console.print("=" * 80)
        
        # Overall metrics
        success_color = "green" if suite.success_rate >= 90 else "yellow" if suite.success_rate >= 70 else "red"
        summary_panel = Panel.fit(
            f"[bold]Overall Results[/bold]\n"
            f"Total Tests: {suite.total_tests}\n"
            f"Successful: [green]{suite.successful_tests}[/green]\n"
            f"Failed: [red]{suite.failed_tests}[/red]\n"
            f"Success Rate: [{success_color}]{suite.success_rate:.1f}%[/]\n"
            f"Total Duration: {suite.total_duration:.2f}s\n"
            f"Generated Documents: {len(self.generated_documents)}",
            title="📊 Summary",
            border_style=success_color
        )
        console.print(summary_panel)
        
        # Detailed results table
        table = Table(title="🧪 Detailed Test Results")
        table.add_column("Test Name", style="cyan", width=40)
        table.add_column("Status", width=10)
        table.add_column("Duration", style="yellow", width=10)
        table.add_column("Details", width=30)
        
        for result in suite.results:
            status_emoji = "✅" if result.success else "❌"
            status_text = f"{status_emoji} {'PASS' if result.success else 'FAIL'}"
            
            # Truncate details for display
            details_str = str(result.details)
            if len(details_str) > 50:
                details_str = details_str[:47] + "..."
            
            table.add_row(
                result.test_name,
                status_text,
                f"{result.duration:.3f}s",
                details_str
            )
        
        console.print(table)
        
        # Display recommendations
        if suite.summary.get("recommendations"):
            recommendations_panel = Panel.fit(
                "\n".join(f"• {rec}" for rec in suite.summary["recommendations"]),
                title="💡 Recommendations",
                border_style="blue"
            )
            console.print(recommendations_panel)
        
        # Display generated documents
        if self.generated_documents:
            docs_table = Table(title="📄 Generated Documents")
            docs_table.add_column("Format", style="cyan")
            docs_table.add_column("Document ID", style="blue")
            docs_table.add_column("Execution ID", style="magenta")
            
            for doc in self.generated_documents:
                docs_table.add_row(
                    doc.get("format", "unknown"),
                    doc.get("document_id", "N/A")[:20] + "..." if doc.get("document_id") and len(doc.get("document_id", "")) > 20 else doc.get("document_id", "N/A"),
                    doc.get("execution_id", "N/A")[:20] + "..." if doc.get("execution_id") and len(doc.get("execution_id", "")) > 20 else doc.get("execution_id", "N/A")
                )
            
            console.print(docs_table)

async def main():
    """Main function to run E2E validation."""
    parser = argparse.ArgumentParser(description="E2E Document Persistence Validation")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive validation suite")
    parser.add_argument("--quick", action="store_true", help="Run quick validation (health + basic integration)")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")
    parser.add_argument("--base-url", default="http://localhost", help="Base URL for services")
    
    args = parser.parse_args()
    
    validator = DocumentPersistenceValidator(base_url=args.base_url)
    
    if args.quick:
        console.print("[blue]Running quick E2E validation...[/blue]")
        # Run only essential tests
        health_results = await validator._validate_service_health()
        integration_results = await validator._validate_service_integration()
        validator.results.extend(health_results + integration_results)
        
        successful = sum(1 for r in validator.results if r.success)
        total = len(validator.results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        suite = E2EValidationSuite(
            total_tests=total,
            successful_tests=successful,
            failed_tests=total - successful,
            total_duration=sum(r.duration for r in validator.results),
            success_rate=success_rate,
            results=validator.results,
            summary=validator._generate_validation_summary()
        )
    else:
        console.print("[blue]Running comprehensive E2E validation...[/blue]")
        suite = await validator.run_comprehensive_validation()
    
    validator.display_results(suite, args.format)
    
    # Return appropriate exit code
    return 0 if suite.success_rate >= 70 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
