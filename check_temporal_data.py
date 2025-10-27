#!/usr/bin/env python3
"""
Check what temporal data actually exists in the database.
"""

import asyncio
from sqlalchemy import create_engine, text
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://ecosystem:ecosystem_password@localhost:5432/ecosystem_mcp"

async def check_temporal_data():
    """Check temporal data in database."""
    engine = create_engine(DATABASE_URL)
    
    print("=" * 80)
    print("  Checking Temporal Data in Database")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Check total documents
        result = conn.execute(text("SELECT COUNT(*) FROM documents"))
        total_docs = result.scalar()
        print(f"\n📊 Total Documents: {total_docs}")
        
        # Check documents with git_date
        result = conn.execute(text("SELECT COUNT(*) FROM documents WHERE git_date IS NOT NULL"))
        git_date_count = result.scalar()
        print(f"📅 Documents with git_date: {git_date_count}")
        
        # Check documents with git_sha
        result = conn.execute(text("SELECT COUNT(*) FROM documents WHERE git_sha IS NOT NULL"))
        git_sha_count = result.scalar()
        print(f"🔗 Documents with git_sha: {git_sha_count}")
        
        # Check documents with git_author
        result = conn.execute(text("SELECT COUNT(*) FROM documents WHERE git_author IS NOT NULL"))
        git_author_count = result.scalar()
        print(f"👤 Documents with git_author: {git_author_count}")
        
        # Check documents with updated_at
        result = conn.execute(text("SELECT COUNT(*) FROM documents WHERE updated_at IS NOT NULL"))
        updated_at_count = result.scalar()
        print(f"⏰ Documents with updated_at: {updated_at_count}")
        
        # Show sample documents with temporal data
        print(f"\n" + "=" * 80)
        print("  Sample Documents with Temporal Data")
        print("=" * 80)
        
        result = conn.execute(text("""
            SELECT 
                id,
                file_path,
                git_date,
                git_sha,
                git_author,
                updated_at,
                created_at
            FROM documents 
            WHERE git_date IS NOT NULL 
               OR updated_at IS NOT NULL
            ORDER BY COALESCE(git_date, updated_at) DESC
            LIMIT 5
        """))
        
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"\n📄 Document ID: {row[0]}")
                print(f"   File: {row[1]}")
                print(f"   git_date: {row[2]}")
                print(f"   git_sha: {row[3][:8] if row[3] else None}...")
                print(f"   git_author: {row[4]}")
                print(f"   updated_at: {row[5]}")
                print(f"   created_at: {row[6]}")
        else:
            print("\n⚠️  No documents with temporal data found!")
        
        # Check date ranges
        print(f"\n" + "=" * 80)
        print("  Temporal Date Ranges")
        print("=" * 80)
        
        # Git date range
        result = conn.execute(text("""
            SELECT 
                MIN(git_date) as earliest_git,
                MAX(git_date) as latest_git
            FROM documents 
            WHERE git_date IS NOT NULL
        """))
        row = result.fetchone()
        if row and row[0]:
            print(f"\n📅 Git Date Range:")
            print(f"   Earliest: {row[0]}")
            print(f"   Latest: {row[1]}")
        
        # Updated_at range
        result = conn.execute(text("""
            SELECT 
                MIN(updated_at) as earliest_update,
                MAX(updated_at) as latest_update
            FROM documents 
            WHERE updated_at IS NOT NULL
        """))
        row = result.fetchone()
        if row and row[0]:
            print(f"\n⏰ Updated_at Range:")
            print(f"   Earliest: {row[0]}")
            print(f"   Latest: {row[1]}")
        
        # Check what fields temporal queries might use
        print(f"\n" + "=" * 80)
        print("  Temporal Query Field Analysis")
        print("=" * 80)
        
        # Check if there are documents in the last 30 days
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM documents 
            WHERE git_date >= NOW() - INTERVAL '30 days'
               OR updated_at >= NOW() - INTERVAL '30 days'
        """))
        recent_count = result.scalar()
        print(f"\n📊 Documents from last 30 days: {recent_count}")
        
        # Check documents by week
        result = conn.execute(text("""
            SELECT 
                DATE_TRUNC('week', COALESCE(git_date, updated_at)) as week,
                COUNT(*) as count
            FROM documents 
            WHERE git_date IS NOT NULL OR updated_at IS NOT NULL
            GROUP BY week
            ORDER BY week DESC
            LIMIT 5
        """))
        rows = result.fetchall()
        if rows:
            print(f"\n📊 Documents by Week (last 5 weeks):")
            for row in rows:
                print(f"   {row[0].strftime('%Y-%m-%d')}: {row[1]} documents")
        
        print(f"\n" + "=" * 80)
        print("  Summary")
        print("=" * 80)
        
        if git_date_count > 0 or updated_at_count > 0:
            print(f"\n✅ Temporal data EXISTS!")
            print(f"   Total documents: {total_docs}")
            print(f"   With git_date: {git_date_count} ({(git_date_count/total_docs*100) if total_docs > 0 else 0:.1f}%)")
            print(f"   With updated_at: {updated_at_count} ({(updated_at_count/total_docs*100) if total_docs > 0 else 0:.1f}%)")
            print(f"\n🎯 Temporal RAG should have data to work with!")
            
            if git_date_count == 0 and updated_at_count > 0:
                print(f"\n⚠️  Note: Only updated_at available (no git_date)")
                print(f"   Temporal queries may be looking for git_date specifically")
        else:
            print(f"\n❌ No temporal data found!")
            print(f"   Need to run enriched ingestion")

if __name__ == "__main__":
    asyncio.run(check_temporal_data())
