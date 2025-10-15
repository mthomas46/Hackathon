# 🔄 Temporal Versioning Migration Guide

**Complete guide for migrating existing databases to the new temporal versioning system**

---

## 📋 Overview

The temporal versioning system adds:
1. ✅ New table: `document_content_store` (deduplicated content)
2. ✅ New table: `document_timeline` (event stream)
3. ✅ New columns to existing `document_versions` table
4. ✅ Helper functions for efficient queries
5. ✅ Indexes for performance
6. ✅ Views for common queries

**Migration Safety:**
- ✅ Non-destructive (adds columns, doesn't drop anything)
- ✅ Backwards compatible (existing data preserved)
- ✅ Idempotent (can be run multiple times safely)

---

## 🚦 Pre-Migration Checklist

### 1. Check Current State

```bash
# Check if database is running
docker-compose -f docker-compose-mcp-ecosystem.yml ps ecosystem-mcp-postgres

# If not running, start it
docker-compose -f docker-compose-mcp-ecosystem.yml up -d ecosystem-mcp-postgres
```

### 2. Backup Database (IMPORTANT!)

```bash
# Create backup directory
mkdir -p backups

# Backup entire database
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  pg_dump -U postgres -d ecosystem_mcp > backups/ecosystem_mcp_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup was created
ls -lh backups/
```

### 3. Check Existing Schema

```bash
# Check existing document tables
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\dt document*"

# Check document_versions columns
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\d document_versions"

# Count existing documents
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "SELECT COUNT(*) FROM documents;"
```

---

## 🚀 Migration Steps

### Step 1: Run Database Migration

```bash
cd /Users/mykalthomas/Documents/work/Hackathon

# Copy migration file into container
docker cp services/ecosystem-mcp/migrations/add_temporal_content_versioning.sql \
  ecosystem-mcp-postgres:/tmp/

# Run migration
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -f /tmp/add_temporal_content_versioning.sql
```

**Expected Output:**
```
BEGIN
CREATE TABLE
ALTER TABLE
ALTER TABLE
... (more ALTER TABLE statements)
CREATE INDEX
... (more CREATE INDEX statements)
CREATE FUNCTION
... (more CREATE FUNCTION statements)
CREATE VIEW
... (more CREATE VIEW statements)
COMMIT
```

### Step 2: Verify Migration

```bash
# Check new tables exist
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\dt document_content_store"

docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\dt document_timeline"

# Check new columns added
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\d document_versions"

# Check functions exist
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\df get_all_documents_as_of"

docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\df get_document_timeline"

# Check views exist
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\dv latest_document_versions"

docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -c "\dv content_deduplication_stats"
```

### Step 3: Backfill Existing Data (Optional but Recommended)

If you have existing documents, you'll want to populate the new fields:

```bash
# Create backfill script
cat > /tmp/backfill_temporal_data.sql << 'EOF'
-- Backfill temporal data for existing document_versions

BEGIN;

-- Set modified_at from created_at for existing versions (if not already set)
UPDATE document_versions
SET modified_at = created_at
WHERE modified_at IS NULL;

-- Set source_path from documents table (if not already set)
UPDATE document_versions v
SET source_path = d.file_path
FROM documents d
WHERE v.document_id = d.id
  AND v.source_path IS NULL;

-- Set title from documents table (if not already set)
UPDATE document_versions v
SET title = d.file_path
FROM documents d
WHERE v.document_id = d.id
  AND v.title IS NULL;

-- Mark most recent version as latest for each document
WITH latest_versions AS (
  SELECT DISTINCT ON (document_id)
    id,
    document_id
  FROM document_versions
  ORDER BY document_id, created_at DESC, version_number DESC
)
UPDATE document_versions v
SET is_latest = (v.id IN (SELECT id FROM latest_versions));

-- Assign timeline positions to existing versions
WITH ordered_versions AS (
  SELECT 
    id,
    ROW_NUMBER() OVER (ORDER BY created_at, version_number) as position
  FROM document_versions
  WHERE timeline_position IS NULL
)
UPDATE document_versions v
SET timeline_position = o.position
FROM ordered_versions o
WHERE v.id = o.id;

COMMIT;

-- Show summary
SELECT 
  COUNT(*) as total_versions,
  COUNT(DISTINCT document_id) as unique_documents,
  COUNT(*) FILTER (WHERE is_latest = true) as latest_versions,
  COUNT(*) FILTER (WHERE timeline_position IS NOT NULL) as positioned_versions,
  MIN(created_at) as earliest_version,
  MAX(created_at) as latest_version
FROM document_versions;
EOF

# Copy and run backfill script
docker cp /tmp/backfill_temporal_data.sql ecosystem-mcp-postgres:/tmp/
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -f /tmp/backfill_temporal_data.sql
```

### Step 4: Generate Content Hashes for Existing Documents (If Content Available)

**Note:** This step requires the actual document content. If you have content in the database or accessible:

```python
# Create a Python script to backfill content hashes
cat > /tmp/backfill_content_hashes.py << 'EOF'
#!/usr/bin/env python3
"""
Backfill content hashes for existing documents.

This script:
1. Reads existing documents
2. Calculates SHA256 hashes
3. Stores in document_content_store
4. Updates document_versions with content_hash
"""

import asyncio
import hashlib
import asyncpg
from pathlib import Path

async def backfill_content_hashes():
    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='ecosystem_mcp'
    )
    
    try:
        # Get all documents with content
        documents = await conn.fetch("""
            SELECT d.id, d.file_path, d.content, v.id as version_id
            FROM documents d
            JOIN document_versions v ON v.document_id = d.id
            WHERE d.content IS NOT NULL
              AND v.content_hash IS NULL
        """)
        
        print(f"Found {len(documents)} documents to process")
        
        for i, doc in enumerate(documents, 1):
            # Calculate hash
            content = doc['content']
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            content_hash = hashlib.sha256(content).hexdigest()
            content_size = len(content)
            
            # Check if content already stored
            existing = await conn.fetchval(
                "SELECT content_hash FROM document_content_store WHERE content_hash = $1",
                content_hash
            )
            
            if not existing:
                # Store content
                await conn.execute("""
                    INSERT INTO document_content_store 
                    (content_hash, content, mime_type, content_size, reference_count)
                    VALUES ($1, $2, 'text/plain', $3, 1)
                    ON CONFLICT (content_hash) DO UPDATE
                    SET reference_count = document_content_store.reference_count + 1
                """, content_hash, content, content_size)
            else:
                # Increment reference
                await conn.execute("""
                    UPDATE document_content_store
                    SET reference_count = reference_count + 1
                    WHERE content_hash = $1
                """, content_hash)
            
            # Update version
            await conn.execute("""
                UPDATE document_versions
                SET content_hash = $1, content_size = $2
                WHERE id = $3
            """, content_hash, content_size, doc['version_id'])
            
            if i % 100 == 0:
                print(f"Processed {i}/{len(documents)} documents...")
        
        print(f"✅ Completed! Processed {len(documents)} documents")
        
        # Show stats
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(DISTINCT content_hash) as unique_content,
                COUNT(*) as total_versions,
                SUM(content_size) as total_size,
                SUM(reference_count * content_size) as size_without_dedup
            FROM document_content_store
        """)
        
        if stats:
            space_saved = stats['size_without_dedup'] - stats['total_size']
            dedup_ratio = (space_saved / stats['size_without_dedup'] * 100) if stats['size_without_dedup'] > 0 else 0
            
            print(f"\n📊 Deduplication Stats:")
            print(f"  Unique content items: {stats['unique_content']}")
            print(f"  Total versions: {stats['total_versions']}")
            print(f"  Space saved: {space_saved / 1024 / 1024:.1f} MB")
            print(f"  Deduplication ratio: {dedup_ratio:.1f}%")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(backfill_content_hashes())
EOF

# Run backfill (if you have documents with content)
python3 /tmp/backfill_content_hashes.py
```

### Step 5: Restart Services

```bash
# Restart API service to load new code
docker-compose -f docker-compose-mcp-ecosystem.yml restart ecosystem-mcp-service

# Restart dashboard to load new UI
docker-compose -f docker-compose-mcp-ecosystem.yml restart ecosystem-mcp-dashboard

# Wait for services to be ready
sleep 10

# Check services are healthy
docker-compose -f docker-compose-mcp-ecosystem.yml ps
```

### Step 6: Verify Everything Works

```bash
# Test API health
curl -s http://localhost:8000/health | jq .

# Test deduplication stats endpoint
curl -s http://localhost:8000/api/v1/versioning/deduplication-stats | jq .

# Test activity summary endpoint
curl -s http://localhost:8000/api/v1/versioning/activity-summary | jq .

# Check OpenAPI docs
open http://localhost:8000/docs

# Check dashboard
open http://localhost:8501
```

---

## 🔍 Post-Migration Verification

### Verify Database State

```sql
-- Connect to database
docker-compose -f docker-compose-mcp-ecosystem.yml exec ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp

-- Check tables exist
\dt document*

-- Should show:
-- document_content_store
-- document_timeline
-- document_versions (existing, now enhanced)
-- documents (existing)

-- Check new columns in document_versions
\d document_versions

-- Should include new columns:
-- content_hash, content_size, modified_at, timeline_position, etc.

-- Check functions
\df get_*

-- Should show:
-- get_all_documents_as_of
-- get_document_timeline
-- get_next_timeline_position

-- Check views
\dv

-- Should show:
-- latest_document_versions
-- content_deduplication_stats
-- timeline_activity_summary

-- Query deduplication stats
SELECT * FROM content_deduplication_stats;

-- Query latest versions
SELECT COUNT(*) FROM latest_document_versions;

-- Exit
\q
```

### Verify API Endpoints

```bash
# Test all new endpoints
endpoints=(
  "/api/v1/versioning/deduplication-stats"
  "/api/v1/versioning/activity-summary"
  "/health"
  "/api/v1/admin/status"
)

for endpoint in "${endpoints[@]}"; do
  echo "Testing $endpoint..."
  curl -s "http://localhost:8000$endpoint" | jq -C . | head -20
  echo ""
done
```

### Verify Dashboard UI

1. Open dashboard: http://localhost:8501
2. Check sidebar navigation includes: `📈 Timeline Viewer`
3. Click `📈 Timeline Viewer`
4. Verify 4 tabs appear:
   - 📋 Document Timeline
   - 🕰️ As Of Date Query
   - 📊 Changes Between Dates
   - 📈 Activity Summary
5. Try each tab to ensure no errors

---

## 🎯 What If You Have No Existing Data?

If this is a **fresh install** with no existing documents:

```bash
# 1. Just run the migration
docker cp services/ecosystem-mcp/migrations/add_temporal_content_versioning.sql \
  ecosystem-mcp-postgres:/tmp/
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp -f /tmp/add_temporal_content_versioning.sql

# 2. Restart services
docker-compose -f docker-compose-mcp-ecosystem.yml restart ecosystem-mcp-service
docker-compose -f docker-compose-mcp-ecosystem.yml restart ecosystem-mcp-dashboard

# 3. Start ingesting documents - they'll use the new system automatically!
```

---

## 🎯 What If You Have Existing Data?

If you have **existing documents** in the database:

**Option A: Keep existing data as-is (Recommended)**
- Run Step 1-2 (migration)
- Run Step 3 (backfill metadata)
- Skip Step 4 (content hashes) - will be generated on next update
- Existing versions will work, but won't have full deduplication until re-ingested

**Option B: Full backfill with content hashing**
- Run all steps including Step 4
- Requires document content to be accessible
- Enables immediate deduplication benefits

**Option C: Start fresh (if safe to do so)**
- Backup existing data
- Run migration
- Re-ingest all documents
- New system will handle everything automatically

---

## ⚠️ Troubleshooting

### Issue: Migration fails with "relation already exists"

**Cause:** Migration was partially run before.

**Solution:**
```sql
-- Check what exists
\dt document_content_store
\dt document_timeline

-- If tables exist, migration is done
-- Just verify columns are present
\d document_versions
```

### Issue: Functions don't exist after migration

**Cause:** Transaction might have rolled back.

**Solution:**
```bash
# Re-run just the function creation part
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp << 'EOF'
-- Paste function definitions from migration SQL
EOF
```

### Issue: API returns 500 errors for versioning endpoints

**Cause:** Services not restarted, or database connection issues.

**Solution:**
```bash
# Check service logs
docker logs ecosystem-mcp-service --tail 100

# Restart services
docker-compose -f docker-compose-mcp-ecosystem.yml restart ecosystem-mcp-service

# Check database connection
docker-compose -f docker-compose-mcp-ecosystem.yml exec ecosystem-mcp-service \
  python -c "from src.storage import get_database; import asyncio; asyncio.run(get_database().check_connection())"
```

### Issue: Dashboard doesn't show Timeline Viewer page

**Cause:** Dashboard not restarted, or file not copied into container.

**Solution:**
```bash
# Copy new files into dashboard container
docker cp services/ecosystem-mcp-dashboard/dashboard_views/timeline_viewer.py \
  ecosystem-mcp-dashboard:/app/dashboard_views/

docker cp services/ecosystem-mcp-dashboard/app.py \
  ecosystem-mcp-dashboard:/app/

# Restart dashboard
docker-compose -f docker-compose-mcp-ecosystem.yml restart ecosystem-mcp-dashboard

# Clear browser cache and refresh
```

---

## 🔄 Rollback Plan (If Needed)

If something goes wrong and you need to rollback:

```bash
# 1. Stop services
docker-compose -f docker-compose-mcp-ecosystem.yml stop ecosystem-mcp-service ecosystem-mcp-dashboard

# 2. Restore database from backup
docker-compose -f docker-compose-mcp-ecosystem.yml exec -T ecosystem-mcp-postgres \
  psql -U postgres -d ecosystem_mcp < backups/ecosystem_mcp_backup_YYYYMMDD_HHMMSS.sql

# 3. Start services
docker-compose -f docker-compose-mcp-ecosystem.yml start ecosystem-mcp-service ecosystem-mcp-dashboard
```

**Note:** This will lose any documents ingested after the backup!

---

## ✅ Migration Checklist

- [ ] ✅ Database backup created
- [ ] ✅ Migration SQL executed successfully
- [ ] ✅ New tables verified (`document_content_store`, `document_timeline`)
- [ ] ✅ New columns verified in `document_versions`
- [ ] ✅ Functions created (`get_all_documents_as_of`, etc.)
- [ ] ✅ Views created (`latest_document_versions`, etc.)
- [ ] ✅ Existing data backfilled (if applicable)
- [ ] ✅ Services restarted
- [ ] ✅ API endpoints tested
- [ ] ✅ Dashboard UI verified
- [ ] ✅ Ingestion tested with new system

---

## 📞 Need Help?

If you encounter issues:

1. Check logs:
   ```bash
   docker logs ecosystem-mcp-service
   docker logs ecosystem-mcp-dashboard
   docker logs ecosystem-mcp-postgres
   ```

2. Verify database state:
   ```bash
   docker-compose -f docker-compose-mcp-ecosystem.yml exec ecosystem-mcp-postgres \
     psql -U postgres -d ecosystem_mcp -c "\dt"
   ```

3. Test connectivity:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8501
   ```

---

**Migration Guide Version:** 1.0.0  
**Last Updated:** October 15, 2025  
**Status:** ✅ Complete and Tested

