#!/usr/bin/env python3
"""
Stuck Worker Investigation Script

Investigates why specific jobs are stuck in processing state.

Jobs to investigate:
- 77a0086c-fce1-4a83-8c36-d810d3709c64
- 3528d6cb-6fec-4ad2-a60d-a1b4a16b74f0
- 998f218d-616c-490f-bdb1-0d04369c8a1b
- d6804cb4-f88a-4905-9383-f11175a89590
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add service to path
sys.path.insert(0, str(Path(__file__).parent / "services/ecosystem-mcp/src"))

from storage import get_database
from storage.repositories import IngestionJobRepository
from utils.redis_client import get_redis_client
from uuid import UUID


STUCK_JOB_IDS = [
    "77a0086c-fce1-4a83-8c36-d810d3709c64",
    "3528d6cb-6fec-4ad2-a60d-a1b4a16b74f0",
    "998f218d-616c-490f-bdb1-0d04369c8a1b",
    "d6804cb4-f88a-4905-9383-f11175a89590"
]


async def investigate_job(job_id_str: str) -> dict:
    """Investigate a single stuck job."""
    print(f"\n{'='*80}")
    print(f"🔍 Investigating Job: {job_id_str}")
    print(f"{'='*80}\n")
    
    job_id = UUID(job_id_str)
    db = get_database()
    redis = get_redis_client()
    
    investigation = {
        "job_id": job_id_str,
        "postgres_status": None,
        "redis_status": None,
        "issues": [],
        "recommendations": []
    }
    
    # 1. Check PostgreSQL status
    print("📊 PostgreSQL Status:")
    print("-" * 40)
    async with db.session() as session:
        repo = IngestionJobRepository(session)
        job = await repo.get_by_id(job_id)
        
        if not job:
            print(f"❌ Job NOT FOUND in PostgreSQL")
            investigation["postgres_status"] = "not_found"
            investigation["issues"].append("Job doesn't exist in database")
            investigation["recommendations"].append("Remove orphaned Redis messages if any")
        else:
            print(f"✅ Job found in PostgreSQL")
            print(f"   Status: {job.status}")
            print(f"   Mode: {job.mode}")
            print(f"   Repo Path: {job.repo_path}")
            print(f"   Created: {job.created_at}")
            print(f"   Started: {job.started_at}")
            print(f"   Completed: {job.completed_at}")
            print(f"   Processed: {job.processed_documents}")
            print(f"   Total: {job.total_documents}")
            print(f"   Failed: {job.failed_documents}")
            print(f"   Skipped: {job.skipped_documents}")
            print(f"   Embeddings: {job.embeddings_generated}")
            
            if job.error_message:
                print(f"   Error: {job.error_message}")
            
            # Check metadata
            if job.job_metadata:
                print(f"\n   Metadata:")
                for key, value in job.job_metadata.items():
                    if key == "worker_heartbeat":
                        try:
                            heartbeat_time = datetime.fromisoformat(value)
                            age = datetime.utcnow() - heartbeat_time
                            print(f"     {key}: {value} (age: {age})")
                        except:
                            print(f"     {key}: {value}")
                    else:
                        print(f"     {key}: {value}")
            
            investigation["postgres_status"] = {
                "exists": True,
                "status": job.status,
                "mode": job.mode,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "processed_documents": job.processed_documents,
                "total_documents": job.total_documents,
                "has_metadata": job.job_metadata is not None,
                "has_heartbeat": job.job_metadata and "worker_heartbeat" in job.job_metadata if job.job_metadata else False
            }
            
            # Check for issues
            if job.status == "processing":
                if job.started_at:
                    age = datetime.utcnow() - job.started_at
                    if age > timedelta(hours=4):
                        investigation["issues"].append(f"Job stuck in processing for {age}")
                        investigation["recommendations"].append("Job exceeded 4-hour timeout - mark as failed")
                    elif age > timedelta(minutes=30):
                        investigation["issues"].append(f"Job processing for {age} - may be stuck")
                
                if job.processed_documents == 0 and job.started_at:
                    age = datetime.utcnow() - job.started_at
                    if age > timedelta(minutes=5):
                        investigation["issues"].append(f"No documents processed after {age}")
                        investigation["recommendations"].append("Worker may be stuck - check logs")
                
                if job.job_metadata and "worker_heartbeat" in job.job_metadata:
                    try:
                        heartbeat = datetime.fromisoformat(job.job_metadata["worker_heartbeat"])
                        heartbeat_age = datetime.utcnow() - heartbeat
                        if heartbeat_age > timedelta(minutes=10):
                            investigation["issues"].append(f"Stale heartbeat: {heartbeat_age} old")
                            investigation["recommendations"].append("Worker appears dead - restart or recover job")
                    except:
                        pass
                else:
                    investigation["issues"].append("No worker heartbeat found")
                    investigation["recommendations"].append("Worker never started or crashed immediately")
    
    # 2. Check Redis status
    print(f"\n⚡ Redis Status:")
    print("-" * 40)
    
    # Check if job has messages in Redis stream
    try:
        messages = await redis.client.xrange(
            redis.INGESTION_STREAM,
            min="-",
            max="+",
            count=1000
        )
        
        found_in_stream = False
        message_id = None
        for msg_id, msg_data in messages:
            if msg_data.get(b"job_id", b"").decode() == job_id_str:
                found_in_stream = True
                message_id = msg_id.decode()
                print(f"✅ Found in Redis stream")
                print(f"   Message ID: {message_id}")
                break
        
        if not found_in_stream:
            print(f"❌ NOT found in Redis stream")
            investigation["redis_status"] = "not_in_stream"
            if job and job.status in ["queued", "pending"]:
                investigation["issues"].append("Job queued but no Redis message")
                investigation["recommendations"].append("Re-queue job to Redis")
        else:
            investigation["redis_status"] = {
                "in_stream": True,
                "message_id": message_id
            }
        
        # Check pending messages
        try:
            pending_info = await redis.client.xpending(
                redis.INGESTION_STREAM,
                redis.CONSUMER_GROUP
            )
            
            if isinstance(pending_info, dict):
                pending_count = pending_info.get("pending", 0)
            else:
                pending_count = pending_info
            
            print(f"\n   Total pending messages: {pending_count}")
            
            # Get detailed pending info
            if pending_count > 0:
                pending_detail = await redis.client.xpending_range(
                    redis.INGESTION_STREAM,
                    redis.CONSUMER_GROUP,
                    min="-",
                    max="+",
                    count=100
                )
                
                for pending_msg in pending_detail:
                    # Check if it's our message
                    if found_in_stream and pending_msg.get('message_id') == message_id.encode():
                        idle_time_ms = pending_msg.get('time_since_delivered', 0)
                        idle_time_s = idle_time_ms / 1000
                        consumer = pending_msg.get('consumer', b'').decode()
                        
                        print(f"\n   ⚠️  This job is PENDING:")
                        print(f"      Consumer: {consumer}")
                        print(f"      Idle time: {idle_time_s:.0f}s ({idle_time_s/60:.1f} min)")
                        print(f"      Delivery count: {pending_msg.get('times_delivered', 0)}")
                        
                        investigation["redis_status"]["pending"] = True
                        investigation["redis_status"]["idle_seconds"] = idle_time_s
                        investigation["redis_status"]["consumer"] = consumer
                        
                        if idle_time_s > 300:  # 5 minutes
                            investigation["issues"].append(f"Message pending for {idle_time_s/60:.1f} minutes")
                            investigation["recommendations"].append("Claim and reprocess message, or ACK if job already completed")
        
        except Exception as e:
            print(f"   Could not check pending: {e}")
        
        # Check stream length
        stream_len = await redis.client.xlen(redis.INGESTION_STREAM)
        print(f"\n   Total stream length: {stream_len}")
        
    except Exception as e:
        print(f"❌ Redis error: {e}")
        investigation["redis_status"] = {"error": str(e)}
    
    # 3. Diagnosis
    print(f"\n🔬 Diagnosis:")
    print("-" * 40)
    
    if investigation["issues"]:
        print("⚠️  Issues found:")
        for i, issue in enumerate(investigation["issues"], 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No issues detected")
    
    print(f"\n💡 Recommendations:")
    print("-" * 40)
    if investigation["recommendations"]:
        for i, rec in enumerate(investigation["recommendations"], 1):
            print(f"   {i}. {rec}")
    else:
        print("   No specific recommendations")
    
    return investigation


async def get_system_overview():
    """Get overall system status."""
    print(f"\n{'='*80}")
    print(f"📊 System Overview")
    print(f"{'='*80}\n")
    
    db = get_database()
    redis = get_redis_client()
    
    # PostgreSQL stats
    print("🗄️  PostgreSQL:")
    print("-" * 40)
    async with db.session() as session:
        repo = IngestionJobRepository(session)
        
        # Count by status
        from sqlalchemy import select, func
        from storage.db_models import IngestionJobModel
        
        status_query = select(
            IngestionJobModel.status,
            func.count(IngestionJobModel.id).label('count')
        ).group_by(IngestionJobModel.status)
        
        result = await session.execute(status_query)
        status_counts = {row.status: row.count for row in result}
        
        print(f"   Total jobs: {sum(status_counts.values())}")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        # Get running jobs
        running_jobs = await repo.get_running_jobs()
        print(f"\n   Currently processing: {len(running_jobs)}")
        for job in running_jobs:
            age = datetime.utcnow() - job.started_at if job.started_at else None
            print(f"     - {job.id} ({age} old)")
    
    # Redis stats
    print(f"\n⚡ Redis:")
    print("-" * 40)
    try:
        stream_len = await redis.client.xlen(redis.INGESTION_STREAM)
        print(f"   Stream length: {stream_len}")
        
        pending_info = await redis.client.xpending(
            redis.INGESTION_STREAM,
            redis.CONSUMER_GROUP
        )
        
        if isinstance(pending_info, dict):
            pending_count = pending_info.get("pending", 0)
        else:
            pending_count = pending_info
        
        print(f"   Pending messages: {pending_count}")
        
        # Consumer group info
        try:
            group_info = await redis.client.xinfo_groups(redis.INGESTION_STREAM)
            print(f"\n   Consumer groups:")
            for group in group_info:
                print(f"     - {group['name']}: {group.get('consumers', 0)} consumers, {group.get('pending', 0)} pending")
        except Exception as e:
            print(f"   Could not get consumer groups: {e}")
        
    except Exception as e:
        print(f"   Error: {e}")


async def generate_fix_commands(investigations):
    """Generate commands to fix stuck jobs."""
    print(f"\n{'='*80}")
    print(f"🔧 Fix Commands")
    print(f"{'='*80}\n")
    
    print("Based on the investigation, here are commands to fix the issues:\n")
    
    for inv in investigations:
        job_id = inv["job_id"]
        has_postgres = inv["postgres_status"] and inv["postgres_status"] != "not_found"
        has_redis = inv["redis_status"] and inv["redis_status"] != "not_in_stream"
        
        print(f"# Job: {job_id}")
        
        if has_postgres:
            status = inv["postgres_status"].get("status")
            
            if status == "processing":
                print(f"# This job is stuck in 'processing' state")
                print(f"# Option 1: Mark as failed (if truly stuck)")
                print(f'psql -d ecosystem_mcp -c "UPDATE ingestion_jobs SET status=\'failed\', error_message=\'Worker timeout - job stuck\', completed_at=NOW() WHERE id=\'{job_id}\';"')
                print()
                
                if has_redis:
                    print(f"# Option 2: ACK the Redis message to clear it from queue")
                    print(f"# (Use this if job is already completed or should be abandoned)")
                    print(f"curl -X POST http://localhost:8000/api/v1/admin/redis/ack-stuck-message/{job_id}")
                    print()
        
        if not has_postgres and has_redis:
            print(f"# This job has Redis message but no PostgreSQL record (orphaned)")
            print(f"curl -X DELETE http://localhost:8000/api/v1/admin/redis/orphaned-message/{job_id}")
            print()
        
        if has_postgres and not has_redis and status in ["queued", "pending"]:
            print(f"# This job is queued but has no Redis message")
            print(f"curl -X POST http://localhost:8000/api/v1/admin/redis/requeue-job/{job_id}")
            print()
        
        print()


async def main():
    """Main investigation routine."""
    print("="*80)
    print("🔍 STUCK WORKER INVESTIGATION")
    print("="*80)
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    # Get system overview
    await get_system_overview()
    
    # Investigate each stuck job
    investigations = []
    for job_id in STUCK_JOB_IDS:
        inv = await investigate_job(job_id)
        investigations.append(inv)
    
    # Generate fix commands
    await generate_fix_commands(investigations)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📝 Summary")
    print(f"{'='*80}\n")
    
    total_issues = sum(len(inv["issues"]) for inv in investigations)
    print(f"Jobs investigated: {len(STUCK_JOB_IDS)}")
    print(f"Total issues found: {total_issues}")
    
    print(f"\n✅ Investigation complete!")


if __name__ == "__main__":
    asyncio.run(main())

