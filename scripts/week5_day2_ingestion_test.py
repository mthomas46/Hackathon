#!/usr/bin/env python3
"""
Week 5, Day 2: Large-Scale Ingestion Testing Script

This script orchestrates a comprehensive test of the ingestion system
using the Hackathon repository (~36,713 files).

Features:
- Detailed progress tracking
- Real-time performance metrics
- API health monitoring
- Comprehensive logging
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Configuration
API_BASE_URL = "http://localhost:8000"
REPO_PATH = "/host"  # Container path for /Users/mykalthomas/Documents/work/Hackathon
TEST_NAME = "Week 5 Day 2 - Large-Scale Test"

class Color:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a colored header"""
    print(f"\n{Color.HEADER}{Color.BOLD}{'='*80}{Color.ENDC}")
    print(f"{Color.HEADER}{Color.BOLD}{text:^80}{Color.ENDC}")
    print(f"{Color.HEADER}{Color.BOLD}{'='*80}{Color.ENDC}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Color.OKGREEN}✅ {text}{Color.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Color.OKCYAN}ℹ️  {text}{Color.ENDC}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Color.WARNING}⚠️  {text}{Color.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Color.FAIL}❌ {text}{Color.ENDC}")

def print_metric(label: str, value: Any, unit: str = ""):
    """Print a metric"""
    print(f"  {Color.OKBLUE}{label:.<40}{Color.ENDC} {Color.BOLD}{value}{unit}{Color.ENDC}")

def check_health() -> Dict[str, Any]:
    """Check API health"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return {}

def clear_database() -> bool:
    """Clear database for fresh test"""
    print_header("STEP 1: DATABASE RESET")
    
    try:
        # Get current stats
        print_info("Checking current database status...")
        health = check_health()
        if health:
            print_success("API is healthy")
            components = health.get('components', {})
            for name, status in components.items():
                state = status.get('status', 'unknown')
                emoji = "✅" if state == "healthy" else "⚠️"
                print(f"  {emoji} {name}: {state}")
        
        # Note: We'll keep existing data to avoid restart
        # In production, you'd use: docker-compose down --volumes && docker-compose up -d
        print_warning("Keeping existing data to avoid service restart")
        print_info("Starting ingestion will track as new job")
        return True
        
    except Exception as e:
        print_error(f"Database reset failed: {e}")
        return False

def start_ingestion(repo_path: str, use_git: bool = True) -> Optional[str]:
    """Start ingestion job"""
    print_header("STEP 2: START INGESTION JOB")
    
    payload = {
        "repo_path": repo_path,
        "use_git_history": use_git,
        "force_reingest": False
    }
    
    print_info(f"Starting ingestion for: {repo_path}")
    print_info(f"Git history enabled: {use_git}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        print_info("Sending POST request to /api/v1/admin/ingest...")
        response = requests.post(
            f"{API_BASE_URL}/api/v1/admin/ingest",
            json=payload,
            timeout=30
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            print_success(f"Ingestion job started!")
            print_metric("Job ID", job_id)
            print_metric("Status", data.get('status', 'unknown'))
            return job_id
        else:
            print_error(f"Failed to start ingestion: HTTP {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Failed to start ingestion: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/admin/ingest/{job_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print_warning(f"Failed to get job status: {e}")
        return None

def get_job_metrics(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job metrics"""
    try:
        # Try to get metrics from the job status itself
        status = get_job_status(job_id)
        if status:
            return {
                'embeddings_generated': status.get('total_embeddings', 0),
                'commits_processed': status.get('commits_processed', 0),
                'duration_seconds': status.get('duration_seconds', 0),
            }
        return None
    except Exception as e:
        return None

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = seconds / 60
        return f"{mins:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def calculate_rate(count: int, duration: float) -> float:
    """Calculate rate (items/sec)"""
    if duration > 0:
        return count / duration
    return 0.0

