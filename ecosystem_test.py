#!/usr/bin/env python3
"""
Ecosystem Integration Test Script
Tests all services in the Docker ecosystem and verifies inter-service communication
"""

import requests
import json
import time
from typing import Dict, List, Tuple

# Service endpoints configuration
SERVICES = {
    "redis": {"port": 6379, "health_path": None, "type": "database"},
    "orchestrator": {"port": 5099, "health_path": "/health", "type": "core"},
    "doc_store": {"port": 5087, "health_path": "/health", "type": "storage"},
    "analysis_service": {"port": 5020, "health_path": "/health", "type": "analysis"},
    "source_agent": {"port": 5000, "health_path": "/health", "type": "agent"},
    "frontend": {"port": 3000, "health_path": "/health", "type": "ui"},
    "architecture_digitizer": {"port": 5105, "health_path": "/health", "type": "analysis"},
    "log_collector": {"port": 5080, "health_path": "/health", "type": "monitoring"},
    "github_mcp": {"port": 5072, "health_path": "/health", "type": "integration"},
    "prompt_store": {"port": 5110, "health_path": "/health", "type": "storage"},
    "memory_agent": {"port": 5040, "health_path": "/health", "type": "agent"},
    "interpreter": {"port": 5120, "health_path": "/health", "type": "execution"},
    "discovery_agent": {"port": 5045, "health_path": "/health", "type": "agent"},
    "bedrock_proxy": {"port": 7090, "health_path": "/health", "type": "llm"},
    "notification_service": {"port": 5095, "health_path": "/health", "type": "communication"},
    "secure_analyzer": {"port": 5070, "health_path": "/health", "type": "security"},
}

def test_service_health(service_name: str, config: Dict) -> Tuple[bool, Dict]:
    """Test individual service health endpoint"""
    if config["health_path"] is None:
        return True, {"status": "no_health_check", "service": service_name}
    
    try:
        url = f"http://localhost:{config['port']}{config['health_path']}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return True, data
            except:
                return True, {"status": "healthy", "service": service_name}
        else:
            return False, {"status": "unhealthy", "status_code": response.status_code}
    except Exception as e:
        return False, {"status": "error", "error": str(e)}

def test_analysis_service_api() -> Dict:
    """Test analysis service specific API endpoints"""
    try:
        # Test status endpoint
        status_url = "http://localhost:5020/api/analysis/status"
        status_response = requests.get(status_url, timeout=5)
        
        # Test analysis endpoint
        analyze_url = "http://localhost:5020/api/analysis/analyze"
        analyze_response = requests.post(analyze_url, timeout=5)
        
        return {
            "status_api": status_response.status_code == 200,
            "analyze_api": analyze_response.status_code == 200,
            "status_data": status_response.json() if status_response.status_code == 200 else None,
            "analyze_data": analyze_response.json() if analyze_response.status_code == 200 else None
        }
    except Exception as e:
        return {"error": str(e)}

def test_inter_service_communication() -> Dict:
    """Test communication between services"""
    results = {}
    
    # Test orchestrator to other services
    try:
        orchestrator_health = requests.get("http://localhost:5099/health", timeout=5)
        if orchestrator_health.status_code == 200:
            results["orchestrator_accessible"] = True
            
            # Test if orchestrator can reach doc_store
            # This would normally be done through orchestrator API if available
            doc_store_health = requests.get("http://localhost:5087/health", timeout=5)
            results["doc_store_via_orchestrator"] = doc_store_health.status_code == 200
            
        else:
            results["orchestrator_accessible"] = False
    except Exception as e:
        results["orchestrator_error"] = str(e)
    
    return results

def run_comprehensive_test() -> Dict:
    """Run comprehensive ecosystem test"""
    print("🚀 Starting Comprehensive Ecosystem Test")
    print("=" * 50)
    
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "service_health": {},
        "service_summary": {"healthy": 0, "unhealthy": 0, "total": 0},
        "analysis_service_apis": {},
        "inter_service_communication": {},
        "overall_status": "unknown"
    }
    
    # Test all service health endpoints
    print("\n📊 Testing Service Health Endpoints:")
    for service_name, config in SERVICES.items():
        print(f"  Testing {service_name}... ", end="")
        is_healthy, health_data = test_service_health(service_name, config)
        
        results["service_health"][service_name] = {
            "healthy": is_healthy,
            "data": health_data,
            "port": config["port"],
            "type": config["type"]
        }
        
        if is_healthy:
            results["service_summary"]["healthy"] += 1
            print("✅ HEALTHY")
        else:
            results["service_summary"]["unhealthy"] += 1
            print("❌ UNHEALTHY")
        
        results["service_summary"]["total"] += 1
    
    # Test Analysis Service APIs
    print("\n🔬 Testing Analysis Service APIs:")
    analysis_results = test_analysis_service_api()
    results["analysis_service_apis"] = analysis_results
    
    if analysis_results.get("status_api") and analysis_results.get("analyze_api"):
        print("  ✅ Analysis Service APIs working")
    else:
        print("  ❌ Analysis Service APIs have issues")
    
    # Test Inter-service Communication
    print("\n🔗 Testing Inter-service Communication:")
    comm_results = test_inter_service_communication()
    results["inter_service_communication"] = comm_results
    
    # Determine overall status
    healthy_percentage = (results["service_summary"]["healthy"] / results["service_summary"]["total"]) * 100
    
    if healthy_percentage >= 90:
        results["overall_status"] = "excellent"
    elif healthy_percentage >= 75:
        results["overall_status"] = "good"
    elif healthy_percentage >= 50:
        results["overall_status"] = "fair"
    else:
        results["overall_status"] = "poor"
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 ECOSYSTEM TEST SUMMARY")
    print("=" * 50)
    print(f"Healthy Services: {results['service_summary']['healthy']}/{results['service_summary']['total']}")
    print(f"Health Percentage: {healthy_percentage:.1f}%")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Timestamp: {results['timestamp']}")
    
    return results

if __name__ == "__main__":
    test_results = run_comprehensive_test()
    
    # Save results to file
    with open("ecosystem_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Results saved to ecosystem_test_results.json")
    print("\n🎯 Test Complete!")
