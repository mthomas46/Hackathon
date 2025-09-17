"""Semantic Analysis Module for Discovery Agent service.

This module provides Phase 4 semantic analysis capabilities using LLM
to intelligently categorize and analyze discovered tools.
"""

import re
from typing import Dict, Any, List, Optional
try:
    from services.shared.clients import ServiceClients
except ImportError:
    # Fallback for when running in Docker or different environment
    ServiceClients = None


class SemanticToolAnalyzer:
    """Semantic analyzer for tool categorization and analysis using LLM"""

    def __init__(self, interpreter_url: str = "http://localhost:5120"):
        self.interpreter_url = interpreter_url
        self.service_client = ServiceClients()

        # Semantic categories and their characteristics
        self.semantic_categories = {
            "content_generation": {
                "keywords": ["generate", "create", "produce", "build", "construct"],
                "capabilities": ["text_generation", "content_creation", "synthesis"],
                "use_cases": ["writing", "creation", "synthesis"]
            },
            "content_analysis": {
                "keywords": ["analyze", "review", "evaluate", "assess", "examine"],
                "capabilities": ["analysis", "evaluation", "assessment"],
                "use_cases": ["quality_check", "review", "validation"]
            },
            "data_processing": {
                "keywords": ["process", "transform", "convert", "format", "clean"],
                "capabilities": ["data_transformation", "formatting", "processing"],
                "use_cases": ["data_prep", "transformation", "cleaning"]
            },
            "storage_management": {
                "keywords": ["store", "save", "retrieve", "persist", "archive"],
                "capabilities": ["data_storage", "retrieval", "persistence"],
                "use_cases": ["data_management", "archival", "backup"]
            },
            "communication": {
                "keywords": ["send", "notify", "alert", "message", "contact"],
                "capabilities": ["messaging", "notification", "communication"],
                "use_cases": ["alerting", "notification", "messaging"]
            },
            "search_retrieval": {
                "keywords": ["search", "find", "query", "lookup", "discover"],
                "capabilities": ["search", "retrieval", "querying"],
                "use_cases": ["information_retrieval", "search", "lookup"]
            },
            "ai_interaction": {
                "keywords": ["prompt", "llm", "ai", "model", "inference"],
                "capabilities": ["ai_interaction", "prompting", "model_usage"],
                "use_cases": ["ai_tasks", "prompt_engineering", "model_interaction"]
            },
            "system_operations": {
                "keywords": ["execute", "run", "command", "system", "infrastructure"],
                "capabilities": ["execution", "system_interaction", "infrastructure"],
                "use_cases": ["automation", "system_tasks", "infrastructure"]
            }
        }

    async def analyze_tool_semantics(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Perform semantic analysis of a tool using LLM understanding"""

        semantic_analysis = {
            "tool_name": tool["name"],
            "original_category": tool.get("category", "unknown"),
            "semantic_categories": [],
            "primary_category": "",
            "confidence_score": 0.0,
            "semantic_description": "",
            "capabilities_identified": [],
            "use_cases_identified": [],
            "relationships": {},
            "llm_analysis": None
        }

        # Use LLM for semantic analysis
        llm_analysis = await self._perform_llm_semantic_analysis(tool)

        if llm_analysis.get("success"):
            semantic_analysis["llm_analysis"] = llm_analysis["analysis"]

            # Parse LLM response for semantic insights
            parsed_semantics = self._parse_llm_semantic_response(llm_analysis["analysis"])
            semantic_analysis.update(parsed_semantics)
        else:
            # Fallback to rule-based semantic analysis
            print(f"LLM analysis failed for {tool['name']}, using rule-based analysis")
            rule_based = self._rule_based_semantic_analysis(tool)
            semantic_analysis.update(rule_based)

        # Calculate confidence score
        semantic_analysis["confidence_score"] = self._calculate_semantic_confidence(semantic_analysis)

        return semantic_analysis

    async def _perform_llm_semantic_analysis(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to perform semantic analysis of the tool"""

        analysis_prompt = f"""
        Analyze the following API tool and provide semantic understanding:

        Tool Name: {tool.get('name', 'Unknown')}
        Description: {tool.get('description', 'No description')}
        Method: {tool.get('method', 'Unknown')}
        Path: {tool.get('path', 'Unknown')}
        Category: {tool.get('category', 'Unknown')}

        Parameters: {len(tool.get('parameters', {}).get('properties', {}))} parameters

        Please provide semantic analysis in JSON format with:
        1. semantic_categories: Array of applicable semantic categories
        2. primary_category: Most appropriate single category
        3. capabilities: What this tool can do
        4. use_cases: Typical use cases for this tool
        5. description: Natural language description of tool purpose
        6. relationships: Related tools or complementary capabilities
        7. complexity_score: 1-10 scale of tool complexity

        Focus on understanding what the tool actually does, not just its technical specification.
        """

        try:
            async with self.service_client.session() as session:
                url = f"{self.interpreter_url}/interpret"

                payload = {
                    "query": analysis_prompt,
                    "context": "tool_semantic_analysis",
                    "response_format": "json"
                }

                async with session.post(url, json=payload, timeout=20) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "analysis": result.get("interpretation", "")
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

    def _parse_llm_semantic_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM semantic analysis response"""

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "semantic_categories": parsed.get("semantic_categories", []),
                    "primary_category": parsed.get("primary_category", ""),
                    "capabilities_identified": parsed.get("capabilities", []),
                    "use_cases_identified": parsed.get("use_cases", []),
                    "semantic_description": parsed.get("description", ""),
                    "relationships": parsed.get("relationships", {}),
                    "complexity_score": parsed.get("complexity_score", 5)
                }
        except:
            pass

        # Fallback parsing
        return {
            "semantic_categories": ["utility"],
            "primary_category": "utility",
            "capabilities_identified": ["unknown"],
            "use_cases_identified": ["general_use"],
            "semantic_description": "Tool purpose could not be determined semantically",
            "relationships": {},
            "complexity_score": 5
        }

    def _rule_based_semantic_analysis(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based semantic analysis as fallback"""

        tool_name = tool.get("name", "").lower()
        description = tool.get("description", "").lower()
        path = tool.get("path", "").lower()
        category = tool.get("category", "").lower()

        # Combine text for analysis
        combined_text = f"{tool_name} {description} {path} {category}"

        semantic_matches = []
        capabilities = []
        use_cases = []

        # Check against semantic categories
        for sem_category, category_data in self.semantic_categories.items():
            score = 0

            # Keyword matching
            for keyword in category_data["keywords"]:
                if keyword in combined_text:
                    score += 2

            # Category name matching
            if sem_category.replace("_", " ") in combined_text:
                score += 3

            if score >= 2:
                semantic_matches.append({
                    "category": sem_category,
                    "score": score,
                    "capabilities": category_data["capabilities"],
                    "use_cases": category_data["use_cases"]
                })

        # Sort by score and select top matches
        semantic_matches.sort(key=lambda x: x["score"], reverse=True)

        primary_category = semantic_matches[0]["category"] if semantic_matches else "utility"

        # Collect capabilities and use cases from top matches
        for match in semantic_matches[:3]:  # Top 3 matches
            capabilities.extend(match["capabilities"])
            use_cases.extend(match["use_cases"])

        # Remove duplicates
        capabilities = list(set(capabilities))
        use_cases = list(set(use_cases))

        return {
            "semantic_categories": [match["category"] for match in semantic_matches],
            "primary_category": primary_category,
            "capabilities_identified": capabilities,
            "use_cases_identified": use_cases,
            "semantic_description": f"Tool appears to be related to {primary_category.replace('_', ' ')} based on keyword analysis",
            "relationships": {},
            "complexity_score": min(len(tool.get("parameters", {}).get("properties", {})), 10)
        }

    def _calculate_semantic_confidence(self, semantic_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for semantic analysis"""

        confidence = 0.0

        # Base confidence from categories found
        categories_count = len(semantic_analysis.get("semantic_categories", []))
        confidence += min(categories_count * 0.2, 0.6)  # Up to 60% from categories

        # Add confidence from LLM analysis
        if semantic_analysis.get("llm_analysis"):
            confidence += 0.3  # 30% bonus for LLM analysis
        else:
            confidence += 0.1  # 10% for rule-based

        # Add confidence from detailed analysis
        capabilities = semantic_analysis.get("capabilities_identified", [])
        use_cases = semantic_analysis.get("use_cases_identified", [])

        if capabilities:
            confidence += 0.1
        if use_cases:
            confidence += 0.1
        if semantic_analysis.get("relationships"):
            confidence += 0.1

        return min(confidence, 1.0)

    async def analyze_tool_relationships(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relationships between tools using semantic understanding"""

        relationship_analysis = {
            "tool_count": len(tools),
            "relationships_found": 0,
            "relationship_types": {},
            "complementary_pairs": [],
            "workflow_suggestions": []
        }

        print(f"🔗 Analyzing relationships between {len(tools)} tools...")

        # Analyze each pair of tools for relationships
        for i, tool1 in enumerate(tools):
            for j, tool2 in enumerate(tools):
                if i >= j:  # Avoid duplicate pairs
                    continue

                relationship = await self._analyze_tool_pair_relationship(tool1, tool2)

                if relationship["has_relationship"]:
                    relationship_analysis["relationships_found"] += 1

                    rel_type = relationship["relationship_type"]
                    if rel_type not in relationship_analysis["relationship_types"]:
                        relationship_analysis["relationship_types"][rel_type] = 0
                    relationship_analysis["relationship_types"][rel_type] += 1

                    relationship_analysis["complementary_pairs"].append({
                        "tool1": tool1["name"],
                        "tool2": tool2["name"],
                        "relationship": rel_type,
                        "strength": relationship["strength"],
                        "description": relationship["description"]
                    })

        # Generate workflow suggestions
        relationship_analysis["workflow_suggestions"] = self._generate_workflow_suggestions(
            relationship_analysis["complementary_pairs"]
        )

        return relationship_analysis

    async def _analyze_tool_pair_relationship(self, tool1: Dict[str, Any], tool2: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relationship between two tools"""

        # Get semantic information
        sem1 = tool1.get("semantic_analysis", {})
        sem2 = tool2.get("semantic_analysis", {})

        categories1 = set(sem1.get("semantic_categories", []))
        categories2 = set(sem2.get("semantic_categories", []))

        capabilities1 = set(sem1.get("capabilities_identified", []))
        capabilities2 = set(sem2.get("capabilities_identified", []))

        use_cases1 = set(sem1.get("use_cases_identified", []))
        use_cases2 = set(sem2.get("use_cases_identified", []))

        # Check for sequential relationships
        sequential_patterns = [
            ({"content_generation"}, {"content_analysis"}, "generation_to_analysis"),
            ({"content_analysis"}, {"storage_management"}, "analysis_to_storage"),
            ({"search_retrieval"}, {"content_analysis"}, "retrieval_to_analysis"),
            ({"data_processing"}, {"storage_management"}, "processing_to_storage"),
            ({"ai_interaction"}, {"content_analysis"}, "ai_to_analysis"),
            ({"content_analysis"}, {"communication"}, "analysis_to_notification")
        ]

        for input_cats, output_cats, rel_type in sequential_patterns:
            if (categories1 & input_cats) and (categories2 & output_cats):
                return {
                    "has_relationship": True,
                    "relationship_type": rel_type,
                    "strength": 0.8,
                    "description": f"{tool1['name']} output can be analyzed/processed by {tool2['name']}"
                }
            elif (categories1 & output_cats) and (categories2 & input_cats):
                return {
                    "has_relationship": True,
                    "relationship_type": rel_type,
                    "strength": 0.8,
                    "description": f"{tool2['name']} output can be analyzed/processed by {tool1['name']}"
                }

        # Check for complementary capabilities
        if capabilities1 & capabilities2:  # Overlapping capabilities
            return {
                "has_relationship": True,
                "relationship_type": "complementary_capabilities",
                "strength": 0.6,
                "description": f"Both tools share capabilities: {', '.join(capabilities1 & capabilities2)}"
            }

        # Check for same use case (potential alternatives)
        if use_cases1 & use_cases2:
            return {
                "has_relationship": True,
                "relationship_type": "alternative_implementations",
                "strength": 0.4,
                "description": f"Both tools serve similar use cases: {', '.join(use_cases1 & use_cases2)}"
            }

        return {
            "has_relationship": False,
            "relationship_type": "none",
            "strength": 0.0,
            "description": "No significant relationship detected"
        }

    def _generate_workflow_suggestions(self, complementary_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate workflow suggestions based on tool relationships"""

        suggestions = []

        # Group by relationship type
        workflows_by_type = {}
        for pair in complementary_pairs:
            rel_type = pair["relationship"]
            if rel_type not in workflows_by_type:
                workflows_by_type[rel_type] = []
            workflows_by_type[rel_type].append(pair)

        # Generate suggestions for each relationship type
        for rel_type, pairs in workflows_by_type.items():
            if len(pairs) >= 2:  # Need at least 2 related pairs for a workflow
                suggestion = {
                    "workflow_type": rel_type,
                    "description": f"Multi-step workflow using {rel_type.replace('_', ' ')}",
                    "tools_involved": list(set([p["tool1"] for p in pairs] + [p["tool2"] for p in pairs])),
                    "estimated_steps": len(pairs) + 1,
                    "complexity": "medium" if len(pairs) <= 3 else "high"
                }
                suggestions.append(suggestion)

        return suggestions

    async def enhance_tool_categorization(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance tool categorization using semantic analysis"""

        enhanced_tools = []

        print(f"🧠 Enhancing categorization for {len(tools)} tools using semantic analysis...")

        for tool in tools:
            # Perform semantic analysis
            semantic_analysis = await self.analyze_tool_semantics(tool)

            # Enhance the tool with semantic information
            enhanced_tool = tool.copy()
            enhanced_tool["semantic_analysis"] = semantic_analysis

            # Update category if semantic analysis provides better categorization
            if semantic_analysis["confidence_score"] > 0.7:
                original_category = tool.get("category", "unknown")
                semantic_category = semantic_analysis["primary_category"]

                if semantic_category != "utility":  # Only override if we have a meaningful semantic category
                    enhanced_tool["enhanced_category"] = semantic_category
                    enhanced_tool["categorization_method"] = "semantic_analysis"
                    print(f"  📋 Enhanced {tool['name']}: {original_category} → {semantic_category}")

            enhanced_tools.append(enhanced_tool)

        return enhanced_tools


# Create singleton instance
semantic_tool_analyzer = SemanticToolAnalyzer()