def monitor_job(job_id: str, check_interval: int = 10):
    """Monitor job progress with detailed metrics"""
    print_header("STEP 3: MONITOR INGESTION PROGRESS")
    
    start_time = time.time()
    last_processed = 0
    last_check_time = start_time
    
    print_info(f"Monitoring job: {job_id}")
    print_info(f"Check interval: {check_interval} seconds")
    print_info("Press Ctrl+C to stop monitoring (job will continue)\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Get job status
            status = get_job_status(job_id)
            if not status:
                print_warning("Could not retrieve job status")
                time.sleep(check_interval)
                continue
            
            # Get metrics if available
            metrics = get_job_metrics(job_id) or {}
            
            # Clear screen for better readability (optional)
            if iteration > 1:
                print("\n" + "─" * 80 + "\n")
            
            # Job info
            job_status = status.get('status', 'unknown')
            created_at = status.get('created_at', '')
            
            print(f"{Color.BOLD}📊 Job Status Update #{iteration}{Color.ENDC}")
            print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"  Elapsed: {format_duration(elapsed)}")
            print()
            
            # Status
            status_emoji = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(job_status, '❓')
            
            print(f"{Color.BOLD}Status:{Color.ENDC} {status_emoji} {job_status.upper()}")
            
            # Progress metrics
            total_files = status.get('total_files', 0)
            processed_files = status.get('processed_files', 0)
            failed_files = status.get('failed_files', 0)
            
            if total_files > 0:
                progress_pct = (processed_files / total_files) * 100
                print(f"{Color.BOLD}Progress:{Color.ENDC} {processed_files:,}/{total_files:,} files ({progress_pct:.1f}%)")
                
                # Progress bar
                bar_width = 50
                filled = int(bar_width * processed_files / total_files)
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"  [{bar}]")
            else:
                print(f"{Color.BOLD}Progress:{Color.ENDC} {processed_files:,} files processed")
            
            print()
            
            # Processing rates
            if processed_files > 0 and elapsed > 0:
                overall_rate = calculate_rate(processed_files, elapsed)
                
                # Instantaneous rate (since last check)
                time_since_last = current_time - last_check_time
                files_since_last = processed_files - last_processed
                instant_rate = calculate_rate(files_since_last, time_since_last) if time_since_last > 0 else 0
                
                print(f"{Color.BOLD}Performance:{Color.ENDC}")
                print_metric("Overall Rate", f"{overall_rate:.1f}", " files/sec")
                print_metric("Current Rate", f"{instant_rate:.1f}", " files/sec")
                
                if total_files > 0 and processed_files < total_files:
                    remaining = total_files - processed_files
                    if overall_rate > 0:
                        eta_seconds = remaining / overall_rate
                        print_metric("ETA", format_duration(eta_seconds))
            
            print()
            
            # Error rate
            if processed_files > 0:
                error_rate = (failed_files / processed_files) * 100
                error_color = Color.OKGREEN if error_rate < 1 else Color.WARNING if error_rate < 5 else Color.FAIL
                print(f"{Color.BOLD}Quality:{Color.ENDC}")
                print(f"  Failed files{error_color}: {failed_files:,} ({error_rate:.2f}%){Color.ENDC}")
            
            # Additional metrics
            if metrics:
                print()
                print(f"{Color.BOLD}Detailed Metrics:{Color.ENDC}")
                
                embeddings = metrics.get('embeddings_generated', 0)
                if embeddings > 0:
                    print_metric("Embeddings Generated", f"{embeddings:,}")
                    if elapsed > 0:
                        emb_rate = calculate_rate(embeddings, elapsed)
                        print_metric("Embedding Rate", f"{emb_rate:.1f}", " emb/sec")
                
                commits = metrics.get('commits_processed', 0)
                if commits > 0:
                    print_metric("Commits Processed", f"{commits:,}")
            
            # Update tracking variables
            last_processed = processed_files
            last_check_time = current_time
            
            # Check if job is complete
            if job_status in ['completed', 'failed', 'cancelled']:
                print()
                if job_status == 'completed':
                    print_success(f"Job completed in {format_duration(elapsed)}!")
                elif job_status == 'failed':
                    print_error(f"Job failed after {format_duration(elapsed)}")
                    error_msg = status.get('error_message', 'Unknown error')
                    print_error(f"Error: {error_msg}")
                else:
                    print_warning(f"Job was cancelled after {format_duration(elapsed)}")
                break
            
            # Wait before next check
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print()
        print_warning("Monitoring stopped by user")
        print_info("Job is still running in the background")
        print_info(f"Check status: curl {API_BASE_URL}/api/v1/jobs/{job_id}")

