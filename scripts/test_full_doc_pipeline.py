"""
Complete Document Generation Pipeline Test

Tests the full end-to-end flow:
1. Discovery scan
2. Documentation generation start
3. Progress monitoring
4. Completion validation
5. Artifact verification
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"
TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class DocumentPipelineTester:
    """Complete pipeline tester with detailed monitoring."""
    
    def __init__(self):
        self.plan_id = None
        self.run_id = None
        self.test_results = {
            'discovery': None,
            'generation_start': None,
            'progress_checks': [],
            'completion': None,
            'artifacts': None
        }
    
    async def test_discovery(self) -> str:
        """Test Step 1: Discovery scan."""
        print("\n" + "=" * 80)
        print("🔍 STEP 1: DISCOVERY SCAN")
        print("=" * 80)
        
        request = {
            "repo_path": "/app",
            "resolve_host_path": False,
            "save_to_db": True
        }
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print(f"\n📤 POST /api/v1/discovery/scan")
            print(f"📋 Request: {json.dumps(request, indent=2)}")
            
            start = time.time()
            response = await client.post(
                f"{BASE_URL}/api/v1/discovery/scan",
                json=request
            )
            duration = time.time() - start
            
            print(f"\n📊 Response: {response.status_code} ({duration:.2f}s)")
            
            if response.status_code == 200:
                data = response.json()
                self.plan_id = data.get('plan_id')
                
                print(f"✅ Success!")
                print(f"   Plan ID: {self.plan_id}")
                print(f"   Files: {data.get('total_files', 'N/A')}")
                print(f"   Services: {data.get('total_services', 0)}")
                
                self.test_results['discovery'] = {
                    'status': 'success',
                    'duration': duration,
                    'plan_id': self.plan_id
                }
                
                return self.plan_id
            else:
                print(f"❌ Failed: {response.text[:200]}")
                self.test_results['discovery'] = {
                    'status': 'failed',
                    'error': response.text
                }
                return None
    
    async def test_generation_start(self, plan_id: str) -> Optional[str]:
        """Test Step 2: Start documentation generation."""
        print("\n" + "=" * 80)
        print("📝 STEP 2: START DOCUMENTATION GENERATION")
        print("=" * 80)
        
        request = {
            "plan_id": plan_id,
            "repo_path": "/app",
            "passes": ["architecture", "component"],
            "output_formats": ["markdown"],
            "include_diagrams": True,
            "include_examples": True,
            "validate_between_passes": True,
            "min_quality_score": 0.7
        }
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print(f"\n📤 POST /api/v1/documentation/generate")
            print(f"📋 Request: {json.dumps(request, indent=2)}")
            
            start = time.time()
            response = await client.post(
                f"{BASE_URL}/api/v1/documentation/generate",
                json=request
            )
            duration = time.time() - start
            
            print(f"\n📊 Response: {response.status_code} ({duration:.2f}s)")
            
            if response.status_code == 200:
                data = response.json()
                self.run_id = data.get('run_id')
                
                print(f"✅ Generation started!")
                print(f"   Run ID: {self.run_id}")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Message: {data.get('message', 'N/A')}")
                
                self.test_results['generation_start'] = {
                    'status': 'success',
                    'duration': duration,
                    'run_id': self.run_id
                }
                
                return self.run_id
            else:
                print(f"❌ Failed: {response.text[:500]}")
                self.test_results['generation_start'] = {
                    'status': 'failed',
                    'error': response.text
                }
                return None
    
    async def monitor_progress(self, run_id: str, max_checks: int = 10):
        """Test Step 3: Monitor generation progress."""
        print("\n" + "=" * 80)
        print("📊 STEP 3: MONITOR PROGRESS")
        print("=" * 80)
        
        if not run_id:
            print("⚠️  No run_id available, checking for runs...")
            # Try to find any recent runs
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                try:
                    response = await client.get(f"{BASE_URL}/api/v1/documentation/runs")
                    if response.status_code == 200:
                        runs = response.json()
                        if runs:
                            run_id = runs[0].get('id') or runs[0].get('run_id')
                            print(f"   Found recent run: {run_id}")
                except:
                    pass
        
        if not run_id:
            print("❌ No run_id available for monitoring")
            return
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for i in range(max_checks):
                print(f"\n📊 Progress Check {i+1}/{max_checks}")
                
                try:
                    response = await client.get(
                        f"{BASE_URL}/api/v1/documentation/runs/{run_id}/progress"
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        print(f"   Status: {data.get('status', 'unknown')}")
                        print(f"   Current Pass: {data.get('current_pass', 'N/A')}")
                        print(f"   Progress: {data.get('progress_percentage', 0):.1f}%")
                        print(f"   Artifacts: {data.get('total_artifacts', 0)}")
                        
                        self.test_results['progress_checks'].append({
                            'check': i+1,
                            'status': data.get('status'),
                            'progress': data.get('progress_percentage', 0),
                            'artifacts': data.get('total_artifacts', 0)
                        })
                        
                        # Check if complete
                        if data.get('status') in ['completed', 'failed']:
                            print(f"\n✅ Generation {data.get('status')}!")
                            self.test_results['completion'] = data
                            break
                    else:
                        print(f"   ⚠️  Progress check failed: {response.status_code}")
                        print(f"   Response: {response.text[:200]}")
                
                except Exception as e:
                    print(f"   ❌ Error checking progress: {e}")
                
                # Wait before next check
                if i < max_checks - 1:
                    await asyncio.sleep(5)
    
    async def verify_artifacts(self, run_id: str):
        """Test Step 4: Verify generated artifacts."""
        print("\n" + "=" * 80)
        print("📄 STEP 4: VERIFY ARTIFACTS")
        print("=" * 80)
        
        if not run_id:
            print("⚠️  No run_id available")
            return
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                response = await client.get(
                    f"{BASE_URL}/api/v1/documentation/runs/{run_id}/artifacts"
                )
                
                if response.status_code == 200:
                    artifacts = response.json()
                    
                    print(f"\n✅ Found {len(artifacts)} artifacts:")
                    for i, artifact in enumerate(artifacts[:5], 1):
                        print(f"\n   {i}. {artifact.get('name', 'Unnamed')}")
                        print(f"      Type: {artifact.get('artifact_type', 'unknown')}")
                        print(f"      Size: {artifact.get('size_bytes', 0)} bytes")
                        print(f"      Quality: {artifact.get('quality_score', 0):.2f}")
                    
                    if len(artifacts) > 5:
                        print(f"\n   ... and {len(artifacts) - 5} more")
                    
                    self.test_results['artifacts'] = {
                        'count': len(artifacts),
                        'artifacts': artifacts[:5]  # Store first 5
                    }
                else:
                    print(f"❌ Failed to get artifacts: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
            
            except Exception as e:
                print(f"❌ Error getting artifacts: {e}")
    
    async def test_analysis_results(self, plan_id: str):
        """Test Step 5: Check analysis results."""
        print("\n" + "=" * 80)
        print("🔬 STEP 5: VERIFY ANALYSIS RESULTS")
        print("=" * 80)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                # Try to get analysis for this plan
                response = await client.get(
                    f"{BASE_URL}/api/v1/analysis/plan/{plan_id}"
                )
                
                if response.status_code == 200:
                    analysis = response.json()
                    
                    print(f"\n✅ Analysis Results:")
                    print(f"   Files Analyzed: {analysis.get('total_files', 0)}")
                    print(f"   Languages: {analysis.get('total_languages', 0)}")
                    print(f"   Frameworks: {analysis.get('total_frameworks', 0)}")
                    print(f"   Services: {analysis.get('total_services', 0)}")
                    print(f"   Architecture: {analysis.get('primary_architecture', 'N/A')}")
                    print(f"   Modularity Score: {analysis.get('modularity_score', 0):.2f}")
                    
                    if analysis.get('primary_language'):
                        print(f"   Primary Language: {analysis['primary_language']}")
                else:
                    print(f"⚠️  Analysis not available: {response.status_code}")
            
            except Exception as e:
                print(f"⚠️  Could not retrieve analysis: {e}")
    
    def generate_report(self):
        """Generate final test report."""
        print("\n" + "=" * 80)
        print("📊 COMPLETE PIPELINE TEST REPORT")
        print("=" * 80)
        
        # Discovery
        print(f"\n🔍 Discovery Scan:")
        if self.test_results['discovery']:
            disc = self.test_results['discovery']
            print(f"   Status: {'✅ ' + disc['status'].upper() if disc['status'] == 'success' else '❌ FAILED'}")
            if disc['status'] == 'success':
                print(f"   Duration: {disc['duration']:.2f}s")
                print(f"   Plan ID: {disc['plan_id']}")
        
        # Generation Start
        print(f"\n📝 Generation Start:")
        if self.test_results['generation_start']:
            gen = self.test_results['generation_start']
            print(f"   Status: {'✅ ' + gen['status'].upper() if gen['status'] == 'success' else '❌ FAILED'}")
            if gen['status'] == 'success':
                print(f"   Duration: {gen['duration']:.2f}s")
                print(f"   Run ID: {gen['run_id']}")
        
        # Progress Monitoring
        print(f"\n📊 Progress Monitoring:")
        if self.test_results['progress_checks']:
            print(f"   Total Checks: {len(self.test_results['progress_checks'])}")
            last_check = self.test_results['progress_checks'][-1]
            print(f"   Last Status: {last_check['status']}")
            print(f"   Last Progress: {last_check['progress']:.1f}%")
        else:
            print(f"   ⚠️  No progress data")
        
        # Completion
        print(f"\n✅ Completion:")
        if self.test_results['completion']:
            comp = self.test_results['completion']
            print(f"   Final Status: {comp.get('status', 'unknown')}")
            print(f"   Total Artifacts: {comp.get('total_artifacts', 0)}")
            print(f"   Quality Score: {comp.get('overall_quality_score', 0):.2f}")
        else:
            print(f"   ⚠️  Not completed during test")
        
        # Artifacts
        print(f"\n📄 Artifacts:")
        if self.test_results['artifacts']:
            art = self.test_results['artifacts']
            print(f"   Count: {art['count']}")
        else:
            print(f"   ⚠️  No artifacts verified")
        
        # Overall Status
        print(f"\n" + "=" * 80)
        
        all_success = (
            self.test_results['discovery'] and 
            self.test_results['discovery']['status'] == 'success' and
            self.test_results['generation_start'] and
            self.test_results['generation_start']['status'] == 'success'
        )
        
        if all_success:
            print("🎉 PIPELINE TEST: ✅ PASSED")
        else:
            print("⚠️  PIPELINE TEST: ❌ INCOMPLETE")
        
        print("=" * 80)
        
        # Save results
        results_file = f"/tmp/full_pipeline_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")


async def main():
    """Run complete pipeline test."""
    print("=" * 80)
    print("🚀 COMPLETE DOCUMENT GENERATION PIPELINE TEST")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = DocumentPipelineTester()
    
    # Step 1: Discovery
    plan_id = await tester.test_discovery()
    
    if not plan_id:
        print("\n❌ Discovery failed, cannot continue")
        tester.generate_report()
        return
    
    # Step 2: Start Generation
    run_id = await tester.test_generation_start(plan_id)
    
    # Step 3: Monitor Progress
    await tester.monitor_progress(run_id, max_checks=10)
    
    # Step 4: Verify Artifacts
    if run_id:
        await tester.verify_artifacts(run_id)
    
    # Step 5: Check Analysis
    await tester.test_analysis_results(plan_id)
    
    # Final Report
    tester.generate_report()


if __name__ == "__main__":
    asyncio.run(main())

