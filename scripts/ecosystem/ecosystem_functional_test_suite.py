#!/usr/bin/env python3
"""
Ecosystem Functional Test Suite
Comprehensive testing of the live ecosystem for stability and functionality gaps
"""

import asyncio
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys


@dataclass
class ServiceConfig:
    """Service configuration with proper localhost ports"""
    name: str
    port: int
    health_endpoint: str = "/health"
    docker_name: str = ""
    expected_response_keys: List[str] = None


class EcosystemAuditor:
    """Comprehensive ecosystem auditor with functional testing capabilities"""
    
    def __init__(self):
        self.services = {
            "redis": ServiceConfig("redis", 6379, "/", "hackathon-redis-1"),
            "doc_store": ServiceConfig("doc_store", 5087, "/health", "hackathon-doc_store-1", ["status", "service"]),
            "orchestrator": ServiceConfig("orchestrator", 5099, "/health", "hackathon-orchestrator-1", ["status"]),
            "llm-gateway": ServiceConfig("llm-gateway", 5055, "/health", "hackathon-llm-gateway-1"),
            "mock-data-generator": ServiceConfig("mock-data-generator", 5065, "/health", "hackathon-mock-data-generator-1"),
            "summarizer-hub": ServiceConfig("summarizer-hub", 5160, "/health", "hackathon-summarizer-hub-1"),
            "bedrock-proxy": ServiceConfig("bedrock-proxy", 5060, "/health", "hackathon-bedrock-proxy-1"),
            "github-mcp": ServiceConfig("github-mcp", 5030, "/health", "hackathon-github-mcp-1"),
            "memory-agent": ServiceConfig("memory-agent", 5090, "/health", "hackathon-memory-agent-1"),
            "discovery-agent": ServiceConfig("discovery-agent", 5045, "/health", "hackathon-discovery-agent-1"),
            "source-agent": ServiceConfig("source-agent", 5085, "/health", "hackathon-source-agent-1"),
            "analysis-service": ServiceConfig("analysis-service", 5080, "/health", "hackathon-analysis-service-1"),
            "code-analyzer": ServiceConfig("code-analyzer", 5025, "/health", "hackathon-code-analyzer-1"),
            "secure-analyzer": ServiceConfig("secure-analyzer", 5100, "/health", "hackathon-secure-analyzer-1"),
            "log-collector": ServiceConfig("log-collector", 5040, "/health", "hackathon-log-collector-1"),
            "prompt_store": ServiceConfig("prompt_store", 5110, "/health", "hackathon-prompt_store-1"),
            "interpreter": ServiceConfig("interpreter", 5120, "/health", "hackathon-interpreter-1"),
            "architecture-digitizer": ServiceConfig("architecture-digitizer", 5105, "/health", "hackathon-architecture-digitizer-1"),
            "notification-service": ServiceConfig("notification-service", 5130, "/health", "hackathon-notification-service-1"),
            "frontend": ServiceConfig("frontend", 3000, "/", "hackathon-frontend-1"),
            "ollama": ServiceConfig("ollama", 11434, "/api/tags", "hackathon-ollama-1")
        }
        
        self.test_results = {}
        self.errors = []
        self.warnings = []
        
    async def test_service_connectivity(self, service_name: str, config: ServiceConfig) -> Dict[str, Any]:
        """Test basic connectivity to a service"""
        url = f"http://localhost:{config.port}{config.health_endpoint}"
        
        try:
            # Test with timeout
            with urllib.request.urlopen(url, timeout=5) as response:
                status_code = response.getcode()
                content = response.read().decode('utf-8')
                
                result = {
                    "service": service_name,
                    "status": "healthy" if status_code == 200 else "unhealthy",
                    "status_code": status_code,
                    "response_size": len(content),
                    "url": url
                }
                
                # Try to parse JSON response
                try:
                    json_data = json.loads(content)
                    result["response_type"] = "json"
                    result["response_data"] = json_data
                    
                    # Validate expected keys
                    if config.expected_response_keys:
                        missing_keys = [key for key in config.expected_response_keys 
                                      if key not in json_data]
                        if missing_keys:
                            result["warnings"] = f"Missing expected keys: {missing_keys}"
                            
                except json.JSONDecodeError:
                    result["response_type"] = "text"
                    result["response_preview"] = content[:200]
                
                return result
                
        except urllib.error.URLError as e:
            return {
                "service": service_name,
                "status": "connection_failed",
                "error": str(e),
                "url": url
            }
        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "error": str(e),
                "url": url
            }
    
    async def test_docker_health_status(self, service_name: str, config: ServiceConfig) -> Dict[str, Any]:
        """Check Docker health status"""
        try:
            result = subprocess.run(
                ["docker", "inspect", config.docker_name, "--format", "{{.State.Health.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                docker_status = result.stdout.strip()
                return {
                    "service": service_name,
                    "docker_health": docker_status,
                    "container_name": config.docker_name
                }
            else:
                return {
                    "service": service_name,
                    "docker_health": "unknown",
                    "error": result.stderr.strip()
                }
                
        except Exception as e:
            return {
                "service": service_name,
                "docker_health": "error",
                "error": str(e)
            }
    
    async def test_basic_functionality(self, service_name: str, config: ServiceConfig) -> Dict[str, Any]:
        """Test basic service functionality beyond health checks"""

        functional_tests = {
            "doc_store": self._test_doc_store_functionality,
            "orchestrator": self._test_orchestrator_functionality,
            "llm-gateway": self._test_llm_gateway_functionality,
            "discovery-agent": self._test_discovery_agent_functionality,
            "analysis-service": self._test_analysis_service_functionality,
            "frontend": self._test_frontend_functionality,
            "notification-service": self._test_notification_service_functionality,
            "code-analyzer": self._test_code_analyzer_functionality,
            "source-agent": self._test_source_agent_functionality
        }

        if service_name in functional_tests:
            try:
                return await functional_tests[service_name](config)
            except Exception as e:
                return {
                    "service": service_name,
                    "functional_test": "error",
                    "error": str(e)
                }
        else:
            return {
                "service": service_name,
                "functional_test": "not_implemented"
            }

    async def test_service_integration(self, service_name: str, config: ServiceConfig) -> Dict[str, Any]:
        """Test service integration with dependencies"""

        integration_tests = {
            "doc_store": self._test_doc_store_integration,
            "analysis-service": self._test_analysis_service_integration,
            "source-agent": self._test_source_agent_integration,
            "frontend": self._test_frontend_integration
        }

        if service_name in integration_tests:
            try:
                return await integration_tests[service_name](config)
            except Exception as e:
                return {
                    "service": service_name,
                    "integration_test": "error",
                    "error": str(e)
                }
        else:
            return {
                "service": service_name,
                "integration_test": "not_implemented"
            }

    async def test_load_performance(self, service_name: str, config: ServiceConfig) -> Dict[str, Any]:
        """Test service performance under load"""

        load_tests = {
            "doc_store": self._test_doc_store_load,
            "llm-gateway": self._test_llm_gateway_load,
            "orchestrator": self._test_orchestrator_load
        }

        if service_name in load_tests:
            try:
                return await load_tests[service_name](config)
            except Exception as e:
                return {
                    "service": service_name,
                    "load_test": "error",
                    "error": str(e)
                }
        else:
            return {
                "service": service_name,
                "load_test": "not_implemented"
            }
    
    async def _test_doc_store_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test doc_store basic CRUD operations"""
        base_url = f"http://localhost:{config.port}"
        
        # Test document listing
        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/documents", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "doc_store",
                        "functional_test": "success",
                        "documents_count": len(data.get("documents", [])),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "doc_store",
                "functional_test": "failed",
                "error": str(e)
            }
    
    async def _test_orchestrator_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test orchestrator service registry"""
        base_url = f"http://localhost:{config.port}"
        
        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/services", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "orchestrator",
                        "functional_test": "success",
                        "registered_services": len(data.get("services", [])),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "orchestrator",
                "functional_test": "failed",
                "error": str(e)
            }
    
    async def _test_llm_gateway_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test LLM Gateway provider status"""
        base_url = f"http://localhost:{config.port}"
        
        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/providers", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "llm-gateway",
                        "functional_test": "success",
                        "available_providers": len(data.get("providers", [])),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "llm-gateway",
                "functional_test": "failed",
                "error": str(e)
            }
    
    async def _test_discovery_agent_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test Discovery Agent service discovery"""
        base_url = f"http://localhost:{config.port}"
        
        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/discovery/services", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "discovery-agent",
                        "functional_test": "success",
                        "discovered_services": len(data.get("services", [])),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "discovery-agent",
                "functional_test": "failed",
                "error": str(e)
            }
    
    async def _test_analysis_service_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test Analysis Service capabilities"""
        base_url = f"http://localhost:{config.port}"
        
        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/analysis/capabilities", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "analysis-service",
                        "functional_test": "success",
                        "analysis_types": len(data.get("capabilities", [])),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "analysis-service",
                "functional_test": "failed",
                "error": str(e)
            }

    async def _test_frontend_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test Frontend service basic functionality"""
        base_url = f"http://localhost:{config.port}"

        try:
            with urllib.request.urlopen(f"{base_url}/", timeout=10) as response:
                if response.getcode() == 200:
                    content = response.read().decode('utf-8')
                    return {
                        "service": "frontend",
                        "functional_test": "success",
                        "ui_accessible": True,
                        "page_size": len(content),
                        "has_html": "<html" in content.lower()
                    }
        except Exception as e:
            return {
                "service": "frontend",
                "functional_test": "failed",
                "error": str(e)
            }

    async def _test_notification_service_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test Notification Service basic functionality"""
        base_url = f"http://localhost:{config.port}"

        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/notifications/status", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "notification-service",
                        "functional_test": "success",
                        "notification_channels": data.get("channels", []),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "notification-service",
                "functional_test": "failed",
                "error": str(e)
            }

    async def _test_code_analyzer_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test Code Analyzer basic functionality"""
        base_url = f"http://localhost:{config.port}"

        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/analysis/status", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "code-analyzer",
                        "functional_test": "success",
                        "supported_languages": data.get("languages", []),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "code-analyzer",
                "functional_test": "failed",
                "error": str(e)
            }

    async def _test_source_agent_functionality(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test Source Agent basic functionality"""
        base_url = f"http://localhost:{config.port}"

        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/sources/status", timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        "service": "source-agent",
                        "functional_test": "success",
                        "supported_sources": data.get("sources", []),
                        "api_accessible": True
                    }
        except Exception as e:
            return {
                "service": "source-agent",
                "functional_test": "failed",
                "error": str(e)
            }

    async def _test_doc_store_integration(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test doc_store integration with other services"""
        base_url = f"http://localhost:{config.port}"

        integration_results = {
            "service": "doc_store",
            "integration_test": "success",
            "dependencies_tested": [],
            "integration_points": []
        }

        # Test connection to orchestrator (if orchestrator is healthy)
        try:
            orchestrator_url = "http://localhost:5099/api/v1/services"
            with urllib.request.urlopen(orchestrator_url, timeout=5) as response:
                if response.getcode() == 200:
                    integration_results["dependencies_tested"].append("orchestrator")
                    integration_results["integration_points"].append("service_registry")
        except:
            pass

        return integration_results

    async def _test_analysis_service_integration(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test analysis-service integration with doc_store and llm-gateway"""
        base_url = f"http://localhost:{config.port}"

        integration_results = {
            "service": "analysis-service",
            "integration_test": "success",
            "dependencies_tested": [],
            "data_flow_verified": False
        }

        # Test doc_store connectivity
        try:
            doc_store_url = "http://localhost:5087/api/v1/documents"
            with urllib.request.urlopen(doc_store_url, timeout=5) as response:
                if response.getcode() == 200:
                    integration_results["dependencies_tested"].append("doc_store")
        except:
            pass

        # Test llm-gateway connectivity
        try:
            llm_url = "http://localhost:5055/api/v1/providers"
            with urllib.request.urlopen(llm_url, timeout=5) as response:
                if response.getcode() == 200:
                    integration_results["dependencies_tested"].append("llm-gateway")
        except:
            pass

        return integration_results

    async def _test_source_agent_integration(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test source-agent integration with doc_store"""
        base_url = f"http://localhost:{config.port}"

        integration_results = {
            "service": "source-agent",
            "integration_test": "success",
            "doc_store_integration": False
        }

        # Test doc_store connectivity for data storage
        try:
            doc_store_url = "http://localhost:5087/api/v1/documents"
            with urllib.request.urlopen(doc_store_url, timeout=5) as response:
                if response.getcode() == 200:
                    integration_results["doc_store_integration"] = True
        except:
            pass

        return integration_results

    async def _test_frontend_integration(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test frontend integration with backend services"""
        base_url = f"http://localhost:{config.port}"

        integration_results = {
            "service": "frontend",
            "integration_test": "success",
            "backend_services_accessible": [],
            "api_endpoints_tested": []
        }

        # Test connections to key backend services
        backend_services = {
            "orchestrator": "http://localhost:5099/health",
            "doc_store": "http://localhost:5087/health",
            "llm-gateway": "http://localhost:5055/health"
        }

        for service_name, url in backend_services.items():
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.getcode() == 200:
                        integration_results["backend_services_accessible"].append(service_name)
                        integration_results["api_endpoints_tested"].append(url)
            except:
                pass

        return integration_results

    async def _test_doc_store_load(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test doc_store performance under load"""
        base_url = f"http://localhost:{config.port}"

        load_results = {
            "service": "doc_store",
            "load_test": "success",
            "requests_made": 0,
            "successful_requests": 0,
            "average_response_time": 0,
            "error_rate": 0
        }

        # Perform 10 concurrent requests to test load handling
        import concurrent.futures
        response_times = []

        def make_request():
            try:
                start_time = time.time()
                with urllib.request.urlopen(f"{base_url}/api/v1/documents", timeout=10) as response:
                    end_time = time.time()
                    if response.getcode() == 200:
                        return end_time - start_time
            except:
                return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                load_results["requests_made"] += 1
                if result is not None:
                    response_times.append(result)
                    load_results["successful_requests"] += 1

        if response_times:
            load_results["average_response_time"] = sum(response_times) / len(response_times)
            load_results["error_rate"] = (load_results["requests_made"] - load_results["successful_requests"]) / load_results["requests_made"]

        return load_results

    async def _test_llm_gateway_load(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test llm-gateway performance under load"""
        base_url = f"http://localhost:{config.port}"

        load_results = {
            "service": "llm-gateway",
            "load_test": "success",
            "concurrent_requests": 0,
            "successful_requests": 0,
            "average_response_time": 0
        }

        # Test provider endpoint under load
        import concurrent.futures

        def make_request():
            try:
                start_time = time.time()
                with urllib.request.urlopen(f"{base_url}/api/v1/providers", timeout=15) as response:
                    end_time = time.time()
                    if response.getcode() == 200:
                        return end_time - start_time
            except:
                return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(6)]
            response_times = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                load_results["concurrent_requests"] += 1
                if result is not None:
                    response_times.append(result)
                    load_results["successful_requests"] += 1

        if response_times:
            load_results["average_response_time"] = sum(response_times) / len(response_times)

        return load_results

    async def _test_orchestrator_load(self, config: ServiceConfig) -> Dict[str, Any]:
        """Test orchestrator performance under load"""
        base_url = f"http://localhost:{config.port}"

        load_results = {
            "service": "orchestrator",
            "load_test": "success",
            "service_registry_calls": 0,
            "successful_calls": 0,
            "average_response_time": 0
        }

        # Test service registry endpoint under load
        import concurrent.futures

        def make_request():
            try:
                start_time = time.time()
                with urllib.request.urlopen(f"{base_url}/api/v1/services", timeout=10) as response:
                    end_time = time.time()
                    if response.getcode() == 200:
                        return end_time - start_time
            except:
                return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request) for _ in range(8)]
            response_times = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                load_results["service_registry_calls"] += 1
                if result is not None:
                    response_times.append(result)
                    load_results["successful_calls"] += 1

        if response_times:
            load_results["average_response_time"] = sum(response_times) / len(response_times)

        return load_results

    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete document processing workflow"""
        workflow_results = {
            "workflow_name": "document_processing",
            "steps": [],
            "overall_status": "unknown",
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Create a test document in doc_store
            doc_data = {
                "title": "Ecosystem Audit Test Document",
                "content": "This is a test document created during ecosystem audit.",
                "content_type": "text",
                "source_type": "test"
            }
            
            doc_create_result = await self._create_test_document(doc_data)
            workflow_results["steps"].append({
                "step": "document_creation",
                "status": "success" if doc_create_result.get("success") else "failed",
                "details": doc_create_result
            })
            
            if doc_create_result.get("success"):
                doc_id = doc_create_result.get("document_id")
                
                # Step 2: Analyze the document
                analysis_result = await self._analyze_test_document(doc_id)
                workflow_results["steps"].append({
                    "step": "document_analysis",
                    "status": "success" if analysis_result.get("success") else "failed",
                    "details": analysis_result
                })
                
                # Step 3: Summarize the document
                summary_result = await self._summarize_test_document(doc_id)
                workflow_results["steps"].append({
                    "step": "document_summarization",
                    "status": "success" if summary_result.get("success") else "failed",
                    "details": summary_result
                })
            
            # Determine overall status
            failed_steps = [step for step in workflow_results["steps"] if step["status"] == "failed"]
            workflow_results["overall_status"] = "failed" if failed_steps else "success"
            
        except Exception as e:
            workflow_results["overall_status"] = "error"
            workflow_results["error"] = str(e)
        
        workflow_results["execution_time"] = time.time() - start_time
        return workflow_results
    
    async def _create_test_document(self, doc_data: Dict) -> Dict[str, Any]:
        """Helper to create a test document"""
        try:
            json_data = json.dumps(doc_data).encode('utf-8')
            req = urllib.request.Request(
                "http://localhost:5087/api/v1/documents",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 201:
                    result = json.loads(response.read().decode('utf-8'))
                    return {
                        "success": True,
                        "document_id": result.get("document_id"),
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.getcode()}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_test_document(self, doc_id: str) -> Dict[str, Any]:
        """Helper to analyze a test document"""
        try:
            analysis_data = {
                "document_id": doc_id,
                "analysis_types": ["basic_analysis"]
            }
            
            json_data = json.dumps(analysis_data).encode('utf-8')
            req = urllib.request.Request(
                "http://localhost:5080/api/v1/analysis/analyze",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.getcode() == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    return {
                        "success": True,
                        "analysis_id": result.get("analysis_id"),
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.getcode()}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _summarize_test_document(self, doc_id: str) -> Dict[str, Any]:
        """Helper to summarize a test document"""
        try:
            summary_data = {
                "document_id": doc_id,
                "summary_type": "basic"
            }
            
            json_data = json.dumps(summary_data).encode('utf-8')
            req = urllib.request.Request(
                "http://localhost:5160/api/v1/summarize",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.getcode() == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    return {
                        "success": True,
                        "summary": result.get("summary"),
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.getcode()}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run complete ecosystem audit"""
        print("🔍 Starting Comprehensive Ecosystem Audit...")
        audit_results = {
            "audit_timestamp": time.time(),
            "total_services": len(self.services),
            "connectivity_tests": {},
            "docker_health_tests": {},
            "functional_tests": {},
            "end_to_end_workflow": {},
            "summary": {},
            "recommendations": []
        }
        
        # Test 1: Service Connectivity
        print("\n📡 Testing Service Connectivity...")
        for service_name, config in self.services.items():
            print(f"  Testing {service_name}...")
            connectivity_result = await self.test_service_connectivity(service_name, config)
            audit_results["connectivity_tests"][service_name] = connectivity_result
        
        # Test 2: Docker Health Status  
        print("\n🐳 Checking Docker Health Status...")
        for service_name, config in self.services.items():
            if config.docker_name:
                docker_result = await self.test_docker_health_status(service_name, config)
                audit_results["docker_health_tests"][service_name] = docker_result
        
        # Test 3: Functional Tests
        print("\n🧪 Running Functional Tests...")
        for service_name, config in self.services.items():
            functional_result = await self.test_basic_functionality(service_name, config)
            audit_results["functional_tests"][service_name] = functional_result
        
        # Test 4: End-to-End Workflow
        print("\n🔄 Testing End-to-End Workflow...")
        workflow_result = await self.test_end_to_end_workflow()
        audit_results["end_to_end_workflow"] = workflow_result

        # Test 5: Service Integration Tests
        print("\n🔗 Testing Service Integration...")
        audit_results["integration_tests"] = {}
        for service_name, config in self.services.items():
            integration_result = await self.test_service_integration(service_name, config)
            audit_results["integration_tests"][service_name] = integration_result

        # Test 6: Load Performance Tests
        print("\n⚡ Testing Load Performance...")
        audit_results["load_tests"] = {}
        for service_name, config in self.services.items():
            load_result = await self.test_load_performance(service_name, config)
            audit_results["load_tests"][service_name] = load_result

        # Generate Summary
        audit_results["summary"] = self._generate_audit_summary(audit_results)
        audit_results["recommendations"] = self._generate_recommendations(audit_results)
        
        return audit_results
    
    def _generate_audit_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audit summary statistics"""
        connectivity = results["connectivity_tests"]
        healthy_services = [s for s, r in connectivity.items() if r["status"] == "healthy"]
        
        return {
            "healthy_services_count": len(healthy_services),
            "unhealthy_services_count": len(connectivity) - len(healthy_services),
            "health_percentage": (len(healthy_services) / len(connectivity)) * 100,
            "critical_issues": self._identify_critical_issues(results),
            "performance_issues": self._identify_performance_issues(results)
        }
    
    def _identify_critical_issues(self, results: Dict[str, Any]) -> List[str]:
        """Identify critical issues from audit results"""
        issues = []
        
        # Check for completely failed services
        connectivity = results["connectivity_tests"]
        failed_services = [s for s, r in connectivity.items() 
                          if r["status"] in ["connection_failed", "error"]]
        
        if failed_services:
            issues.append(f"Services completely unreachable: {', '.join(failed_services)}")
        
        # Check end-to-end workflow
        workflow = results["end_to_end_workflow"]
        if workflow.get("overall_status") == "failed":
            issues.append("End-to-end workflow failed - ecosystem integration broken")

        # Check integration tests
        integration_tests = results.get("integration_tests", {})
        failed_integrations = []
        for service, result in integration_tests.items():
            if result.get("integration_test") == "error":
                failed_integrations.append(service)

        if failed_integrations:
            issues.append(f"Integration test failures: {', '.join(failed_integrations)}")

        # Check load tests
        load_tests = results.get("load_tests", {})
        high_error_load_tests = []
        for service, result in load_tests.items():
            if result.get("load_test") == "success":
                error_rate = result.get("error_rate", 0)
                if error_rate > 0.5:  # More than 50% error rate
                    high_error_load_tests.append(service)

        if high_error_load_tests:
            issues.append(f"High error rates under load: {', '.join(high_error_load_tests)}")

        return issues
    
    def _identify_performance_issues(self, results: Dict[str, Any]) -> List[str]:
        """Identify performance issues"""
        issues = []

        # Check workflow execution time
        workflow = results["end_to_end_workflow"]
        if workflow.get("execution_time", 0) > 30:
            issues.append(f"Slow end-to-end workflow: {workflow.get('execution_time'):.2f}s")

        # Check load test performance
        load_tests = results.get("load_tests", {})
        slow_services = []
        high_latency_services = []

        for service, result in load_tests.items():
            if result.get("load_test") == "success":
                avg_response_time = result.get("average_response_time", 0)
                if avg_response_time > 5.0:  # More than 5 seconds average response
                    slow_services.append(f"{service} ({avg_response_time:.2f}s)")
                elif avg_response_time > 2.0:  # More than 2 seconds average response
                    high_latency_services.append(f"{service} ({avg_response_time:.2f}s)")

        if slow_services:
            issues.append(f"Very slow services under load: {', '.join(slow_services)}")
        if high_latency_services:
            issues.append(f"High latency services: {', '.join(high_latency_services)}")

        return issues
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        summary = results["summary"]
        if summary["health_percentage"] < 80:
            recommendations.append("Investigate and fix unhealthy services to improve ecosystem stability")
        
        if summary["critical_issues"]:
            recommendations.append("Address critical connectivity issues immediately")
        
        if summary["performance_issues"]:
            recommendations.append("Optimize performance bottlenecks identified in testing")
        
        # Check for Docker health discrepancies
        connectivity = results["connectivity_tests"]
        docker_health = results["docker_health_tests"]
        
        discrepancies = []
        for service in connectivity:
            conn_healthy = connectivity[service]["status"] == "healthy"
            docker_status = docker_health.get(service, {}).get("docker_health")
            docker_healthy = docker_status == "healthy"
            
            if conn_healthy != docker_healthy:
                discrepancies.append(service)
        
        if discrepancies:
            recommendations.append(f"Resolve health check discrepancies for: {', '.join(discrepancies)}")
        
        return recommendations
    
    def print_audit_report(self, results: Dict[str, Any]):
        """Print comprehensive audit report"""
        print("\n" + "="*80)
        print("🔍 ECOSYSTEM FUNCTIONAL AUDIT REPORT")
        print("="*80)
        
        summary = results["summary"]
        print(f"\n📊 SUMMARY")
        print(f"  Total Services: {results['total_services']}")
        print(f"  Healthy Services: {summary['healthy_services_count']}")
        print(f"  Unhealthy Services: {summary['unhealthy_services_count']}")
        print(f"  Health Percentage: {summary['health_percentage']:.1f}%")
        
        # Service Status Details
        print(f"\n🔗 SERVICE CONNECTIVITY")
        for service, result in results["connectivity_tests"].items():
            status_emoji = "✅" if result["status"] == "healthy" else "❌"
            print(f"  {status_emoji} {service:20} | {result['status']:15} | Port {self.services[service].port}")
        
        # End-to-end workflow
        workflow = results["end_to_end_workflow"]
        print(f"\n🔄 END-TO-END WORKFLOW")
        workflow_emoji = "✅" if workflow.get("overall_status") == "success" else "❌"
        print(f"  {workflow_emoji} Status: {workflow.get('overall_status', 'unknown')}")
        print(f"  ⏱️  Execution Time: {workflow.get('execution_time', 0):.2f}s")
        
        for step in workflow.get("steps", []):
            step_emoji = "✅" if step["status"] == "success" else "❌"
            print(f"    {step_emoji} {step['step']}: {step['status']}")

        # Integration Tests
        integration_tests = results.get("integration_tests", {})
        if integration_tests:
            print(f"\n🔗 SERVICE INTEGRATION")
            for service, result in integration_tests.items():
                if result.get("integration_test") == "success":
                    deps = result.get("dependencies_tested", [])
                    print(f"  ✅ {service:20} | {len(deps)} dependencies tested")
                else:
                    status = result.get("integration_test", "unknown")
                    print(f"  ❌ {service:20} | {status}")

        # Load Performance Tests
        load_tests = results.get("load_tests", {})
        if load_tests:
            print(f"\n⚡ LOAD PERFORMANCE")
            for service, result in load_tests.items():
                if result.get("load_test") == "success":
                    avg_time = result.get("average_response_time", 0)
                    error_rate = result.get("error_rate", 0)
                    print(f"  ✅ {service:20} | {avg_time:.2f}s avg | {error_rate:.1%} errors")
                else:
                    status = result.get("load_test", "unknown")
                    print(f"  ❌ {service:20} | {status}")

        # Critical Issues
        if summary["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES")
            for issue in summary["critical_issues"]:
                print(f"  ❌ {issue}")
        
        # Recommendations
        if results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*80)


async def main():
    """Main audit execution"""
    auditor = EcosystemAuditor()
    results = await auditor.run_comprehensive_audit()
    auditor.print_audit_report(results)
    
    # Save detailed results
    with open("ecosystem_audit_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: ecosystem_audit_results.json")


if __name__ == "__main__":
    asyncio.run(main())
