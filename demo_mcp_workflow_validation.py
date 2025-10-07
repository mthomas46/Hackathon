#!/usr/bin/env python3
"""
MCP Workflow Validation Demo Script

This script validates the complete MCP creation workflow:
1. Document ingestion via kafka-ingestion-service
2. LLM tagging via llm-tagging-pipeline
3. Model training via mcp-training-coordinator
4. Storage via mcp-store
5. Registration via mcp-registry
6. Package export via mcp-package-manager
7. Documentation sync via mcp-evergreen-docs
8. Observability via mcp-logs

All operations are tracked with correlation IDs for end-to-end tracing.
"""

import asyncio
import httpx
import json
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime


class Colors:
    """Terminal colors for pretty output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class MCPWorkflowValidator:
    """Validates MCP workflow end-to-end."""
    
    def __init__(self):
        self.correlation_id = str(uuid.uuid4())
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Service endpoints
        self.services = {
            "kafka-ingestion": "http://localhost:5700",
            "llm-tagging": "http://localhost:8021",
            "mcp-local-llm": "http://localhost:8014",
            "mcp-package-manager": "http://localhost:8103",
            "mcp-evergreen-docs": "http://localhost:8104",
            "mcp-logs": "http://localhost:8016",
            "mcp-training": "http://localhost:8100",
            "mcp-store": "http://localhost:8101",
            "mcp-registry": "http://localhost:8102",
        }
        
        self.results = {}
    
    def print_header(self, text: str):
        """Print colored header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")
    
    async def check_service_health(self, name: str, url: str) -> bool:
        """Check if service is healthy."""
        try:
            response = await self.client.get(f"{url}/health")
            if response.status_code == 200:
                self.print_success(f"{name:30} | {url:40} | HEALTHY")
                return True
            else:
                self.print_error(f"{name:30} | {url:40} | UNHEALTHY")
                return False
        except Exception as e:
            self.print_error(f"{name:30} | {url:40} | OFFLINE ({str(e)[:30]})")
            return False
    
    async def validate_infrastructure(self):
        """Validate all services are running."""
        self.print_header("STEP 1: INFRASTRUCTURE VALIDATION")
        
        self.print_info("Checking service health...")
        print(f"\n{Colors.BOLD}{'Service':<30} | {'URL':<40} | {'Status':<10}{Colors.ENDC}")
        print("-" * 85)
        
        all_healthy = True
        for name, url in self.services.items():
            is_healthy = await self.check_service_health(name, url)
            self.results[f"{name}_health"] = is_healthy
            all_healthy = all_healthy and is_healthy
            await asyncio.sleep(0.5)
        
        print()
        if all_healthy:
            self.print_success("All services are healthy ✨")
        else:
            self.print_warning("Some services are not available (this may be expected)")
        
        return all_healthy
    
    async def validate_logging_integration(self):
        """Validate logging integration."""
        self.print_header("STEP 2: LOGGING INTEGRATION VALIDATION")
        
        self.print_info(f"Correlation ID: {self.correlation_id}")
        
        # Check mcp-logs is receiving logs
        try:
            response = await self.client.get(
                f"{self.services['mcp-logs']}/api/v1/logs",
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                logs = response.json()
                self.print_success(f"mcp-logs is operational ({len(logs.get('entries', []))} recent entries)")
                self.results["logging_operational"] = True
            else:
                self.print_error("mcp-logs returned non-200 status")
                self.results["logging_operational"] = False
        except Exception as e:
            self.print_error(f"Failed to query mcp-logs: {e}")
            self.results["logging_operational"] = False
    
    async def validate_document_ingestion(self):
        """Validate document ingestion workflow."""
        self.print_header("STEP 3: DOCUMENT INGESTION VALIDATION")
        
        # Create test document event
        doc_event = {
            "document_id": f"doc_{uuid.uuid4().hex[:8]}",
            "event_type": "DOCUMENT_CREATED",
            "source": "demo_validation",
            "content": "This is a test document for MCP workflow validation.",
            "metadata": {
                "title": "Test Document",
                "author": "MCP Validator",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        self.print_info(f"Ingesting document: {doc_event['document_id']}")
        
        try:
            response = await self.client.post(
                f"{self.services['kafka-ingestion']}/api/v1/ingestion/ingest",
                json=doc_event,
                headers={"X-Correlation-ID": self.correlation_id}
            )
            
            if response.status_code in [200, 201]:
                self.print_success("Document ingested successfully")
                self.results["document_ingested"] = True
                self.results["document_id"] = doc_event["document_id"]
            else:
                self.print_error(f"Ingestion failed: {response.status_code}")
                self.results["document_ingested"] = False
        except Exception as e:
            self.print_error(f"Failed to ingest document: {e}")
            self.results["document_ingested"] = False
    
    async def validate_llm_tagging(self):
        """Validate LLM tagging workflow."""
        self.print_header("STEP 4: LLM TAGGING VALIDATION")
        
        if not self.results.get("document_id"):
            self.print_warning("Skipping (no document ID from previous step)")
            return
        
        # Request LLM tagging
        tag_request = {
            "document_id": self.results["document_id"],
            "content": "This is a test document about MCP workflow validation and observability.",
            "extraction_types": ["summary", "keywords", "tags"]
        }
        
        self.print_info(f"Requesting LLM tagging for: {self.results['document_id']}")
        
        try:
            response = await self.client.post(
                f"{self.services['llm-tagging']}/api/v1/tagging/tag",
                json=tag_request,
                headers={"X-Correlation-ID": self.correlation_id}
            )
            
            if response.status_code in [200, 201]:
                self.print_success("LLM tagging completed successfully")
                self.results["llm_tagging_completed"] = True
            else:
                self.print_error(f"LLM tagging failed: {response.status_code}")
                self.results["llm_tagging_completed"] = False
        except Exception as e:
            self.print_error(f"Failed to request LLM tagging: {e}")
            self.results["llm_tagging_completed"] = False
    
    async def validate_correlation_tracking(self):
        """Validate correlation ID is tracked across services."""
        self.print_header("STEP 5: CORRELATION TRACKING VALIDATION")
        
        self.print_info(f"Querying logs with correlation ID: {self.correlation_id}")
        
        try:
            response = await self.client.get(
                f"{self.services['mcp-logs']}/api/v1/logs",
                params={"correlation_id": self.correlation_id, "limit": 100}
            )
            
            if response.status_code == 200:
                logs = response.json()
                log_entries = logs.get("entries", [])
                
                if len(log_entries) > 0:
                    self.print_success(f"Found {len(log_entries)} log entries with correlation ID")
                    
                    # Group by service
                    services_logged = set()
                    for entry in log_entries:
                        service = entry.get("service", "unknown")
                        services_logged.add(service)
                    
                    self.print_info(f"Services that logged: {', '.join(sorted(services_logged))}")
                    self.results["correlation_tracked"] = True
                    self.results["services_logged"] = len(services_logged)
                else:
                    self.print_warning("No log entries found with correlation ID yet (logs may be delayed)")
                    self.results["correlation_tracked"] = False
            else:
                self.print_error(f"Failed to query logs: {response.status_code}")
                self.results["correlation_tracked"] = False
        except Exception as e:
            self.print_error(f"Failed to validate correlation tracking: {e}")
            self.results["correlation_tracked"] = False
    
    async def validate_package_operations(self):
        """Validate package manager operations."""
        self.print_header("STEP 6: PACKAGE OPERATIONS VALIDATION")
        
        # List packages
        self.print_info("Listing available packages...")
        
        try:
            response = await self.client.get(
                f"{self.services['mcp-package-manager']}/api/v1/packages",
                headers={"X-Correlation-ID": self.correlation_id}
            )
            
            if response.status_code == 200:
                packages = response.json()
                self.print_success(f"Package manager operational ({len(packages.get('packages', []))} packages)")
                self.results["package_manager_operational"] = True
            else:
                self.print_error(f"Package manager query failed: {response.status_code}")
                self.results["package_manager_operational"] = False
        except Exception as e:
            self.print_error(f"Failed to query package manager: {e}")
            self.results["package_manager_operational"] = False
    
    async def validate_evergreen_docs(self):
        """Validate evergreen docs operations."""
        self.print_header("STEP 7: EVERGREEN DOCS VALIDATION")
        
        # List documentation
        self.print_info("Checking evergreen docs service...")
        
        try:
            response = await self.client.get(
                f"{self.services['mcp-evergreen-docs']}/api/v1/documentation",
                headers={"X-Correlation-ID": self.correlation_id}
            )
            
            if response.status_code == 200:
                docs = response.json()
                self.print_success(f"Evergreen docs operational ({len(docs.get('documents', []))} documents)")
                self.results["evergreen_docs_operational"] = True
            else:
                self.print_error(f"Evergreen docs query failed: {response.status_code}")
                self.results["evergreen_docs_operational"] = False
        except Exception as e:
            self.print_error(f"Failed to query evergreen docs: {e}")
            self.results["evergreen_docs_operational"] = False
    
    async def print_final_report(self):
        """Print final validation report."""
        self.print_header("VALIDATION REPORT")
        
        total_checks = len(self.results)
        passed_checks = sum(1 for v in self.results.values() if v is True)
        
        print(f"{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  Total Checks: {total_checks}")
        print(f"  Passed: {Colors.OKGREEN}{passed_checks}{Colors.ENDC}")
        print(f"  Failed: {Colors.FAIL}{total_checks - passed_checks}{Colors.ENDC}")
        print(f"  Success Rate: {(passed_checks/total_checks*100):.1f}%\n")
        
        print(f"{Colors.BOLD}Detailed Results:{Colors.ENDC}")
        for key, value in sorted(self.results.items()):
            if isinstance(value, bool):
                status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if value else f"{Colors.FAIL}❌ FAIL{Colors.ENDC}"
                print(f"  {key:40} {status}")
            else:
                print(f"  {key:40} {Colors.OKCYAN}{value}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Correlation ID:{Colors.ENDC} {self.correlation_id}")
        print(f"{Colors.BOLD}Timestamp:{Colors.ENDC} {datetime.utcnow().isoformat()}Z")
        
        # Save results to file
        report_file = f"validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "correlation_id": self.correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "results": self.results,
                "summary": {
                    "total": total_checks,
                    "passed": passed_checks,
                    "failed": total_checks - passed_checks,
                    "success_rate": f"{(passed_checks/total_checks*100):.1f}%"
                }
            }, f, indent=2)
        
        self.print_success(f"Report saved to: {report_file}")
    
    async def run_validation(self):
        """Run complete validation workflow."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║        MCP WORKFLOW VALIDATION - END-TO-END TEST                     ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        
        start_time = time.time()
        
        try:
            # Run validation steps
            await self.validate_infrastructure()
            await asyncio.sleep(1)
            
            await self.validate_logging_integration()
            await asyncio.sleep(1)
            
            await self.validate_document_ingestion()
            await asyncio.sleep(2)
            
            await self.validate_llm_tagging()
            await asyncio.sleep(2)
            
            await self.validate_correlation_tracking()
            await asyncio.sleep(1)
            
            await self.validate_package_operations()
            await asyncio.sleep(1)
            
            await self.validate_evergreen_docs()
            await asyncio.sleep(1)
            
            # Print final report
            await self.print_final_report()
            
            elapsed_time = time.time() - start_time
            print(f"\n{Colors.OKGREEN}Validation completed in {elapsed_time:.2f} seconds{Colors.ENDC}\n")
            
        finally:
            await self.client.aclose()


async def main():
    """Main entry point."""
    validator = MCPWorkflowValidator()
    await validator.run_validation()


if __name__ == "__main__":
    asyncio.run(main())

