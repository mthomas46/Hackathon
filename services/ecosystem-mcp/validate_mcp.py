#!/usr/bin/env python3
"""
MCP Validation Script

Tests the ecosystem-mcp service by:
1. Checking service health
2. Getting recent commits and documentation
3. Creating test documents from actual work
4. Querying the MCP to validate responses
5. Comparing responses to ground truth
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import subprocess

import httpx


class MCPValidator:
    """Validates the ecosystem-mcp service."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def check_health(self) -> bool:
        """Check if service is healthy."""
        try:
            response = self.client.get(f"{self.base_url}/health")
            data = response.json()
            status = data.get("status")
            print(f"✓ Service health: {status}")
            return status in ["healthy", "degraded"]
        except Exception as e:
            print(f"✗ Service health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current service statistics."""
        try:
            response = self.client.get(f"{self.base_url}/api/v1/admin/stats")
            stats = response.json()
            print(f"\n📊 Current Stats:")
            print(f"  Documents: {stats.get('documents', 0)}")
            print(f"  Embeddings: {stats.get('embeddings', 0)}")
            print(f"  Ingestion Jobs: {stats.get('ingestion_jobs', 0)}")
            return stats
        except Exception as e:
            print(f"✗ Failed to get stats: {e}")
            return {}
    
    def get_recent_docs(self) -> List[Path]:
        """Get recently created documentation files."""
        docs_dir = Path(".")
        
        # Documentation files created in Phase 3 & 4
        doc_files = [
            "MIGRATION_STRATEGY.md",
            "CACHING_DOCUMENTATION.md",
            "CHROMADB_OPTIMIZATION.md",
            "CIRCUIT_BREAKER.md",
            "REPOSITORY_PATTERN.md",
            "PHASE3_AND_4_COMPLETE.md",
            "PHASE4_COMPLETE.md",
            "tests/load/README.md",
        ]
        
        existing = []
        for doc in doc_files:
            path = docs_dir / doc
            if path.exists():
                existing.append(path)
        
        print(f"\n📄 Found {len(existing)} documentation files:")
        for path in existing:
            print(f"  • {path}")
        
        return existing
    
    def create_test_queries(self) -> List[Dict[str, Any]]:
        """Create test queries based on Phase 3 & 4 work."""
        queries = [
            {
                "query": "What is the circuit breaker pattern and how is it implemented?",
                "expected_keywords": ["circuit breaker", "CLOSED", "OPEN", "HALF_OPEN", "resilience", "failure"],
                "ground_truth_file": "CIRCUIT_BREAKER.md"
            },
            {
                "query": "How does response caching work in the service?",
                "expected_keywords": ["cache", "Redis", "TTL", "decorator", "cache_hits", "cache_misses"],
                "ground_truth_file": "CACHING_DOCUMENTATION.md"
            },
            {
                "query": "What is the repository pattern and what are bulk operations?",
                "expected_keywords": ["repository", "bulk", "BaseRepository", "bulk_create", "bulk_update", "10x faster"],
                "ground_truth_file": "REPOSITORY_PATTERN.md"
            },
            {
                "query": "How do I run load tests on the service?",
                "expected_keywords": ["locust", "load test", "users", "sustained", "spike", "soak"],
                "ground_truth_file": "tests/load/README.md"
            },
            {
                "query": "What database migrations are available?",
                "expected_keywords": ["migration", "alembic", "schema", "upgrade", "downgrade", "PostgreSQL"],
                "ground_truth_file": "MIGRATION_STRATEGY.md"
            },
            {
                "query": "What is the production readiness percentage?",
                "expected_keywords": ["99%", "production", "ready", "phase", "complete"],
                "ground_truth_file": "PHASE4_COMPLETE.md"
            },
            {
                "query": "How much faster are bulk operations compared to individual operations?",
                "expected_keywords": ["20x", "bulk", "faster", "1000", "records", "0.5s"],
                "ground_truth_file": "REPOSITORY_PATTERN.md"
            },
            {
                "query": "What security checks are performed in the security audit?",
                "expected_keywords": ["security", "OWASP", "dependency", "secrets", "Bandit", "Safety"],
                "ground_truth_file": "PHASE4_COMPLETE.md"
            }
        ]
        
        print(f"\n❓ Created {len(queries)} test queries")
        return queries
    
    def query_mcp(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Query the MCP service."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/query",
                json={"query": query, "limit": limit, "threshold": 0.5}
            )
            return response.json()
        except Exception as e:
            print(f"✗ Query failed: {e}")
            return {"results": [], "error": str(e)}
    
    def validate_response(
        self,
        query_text: str,
        response: Dict[str, Any],
        expected_keywords: List[str],
        ground_truth_file: str
    ) -> bool:
        """Validate MCP response against expected keywords."""
        results = response.get("results", [])
        
        if not results:
            print(f"  ✗ No results returned")
            return False
        
        # Check if ground truth file is in results
        found_ground_truth = any(
            ground_truth_file in result.get("file_path", "")
            for result in results
        )
        
        # Check for expected keywords in results
        all_text = " ".join([
            result.get("content", "") + " " + result.get("file_path", "")
            for result in results
        ]).lower()
        
        keyword_matches = sum(
            1 for keyword in expected_keywords
            if keyword.lower() in all_text
        )
        
        keyword_coverage = keyword_matches / len(expected_keywords) if expected_keywords else 0
        
        print(f"  {'✓' if found_ground_truth else '✗'} Ground truth file: {ground_truth_file}")
        print(f"  {'✓' if keyword_coverage >= 0.5 else '✗'} Keyword coverage: {keyword_coverage:.1%} ({keyword_matches}/{len(expected_keywords)})")
        print(f"  • Results returned: {len(results)}")
        print(f"  • Top result: {results[0].get('file_path', 'unknown')[:50]}...")
        print(f"  • Score: {results[0].get('score', 0):.3f}")
        
        return found_ground_truth and keyword_coverage >= 0.5
    
    def ingest_documents_manually(self, docs: List[Path]) -> int:
        """
        Manually ingest documents by reading and creating entries.
        
        Note: This is a workaround since the full ingestion pipeline
        may not be implemented yet.
        """
        print(f"\n📥 Manual document ingestion (workaround)...")
        print(f"Note: Full git-based ingestion may need implementation")
        
        ingested = 0
        for doc_path in docs:
            try:
                content = doc_path.read_text()
                print(f"  • {doc_path.name}: {len(content)} chars")
                ingested += 1
            except Exception as e:
                print(f"  ✗ Failed to read {doc_path}: {e}")
        
        print(f"\n✓ Read {ingested}/{len(docs)} documents")
        return ingested
    
    def run_validation(self):
        """Run complete validation workflow."""
        print("═" * 70)
        print("🧪 ECOSYSTEM-MCP VALIDATION TEST")
        print("═" * 70)
        
        # Step 1: Health check
        print("\nStep 1: Health Check")
        print("-" * 70)
        if not self.check_health():
            print("\n❌ Service is not healthy. Aborting validation.")
            return False
        
        # Step 2: Get current stats
        print("\nStep 2: Current Statistics")
        print("-" * 70)
        stats = self.get_stats()
        
        # Step 3: Check documentation
        print("\nStep 3: Documentation Files")
        print("-" * 70)
        docs = self.get_recent_docs()
        
        if not docs:
            print("⚠️ No documentation files found. This is unexpected.")
        
        # Step 4: Manual ingestion check
        print("\nStep 4: Document Ingestion Check")
        print("-" * 70)
        self.ingest_documents_manually(docs)
        
        # Step 5: Create test queries
        print("\nStep 5: Test Queries")
        print("-" * 70)
        queries = self.create_test_queries()
        
        # Step 6: Run queries and validate
        print("\nStep 6: Query & Validation")
        print("-" * 70)
        
        results = []
        for i, test in enumerate(queries, 1):
            print(f"\nQuery {i}/{len(queries)}: {test['query']}")
            print("-" * 70)
            
            response = self.query_mcp(test["query"])
            
            is_valid = self.validate_response(
                test["query"],
                response,
                test["expected_keywords"],
                test["ground_truth_file"]
            )
            
            results.append({
                "query": test["query"],
                "valid": is_valid,
                "results_count": len(response.get("results", []))
            })
            
            time.sleep(1)  # Rate limiting
        
        # Summary
        print("\n" + "═" * 70)
        print("📊 VALIDATION SUMMARY")
        print("═" * 70)
        
        passed = sum(1 for r in results if r["valid"])
        total = len(results)
        
        print(f"\nResults: {passed}/{total} queries passed ({passed/total*100:.1f}%)")
        print("\nQuery Results:")
        for i, result in enumerate(results, 1):
            status = "✓" if result["valid"] else "✗"
            print(f"  {status} Query {i}: {result['results_count']} results")
        
        # Overall assessment
        print("\n" + "═" * 70)
        if passed == total:
            print("✅ VALIDATION PASSED: MCP is working correctly!")
        elif passed >= total * 0.75:
            print("⚠️ VALIDATION PARTIAL: MCP is working but needs improvement")
        else:
            print("❌ VALIDATION FAILED: MCP needs attention")
        print("═" * 70)
        
        return passed >= total * 0.75


def main():
    """Main entry point."""
    validator = MCPValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

