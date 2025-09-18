#!/usr/bin/env python3
"""
CLI Integration Test for Document Persistence System

This script tests the CLI commands that interact with the enhanced
interpreter service for document persistence and provenance features.
"""

import asyncio
import subprocess
import json
import time
from datetime import datetime

class CLIDocumentPersistenceTest:
    """Test the CLI integration with document persistence features."""

    def __init__(self):
        self.cli_path = "/Users/mykalthomas/Documents/work/Hackathon/services/cli/main.py"
        self.test_results = []
        self.generated_docs = []

    def run_cli_command(self, command_args):
        """Run a CLI command and return the result."""
        try:
            cmd = ["python", self.cli_path] + command_args
            result = subprocess.run(cmd, capture_output=True, text=True, cwd="/Users/mykalthomas/Documents/work/Hackathon")
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def test_cli_document_persistence(self):
        """Test CLI integration with document persistence features."""
        print("🚀 Starting CLI Document Persistence Integration Test")
        print("=" * 60)
        print(f"⏰ Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test 1: Check supported formats via CLI
        self._test_get_supported_formats()

        # Test 2: List workflow templates via CLI
        self._test_list_workflow_templates()

        # Test 3: Execute end-to-end query via CLI
        self._test_execute_e2e_query()

        # Test 4: Execute direct workflow via CLI
        self._test_execute_direct_workflow()

        # Test 5: Test document provenance via CLI
        self._test_document_provenance()

        # Test 6: Test workflow documents listing
        self._test_list_workflow_documents()

        # Test 7: Test execution trace
        self._test_execution_trace()

        # Print summary
        self._print_test_summary()

    def _test_get_supported_formats(self):
        """Test 1: Get supported formats via CLI."""
        print("📋 Test 1: Get Supported Formats via CLI")
        
        result = self.run_cli_command(["get-supported-formats"])
        
        if result["success"]:
            print(f"  ✅ CLI command executed successfully")
            print(f"  ✅ Output preview:")
            output_lines = result["stdout"].strip().split('\n')
            for line in output_lines[:5]:  # Show first 5 lines
                print(f"    {line}")
            
            if "json" in result["stdout"] and "markdown" in result["stdout"]:
                print(f"  ✅ Expected formats found in output")
                self.test_results.append({"test": "CLI Supported Formats", "status": "success"})
            else:
                print(f"  ⚠️  Expected formats not found")
                self.test_results.append({"test": "CLI Supported Formats", "status": "partial"})
        else:
            print(f"  ❌ CLI command failed: {result['stderr']}")
            self.test_results.append({"test": "CLI Supported Formats", "status": "failed"})
        
        print()

    def _test_list_workflow_templates(self):
        """Test 2: List workflow templates via CLI."""
        print("📋 Test 2: List Workflow Templates via CLI")
        
        result = self.run_cli_command(["list-workflow-templates"])
        
        if result["success"]:
            print(f"  ✅ CLI command executed successfully")
            print(f"  ✅ Output preview:")
            output_lines = result["stdout"].strip().split('\n')
            for line in output_lines[:5]:  # Show first 5 lines
                print(f"    {line}")
            
            if "document_analysis" in result["stdout"] or "security_audit" in result["stdout"]:
                print(f"  ✅ Expected templates found in output")
                self.test_results.append({"test": "CLI Workflow Templates", "status": "success"})
            else:
                print(f"  ⚠️  Expected templates not found")
                self.test_results.append({"test": "CLI Workflow Templates", "status": "partial"})
        else:
            print(f"  ❌ CLI command failed: {result['stderr']}")
            self.test_results.append({"test": "CLI Workflow Templates", "status": "failed"})
        
        print()

    def _test_execute_e2e_query(self):
        """Test 3: Execute end-to-end query via CLI."""
        print("📋 Test 3: Execute End-to-End Query via CLI")
        
        result = self.run_cli_command([
            "execute-e2e-query", 
            "Analyze our codebase for security vulnerabilities",
            "--format", "json",
            "--user-id", "cli_test_user"
        ])
        
        if result["success"]:
            print(f"  ✅ CLI command executed successfully")
            print(f"  ✅ Output preview:")
            output_lines = result["stdout"].strip().split('\n')
            for line in output_lines[:10]:  # Show first 10 lines
                print(f"    {line}")
            
            # Look for key indicators
            if ("Document ID" in result["stdout"] or "document_id" in result["stdout"]) and \
               ("Execution ID" in result["stdout"] or "execution_id" in result["stdout"]):
                print(f"  ✅ Document generation confirmed")
                self.test_results.append({"test": "CLI E2E Query", "status": "success"})
                
                # Try to extract document ID for later tests
                for line in output_lines:
                    if "Document ID:" in line:
                        doc_id = line.split("Document ID:")[-1].strip()
                        self.generated_docs.append({"id": doc_id, "type": "e2e_query"})
                        break
            else:
                print(f"  ⚠️  Document generation not confirmed")
                self.test_results.append({"test": "CLI E2E Query", "status": "partial"})
        else:
            print(f"  ❌ CLI command failed: {result['stderr']}")
            self.test_results.append({"test": "CLI E2E Query", "status": "failed"})
        
        print()

    def _test_execute_direct_workflow(self):
        """Test 4: Execute direct workflow via CLI."""
        print("📋 Test 4: Execute Direct Workflow via CLI")
        
        result = self.run_cli_command([
            "execute-direct-workflow",
            "--name", "document_analysis",
            "--format", "markdown",
            "--user-id", "cli_test_user"
        ])
        
        if result["success"]:
            print(f"  ✅ CLI command executed successfully")
            print(f"  ✅ Output preview:")
            output_lines = result["stdout"].strip().split('\n')
            for line in output_lines[:10]:  # Show first 10 lines
                print(f"    {line}")
            
            if ("Document ID" in result["stdout"] or "document_id" in result["stdout"]) and \
               ("markdown" in result["stdout"] or "Markdown" in result["stdout"]):
                print(f"  ✅ Direct workflow execution confirmed")
                self.test_results.append({"test": "CLI Direct Workflow", "status": "success"})
                
                # Try to extract document ID for later tests
                for line in output_lines:
                    if "Document ID:" in line:
                        doc_id = line.split("Document ID:")[-1].strip()
                        self.generated_docs.append({"id": doc_id, "type": "direct_workflow"})
                        break
            else:
                print(f"  ⚠️  Direct workflow execution not confirmed")
                self.test_results.append({"test": "CLI Direct Workflow", "status": "partial"})
        else:
            print(f"  ❌ CLI command failed: {result['stderr']}")
            self.test_results.append({"test": "CLI Direct Workflow", "status": "failed"})
        
        print()

    def _test_document_provenance(self):
        """Test 5: Test document provenance via CLI."""
        print("📋 Test 5: Document Provenance via CLI")
        
        if not self.generated_docs:
            print("  ⚠️  No document IDs available, testing with mock ID")
            doc_id = "doc_12345678"
        else:
            doc_id = self.generated_docs[0]["id"]
        
        result = self.run_cli_command([
            "get-document-provenance",
            "--doc-id", doc_id
        ])
        
        if result["success"]:
            print(f"  ✅ CLI command executed successfully")
            print(f"  ✅ Testing with Document ID: {doc_id}")
            print(f"  ✅ Output preview:")
            output_lines = result["stdout"].strip().split('\n')
            for line in output_lines[:8]:  # Show first 8 lines
                print(f"    {line}")
            
            if "Provenance" in result["stdout"] and ("Workflow" in result["stdout"] or "Services" in result["stdout"]):
                print(f"  ✅ Provenance data retrieved")
                self.test_results.append({"test": "CLI Document Provenance", "status": "success"})
            else:
                print(f"  ⚠️  Provenance data incomplete")
                self.test_results.append({"test": "CLI Document Provenance", "status": "partial"})
        else:
            print(f"  ❌ CLI command failed: {result['stderr']}")
            self.test_results.append({"test": "CLI Document Provenance", "status": "failed"})
        
        print()

    def _test_list_workflow_documents(self):
        """Test 6: List workflow documents via CLI."""
        print("📋 Test 6: List Workflow Documents via CLI")
        
        result = self.run_cli_command([
            "list-workflow-documents",
            "--workflow", "document_analysis",
            "--limit", "5"
        ])
        
        if result["success"]:
            print(f"  ✅ CLI command executed successfully")
            print(f"  ✅ Output preview:")
            output_lines = result["stdout"].strip().split('\n')
            for line in output_lines[:8]:  # Show first 8 lines
                print(f"    {line}")
            
            if "document_analysis" in result["stdout"] and ("Document" in result["stdout"] or "documents" in result["stdout"]):
                print(f"  ✅ Workflow documents listed")
                self.test_results.append({"test": "CLI List Workflow Documents", "status": "success"})
            else:
                print(f"  ⚠️  Workflow documents not found")
                self.test_results.append({"test": "CLI List Workflow Documents", "status": "partial"})
        else:
            print(f"  ❌ CLI command failed: {result['stderr']}")
            self.test_results.append({"test": "CLI List Workflow Documents", "status": "failed"})
        
        print()

    def _test_execution_trace(self):
        """Test 7: Test execution trace via CLI."""
        print("📋 Test 7: Execution Trace via CLI")
        
        # Use a mock execution ID for testing
        exec_id = "exec_20250917_test"
        
        result = self.run_cli_command([
            "get-execution-trace",
            "--execution-id", exec_id
        ])
        
        if result["success"]:
            print(f"  ✅ CLI command executed successfully")
            print(f"  ✅ Testing with Execution ID: {exec_id}")
            print(f"  ✅ Output preview:")
            output_lines = result["stdout"].strip().split('\n')
            for line in output_lines[:8]:  # Show first 8 lines
                print(f"    {line}")
            
            if "Execution" in result["stdout"] and ("Trace" in result["stdout"] or "Details" in result["stdout"]):
                print(f"  ✅ Execution trace retrieved")
                self.test_results.append({"test": "CLI Execution Trace", "status": "success"})
            else:
                print(f"  ⚠️  Execution trace incomplete")
                self.test_results.append({"test": "CLI Execution Trace", "status": "partial"})
        else:
            print(f"  ❌ CLI command failed: {result['stderr']}")
            self.test_results.append({"test": "CLI Execution Trace", "status": "failed"})
        
        print()

    def _print_test_summary(self):
        """Print test summary."""
        print("=" * 60)
        print("🏆 CLI DOCUMENT PERSISTENCE INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t["status"] == "success"])
        partial_tests = len([t for t in self.test_results if t["status"] == "partial"])
        failed_tests = len([t for t in self.test_results if t["status"] == "failed"])
        
        print(f"\n📊 Overall Results:")
        print(f"  • Total Tests: {total_tests}")
        print(f"  • Successful: {successful_tests} ✅")
        print(f"  • Partial: {partial_tests} ⚠️")
        print(f"  • Failed: {failed_tests} ❌")
        
        success_rate = (successful_tests + (partial_tests * 0.5)) / total_tests * 100 if total_tests > 0 else 0
        print(f"  • Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}[result["status"]]
            print(f"  {status_icon} {result['test']}: {result['status']}")
        
        print(f"\n📁 Generated Documents ({len(self.generated_docs)}):")
        for i, doc in enumerate(self.generated_docs, 1):
            print(f"  {i}. Document ID: {doc['id']} (Type: {doc['type']})")
        
        print(f"\n🎯 CLI Features Tested:")
        print(f"  ✅ Format Discovery")
        print(f"  ✅ Workflow Template Listing")
        print(f"  ✅ End-to-End Query Execution")
        print(f"  ✅ Direct Workflow Execution")
        print(f"  ✅ Document Provenance Retrieval")
        print(f"  ✅ Workflow Document Discovery")
        print(f"  ✅ Execution Trace Analysis")
        
        if success_rate >= 80:
            print(f"\n🏆 CLI INTEGRATION FULLY WORKING: All document persistence features accessible via CLI!")
        elif success_rate >= 60:
            print(f"\n⚠️  CLI INTEGRATION MOSTLY WORKING: Minor issues to resolve")
        else:
            print(f"\n❌ CLI INTEGRATION NEEDS WORK: Significant issues detected")
        
        print(f"\n⏰ Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 80


def main():
    """Main test runner."""
    tester = CLIDocumentPersistenceTest()
    success = tester.test_cli_document_persistence()
    
    if success:
        print("\n🎉 CLI DOCUMENT PERSISTENCE INTEGRATION TEST COMPLETE!")
    else:
        print("\n💥 CLI INTEGRATION NEEDS ATTENTION!")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
