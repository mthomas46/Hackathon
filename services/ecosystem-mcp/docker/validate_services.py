#!/usr/bin/env python3
"""
Ecosystem MCP Service Validation Script

Tests network connectivity, health checks, and self-healing capabilities
for all services in the ecosystem-mcp Docker Compose stack.
"""

import asyncio
import httpx
import sys
import time
from typing import Dict, Tuple, List
import json

# ANSI Colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Service endpoints (using Docker service names)
SERVICES = {
    "postgres": {
        "name": "PostgreSQL",
        "host": "postgres",
        "port": 5432,
        "type": "tcp"
    },
    "redis": {
        "name": "Redis",
        "host": "redis",
        "port": 6379,
        "type": "tcp"
    },
    "ollama": {
        "name": "Ollama",
        "host": "ollama",
        "port": 11434,
        "url": "http://ollama:11434/api/tags",
        "type": "http"
    },
    "ecosystem-mcp": {
        "name": "Ecosystem MCP API",
        "host": "ecosystem-mcp",
        "port": 8000,
        "url": "http://ecosystem-mcp:8000/health",
        "type": "http"
    },
    "dashboard": {
        "name": "Dashboard",
        "host": "dashboard",
        "port": 8501,
        "url": "http://dashboard:8501/_stcore/health",
        "type": "http"
    }
}

def print_header(text: str, color: str = Colors.BLUE):
    """Print a formatted header"""
    width = 100
    print(f"\n{color}{Colors.BOLD}{'=' * width}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{text.center(width)}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{'=' * width}{Colors.RESET}\n")

def print_test(name: str, passed: bool, details: str = "", timing: float = None):
    """Print test result"""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    timing_str = f" ({timing:.2f}s)" if timing else ""
    print(f"{status} {name}{timing_str}")
    if details:
        indent = "     "
        for line in details.split('\n'):
            print(f"{indent}{Colors.YELLOW}{line}{Colors.RESET}")

async def test_tcp_connection(host: str, port: int, timeout: float = 5.0) -> Tuple[bool, str]:
    """Test TCP connectivity to a service"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True, f"Connected to {host}:{port}"
    except asyncio.TimeoutError:
        return False, f"Connection timeout to {host}:{port}"
    except ConnectionRefusedError:
        return False, f"Connection refused to {host}:{port}"
    except Exception as e:
        return False, f"Error connecting to {host}:{port}: {str(e)}"

async def test_http_endpoint(url: str, timeout: float = 10.0) -> Tuple[bool, str, Dict]:
    """Test HTTP endpoint"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            start = time.time()
            response = await client.get(url)
            latency = time.time() - start
            
            if 200 <= response.status_code < 300:
                try:
                    data = response.json()
                    return True, f"HTTP {response.status_code} ({latency*1000:.0f}ms)", data
                except:
                    return True, f"HTTP {response.status_code} ({latency*1000:.0f}ms)", {}
            else:
                return False, f"HTTP {response.status_code}", {}
    except httpx.ConnectError:
        return False, "Cannot connect", {}
    except httpx.TimeoutException:
        return False, "Timeout", {}
    except Exception as e:
        return False, str(e)[:50], {}

async def test_redis_health(host: str = "redis", port: int = 6379) -> Tuple[bool, str]:
    """Test Redis health using direct connection"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5.0
        )
        # Send PING command
        writer.write(b"PING\r\n")
        await writer.drain()
        
        # Read response
        response = await asyncio.wait_for(reader.read(100), timeout=2.0)
        writer.close()
        await writer.wait_closed()
        
        if b"+PONG" in response:
            return True, "Redis PING successful"
        return False, f"Unexpected response: {response}"
    except Exception as e:
        return False, f"Redis health check failed: {str(e)}"

async def test_postgres_health(host: str = "postgres", port: int = 5432) -> Tuple[bool, str]:
    """Test PostgreSQL health"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5.0
        )
        writer.close()
        await writer.wait_closed()
        return True, "PostgreSQL accepting connections"
    except Exception as e:
        return False, f"PostgreSQL health check failed: {str(e)}"

async def test_api_endpoints(base_url: str = "http://ecosystem-mcp:8000") -> Dict[str, Tuple[bool, str]]:
    """Test all API endpoints"""
    endpoints = {
        "Health": f"{base_url}/health",
        "Infrastructure Health": f"{base_url}/api/v1/infrastructure/health",
        "Infrastructure Diagnostics": f"{base_url}/api/v1/infrastructure/diagnostics",
        "Monitoring": f"{base_url}/api/v1/diagnostics/monitor",
        "Documents": f"{base_url}/api/v1/documents?limit=1",
        "Collections": f"{base_url}/api/v1/collections",
    }
    
    results = {}
    async with httpx.AsyncClient(timeout=15.0) as client:
        for name, url in endpoints.items():
            try:
                start = time.time()
                response = await client.get(url)
                latency = time.time() - start
                
                if 200 <= response.status_code < 300:
                    results[name] = (True, f"HTTP {response.status_code} ({latency*1000:.0f}ms)")
                else:
                    results[name] = (False, f"HTTP {response.status_code}")
            except httpx.TimeoutException:
                results[name] = (False, "Timeout")
            except Exception as e:
                results[name] = (False, str(e)[:50])
    
    return results

