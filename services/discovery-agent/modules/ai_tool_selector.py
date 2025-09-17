"""AI-Powered Tool Selection Module for Discovery Agent service.

This module provides Phase 3 AI-powered tool selection and multi-service workflow
generation using intelligent analysis of tool capabilities and requirements.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
try:
    from services.shared.clients import ServiceClients
except ImportError:
    # Fallback for when running in Docker or different environment
    ServiceClients = None


class AIToolSelector:
    """AI-powered tool selection and workflow generation"""

    def __init__(self, interpreter_url: str = "http://localhost:5120"):
        self.interpreter_url = interpreter_url
        self.service_client = ServiceClients()
        self.tool_knowledge_base = {}

    async def select_tools_for_task(self, task_description: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AI to select optimal tools for a given task

        Args:
            task_description: Natural language description of the task
            available_tools: List of available tools to choose from

        Returns:
            Tool selection results with reasoning and recommendations
        """
        try:
            # Analyze task requirements
            task_analysis = await self._analyze_task_requirements(task_description)

            # Score and rank tools for the task
            tool_scores = await self._score_tools_for_task(task_analysis, available_tools)

            # Select optimal tool combination
            selected_tools = self._select_optimal_tools(tool_scores, task_analysis)

            # Generate workflow if multiple tools selected
            workflow = None
            if len(selected_tools) > 1:
                workflow = await self._generate_multi_tool_workflow(selected_tools, task_analysis)

            return {
                "success": True,
                "task_analysis": task_analysis,
                "selected_tools": selected_tools,
                "workflow": workflow,
                "confidence_score": self._calculate_selection_confidence(selected_tools, task_analysis),
                "reasoning": self._generate_selection_reasoning(selected_tools, task_analysis)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"AI tool selection failed: {str(e)}",
                "fallback_tools": self._fallback_tool_selection(task_description, available_tools)
            }

    async def _analyze_task_requirements(self, task_description: str) -> Dict[str, Any]:
        """Analyze task requirements using AI interpretation"""

        analysis_prompt = f"""
        Analyze the following task and identify key requirements:

        Task: {task_description}

        Please identify:
        1. Primary action (create, read, update, delete, analyze, etc.)
        2. Data types involved (documents, prompts, code, etc.)
        3. Required capabilities (AI, storage, analysis, etc.)
        4. Sequential steps needed
        5. Success criteria

        Provide analysis in JSON format.
        """

        try:
            # Use interpreter service for AI analysis
            analysis_result = await self._query_ai_interpreter(analysis_prompt)

            if analysis_result.get("success"):
                # Parse AI response into structured format
                ai_response = analysis_result.get("response", "")
                return self._parse_task_analysis(ai_response)
            else:
                # Fallback to rule-based analysis
                return self._rule_based_task_analysis(task_description)

        except Exception as e:
            print(f"AI analysis failed, using rule-based: {e}")
            return self._rule_based_task_analysis(task_description)

    def _rule_based_task_analysis(self, task_description: str) -> Dict[str, Any]:
        """Fallback rule-based task analysis"""
        task_lower = task_description.lower()

        analysis = {
            "primary_action": "analyze",
            "data_types": [],
            "capabilities": [],
            "steps": [],
            "success_criteria": []
        }

        # Determine primary action
        if any(word in task_lower for word in ["create", "generate", "build", "make"]):
            analysis["primary_action"] = "create"
        elif any(word in task_lower for word in ["read", "get", "retrieve", "fetch"]):
            analysis["primary_action"] = "read"
        elif any(word in task_lower for word in ["update", "modify", "change", "edit"]):
            analysis["primary_action"] = "update"
        elif any(word in task_lower for word in ["delete", "remove", "destroy"]):
            analysis["primary_action"] = "delete"
        elif any(word in task_lower for word in ["analyze", "process", "review", "check"]):
            analysis["primary_action"] = "analyze"

        # Determine data types
        if any(word in task_lower for word in ["document", "file", "text", "content"]):
            analysis["data_types"].append("documents")
        if any(word in task_lower for word in ["prompt", "instruction", "query"]):
            analysis["data_types"].append("prompts")
        if any(word in task_lower for word in ["code", "script", "program"]):
            analysis["data_types"].append("code")

        # Determine capabilities
        if any(word in task_lower for word in ["ai", "llm", "gpt", "generate", "intelligent"]):
            analysis["capabilities"].append("ai")
        if any(word in task_lower for word in ["store", "save", "persist", "database"]):
            analysis["capabilities"].append("storage")
        if any(word in task_lower for word in ["analyze", "review", "check", "validate"]):
            analysis["capabilities"].append("analysis")

        # Basic steps
        analysis["steps"] = ["analyze_requirements", "select_tools", "execute_workflow", "validate_results"]

        return analysis

    def _parse_task_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response into structured task analysis"""
        try:
            # Try to extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
        except:
            pass

        # Fallback to structured parsing
        return {
            "primary_action": "analyze",
            "data_types": ["documents"],
            "capabilities": ["ai"],
            "steps": ["analyze", "process", "generate"],
            "success_criteria": ["task_completed"],
            "ai_analysis": ai_response
        }

    async def _score_tools_for_task(self, task_analysis: Dict[str, Any], tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score each tool for suitability to the task"""
        scored_tools = []

        for tool in tools:
            score = await self._calculate_tool_score(tool, task_analysis)
            scored_tools.append({
                "tool": tool,
                "score": score["total_score"],
                "breakdown": score,
                "reasoning": self._generate_tool_reasoning(tool, score, task_analysis)
            })

        # Sort by score descending
        scored_tools.sort(key=lambda x: x["score"], reverse=True)
        return scored_tools

    async def _calculate_tool_score(self, tool: Dict[str, Any], task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive score for tool suitability"""
        score = {
            "total_score": 0,
            "action_match": 0,
            "data_type_match": 0,
            "capability_match": 0,
            "readiness_score": 0,
            "category_bonus": 0
        }

        # Action match scoring (0-30 points)
        tool_method = tool.get("method", "").upper()
        primary_action = task_analysis.get("primary_action", "")

        action_mapping = {
            "create": ["POST"],
            "read": ["GET"],
            "update": ["PUT", "PATCH"],
            "delete": ["DELETE"],
            "analyze": ["POST", "GET"]  # Analysis can use various methods
        }

        if primary_action in action_mapping and tool_method in action_mapping[primary_action]:
            score["action_match"] = 30
        elif primary_action == "analyze" and tool_method in ["POST", "GET"]:
            score["action_match"] = 25

        # Data type match scoring (0-25 points)
        tool_category = tool.get("category", "").lower()
        required_data_types = task_analysis.get("data_types", [])

        data_type_mapping = {
            "documents": ["storage", "analysis", "document"],
            "prompts": ["ai", "prompt", "intelligence"],
            "code": ["execution", "analysis", "code"]
        }

        for data_type in required_data_types:
            if data_type in data_type_mapping:
                matching_categories = data_type_mapping[data_type]
                if any(cat in tool_category for cat in matching_categories):
                    score["data_type_match"] += 25 / len(required_data_types)
                    break

        # Capability match scoring (0-20 points)
        required_capabilities = task_analysis.get("capabilities", [])
        capability_keywords = {
            "ai": ["ai", "llm", "intelligence", "prompt"],
            "storage": ["storage", "document", "memory"],
            "analysis": ["analysis", "validate", "check"]
        }

        for capability in required_capabilities:
            if capability in capability_keywords:
                keywords = capability_keywords[capability]
                if any(keyword in tool_category for keyword in keywords):
                    score["capability_match"] += 20 / len(required_capabilities)

        # LangGraph readiness bonus (0-15 points)
        readiness = tool.get("langraph_ready", {})
        readiness_score = readiness.get("score", 0)
        score["readiness_score"] = (readiness_score / 10) * 15

        # Category bonus for high-priority tools (0-10 points)
        high_priority_categories = ["analysis", "ai", "storage"]
        if tool_category in high_priority_categories:
            score["category_bonus"] = 10

        # Calculate total
        score["total_score"] = sum([
            score["action_match"],
            score["data_type_match"],
            score["capability_match"],
            score["readiness_score"],
            score["category_bonus"]
        ])

        return score

    def _generate_tool_reasoning(self, tool: Dict[str, Any], score: Dict[str, Any], task_analysis: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for tool selection"""
        reasons = []

        if score["action_match"] > 0:
            reasons.append(f"Good action match ({score['action_match']} pts)")

        if score["data_type_match"] > 0:
            reasons.append(f"Data type compatibility ({score['data_type_match']:.1f} pts)")

        if score["capability_match"] > 0:
            reasons.append(f"Capability alignment ({score['capability_match']:.1f} pts)")

        if score["readiness_score"] > 0:
            reasons.append(f"LangGraph ready ({score['readiness_score']:.1f} pts)")

        if score["category_bonus"] > 0:
            reasons.append(f"High priority category ({score['category_bonus']} pts)")

        return "; ".join(reasons) if reasons else "No strong matches found"

    def _select_optimal_tools(self, scored_tools: List[Dict[str, Any]], task_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select optimal combination of tools for the task"""
        selected = []

        # Always include the top-scoring tool
        if scored_tools:
            top_tool = scored_tools[0]
            if top_tool["score"] > 20:  # Minimum threshold
                selected.append(top_tool["tool"])

        # Add complementary tools for complex tasks
        required_steps = len(task_analysis.get("steps", []))
        if required_steps > 1 and len(scored_tools) > 1:
            # Look for tools that complement the primary tool
            primary_category = selected[0].get("category", "") if selected else ""

            for tool_entry in scored_tools[1:]:
                tool = tool_entry["tool"]
                tool_category = tool.get("category", "")

                # Add tools from different categories for workflow diversity
                if tool_category != primary_category and tool_entry["score"] > 15:
                    selected.append(tool)
                    if len(selected) >= min(required_steps, 3):  # Limit to 3 tools max
                        break

        return selected

    async def _generate_multi_tool_workflow(self, selected_tools: List[Dict[str, Any]], task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a workflow specification for multiple tools"""
        workflow = {
            "name": f"ai_generated_{task_analysis.get('primary_action', 'task')}_workflow",
            "description": f"AI-generated workflow for {task_analysis.get('primary_action', 'task')}",
            "steps": [],
            "required_tools": [tool["name"] for tool in selected_tools]
        }

        # Generate workflow steps based on task analysis
        steps = task_analysis.get("steps", [])
        for i, step in enumerate(steps):
            # Assign tools to steps
            assigned_tool = selected_tools[min(i, len(selected_tools) - 1)]

            workflow["steps"].append({
                "step_name": step,
                "tool": assigned_tool["name"],
                "service": assigned_tool["service"],
                "description": f"Execute {step} using {assigned_tool['name']}",
                "parameters": self._generate_step_parameters(step, assigned_tool)
            })

        return workflow

    def _generate_step_parameters(self, step: str, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appropriate parameters for a workflow step"""
        # This would use AI to determine optimal parameters
        # For now, provide basic parameter mapping

        param_mapping = {
            "analyze_requirements": {"input": "task_description"},
            "select_tools": {"criteria": "task_requirements"},
            "execute_workflow": {"tools": tool["name"]},
            "validate_results": {"expected_output": "task_completion"}
        }

        return param_mapping.get(step, {"input": "previous_step_output"})

    def _calculate_selection_confidence(self, selected_tools: List[Dict[str, Any]], task_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for tool selection"""
        if not selected_tools:
            return 0.0

        # Base confidence on tool scores and task complexity
        avg_score = sum(tool.get("score", 0) for tool in selected_tools) / len(selected_tools)
        task_complexity = len(task_analysis.get("steps", [])) / 5.0  # Normalize to 0-1

        confidence = (avg_score / 100.0) * 0.7 + task_complexity * 0.3
        return min(confidence, 1.0)  # Cap at 100%

    def _generate_selection_reasoning(self, selected_tools: List[Dict[str, Any]], task_analysis: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the complete selection"""
        if not selected_tools:
            return "No suitable tools found for the task requirements."

        reasoning_parts = [
            f"Selected {len(selected_tools)} tool(s) for {task_analysis.get('primary_action', 'task')}:"
        ]

        for i, tool in enumerate(selected_tools, 1):
            tool_name = tool.get("name", "Unknown")
            tool_score = tool.get("score", 0)
            reasoning_parts.append(f"{i}. {tool_name} (score: {tool_score:.1f})")

        if len(selected_tools) > 1:
            reasoning_parts.append(f"Combined tools provide comprehensive {task_analysis.get('primary_action', 'task')} workflow.")

        return " ".join(reasoning_parts)

    def _fallback_tool_selection(self, task_description: str, available_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback tool selection when AI analysis fails"""
        # Simple keyword-based selection
        task_lower = task_description.lower()

        fallback_tools = []
        for tool in available_tools:
            tool_name = tool.get("name", "").lower()
            tool_category = tool.get("category", "").lower()

            # Basic keyword matching
            if any(word in task_lower for word in tool_name.split("_")):
                fallback_tools.append(tool)
            elif any(word in task_lower for word in tool_category.split()):
                fallback_tools.append(tool)

        # Return top 2 fallback tools
        return fallback_tools[:2]

    async def _query_ai_interpreter(self, prompt: str) -> Dict[str, Any]:
        """Query the AI interpreter service"""
        try:
            async with self.service_client.session() as session:
                url = f"{self.interpreter_url}/interpret"

                payload = {
                    "query": prompt,
                    "context": "tool_selection_analysis",
                    "response_format": "json"
                }

                async with session.post(url, json=payload, timeout=15) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "response": result.get("interpretation", "")
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Interpreter returned {response.status}"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Create singleton instance
ai_tool_selector = AIToolSelector()
