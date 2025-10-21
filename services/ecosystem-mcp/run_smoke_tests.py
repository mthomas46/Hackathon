#!/usr/bin/env python3
"""
Smoke Test Runner

Runs functional smoke tests against our own codebase to validate
all 4 phases of the system.

Usage:
    python run_smoke_tests.py [--quick] [--save-output]

Options:
    --quick         Run only fast tests (skip slow integration tests)
    --save-output   Save generated documentation to output directory
    --verbose       Show detailed output
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


async def run_phase1_smoke_test():
    """Run Phase 1 (Discovery) smoke tests."""
    print_header("Phase 1: Discovery Engine - Smoke Tests")
    
    from src.services.discovery.repository_scanner import RepositoryScanner
    from src.services.discovery.file_classifier import FileClassifier
    from src.services.discovery.processing_planner import ProcessingPlanner
    
    test_paths = [
        "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp",
        "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard",
        "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-embedding"
    ]
    
    results = []
    
    for path in test_paths:
        service_name = Path(path).name
        print(f"\n📂 Testing: {service_name}")
        
        try:
            # Test scanning
            scanner = RepositoryScanner()
            inventory = await scanner.scan(path)
            print_success(f"Scanned {len(inventory['files'])} files")
            
            # Test classification
            classifier = FileClassifier()
            sample_files = inventory['files'][:10]
            classifications = []
            for file_info in sample_files:
                result = await classifier.classify(file_info)
                classifications.append(result)
            print_success(f"Classified {len(classifications)} files")
            
            # Test planning
            planner = ProcessingPlanner()
            plan = await planner.create_plan(path, inventory, classifications)
            print_success(f"Created plan with {len(plan['sub_jobs'])} sub-jobs")
            
            results.append({
                'service': service_name,
                'phase': 'discovery',
                'status': 'passed',
                'files': len(inventory['files']),
                'sub_jobs': len(plan['sub_jobs'])
            })
            
        except Exception as e:
            print_error(f"Failed: {e}")
            results.append({
                'service': service_name,
                'phase': 'discovery',
                'status': 'failed',
                'error': str(e)
            })
    
    return results


async def run_phase3_smoke_test():
    """Run Phase 3 (Analysis) smoke tests."""
    print_header("Phase 3: Multi-File Analysis - Smoke Tests")
    
    from src.services.analysis.stack_detector import TechnologyStackDetector
    from src.services.analysis.architecture_detector import ArchitectureDetector
    from src.services.analysis.analysis_engine import AnalysisEngine
    from src.services.discovery.repository_scanner import RepositoryScanner
    
    test_path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"
    service_name = Path(test_path).name
    
    print(f"\n🔍 Testing: {service_name}")
    
    results = []
    
    try:
        # Scan first
        scanner = RepositoryScanner()
        inventory = await scanner.scan(test_path)
        
        # Test stack detection
        stack_detector = TechnologyStackDetector()
        stack = await stack_detector.detect(test_path, inventory)
        print_success(f"Detected {len(stack.languages)} languages")
        print_success(f"Detected {len(stack.frameworks)} frameworks")
        
        # Test architecture detection
        arch_detector = ArchitectureDetector()
        architecture = await arch_detector.detect(test_path, inventory)
        print_success(f"Pattern: {architecture.primary_pattern.name}")
        print_success(f"Confidence: {architecture.primary_pattern.confidence:.1%}")
        
        # Test full analysis
        analysis_engine = AnalysisEngine()
        report = await analysis_engine.analyze_repository(test_path)
        print_success(f"Complete analysis generated")
        print_success(f"Modularity score: {report.modularity_score:.2f}")
        
        results.append({
            'service': service_name,
            'phase': 'analysis',
            'status': 'passed',
            'languages': len(stack.languages),
            'frameworks': len(stack.frameworks),
            'pattern': architecture.primary_pattern.name,
            'modularity': report.modularity_score
        })
        
    except Exception as e:
        print_error(f"Failed: {e}")
        results.append({
            'service': service_name,
            'phase': 'analysis',
            'status': 'failed',
            'error': str(e)
        })
    
    return results


async def run_phase4_smoke_test(save_output=False):
    """Run Phase 4 (Documentation) smoke tests."""
    print_header("Phase 4: Documentation Generation - Smoke Tests")
    
    from src.services.documentation import get_doc_orchestrator, DocConfig
    from src.services.analysis.analysis_engine import AnalysisEngine
    
    # Test on smallest service for speed
    test_path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-embedding"
    service_name = Path(test_path).name
    
    print(f"\n📚 Testing: {service_name}")
    
    results = []
    
    try:
        # Run analysis first
        print_info("Running analysis...")
        analysis_engine = AnalysisEngine()
        analysis_report = await analysis_engine.analyze_repository(test_path)
        print_success("Analysis complete")
        
        # Generate documentation
        print_info("Generating documentation...")
        orchestrator = get_doc_orchestrator()
        config = DocConfig(min_quality_score=0.5)
        
        doc_set = await orchestrator.generate_documentation(
            plan_id="smoke_test",
            analysis_report=analysis_report,
            config=config
        )
        
        print_success(f"Generated {doc_set.total_artifacts} artifacts")
        print_success(f"Total words: {doc_set.total_words:,}")
        print_success(f"Quality score: {doc_set.overall_quality_score:.2f}/1.0")
        
        # Print pass breakdown
        for idx, pass_result in enumerate(doc_set.pass_results, 1):
            print(f"   Pass {idx} ({pass_result.pass_type.value}): "
                  f"{len(pass_result.artifacts)} artifacts, "
                  f"{pass_result.duration_seconds:.1f}s")
        
        # Save output if requested
        if save_output:
            output_dir = Path("smoke_test_output") / datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for pass_result in doc_set.pass_results:
                for artifact in pass_result.artifacts:
                    filename = f"{artifact['title'].lower().replace(' ', '_').replace(':', '')}.md"
                    filepath = output_dir / filename
                    
                    with open(filepath, 'w') as f:
                        f.write(artifact['content'])
            
            print_success(f"Saved output to: {output_dir}")
        
        results.append({
            'service': service_name,
            'phase': 'documentation',
            'status': 'passed',
            'artifacts': doc_set.total_artifacts,
            'words': doc_set.total_words,
            'quality': doc_set.overall_quality_score,
            'passes': len(doc_set.pass_results)
        })
        
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        results.append({
            'service': service_name,
            'phase': 'documentation',
            'status': 'failed',
            'error': str(e)
        })
    
    return results


async def run_integration_smoke_test():
    """Run complete pipeline integration test."""
    print_header("Complete Pipeline Integration - Smoke Test")
    
    from src.services.discovery.discovery_engine import DiscoveryEngine
    from src.services.analysis.analysis_engine import AnalysisEngine
    from src.services.documentation import get_doc_orchestrator, DocConfig
    
    # Test on embedding service (smallest)
    test_path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-embedding"
    service_name = Path(test_path).name
    
    print(f"\n🚀 Complete pipeline test: {service_name}\n")
    
    results = {
        'service': service_name,
        'phase': 'integration',
        'status': 'passed',
        'steps': []
    }
    
    try:
        # Step 1: Discovery
        print_info("Step 1: Discovery")
        discovery_engine = DiscoveryEngine()
        discovery_result = await discovery_engine.discover(test_path)
        print_success(f"Files: {discovery_result['total_files']}, "
                     f"Sub-jobs: {len(discovery_result['plan']['sub_jobs'])}")
        results['steps'].append({'discovery': 'passed'})
        
        # Step 2: Analysis
        print_info("Step 2: Analysis")
        analysis_engine = AnalysisEngine()
        analysis_report = await analysis_engine.analyze_repository(test_path)
        print_success(f"Pattern: {analysis_report.architecture.primary_pattern.name}, "
                     f"Modularity: {analysis_report.modularity_score:.2f}")
        results['steps'].append({'analysis': 'passed'})
        
        # Step 3: Documentation
        print_info("Step 3: Documentation")
        orchestrator = get_doc_orchestrator()
        config = DocConfig(min_quality_score=0.5)
        doc_set = await orchestrator.generate_documentation(
            plan_id="integration_test",
            analysis_report=analysis_report,
            config=config
        )
        print_success(f"Artifacts: {doc_set.total_artifacts}, "
                     f"Quality: {doc_set.overall_quality_score:.2f}")
        results['steps'].append({'documentation': 'passed'})
        
        print_success("\n✅ Complete pipeline test PASSED!")
        
    except Exception as e:
        print_error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        results['status'] = 'failed'
        results['error'] = str(e)
    
    return results


async def main():
    """Main smoke test runner."""
    parser = argparse.ArgumentParser(description="Run smoke tests")
    parser.add_argument('--quick', action='store_true', 
                       help="Run only fast tests")
    parser.add_argument('--save-output', action='store_true',
                       help="Save generated documentation")
    parser.add_argument('--verbose', action='store_true',
                       help="Show detailed output")
    args = parser.parse_args()
    
    print_header("🔥 Smoke Test Suite - All 4 Phases")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_results = []
    
    # Run tests
    try:
        # Phase 1
        phase1_results = await run_phase1_smoke_test()
        all_results.extend(phase1_results)
        
        # Phase 3
        phase3_results = await run_phase3_smoke_test()
        all_results.extend(phase3_results)
        
        # Phase 4
        phase4_results = await run_phase4_smoke_test(save_output=args.save_output)
        all_results.extend(phase4_results)
        
        # Integration (unless quick mode)
        if not args.quick:
            integration_results = await run_integration_smoke_test()
            all_results.append(integration_results)
    
    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        return 1
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for r in all_results if r.get('status') == 'passed')
    failed = sum(1 for r in all_results if r.get('status') == 'failed')
    total = len(all_results)
    
    print(f"\nTotal Tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    
    # Save results
    results_file = Path("smoke_test_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': all_results,
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed
            }
        }, f, indent=2)
    
    print(f"\n📊 Results saved to: {results_file}")
    
    # Exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

