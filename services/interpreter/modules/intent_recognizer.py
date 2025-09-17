"""Intent recognition functionality for the Interpreter service.

This module contains the IntentRecognizer class and related functionality,
extracted from the main interpreter service to improve maintainability.
Enhanced with ecosystem context awareness for project-specific understanding.
"""

import re
from typing import Dict, Any, List, Tuple, Optional

from services.shared.models import Document, Finding

# Import shared utilities for consistent error handling
from .shared_utils import (
    handle_interpreter_error,
    build_interpreter_context
)
from .ecosystem_context import ecosystem_context


class IntentRecognizer:
    """NLP-based intent recognition engine."""

    def __init__(self):
        # Initialize with ecosystem context
        self._load_ecosystem_patterns()

    def _load_ecosystem_patterns(self):
        """Load intent patterns based on ecosystem capabilities."""
        # Base intent patterns
        self.intent_patterns = {
            # Analysis intents
            "analyze_document": [
                r"analyze\s+(?:this|the|that|my|your|a)?\s*(?:document|file|content|code)",
                r"check\s+(?:this|the|that|my|your|a)?\s*(?:document|file)",
                r"review\s+(?:this|the|that|my|your|a)?\s*(?:document|content)",
                r"examine\s+(?:this|the|that|my|your|a)?\s*(?:document|file)"
            ],

            "consistency_check": [
                r"check\s+consistency",
                r"find\s+inconsistencies",
                r"consistency\s+analysis",
                r"validate\s+consistency"
            ],

            "security_scan": [
                r"security\s+(?:scan|check|analysis)",
                r"scan\s+for\s+security",
                r"check\s+security",
                r"security\s+vulnerabilities"
            ],

            # Enhanced ingestion intents with ecosystem context
            "ingest_github": [
                r"ingest\s+(?:from\s+)?github",
                r"pull\s+from\s+github",
                r"import\s+github\s+(?:repo|repository)",
                r"sync\s+github"
            ],

            "ingest_jira": [
                r"ingest\s+(?:from\s+)?jira",
                r"pull\s+from\s+jira",
                r"import\s+jira\s+tickets",
                r"sync\s+jira"
            ],

            "ingest_confluence": [
                r"ingest\s+(?:from\s+)?confluence",
                r"pull\s+from\s+confluence",
                r"import\s+confluence\s+pages",
                r"sync\s+confluence"
            ],

            # Prompt management intents
            "create_prompt": [
                r"create\s+(?:a\s+)?(?:new\s+)?prompt",
                r"make\s+(?:a\s+)?prompt",
                r"add\s+(?:a\s+)?prompt",
                r"new\s+prompt"
            ],

            "find_prompt": [
                r"find\s+(?:a\s+)?prompt",
                r"search\s+(?:for\s+)?prompts?",
                r"get\s+(?:a\s+)?prompt",
                r"show\s+(?:me\s+)?prompts?"
            ],

            "optimize_prompt": [
                r"optimize\s+(?:a\s+)?prompt",
                r"improve\s+(?:a\s+)?prompt",
                r"enhance\s+(?:a\s+)?prompt",
                r"refine\s+(?:a\s+)?prompt"
            ],

            # Document management intents
            "store_document": [
                r"store\s+(?:a\s+)?document",
                r"save\s+(?:a\s+)?document",
                r"upload\s+(?:a\s+)?document",
                r"add\s+(?:a\s+)?document"
            ],

            "search_documents": [
                r"search\s+(?:for\s+)?documents?",
                r"find\s+(?:a\s+)?document",
                r"look\s+for\s+documents?",
                r"query\s+documents?"
            ],

            # Code analysis intents
            "analyze_code": [
                r"analyze\s+(?:this|the|that)?\s*code",
                r"check\s+(?:this|the|that)?\s*code",
                r"review\s+(?:this|the|that)?\s*code",
                r"examine\s+(?:this|the|that)?\s*code"
            ],

            "generate_code_docs": [
                r"generate\s+(?:code\s+)?docs?",
                r"create\s+(?:code\s+)?docs?",
                r"document\s+(?:the\s+)?code",
                r"auto.*docs?"
            ],

            # Content processing intents
            "summarize_content": [
                r"summarize\s+(?:this|the|that)?\s*content",
                r"create\s+(?:a\s+)?summary",
                r"generate\s+(?:a\s+)?summary",
                r"abstract\s+(?:the\s+)?content"
            ],

            # Workflow execution intents
            "execute_workflow": [
                r"(?:run|execute|start)\s+(?:a\s+)?workflow",
                r"trigger\s+(?:a\s+)?workflow",
                r"launch\s+(?:a\s+)?workflow",
                r"perform\s+(?:a\s+)?workflow"
            ],

            "list_workflows": [
                r"(?:show|list|get)\s+(?:available\s+)?workflows?",
                r"what\s+workflows?\s+(?:are\s+)?available",
                r"workflow\s+options",
                r"available\s+workflows?"
            ],

            # Report generation intents
            "generate_report": [
                r"generate\s+(?:a\s+)?report",
                r"create\s+(?:a\s+)?report",
                r"make\s+(?:a\s+)?report",
                r"run\s+(?:a\s+)?report"
            ],

            # Notification intents
            "send_notification": [
                r"send\s+(?:a\s+)?notification",
                r"notify\s+(?:someone|team|user)",
                r"alert\s+(?:someone|team)",
                r"send\s+alert"
            ],

            # System intents
            "help": [
                r"help(?:\s+me)?",
                r"what\s+can\s+you\s+do",
                r"show\s+commands",
                r"list\s+(?:available\s+)?commands"
            ],

            "status": [
                r"(?:show\s+)?status",
                r"(?:system\s+)?status",
                r"health\s+(?:check|status)",
                r"how\s+are\s+you"
            ],

            "discover_tools": [
                r"discover\s+(?:available\s+)?tools?",
                r"what\s+tools?\s+(?:are\s+)?available",
                r"list\s+(?:available\s+)?tools?",
                r"show\s+(?:me\s+)?tools?"
            ]
        }

        # Add dynamic patterns based on ecosystem services
        self._add_service_specific_patterns()

    def _add_service_specific_patterns(self):
        """Add service-specific intent patterns based on ecosystem capabilities."""
        # Get service capabilities from ecosystem context
        services = ecosystem_context.service_capabilities

        # Add patterns for each service based on its capabilities
        for service_name, service_info in services.items():
            capabilities = service_info.get("capabilities", [])
            aliases = service_info.get("aliases", [])

            # Create patterns for service-specific actions
            for capability in capabilities:
                capability_words = capability.replace("_", " ").split()
                action_words = ["analyze", "check", "create", "find", "generate", "process", "scan"]

                # Create intent patterns for service + capability combinations
                for action in action_words:
                    if action in capability:
                        pattern_key = f"{service_name}_{capability}"
                        pattern = rf"{action}\s+(?:using\s+)?(?:{'|'.join(aliases)}|{service_name.replace('_', ' ')})"

                        if pattern_key not in self.intent_patterns:
                            self.intent_patterns[pattern_key] = []
                        self.intent_patterns[pattern_key].append(pattern)

            # Add service-specific help patterns
            help_pattern = rf"help\s+with\s+(?:{'|'.join(aliases)}|{service_name.replace('_', ' ')})"
            if "help" not in self.intent_patterns:
                self.intent_patterns["help"] = []
            self.intent_patterns["help"].append(help_pattern)

        # Define entity patterns
        self.entity_patterns = {
            "url": r'https?://[^\s\'"]+',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "repo": r'(?:github\.com/)?([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)',
            "jira_key": r'\b[A-Z]{2,}-\d+\b',
            "file_path": r'(?:/[^/\s]+)+/\S+',
            "version": r'\bv?\d+(?:\.\d+)*(?:\.\d+)*\b'
        }

    def recognize_intent(self, query: str) -> Tuple[str, float, Dict[str, Any]]:
        """Recognize intent from user query using ecosystem context."""
        context = build_interpreter_context("recognize_intent", query_length=len(query))

        try:
            query_lower = query.lower()

            best_intent = "unknown"
            best_score = 0.0
            intent_metadata = {}

            # Check each intent pattern
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, query_lower, re.IGNORECASE)
                    if match:
                        # Enhanced scoring with ecosystem context
                        score = self._calculate_intent_score(intent, query_lower, match, pattern)
                        intent_metadata[intent] = {
                            "pattern": pattern,
                            "match": match.group(),
                            "score": score
                        }

                        if score > best_score:
                            best_score = score
                            best_intent = intent

            # Use ecosystem context for additional intent recognition
            if best_score < 0.7:  # If confidence is low, try ecosystem-aware recognition
                ecosystem_intent, ecosystem_score, ecosystem_meta = self._recognize_with_ecosystem_context(query_lower)
                if ecosystem_score > best_score:
                    best_intent = ecosystem_intent
                    best_score = ecosystem_score
                    intent_metadata.update(ecosystem_meta)

            # Extract entities with ecosystem context
            entities = self.extract_entities_with_context(query, best_intent)

            # Add ecosystem context to entities
            entities["ecosystem_context"] = {
                "detected_services": self._detect_services_in_query(query_lower),
                "detected_capabilities": self._detect_capabilities_in_query(query_lower),
                "suggested_workflows": self._suggest_workflows(query_lower, best_intent)
            }

            return best_intent, best_score, entities

        except Exception as e:
            # Return unknown intent with error context on failure
            handle_interpreter_error("recognize intent", e, query_length=len(query), **context)
            return "unknown", 0.0, {"error": str(e)}

    def _calculate_intent_score(self, intent: str, query: str, match, pattern: str) -> float:
        """Calculate intent confidence score with enhanced logic."""
        base_score = 0.6

        # High confidence for exact matches
        if intent in ["analyze_document", "security_scan"] and any(word in query for word in ["analyze", "scan", "check"]):
            base_score = 0.9

        # Medium-high confidence for action verbs
        action_verbs = ["analyze", "check", "review", "examine", "create", "find", "generate", "process", "scan"]
        if any(verb in query for verb in action_verbs):
            base_score = max(base_score, 0.8)

        # Boost for service-specific patterns
        if "_" in intent and any(service in intent for service in ecosystem_context.service_capabilities.keys()):
            base_score += 0.1

        # Reduce score for very short matches
        if len(match.group()) < 3:
            base_score -= 0.2

        return min(base_score, 1.0)

    def _recognize_with_ecosystem_context(self, query: str) -> Tuple[str, float, Dict[str, Any]]:
        """Use ecosystem context for intent recognition when pattern matching is uncertain."""
        best_intent = "unknown"
        best_score = 0.0
        metadata = {}

        # Check for service mentions
        detected_services = self._detect_services_in_query(query)
        if detected_services:
            # Try to infer intent based on mentioned services
            for service in detected_services:
                service_capabilities = ecosystem_context.service_capabilities.get(service, {}).get("capabilities", [])
                for capability in service_capabilities:
                    # Look for capability-related words in query
                    capability_words = capability.replace("_", " ").split()
                    if any(word in query for word in capability_words):
                        intent = f"{service}_{capability}"
                        score = 0.75  # Medium-high confidence for service + capability match
                        if score > best_score:
                            best_score = score
                            best_intent = intent
                            metadata = {"detected_service": service, "detected_capability": capability}

        # Check for workflow-related queries
        if any(word in query for word in ["workflow", "process", "pipeline", "automation"]):
            best_intent = "execute_workflow"
            best_score = 0.8
            metadata = {"workflow_focus": True}

        return best_intent, best_score, metadata

    def _detect_services_in_query(self, query: str) -> List[str]:
        """Detect service mentions in the query."""
        detected = []
        for service_name, service_info in ecosystem_context.service_capabilities.items():
            aliases = service_info.get("aliases", [])
            all_names = [service_name.replace("_", " ")] + aliases

            for name in all_names:
                if name.lower() in query:
                    detected.append(service_name)
                    break
        return list(set(detected))  # Remove duplicates

    def _detect_capabilities_in_query(self, query: str) -> List[str]:
        """Detect capability mentions in the query."""
        detected = []
        for service_info in ecosystem_context.service_capabilities.values():
            capabilities = service_info.get("capabilities", [])
            for capability in capabilities:
                capability_words = capability.replace("_", " ").split()
                if any(word in query for word in capability_words):
                    detected.append(capability)
        return list(set(detected))

    def _suggest_workflows(self, query: str, intent: str) -> List[str]:
        """Suggest relevant workflows based on query and intent."""
        suggestions = []

        # Map intents to workflow templates
        workflow_mapping = {
            "analyze_document": ["document_analysis"],
            "analyze_code": ["code_documentation"],
            "security_scan": ["security_audit"],
            "summarize_content": ["content_processing"],
            "ingest_github": ["code_documentation"],
            "ingest_jira": ["content_processing"],
            "ingest_confluence": ["content_processing"]
        }

        if intent in workflow_mapping:
            suggestions.extend(workflow_mapping[intent])

        # Add general suggestions based on query content
        if "document" in query or "content" in query:
            suggestions.append("document_analysis")
        if "code" in query or "repository" in query:
            suggestions.append("code_documentation")
        if "security" in query or "scan" in query:
            suggestions.append("security_audit")

        return list(set(suggestions))  # Remove duplicates

    def extract_entities_with_context(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract entities with ecosystem context awareness."""
        # Start with basic entity extraction
        entities = self.extract_entities(query)

        # Add intent-specific context
        if intent:
            entities["intent_context"] = self._extract_intent_specific_entities(query, intent)

        return entities

    def _extract_intent_specific_entities(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract entities specific to the detected intent."""
        context_entities = {}

        if intent == "analyze_document":
            # Look for document-related entities
            context_entities["document_types"] = []
            if "code" in query.lower():
                context_entities["document_types"].append("code")
            if "documentation" in query.lower():
                context_entities["document_types"].append("documentation")
            if not context_entities["document_types"]:
                context_entities["document_types"] = ["general"]

        elif intent.startswith("ingest_"):
            # Extract source information
            context_entities["source_type"] = intent.replace("ingest_", "")
            context_entities["source_urls"] = self.extract_entities(query).get("url", [])

        elif intent == "find_prompt":
            # Extract prompt search criteria
            context_entities["search_criteria"] = []
            if "category" in query.lower():
                context_entities["search_criteria"].append("category")
            if "performance" in query.lower():
                context_entities["search_criteria"].append("performance")
            if "recent" in query.lower():
                context_entities["search_criteria"].append("recent")

        return context_entities

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from query using regex patterns."""
        context = build_interpreter_context("extract_entities", query_length=len(query))

        try:
            entities = {}

            for entity_type, pattern in self.entity_patterns.items():
                matches = re.findall(pattern, query, re.IGNORECASE)
                if matches:
                    # Clean up matches
                    if entity_type == "repo":
                        # Special handling for repo patterns
                        cleaned_matches = []
                        for match in matches:
                            if isinstance(match, tuple):
                                cleaned_matches.append(f"{match[0]}/{match[1]}")
                            else:
                                cleaned_matches.append(match)
                        entities[entity_type] = cleaned_matches
                    else:
                        entities[entity_type] = list(set(matches))  # Remove duplicates

            return entities

        except Exception as e:
            # Return empty entities with error context on failure
            handle_interpreter_error("extract entities", e, query_length=len(query), **context)
            return {"error": str(e)}
