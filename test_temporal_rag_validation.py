"""
Temporal RAG API Validation Script

Tests all temporal RAG endpoints against running services.
"""

import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import subprocess

# Configuration
API_BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_result(test_name: str, result: Dict[str, Any], success: bool = True):
    """Print test result in a formatted way."""
    status_emoji = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status_emoji} | {test_name}")
    print(f"{'-'*80}")
    print(json.dumps(result, indent=2))
    print(f"{'-'*80}\n")

def get_git_history():
    """Get git history for testing dates."""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H|%ad", "--date=iso", "-10"],
            capture_output=True,
            text=True,
            check=True
        )
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                sha, date_str = line.split('|')
                commits.append({
                    "sha": sha,
                    "date": datetime.fromisoformat(date_str.strip())
                })
        return commits
    except Exception as e:
        print(f"Warning: Could not get git history: {e}")
        return []


def test_query_as_of():
    """Test 1: Query As Of (Point in Time)"""
    print_section("TEST 1: Query As Of (Point in Time)")
    
    try:
        # Query as of one week ago
        as_of_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/rag/temporal/query",
            json={
                "question": "What is the RAG system architecture?",
                "as_of_date": as_of_date,
                "limit": 5
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result("Query As Of", {
                "status": "SUCCESS",
                "as_of_date": as_of_date,
                "answer_preview": result.get("answer", "...")[:100] + "...",
                "documents_found": len(result.get("documents", [])),
                "confidence": result.get("confidence", 0),
                "metadata": result.get("metadata", {})
            })
            return True
        else:
            print_result("Query As Of", {
                "status": "FAILED",
                "status_code": response.status_code,
                "error": response.text
            }, success=False)
            return False
            
    except Exception as e:
        print_result("Query As Of", {
            "status": "ERROR",
            "error": str(e)
        }, success=False)
        return False


def test_query_evolution(service_name: str = "ecosystem-mcp"):
    """Test 2: Query Evolution Tracking"""
    print_section("TEST 2: Query Evolution Tracking")
    
    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/rag/temporal/evolution",
            json={
                "topic": "test coverage strategy",
                "service_name": service_name,
                "limit_per_period": 3
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            result = response.json()
            evolution = result.get("evolution", [])
            
            print_result("Query Evolution", {
                "status": "SUCCESS",
                "timeline_found": result.get("timeline_id") is not None,
                "periods_analyzed": len(evolution),
                "evolution_summary": result.get("summary", "...")[:100] + "...",
                "metadata": result.get("metadata", {})
            })
            return True
        else:
            print_result("Query Evolution", {
                "status": "FAILED",
                "status_code": response.status_code,
                "error": response.text
            }, success=False)
            return False
            
    except Exception as e:
        print_result("Query Evolution", {
            "status": "ERROR",
            "error": str(e)
        }, success=False)
        return False


def test_query_comparison(start_date_1: datetime, end_date: datetime):
    """Test 3: Period Comparison"""
    print_section("TEST 3: Period Comparison")
    
    try:
        # Calculate midpoint for comparison
        midpoint = start_date_1 + (end_date - start_date_1) / 2
        
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/rag/temporal/comparison",
            json={
                "question": "test coverage improvements",
                "start_date": start_date_1.isoformat(),
                "end_date": end_date.isoformat(),
                "limit": 5
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print_result("Period Comparison", {
                "status": "SUCCESS",
                "period_1": f"{start_date_1.date()} to {midpoint.date()}",
                "period_2": f"{midpoint.date()} to {end_date.date()}",
                "comparison_summary": result.get("summary", "...")[:100] + "...",
                "changes_detected": len(result.get("changes", [])),
                "metadata": result.get("metadata", {})
            })
            return True
        else:
            print_result("Period Comparison", {
                "status": "FAILED",
                "status_code": response.status_code,
                "error": response.text
            }, success=False)
            return False
            
    except Exception as e:
        print_result("Period Comparison", {
            "status": "ERROR",
            "error": str(e)
        }, success=False)
        return False


def test_versioning_as_of():
    """Test 4: Versioning As Of Query"""
    print_section("TEST 4: Versioning As Of Query")
    
    try:
        as_of_date = (datetime.now() - timedelta(days=5)).date().isoformat()
        
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/versioning/as-of",
            json={
                "query": "multi-pass RAG implementation",
                "as_of_date": as_of_date,
                "limit": 5
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result("Versioning As Of", {
                "status": "SUCCESS",
                "as_of_date": as_of_date,
                "documents_found": len(result.get("documents", [])),
                "has_answer": "answer" in result,
                "metadata": result.get("metadata", {})
            })
            return True
        else:
            print_result("Versioning As Of", {
                "status": "FAILED",
                "status_code": response.status_code,
                "error": response.text
            }, success=False)
            return False
            
    except Exception as e:
        print_result("Versioning As Of", {
            "status": "ERROR",
            "error": str(e)
        }, success=False)
        return False


def test_timeline_query():
    """Test 5: Timeline Query"""
    print_section("TEST 5: Timeline Query")
    
    try:
        # Query timeline for ecosystem-mcp service
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/rag/temporal/timeline",
            json={
                "service_name": "ecosystem-mcp",
                "limit": 10
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if we got a successful response
            if result.get("success"):
                timeline = result.get("timeline", {})
                
                print_result("Timeline Query", {
                    "status": "SUCCESS",
                    "service_name": result.get("service_name"),
                    "timeline_id": timeline.get("timeline_id"),
                    "timeline_name": timeline.get("name"),
                    "total_periods": timeline.get("total_periods", 0),
                    "start_date": timeline.get("start_date"),
                    "end_date": timeline.get("end_date"),
                    "confidence_level": timeline.get("confidence_level")
                })
                return True
            else:
                print_result("Timeline Query", {
                    "status": "FAILED",
                    "error": "Response not successful",
                    "response": result
                }, success=False)
                return False
        else:
            print_result("Timeline Query", {
                "status": "FAILED",
                "status_code": response.status_code,
                "error": response.text
            }, success=False)
            return False
            
    except Exception as e:
        print_result("Timeline Query", {
            "status": "ERROR",
            "error": str(e)
        }, success=False)
        return False


def main():
    print_section("TEMPORAL RAG API VALIDATION")
    print("Using Real Git History for Testing")
    print("="*80 + "\n")

    # Get git history for dynamic testing dates
    git_history = get_git_history()
    if not git_history:
        print("❌ No git history found. Cannot run temporal RAG tests.")
        return False

    # Define test dates based on recent history
    today = datetime.now()
    one_week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)
    four_weeks_ago = today - timedelta(days=28)

    # Test all operations
    results = {
        "Query As Of (Point in Time)": test_query_as_of(),
        "Query Evolution Tracking": test_query_evolution(service_name="ecosystem-mcp"),
        "Period Comparison": test_query_comparison(two_weeks_ago, today),
        "Versioning As Of Query": test_versioning_as_of(),
        "Timeline Query": test_timeline_query()
    }

    # Summary
    print_section("VALIDATION SUMMARY")
    passed_count = sum(1 for v in results.values() if v is True)
    total = len(results)

    print(f"\nTests Passed: {passed_count}/{total}\n")

    for test_name, test_passed in results.items():
        status = "✅ PASS" if test_passed else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print("\n" + "="*80)

    if passed_count == total:
        print("🎉 ALL TEMPORAL RAG OPERATIONS VALIDATED!")
    else:
        print(f"⚠️  {total - passed_count} tests failed or require setup")

    print("="*80 + "\n")

    return passed_count == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
