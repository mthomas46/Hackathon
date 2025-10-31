#!/usr/bin/env python3
"""
Stuck Worker Investigation Script (API-based)

Investigates why specific jobs are stuck in processing state using API calls.

Jobs to investigate:
- 77a0086c-fce1-4a83-8c36-d810d3709c64
- 3528d6cb-6fec-4ad2-a60d-a1b4a16b74f0
- 998f218d-616c-490f-bdb1-0d04369c8a1b
- d6804cb4-f88a-4905-9383-f11175a89590
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List


API_BASE = "http://localhost:8000"

STUCK_JOB_IDS = [
    "77a0086c-fce1-4a83-8c36-d810d3709c64",
    "3528d6cb-6fec-4ad2-a60d-a1b4a16b74f0",
    "998f218d-616c-490f-bdb1-0d04369c8a1b",
    "d6804cb4-f88a-4905-9383-f11175a89590"
]


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def print_subsection(title: str):
    """Print a subsection header."""
    print(f"\n{title}")
    print("-" * 40)


def investigate_job(job_id: str) -> Dict[str, Any]:
    """Investigate a single stuck job."""
    print_section(f"🔍 Investigating Job: {job_id}")
    
    investigation = {
        "job_id": job_id,
        "postgres_status": None,
        "redis_status": None,
        "issues": [],
        "recommendations": []
    }
    
    # 1. Get job status from API
    print_subsection("📊 Job Status")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/ingest/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            
            # Find our job
            job = None
            for j in jobs:
                if j.get("job_id") == job_id:
                    job = j
                    break
            
            if not job:
                print(f"❌ Job NOT FOUND in database")
                investigation["postgres_status"] = "not_found"
                investigation["issues"].append("Job doesn't exist in database")
                investigation["recommendations"].append("Remove orphaned Redis messages if any")
            else:
                print(f"✅ Job found")
                print(f"   Status: {job.get('status')}")
                print(f"   Mode: {job.get('mode')}")
                print(f"   Processing Mode: {job.get('processing_mode', 'git_history')}")
                print(f"   Repo Path: {job.get('repo_path')}")
                print(f"   Started: {job.get('started_at')}")
                print(f"   Completed: {job.get('completed_at')}")
                print(f"   Processed: {job.get('processed_documents', 0)}")
                print(f"   Total: {job.get('total_documents', 0)}")
                print(f"   Failed: {job.get('failed_documents', 0)}")
                print(f"   Skipped: {job.get('skipped_documents', 0)}")
                print(f"   Embeddings: {job.get('embeddings_generated', 0)}")
                
                if job.get('error_message'):
                    print(f"   Error: {job.get('error_message')}")
                
                investigation["postgres_status"] = job
                
                # Analyze issues
                status = job.get('status')
                started_at = job.get('started_at')
                processed = job.get('processed_documents', 0)
                
                if status == "processing":
                    if started_at:
                        try:
                            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                            age = datetime.now(start_time.tzinfo) - start_time
                            print(f"   Age: {age}")
                            
                            if age > timedelta(hours=4):
                                investigation["issues"].append(f"Job stuck in processing for {age}")
                                investigation["recommendations"].append("Job exceeded 4-hour timeout - should be marked as failed")
                            elif age > timedelta(minutes=30):
                                investigation["issues"].append(f"Job processing for {age} - may be stuck")
                                investigation["recommendations"].append("Monitor or consider restarting")
                        except Exception as e:
                            print(f"   Could not parse started_at: {e}")
                    
                    if processed == 0 and started_at:
                        try:
                            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                            age = datetime.now(start_time.tzinfo) - start_time
                            if age > timedelta(minutes=5):
                                investigation["issues"].append(f"No documents processed after {age}")
                                investigation["recommendations"].append("Worker may be stuck - check worker logs")
                        except:
                            pass
        else:
            print(f"❌ API error: HTTP {response.status_code}")
            investigation["postgres_status"] = {"error": f"HTTP {response.status_code}"}
    
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        investigation["postgres_status"] = {"error": str(e)}
    
    # 2. Check Redis status
    print_subsection("⚡ Redis Stream Status")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/redis/stream-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", {})
            
            ingestion_stream = status.get("ingestion_stream", {})
            if ingestion_stream.get("exists"):
                length = ingestion_stream.get("length", 0)
                print(f"✅ Redis stream exists")
                print(f"   Stream length: {length}")
                print(f"   Consumer groups: {ingestion_stream.get('groups', 0)}")
            else:
                print(f"❌ Redis stream doesn't exist or error")
                print(f"   Error: {ingestion_stream.get('error', 'Unknown')}")
            
            pending = status.get("pending_messages", {})
            if isinstance(pending, dict):
                pending_count = pending.get("count", 0)
                print(f"   Pending messages: {pending_count}")
            
            investigation["redis_status"] = status
        else:
            print(f"❌ API error: HTTP {response.status_code}")
    
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    # 3. Check worker health
    print_subsection("⚙️ Worker Health")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/workers/ingestion/status", timeout=10)
        if response.status_code == 200:
            worker = response.json()
            print(f"   Running: {worker.get('running', False)}")
            print(f"   Healthy: {worker.get('healthy', False)}")
            print(f"   Processing: {worker.get('processing', False)}")
        else:
            print(f"❌ Could not get worker status: HTTP {response.status_code}")
    
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    # 4. Check stuck workers
    print_subsection("🔍 Stuck Worker Detection")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/workers/stuck-check", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stuck_count = data.get("stuck_workers", 0)
            stuck_jobs = data.get("stuck_jobs", [])
            
            print(f"   Total processing jobs: {data.get('total_processing', 0)}")
            print(f"   Stuck workers: {stuck_count}")
            
            # Check if our job is in stuck list
            for stuck in stuck_jobs:
                if stuck.get("job_id") == job_id:
                    print(f"\n   ⚠️ THIS JOB IS DETECTED AS STUCK:")
                    print(f"      Reason: {stuck.get('reason')}")
                    print(f"      Worker: {stuck.get('worker_id', 'unknown')}")
                    if 'heartbeat_age_minutes' in stuck:
                        print(f"      Heartbeat age: {stuck.get('heartbeat_age_minutes'):.1f} minutes")
                    
                    investigation["issues"].append(f"Detected as stuck: {stuck.get('reason')}")
                    investigation["recommendations"].append("Worker needs restart or job needs recovery")
        else:
            print(f"   Could not check: HTTP {response.status_code}")
    
    except requests.RequestException as e:
        print(f"   Error: {e}")
    
    # 5. Diagnosis
    print_subsection("🔬 Diagnosis")
    if investigation["issues"]:
        print("⚠️  Issues found:")
        for i, issue in enumerate(investigation["issues"], 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No issues detected")
    
    print_subsection("💡 Recommendations")
    if investigation["recommendations"]:
        for i, rec in enumerate(investigation["recommendations"], 1):
            print(f"   {i}. {rec}")
    else:
        print("   No specific recommendations")
    
    return investigation


def get_system_overview():
    """Get overall system status."""
    print_section("📊 System Overview")
    
    # Get all job statuses
    print_subsection("🗄️  All Jobs")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/ingest/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            total = data.get("total", 0)
            
            # Count by status
            status_counts = {}
            processing_jobs = []
            for job in jobs:
                status = job.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
                if status == "processing":
                    processing_jobs.append(job)
            
            print(f"   Total jobs: {total}")
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
            
            if processing_jobs:
                print(f"\n   Currently processing:")
                for job in processing_jobs:
                    job_id_short = job.get('job_id', '')[:12]
                    started = job.get('started_at', 'unknown')
                    try:
                        if started != 'unknown':
                            start_time = datetime.fromisoformat(started.replace('Z', '+00:00'))
                            age = datetime.now(start_time.tzinfo) - start_time
                            print(f"     - {job_id_short}... (age: {age})")
                        else:
                            print(f"     - {job_id_short}... (age: unknown)")
                    except:
                        print(f"     - {job_id_short}...")
        else:
            print(f"   API error: HTTP {response.status_code}")
    
    except requests.RequestException as e:
        print(f"   Connection error: {e}")
    
    # Get Redis stream status
    print_subsection("⚡ Redis")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/redis/stream-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", {})
            
            stream = status.get("ingestion_stream", {})
            if stream.get("exists"):
                print(f"   Stream length: {stream.get('length', 0)}")
                print(f"   Consumer groups: {stream.get('groups', 0)}")
            
            pending = status.get("pending_messages", {})
            if isinstance(pending, dict):
                print(f"   Pending messages: {pending.get('count', 0)}")
        else:
            print(f"   API error: HTTP {response.status_code}")
    
    except requests.RequestException as e:
        print(f"   Connection error: {e}")
    
    # Get worker health
    print_subsection("⚙️ Worker Health")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/workers/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   Overall healthy: {data.get('overall_healthy', False)}")
            
            workers = data.get("workers", {})
            ingestion = workers.get("ingestion", {})
            print(f"   Ingestion worker:")
            print(f"     - Running: {ingestion.get('running', False)}")
            print(f"     - Healthy: {ingestion.get('healthy', False)}")
            print(f"     - Processing: {ingestion.get('processing', False)}")
        else:
            print(f"   API error: HTTP {response.status_code}")
    
    except requests.RequestException as e:
        print(f"   Connection error: {e}")


def generate_fix_commands(investigations: List[Dict[str, Any]]):
    """Generate commands to fix stuck jobs."""
    print_section("🔧 Fix Commands")
    
    print("Based on the investigation, here are commands to fix the issues:\n")
    
    for inv in investigations:
        job_id = inv["job_id"]
        postgres_status = inv.get("postgres_status")
        
        if not postgres_status or postgres_status == "not_found":
            print(f"# Job: {job_id}")
            print(f"# Job not found in database - may have been already cleaned up")
            print()
            continue
        
        if isinstance(postgres_status, dict) and "error" in postgres_status:
            print(f"# Job: {job_id}")
            print(f"# Could not get job status: {postgres_status['error']}")
            print()
            continue
        
        status = postgres_status.get("status")
        job_id_short = job_id[:12]
        
        print(f"# Job: {job_id_short}... (Status: {status})")
        
        if status == "processing":
            print(f"# This job is stuck in 'processing' state")
            print()
            print(f"# Option 1: Cancel the job (marks as failed)")
            print(f"curl -X POST http://localhost:8000/api/v1/admin/ingest/{job_id}/cancel")
            print()
            print(f"# Option 2: Try worker auto-recovery")
            print(f"curl -X POST http://localhost:8000/api/v1/admin/workers/ingestion/auto-recover")
            print()
            print(f"# Option 3: Restart the worker (affects all jobs)")
            print(f"curl -X POST http://localhost:8000/api/v1/admin/workers/ingestion/restart")
            print()
        
        print()


def test_api_connectivity():
    """Test if API is accessible."""
    print("🔌 Testing API connectivity...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is accessible\n")
            return True
        else:
            print(f"⚠️  API returned HTTP {response.status_code}\n")
            return False
    except requests.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Make sure the ecosystem-mcp service is running at {API_BASE}\n")
        return False


def main():
    """Main investigation routine."""
    print("="*80)
    print("🔍 STUCK WORKER INVESTIGATION (API-based)")
    print("="*80)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"API Base: {API_BASE}")
    print()
    
    # Test connectivity
    if not test_api_connectivity():
        print("⚠️  Continuing anyway, but results may be incomplete...\n")
    
    # Get system overview
    get_system_overview()
    
    # Investigate each stuck job
    investigations = []
    for job_id in STUCK_JOB_IDS:
        inv = investigate_job(job_id)
        investigations.append(inv)
    
    # Generate fix commands
    generate_fix_commands(investigations)
    
    # Summary
    print_section("📝 Summary")
    
    total_issues = sum(len(inv.get("issues", [])) for inv in investigations)
    jobs_not_found = sum(1 for inv in investigations if inv.get("postgres_status") == "not_found")
    jobs_stuck = sum(1 for inv in investigations if len(inv.get("issues", [])) > 0)
    
    print(f"Jobs investigated: {len(STUCK_JOB_IDS)}")
    print(f"Jobs not found: {jobs_not_found}")
    print(f"Jobs with issues: {jobs_stuck}")
    print(f"Total issues found: {total_issues}")
    
    print(f"\n✅ Investigation complete!")
    print(f"\n💡 Next steps:")
    print(f"   1. Review the fix commands above")
    print(f"   2. Check Docker logs: docker logs ecosystem-mcp-service --tail 100")
    print(f"   3. Access dashboard: http://localhost:8001")


if __name__ == "__main__":
    main()