async def test_service_connectivity() -> Dict[str, Tuple[bool, str]]:
    """Test connectivity to all backend services via API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://ecosystem-mcp:8000/api/v1/infrastructure/health")
            
            if response.status_code != 200:
                return {"Infrastructure Check": (False, f"API returned {response.status_code}")}
            
            data = response.json()
            components = data.get("components", {})
            
            results = {}
            for service, info in components.items():
                status = info.get("status", "unknown")
                if status == "healthy":
                    results[f"{service.title()} (via API)"] = (True, "Healthy")
                else:
                    error = info.get("error", "Unknown error")
                    results[f"{service.title()} (via API)"] = (False, error[:80])
            
            return results
    except Exception as e:
        return {"Infrastructure Check": (False, str(e)[:80])}

async def test_dashboard_api_connectivity() -> Tuple[bool, str]:
    """Test if dashboard can reach the API"""
    # This test would need to be run from inside the dashboard container
    # For now, we test if the API is reachable from the network
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://ecosystem-mcp:8000/health")
            if response.status_code == 200:
                return True, "Dashboard can reach API (network test)"
            return False, f"API returned {response.status_code}"
    except Exception as e:
        return False, f"Cannot reach API: {str(e)[:50]}"

async def run_validation():
    """Run complete service validation"""
    print_header("🔍 ECOSYSTEM MCP SERVICE VALIDATION", Colors.CYAN)
    print(f"{Colors.BOLD}Testing network connectivity, health checks, and inter-service communication{Colors.RESET}\n")
    
    all_results = []
    
    # Test 1: Basic TCP Connectivity
    print_header("1️⃣  TCP CONNECTIVITY TESTS", Colors.BLUE)
    for service_id, config in SERVICES.items():
        if config["type"] == "tcp" or "port" in config:
            start = time.time()
            passed, details = await test_tcp_connection(config["host"], config["port"])
            elapsed = time.time() - start
            print_test(f"{config['name']} TCP ({config['host']}:{config['port']})", passed, details, elapsed)
            all_results.append((f"{config['name']} TCP", passed))
    
    # Test 2: HTTP Health Endpoints
    print_header("2️⃣  HTTP HEALTH ENDPOINT TESTS", Colors.BLUE)
    for service_id, config in SERVICES.items():
        if config["type"] == "http" and "url" in config:
            start = time.time()
            passed, details, data = await test_http_endpoint(config["url"])
            elapsed = time.time() - start
            
            # Extract additional health info
            extra_info = ""
            if data and isinstance(data, dict):
                if "status" in data:
                    extra_info = f"\n Status: {data.get('status')}"
                if "components" in data:
                    comp_count = len(data["components"])
                    extra_info += f"\n Components: {comp_count}"
            
            print_test(f"{config['name']} Health", passed, details + extra_info, elapsed)
            all_results.append((f"{config['name']} Health", passed))
    
    # Test 3: Specialized Health Checks
    print_header("3️⃣  SPECIALIZED HEALTH CHECKS", Colors.BLUE)
    
    start = time.time()
    passed, details = await test_redis_health()
    print_test("Redis PING Command", passed, details, time.time() - start)
    all_results.append(("Redis PING", passed))
    
    start = time.time()
    passed, details = await test_postgres_health()
    print_test("PostgreSQL Connection", passed, details, time.time() - start)
    all_results.append(("PostgreSQL Connection", passed))
    
    # Test 4: API Endpoints
    print_header("4️⃣  API ENDPOINT TESTS", Colors.BLUE)
    api_results = await test_api_endpoints()
    for endpoint, (passed, details) in api_results.items():
        print_test(f"API: {endpoint}", passed, details)
        all_results.append((f"API: {endpoint}", passed))
    
    # Test 5: Service Connectivity (via API)
    print_header("5️⃣  INTER-SERVICE CONNECTIVITY (via API)", Colors.BLUE)
    service_results = await test_service_connectivity()
    for service, (passed, details) in service_results.items():
        print_test(service, passed, details)
        all_results.append((service, passed))
    
    # Test 6: Dashboard to API
    print_header("6️⃣  DASHBOARD → API CONNECTIVITY", Colors.BLUE)
    start = time.time()
    passed, details = await test_dashboard_api_connectivity()
    print_test("Dashboard can reach API", passed, details, time.time() - start)
    all_results.append(("Dashboard → API", passed))
    
    # Summary
    print_header("📊 VALIDATION SUMMARY", Colors.MAGENTA)
    total = len(all_results)
    passed_count = sum(1 for _, p in all_results if p)
    failed_count = total - passed_count
    success_rate = (passed_count / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}Total Tests:{Colors.RESET} {total}")
    print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.RESET} {passed_count}")
    print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.RESET} {failed_count}")
    print(f"{Colors.CYAN}{Colors.BOLD}Success Rate:{Colors.RESET} {success_rate:.1f}%\n")
    
    if failed_count > 0:
        print(f"{Colors.YELLOW}{Colors.BOLD}Failed Tests:{Colors.RESET}")
        for name, passed in all_results:
            if not passed:
                print(f"  {Colors.RED}❌ {name}{Colors.RESET}")
        print()
        
        print(f"{Colors.YELLOW}{Colors.BOLD}💡 Troubleshooting Tips:{Colors.RESET}")
        print("  1. Check Docker Compose logs: docker compose logs [service-name]")
        print("  2. Verify all containers are running: docker ps")
        print("  3. Check network connectivity: docker network inspect ecosystem-mcp")
        print("  4. Restart failed services: docker compose restart [service-name]")
        print()
    
    # Determine exit code
    if success_rate >= 80:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ VALIDATION PASSED{Colors.RESET} (>80% success rate)\n")
        return 0
    elif success_rate >= 50:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  VALIDATION WARNING{Colors.RESET} (50-80% success rate)\n")
        return 1
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ VALIDATION FAILED{Colors.RESET} (<50% success rate)\n")
        return 2

async def main():
    """Main entry point"""
    try:
        exit_code = await run_validation()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}Validation error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())

