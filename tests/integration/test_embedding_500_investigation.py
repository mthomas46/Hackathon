#!/usr/bin/env python3
"""
TDD: Investigate "Embedding generation returned 500" error.
"""

import requests
import json
import subprocess


class TestEmbedding500Investigation:
    """Diagnose why embedding generation returns HTTP 500."""
    
    def test_1_reproduce_500_error(self):
        """TEST 1: Reproduce the exact 500 error from demo."""
        print("\n" + "=" * 70)
        print("🧪 TEST 1: Reproduce Embedding Generation 500 Error")
        print("=" * 70)
        
        doc_store_url = "http://localhost:5087"
        
        try:
            # Make the same call the demo makes
            response = requests.post(
                f"{doc_store_url}/api/v1/embeddings/generate-batch",
                params={"limit": 100},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print(f"✅ Successfully reproduced 500 error")
                
                # Get detailed error
                try:
                    error_data = response.json()
                    print(f"\nError Response:")
                    print(json.dumps(error_data, indent=2))
                    
                    # Extract the actual error message
                    detail = error_data.get('detail', '')
                    if 'sentence-transformers' in detail:
                        print(f"\n🔍 ROOT CAUSE FOUND:")
                        print(f"   Missing dependency: sentence-transformers")
                        return "missing_dependency"
                    else:
                        print(f"\n🔍 Error detail: {detail}")
                        return "other_error"
                        
                except Exception as e:
                    print(f"Could not parse error JSON: {e}")
                    print(f"Raw response: {response.text[:500]}")
                    
            elif response.status_code == 200:
                print(f"✅ Endpoint working! (200 OK)")
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
                return "working"
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                return "unexpected"
                
        except Exception as e:
            print(f"❌ Error calling endpoint: {e}")
            return "connection_error"
    
    def test_2_check_sentence_transformers_in_container(self):
        """TEST 2: Is sentence-transformers installed in doc-store container?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 2: Check sentence-transformers Installation")
        print("=" * 70)
        
        try:
            # Check if sentence-transformers is installed
            result = subprocess.run(
                ["docker", "exec", "doc_store", "pip", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                packages = result.stdout.lower()
                
                if 'sentence-transformers' in packages or 'sentence_transformers' in packages:
                    print(f"✅ sentence-transformers IS installed")
                    
                    # Get version
                    for line in result.stdout.split('\n'):
                        if 'sentence' in line.lower():
                            print(f"   {line}")
                    return True
                else:
                    print(f"❌ sentence-transformers NOT installed")
                    print(f"\n📦 Installed ML packages:")
                    
                    # Show what IS installed
                    ml_packages = ['torch', 'transformers', 'numpy', 'scipy']
                    for pkg in ml_packages:
                        for line in result.stdout.split('\n'):
                            if pkg in line.lower():
                                print(f"   {line}")
                                break
                    
                    return False
            else:
                print(f"❌ Could not check packages: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error checking installation: {e}")
            return None
    
    def test_3_check_requirements_file(self):
        """TEST 3: Is sentence-transformers in requirements?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 3: Check Requirements File")
        print("=" * 70)
        
        req_files = [
            "services/doc_store/requirements.txt",
            "requirements.txt",
            "services/doc_store/Dockerfile"
        ]
        
        for req_file in req_files:
            try:
                with open(req_file, 'r') as f:
                    content = f.read()
                
                print(f"\n📄 {req_file}:")
                
                if 'sentence-transformers' in content or 'sentence_transformers' in content:
                    print(f"   ✅ sentence-transformers found in {req_file}")
                    # Show the line
                    for line in content.split('\n'):
                        if 'sentence' in line.lower():
                            print(f"      {line}")
                else:
                    print(f"   ❌ sentence-transformers NOT in {req_file}")
                    
            except FileNotFoundError:
                print(f"   ⚠️  File not found: {req_file}")
            except Exception as e:
                print(f"   ❌ Error reading {req_file}: {e}")
    
    def test_4_check_embedding_service_code(self):
        """TEST 4: What does the embedding service code expect?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 4: Embedding Service Code Analysis")
        print("=" * 70)
        
        service_file = "services/doc_store/domain/embeddings/service.py"
        
        try:
            with open(service_file, 'r') as f:
                content = f.read()
            
            print(f"📄 Analyzing {service_file}...")
            
            # Check for sentence-transformers import
            if 'sentence_transformers' in content or 'sentence-transformers' in content:
                print(f"   ✅ Code imports sentence-transformers")
                
                # Find the import line
                for line in content.split('\n'):
                    if 'import' in line and 'sentence' in line.lower():
                        print(f"      {line.strip()}")
            else:
                print(f"   ⚠️  No direct sentence-transformers import found")
            
            # Check for error handling
            if 'sentence-transformers' in content:
                print(f"\n   🔍 Found error message mentioning sentence-transformers")
                # Find the error message
                for i, line in enumerate(content.split('\n')):
                    if 'sentence-transformers' in line and ('raise' in line or 'error' in line.lower()):
                        print(f"      Line {i+1}: {line.strip()[:80]}")
            
            # Check if there's a try/except for missing dependency
            if 'ImportError' in content or 'ModuleNotFoundError' in content:
                print(f"\n   ✅ Code has import error handling")
            else:
                print(f"\n   ⚠️  Code may not handle missing dependency gracefully")
                
        except FileNotFoundError:
            print(f"   ❌ File not found: {service_file}")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    
    def test_5_is_it_optional_or_required(self):
        """TEST 5: Is sentence-transformers optional or required?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 5: Determine if Dependency is Optional")
        print("=" * 70)
        
        print("Checking if system can work without embeddings...")
        
        # Check if Phase 7 completed despite 500
        with open("horus_demo_final_run.log", 'r') as f:
            log = f.read()
        
        if "✅ ✨ Horus Heresy Knowledge Base Demo Complete!" in log:
            print(f"✅ Demo completed successfully despite 500 error")
            print(f"   → sentence-transformers is OPTIONAL")
            
            # Check what still worked
            if "RAG synthesis completed" in log:
                print(f"   ✅ RAG synthesis still worked")
            if "Hybrid search" in log:
                print(f"   ✅ Hybrid search still worked")
            
            return "optional"
        else:
            print(f"❌ Demo failed due to 500 error")
            print(f"   → sentence-transformers is REQUIRED")
            return "required"
    
    def test_6_provide_solution(self):
        """TEST 6: Provide clear solution."""
        print("\n" + "=" * 70)
        print("🔧 TEST 6: Solution Recommendation")
        print("=" * 70)
        
        is_installed = self.test_2_check_sentence_transformers_in_container()
        is_optional = self.test_5_is_it_optional_or_required()
        
        print("\n" + "=" * 70)
        print("💡 DIAGNOSIS SUMMARY")
        print("=" * 70)
        
        if not is_installed:
            print("\n🔍 ROOT CAUSE:")
            print("   sentence-transformers package is NOT installed in doc-store container")
            
            print("\n📊 IMPACT:")
            if is_optional == "optional":
                print("   ⚠️  LOW - System works without it (graceful degradation)")
                print("   • RAG synthesis works (no_context mode)")
                print("   • Hybrid search works (keyword-only mode)")
                print("   • Demo completes successfully")
            else:
                print("   ❌ HIGH - System requires it for embeddings")
            
            print("\n🔧 SOLUTION OPTIONS:")
            print("\n   Option 1: Add to Dockerfile (RECOMMENDED)")
            print("   ────────────────────────────────────────")
            print("   Edit: services/doc_store/Dockerfile")
            print("   Add:  RUN pip install sentence-transformers")
            print("   Then: Rebuild and restart container")
            print("\n   Commands:")
            print("   $ docker stop doc_store && docker rm doc_store")
            print("   $ docker build -f services/doc_store/Dockerfile -t hackathon-doc_store .")
            print("   $ docker run -d --name doc_store --network ams -p 5087:5010 \\")
            print("       -e ENVIRONMENT=development -v $(pwd)/services/doc_store/data:/app/data \\")
            print("       hackathon-doc_store:latest")
            
            print("\n   Option 2: Install in Running Container (TEMPORARY)")
            print("   ──────────────────────────────────────────────────")
            print("   $ docker exec doc_store pip install sentence-transformers")
            print("   ⚠️  Note: Will be lost if container is recreated")
            
            print("\n   Option 3: Accept Graceful Degradation (CURRENT)")
            print("   ────────────────────────────────────────────────")
            print("   • System works without embeddings")
            print("   • Uses keyword search instead of semantic")
            print("   • No changes needed")
            print("   ✅ Already working this way!")
            
        else:
            print("\n✅ sentence-transformers IS installed")
            print("   Need to investigate other cause of 500 error")
    
    def run_all_tests(self):
        """Run complete investigation."""
        print("\n" + "╔" + "=" * 68 + "╗")
        print("║" + " " * 68 + "║")
        print("║" + "  TDD: EMBEDDING 500 ERROR INVESTIGATION".center(68) + "║")
        print("║" + " " * 68 + "║")
        print("╚" + "=" * 68 + "╝")
        
        self.test_1_reproduce_500_error()
        self.test_2_check_sentence_transformers_in_container()
        self.test_3_check_requirements_file()
        self.test_4_check_embedding_service_code()
        self.test_5_is_it_optional_or_required()
        self.test_6_provide_solution()
        
        print("\n" + "=" * 70)
        print("✅ INVESTIGATION COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    tester = TestEmbedding500Investigation()
    tester.run_all_tests()

