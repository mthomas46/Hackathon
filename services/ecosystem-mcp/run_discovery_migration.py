#!/usr/bin/env python3
"""
Run discovery migration script.

Creates tables for processing plans, sub-jobs, and file classifications.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from storage import get_database
from storage.migrations import add_discovery_and_sub_jobs


async def main():
    """Run migration."""
    print("=" * 80)
    print("🔄 RUNNING DISCOVERY MIGRATION")
    print("=" * 80)
    print()
    
    try:
        # Get database
        db = get_database()
        
        print("📊 Applying migration...")
        async with db.session() as session:
            await add_discovery_and_sub_jobs.upgrade(session)
        
        print()
        print("=" * 80)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 80)
        print()
        print("Created tables:")
        print("  • processing_plans")
        print("  • sub_jobs")
        print("  • file_classifications")
        print()
        print("Created indexes:")
        print("  • Performance indexes on all tables")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ MIGRATION FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

