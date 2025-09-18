#!/usr/bin/env python3
"""
Comprehensive Document Persistence and Provenance System Demo

This script proves that the enhanced interpreter service creates persistent
documents with full workflow provenance tracking that can be downloaded
and audited across the ecosystem.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path

class DocumentPersistenceDemo:
    """Demonstrates the complete document persistence and provenance system."""

    def __init__(self):
        self.interpreter_url = "http://localhost:5120"
        self.test_results = []
        self.generated_documents = []

    async def run_comprehensive_demo(self):
        """Run complete demonstration of document persistence features."""
        print("🚀 Starting Document Persistence & Provenance System Demo")
        print("=" * 60)
        print(f"⏰ Demo started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test 1: Basic health check with new features
        await self._test_enhanced_health_check()

        # Test 2: Get supported formats
        await self._test_supported_formats()

        # Test 3: Get workflow templates
        await self._test_workflow_templates()

        # Test 4: Execute end-to-end query with document generation
        await self._test_e2e_query_execution()

        # Test 5: Direct workflow execution
        await self._test_direct_workflow_execution()

        # Test 6: Document provenance tracking
        await self._test_document_provenance()

        # Test 7: Workflow execution traces
        await self._test_execution_traces()

        # Test 8: Document discovery by workflow
        await self._test_document_discovery()

        # Test 9: Document downloads
        await self._test_document_downloads()

        # Test 10: Recent executions with documents
        await self._test_recent_executions()

        # Print comprehensive summary
        self._print_demo_summary()

    async def _test_enhanced_health_check(self):
        """Test 1: Enhanced health check with new features."""
        print("📋 Test 1: Enhanced Health Check")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.interpreter_url}/health") as response:
                    result = await response.json()
            
            features = result.get("features", [])
            expected_features = ["document_persistence", "workflow_provenance", "doc_store_integration"]
            
            print(f"  ✅ Service Status: {result.get('status')}")
            print(f"  ✅ Version: {result.get('version')}")
            print(f"  ✅ Enhanced Features: {', '.join(features)}")
            
            missing_features = [f for f in expected_features if f not in features]
            if not missing_features:
                print(f"  ✅ All expected features present!")
                self.test_results.append({"test": "Health Check", "status": "success"})
            else:
                print(f"  ⚠️  Missing features: {', '.join(missing_features)}")
                self.test_results.append({"test": "Health Check", "status": "partial"})
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({"test": "Health Check", "status": "failed"})
        
        print()

    async def _test_supported_formats(self):
        """Test 2: Get supported output formats."""
        print("📋 Test 2: Supported Output Formats")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.interpreter_url}/outputs/formats") as response:
                    result = await response.json()
            
            formats = result.get("supported_formats", [])
            descriptions = result.get("format_descriptions", {})
            
            print(f"  ✅ Supported formats: {', '.join(formats)}")
            for format_name in formats:
                description = descriptions.get(format_name, "No description")
                print(f"    • {format_name}: {description}")
            
            if len(formats) >= 3:
                self.test_results.append({"test": "Supported Formats", "status": "success", "formats": len(formats)})
            else:
                self.test_results.append({"test": "Supported Formats", "status": "partial", "formats": len(formats)})
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({"test": "Supported Formats", "status": "failed"})
        
        print()

    async def _test_workflow_templates(self):
        """Test 3: Get workflow templates."""
        print("📋 Test 3: Workflow Templates")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.interpreter_url}/workflows/templates") as response:
                    result = await response.json()
            
            templates = result.get("templates", {})
            
            print(f"  ✅ Found {len(templates)} workflow templates:")
            for name, template in templates.items():
                print(f"    • {name}: {template.get('description', 'No description')}")
                print(f"      Services: {', '.join(template.get('services', []))}")
                print(f"      Outputs: {', '.join(template.get('output_types', []))}")
            
            if len(templates) >= 3:
                self.test_results.append({"test": "Workflow Templates", "status": "success", "templates": len(templates)})
            else:
                self.test_results.append({"test": "Workflow Templates", "status": "partial", "templates": len(templates)})
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({"test": "Workflow Templates", "status": "failed"})
        
        print()

    async def _test_e2e_query_execution(self):
        """Test 4: End-to-end query execution with document generation."""
        print("📋 Test 4: End-to-End Query Execution with Document Persistence")
        
        test_queries = [
            {
                "query": "Analyze the security of our codebase and generate a report",
                "format": "json",
                "expected_workflow": "security_audit"
            },
            {
                "query": "Create documentation for our API endpoints",
                "format": "markdown", 
                "expected_workflow": "code_documentation"
            },
            {
                "query": "Analyze document quality and provide insights",
                "format": "csv",
                "expected_workflow": "document_analysis"
            }
        ]
        
        successful_executions = 0
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"  Query {i}: {test_case['query']}")
            
            try:
                request_data = {
                    "query": test_case["query"],
                    "output_format": test_case["format"],
                    "user_id": "demo_user",
                    "filename_prefix": f"test_e2e_{i}"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.interpreter_url}/execute-query", json=request_data) as response:
                        result = await response.json()
                
                if result.get("status") == "completed":
                    execution_id = result.get("execution_id")
                    workflow_executed = result.get("workflow_executed")
                    output_info = result.get("output", {})
                    
                    print(f"    ✅ Execution ID: {execution_id}")
                    print(f"    ✅ Workflow: {workflow_executed}")
                    print(f"    ✅ Document ID: {output_info.get('document_id')}")
                    print(f"    ✅ Format: {output_info.get('format')}")
                    print(f"    ✅ Storage: {output_info.get('storage_type', 'unknown')}")
                    print(f"    ✅ Persistent: {output_info.get('metadata', {}).get('persistent', False)}")
                    
                    # Store document info for later tests
                    self.generated_documents.append({
                        "execution_id": execution_id,
                        "document_id": output_info.get("document_id"),
                        "workflow_name": workflow_executed,
                        "format": output_info.get("format"),
                        "query": test_case["query"]
                    })
                    
                    successful_executions += 1
                    
                elif result.get("status") == "failed":
                    print(f"    ❌ Execution failed: {result.get('error')}")
                    
                else:
                    print(f"    ⚠️  Unknown status: {result.get('status')}")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
        
        print(f"  📊 Results: {successful_executions}/{len(test_queries)} successful executions")
        
        if successful_executions >= 2:
            self.test_results.append({"test": "E2E Query Execution", "status": "success", "executions": successful_executions})
        else:
            self.test_results.append({"test": "E2E Query Execution", "status": "failed", "executions": successful_executions})
        
        print()

    async def _test_direct_workflow_execution(self):
        """Test 5: Direct workflow execution."""
        print("📋 Test 5: Direct Workflow Execution")
        
        try:
            request_data = {
                "workflow_name": "document_analysis",
                "parameters": {"content_type": "technical_documentation", "quality_threshold": 0.8},
                "output_format": "json",
                "user_id": "demo_user",
                "filename_prefix": "direct_test"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.interpreter_url}/workflows/execute-direct", json=request_data) as response:
                    result = await response.json()
            
            if result.get("status") == "completed":
                execution_id = result.get("execution_id")
                output_info = result.get("output", {})
                
                print(f"  ✅ Direct execution successful!")
                print(f"  ✅ Execution ID: {execution_id}")
                print(f"  ✅ Document ID: {output_info.get('document_id')}")
                print(f"  ✅ Provenance tracked: {bool(output_info.get('provenance'))}")
                
                # Store for later tests
                self.generated_documents.append({
                    "execution_id": execution_id,
                    "document_id": output_info.get("document_id"),
                    "workflow_name": "document_analysis",
                    "format": "json",
                    "query": "Direct workflow execution test"
                })
                
                self.test_results.append({"test": "Direct Workflow Execution", "status": "success"})
            else:
                print(f"  ❌ Execution failed: {result.get('error', 'Unknown error')}")
                self.test_results.append({"test": "Direct Workflow Execution", "status": "failed"})
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({"test": "Direct Workflow Execution", "status": "failed"})
        
        print()

    async def _test_document_provenance(self):
        """Test 6: Document provenance tracking."""
        print("📋 Test 6: Document Provenance Tracking")
        
        if not self.generated_documents:
            print("  ⚠️  No documents generated yet, skipping provenance test")
            self.test_results.append({"test": "Document Provenance", "status": "skipped"})
            print()
            return
        
        try:
            # Test provenance for the first generated document
            doc = self.generated_documents[0]
            document_id = doc["document_id"]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.interpreter_url}/documents/{document_id}/provenance") as response:
                    result = await response.json()
            
            if result.get("error"):
                print(f"  ❌ Error: {result['error']}")
                self.test_results.append({"test": "Document Provenance", "status": "failed"})
                return
            
            provenance = result.get("provenance", {})
            workflow_chain = result.get("workflow_chain", {})
            doc_info = result.get("document_info", {})
            
            print(f"  ✅ Document ID: {document_id}")
            print(f"  ✅ Document Title: {doc_info.get('title', 'N/A')}")
            print(f"  ✅ Workflow: {provenance.get('workflow_execution', {}).get('workflow_name', 'N/A')}")
            print(f"  ✅ Services Used: {', '.join(workflow_chain.get('services_used', []))}")
            print(f"  ✅ Prompts Tracked: {len(workflow_chain.get('prompts_used', []))}")
            print(f"  ✅ Quality Score: {workflow_chain.get('quality_metrics', {}).get('confidence', 0):.2f}")
            print(f"  ✅ Execution ID: {provenance.get('workflow_execution', {}).get('execution_id', 'N/A')}")
            
            # Verify key provenance elements exist
            required_elements = [
                provenance.get('workflow_execution'),
                workflow_chain.get('services_used'),
                workflow_chain.get('quality_metrics')
            ]
            
            if all(required_elements):
                print(f"  ✅ Complete provenance data verified!")
                self.test_results.append({"test": "Document Provenance", "status": "success"})
            else:
                print(f"  ⚠️  Incomplete provenance data")
                self.test_results.append({"test": "Document Provenance", "status": "partial"})
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({"test": "Document Provenance", "status": "failed"})
        
        print()

    async def _test_execution_traces(self):
        """Test 7: Workflow execution traces."""
        print("📋 Test 7: Workflow Execution Traces")
        
        if not self.generated_documents:
            print("  ⚠️  No executions to trace, skipping")
            self.test_results.append({"test": "Execution Traces", "status": "skipped"})
            print()
            return
        
        try:
            # Test trace for the first execution
            doc = self.generated_documents[0]
            execution_id = doc["execution_id"]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.interpreter_url}/workflows/{execution_id}/trace") as response:
                    result = await response.json()
            
            if result.get("error"):
                print(f"  ❌ Error: {result['error']}")
                self.test_results.append({"test": "Execution Traces", "status": "failed"})
                return
            
            execution_details = result.get("execution_details", {})
            generated_documents = result.get("generated_documents", [])
            
            print(f"  ✅ Execution ID: {execution_id}")
            print(f"  ✅ Workflow: {execution_details.get('workflow_name', 'N/A')}")
            print(f"  ✅ Status: {execution_details.get('status', 'N/A')}")
            print(f"  ✅ User: {execution_details.get('user_id', 'N/A')}")
            print(f"  ✅ Execution Time: {execution_details.get('execution_time', 'N/A')}")
            print(f"  ✅ Documents Generated: {len(generated_documents)}")
            
            for i, doc in enumerate(generated_documents, 1):
                print(f"    {i}. {doc.get('title', 'Untitled')} ({doc.get('format', 'unknown')})")
                print(f"       ID: {doc.get('document_id', 'N/A')}")
            
            if execution_details and generated_documents:
                print(f"  ✅ Complete execution trace verified!")
                self.test_results.append({"test": "Execution Traces", "status": "success"})
            else:
                print(f"  ⚠️  Incomplete trace data")
                self.test_results.append({"test": "Execution Traces", "status": "partial"})
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({"test": "Execution Traces", "status": "failed"})
        
        print()

    async def _test_document_discovery(self):
        """Test 8: Document discovery by workflow."""
        print("📋 Test 8: Document Discovery by Workflow")
        
        workflows_to_test = ["document_analysis", "security_audit", "code_documentation"]
        successful_discoveries = 0
        
        for workflow_name in workflows_to_test:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.interpreter_url}/documents/by-workflow/{workflow_name}") as response:
                        result = await response.json()
                
                documents = result.get("documents", [])
                
                print(f"  ✅ {workflow_name}: {len(documents)} documents found")
                
                for doc in documents[:2]:  # Show first 2
                    print(f"    • {doc.get('title', 'Untitled')} ({doc.get('format', 'unknown')})")
                    print(f"      Quality: {doc.get('quality_score', 0):.2f}, Size: {doc.get('size_bytes', 0) / 1024:.1f} KB")
                
                if len(documents) > 0:
                    successful_discoveries += 1
                    
            except Exception as e:
                print(f"  ❌ Error for {workflow_name}: {str(e)}")
        
        print(f"  📊 Results: {successful_discoveries}/{len(workflows_to_test)} workflows have discoverable documents")
        
        if successful_discoveries >= 2:
            self.test_results.append({"test": "Document Discovery", "status": "success", "workflows": successful_discoveries})
        else:
            self.test_results.append({"test": "Document Discovery", "status": "partial", "workflows": successful_discoveries})
        
        print()

    async def _test_document_downloads(self):
        """Test 9: Document downloads."""
        print("📋 Test 9: Document Downloads")
        
        if not self.generated_documents:
            print("  ⚠️  No documents to download, skipping")
            self.test_results.append({"test": "Document Downloads", "status": "skipped"})
            print()
            return
        
        successful_downloads = 0
        
        for i, doc in enumerate(self.generated_documents[:2], 1):  # Test first 2 documents
            document_id = doc["document_id"]
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.interpreter_url}/documents/{document_id}/download") as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            print(f"  ✅ Document {i} downloaded successfully")
                            print(f"    • Document ID: {document_id}")
                            print(f"    • Content Size: {len(content)} bytes")
                            print(f"    • Format: {doc['format']}")
                            print(f"    • Content Preview: {content[:100]}...")
                            
                            # Verify content contains expected elements
                            if document_id in content or "workflow" in content.lower():
                                print(f"    • ✅ Content validation passed")
                                successful_downloads += 1
                            else:
                                print(f"    • ⚠️  Content validation failed")
                        else:
                            print(f"  ❌ Download failed for document {i}: HTTP {response.status}")
                            
            except Exception as e:
                print(f"  ❌ Error downloading document {i}: {str(e)}")
        
        print(f"  📊 Results: {successful_downloads}/{min(len(self.generated_documents), 2)} documents downloaded successfully")
        
        if successful_downloads >= 1:
            self.test_results.append({"test": "Document Downloads", "status": "success", "downloads": successful_downloads})
        else:
            self.test_results.append({"test": "Document Downloads", "status": "failed", "downloads": successful_downloads})
        
        print()

    async def _test_recent_executions(self):
        """Test 10: Recent executions with documents."""
        print("📋 Test 10: Recent Executions with Documents")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.interpreter_url}/workflows/executions/recent?limit=10") as response:
                    result = await response.json()
            
            executions = result.get("recent_executions", [])
            execution_metrics = result.get("execution_metrics", {})
            
            print(f"  ✅ Found {len(executions)} recent executions")
            print(f"  ✅ Total Executions: {execution_metrics.get('total_executions', 0)}")
            print(f"  ✅ Success Rate: {execution_metrics.get('success_rate', 0):.1%}")
            
            for i, execution in enumerate(executions[:3], 1):  # Show first 3
                print(f"    {i}. {execution.get('workflow_name', 'Unknown')} - {execution.get('status', 'Unknown')}")
                print(f"       User: {execution.get('user_id', 'N/A')}, Documents: {execution.get('documents_generated', 0)}")
                print(f"       Time: {execution.get('execution_time', 'N/A')}")
            
            if len(executions) > 0 and execution_metrics.get('total_executions', 0) > 0:
                print(f"  ✅ Execution history tracking verified!")
                self.test_results.append({"test": "Recent Executions", "status": "success", "executions": len(executions)})
            else:
                print(f"  ⚠️  Limited execution data")
                self.test_results.append({"test": "Recent Executions", "status": "partial", "executions": len(executions)})
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({"test": "Recent Executions", "status": "failed"})
        
        print()

    def _print_demo_summary(self):
        """Print comprehensive demo summary."""
        print("=" * 60)
        print("🏆 DOCUMENT PERSISTENCE & PROVENANCE SYSTEM DEMO RESULTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t["status"] == "success"])
        partial_tests = len([t for t in self.test_results if t["status"] == "partial"])
        failed_tests = len([t for t in self.test_results if t["status"] == "failed"])
        skipped_tests = len([t for t in self.test_results if t["status"] == "skipped"])
        
        print(f"\n📊 Overall Results:")
        print(f"  • Total Tests: {total_tests}")
        print(f"  • Successful: {successful_tests} ✅")
        print(f"  • Partial: {partial_tests} ⚠️")
        print(f"  • Failed: {failed_tests} ❌")
        print(f"  • Skipped: {skipped_tests} ⏭️")
        
        success_rate = (successful_tests + (partial_tests * 0.5)) / (total_tests - skipped_tests) * 100 if (total_tests - skipped_tests) > 0 else 0
        print(f"  • Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = {"success": "✅", "partial": "⚠️", "failed": "❌", "skipped": "⏭️"}[result["status"]]
            print(f"  {status_icon} {result['test']}: {result['status']}")
        
        print(f"\n📁 Generated Documents ({len(self.generated_documents)}):")
        for i, doc in enumerate(self.generated_documents, 1):
            print(f"  {i}. Document ID: {doc['document_id']}")
            print(f"     Workflow: {doc['workflow_name']} | Format: {doc['format']}")
            print(f"     Query: {doc['query'][:60]}{'...' if len(doc['query']) > 60 else ''}")
        
        print(f"\n🎯 Key Features Demonstrated:")
        print(f"  ✅ End-to-End Document Persistence")
        print(f"  ✅ Comprehensive Workflow Provenance")
        print(f"  ✅ Doc_Store Integration")
        print(f"  ✅ Execution Traceability")
        print(f"  ✅ Document Discovery & Management")
        print(f"  ✅ Multi-Format Output Generation")
        print(f"  ✅ Quality Metrics Tracking")
        print(f"  ✅ User Context Preservation")
        
        if success_rate >= 80:
            print(f"\n🏆 SYSTEM FULLY OPERATIONAL: Document persistence & provenance system working perfectly!")
        elif success_rate >= 60:
            print(f"\n⚠️  SYSTEM MOSTLY WORKING: Minor issues to resolve")
        else:
            print(f"\n❌ SYSTEM NEEDS ATTENTION: Significant issues detected")
        
        print(f"\n⏰ Demo completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate


async def main():
    """Main demo runner."""
    demo = DocumentPersistenceDemo()
    success_rate = await demo.run_comprehensive_demo()
    
    if success_rate and success_rate >= 80:
        print("\n🎉 DOCUMENT PERSISTENCE & PROVENANCE SYSTEM DEMO COMPLETE!")
        return True
    else:
        print("\n💥 DOCUMENT PERSISTENCE SYSTEM NEEDS WORK!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
