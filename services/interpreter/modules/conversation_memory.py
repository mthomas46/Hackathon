"""Conversation Memory Management for Interpreter Service.

This module manages conversation context and memory across user interactions,
integrating with the memory-agent service for persistent storage and retrieval.
Enables the interpreter to maintain context, learn from previous queries,
and provide more intelligent responses based on conversation history.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class ConversationMemory:
    """Manages conversation context and memory for enhanced user interactions."""

    def __init__(self):
        self.client = ServiceClients()
        self.memory_agent_url = "http://memory-agent:5030"
        self.interpreter_namespace = "interpreter_conversations"

        # Local cache for performance (backed by memory-agent)
        self.cache = defaultdict(lambda: {
            "sessions": deque(maxlen=10),  # Keep last 10 sessions in cache
            "preferences": {},
            "domain_context": {},
            "recent_workflows": deque(maxlen=20),
            "frequent_patterns": defaultdict(int),
            "last_activity": None,
            "total_interactions": 0
        })

        # Global conversation patterns (also cached)
        self.global_patterns = defaultdict(int)
        self.workflow_transitions = defaultdict(lambda: defaultdict(int))

        # Context expiration settings
        self.session_timeout = timedelta(hours=2)
        self.context_retention = timedelta(days=7)
        self.cache_ttl = timedelta(minutes=30)  # Cache validity period

        # Initialize memory-agent connection
        self.memory_agent_available = False

    async def _check_memory_agent_availability(self) -> bool:
        """Check if memory-agent service is available."""
        try:
            response = await self.client.get_json(f"{self.memory_agent_url}/health")
            self.memory_agent_available = response.get("status") == "healthy"
            return self.memory_agent_available
        except Exception:
            self.memory_agent_available = False
            return False

    # ============================================================================
    # MEMORY-AGENT INTEGRATION METHODS
    # ============================================================================

    async def _store_memory(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Store data in memory-agent with optional TTL."""
        try:
            memory_key = f"{self.interpreter_namespace}:{key}"

            payload = {
                "key": memory_key,
                "data": data,
                "namespace": self.interpreter_namespace
            }

            if ttl_seconds:
                payload["ttl_seconds"] = ttl_seconds

            response = await self.client.post_json(f"{self.memory_agent_url}/memory/store", payload)

            return response.get("success", False)

        except Exception as e:
            fire_and_forget(
                "memory_agent_store_error",
                f"Failed to store in memory-agent: {str(e)}",
                ServiceNames.INTERPRETER,
                {"key": key, "error": str(e)}
            )
            return False

    async def _retrieve_memory(self, key: str) -> Optional[Any]:
        """Retrieve data from memory-agent."""
        try:
            memory_key = f"{self.interpreter_namespace}:{key}"

            response = await self.client.get_json(
                f"{self.memory_agent_url}/memory/retrieve",
                params={"key": memory_key, "namespace": self.interpreter_namespace}
            )

            if response.get("success", False):
                return response.get("data")

            return None

        except Exception as e:
            fire_and_forget(
                "memory_agent_retrieve_error",
                f"Failed to retrieve from memory-agent: {str(e)}",
                ServiceNames.INTERPRETER,
                {"key": key, "error": str(e)}
            )
            return None

    async def _delete_memory(self, key: str) -> bool:
        """Delete data from memory-agent."""
        try:
            memory_key = f"{self.interpreter_namespace}:{key}"

            response = await self.client.delete_json(
                f"{self.memory_agent_url}/memory/delete",
                params={"key": memory_key, "namespace": self.interpreter_namespace}
            )

            return response.get("success", False)

        except Exception as e:
            fire_and_forget(
                "memory_agent_delete_error",
                f"Failed to delete from memory-agent: {str(e)}",
                ServiceNames.INTERPRETER,
                {"key": key, "error": str(e)}
            )
            return False

    async def _list_memory_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching a pattern in memory-agent."""
        try:
            response = await self.client.get_json(
                f"{self.memory_agent_url}/memory/list",
                params={"namespace": self.interpreter_namespace, "pattern": pattern}
            )

            if response.get("success", False):
                return response.get("keys", [])

            return []

        except Exception as e:
            fire_and_forget(
                "memory_agent_list_error",
                f"Failed to list memory keys: {str(e)}",
                ServiceNames.INTERPRETER,
                {"pattern": pattern, "error": str(e)}
            )
            return []

    async def _load_user_context_from_memory(self, user_id: str) -> Dict[str, Any]:
        """Load user conversation context from memory-agent."""
        try:
            context_key = f"user_context:{user_id}"
            stored_context = await self._retrieve_memory(context_key)

            if stored_context:
                # Convert stored data back to appropriate types
                if "sessions" in stored_context:
                    # Reconstruct deque from list
                    sessions_list = stored_context["sessions"]
                    stored_context["sessions"] = deque(sessions_list, maxlen=10)

                if "recent_workflows" in stored_context:
                    workflows_list = stored_context["recent_workflows"]
                    stored_context["recent_workflows"] = deque(workflows_list, maxlen=20)

                if "frequent_patterns" in stored_context:
                    stored_context["frequent_patterns"] = defaultdict(int, stored_context["frequent_patterns"])

                return stored_context

            return self.cache[user_id]  # Return empty cache structure

        except Exception as e:
            fire_and_forget(
                "memory_agent_load_error",
                f"Failed to load user context from memory: {str(e)}",
                ServiceNames.INTERPRETER,
                {"user_id": user_id, "error": str(e)}
            )
            return self.cache[user_id]

    async def _save_user_context_to_memory(self, user_id: str, context: Dict[str, Any]) -> bool:
        """Save user conversation context to memory-agent."""
        try:
            # Prepare data for storage (convert deques to lists)
            storage_data = context.copy()

            if "sessions" in storage_data:
                storage_data["sessions"] = list(storage_data["sessions"])

            if "recent_workflows" in storage_data:
                storage_data["recent_workflows"] = list(storage_data["recent_workflows"])

            if "frequent_patterns" in storage_data:
                storage_data["frequent_patterns"] = dict(storage_data["frequent_patterns"])

            context_key = f"user_context:{user_id}"

            # Store with 7-day TTL (context_retention)
            ttl_seconds = int(self.context_retention.total_seconds())

            return await self._store_memory(context_key, storage_data, ttl_seconds)

        except Exception as e:
            fire_and_forget(
                "memory_agent_save_error",
                f"Failed to save user context to memory: {str(e)}",
                ServiceNames.INTERPRETER,
                {"user_id": user_id, "error": str(e)}
            )
            return False

    async def _load_global_patterns_from_memory(self) -> Dict[str, int]:
        """Load global conversation patterns from memory-agent."""
        try:
            patterns_key = "global_patterns"
            stored_patterns = await self._retrieve_memory(patterns_key)

            if stored_patterns:
                return defaultdict(int, stored_patterns)

            return self.global_patterns

        except Exception as e:
            fire_and_forget(
                "memory_agent_load_global_error",
                f"Failed to load global patterns: {str(e)}",
                ServiceNames.INTERPRETER,
                {"error": str(e)}
            )
            return self.global_patterns

    async def _save_global_patterns_to_memory(self) -> bool:
        """Save global conversation patterns to memory-agent."""
        try:
            patterns_key = "global_patterns"
            patterns_data = dict(self.global_patterns)

            return await self._store_memory(patterns_key, patterns_data)

        except Exception as e:
            fire_and_forget(
                "memory_agent_save_global_error",
                f"Failed to save global patterns: {str(e)}",
                ServiceNames.INTERPRETER,
                {"error": str(e)}
            )
            return False

    async def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """Get current conversation context for a user."""
        if not user_id:
            return {}

        try:
            # Try to load from memory-agent first, then fall back to cache
            user_data = await self._load_user_context_from_memory(user_id)

            # Check if context has expired
            last_activity = user_data.get("last_activity")
            if last_activity and datetime.fromisoformat(last_activity) < datetime.utcnow() - self.session_timeout:
                await self._start_new_session(user_id)
                # Reload updated context
                user_data = await self._load_user_context_from_memory(user_id)

            # Build current context
            current_session = user_data["sessions"][-1] if user_data["sessions"] else {}

            context = {
                "user_id": user_id,
                "current_session": current_session,
                "preferences": user_data["preferences"],
                "domain_context": user_data["domain_context"],
                "recent_workflows": list(user_data["recent_workflows"]),
                "frequent_patterns": dict(user_data["frequent_patterns"]),
                "total_interactions": user_data["total_interactions"],
                "session_start": current_session.get("start_time"),
                "implied_context": await self._build_implied_context(user_data)
            }

            return context

        except Exception as e:
            fire_and_forget(
                "conversation_memory_error",
                f"Failed to get conversation context: {str(e)}",
                ServiceNames.INTERPRETER,
                {"user_id": user_id, "error": str(e)}
            )
            return {}

    async def update_conversation(self, user_id: str, query: str, workflow_name: str,
                                result: Dict[str, Any]) -> bool:
        """Update conversation with new interaction."""
        try:
            if not user_id:
                return False

            # Load current user data from memory
            user_data = await self._load_user_context_from_memory(user_id)
            current_time = datetime.utcnow().isoformat()

            # Ensure we have a current session
            if not user_data["sessions"] or self._is_new_session_needed(user_data):
                await self._start_new_session(user_id)
                # Reload after session creation
                user_data = await self._load_user_context_from_memory(user_id)

            current_session = user_data["sessions"][-1]

            # Create interaction record
            interaction = {
                "timestamp": current_time,
                "query": query,
                "workflow": workflow_name,
                "status": result.get("status", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "services_used": result.get("execution_metadata", {}).get("services_used", []),
                "execution_time": result.get("execution_metadata", {}).get("execution_time"),
                "entities_extracted": result.get("entities", {}),
                "intent": result.get("intent", "unknown")
            }

            # Add to current session
            if "interactions" not in current_session:
                current_session["interactions"] = []
            current_session["interactions"].append(interaction)

            # Update user statistics
            user_data["total_interactions"] += 1
            user_data["last_activity"] = current_time
            user_data["recent_workflows"].append(workflow_name)

            # Update patterns
            await self._update_patterns(user_id, query, workflow_name, interaction)

            # Update preferences based on successful interactions
            if result.get("status") == "success":
                await self._update_preferences(user_id, workflow_name, interaction)

            # Update domain context
            await self._update_domain_context(user_id, workflow_name, interaction)

            # Save updated context to memory-agent
            await self._save_user_context_to_memory(user_id, user_data)

            fire_and_forget(
                "conversation_updated",
                f"Updated conversation for user {user_id}",
                ServiceNames.INTERPRETER,
                {
                    "user_id": user_id,
                    "workflow": workflow_name,
                    "interaction_count": len(current_session["interactions"])
                }
            )

            return True

        except Exception as e:
            fire_and_forget(
                "conversation_update_error",
                f"Failed to update conversation: {str(e)}",
                ServiceNames.INTERPRETER,
                {"user_id": user_id, "error": str(e)}
            )
            return False

    async def _start_new_session(self, user_id: str) -> Dict[str, Any]:
        """Start a new conversation session for a user."""
        # Load current user data from memory
        user_data = await self._load_user_context_from_memory(user_id)

        new_session = {
            "session_id": f"{user_id}_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "interactions": [],
            "session_context": {},
            "active": True
        }

        # Close previous session if exists
        if user_data["sessions"]:
            user_data["sessions"][-1]["active"] = False
            user_data["sessions"][-1]["end_time"] = datetime.utcnow().isoformat()

        user_data["sessions"].append(new_session)

        # Save updated context to memory
        await self._save_user_context_to_memory(user_id, user_data)

        return new_session

    def _is_new_session_needed(self, user_data: Dict[str, Any]) -> bool:
        """Determine if a new session should be started."""
        if not user_data["sessions"]:
            return True
        
        last_activity = user_data.get("last_activity")
        if not last_activity:
            return True
        
        # Check timeout
        if datetime.fromisoformat(last_activity) < datetime.utcnow() - self.session_timeout:
            return True
        
        # Check interaction count (start new session after 50 interactions)
        current_session = user_data["sessions"][-1]
        if len(current_session.get("interactions", [])) >= 50:
            return True
        
        return False

    async def _update_patterns(self, user_id: str, query: str, workflow_name: str, 
                             interaction: Dict[str, Any]):
        """Update usage patterns for learning."""
        user_data = self.user_conversations[user_id]
        
        # Update user-specific patterns
        query_pattern = self._extract_query_pattern(query)
        user_data["frequent_patterns"][query_pattern] += 1
        
        # Update global patterns
        self.global_patterns[query_pattern] += 1
        
        # Update workflow transitions
        recent_workflows = list(user_data["recent_workflows"])
        if len(recent_workflows) >= 2:
            prev_workflow = recent_workflows[-2]
            self.workflow_transitions[prev_workflow][workflow_name] += 1

    def _extract_query_pattern(self, query: str) -> str:
        """Extract a pattern from the query for learning."""
        # Normalize query
        normalized = query.lower().strip()
        
        # Extract action verbs
        action_verbs = ["analyze", "check", "generate", "create", "find", "search", 
                       "scan", "process", "optimize", "review", "examine"]
        
        found_actions = [verb for verb in action_verbs if verb in normalized]
        
        # Extract object types
        object_types = ["document", "code", "repository", "prompt", "content", 
                       "security", "quality", "data", "information"]
        
        found_objects = [obj for obj in object_types if obj in normalized]
        
        # Create pattern
        if found_actions and found_objects:
            return f"{found_actions[0]}_{found_objects[0]}"
        elif found_actions:
            return f"{found_actions[0]}_general"
        elif found_objects:
            return f"general_{found_objects[0]}"
        else:
            return "general_query"

    async def _update_preferences(self, user_id: str, workflow_name: str, 
                                interaction: Dict[str, Any]):
        """Update user preferences based on successful interactions."""
        user_data = self.user_conversations[user_id]
        preferences = user_data["preferences"]
        
        # Track preferred workflows
        if "preferred_workflows" not in preferences:
            preferences["preferred_workflows"] = defaultdict(int)
        preferences["preferred_workflows"][workflow_name] += 1
        
        # Track preferred services
        services_used = interaction.get("services_used", [])
        if services_used:
            if "preferred_services" not in preferences:
                preferences["preferred_services"] = defaultdict(int)
            for service in services_used:
                preferences["preferred_services"][service] += 1
        
        # Track preferred interaction patterns
        intent = interaction.get("intent", "unknown")
        if intent != "unknown":
            if "preferred_intents" not in preferences:
                preferences["preferred_intents"] = defaultdict(int)
            preferences["preferred_intents"][intent] += 1
        
        # Update confidence thresholds based on user feedback
        confidence = interaction.get("confidence", 0.0)
        if confidence > 0.8:  # High confidence interactions
            if "confidence_preference" not in preferences:
                preferences["confidence_preference"] = "high"
            elif preferences["confidence_preference"] == "medium":
                preferences["confidence_preference"] = "high"

    async def _update_domain_context(self, user_id: str, workflow_name: str, 
                                   interaction: Dict[str, Any]):
        """Update domain context based on interaction patterns."""
        user_data = self.user_conversations[user_id]
        domain_context = user_data["domain_context"]
        
        # Map workflows to domains
        workflow_domains = {
            "document_analysis": "content_management",
            "code_documentation": "software_development",
            "security_audit": "security_compliance",
            "content_processing": "content_management",
            "data_ingestion": "data_management",
            "prompt_optimization": "ai_optimization",
            "quality_assurance": "quality_management",
            "research_assistance": "research_analysis"
        }
        
        domain = workflow_domains.get(workflow_name, "general")
        
        if "primary_domain" not in domain_context:
            domain_context["primary_domain"] = domain
            domain_context["domain_confidence"] = 1
        else:
            # Update domain confidence
            if domain_context["primary_domain"] == domain:
                domain_context["domain_confidence"] += 1
            else:
                # Track secondary domains
                if "secondary_domains" not in domain_context:
                    domain_context["secondary_domains"] = defaultdict(int)
                domain_context["secondary_domains"][domain] += 1
                
                # Switch primary domain if secondary becomes more frequent
                if domain_context["secondary_domains"][domain] > domain_context["domain_confidence"]:
                    domain_context["secondary_domains"][domain_context["primary_domain"]] = domain_context["domain_confidence"]
                    domain_context["primary_domain"] = domain
                    domain_context["domain_confidence"] = domain_context["secondary_domains"][domain]

    async def _build_implied_context(self, user_data: Dict[str, Any]) -> str:
        """Build implied context from recent interactions."""
        
        if not user_data["sessions"]:
            return ""
        
        current_session = user_data["sessions"][-1]
        recent_interactions = current_session.get("interactions", [])
        
        if not recent_interactions:
            return ""
        
        # Get last few interactions for context
        last_interactions = recent_interactions[-3:] if len(recent_interactions) >= 3 else recent_interactions
        
        # Extract common themes
        common_services = defaultdict(int)
        common_intents = defaultdict(int)
        
        for interaction in last_interactions:
            for service in interaction.get("services_used", []):
                common_services[service] += 1
            
            intent = interaction.get("intent", "")
            if intent and intent != "unknown":
                common_intents[intent] += 1
        
        # Build implied context
        context_parts = []
        
        if common_services:
            most_common_service = max(common_services.items(), key=lambda x: x[1])[0]
            context_parts.append(f"working with {most_common_service}")
        
        if common_intents:
            most_common_intent = max(common_intents.items(), key=lambda x: x[1])[0]
            if most_common_intent.startswith("analyze"):
                context_parts.append("continuing analysis work")
            elif most_common_intent.startswith("find"):
                context_parts.append("continuing search tasks")
        
        return " ".join(context_parts)

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences for personalization."""
        if not user_id:
            return {}

        # Load user data from memory-agent
        user_data = await self._load_user_context_from_memory(user_id)
        return user_data["preferences"]

    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        if not user_id:
            return []

        # Load user data from memory-agent
        user_data = await self._load_user_context_from_memory(user_id)
        all_interactions = []

        # Collect interactions from all sessions
        for session in reversed(user_data["sessions"]):
            session_interactions = session.get("interactions", [])
            for interaction in reversed(session_interactions):
                all_interactions.append({
                    **interaction,
                    "session_id": session.get("session_id", "unknown")
                })

                if len(all_interactions) >= limit:
                    break

            if len(all_interactions) >= limit:
                break

        return all_interactions

    async def get_workflow_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized workflow suggestions based on user history."""
        if not user_id:
            return []

        preferences = await self.get_user_preferences(user_id)

        suggestions = []

        # Suggest based on preferred workflows
        preferred_workflows = preferences.get("preferred_workflows", {})
        if preferred_workflows:
            top_workflows = sorted(preferred_workflows.items(), key=lambda x: x[1], reverse=True)[:3]
            for workflow_name, count in top_workflows:
                suggestions.append({
                    "type": "preferred_workflow",
                    "workflow_name": workflow_name,
                    "reason": f"You've used this workflow {count} times",
                    "confidence": min(count / 10.0, 1.0)
                })

        # Suggest based on workflow transitions
        user_data = await self._load_user_context_from_memory(user_id)
        recent_workflows = list(user_data["recent_workflows"])
        if recent_workflows:
            last_workflow = recent_workflows[-1]
            common_transitions = self.workflow_transitions.get(last_workflow, {})
            if common_transitions:
                next_workflow = max(common_transitions.items(), key=lambda x: x[1])[0]
                suggestions.append({
                    "type": "workflow_transition",
                    "workflow_name": next_workflow,
                    "reason": f"Often follows {last_workflow}",
                    "confidence": 0.7
                })

        return suggestions

    async def clear_user_context(self, user_id: str) -> bool:
        """Clear conversation context for a user."""
        try:
            # Remove from memory-agent
            context_key = f"user_context:{user_id}"
            await self._delete_memory(context_key)

            # Also clear from local cache if exists
            if user_id in self.cache:
                del self.cache[user_id]

            return True
        except Exception:
            return False

    async def get_conversation_analytics(self, user_id: str = None) -> Dict[str, Any]:
        """Get conversation analytics."""
        if user_id:
            # User-specific analytics
            user_data = await self._load_user_context_from_memory(user_id)
            return {
                "user_id": user_id,
                "total_interactions": user_data.get("total_interactions", 0),
                "session_count": len(user_data.get("sessions", [])),
                "preferences": user_data.get("preferences", {}),
                "domain_context": user_data.get("domain_context", {}),
                "recent_workflows": list(user_data.get("recent_workflows", []))
            }
        else:
            # Global analytics - count users from memory-agent
            try:
                # Get all user context keys from memory-agent
                user_keys = await self._list_memory_keys("user_context:*")
                total_users = len(user_keys)

                # Calculate total interactions (would need to sum across all users)
                total_interactions = 0

                # Load global patterns
                global_patterns = await self._load_global_patterns_from_memory()

                return {
                    "total_users": total_users,
                    "total_interactions": total_interactions,
                    "global_patterns": dict(global_patterns),
                    "workflow_transitions": {k: dict(v) for k, v in self.workflow_transitions.items()},
                    "active_users": total_users,  # Simplified - all stored users are considered active
                    "storage_backend": "memory-agent",
                    "namespace": self.interpreter_namespace
                }
            except Exception:
                # Fallback to basic analytics
                return {
                    "total_users": 0,
                    "total_interactions": 0,
                    "global_patterns": dict(self.global_patterns),
                    "workflow_transitions": {k: dict(v) for k, v in self.workflow_transitions.items()},
                    "active_users": 0,
                    "storage_backend": "memory-agent",
                    "error": "Failed to load analytics from memory-agent"
                }

    async def cleanup_expired_contexts(self):
        """Clean up expired conversation contexts from memory-agent."""
        try:
            # Get all user context keys
            user_keys = await self._list_memory_keys("user_context:*")
            expired_count = 0

            for key in user_keys:
                try:
                    # Extract user_id from key
                    if ":" in key:
                        user_id = key.split(":", 1)[1]  # Remove namespace prefix

                        # Load context to check expiration
                        user_data = await self._load_user_context_from_memory(user_id)
                        last_activity = user_data.get("last_activity")

                        if last_activity:
                            current_time = datetime.utcnow()
                            if datetime.fromisoformat(last_activity) < current_time - self.context_retention:
                                # Delete expired context
                                await self._delete_memory(f"user_context:{user_id}")
                                expired_count += 1

                except Exception as e:
                    fire_and_forget(
                        "conversation_cleanup_error",
                        f"Error cleaning up context for {key}: {str(e)}",
                        ServiceNames.INTERPRETER,
                        {"key": key, "error": str(e)}
                    )

            fire_and_forget(
                "conversation_cleanup",
                f"Cleaned up {expired_count} expired conversation contexts from memory-agent",
                ServiceNames.INTERPRETER,
                {"expired_count": expired_count, "storage_backend": "memory-agent"}
            )

        except Exception as e:
            fire_and_forget(
                "conversation_cleanup_failed",
                f"Failed to cleanup expired contexts: {str(e)}",
                ServiceNames.INTERPRETER,
                {"error": str(e), "storage_backend": "memory-agent"}
            )


# Create singleton instance
conversation_memory = ConversationMemory()
