#!/usr/bin/env python3
"""
Comprehensive Ingestion Validation Script

Tests the complete MCP pipeline:
1. Ingest last 200 commits from repository
2. Monitor ingestion progress
3. Run validation queries
4. Compare responses to ground truth
"""

import httpx
import time
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import subprocess


class IngestionValidator:
    """Validates MCP ingestion and query capabilities."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)
        self.repo_path = Path("/Users/mykalthomas/Documents/work/Hackathon")
    
    def print_banner(self, text: str):
        """Print banner."""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)
    
    def print_section(self, text: str):
        """Print section."""
        print(f"\n{'─' * 80}")
        print(f"  {text}")
        print(f"{'─' * 80}")
    
    def check_service_health(self) -> bool:
        """Check service health."""
        try:
            response = self.client.get(f"{self.base_url}/health")
            data = response.json()
            status = data.get("status")
            
            print(f"✓ Service Status: {status}")
            
            components = data.get("components", {})
            for name, comp in components.items():
                comp_status = comp.get("status", "unknown") if isinstance(comp, dict) else comp
                print(f"  • {name}: {comp_status}")
            
            return status in ["healthy", "degraded"]
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    def get_initial_stats(self) -> Dict[str, Any]:
        """Get initial statistics."""
        try:
            response = self.client.get(f"{self.base_url}/api/v1/admin/stats")
            stats = response.json()
            
            print("\n📊 Initial Statistics:")
            print(f"  Documents: {stats.get('documents', {}).get('total', 0)}")
            print(f"  Embeddings: {stats.get('documents', {}).get('embeddings', 0)}")
            print(f"  Ingestion Jobs: {stats.get('documents', {}).get('total', 0)}")
            
            return stats
        except Exception as e:
            print(f"✗ Failed to get stats: {e}")
            return {}
    
    def get_recent_commits(self, count: int = 200) -> List[str]:
        """Get recent commit SHAs."""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%H"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            print(f"\n✓ Found {len(commits)} recent commits")
            
            # Show sample
            print(f"\n📝 Sample commits:")
            for i, sha in enumerate(commits[:5], 1):
                print(f"  {i}. {sha[:12]}")
            print(f"  ... and {len(commits) - 5} more")
            
            return commits
        except Exception as e:
            print(f"✗ Failed to get commits: {e}")
            return []
    
    def trigger_ingestion(self, mode: str = "historical") -> Dict[str, Any]:
        """Trigger ingestion job."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/admin/ingest",
                json={
                    "repo_path": str(self.repo_path),
                    "mode": mode
                }
            )
            
            if response.status_code not in [200, 201, 202]:
                print(f"✗ Ingestion failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return {}
            
            data = response.json()
            job_id = data.get("job_id")
            
            print(f"\n✓ Ingestion job created")
            print(f"  Job ID: {job_id}")
            print(f"  Mode: {mode}")
            print(f"  Status: {data.get('status', 'unknown')}")
            
            return data
        except Exception as e:
            print(f"✗ Failed to trigger ingestion: {e}")
            return {}
    
    def monitor_ingestion(self, timeout: int = 300):
        """Monitor ingestion progress."""
        print(f"\n⏳ Monitoring ingestion (timeout: {timeout}s)...")
        
        start_time = time.time()
        last_stats = None
        
        while (time.time() - start_time) < timeout:
            try:
                # Get current stats
                response = self.client.get(f"{self.base_url}/api/v1/admin/stats")
                stats = response.json()
                
                # Get queue status
                queue_response = self.client.get(f"{self.base_url}/api/v1/admin/queue-status")
                queue_stats = queue_response.json()
                
                doc_count = stats.get('documents', {}).get('total', 0)
                embedding_count = stats.get('documents', {}).get('embeddings', 0)
                
                ingestion_queue = queue_stats.get('ingestion_queue', 0)
                embedding_queue = queue_stats.get('embedding_queue', 0)
                failed_queue = queue_stats.get('failed_queue', 0)
                
                # Print update
                elapsed = int(time.time() - start_time)
                print(f"  [{elapsed:3d}s] Docs: {doc_count:4d} | "
                      f"Embeddings: {embedding_count:4d} | "
                      f"Queues: I:{ingestion_queue} E:{embedding_queue} F:{failed_queue}")
                
                # Check if done (no items in queue and doc count stable)
                if ingestion_queue == 0 and embedding_queue == 0:
                    if last_stats and last_stats['doc_count'] == doc_count:
                        print(f"\n✓ Ingestion complete!")
                        return {
                            'documents': doc_count,
                            'embeddings': embedding_count,
                            'duration': elapsed
                        }
                
                last_stats = {'doc_count': doc_count}
                time.sleep(5)
                
            except Exception as e:
                print(f"  ⚠️  Monitoring error: {e}")
                time.sleep(5)
        
        print(f"\n⏱️  Timeout reached after {timeout}s")
        return {}
    
    def create_validation_queries(self) -> List[Dict[str, Any]]:
        """Create validation queries based on known work."""
        queries = [
            {
                "query": "What testing improvements were made to ecosystem-mcp?",
                "expected_keywords": ["test", "E2E", "unit", "integration", "pytest", "coverage"],
                "context": "Recent testing work"
            },
            {
                "query": "What standard endpoints were implemented?",
                "expected_keywords": ["about-me", "endpoints", "provider-consumer", "standard"],
                "context": "Standard endpoint implementation"
            },
            {
                "query": "What bugs were fixed in the DocumentRepository?",
                "expected_keywords": ["model", "model_class", "repository", "AttributeError"],
                "context": "DocumentRepository bug fix"
            },
            {
                "query": "How does the circuit breaker pattern work?",
                "expected_keywords": ["circuit", "breaker", "CLOSED", "OPEN", "failure", "resilience"],
                "context": "Circuit breaker implementation"
            },
            {
                "query": "What is the response caching strategy?",
                "expected_keywords": ["cache", "Redis", "TTL", "decorator", "hits", "misses"],
                "context": "Caching implementation"
            },
            {
                "query": "How does the ingestion worker process documents?",
                "expected_keywords": ["worker", "ingestion", "Redis", "streams", "queue", "process"],
                "context": "Ingestion worker"
            },
            {
                "query": "What is the repository pattern implementation?",
                "expected_keywords": ["BaseRepository", "bulk", "operations", "transaction", "CRUD"],
                "context": "Repository pattern"
            },
            {
                "query": "How are embeddings generated?",
                "expected_keywords": ["embedding", "Ollama", "vector", "ChromaDB", "semantic"],
                "context": "Embedding generation"
            }
        ]
        
        print(f"\n✓ Created {len(queries)} validation queries")
        return queries
    
    def run_search_query(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Run semantic search query."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/search",
                json={"query": query, "limit": limit}
            )
            
            if response.status_code == 429:
                print(f"    ⚠️  Rate limited, waiting...")
                time.sleep(10)
                return self.run_search_query(query, limit)
            
            return response.json()
        except Exception as e:
            print(f"    ✗ Query failed: {e}")
            return {"results": []}
    
    def validate_query_response(
        self,
        query_text: str,
        response: Dict[str, Any],
        expected_keywords: List[str],
        context: str
    ) -> Dict[str, Any]:
        """Validate query response."""
        results = response.get("results", [])
        total_results = response.get("total_results", 0)
        
        print(f"\n  Query: {query_text}")
        print(f"  Context: {context}")
        print(f"  Results: {len(results)} (total: {total_results})")
        
        if not results:
            print(f"    ✗ No results returned")
            return {
                "success": False,
                "keyword_coverage": 0.0,
                "result_count": 0
            }
        
        # Check keyword coverage
        all_text = " ".join([
            r.get("content", "") + " " + r.get("file_path", "")
            for r in results
        ]).lower()
        
        matched_keywords = [kw for kw in expected_keywords if kw.lower() in all_text]
        keyword_coverage = len(matched_keywords) / len(expected_keywords) if expected_keywords else 0
        
        # Show top result
        top_result = results[0]
        print(f"  Top Result:")
        print(f"    File: {top_result.get('file_path', 'unknown')[:60]}")
        print(f"    Score: {top_result.get('score', 0):.3f}")
        print(f"    Snippet: {top_result.get('content', '')[:100]}...")
        
        # Show keyword matches
        print(f"  Keywords: {len(matched_keywords)}/{len(expected_keywords)} matched")
        print(f"    Matched: {', '.join(matched_keywords[:5])}")
        if len(matched_keywords) < len(expected_keywords):
            missing = [kw for kw in expected_keywords if kw not in matched_keywords]
            print(f"    Missing: {', '.join(missing[:3])}")
        
        success = keyword_coverage >= 0.5 and len(results) > 0
        status = "✓" if success else "✗"
        print(f"  {status} Coverage: {keyword_coverage:.1%}")
        
        return {
            "success": success,
            "keyword_coverage": keyword_coverage,
            "result_count": len(results),
            "matched_keywords": matched_keywords
        }
    
    def run_validation(self):
        """Run complete validation workflow."""
        self.print_banner("🧪 ECOSYSTEM-MCP INGESTION VALIDATION")
        
        # Step 1: Health Check
        self.print_section("Step 1: Service Health Check")
        if not self.check_service_health():
            print("\n❌ Service is not healthy. Aborting.")
            return False
        
        # Step 2: Initial Stats
        self.print_section("Step 2: Initial Statistics")
        initial_stats = self.get_initial_stats()
        
        # Step 3: Get Recent Commits
        self.print_section("Step 3: Retrieve Recent Commits")
        commits = self.get_recent_commits(200)
        
        if not commits:
            print("\n❌ No commits found. Aborting.")
            return False
        
        # Step 4: Trigger Ingestion
        self.print_section("Step 4: Trigger Ingestion")
        job = self.trigger_ingestion("historical")
        
        if not job:
            print("\n❌ Failed to create ingestion job. Aborting.")
            return False
        
        # Step 5: Monitor Progress
        self.print_section("Step 5: Monitor Ingestion Progress")
        final_stats = self.monitor_ingestion(timeout=300)
        
        if not final_stats:
            print("\n⚠️  Ingestion monitoring timed out or failed")
            print("  Continuing with validation anyway...")
        else:
            print(f"\n✓ Final Statistics:")
            print(f"  Documents: {final_stats.get('documents', 0)}")
            print(f"  Embeddings: {final_stats.get('embeddings', 0)}")
            print(f"  Duration: {final_stats.get('duration', 0)}s")
        
        # Step 6: Create Validation Queries
        self.print_section("Step 6: Validation Queries")
        queries = self.create_validation_queries()
        
        # Step 7: Run Queries
        self.print_section("Step 7: Execute Validation Queries")
        
        results = []
        for i, test in enumerate(queries, 1):
            print(f"\n[Query {i}/{len(queries)}]")
            
            response = self.run_search_query(test['query'])
            validation = self.validate_query_response(
                test['query'],
                response,
                test['expected_keywords'],
                test['context']
            )
            
            results.append({
                **test,
                **validation
            })
            
            time.sleep(2)  # Rate limiting courtesy
        
        # Step 8: Summary
        self.print_section("Step 8: Validation Summary")
        
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        avg_coverage = sum(r['keyword_coverage'] for r in results) / total if total > 0 else 0
        
        print(f"\n📊 Results:")
        print(f"  Queries Run: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {total - successful}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Avg Keyword Coverage: {avg_coverage:.1%}")
        
        print(f"\n📋 Per-Query Results:")
        for i, result in enumerate(results, 1):
            status = "✓" if result['success'] else "✗"
            print(f"  {i}. {status} {result['context']}: "
                  f"{result['keyword_coverage']:.0%} coverage, "
                  f"{result['result_count']} results")
        
        # Final Assessment
        self.print_section("✅ FINAL ASSESSMENT")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: MCP is working well!")
            print(f"  • {successful}/{total} queries successful")
            print(f"  • {avg_coverage:.0%} average keyword coverage")
            print(f"  • Semantic search is effective")
        elif success_rate >= 60:
            print("✅ GOOD: MCP is functional with room for improvement")
            print(f"  • {successful}/{total} queries successful")
            print(f"  • Consider ingesting more documents")
        else:
            print("⚠️  NEEDS WORK: MCP needs more training data")
            print(f"  • Only {successful}/{total} queries successful")
            print(f"  • Ingest more documents for better results")
        
        return success_rate >= 60


def main():
    """Main entry point."""
    print("Starting Ecosystem-MCP Ingestion Validation...")
    
    validator = IngestionValidator()
    success = validator.run_validation()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

