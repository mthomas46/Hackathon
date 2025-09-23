"""Unit Tests for Interactive Features in CLI Service.

This module tests interactive CLI capabilities including:
- Interactive session management
- Command completion and suggestions
- Real-time help and guidance
- User input validation and correction
- Session state persistence
- Interactive workflow building

Tests cover the complete interactive user experience within the CLI service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from prompt_toolkit import PromptSession
from prompt_toolkit.input import create_input
from prompt_toolkit.output import create_output

from modules.interactive_overlay import InteractiveOverlay
from modules.managers.workflow_manager import WorkflowManager
from modules.models import CommandResult


class TestInteractiveSession:
    """Test Interactive Session functionality."""

    @pytest.fixture
    def interactive_overlay(self, mock_service_adapter):
        """Create interactive overlay instance."""
        return InteractiveOverlay(service_adapter=mock_service_adapter)

    def test_interactive_session_initialization(self, interactive_overlay):
        """Test interactive session initialization."""
        session_config = {
            "user": "test_user",
            "working_directory": "/home/user",
            "environment": "development",
            "auto_complete": True,
            "history_enabled": True,
            "session_timeout_minutes": 60
        }

        session_result = interactive_overlay.initialize_session(session_config)

        assert session_result["success"] is True
        assert "session_id" in session_result
        assert session_result["session"]["user"] == "test_user"
        assert session_result["session"]["status"] == "active"
        assert "start_time" in session_result["session"]

    def test_session_state_management(self, interactive_overlay):
        """Test session state management."""
        session_id = str(uuid.uuid4())

        # Set session variables
        variables = {
            "current_workflow": "data_pipeline",
            "last_command": "status",
            "working_directory": "/data",
            "environment": "production"
        }

        state_result = interactive_overlay.update_session_state(session_id, variables)
        assert state_result["success"] is True

        # Retrieve session state
        retrieved_state = interactive_overlay.get_session_state(session_id)
        assert retrieved_state["success"] is True

        for key, value in variables.items():
            assert retrieved_state["state"][key] == value

    def test_session_persistence_and_recovery(self, interactive_overlay):
        """Test session persistence and recovery."""
        session_data = {
            "session_id": str(uuid.uuid4()),
            "user": "test_user",
            "start_time": datetime.now(),
            "command_history": [
                {"command": "help", "timestamp": datetime.now() - timedelta(minutes=10)},
                {"command": "status", "timestamp": datetime.now() - timedelta(minutes=5)}
            ],
            "variables": {
                "current_project": "ai_assistant",
                "debug_mode": True
            }
        }

        # Persist session
        persist_result = interactive_overlay.persist_session(session_data)
        assert persist_result["success"] is True

        # Recover session
        recovery_result = interactive_overlay.recover_session(session_data["session_id"])
        assert recovery_result["success"] is True

        recovered_session = recovery_result["session"]
        assert recovered_session["user"] == session_data["user"]
        assert len(recovered_session["command_history"]) == len(session_data["command_history"])
        assert recovered_session["variables"]["current_project"] == "ai_assistant"

    def test_session_timeout_handling(self, interactive_overlay):
        """Test session timeout handling."""
        session_id = str(uuid.uuid4())
        timeout_minutes = 5

        # Initialize session with timeout
        interactive_overlay.initialize_session({
            "session_id": session_id,
            "user": "test_user",
            "session_timeout_minutes": timeout_minutes
        })

        # Check session status before timeout
        status_result = interactive_overlay.check_session_status(session_id)
        assert status_result["active"] is True
        assert status_result["time_remaining_minutes"] > 0

        # Simulate timeout by advancing time
        with patch('modules.interactive_overlay.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=timeout_minutes + 1)

            status_result = interactive_overlay.check_session_status(session_id)
            assert status_result["active"] is False
            assert "expired" in status_result["status"].lower()

    def test_concurrent_session_management(self, interactive_overlay):
        """Test concurrent session management."""
        # Create multiple sessions
        session_ids = []
        for i in range(5):
            session_config = {
                "user": f"user_{i}",
                "environment": "test",
                "session_timeout_minutes": 30
            }

            session_result = interactive_overlay.initialize_session(session_config)
            assert session_result["success"] is True
            session_ids.append(session_result["session_id"])

        # Verify all sessions are active and independent
        for session_id in session_ids:
            status_result = interactive_overlay.check_session_status(session_id)
            assert status_result["active"] is True

        # Verify session isolation (one user's state doesn't affect others)
        test_session_id = session_ids[0]
        interactive_overlay.update_session_state(test_session_id, {"test_var": "test_value"})

        for session_id in session_ids[1:]:
            state_result = interactive_overlay.get_session_state(session_id)
            assert "test_var" not in state_result["state"]


class TestCommandCompletion:
    """Test Command Completion functionality."""

    @pytest.fixture
    def command_completer(self):
        """Create command completer instance."""
        return InteractiveOverlay()

    def test_basic_command_completion(self, command_completer):
        """Test basic command completion."""
        available_commands = ["status", "workflow", "service", "help", "exit"]

        # Test partial completion
        completions = command_completer.get_command_completions("stat", available_commands)
        assert "status" in completions

        completions = command_completer.get_command_completions("work", available_commands)
        assert "workflow" in completions

        # Test no matches
        completions = command_completer.get_command_completions("xyz", available_commands)
        assert len(completions) == 0

    def test_context_aware_completion(self, command_completer):
        """Test context-aware command completion."""
        context_commands = {
            "workflow": ["create", "list", "execute", "delete"],
            "service": ["start", "stop", "restart", "status"],
            "config": ["show", "set", "get", "list"]
        }

        # Test subcommand completion
        workflow_completions = command_completer.get_context_completions(
            "workflow ", context_commands
        )
        assert "create" in workflow_completions
        assert "list" in workflow_completions

        service_completions = command_completer.get_context_completions(
            "service ", context_commands
        )
        assert "start" in service_completions
        assert "status" in service_completions

    def test_argument_completion(self, command_completer):
        """Test argument completion."""
        argument_suggestions = {
            "--service": ["interpreter", "orchestrator", "doc_store", "all"],
            "--format": ["json", "xml", "table", "text"],
            "--environment": ["development", "staging", "production"]
        }

        # Test service argument completion
        service_completions = command_completer.get_argument_completions(
            "status --service ", argument_suggestions
        )
        assert "interpreter" in service_completions
        assert "all" in service_completions

        # Test format argument completion
        format_completions = command_completer.get_argument_completions(
            "workflow list --format ", argument_suggestions
        )
        assert "json" in format_completions
        assert "table" in format_completions

    def test_dynamic_completion_from_history(self, command_completer):
        """Test dynamic completion based on command history."""
        command_history = [
            "status --service interpreter",
            "workflow create --name data_pipeline",
            "service restart orchestrator",
            "config set environment development",
            "workflow execute --id wf_123"
        ]

        # Should suggest previously used arguments
        status_completions = command_completer.get_history_based_completions(
            "status --service ", command_history
        )
        assert "interpreter" in status_completions

        workflow_completions = command_completer.get_history_based_completions(
            "workflow create --name ", command_history
        )
        assert "data_pipeline" in workflow_completions

    def test_completion_ranking_and_prioritization(self, command_completer):
        """Test completion ranking and prioritization."""
        completion_candidates = [
            {"text": "status", "frequency": 50, "recency": 1},  # Most recent, high frequency
            {"text": "start", "frequency": 30, "recency": 2},
            {"text": "stop", "frequency": 40, "recency": 10},  # High frequency, less recent
            {"text": "restart", "frequency": 10, "recency": 3}  # Low frequency, recent
        ]

        ranked_completions = command_completer.rank_completions(completion_candidates, "st")

        # Should rank by relevance, frequency, and recency
        assert len(ranked_completions) == 3  # All match "st"
        assert ranked_completions[0]["text"] == "status"  # Best match
        assert ranked_completions[1]["text"] == "start"   # Second best
        assert ranked_completions[2]["text"] == "stop"    # Third

    def test_completion_with_typo_correction(self, command_completer):
        """Test completion with typo correction."""
        valid_commands = ["status", "workflow", "service", "help"]

        # Test typo correction
        corrections = command_completer.get_typo_corrections("statas", valid_commands)
        assert "status" in corrections

        corrections = command_completer.get_typo_corrections("workflor", valid_commands)
        assert "workflow" in corrections

        # Test no correction needed
        corrections = command_completer.get_typo_corrections("status", valid_commands)
        assert len(corrections) == 0 or "status" in corrections


class TestInteractiveHelp:
    """Test Interactive Help functionality."""

    @pytest.fixture
    def help_system(self):
        """Create interactive help system instance."""
        return InteractiveOverlay()

    def test_context_sensitive_help(self, help_system):
        """Test context-sensitive help generation."""
        contexts = [
            {
                "command": "status",
                "context": "basic",
                "expected_topics": ["syntax", "examples", "options"]
            },
            {
                "command": "workflow",
                "context": "create",
                "expected_topics": ["parameters", "templates", "validation"]
            },
            {
                "command": "service",
                "context": "troubleshooting",
                "expected_topics": ["diagnostics", "logs", "restart"]
            }
        ]

        for context_info in contexts:
            help_result = help_system.get_context_help(
                context_info["command"], context_info["context"]
            )

            assert help_result["success"] is True
            help_content = help_result["help"]

            for topic in context_info["expected_topics"]:
                assert topic in help_content.lower() or any(topic in section.lower()
                    for section in help_content.get("sections", []))

    def test_dynamic_help_based_on_user_skill(self, help_system):
        """Test dynamic help adaptation based on user skill level."""
        skill_levels = ["beginner", "intermediate", "advanced"]

        for skill_level in skill_levels:
            help_result = help_system.get_adaptive_help("workflow", skill_level)

            assert help_result["success"] is True
            adaptive_help = help_result["help"]

            assert "skill_level" in adaptive_help
            assert adaptive_help["skill_level"] == skill_level

            # Beginner help should be more verbose with examples
            if skill_level == "beginner":
                assert "examples" in adaptive_help
                assert len(adaptive_help.get("examples", [])) > 0

            # Advanced help should include technical details
            elif skill_level == "advanced":
                assert "technical_details" in adaptive_help
                assert "api_reference" in adaptive_help

    def test_help_with_examples_and_tutorials(self, help_system):
        """Test help system with examples and tutorials."""
        help_request = {
            "topic": "workflow_creation",
            "include_examples": True,
            "include_tutorial": True,
            "difficulty": "intermediate"
        }

        help_result = help_system.get_comprehensive_help(help_request)

        assert help_result["success"] is True
        comprehensive_help = help_result["help"]

        # Should include examples
        assert "examples" in comprehensive_help
        examples = comprehensive_help["examples"]
        assert len(examples) > 0

        # Each example should have description and command
        for example in examples:
            assert "description" in example
            assert "command" in example
            assert "expected_output" in example

        # Should include tutorial
        assert "tutorial" in comprehensive_help
        tutorial = comprehensive_help["tutorial"]
        assert "steps" in tutorial
        assert len(tutorial["steps"]) > 0

        # Should be appropriate difficulty
        assert comprehensive_help["difficulty"] == "intermediate"

    def test_help_search_and_discovery(self, help_system):
        """Test help search and discovery functionality."""
        help_database = [
            {"topic": "workflow_basics", "content": "Basic workflow operations"},
            {"topic": "advanced_workflows", "content": "Complex workflow patterns"},
            {"topic": "service_management", "content": "Managing services"},
            {"topic": "troubleshooting", "content": "Common issues and solutions"}
        ]

        # Test keyword search
        search_results = help_system.search_help("workflow", help_database)
        assert len(search_results) >= 2  # Should find both workflow topics

        workflow_topics = [r["topic"] for r in search_results]
        assert "workflow_basics" in workflow_topics
        assert "advanced_workflows" in workflow_topics

        # Test category search
        category_results = help_system.search_help_by_category("management", help_database)
        assert len(category_results) >= 1
        assert "service_management" in [r["topic"] for r in category_results]

    def test_help_feedback_and_improvement(self, help_system):
        """Test help system feedback and continuous improvement."""
        help_session = {
            "user": "test_user",
            "topic": "workflow_creation",
            "help_provided": "Basic workflow creation guide",
            "session_duration_seconds": 300
        }

        feedback_data = {
            "helpfulness_rating": 4,  # 1-5 scale
            "understanding_improved": True,
            "additional_topics_needed": ["error_handling", "best_practices"],
            "suggestions": "Add more visual examples"
        }

        feedback_result = help_system.process_help_feedback(help_session, feedback_data)

        assert feedback_result["success"] is True
        assert "feedback_processed" in feedback_result

        # Should update help quality metrics
        assert "quality_metrics_updated" in feedback_result

        # Should identify improvement areas
        if feedback_data["additional_topics_needed"]:
            assert "new_topics_identified" in feedback_result
            assert len(feedback_result["new_topics_identified"]) > 0


class TestInputValidationAndCorrection:
    """Test Input Validation and Correction functionality."""

    @pytest.fixture
    def input_validator(self):
        """Create input validator instance."""
        return InteractiveOverlay()

    def test_command_syntax_validation(self, input_validator):
        """Test command syntax validation."""
        valid_commands = [
            "status --service interpreter",
            "workflow create --name test_workflow",
            "service restart --all",
            "config set environment development"
        ]

        for command in valid_commands:
            validation_result = input_validator.validate_command_syntax(command)
            assert validation_result["valid"] is True

        invalid_commands = [
            "status --service",  # Missing argument
            "workflow create --name",  # Incomplete argument
            "service restart --invalid-flag",  # Invalid flag
            "config set environment",  # Missing value
            "unknown_command --param value"  # Unknown command
        ]

        for command in invalid_commands:
            validation_result = input_validator.validate_command_syntax(command)
            assert validation_result["valid"] is False
            assert "errors" in validation_result

    def test_automatic_input_correction(self, input_validator):
        """Test automatic input correction."""
        correction_test_cases = [
            {
                "input": "statas --servce interpreter",
                "expected_correction": "status --service interpreter",
                "corrections": ["statas -> status", "servce -> service"]
            },
            {
                "input": "workflor creat --nam test",
                "expected_correction": "workflow create --name test",
                "corrections": ["workflor -> workflow", "creat -> create", "nam -> name"]
            },
            {
                "input": "servce restar --all",
                "expected_correction": "service restart --all",
                "corrections": ["servce -> service", "restar -> restart"]
            }
        ]

        for test_case in correction_test_cases:
            correction_result = input_validator.auto_correct_input(test_case["input"])

            assert correction_result["success"] is True
            assert correction_result["corrected_command"] == test_case["expected_correction"]

            applied_corrections = correction_result["applied_corrections"]
            for expected_correction in test_case["corrections"]:
                assert expected_correction in applied_corrections

    def test_input_safety_validation(self, input_validator):
        """Test input safety validation and sanitization."""
        safe_inputs = [
            "status --service interpreter",
            "workflow list",
            "echo 'hello world'"
        ]

        for safe_input in safe_inputs:
            safety_result = input_validator.validate_input_safety(safe_input)
            assert safety_result["safe"] is True

        unsafe_inputs = [
            "rm -rf /",  # Dangerous command
            "sudo su",   # Privilege escalation
            "$(cat /etc/passwd)",  # Command injection
            "`whoami`",  # Command substitution
            "eval 'malicious code'"  # Code evaluation
        ]

        for unsafe_input in unsafe_inputs:
            safety_result = input_validator.validate_input_safety(unsafe_input)
            assert safety_result["safe"] is False
            assert "security_violations" in safety_result
            assert len(safety_result["security_violations"]) > 0

    def test_input_history_and_learning(self, input_validator):
        """Test input history analysis and learning."""
        command_history = [
            "status --service interpreter",
            "status --service orchestrator",
            "status --service doc_store",
            "workflow list",
            "workflow create --name analysis",
            "workflow execute --id wf_123",
            "service restart interpreter"
        ]

        # Analyze patterns
        pattern_result = input_validator.analyze_input_patterns(command_history)

        assert pattern_result["success"] is True
        patterns = pattern_result["patterns"]

        # Should identify frequent commands
        assert "status" in patterns["frequent_commands"]
        assert "workflow" in patterns["frequent_commands"]

        # Should identify common arguments
        assert "--service" in patterns["common_arguments"]

        # Should suggest shortcuts or aliases
        assert "suggestions" in patterns
        suggestions = patterns["suggestions"]

        # Should suggest alias for frequent status command
        status_alias_suggestions = [s for s in suggestions if "status" in s.get("command", "")]
        assert len(status_alias_suggestions) > 0

    def test_multiline_input_handling(self, input_validator):
        """Test multiline input handling and validation."""
        multiline_input = """workflow create --name complex_analysis
