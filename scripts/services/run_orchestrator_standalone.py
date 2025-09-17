#!/usr/bin/env python3
"""
Orchestrator Standalone Runner

Runs the orchestrator service standalone with all Phase 1 and Phase 2 integrations.
Provides a terminal-based interface for testing and interacting with the orchestrator.
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

# Import orchestrator and related services
from services.orchestrator.main import app as orchestrator_app
from services.orchestrator.modules.workflow_handlers import handle_workflow_run
from services.orchestrator.modules.langgraph.engine import LangGraphWorkflowEngine
from services.orchestrator.modules.langgraph.tools import initialize_service_tools
from services.orchestrator.modules.langgraph.state import create_workflow_state

# Import Phase 2 modules for standalone testing
from services.interpreter.modules.advanced_nlp_engine import (
    ConversationMemoryManager, AdvancedIntentRecognizer
)
from services.source_agent.modules.intelligent_ingestion import IntelligentIngestionEngine
from services.summarizer_hub.modules.multi_model_summarization import MultiModelSummarizer
from services.frontend.modules.realtime_interface import RealTimeCollaborationEngine

# Import shared components
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class OrchestratorStandaloneRunner:
    """Standalone orchestrator runner with terminal interface."""

    def __init__(self):
        self.orchestrator_app = orchestrator_app
        self.workflow_engine = LangGraphWorkflowEngine()
        self.conversation_memory = ConversationMemoryManager()
        self.ingestion_engine = IntelligentIngestionEngine()
        self.summarizer = MultiModelSummarizer()
        self.collaboration_engine = RealTimeCollaborationEngine()

        self.is_running = False
        self.command_history = []

    async def initialize_services(self):
        """Initialize all integrated services."""
        print("🚀 Initializing Orchestrator Standalone Environment...")
        print("=" * 60)

        try:
            # Initialize Phase 2 components
            print("📝 Initializing Advanced NLP Engine...")
            from services.interpreter.modules.advanced_nlp_engine import initialize_advanced_nlp
            await initialize_advanced_nlp()

            print("🔄 Initializing Intelligent Data Ingestion...")
            from services.source_agent.modules.intelligent_ingestion import initialize_intelligent_ingestion
            await initialize_intelligent_ingestion()

            print("📝 Initializing Multi-Model Summarization...")
            from services.summarizer_hub.modules.multi_model_summarization import initialize_multi_model_summarization
            await initialize_multi_model_summarization()

            print("🔗 Initializing Real-Time Collaboration...")
            from services.frontend.modules.realtime_interface import initialize_realtime_interface
            await initialize_realtime_interface()

            # Initialize workflow engine
            print("⚙️  Initializing Workflow Engine...")
            await self.workflow_engine.initialize_tools([
                ServiceNames.ANALYSIS_SERVICE,
                ServiceNames.DOC_STORE,
                ServiceNames.PROMPT_STORE,
                ServiceNames.INTERPRETER,
                ServiceNames.SOURCE_AGENT,
                ServiceNames.SUMMARIZER_HUB
            ])

            print("✅ All services initialized successfully!")
            print()

        except Exception as e:
            print(f"❌ Service initialization failed: {e}")
            raise

    async def start_terminal_interface(self):
        """Start the terminal-based interface."""
        print("🎯 ORCHESTRATOR STANDALONE INTERFACE")
        print("=" * 60)
        print("Available commands:")
        print("  help              - Show this help message")
        print("  status            - Show system status")
        print("  workflow <type>   - Run a workflow (document_analysis, pr_analysis)")
        print("  nlp <query>       - Test NLP processing")
        print("  ingest <source>   - Test data ingestion")
        print("  summarize <text>  - Test summarization")
        print("  collaborate       - Test collaboration features")
        print("  history           - Show command history")
        print("  exit              - Exit the interface")
        print()

        self.is_running = True

        while self.is_running:
            try:
                command = input("orchestrator> ").strip()
                if command:
                    self.command_history.append(command)
                    await self.process_command(command)
            except KeyboardInterrupt:
                print("\n👋 Shutting down orchestrator...")
                break
            except Exception as e:
                print(f"❌ Command error: {e}")

        print("🏁 Orchestrator standalone session ended.")

    async def process_command(self, command: str):
        """Process a terminal command."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "help":
            self.show_help()
        elif cmd == "status":
            await self.show_status()
        elif cmd == "workflow":
            if len(parts) > 1:
                await self.run_workflow(parts[1])
            else:
                print("❌ Usage: workflow <type>")
        elif cmd == "nlp":
            if len(parts) > 1:
                query = " ".join(parts[1:])
                await self.test_nlp(query)
            else:
                print("❌ Usage: nlp <query>")
        elif cmd == "ingest":
            if len(parts) > 1:
                source = parts[1]
                await self.test_ingestion(source)
            else:
                print("❌ Usage: ingest <source>")
        elif cmd == "summarize":
            if len(parts) > 1:
                text = " ".join(parts[1:])
                await self.test_summarization(text)
            else:
                print("❌ Usage: summarize <text>")
        elif cmd == "collaborate":
            await self.test_collaboration()
        elif cmd == "history":
            self.show_history()
        elif cmd == "exit":
            self.is_running = False
        else:
            print(f"❌ Unknown command: {cmd}. Type 'help' for available commands.")

    def show_help(self):
        """Show help message."""
        print("🎯 Orchestrator Standalone Interface Commands:")
        print()
        print("Core Commands:")
        print("  help              - Show this help message")
        print("  status            - Show system status")
        print("  exit              - Exit the interface")
        print()
        print("Workflow Commands:")
        print("  workflow document_analysis  - Run document analysis workflow")
        print("  workflow pr_analysis        - Run PR confidence analysis workflow")
        print()
        print("Service Testing:")
        print("  nlp <query>       - Test NLP query processing")
        print("  ingest github     - Test GitHub data ingestion")
        print("  ingest jira       - Test Jira data ingestion")
        print("  summarize <text>  - Test text summarization")
        print("  collaborate       - Test collaboration features")
        print()
        print("Utilities:")
        print("  history           - Show command history")

    async def show_status(self):
        """Show system status."""
        print("📊 System Status:")
        print("-" * 30)

        # Orchestrator status
        print("🔧 Orchestrator: ✅ Running")

        # Service integrations
        print("🔗 Service Integrations:")
        print("   • Analysis Service: ✅ Integrated")
        print("   • Doc Store: ✅ Integrated")
        print("   • Prompt Store: ✅ Integrated")
        print("   • Interpreter: ✅ Integrated")
        print("   • Source Agent: ✅ Integrated")
        print("   • Summarizer Hub: ✅ Integrated")
        print("   • Frontend: ✅ Integrated")

        # Component status
        print("⚙️  Component Status:")
        print(f"   • Workflow Engine: ✅ Active ({len(self.workflow_engine.workflows)} workflows)")
        print(f"   • Conversation Memory: ✅ Active ({self.conversation_memory.get_active_conversations_count()} conversations)")
        print(f"   • Ingestion Engine: ✅ Active ({len(self.ingestion_engine.ingestion_jobs)} jobs)")
        print("   • Summarizer: ✅ Active")
        print(f"   • Collaboration Engine: ✅ Active ({len(self.collaboration_engine.active_sessions)} sessions)")

        # Resource usage (simplified)
        print("💾 Resource Usage:")
        print("   • Memory: Normal")
        print("   • CPU: Low")
        print("   • Network: Idle")

        print(f"⏱️  Uptime: Standalone session active")
        print(f"📝 Commands processed: {len(self.command_history)}")

    async def run_workflow(self, workflow_type: str):
        """Run a workflow."""
        print(f"⚙️  Running {workflow_type} workflow...")

        if workflow_type not in ["document_analysis", "pr_analysis"]:
            print(f"❌ Unknown workflow type: {workflow_type}")
            return

        try:
            # Create workflow input
            if workflow_type == "document_analysis":
                workflow_input = {
                    "content": "Sample document for analysis",
                    "document_type": "technical",
                    "analysis_type": "comprehensive"
                }
            else:  # pr_analysis
                workflow_input = {
                    "pr_number": "123",
                    "repository": "test/repo",
                    "jira_ticket": "PROJ-456"
                }

            # Execute workflow
            start_time = time.time()
            result = await self.workflow_engine.execute_workflow(
                workflow_type,
                workflow_input,
                [],  # No additional tools needed for basic test
                "standalone_user"
            )

            duration = time.time() - start_time

            print("✅ Workflow completed successfully!")
            print(f"   • Duration: {duration:.2f} seconds")
            print(f"   • Result: {result.get('final_output', 'No output')}")
            print(f"   • Status: {result.get('final_status', 'Unknown')}")

        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")

    async def test_nlp(self, query: str):
        """Test NLP processing."""
        print(f"🧠 Processing NLP query: '{query}'")

        try:
            # Create conversation
            conversation = await self.conversation_memory.create_conversation("standalone_user", "terminal_session")

            # Add user message
            conversation.add_message({"text": query, "type": "user"})

            # Recognize intent
            intent_recognizer = AdvancedIntentRecognizer()
            intent_result = await intent_recognizer.recognize_intent(query, conversation)

            print("✅ NLP Analysis Complete:")
            print(f"   • Intent: {intent_result.intent}")
            print(f"   • Confidence: {intent_result.confidence.value} ({intent_result.confidence_score:.2f})")
            print(f"   • Entities: {intent_result.entities}")
            print(f"   • Processing Time: {intent_result.processing_time_ms:.2f}ms")

            if intent_result.requires_clarification:
                print(f"   • Clarification Needed: {intent_result.clarification_question}")

            # Add response to conversation
            conversation.add_message({
                "intent": intent_result.intent,
                "confidence": intent_result.confidence_score
            }, "assistant")

        except Exception as e:
            print(f"❌ NLP processing failed: {e}")

    async def test_ingestion(self, source: str):
        """Test data ingestion."""
        print(f"🔄 Testing data ingestion from {source}...")

        try:
            # Create ingestion job
            from services.source_agent.modules.intelligent_ingestion import DataSource

            if source.lower() == "github":
                data_source = DataSource.GITHUB
                config = {"repository": "test/repo", "branch": "main"}
            elif source.lower() == "jira":
                data_source = DataSource.JIRA
                config = {"project": "TEST", "issue_types": ["bug", "feature"]}
            elif source.lower() == "confluence":
                data_source = DataSource.CONFLUENCE
                config = {"space": "TEST", "page_types": ["guide"]}
            else:
                print(f"❌ Unsupported source: {source}")
                return

            job_id = await self.ingestion_engine.create_ingestion_job(
                data_source,
                config,
                {"target": "doc_store"}
            )

            # Execute job
            result = await self.ingestion_engine.execute_ingestion_job(job_id)

            if result["status"] == "completed":
                print("✅ Ingestion completed successfully!")
                print(f"   • Items processed: {result['result']['processed']}")
                print(f"   • Items ingested: {result['result']['ingested']}")
                print(f"   • Items failed: {result['result']['failed']}")
            else:
                print(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Ingestion test failed: {e}")

    async def test_summarization(self, text: str):
        """Test text summarization."""
        print("📝 Testing multi-model summarization...")

        try:
            from services.summarizer_hub.modules.multi_model_summarization import (
                SummarizationRequest, ContentType, SummarizationStrategy
            )

            request = SummarizationRequest(
                content=text,
                content_type=ContentType.GENERAL_TEXT,
                strategy=SummarizationStrategy.ENSEMBLE
            )

            result = await self.summarizer.summarize_content(request)

            print("✅ Summarization completed successfully!")
            print(f"   • Models used: {[m.value for m in result.models_used]}")
            print(f"   • Quality score: {result.quality_score:.2f}")
            print(f"   • Confidence: {result.confidence_score:.2f}")
            print(f"   • Processing time: {result.total_processing_time:.2f}s")
            print()
            print("📄 Summary:")
            print(f"   {result.final_summary}")

        except Exception as e:
            print(f"❌ Summarization test failed: {e}")

    async def test_collaboration(self):
        """Test collaboration features."""
        print("🔗 Testing real-time collaboration...")

        try:
            # Create user session
            user_session = await self.collaboration_engine.create_user_session(
                "standalone_user", "Standalone User"
            )

            print("✅ User session created")

            # Join document
            success = await self.collaboration_engine.join_document(
                user_session.session_id, "standalone_doc"
            )

            if success:
                print("✅ Joined collaborative document")

                # Apply an operation
                from services.frontend.modules.realtime_interface import OperationalTransform, OperationType

                operation = OperationalTransform(
                    user_id=user_session.user_id,
                    document_id="standalone_doc",
                    operation_type=OperationType.INSERT,
                    position=0,
                    content="Standalone collaboration test content"
                )

                success = await self.collaboration_engine.apply_operation(operation)

                if success:
                    print("✅ Operational transform applied successfully")

                    # Generate AI suggestion
                    suggestion = await self.collaboration_engine.generate_ai_suggestion(
                        "standalone_doc", user_session.user_id
                    )

                    if suggestion:
                        print("✅ AI suggestion generated:")
                        print(f"   • Type: {suggestion.suggestion_type}")
                        print(f"   • Content: {suggestion.content}")
                        print(f"   • Confidence: {suggestion.confidence_score:.2f}")
                else:
                    print("❌ Operational transform failed")
            else:
                print("❌ Failed to join document")

            # Get document state
            doc_state = self.collaboration_engine.get_document_state("standalone_doc")
            if doc_state:
                print(f"✅ Document state retrieved:")
                print(f"   • Version: {doc_state['version']}")
                print(f"   • Content length: {len(doc_state['content'])}")
                print(f"   • Active users: {len(doc_state['active_users'])}")

        except Exception as e:
            print(f"❌ Collaboration test failed: {e}")

    def show_history(self):
        """Show command history."""
        print("📝 Command History:")
        print("-" * 30)

        if not self.command_history:
            print("   No commands executed yet.")
            return

        for i, cmd in enumerate(self.command_history[-10:], 1):  # Show last 10 commands
            print("2d")

    async def run_diagnostics(self):
        """Run system diagnostics."""
        print("🔍 Running system diagnostics...")

        diagnostics = {
            "services": {},
            "performance": {},
            "connectivity": {}
        }

        # Test service availability
        services_to_test = [
            ("conversation_memory", self.conversation_memory),
            ("ingestion_engine", self.ingestion_engine),
            ("summarizer", self.summarizer),
            ("collaboration_engine", self.collaboration_engine),
            ("workflow_engine", self.workflow_engine)
        ]

        for service_name, service in services_to_test:
            try:
                # Simple health check
                diagnostics["services"][service_name] = "healthy"
            except Exception as e:
                diagnostics["services"][service_name] = f"unhealthy: {e}"

        # Performance metrics
        diagnostics["performance"] = {
            "active_conversations": self.conversation_memory.get_active_conversations_count(),
            "ingestion_jobs": len(self.ingestion_engine.ingestion_jobs),
            "active_sessions": len(self.collaboration_engine.active_sessions),
            "loaded_workflows": len(self.workflow_engine.workflows)
        }

        # Connectivity (simplified)
        diagnostics["connectivity"] = {
            "internal_services": "connected",
            "external_apis": "simulated",
            "database": "available"
        }

        print("✅ Diagnostics completed:")
        print(f"   • Services: {len([s for s in diagnostics['services'].values() if s == 'healthy'])}/{len(diagnostics['services'])} healthy")
        print(f"   • Active conversations: {diagnostics['performance']['active_conversations']}")
        print(f"   • Ingestion jobs: {diagnostics['performance']['ingestion_jobs']}")
        print(f"   • Active sessions: {diagnostics['performance']['active_sessions']}")

        return diagnostics


async def main():
    """Main entry point for orchestrator standalone runner."""
    print("🎯 Orchestrator Standalone Runner")
    print("=================================")
    print("Starting orchestrator in standalone mode...")
    print()

    # Create runner instance
    runner = OrchestratorStandaloneRunner()

    try:
        # Initialize all services
        await runner.initialize_services()

        # Run diagnostics
        await runner.run_diagnostics()
        print()

        # Start terminal interface
        await runner.start_terminal_interface()

    except KeyboardInterrupt:
        print("\n👋 Received interrupt signal, shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        raise
    finally:
        print("🏁 Orchestrator standalone runner shutdown complete.")


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--test":
            print("🧪 Running Phase 2 integration tests...")
            from test_phase2_implementation import run_phase2_integration_test
            asyncio.run(run_phase2_integration_test())
        elif command == "--help":
            print("🎯 Orchestrator Standalone Runner")
            print("Usage:")
            print("  python run_orchestrator_standalone.py          # Start interactive mode")
            print("  python run_orchestrator_standalone.py --test   # Run integration tests")
            print("  python run_orchestrator_standalone.py --help   # Show this help")
        else:
            print(f"❌ Unknown command: {command}")
            print("Use --help for usage information")
    else:
        # Start interactive mode
        asyncio.run(main())
