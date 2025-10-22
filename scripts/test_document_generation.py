"""
Comprehensive test script for document generation API.

Tests the complete pipeline:
1. Discovery scan (create processing plan)
2. Documentation generation (multi-pass)
3. Status monitoring
4. Results validation
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 300.0  # 5 minutes for long operations
TEST_REPO_PATH = "/app"  # Container path


class DocumentGenerationTester:
    """Comprehensive tester for document generation API."""
    
    def __init__(self):
        self.results = {
            "discovery": None,
            "generation": None,
            "monitoring": [],
            "validation": None,
            "errors": []
        }
        self.plan_id = None
        self.run_id = None
    
    async def test_discovery_scan(self, repo_path: str) -> Dict[str, Any]:
        """Test Step 1: Discovery scan to create processing plan."""
        print("\n" + "=" * 70)
        print("🔍 STEP 1: DISCOVERY SCAN")
        print("=" * 70)
        print(f"\n📂 Scanning repository: {repo_path}")
        
        request_body = {
            "repo_path": repo_path,
            "resolve_host_path": False,
            "save_to_db": True
        }
        
        print(f"\n📤 Request:")
        print(json.dumps(request_body, indent=2))
        
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                start_time = time.time()
                response = await client.post(
                    f"{BASE_URL}/api/v1/discovery/scan",
                    json=request_body
                )
                duration = time.time() - start_time
                
                print(f"\n⏱️  Duration: {duration:.2f}s")
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n✅ Discovery scan successful!")
                    
                    # Extract key information
                    self.plan_id = data.get("plan_id")
                    print(f"\n📋 Plan ID: {self.plan_id}")
                    print(f"📊 Summary:")
                    print(f"   Total Files: {data.get('total_files', 'N/A')}")
                    print(f"   Total Sub-Jobs: {data.get('total_sub_jobs', 'N/A')}")
                    print(f"   Services Detected: {len(data.get('services', []))}")
                    
                    if data.get('services'):
                        print(f"\n🔧 Detected Services:")
                        for svc in data['services'][:5]:  # Show first 5
                            print(f"      - {svc}")
                    
                    self.results['discovery'] = {
                        "success": True,
                        "plan_id": self.plan_id,
                        "duration": duration,
                        "data": data
                    }
                    
                    return data
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"\n❌ Discovery scan failed: {error_msg}")
                    self.results['errors'].append({
                        "step": "discovery",
                        "error": error_msg
                    })
                    return None
                    
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"\n❌ Discovery scan error: {error_msg}")
            self.results['errors'].append({
                "step": "discovery",
                "error": error_msg
            })
            return None
    
    async def test_documentation_generation(
        self,
        plan_id: str,
        repo_path: str,
        passes: Optional[list] = None
    ) -> Dict[str, Any]:
        """Test Step 2: Start documentation generation."""
        print("\n" + "=" * 70)
        print("📝 STEP 2: DOCUMENTATION GENERATION")
        print("=" * 70)
        print(f"\n🎯 Starting multi-pass documentation generation...")
        print(f"📋 Plan ID: {plan_id}")
        print(f"📂 Repo Path: {repo_path}")
        
        request_body = {
            "plan_id": plan_id,
            "repo_path": repo_path,
            "passes": passes or ["architecture", "component"],
            "output_formats": ["markdown"],
            "include_diagrams": True,
            "include_examples": True,
            "validate_between_passes": True,
            "min_quality_score": 0.7
        }
        
        print(f"\n📤 Request:")
        print(json.dumps(request_body, indent=2))
        
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                start_time = time.time()
                response = await client.post(
                    f"{BASE_URL}/api/v1/documentation/generate",
                    json=request_body
                )
                duration = time.time() - start_time
                
                print(f"\n⏱️  Duration: {duration:.2f}s")
                print(f"📊 Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n✅ Documentation generation started!")
                    
                    self.run_id = data.get("run_id")
                    print(f"\n📋 Run ID: {self.run_id}")
                    print(f"📊 Status: {data.get('status', 'N/A')}")
                    print(f"🎯 Passes: {', '.join(data.get('passes', []))}")
                    
                    self.results['generation'] = {
                        "success": True,
                        "run_id": self.run_id,
                        "duration": duration,
                        "data": data
                    }
                    
                    return data
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"\n❌ Generation start failed: {error_msg}")
                    self.results['errors'].append({
                        "step": "generation",
                        "error": error_msg
                    })
                    return None
                    
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"\n❌ Generation error: {error_msg}")
            self.results['errors'].append({
                "step": "generation",
                "error": error_msg
            })
            return None
    
    async def monitor_generation_progress(
        self,
        run_id: str,
        poll_interval: int = 10,
        max_polls: int = 30
    ) -> Dict[str, Any]:
        """Test Step 3: Monitor documentation generation progress."""
        print("\n" + "=" * 70)
        print("📊 STEP 3: MONITORING PROGRESS")
        print("=" * 70)
        print(f"\n👀 Monitoring run: {run_id}")
        print(f"⏱️  Poll interval: {poll_interval}s")
        print(f"🔄 Max polls: {max_polls}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for poll_num in range(max_polls):
                    print(f"\n📊 Poll {poll_num + 1}/{max_polls}...")
                    
                    response = await client.get(
                        f"{BASE_URL}/api/v1/documentation/runs/{run_id}"
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get('status', 'unknown')
                        
                        print(f"   Status: {status}")
                        print(f"   Progress: {data.get('progress', 0):.1f}%")
                        print(f"   Current Pass: {data.get('current_pass', 'N/A')}")
                        
                        if data.get('documents_generated'):
                            print(f"   Documents: {data.get('documents_generated')}")
                        
                        # Store monitoring data
                        self.results['monitoring'].append({
                            "poll_num": poll_num + 1,
                            "status": status,
                            "data": data
                        })
                        
                        # Check if complete
                        if status in ['completed', 'failed', 'cancelled']:
                            print(f"\n✅ Generation {status}!")
                            return data
                    else:
                        print(f"   ⚠️  HTTP {response.status_code}")
                    
                    if poll_num < max_polls - 1:
                        await asyncio.sleep(poll_interval)
                
                print(f"\n⚠️  Max polls reached. Generation may still be in progress.")
                return None
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"\n❌ Monitoring error: {error_msg}")
            self.results['errors'].append({
                "step": "monitoring",
                "error": error_msg
            })
            return None
    
    async def validate_generated_documents(self, run_id: str) -> Dict[str, Any]:
        """Test Step 4: Validate generated documents."""
        print("\n" + "=" * 70)
        print("✅ STEP 4: VALIDATION")
        print("=" * 70)
        print(f"\n🔍 Validating documents for run: {run_id}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get run details
                response = await client.get(
                    f"{BASE_URL}/api/v1/documentation/runs/{run_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"\n📊 Run Summary:")
                    print(f"   Status: {data.get('status', 'N/A')}")
                    print(f"   Documents Generated: {data.get('documents_generated', 0)}")
                    print(f"   Total Passes: {len(data.get('completed_passes', []))}")
                    print(f"   Quality Score: {data.get('quality_score', 'N/A')}")
                    
                    # Try to get generated documents
                    if data.get('artifact_ids'):
                        print(f"\n📄 Generated Artifacts: {len(data['artifact_ids'])}")
                        for artifact_id in data['artifact_ids'][:5]:  # Show first 5
                            print(f"      - {artifact_id}")
                    
                    validation_result = {
                        "success": True,
                        "documents_count": data.get('documents_generated', 0),
                        "quality_score": data.get('quality_score'),
                        "status": data.get('status'),
                        "data": data
                    }
                    
                    self.results['validation'] = validation_result
                    return validation_result
                else:
                    print(f"\n❌ Validation failed: HTTP {response.status_code}")
                    return None
                    
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"\n❌ Validation error: {error_msg}")
            self.results['errors'].append({
                "step": "validation",
                "error": error_msg
            })
            return None
    
    async def run_comprehensive_test(
        self,
        repo_path: str = TEST_REPO_PATH,
        passes: Optional[list] = None
    ) -> Dict[str, Any]:
        """Run complete test suite."""
        print("\n" + "=" * 70)
        print("🚀 DOCUMENT GENERATION API - COMPREHENSIVE TEST")
        print("=" * 70)
        print(f"\n⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Repository: {repo_path}")
        
        test_start = time.time()
        
        # Step 1: Discovery scan
        discovery_result = await self.test_discovery_scan(repo_path)
        if not discovery_result or not self.plan_id:
            print("\n❌ CRITICAL: Discovery scan failed. Cannot proceed.")
            self.generate_report()
            return self.results
        
        await asyncio.sleep(2)  # Brief pause
        
        # Step 2: Start documentation generation
        generation_result = await self.test_documentation_generation(
            self.plan_id,
            repo_path,
            passes
        )
        if not generation_result or not self.run_id:
            print("\n❌ CRITICAL: Generation start failed. Cannot proceed.")
            self.generate_report()
            return self.results
        
        await asyncio.sleep(5)  # Let generation start
        
        # Step 3: Monitor progress
        final_status = await self.monitor_generation_progress(self.run_id)
        
        await asyncio.sleep(2)  # Brief pause
        
        # Step 4: Validate results
        validation = await self.validate_generated_documents(self.run_id)
        
        test_duration = time.time() - test_start
        
        # Generate final report
        self.generate_report(test_duration)
        
        return self.results
    
    def generate_report(self, total_duration: Optional[float] = None):
        """Generate comprehensive test report."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        if total_duration:
            print(f"\n⏱️  Total Test Duration: {total_duration:.2f}s")
        
        # Discovery results
        print("\n🔍 Discovery Scan:")
        if self.results['discovery']:
            disc = self.results['discovery']
            print(f"   ✅ Status: SUCCESS")
            print(f"   ⏱️  Duration: {disc['duration']:.2f}s")
            print(f"   📋 Plan ID: {disc['plan_id']}")
        else:
            print(f"   ❌ Status: FAILED")
        
        # Generation results
        print("\n📝 Documentation Generation:")
        if self.results['generation']:
            gen = self.results['generation']
            print(f"   ✅ Status: STARTED")
            print(f"   ⏱️  Duration: {gen['duration']:.2f}s")
            print(f"   📋 Run ID: {gen['run_id']}")
        else:
            print(f"   ❌ Status: FAILED")
        
        # Monitoring results
        print(f"\n📊 Progress Monitoring:")
        if self.results['monitoring']:
            print(f"   📊 Total Polls: {len(self.results['monitoring'])}")
            last_poll = self.results['monitoring'][-1]
            print(f"   📊 Final Status: {last_poll['status']}")
        else:
            print(f"   ⚠️  No monitoring data")
        
        # Validation results
        print(f"\n✅ Validation:")
        if self.results['validation']:
            val = self.results['validation']
            print(f"   ✅ Status: {val['status']}")
            print(f"   📄 Documents: {val['documents_count']}")
            if val.get('quality_score'):
                print(f"   ⭐ Quality: {val['quality_score']:.2f}")
        else:
            print(f"   ❌ Status: NOT VALIDATED")
        
        # Errors
        if self.results['errors']:
            print(f"\n❌ Errors Encountered:")
            for error in self.results['errors']:
                print(f"   • {error['step']}: {error['error']}")
        else:
            print(f"\n✅ No errors encountered!")
        
        # Save results to file
        results_file = f"/tmp/doc_generation_test_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Final verdict
        print("\n" + "=" * 70)
        if (self.results['discovery'] and 
            self.results['generation'] and 
            not self.results['errors']):
            print("🎉 TEST SUITE: ✅ PASSED")
        else:
            print("⚠️  TEST SUITE: ❌ FAILED (see errors above)")
        print("=" * 70)


async def main():
    """Run the comprehensive test."""
    tester = DocumentGenerationTester()
    
    # Run with a subset of passes for faster testing
    # Valid Options: "architecture", "component", "api_reference", "examples", "synthesis"
    test_passes = ["architecture", "component"]
    
    await tester.run_comprehensive_test(
        repo_path=TEST_REPO_PATH,
        passes=test_passes
    )


if __name__ == "__main__":
    asyncio.run(main())