--description "Multi-step analysis workflow"
--steps '[
  {"command": "doc-store retrieve", "args": {"id": "doc_123"}},
  {"command": "interpreter analyze", "args": {"content": "{result}"}},
  {"command": "doc-store store", "args": {"content": "{analysis}", "title": "Analysis Result"}}
]'"""

        validation_result = input_validator.validate_multiline_input(multiline_input)

        assert validation_result["success"] is True
        assert validation_result["multiline_valid"] is True
        assert "parsed_command" in validation_result

        parsed = validation_result["parsed_command"]
        assert parsed["command"] == "workflow"
        assert parsed["subcommand"] == "create"
        assert "--name" in str(parsed["args"])
        assert "complex_analysis" in str(parsed["args"])

    def test_input_prediction_and_suggestion(self, input_validator):
        """Test input prediction and intelligent suggestions."""
        context = {
            "current_command": "workflow",
            "partial_input": "workflow cre",
            "user_history": [
                "workflow create --name data_pipeline --template basic",
                "workflow create --name analysis_workflow --template advanced",
                "workflow list --format table"
            ],
            "session_context": {
                "recent_templates": ["basic", "advanced"],
                "preferred_format": "table"
            }
        }

        prediction_result = input_validator.predict_and_suggest_input(context)

        assert prediction_result["success"] is True
        assert "predictions" in prediction_result
        assert "suggestions" in prediction_result

        predictions = prediction_result["predictions"]

        # Should predict command completion
        assert "workflow create" in predictions["command_completion"]

        # Should suggest based on history
        suggestions = prediction_result["suggestions"]
        assert len(suggestions) > 0

        # Should include template suggestions
        template_suggestions = [s for s in suggestions if "template" in s.lower()]
        assert len(template_suggestions) > 0

        # Should include name suggestions from history
        name_suggestions = [s for s in suggestions if "data_pipeline" in s or "analysis_workflow" in s]
        assert len(name_suggestions) > 0


