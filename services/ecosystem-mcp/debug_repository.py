#!/usr/bin/env python3
"""
Debug script to test repository creation logic.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.db_models import IngestionJobModel
from src.storage import get_database
from src.storage.repositories import IngestionJobRepository


async def test_model_creation():
    """Test 1: Can we create the model object?"""
    print("\n" + "="*60)
    print("TEST 1: Creating IngestionJobModel object")
    print("="*60)
    
    try:
        job = IngestionJobModel(
            mode="test",
            status="queued",
            repo_path="/test/path",
            total_documents=0,
            processed_documents=0,
            failed_documents=0,
            embeddings_generated=0,
            total_cost_usd=0.0
        )
        print(f"✅ Model created successfully")
        print(f"   - mode: {job.mode}")
        print(f"   - status: {job.status}")
        print(f"   - repo_path: {job.repo_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create model: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_repository_init():
    """Test 2: Can we initialize the repository?"""
    print("\n" + "="*60)
    print("TEST 2: Initializing IngestionJobRepository")
    print("="*60)
    
    try:
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            print(f"✅ Repository initialized successfully")
            print(f"   - model_class: {repo.model_class}")
            print(f"   - session: {type(repo.session)}")
            return True
    except Exception as e:
        print(f"❌ Failed to initialize repository: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_base_create():
    """Test 3: Can we call base repository create()?"""
    print("\n" + "="*60)
    print("TEST 3: Testing BaseRepository.create() with model object")
    print("="*60)
    
    try:
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Create model object
            job = IngestionJobModel(
                mode="test",
                status="queued",
                repo_path="/test/path",
                total_documents=0,
                processed_documents=0,
                failed_documents=0,
                embeddings_generated=0,
                total_cost_usd=0.0
            )
            
            # Try to create
            print("   Calling repo.create(job)...")
            created_job = await repo.create(job)
            await session.commit()
            
            print(f"✅ BaseRepository.create() successful")
            print(f"   - id: {created_job.id}")
            print(f"   - mode: {created_job.mode}")
            return True
    except Exception as e:
        print(f"❌ Failed BaseRepository.create(): {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_create_job_method():
    """Test 4: Can we call create_job() method?"""
    print("\n" + "="*60)
    print("TEST 4: Testing IngestionJobRepository.create_job()")
    print("="*60)
    
    try:
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            print("   Calling repo.create_job(mode='test', status='queued', repo_path='/test/path')...")
            job = await repo.create_job(
                mode="test",
                status="queued",
                repo_path="/test/path"
            )
            await session.commit()
            
            print(f"✅ create_job() successful")
            print(f"   - id: {job.id}")
            print(f"   - mode: {job.mode}")
            print(f"   - status: {job.status}")
            return True
    except Exception as e:
        print(f"❌ Failed create_job(): {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("REPOSITORY DEBUG TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Model creation
    results.append(("Model Creation", await test_model_creation()))
    
    # Test 2: Repository init
    results.append(("Repository Init", await test_repository_init()))
    
    # Test 3: Base create
    results.append(("Base Create", await test_base_create()))
    
    # Test 4: create_job method
    results.append(("create_job Method", await test_create_job_method()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n⚠️  Some tests failed - check output above for details")
        return 1
    else:
        print("\n🎉 All tests passed!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

