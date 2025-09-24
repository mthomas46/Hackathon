"""API endpoint tests for Interpreter Service."""

import asyncio
import json

import httpx


class TestSampleDocumentsAPI:
    """Test the sample documents API endpoints."""

    def __init__(self):
        self.base_url = "http://localhost:5120"
        self.client = None

    async def setup_client(self):
        """Setup HTTP client for testing."""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def teardown_client(self):
        """Cleanup HTTP client."""
        if self.client:
            await self.client.aclose()

    async def test_health_endpoint(self):
        """Test the health endpoint."""
        print("Testing health endpoint...")
        try:
            await self.setup_client()
            response = await self.client.get("/health")

            print(f"Health endpoint status: {response.status_code}")
            assert response.status_code == 200

            data = response.json()
            print(f"Health response: {json.dumps(data, indent=2)}")
            assert data.get("status") == "healthy"
            print("✓ Health endpoint working")

        except Exception as e:
            print(f"✗ Health endpoint failed: {e}")
            raise
        finally:
            await self.teardown_client()

    async def test_sample_documents_types_endpoint(self):
        """Test the sample documents types endpoint."""
        print("\nTesting sample documents types endpoint...")
        try:
            await self.setup_client()
            response = await self.client.get("/documents/sample/types")

            print(f"Types endpoint status: {response.status_code}")
            data = response.json()
            print(f"Types response: {json.dumps(data, indent=2)}")

            # Check if there's an error
            if "error" in data:
                print(f"⚠️  Error in response: {data['error']}")
                if data["error"] == "Sample documents module not available":
                    print("🔍 This is the error we're trying to track down!")
                    return False

            assert response.status_code == 200
            assert "document_types" in data
            assert "special_collections" in data
            print("✓ Types endpoint working")

        except Exception as e:
            print(f"✗ Types endpoint failed: {e}")
            raise
        finally:
            await self.teardown_client()

    async def test_sample_documents_endpoint(self):
        """Test the sample documents endpoint."""
        print("\nTesting sample documents endpoint...")
        try:
            await self.setup_client()
            response = await self.client.get("/documents/sample")

            print(f"Documents endpoint status: {response.status_code}")
            data = response.json()
            print(f"Documents response keys: {list(data.keys())}")

            # Check if there's an error
            if "error" in data:
                print(f"⚠️  Error in response: {data['error']}")
                if data["error"] == "Sample documents module not available":
                    print("🔍 This is the error we're trying to track down!")
                    return False

            assert response.status_code == 200
            assert "documents" in data
            assert "total_count" in data
            print(
                f"✓ Documents endpoint working, returned {data.get('total_count', 0)} documents"
            )

        except Exception as e:
            print(f"✗ Documents endpoint failed: {e}")
            raise
        finally:
            await self.teardown_client()

    async def test_sample_documents_context_endpoint(self):
        """Test the sample documents context endpoint."""
        print("\nTesting sample documents context endpoint...")
        try:
            await self.setup_client()

            test_query = {
                "query": "Create a banking application with user authentication",
                "context": {"demo_mode": True},
            }

            response = await self.client.post(
                "/documents/sample/context", json=test_query
            )

            print(f"Context endpoint status: {response.status_code}")
            data = response.json()
            print(f"Context response keys: {list(data.keys())}")

            # Check if there's an error
            if "error" in data:
                print(f"⚠️  Error in response: {data['error']}")
                if data["error"] == "Sample documents module not available":
                    print("🔍 This is the error we're trying to track down!")
                    return False

            assert response.status_code == 200
            assert "relevant_documents" in data
            assert "total_relevant" in data
            print(
                f"✓ Context endpoint working, returned {data.get('total_relevant', 0)} relevant documents"
            )

        except Exception as e:
            print(f"✗ Context endpoint failed: {e}")
            raise
        finally:
            await self.teardown_client()

    async def test_openapi_docs(self):
        """Test that the OpenAPI docs include our endpoints."""
        print("\nTesting OpenAPI documentation...")
        try:
            await self.setup_client()
            response = await self.client.get("/docs")

            assert response.status_code == 200
            html_content = response.text

            # Check if our endpoints are in the docs
            endpoints_to_check = [
                "/documents/sample",
                "/documents/sample/types",
                "/documents/sample/context",
            ]

            for endpoint in endpoints_to_check:
                if endpoint in html_content:
                    print(f"✓ Found {endpoint} in OpenAPI docs")
                else:
                    print(f"⚠️  Missing {endpoint} in OpenAPI docs")

        except Exception as e:
            print(f"✗ OpenAPI docs test failed: {e}")
            raise
        finally:
            await self.teardown_client()


class TestDirectImportInContainer:
    """Test direct import within the container."""

    def test_container_import(self):
        """Test importing the module directly in the container."""
        print("\nTesting direct import in container...")

        import subprocess

        try:
            # Test the import directly in the container
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "hackathon-interpreter-1",
                    "python",
                    "-c",
                    "from services.interpreter.modules.sample_documents import sample_documents; print('Import successful')",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print("✓ Direct import in container successful")
                print(f"Output: {result.stdout.strip()}")
            else:
                print(f"✗ Direct import in container failed: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            print("✗ Direct import test timed out")
            return False
        except Exception as e:
            print(f"✗ Direct import test error: {e}")
            return False

        return True


async def run_api_tests():
    """Run all API tests."""
    print("🧪 Running Interpreter Service API Tests...\n")

    # Test health endpoint
    api_tester = TestSampleDocumentsAPI()
    await api_tester.test_health_endpoint()

    # Test sample documents endpoints
    success = await api_tester.test_sample_documents_types_endpoint()
    if not success:
        print("\n🔍 ISSUE DETECTED: Sample documents module not available!")
        print("Let's investigate further...")

        # Test direct import in container
        import_tester = TestDirectImportInContainer()
        import_tester.test_container_import()

        # Try to restart the service
        print("\n🔄 Attempting to restart interpreter service...")
        import subprocess

        result = subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose.dev.yml",
                "restart",
                "interpreter",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✓ Service restarted successfully")
            # Wait a moment for the service to start
            await asyncio.sleep(3)
            # Test again
            await api_tester.test_sample_documents_types_endpoint()
        else:
            print(f"✗ Service restart failed: {result.stderr}")

    # Continue with other tests
    await api_tester.test_sample_documents_endpoint()
    await api_tester.test_sample_documents_context_endpoint()
    await api_tester.test_openapi_docs()

    print("\n✅ API tests completed!")


def run_all_tests():
    """Run all tests."""
    print("🚀 Starting comprehensive test suite...\n")

    # Run the manual sample documents tests first
    print("1. Running sample documents unit tests...")
    try:
        from test_sample_documents import run_all_tests as run_sample_tests

        run_sample_tests()
    except Exception as e:
        print(f"✗ Sample documents tests failed: {e}")

    # Run API tests
    print("\n2. Running API endpoint tests...")
    asyncio.run(run_api_tests())


if __name__ == "__main__":
    run_all_tests()