class TestInteractiveWorkflowBuilding:
    """Test Interactive Workflow Building functionality."""

    @pytest.fixture
    def workflow_builder(self, mock_workflow_manager):
        """Create interactive workflow builder instance."""
        return InteractiveOverlay(workflow_manager=mock_workflow_manager)

    def test_guided_workflow_creation(self, workflow_builder):
        """Test guided workflow creation process."""
        creation_session = {
            "user": "test_user",
            "workflow_type": "data_processing",
            "guidance_level": "detailed",
            "expertise_level": "intermediate"
        }

        guidance_result = workflow_builder.start_guided_workflow_creation(creation_session)

        assert guidance_result["success"] is True
        assert "creation_session_id" in guidance_result
        assert "guidance_steps" in guidance_result

        guidance_steps = guidance_result["guidance_steps"]
        assert len(guidance_steps) > 0

        # Should include essential workflow creation steps
        step_types = [step["type"] for step in guidance_steps]
        assert "goal_definition" in step_types
        assert "step_design" in step_types
        assert "validation" in step_types

    def test_workflow_template_selection(self, workflow_builder):
        """Test workflow template selection and customization."""
        available_templates = [
            {
                "id": "data_pipeline",
                "name": "Data Processing Pipeline",
                "category": "data_processing",
                "complexity": "intermediate",
                "description": "Standard ETL pipeline for data processing",
                "tags": ["etl", "data", "processing"]
            },
            {
                "id": "ai_analysis",
                "name": "AI Analysis Workflow",
                "category": "ai_ml",
                "complexity": "advanced",
                "description": "AI-powered content analysis and insights",
                "tags": ["ai", "analysis", "insights"]
            }
        ]

        user_requirements = {
            "task": "analyze customer feedback data",
            "input_type": "text_documents",
            "output_needs": "sentiment_analysis, key_themes",
            "timeline": "real_time"
        }

        selection_result = workflow_builder.recommend_workflow_templates(
            user_requirements, available_templates
        )

        assert selection_result["success"] is True
        assert "recommendations" in selection_result

        recommendations = selection_result["recommendations"]
        assert len(recommendations) > 0

        # Should recommend AI analysis template for sentiment analysis
        ai_recommendations = [r for r in recommendations if r["template"]["id"] == "ai_analysis"]
        assert len(ai_recommendations) > 0

        # Should include match score and reasoning
        best_match = recommendations[0]
        assert "match_score" in best_match
        assert "reasoning" in best_match
        assert best_match["match_score"] > 0.5

    def test_step_by_step_workflow_construction(self, workflow_builder):
        """Test step-by-step workflow construction."""
        workflow_spec = {
            "name": "custom_analysis_workflow",
            "description": "Custom workflow built interactively",
            "max_steps": 5,
            "allow_parallel": True
        }

        construction_result = workflow_builder.initialize_workflow_construction(workflow_spec)

        assert construction_result["success"] is True
        assert "construction_session_id" in construction_result
        assert "available_steps" in construction_result

        available_steps = construction_result["available_steps"]

        # Should provide categorized step options
        step_categories = [step["category"] for step in available_steps]
        expected_categories = ["data_input", "processing", "analysis", "output"]
        for category in expected_categories:
            assert category in step_categories

        # Test adding steps interactively
        step_addition = {
            "construction_session_id": construction_result["construction_session_id"],
            "step": {
                "type": "data_input",
                "command": "doc-store retrieve",
                "name": "Load Document",
                "args": {"document_id": "{input_id}"},
                "order": 1
            }
        }

        addition_result = workflow_builder.add_workflow_step(step_addition)

        assert addition_result["success"] is True
        assert "current_workflow" in addition_result

        current_workflow = addition_result["current_workflow"]
        assert len(current_workflow["steps"]) == 1
        assert current_workflow["steps"][0]["name"] == "Load Document"

    def test_workflow_validation_and_preview(self, workflow_builder):
        """Test workflow validation and preview functionality."""
        test_workflow = {
            "name": "validation_test_workflow",
            "steps": [
                {
                    "id": "load",
                    "command": "doc-store retrieve",
                    "args": {"document_id": "doc_123"},
                    "order": 1
                },
                {
                    "id": "analyze",
                    "command": "interpreter analyze",
                    "args": {"content": "{load.result}"},
                    "depends_on": ["load"],
                    "order": 2
                },
                {
                    "id": "save",
                    "command": "doc-store store",
                    "args": {"content": "{analyze.result}", "title": "Analysis"},
                    "depends_on": ["analyze"],
                    "order": 3
                }
            ]
        }

        validation_result = workflow_builder.validate_and_preview_workflow(test_workflow)

        assert validation_result["success"] is True
        assert "validation_results" in validation_result
        assert "workflow_preview" in validation_result

        validation = validation_result["validation_results"]
        assert validation["structure_valid"] is True
        assert validation["dependencies_resolved"] is True
        assert len(validation["warnings"]) == 0  # Should be valid workflow

        preview = validation_result["workflow_preview"]
        assert "estimated_execution_time" in preview
        assert "resource_requirements" in preview
        assert "execution_plan" in preview

    def test_workflow_suggestions_and_optimization(self, workflow_builder):
        """Test workflow suggestions and optimization during building."""
        partial_workflow = {
            "name": "optimizable_workflow",
            "steps": [
                {"id": "load", "command": "doc-store retrieve", "args": {"document_id": "doc_123"}},
                {"id": "analyze", "command": "interpreter analyze", "args": {"content": "static_content"}},
                {"id": "save", "command": "doc-store store", "args": {"content": "result", "title": "Output"}}
            ]
        }

        optimization_result = workflow_builder.suggest_workflow_optimizations(partial_workflow)

        assert optimization_result["success"] is True
        assert "optimizations" in optimization_result
        assert "improvement_score" in optimization_result

        optimizations = optimization_result["optimizations"]
        assert len(optimizations) > 0

        # Should suggest connecting steps with data flow
        data_flow_suggestions = [opt for opt in optimizations if "data_flow" in opt["type"]]
        assert len(data_flow_suggestions) > 0

        # Should suggest performance improvements
        performance_suggestions = [opt for opt in optimizations if "performance" in opt["type"]]
        assert len(performance_suggestions) > 0

        # Improvement score should reflect potential gains
        assert optimization_result["improvement_score"] > 0

    def test_workflow_testing_and_iteration(self, workflow_builder):
        """Test workflow testing and iterative improvement."""
        workflow_draft = {
            "name": "iterative_workflow",
            "steps": [
                {"id": "step1", "command": "status", "args": {}},
                {"id": "step2", "command": "failing_command", "args": {}},  # Will fail
                {"id": "step3", "command": "status", "args": {}}
            ]
        }

        test_result = workflow_builder.test_workflow_draft(workflow_draft)

        assert test_result["success"] is True  # Test execution successful
        assert "test_results" in test_result
        assert "issues_found" in test_result

        test_results = test_result["test_results"]
        issues = test_result["issues_found"]

        # Should identify failing step
        assert len(issues) > 0
        failing_issues = [issue for issue in issues if "failing_command" in str(issue)]
        assert len(failing_issues) > 0

        # Should provide improvement suggestions
        assert "improvement_suggestions" in test_result
        suggestions = test_result["improvement_suggestions"]

        # Should suggest fixes for failing step
        fix_suggestions = [s for s in suggestions if "fix" in s.get("type", "").lower()]
        assert len(fix_suggestions) > 0

        # Should suggest error handling
        error_handling_suggestions = [s for s in suggestions if "error" in s.get("type", "").lower()]
        assert len(error_handling_suggestions) > 0
