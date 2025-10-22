"""
Validation script to verify FastEmbed usage and performance.

This script:
1. Checks if FastEmbed service is accessible
2. Validates environment variables are set correctly
3. Tests query performance with FastEmbed vs Ollama
4. Verifies model consistency across pipeline
5. Generates performance report
"""

import asyncio
import httpx
import time
import json
from typing import Dict, List, Any
import statistics


# Configuration
BASE_URL = "http://localhost:8000"
FASTEMBED_URL = "http://localhost:8001"
TIMEOUT = 30.0


class FastEmbedValidator:
    """Validator for FastEmbed integration."""
    
    def __init__(self):
        self.results = {}
        self.performance_metrics = {
            "fastembed_queries": [],
            "ollama_queries": []
        }
    
    async def validate_fastembed_service(self) -> Dict[str, Any]:
        """Check if FastEmbed service is healthy and accessible."""
        print("\n🔍 Step 1: Validating FastEmbed Service")
        print("=" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{FASTEMBED_URL}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ FastEmbed service is HEALTHY")
                    print(f"   Model: {data.get('model')}")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Redis: {data.get('redis_connected')}")
                    
                    return {
                        "status": "healthy",
                        "accessible": True,
                        "model": data.get('model'),
                        **data
                    }
                else:
                    print(f"⚠️  FastEmbed service returned: {response.status_code}")
                    return {
                        "status": "unhealthy",
                        "accessible": True,
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            print(f"❌ FastEmbed service NOT accessible: {e}")
            return {
                "status": "unreachable",
                "accessible": False,
                "error": str(e)
            }
    
    async def validate_environment_vars(self) -> Dict[str, Any]:
        """Validate that correct environment variables are set."""
        print("\n🔍 Step 2: Validating Environment Variables")
        print("=" * 50)
        
        # We can't directly check env vars in the container, but we can
        # infer from behavior and logs
        print("ℹ️  Environment variables should be set:")
        print("   - EMBEDDING_BACKEND=service")
        print("   - EMBEDDING_SERVICE_URL=http://ecosystem-mcp-embedding:8000")
        print("\nℹ️  Check container logs for confirmation:")
        print("   docker logs ecosystem-mcp-service | grep EMBEDDING")
        
        return {
            "status": "manual_check_required",
            "expected_vars": {
                "EMBEDDING_BACKEND": "service",
                "EMBEDDING_SERVICE_URL": "http://ecosystem-mcp-embedding:8000"
            }
        }
    
    async def test_query_performance(self, query: str, num_runs: int = 5) -> Dict[str, Any]:
        """Test query performance and track which backend was used."""
        print(f"\n🧪 Testing query: '{query}'")
        
        times = []
        backend_used = None
        model_used = None
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for i in range(num_runs):
                try:
                    start = time.time()
                    response = await client.post(
                        f"{BASE_URL}/api/v1/search",
                        json={"query": query, "limit": 3}
                    )
                    duration = time.time() - start
                    
                    if response.status_code == 200:
                        times.append(duration)
                        print(f"   Run {i+1}: {duration:.3f}s")
                    else:
                        print(f"   Run {i+1}: FAILED ({response.status_code})")
                    
                    # Wait to avoid rate limiting
                    if i < num_runs - 1:
                        await asyncio.sleep(7)
                        
                except Exception as e:
                    print(f"   Run {i+1}: ERROR - {e}")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            # Estimate backend based on performance
            # FastEmbed: ~0.01-0.05s, Ollama: ~0.3-0.5s
            if avg_time < 0.1:
                backend_used = "fastembed (estimated)"
            elif avg_time > 0.2:
                backend_used = "ollama (estimated)"
            else:
                backend_used = "unknown"
            
            print(f"\n📊 Performance Summary:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Min: {min_time:.3f}s")
            print(f"   Max: {max_time:.3f}s")
            print(f"   Backend: {backend_used}")
            
            return {
                "query": query,
                "runs": num_runs,
                "times": times,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "backend_estimated": backend_used
            }
        else:
            return {
                "query": query,
                "runs": 0,
                "error": "All runs failed"
            }
    
    async def validate_model_consistency(self) -> Dict[str, Any]:
        """Validate that the same model is used for ingestion and queries."""
        print("\n🔍 Step 3: Validating Model Consistency")
        print("=" * 50)
        
        print("ℹ️  To verify model consistency:")
        print("   1. Check ingestion logs for embedding model")
        print("   2. Check query logs for embedding model")
        print("   3. Ensure both show same model (BAAI/bge-base-en-v1.5 or nomic-embed-text)")
        print("\nℹ️  Command to check:")
        print("   docker logs ecosystem-mcp-service | grep 'embedding generated'")
        
        return {
            "status": "manual_verification_required",
            "expected_model": "BAAI/bge-base-en-v1.5 (FastEmbed) or nomic-embed-text (Ollama)",
            "consistency_required": True
        }
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        print("\n" + "=" * 70)
        print("🔥 FASTEMBED USAGE VALIDATION")
        print("=" * 70)
        
        # Step 1: Check FastEmbed service
        fastembed_status = await self.validate_fastembed_service()
        self.results["fastembed_service"] = fastembed_status
        
        # Step 2: Check environment variables
        env_status = await self.validate_environment_vars()
        self.results["environment_vars"] = env_status
        
        # Step 3: Test performance
        print("\n🔍 Step 4: Testing Query Performance")
        print("=" * 50)
        
        test_queries = [
            "worker loop implementation",
            "embedding generation process",
            "document processing workflow"
        ]
        
        performance_results = []
        for query in test_queries:
            result = await self.test_query_performance(query, num_runs=3)
            performance_results.append(result)
            await asyncio.sleep(2)  # Brief pause between tests
        
        self.results["performance_tests"] = performance_results
        
        # Step 4: Model consistency
        consistency_status = await self.validate_model_consistency()
        self.results["model_consistency"] = consistency_status
        
        # Generate summary
        self.generate_summary()
        
        return self.results
    
    def generate_summary(self):
        """Generate validation summary."""
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)
        
        # FastEmbed Service Status
        fastembed = self.results.get("fastembed_service", {})
        print(f"\n✅ FastEmbed Service:")
        print(f"   Status: {fastembed.get('status')}")
        print(f"   Accessible: {fastembed.get('accessible')}")
        if fastembed.get('model'):
            print(f"   Model: {fastembed.get('model')}")
        
        # Performance Analysis
        perf_tests = self.results.get("performance_tests", [])
        if perf_tests:
            print(f"\n✅ Performance Tests:")
            all_times = []
            for test in perf_tests:
                if test.get('times'):
                    all_times.extend(test['times'])
                    print(f"   Query: {test['query'][:30]}...")
                    print(f"     Avg: {test['avg_time']:.3f}s")
                    print(f"     Backend: {test.get('backend_estimated', 'unknown')}")
            
            if all_times:
                overall_avg = statistics.mean(all_times)
                print(f"\n   Overall Average: {overall_avg:.3f}s")
                
                if overall_avg < 0.1:
                    print(f"   ✅ EXCELLENT - FastEmbed likely in use!")
                elif overall_avg < 0.3:
                    print(f"   🟡 GOOD - Mixed or cached")
                else:
                    print(f"   ⚠️  SLOW - Likely using Ollama fallback")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if fastembed.get('status') == 'healthy':
            print("   ✅ FastEmbed service is healthy")
            print("   ✅ System can use FastEmbed for queries")
        else:
            print("   ⚠️  FastEmbed service needs attention")
            print("   ⚠️  System will fall back to Ollama")
        
        print("\n📋 Next Steps:")
        print("   1. Check logs: docker logs ecosystem-mcp-service | grep 'backend='")
        print("   2. Verify environment variables are set")
        print("   3. Monitor query performance over time")
        print("   4. Compare with Ollama-only performance")
        
        # Save results
        with open("/tmp/fastembed_validation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n💾 Results saved to: /tmp/fastembed_validation_results.json")


async def main():
    """Run validation."""
    validator = FastEmbedValidator()
    await validator.run_full_validation()


if __name__ == "__main__":
    asyncio.run(main())

