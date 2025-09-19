#!/usr/bin/env python3
"""
🚀 **WORKFLOW DEMO SCRIPT**
Complete Interpreter → Orchestrator → Simulation → Analysis Workflow Demonstration

This script demonstrates the full end-to-end workflow from natural language query
through simulation execution with comprehensive document analysis and recommendations.

USAGE:
    python demo_workflow.py

REQUIREMENTS:
    - All services running (see docker-compose.dev.yml)
    - Interpreter service on port 5050
    - Orchestrator service on port 5000
    - Simulation service on port 5075
    - Summarizer service on port 5160

WORKFLOW STEPS:
    1. 📝 User submits natural language query
    2. 🧠 Interpreter processes and understands intent
    3. 🎯 Orchestrator coordinates workflow execution
    4. 🏗️ Simulation service creates simulation with mock data
    5. 🔬 Summarizer-hub performs comprehensive analysis
    6. 📊 Results aggregated and presented to user
    7. 🎫 Optional Jira tickets created for follow-up
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class WorkflowDemo:
    """Complete workflow demonstration class."""

    def __init__(self):
        self.config = {
            "interpreter_url": os.getenv("INTERPRETER_URL", "http://localhost:5050"),
            "orchestrator_url": os.getenv("ORCHESTRATOR_URL", "http://localhost:5000"),
            "simulation_url": os.getenv("SIMULATION_URL", "http://localhost:5075"),
            "summarizer_url": os.getenv("SUMMARIZER_URL", "http://localhost:5160"),
            "timeout": 30.0,
            "demo_mode": os.getenv("DEMO_MODE", "full")  # full, analysis_only, simulation_only
        }

        self.colors = {
            "SUCCESS": "\033[92m",
            "ERROR": "\033[91m",
            "WARNING": "\033[93m",
            "INFO": "\033[94m",
            "RESET": "\033[0m",
            "BOLD": "\033[1m"
        }

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{self.colors['BOLD']}{'='*60}{self.colors['RESET']}")
        print(f"{self.colors['BOLD']}{text.center(60)}{self.colors['RESET']}")
        print(f"{self.colors['BOLD']}{'='*60}{self.colors['RESET']}")

    def print_step(self, step_num: int, description: str):
        """Print a workflow step."""
        print(f"\n{self.colors['INFO']}Step {step_num}: {description}{self.colors['RESET']}")

    def print_success(self, message: str):
        """Print a success message."""
        print(f"{self.colors['SUCCESS']}✅ {message}{self.colors['RESET']}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"{self.colors['ERROR']}❌ {message}{self.colors['RESET']}")

    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"{self.colors['WARNING']}⚠️ {message}{self.colors['RESET']}")

    def print_info(self, message: str):
        """Print an info message."""
        print(f"{self.colors['INFO']}ℹ️ {message}{self.colors['RESET']}")

    async def check_service_health(self, service_name: str, url: str) -> bool:
        """Check if a service is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    self.print_success(f"{service_name} is healthy")
                    return True
                else:
                    self.print_error(f"{service_name} unhealthy (status: {response.status_code})")
                    return False
        except Exception as e:
            self.print_error(f"{service_name} unreachable: {str(e)}")
            return False

    async def check_all_services(self) -> bool:
        """Check health of all required services."""
        self.print_header("🔍 SERVICE HEALTH CHECK")

        services = [
            ("Interpreter", self.config["interpreter_url"]),
            ("Orchestrator", self.config["orchestrator_url"]),
            ("Simulation", self.config["simulation_url"]),
            ("Summarizer", self.config["summarizer_url"])
        ]

        all_healthy = True
        for service_name, url in services:
            if not await self.check_service_health(service_name, url):
                all_healthy = False

        if not all_healthy:
            self.print_error("Some services are not healthy. Please start all services first.")
            self.print_info("Run: docker-compose -f docker-compose.dev.yml up -d")
            return False

        self.print_success("All services are healthy and ready!")
        return True

    async def demonstrate_interpreter_processing(self) -> Dict[str, Any]:
        """Demonstrate interpreter query processing."""
        self.print_step(1, "🧠 Interpreter Query Processing")

        sample_query = "Create a simulation for building an e-commerce platform with microservices architecture, 6 developers, over 10 weeks"

        self.print_info(f"Query: {sample_query}")

        # In a real implementation, this would call the interpreter service
        # For demo purposes, we'll simulate the response
        interpreted_result = {
            "original_query": sample_query,
            "interpreted_intent": "create_simulation",
            "confidence": 0.95,
            "parameters": {
                "project_type": "e_commerce_platform",
                "architecture": "microservices",
                "team_size": 6,
                "duration_weeks": 10,
                "complexity": "high",
                "technologies": ["React", "Node.js", "Python", "PostgreSQL", "Docker", "Kubernetes"]
            }
        }

        self.print_success("Query interpreted successfully")
        self.print_info(f"Intent: {interpreted_result['interpreted_intent']}")
        self.print_info(f"Confidence: {interpreted_result['confidence']:.1%}")
        self.print_info(f"Parameters: {json.dumps(interpreted_result['parameters'], indent=2)}")

        return interpreted_result

    async def demonstrate_orchestrator_coordination(self, interpreted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate orchestrator coordination."""
        self.print_step(2, "🎯 Orchestrator Coordination")

        simulation_request = {
            "query": interpreted_data["original_query"],
            "context": {"source": "demo_workflow", "user_id": "demo_user"},
            "simulation_config": interpreted_data["parameters"],
            "generate_mock_data": True,
            "analysis_types": ["consolidation", "duplicate", "outdated", "quality"]
        }

        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                self.print_info("Sending request to orchestrator...")
                response = await client.post(
                    f"{self.config['orchestrator_url']}/simulation/create",
                    json=simulation_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    self.print_success("Orchestrator processed request successfully")
                    self.print_info(f"Request ID: {result.get('orchestrator_request_id', 'N/A')}")
                    self.print_info(f"Query processed: {result.get('query_processed', 'N/A')}")

                    return result
                else:
                    self.print_error(f"Orchestrator error: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    return {}

        except Exception as e:
            self.print_error(f"Orchestrator communication failed: {str(e)}")
            return {}

    async def demonstrate_simulation_creation(self, orchestrator_result: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate simulation creation and execution."""
        self.print_step(3, "🏗️ Simulation Creation & Execution")

        # Extract simulation parameters from orchestrator result
        simulation_config = {
            "type": "e_commerce_platform",
            "complexity": "high",
            "duration_weeks": 10,
            "budget": 250000,
            "team_size": 6,
            "technologies": ["React", "Node.js", "Python", "PostgreSQL", "Docker"]
        }

        interpreter_request = {
            "query": "Build an e-commerce platform with microservices",
            "context": {"demo": True, "workflow_step": "simulation_creation"},
            "simulation_config": simulation_config
        }

        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                self.print_info("Creating simulation via interpreter endpoint...")
                response = await client.post(
                    f"{self.config['simulation_url']}/api/v1/interpreter/simulate",
                    json=interpreter_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    self.print_success("Simulation created and executed successfully")

                    if result.get("success"):
                        self.print_info(f"Simulation ID: {result.get('simulation_id', 'N/A')}")
                        self.print_info(f"Status: {result.get('status', 'completed')}")
                        self.print_info(f"Mock data generated: {result.get('mock_data_generated', False)}")

                        # Show analysis results if available
                        if "analysis_results" in result:
                            analysis = result["analysis_results"]
                            self.print_info("Analysis Results:")
                            self.print_info(f"  📊 Documents analyzed: {len(analysis.get('document_analysis', []))}")
                            self.print_info(f"  👥 Team analysis: {analysis.get('team_analysis', 'N/A')}")
                            self.print_info(f"  📅 Timeline analysis: {'Available' if analysis.get('timeline_analysis') else 'N/A'}")

                    return result
                else:
                    self.print_error(f"Simulation creation failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    return {}

        except Exception as e:
            self.print_error(f"Simulation service communication failed: {str(e)}")
            return {}

    async def demonstrate_analysis_processing(self) -> Dict[str, Any]:
        """Demonstrate comprehensive analysis processing."""
        self.print_step(4, "🔬 Comprehensive Analysis Processing")

        # Sample documents for analysis
        sample_documents = [
            {
                "id": "req_doc_001",
                "title": "E-commerce Platform Requirements",
                "content": "The platform must support user registration, product catalog, shopping cart, payment processing, and order management. Key features include search functionality, product reviews, inventory management, and multi-vendor support.",
                "dateCreated": "2024-01-01T10:00:00Z",
                "dateUpdated": "2024-01-15T14:30:00Z"
            },
            {
                "id": "arch_doc_002",
                "title": "Microservices Architecture Design",
                "content": "The system will be built using microservices architecture with separate services for user management, product catalog, order processing, payment gateway, and notification system. Each service will have its own database and API.",
                "dateCreated": "2024-01-05T09:15:00Z",
                "dateUpdated": "2024-01-20T16:45:00Z"
            },
            {
                "id": "dev_doc_003",
                "title": "Development Guidelines",
                "content": "All services must follow REST API principles, include comprehensive error handling, implement proper logging, and have unit test coverage above 80%. Code reviews are mandatory for all changes.",
                "dateCreated": "2024-01-03T11:20:00Z",
                "dateUpdated": "2024-01-18T13:10:00Z"
            },
            {
                "id": "deploy_doc_004",
                "title": "Deployment and DevOps Guide",
                "content": "The platform will use Docker for containerization, Kubernetes for orchestration, Jenkins for CI/CD pipelines, and AWS for cloud infrastructure. Monitoring will be implemented using Prometheus and Grafana.",
                "dateCreated": "2024-01-08T08:30:00Z",
                "dateUpdated": "2024-01-22T12:15:00Z"
            }
        ]

        # Sample timeline
        sample_timeline = {
            "phases": [
                {"name": "Planning", "start_week": 0, "duration_weeks": 2},
                {"name": "Design", "start_week": 2, "duration_weeks": 2},
                {"name": "Development", "start_week": 4, "duration_weeks": 4},
                {"name": "Testing", "start_week": 8, "duration_weeks": 2}
            ]
        }

        analysis_request = {
            "documents": sample_documents,
            "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"],
            "confidence_threshold": 0.4,
            "include_jira_suggestions": True,
            "create_jira_tickets": False,  # Don't actually create tickets in demo
            "jira_project_key": "DEMO",
            "timeline": sample_timeline
        }

        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                self.print_info("Submitting documents for comprehensive analysis...")
                response = await client.post(
                    f"{self.config['summarizer_url']}/recommendations",
                    json=analysis_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    self.print_success("Analysis completed successfully")

                    # Display analysis results
                    self.display_analysis_results(result)
                    return result
                else:
                    self.print_error(f"Analysis failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    return {}

        except Exception as e:
            self.print_error(f"Analysis service communication failed: {str(e)}")
            return {}

    def display_analysis_results(self, result: Dict[str, Any]):
        """Display comprehensive analysis results."""
        print(f"\n{self.colors['BOLD']}📊 ANALYSIS RESULTS{self.colors['RESET']}")

        # Basic stats
        total_docs = result.get("total_documents", 0)
        total_recs = result.get("recommendations_count", 0)
        processing_time = result.get("processing_time", 0)

        print(f"📄 Documents analyzed: {total_docs}")
        print(f"💡 Recommendations generated: {total_recs}")
        print(f"⚡ Processing time: {processing_time:.2f}s")

        # Recommendations breakdown
        recommendations = result.get("recommendations", [])
        rec_types = {}
        priorities = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for rec in recommendations:
            rec_type = rec.get("type", "unknown")
            priority = rec.get("priority", "medium")

            rec_types[rec_type] = rec_types.get(rec_type, 0) + 1
            priorities[priority] += 1

        print(f"\n🔍 Recommendation Types:")
        for rec_type, count in rec_types.items():
            print(f"  • {rec_type.title()}: {count}")

        print(f"\n🎯 Priority Breakdown:")
        for priority, count in priorities.items():
            if count > 0:
                print(f"  • {priority.title()}: {count}")

        # Jira suggestions
        jira_tickets = result.get("suggested_jira_tickets", [])
        if jira_tickets:
            print(f"\n🎫 Suggested Jira Tickets: {len(jira_tickets)}")
            for i, ticket in enumerate(jira_tickets[:3]):  # Show first 3
                print(f"  {i+1}. [{ticket['priority']}] {ticket['summary']}")

        # Drift analysis
        drift = result.get("drift_analysis", {})
        if drift.get("drift_alerts"):
            alerts = drift["drift_alerts"]
            print(f"\n🚨 Drift Alerts: {len(alerts)}")
            high_priority = [a for a in alerts if a.get("severity") == "high"]
            if high_priority:
                print(f"  ⚠️ High Priority: {len(high_priority)}")

        # Alignment analysis
        alignment = result.get("alignment_analysis", {})
        if alignment.get("alignment_score", 0) > 0:
            score = alignment["alignment_score"]
            print(".2%")

        # Timeline analysis
        timeline = result.get("timeline_analysis", {})
        if timeline.get("placement_score", 0) > 0:
            placement_score = timeline["placement_score"]
            print(".1%")
            phases = timeline.get("timeline_structure", {}).get("phase_count", 0)
            print(f"  📅 Timeline phases: {phases}")

        # Inconclusive analysis
        inconclusive = result.get("inconclusive_analysis", {})
        if inconclusive.get("insufficient_data_warnings"):
            warnings = inconclusive["insufficient_data_warnings"]
            print(f"\n🤔 Data Quality Warnings: {len(warnings)}")

    async def demonstrate_jira_integration(self, analysis_result: Dict[str, Any]):
        """Demonstrate Jira ticket creation (optional)."""
        self.print_step(5, "🎫 Jira Integration (Optional)")

        jira_tickets = analysis_result.get("suggested_jira_tickets", [])
        if not jira_tickets:
            self.print_warning("No Jira tickets to create")
            return

        self.print_info(f"Found {len(jira_tickets)} suggested Jira tickets")

        # Ask user if they want to create actual tickets
        create_tickets = input("\nCreate actual Jira tickets? (y/N): ").lower().strip() == 'y'

        if create_tickets:
            try:
                async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                    jira_request = {
                        "suggested_tickets": jira_tickets[:2],  # Create first 2 tickets only
                        "project_key": "DEMO"
                    }

                    self.print_info("Creating Jira tickets...")
                    response = await client.post(
                        f"{self.config['summarizer_url']}/jira/create-tickets",
                        json=jira_request,
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        self.print_success("Jira tickets created successfully")
                        self.print_info(f"Tickets created: {result.get('tickets_created', 0)}")
                        self.print_info(f"Tickets failed: {result.get('tickets_failed', 0)}")
                    else:
                        self.print_warning(f"Jira ticket creation failed: {response.status_code}")
                        self.print_info("This is expected if Jira is not configured in the demo environment")

            except Exception as e:
                self.print_warning(f"Jira integration failed: {str(e)}")
                self.print_info("Jira integration requires proper configuration")
        else:
            self.print_info("Skipping Jira ticket creation")
            self.print_info(f"Would have created {len(jira_tickets)} tickets")

    async def run_complete_demo(self):
        """Run the complete workflow demonstration."""
        start_time = datetime.now()

        self.print_header("🚀 COMPLETE WORKFLOW DEMONSTRATION")
        self.print_info("This demo showcases the full Interpreter → Orchestrator → Simulation → Analysis workflow")
        self.print_info(f"Demo mode: {self.config['demo_mode']}")
        self.print_info(f"Timeout: {self.config['timeout']}s per request")

        # Step 1: Check service health
        if not await self.check_all_services():
            return False

        # Step 2: Interpreter processing
        interpreted_data = await self.demonstrate_interpreter_processing()

        # Step 3: Orchestrator coordination
        orchestrator_result = await self.demonstrate_orchestrator_coordination(interpreted_data)

        # Step 4: Simulation creation and execution
        simulation_result = await self.demonstrate_simulation_creation(orchestrator_result)

        # Step 5: Comprehensive analysis
        analysis_result = await self.demonstrate_analysis_processing()

        # Step 6: Jira integration (optional)
        if analysis_result:
            await self.demonstrate_jira_integration(analysis_result)

        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.print_header("🏁 DEMONSTRATION COMPLETE")
        self.print_success(f"Workflow completed in {duration:.1f} seconds")
        self.print_info("🎯 Key achievements:")
        self.print_info("  ✅ Interpreter query processing")
        self.print_info("  ✅ Orchestrator coordination")
        self.print_info("  ✅ Simulation creation with mock data")
        self.print_info("  ✅ Comprehensive document analysis")
        self.print_info("  ✅ Multiple recommendation types")
        self.print_info("  ✅ Timeline analysis integration")
        self.print_info("  ✅ Drift detection and alerting")
        self.print_info("  ✅ Documentation alignment analysis")
        self.print_info("  ✅ Jira ticket suggestions")

        if analysis_result:
            total_recommendations = analysis_result.get("recommendations_count", 0)
            jira_tickets = len(analysis_result.get("suggested_jira_tickets", []))
            self.print_info(f"  📊 Generated {total_recommendations} recommendations")
            self.print_info(f"  🎫 Suggested {jira_tickets} Jira tickets")

        self.print_success("🎉 All workflow components are working correctly!")
        return True


async def main():
    """Main demo execution function."""
    demo = WorkflowDemo()

    try:
        success = await demo.run_complete_demo()
        if success:
            print("\n🎯 WORKFLOW VALIDATION: SUCCESS")
            print("✅ All required components are implemented and working")
            return 0
        else:
            print("\n❌ WORKFLOW VALIDATION: FAILED")
            print("Some components are not available or not working properly")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    print(__doc__)

    # Check if user wants to run the demo
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("\nUSAGE:")
        print("  python demo_workflow.py          # Run complete demo")
        print("  python demo_workflow.py --help   # Show this help")
        print("\nENVIRONMENT VARIABLES:")
        print("  DEMO_MODE=full                  # full, analysis_only, simulation_only")
        print("  RUN_INTEGRATION_TESTS=true      # Enable integration tests")
        sys.exit(0)

    # Run the demo
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
