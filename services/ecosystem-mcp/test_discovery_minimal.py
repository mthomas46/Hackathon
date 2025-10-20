#!/usr/bin/env python3
"""
Minimal test for discovery module (no dependencies).
"""

import asyncio
import sys
from pathlib import Path

# Direct imports without going through __init__.py
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import discovery components directly
from services.discovery.repository_scanner import get_repository_scanner
from services.discovery.file_classifier import get_file_classifier
from services.discovery.processing_planner import get_processing_planner
from services.discovery.discovery_engine import DiscoveryEngine


async def main():
    """Test discovery engine."""
    print("=" * 80)
    print("🔍 TESTING DISCOVERY ENGINE (Minimal)")
    print("=" * 80)
    print()
    
    # Test directory
    test_dir = Path(__file__).parent / "src" / "services"
    
    print(f"📁 Test directory: {test_dir}")
    print()
    
    try:
        # Test scanner
        print("1️⃣  Testing RepositoryScanner...")
        scanner = get_repository_scanner()
        inventory = await scanner.scan(test_dir)
        print(f"   ✅ Scanned {inventory.total_files} files ({inventory.total_size_bytes / 1024 / 1024:.2f} MB)")
        print(f"   📊 Languages: {list(inventory.languages.keys())[:5]}")
        print()
        
        # Test classifier
        print("2️⃣  Testing FileClassifier...")
        classifier = get_file_classifier()
        classified = await classifier.classify(inventory.files)
        print(f"   ✅ Classified {len(classified)} files")
        from collections import Counter
        level_counts = Counter(cf.importance_level for cf in classified)
        for level, count in level_counts.most_common():
            print(f"   - {level}: {count} files")
        print()
        
        # Test planner
        print("3️⃣  Testing ProcessingPlanner...")
        planner = get_processing_planner()
        plan = await planner.create_plan(inventory, classified, str(test_dir))
        print(f"   ✅ Created plan with {len(plan.sub_jobs)} sub-jobs")
        print(f"   ⏱️  Estimated time: {plan.estimated_total_time_minutes:.1f} minutes")
        print(f"   ⚡ Max parallelization: {plan.max_parallelization}")
        print()
        
        # Test discovery engine
        print("4️⃣  Testing DiscoveryEngine (full integration)...")
        engine = DiscoveryEngine()
        plan2 = await engine.discover(str(test_dir))
        summary = engine.get_plan_summary(plan2)
        print(f"   ✅ Discovery complete!")
        print(f"   📊 Total files: {summary['total_files']}")
        print(f"   📦 Sub-jobs: {summary['sub_jobs']}")
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