def print_final_report(job_id: str):
    """Print final test report"""
    print_header("STEP 4: FINAL REPORT")
    
    status = get_job_status(job_id)
    if not status:
        print_error("Could not retrieve final job status")
        return
    
    metrics = get_job_metrics(job_id) or {}
    
    # Summary
    print(f"{Color.BOLD}Test Summary:{Color.ENDC}")
    print_metric("Job ID", job_id)
    print_metric("Final Status", status.get('status', 'unknown'))
    print_metric("Total Files", f"{status.get('total_files', 0):,}")
    print_metric("Processed Files", f"{status.get('processed_files', 0):,}")
    print_metric("Failed Files", f"{status.get('failed_files', 0):,}")
    
    if metrics:
        print()
        print(f"{Color.BOLD}Performance Metrics:{Color.ENDC}")
        
        duration = metrics.get('duration_seconds', 0)
        if duration > 0:
            print_metric("Total Duration", format_duration(duration))
            
            processed = status.get('processed_files', 0)
            if processed > 0:
                rate = calculate_rate(processed, duration)
                print_metric("Average Rate", f"{rate:.1f}", " files/sec")
        
        embeddings = metrics.get('embeddings_generated', 0)
        if embeddings > 0:
            print_metric("Embeddings Generated", f"{embeddings:,}")
            if duration > 0:
                emb_rate = calculate_rate(embeddings, duration)
                print_metric("Embedding Rate", f"{emb_rate:.1f}", " emb/sec")
    
    # Success criteria
    print()
    print(f"{Color.BOLD}Success Criteria:{Color.ENDC}")
    
    criteria = {
        "Job Completed": status.get('status') == 'completed',
        "Files Processed": status.get('processed_files', 0) > 0,
        "Error Rate < 5%": (status.get('failed_files', 0) / max(status.get('processed_files', 1), 1)) < 0.05,
        "Embeddings Generated": metrics.get('embeddings_generated', 0) > 0,
    }
    
    for criterion, passed in criteria.items():
        emoji = "✅" if passed else "❌"
        print(f"  {emoji} {criterion}")
    
    overall_pass = all(criteria.values())
    print()
    if overall_pass:
        print_success("🎉 ALL SUCCESS CRITERIA MET!")
    else:
        print_warning("⚠️  Some success criteria not met")

def main():
    """Main test execution"""
    print_header("WEEK 5, DAY 2: LARGE-SCALE INGESTION TEST")
    
    print(f"{Color.BOLD}Test Configuration:{Color.ENDC}")
    print_metric("Test Name", TEST_NAME)
    print_metric("API Base URL", API_BASE_URL)
    print_metric("Repository Path", REPO_PATH)
    print_metric("Expected Files", "~36,713")
    print()
    
    # Step 1: Check health and prepare
    if not clear_database():
        print_error("Database preparation failed")
        sys.exit(1)
    
    # Step 2: Start ingestion
    job_id = start_ingestion(REPO_PATH, use_git=True)
    if not job_id:
        print_error("Failed to start ingestion job")
        sys.exit(1)
    
    print()
    print_info("Waiting 5 seconds for job to initialize...")
    time.sleep(5)
    
    # Step 3: Monitor progress
    monitor_job(job_id, check_interval=10)
    
    # Step 4: Final report
    print_final_report(job_id)
    
    print_header("TEST COMPLETE")
    print_success(f"Job ID: {job_id}")
    print_info("View detailed results in dashboard: http://localhost:8501")

if __name__ == "__main__":
    main()

