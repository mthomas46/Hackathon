#!/usr/bin/env python3
"""
Test script for demo endpoints.

Tests the /demos and /run-demo endpoints to ensure they work correctly.
"""

import asyncio
from application.demos.demo_service import DemoService


async def test_list_demos():
    """Test listing available demos."""
    print("=" * 70)
    print("TEST 1: List Available Demos")
    print("=" * 70)
    
    demo_service = DemoService()
    demos = demo_service.list_demos()
    
    print(f"\nTotal Demos Available: {len(demos)}")
    print("\nDemo List:")
    for idx, demo in enumerate(demos, 1):
        print(f"\n  {idx}. {demo['name']}")
        print(f"     ID: {demo['id']}")
        print(f"     Type: {demo['type']}")
        print(f"     Duration: {demo['duration']}")
        print(f"     Requires Dependencies: {demo['requires_dependencies']}")
        print(f"     Description: {demo['description']}")
    
    print("\n✅ List demos test passed!")
    return True


async def test_self_contained_demos():
    """Test self-contained demos (no dependencies required)."""
    print("\n" + "=" * 70)
    print("TEST 2: Self-Contained Demos")
    print("=" * 70)
    
    demo_service = DemoService()
    
    # Test self-contained demos
    self_contained_demos = [
        "scoring-algorithm",
        "expert-matching",
        "sme-identification",
        "performance-benchmark"
    ]
    
    results = []
    for demo_id in self_contained_demos:
        print(f"\n--- Testing Demo: {demo_id} ---")
        try:
            result = await demo_service.run_demo(demo_id)
            print(f"✅ Demo '{demo_id}' executed successfully")
            print(f"   Execution Time: {result['execution_time_seconds']:.3f}s")
            print(f"   Status: {result['status']}")
            
            # Show sample data
            if 'data' in result and 'results' in result['data']:
                num_results = len(result['data']['results'])
                print(f"   Results: {num_results} items")
            
            results.append((demo_id, True, None))
        except Exception as e:
            print(f"❌ Demo '{demo_id}' failed: {str(e)}")
            results.append((demo_id, False, str(e)))
    
    # Summary
    print("\n" + "-" * 70)
    print("Self-Contained Demo Test Summary:")
    passed = sum(1 for _, success, _ in results if success)
    print(f"  Passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n✅ All self-contained demo tests passed!")
        return True
    else:
        print("\n⚠️ Some demos failed:")
        for demo_id, success, error in results:
            if not success:
                print(f"  - {demo_id}: {error}")
        return False


async def test_scoring_algorithm_details():
    """Test scoring algorithm demo in detail."""
    print("\n" + "=" * 70)
    print("TEST 3: Scoring Algorithm Demo (Detailed)")
    print("=" * 70)
    
    demo_service = DemoService()
    
    result = await demo_service.run_demo("scoring-algorithm")
    
    print(f"\nDemo: {result['demo_name']}")
    print(f"Execution Time: {result['execution_time_seconds']:.3f}s")
    print(f"Status: {result['status']}")
    
    data = result['data']
    print(f"\nQuery: {data['query']}")
    print(f"Candidates Scored: {data['candidates_scored']}")
    
    print("\nScoring Weights:")
    for factor, weight in data['scoring_weights'].items():
        print(f"  {factor.capitalize()}: {weight*100}%")
    
    print("\nTop 3 Matches:")
    for match in data['results']:
        print(f"\n  Rank {match['rank']}: {match['expert']['name']}")
        print(f"    Role: {match['expert']['role']}")
        print(f"    Topics: {', '.join(match['expert']['topics'])}")
        print(f"    Overall Score: {match['scores']['overall']:.3f}")
        print(f"    Match Quality: {match['match_quality']}")
        print(f"    Explanation: {match['explanation']}")
    
    print("\n✅ Scoring algorithm demo test passed!")
    return True


async def test_performance_benchmark():
    """Test performance benchmark demo."""
    print("\n" + "=" * 70)
    print("TEST 4: Performance Benchmark Demo")
    print("=" * 70)
    
    demo_service = DemoService()
    
    result = await demo_service.run_demo("performance-benchmark")
    
    print(f"\nDemo: {result['demo_name']}")
    print(f"Execution Time: {result['execution_time_seconds']:.3f}s")
    
    data = result['data']
    print(f"\nBenchmark: {data['benchmark']}")
    print(f"Algorithm: {data['algorithm']}")
    
    print("\nPerformance Results:")
    print(f"{'Dataset Size':<15} {'Duration (ms)':<15} {'Experts/sec':<15} {'Matches Found':<15}")
    print("-" * 60)
    for item in data['results']:
        print(f"{item['dataset_size']:<15} "
              f"{item['duration_ms']:<15.3f} "
              f"{item['experts_per_second']:<15.2f} "
              f"{item['matches_found']:<15}")
    
    print("\nInsights:")
    for key, value in data['insights'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\n✅ Performance benchmark test passed!")
    return True


async def test_invalid_demo():
    """Test error handling for invalid demo ID."""
    print("\n" + "=" * 70)
    print("TEST 5: Error Handling (Invalid Demo)")
    print("=" * 70)
    
    demo_service = DemoService()
    
    try:
        await demo_service.run_demo("non-existent-demo")
        print("❌ Should have raised ValueError for invalid demo ID!")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {str(e)}")
        return True


async def main():
    """Run all demo tests."""
    print("\n" + "=" * 70)
    print("EXPERT FINDER SERVICE - DEMO ENDPOINTS TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("List Demos", test_list_demos),
        ("Self-Contained Demos", test_self_contained_demos),
        ("Scoring Algorithm Details", test_scoring_algorithm_details),
        ("Performance Benchmark", test_performance_benchmark),
        ("Invalid Demo Error Handling", test_invalid_demo),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

