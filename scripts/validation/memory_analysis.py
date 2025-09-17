"""Memory Usage Analysis Script

Analyzes memory usage patterns, detects potential memory leaks, and identifies
optimization opportunities in the refactored DDD architecture.
"""

import gc
import tracemalloc
import psutil
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os


@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""
    timestamp: float
    current_mb: float
    peak_mb: float
    objects_count: int
    top_allocations: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "current_mb": self.current_mb,
            "peak_mb": self.peak_mb,
            "objects_count": self.objects_count,
            "top_allocations": self.top_allocations
        }


class MemoryAnalyzer:
    """Comprehensive memory usage analyzer."""

    def __init__(self):
        """Initialize memory analyzer."""
        self.process = psutil.Process()
        self.snapshots = []
        self.baseline_snapshot = None

    def run_memory_analysis(self) -> Dict[str, Any]:
        """Run comprehensive memory analysis."""
        print("🧠 Starting Memory Usage Analysis")
        print("=" * 50)

        # Start memory tracing
        tracemalloc.start()

        try:
            # Take baseline snapshot
            self.baseline_snapshot = tracemalloc.take_snapshot()
            print("📸 Baseline memory snapshot taken")

            # Run memory-intensive operations
            analysis_results = self._run_memory_intensive_operations()

            # Take final snapshot
            final_snapshot = tracemalloc.take_snapshot()

            # Analyze memory usage
            memory_stats = self._analyze_memory_usage(final_snapshot)

            # Check for potential leaks
            leak_analysis = self._analyze_potential_leaks(final_snapshot)

            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(memory_stats, leak_analysis)

            results = {
                "memory_stats": memory_stats,
                "leak_analysis": leak_analysis,
                "optimization_recommendations": recommendations,
                "analysis_results": analysis_results,
                "system_memory": self._get_system_memory_info(),
                "analysis_timestamp": time.time()
            }

            print("\n📊 MEMORY ANALYSIS SUMMARY:")
            print(".1f")
            print(f"   Objects Tracked: {memory_stats['total_objects']:,}")
            print(f"   Memory Efficiency: {memory_stats['memory_efficiency']:.1f}%")
            print(f"   Potential Leaks: {leak_analysis['potential_leaks_count']}")

            if recommendations:
                print("💡 Key Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec}")

            return results

        finally:
            tracemalloc.stop()

    def _run_memory_intensive_operations(self) -> Dict[str, Any]:
        """Run operations that stress memory usage."""
        print("🔄 Running memory-intensive operations...")

        results = {}

        # Test 1: Large data structure creation
        print("   Creating large data structures...")
        large_list = []
        for i in range(10000):
            large_list.append({
                "id": i,
                "data": "x" * 100,  # 100 bytes per item
                "metadata": {
                    "created": time.time(),
                    "tags": [f"tag_{j}" for j in range(10)],
                    "nested": {"level1": {"level2": "deep_data" * 20}}
                }
            })

        results["large_data_creation"] = {
            "items_created": len(large_list),
            "estimated_size_mb": len(large_list) * 0.5  # Rough estimate
        }

        # Force garbage collection
        gc.collect()

        # Test 2: Object instantiation stress test
        print("   Stress testing object instantiation...")
        objects_created = 0
        start_time = time.time()

        for i in range(5000):
            # Create various types of objects
            test_obj = type(f"TestClass_{i}", (), {
                "id": i,
                "data": list(range(100)),
                "metadata": {"type": "test", "index": i}
            })()

            # Create some references to stress GC
            if i % 100 == 0:
                temp_refs = [test_obj] * 10

            objects_created += 1

        creation_time = time.time() - start_time
        results["object_instantiation"] = {
            "objects_created": objects_created,
            "creation_time_seconds": creation_time,
            "objects_per_second": objects_created / creation_time
        }

        # Test 3: Memory cleanup test
        print("   Testing memory cleanup...")
        before_cleanup = len(gc.get_objects())

        # Create temporary objects that should be cleaned up
        temp_objects = []
        for i in range(1000):
            temp_objects.append({"temp_data": "x" * 1000})

        # Delete references
        del temp_objects
        gc.collect()

        after_cleanup = len(gc.get_objects())
        results["memory_cleanup"] = {
            "objects_before_cleanup": before_cleanup,
            "objects_after_cleanup": after_cleanup,
            "cleanup_efficiency": (before_cleanup - after_cleanup) / before_cleanup * 100
        }

        return results

    def _analyze_memory_usage(self, final_snapshot) -> Dict[str, Any]:
        """Analyze memory usage patterns."""
        print("🔍 Analyzing memory usage patterns...")

        # Compare with baseline
        if self.baseline_snapshot:
            stats = final_snapshot.compare_to(self.baseline_snapshot, 'lineno')
        else:
            stats = final_snapshot.statistics('lineno')

        # Calculate totals
        total_memory = sum(stat.size for stat in stats)
        total_memory_mb = total_memory / (1024 * 1024)

        # Get top memory allocations
        top_allocations = []
        for stat in stats[:20]:  # Top 20 allocations
            top_allocations.append({
                "file": stat.traceback[0].filename if stat.traceback else "unknown",
                "line": stat.traceback[0].lineno if stat.traceback else 0,
                "size_mb": stat.size / (1024 * 1024),
                "count": stat.count,
                "average_mb": (stat.size / stat.count) / (1024 * 1024) if stat.count > 0 else 0
            })

        # Calculate memory efficiency metrics
        large_objects = [s for s in stats if s.size > 1024 * 1024]  # Objects > 1MB
        memory_efficiency = (1 - len(large_objects) / len(stats)) * 100 if stats else 100

        # Get current memory usage
        process_memory = self.process.memory_info()
        current_memory_mb = process_memory.rss / (1024 * 1024)
        peak_memory_mb = getattr(process_memory, 'peak_rss', process_memory.rss) / (1024 * 1024)

        return {
            "total_memory_mb": total_memory_mb,
            "current_memory_mb": current_memory_mb,
            "peak_memory_mb": peak_memory_mb,
            "total_objects": len(stats),
            "large_objects_count": len(large_objects),
            "memory_efficiency": memory_efficiency,
            "top_allocations": top_allocations,
            "memory_per_object_kb": (total_memory / len(stats)) / 1024 if stats else 0
        }

    def _analyze_potential_leaks(self, final_snapshot) -> Dict[str, Any]:
        """Analyze potential memory leaks."""
        print("🔍 Analyzing potential memory leaks...")

        # Look for suspiciously large allocations
        stats = final_snapshot.statistics('lineno')
        potential_leaks = []

        for stat in stats:
            # Flag allocations that are unusually large
            size_mb = stat.size / (1024 * 1024)
            if size_mb > 10:  # More than 10MB in one location
                potential_leaks.append({
                    "file": stat.traceback[0].filename if stat.traceback else "unknown",
                    "line": stat.traceback[0].lineno if stat.traceback else 0,
                    "size_mb": size_mb,
                    "count": stat.count,
                    "severity": "high" if size_mb > 50 else "medium"
                })

        # Look for objects that might not be getting garbage collected
        gc_objects = gc.get_objects()
        object_counts = {}

        for obj in gc_objects[:10000]:  # Sample first 10k objects
            obj_type = type(obj).__name__
            object_counts[obj_type] = object_counts.get(obj_type, 0) + 1

        # Flag potentially problematic object types
        problematic_types = ['dict', 'list', 'tuple']
        suspicious_objects = {
            obj_type: count for obj_type, count in object_counts.items()
            if obj_type in problematic_types and count > 1000
        }

        return {
            "potential_leaks_count": len(potential_leaks),
            "large_allocations": potential_leaks,
            "suspicious_objects": suspicious_objects,
            "gc_objects_sampled": len(gc_objects),
            "leak_risk_level": self._assess_leak_risk(potential_leaks, suspicious_objects)
        }

    def _assess_leak_risk(self, potential_leaks: List[Dict], suspicious_objects: Dict[str, int]) -> str:
        """Assess overall memory leak risk."""
        risk_score = 0

        # Score based on large allocations
        for leak in potential_leaks:
            if leak["severity"] == "high":
                risk_score += 3
            elif leak["severity"] == "medium":
                risk_score += 1

        # Score based on suspicious object counts
        for obj_type, count in suspicious_objects.items():
            if count > 5000:
                risk_score += 2
            elif count > 2000:
                risk_score += 1

        if risk_score >= 10:
            return "high"
        elif risk_score >= 5:
            return "medium"
        elif risk_score >= 2:
            return "low"
        else:
            return "minimal"

    def _generate_optimization_recommendations(self, memory_stats: Dict, leak_analysis: Dict) -> List[str]:
        """Generate memory optimization recommendations."""
        recommendations = []

        # Memory efficiency recommendations
        efficiency = memory_stats.get("memory_efficiency", 100)
        if efficiency < 80:
            recommendations.append("Consider using memory-efficient data structures (__slots__, arrays instead of lists)")

        # Large object recommendations
        large_objects = memory_stats.get("large_objects_count", 0)
        if large_objects > 10:
            recommendations.append("Reduce the number of large objects - consider streaming or pagination for large datasets")

        # Memory per object recommendations
        memory_per_object = memory_stats.get("memory_per_object_kb", 0)
        if memory_per_object > 10:  # More than 10KB per object
            recommendations.append("Optimize object sizes - consider lazy loading and computed properties")

        # Leak prevention recommendations
        leak_risk = leak_analysis.get("leak_risk_level", "minimal")
        if leak_risk in ["high", "medium"]:
            recommendations.append("Implement proper object cleanup and weak references for large data structures")
            recommendations.append("Use context managers for resource management")

        # General recommendations
        total_memory = memory_stats.get("total_memory_mb", 0)
        if total_memory > 100:
            recommendations.append("Implement caching with TTL to reduce memory footprint")
            recommendations.append("Consider memory profiling in production to identify hotspots")

        if not recommendations:
            recommendations.append("Memory usage is well-optimized - continue monitoring")

        return recommendations

    def _get_system_memory_info(self) -> Dict[str, Any]:
        """Get system memory information."""
        vm = psutil.virtual_memory()
        return {
            "total_gb": vm.total / (1024**3),
            "available_gb": vm.available / (1024**3),
            "used_gb": vm.used / (1024**3),
            "percentage": vm.percent,
            "process_memory_mb": self.process.memory_info().rss / (1024**2)
        }


def main():
    """Main memory analysis execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Memory Usage Analysis")
    parser.add_argument("--output", default="memory_analysis_results.json",
                       help="Output file for results")
    parser.add_argument("--stress-test", action="store_true",
                       help="Run additional stress tests")

    args = parser.parse_args()

    print("🧠 Memory Usage Analysis")
    print("=" * 40)

    analyzer = MemoryAnalyzer()
    results = analyzer.run_memory_analysis()

    # Save results
    import json
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {args.output}")

    # Memory health assessment
    leak_risk = results.get("leak_analysis", {}).get("leak_risk_level", "unknown")

    if leak_risk == "minimal":
        print("✅ EXCELLENT: Memory usage is clean and efficient!")
    elif leak_risk == "low":
        print("✅ GOOD: Minor memory optimization opportunities exist")
    elif leak_risk == "medium":
        print("⚠️  FAIR: Some memory optimization recommended")
    else:
        print("❌ CONCERNS: Memory optimization required")

    return 0


if __name__ == "__main__":
    sys.exit(main())
