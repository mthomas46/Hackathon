#!/usr/bin/env python3
"""
Standalone test for discovery module.

Run with: python test_discovery_standalone.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.discovery.discovery_engine import get_discovery_engine


async def main():
    """Test discovery engine."""
    print("=" * 80)
    print("🔍 TESTING DISCOVERY ENGINE")
    print("=" * 80)
    print()
    
    # Test directory (current directory)
    test_dir = Path(__file__).parent
    
    print(f"📁 Test directory: {test_dir}")
    print()
    
    # Get discovery engine
    engine = get_discovery_engine()
    
    try:
        # Run discovery
        print("🚀 Running discovery...")
        plan = await engine.discover(str(test_dir))
        
        # Get summary
        summary = engine.get_plan_summary(plan)
        
        # Print results
        print()
        print("✅ DISCOVERY COMPLETE!")
        print("=" * 80)
        print()
        print(f"📊 Repository: {summary['repo_path']}")
        print(f"📄 Total Files: {summary['total_files']}")
        print(f"💾 Total Size: {summary['total_size_mb']:.2f} MB")
        print(f"📦 Sub-Jobs: {summary['sub_jobs']}")
        print(f"⏱️  Estimated Time: {summary['estimated_time_minutes']:.1f} minutes")
        print(f"⚡ Max Parallelization: {summary['max_parallelization']}")
        print()
        
        print("📋 Sub-Job Details:")
        print("-" * 80)
        for sj in summary['sub_job_details']:
            print(f"  {sj['id']:20s} | {sj['name']:30s} | {sj['files']:5d} files | {sj['estimated_minutes']:5.1f} min")
        print()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print()
        print("❌ ERROR!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

