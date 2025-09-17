#!/usr/bin/env python3
"""
Inter-Service Communication Test Suite
Tests communication between services in the LLM Documentation Ecosystem
"""

import asyncio
import json
import time
import requests
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.text import Text
import statistics

console = Console()

class InterServiceCommunicationTester:
    """Test inter-service communication and integration workflows."""

    def __init__(self):
        self.base_urls = {
            'code_analyzer': 'http://localhost:5085',
            'log_collector': 'http://localhost:5080',
            'secure_analyzer': 'http://localhost:5070',
            'summarizer_hub': 'http://localhost:5060',
            'doc_store': 'http://localhost:5087',
            'analysis_service': 'http://localhost:5020',
            'orchestrator': 'http://localhost:5099'
        }

        self.results = {
            'individual_tests': [],
            'cross_service_tests': [],
            'workflows': [],
            'performance': [],
            'errors': []
        }

    async def test_individual_service_endpoints(self):
        """Test individual service endpoints."""
        console.print("\n🔍 Testing Individual Service Endpoints")
        console.print("=" * 50)

        test_cases = [
            # Code Analyzer
            ('code_analyzer', 'GET', '/health', None, "Health check"),
            ('code_analyzer', 'POST', '/analyze', {
                "code": "def hello():\n    print('Hello World')",
                "language": "python"
            }, "Code analysis"),

            # Secure Analyzer
            ('secure_analyzer', 'GET', '/health', None, "Health check"),
            ('secure_analyzer', 'POST', '/detect', {
                "content": "password = 'admin123'",
                "language": "python"
            }, "Security detection"),

            # Log Collector
            ('log_collector', 'GET', '/health', None, "Health check"),
            ('log_collector', 'POST', '/logs', {
                "level": "INFO",
                "message": "Test log message",
                "service": "test_service"
            }, "Log submission"),
            ('log_collector', 'GET', '/logs', None, "Log retrieval"),

            # Summarizer Hub
            ('summarizer_hub', 'GET', '/health', None, "Health check"),
            ('summarizer_hub', 'POST', '/summarize', {
                "content": "This is a test document for summarization.",
                "format": "text"
            }, "Document summarization"),
        ]

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        )

        with progress:
            task = progress.add_task("Testing endpoints...", total=len(test_cases))

            for service, method, endpoint, data, description in test_cases:
                progress.update(task, description=f"Testing {service} {endpoint}")

                result = await self._test_endpoint(service, method, endpoint, data, description)
                self.results['individual_tests'].append(result)

                progress.update(task, advance=1)

        # Display results
        self._display_individual_test_results()

    async def test_cross_service_communication(self):
        """Test cross-service communication scenarios."""
        console.print("\n🔗 Testing Cross-Service Communication")
        console.print("=" * 50)

        # Test scenarios that involve multiple services
        scenarios = [
            {
                'name': 'Code Analysis -> Secure Analysis',
                'steps': [
                    ('code_analyzer', 'POST', '/analyze', {
                        "code": "import os\npassword = os.getenv('SECRET')",
                        "language": "python"
                    }),
                    ('secure_analyzer', 'POST', '/detect', {
                        "content": "import os\npassword = os.getenv('SECRET')",
                        "language": "python"
                    })
                ]
            },
            {
                'name': 'Log Collection Workflow',
                'steps': [
                    ('log_collector', 'POST', '/logs', {
                        "level": "ERROR",
                        "message": "Security vulnerability detected in user authentication",
                        "service": "auth_service"
                    }),
                    ('log_collector', 'GET', '/logs', None),
                    ('log_collector', 'GET', '/stats', None)
                ]
            },
            {
                'name': 'Summarization Pipeline',
                'steps': [
                    ('summarizer_hub', 'POST', '/categorize', {
                        "document": {
                            "id": "test_doc_001",
                            "content": "This document contains information about machine learning algorithms and their applications in natural language processing."
                        }
                    }),
                    ('summarizer_hub', 'POST', '/summarize', {
                        "content": "Machine learning algorithms are powerful tools for processing natural language data.",
                        "format": "markdown"
                    })
                ]
            }
        ]

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        )

        for scenario in scenarios:
            console.print(f"🔗 Testing: {scenario['name']}")

            scenario_result = {
                'name': scenario['name'],
                'steps': [],
                'success': True,
                'total_time': 0
            }

            start_time = time.time()

            for i, (service, method, endpoint, data) in enumerate(scenario['steps']):
                console.print(f"   Step {i+1}: {service} {endpoint}")

                step_result = await self._test_endpoint(
                    service, method, endpoint, data,
                    f"Step {i+1}: {service} {endpoint}"
                )

                scenario_result['steps'].append(step_result)

                if not step_result['success']:
                    console.print(f"   ❌ Failed: {step_result.get('error', 'Unknown error')}")
                    scenario_result['success'] = False
                    break
                else:
                    console.print(f"   ✅ Success ({step_result['response_time']:.1f}ms)")

            scenario_result['total_time'] = time.time() - start_time
            self.results['cross_service_tests'].append(scenario_result)

        # Display results
        self._display_cross_service_results()

    async def test_service_workflows(self):
        """Test complex service workflows."""
        console.print("\n⚡ Testing Service Workflows")
        console.print("=" * 50)

        workflows = [
            {
                'name': 'Document Processing Pipeline',
                'description': 'Process document through multiple analysis services',
                'steps': [
                    # 1. Analyze code
                    ('code_analyzer', 'POST', '/analyze', {
                        "code": "def authenticate_user(username, password):\n    return username == 'admin' and password == 'secret'",
                        "language": "python"
                    }),
                    # 2. Check for security issues
                    ('secure_analyzer', 'POST', '/detect', {
                        "content": "def authenticate_user(username, password):\n    return username == 'admin' and password == 'secret'",
                        "language": "python"
                    }),
                    # 3. Log the analysis
                    ('log_collector', 'POST', '/logs', {
                        "level": "INFO",
                        "message": "Completed security analysis of authentication function",
                        "service": "analysis_pipeline"
                    }),
                    # 4. Generate summary
                    ('summarizer_hub', 'POST', '/summarize', {
                        "content": "Security analysis completed for authentication function. Found hardcoded credentials.",
                        "format": "text"
                    })
                ]
            }
        ]

        for workflow in workflows:
            console.print(f"\n🔄 Running workflow: {workflow['name']}")
            console.print(f"   {workflow['description']}")

            workflow_result = {
                'name': workflow['name'],
                'steps': [],
                'success': True,
                'total_time': 0
            }

            start_time = time.time()

            for i, (service, method, endpoint, data) in enumerate(workflow['steps']):
                console.print(f"   Step {i+1}: {service} {endpoint}")

                step_result = await self._test_endpoint(
                    service, method, endpoint, data,
                    f"Workflow step {i+1}"
                )

                workflow_result['steps'].append(step_result)

                if not step_result['success']:
                    workflow_result['success'] = False
                    console.print(f"   ❌ Step {i+1} failed: {step_result.get('error', 'Unknown error')}")
                    break
                else:
                    console.print(f"   ✅ Step {i+1} completed ({step_result['response_time']:.1f}ms)")

            workflow_result['total_time'] = time.time() - start_time
            self.results['workflows'].append(workflow_result)

            status = "✅ PASSED" if workflow_result['success'] else "❌ FAILED"
            console.print(f"\n{status} Workflow completed in {workflow_result['total_time']:.2f}s")

    async def test_performance_and_load(self):
        """Test performance and load handling."""
        console.print("\n⚡ Testing Performance & Load")
        console.print("=" * 50)

        # Test concurrent requests to different services
        concurrent_tests = [
            ('code_analyzer', 'GET', '/health'),
            ('secure_analyzer', 'GET', '/health'),
            ('log_collector', 'GET', '/health'),
            ('summarizer_hub', 'GET', '/health')
        ]

        console.print("Testing concurrent requests...")

        response_times = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []

            for service, method, endpoint in concurrent_tests:
                future = executor.submit(
                    self._sync_test_endpoint,
                    service, method, endpoint, None
                )
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    response_times.append(result['response_time'])

        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            console.print("📊 Performance Results:")
            console.print(f"   Average response time: {avg_time:.2f}ms")
            console.print(f"   Min response time: {min_time:.2f}ms")
            console.print(f"   Max response time: {max_time:.2f}ms")
            console.print(f"   Concurrent requests: {len(response_times)}")

            self.results['performance'].append({
                'test_type': 'concurrent_health_checks',
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'requests': len(response_times)
            })

    async def _test_endpoint(self, service: str, method: str, endpoint: str,
                           data: Optional[Dict] = None, description: str = "") -> Dict[str, Any]:
        """Test a single endpoint."""
        base_url = self.base_urls.get(service)
        if not base_url:
            return {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'success': False,
                'error': f'Service {service} not configured',
                'response_time': 0
            }

        url = f"{base_url}{endpoint}"

        try:
            start_time = time.time()

            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=10)
            else:
                return {
                    'service': service,
                    'endpoint': endpoint,
                    'method': method,
                    'success': False,
                    'error': f'Unsupported method: {method}',
                    'response_time': 0
                }

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            return {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'description': description,
                'success': response.status_code in [200, 201, 202],
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'response_size': len(response.content),
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }

        except requests.exceptions.RequestException as e:
            return {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'description': description,
                'success': False,
                'error': str(e),
                'response_time': 0
            }
        except Exception as e:
            return {
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'description': description,
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'response_time': 0
            }

    def _sync_test_endpoint(self, service: str, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Synchronous version for ThreadPoolExecutor."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._test_endpoint(service, method, endpoint, data))
        finally:
            loop.close()

    def _display_individual_test_results(self):
        """Display results of individual endpoint tests."""
        table = Table(title="Individual Service Endpoint Tests")
        table.add_column("Service", style="cyan")
        table.add_column("Endpoint", style="white")
        table.add_column("Method", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Time", style="blue")
        table.add_column("Description", style="white")

        successful = 0
        total = len(self.results['individual_tests'])

        for result in self.results['individual_tests']:
            if result['success']:
                status = f"✅ {result['status_code']}"
                successful += 1
            else:
                status = f"❌ {result.get('error', 'Failed')}"

            time_str = f"{result['response_time']}ms" if result['success'] else "N/A"

            table.add_row(
                result['service'],
                result['endpoint'],
                result['method'],
                status,
                time_str,
                result.get('description', '')
            )

        console.print(table)
        console.print(f"\n📊 Individual Tests: {successful}/{total} passed")

    def _display_cross_service_results(self):
        """Display results of cross-service communication tests."""
        table = Table(title="Cross-Service Communication Tests")
        table.add_column("Scenario", style="cyan")
        table.add_column("Steps", style="white")
        table.add_column("Success Rate", style="green")
        table.add_column("Total Time", style="blue")

        for result in self.results['cross_service_tests']:
            successful_steps = sum(1 for step in result['steps'] if step['success'])
            total_steps = len(result['steps'])

            success_rate = f"{successful_steps}/{total_steps}"
            status_icon = "✅" if result['success'] else "❌"
            time_str = f"{result['total_time']:.2f}s"

            table.add_row(
                result['name'],
                str(total_steps),
                f"{status_icon} {success_rate}",
                time_str
            )

        console.print(table)

    def generate_report(self):
        """Generate comprehensive test report."""
        console.print("\n" + "=" * 80)
        console.print("📊 INTER-SERVICE COMMUNICATION TEST REPORT")
        console.print("=" * 80)

        # Overall summary
        individual_passed = sum(1 for r in self.results['individual_tests'] if r['success'])
        individual_total = len(self.results['individual_tests'])

        workflow_passed = sum(1 for r in self.results['workflows'] if r['success'])
        workflow_total = len(self.results['workflows'])

        cross_service_passed = sum(1 for r in self.results['cross_service_tests'] if r['success'])
        cross_service_total = len(self.results['cross_service_tests'])

        console.print("🎯 OVERALL RESULTS:")
        console.print(f"   Individual Endpoint Tests: {individual_passed}/{individual_total}")
        console.print(f"   Cross-Service Tests: {cross_service_passed}/{cross_service_total}")
        console.print(f"   Workflow Tests: {workflow_passed}/{workflow_total}")

        if self.results['performance']:
            perf = self.results['performance'][0]
            console.print("⚡ PERFORMANCE:")
            console.print(f"   Concurrent Requests: {perf['requests']}")
            console.print(f"   Avg Response Time: {perf['avg_time']:.2f}ms")
            console.print(f"   Response Time Range: {perf['min_time']:.2f}ms - {perf['max_time']:.2f}ms")

        # Determine overall status
        total_passed = individual_passed + cross_service_passed + workflow_passed
        total_tests = individual_total + cross_service_total + workflow_total

        if total_passed == total_tests:
            overall_status = "🎉 ALL TESTS PASSED"
            console.print(f"\n{overall_status}")
            console.print("✅ Inter-service communication is working perfectly!")
        elif total_passed > total_tests * 0.8:
            overall_status = "⚠️ MOSTLY SUCCESSFUL"
            console.print(f"\n{overall_status}")
            console.print("⚠️ Some tests failed - check individual results above")
        else:
            overall_status = "❌ ISSUES DETECTED"
            console.print(f"\n{overall_status}")
            console.print("❌ Multiple test failures - investigate communication issues")

        # Save detailed results
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'individual_tests': f'{individual_passed}/{individual_total}',
                'cross_service_tests': f'{cross_service_passed}/{cross_service_total}',
                'workflow_tests': f'{workflow_passed}/{workflow_total}',
                'overall_status': overall_status
            },
            'results': self.results
        }

        report_file = 'scripts/integration/inter_service_communication_report.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        console.print(f"\n📄 Detailed report saved to: {report_file}")

        return total_passed == total_tests

async def main():
    """Main test execution."""
    console.print(Panel.fit(
        "[bold blue]🔗 LLM Documentation Ecosystem[/bold blue]\n"
        "[dim]Inter-Service Communication Test Suite[/dim]"
    ))

    tester = InterServiceCommunicationTester()

    try:
        # Test individual endpoints
        await tester.test_individual_service_endpoints()

        # Test cross-service communication
        await tester.test_cross_service_communication()

        # Test complex workflows
        await tester.test_service_workflows()

        # Test performance
        await tester.test_performance_and_load()

        # Generate final report
        success = tester.generate_report()

        if success:
            console.print("\n🎉 INTER-SERVICE COMMUNICATION: HEALTHY")
            return 0
        else:
            console.print("\n⚠️ INTER-SERVICE COMMUNICATION: ISSUES DETECTED")
            return 1

    except KeyboardInterrupt:
        console.print("\n\n🛑 Test interrupted by user")
        return 1
    except Exception as e:
        console.print(f"\n❌ Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
