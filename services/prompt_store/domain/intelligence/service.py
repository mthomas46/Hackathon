"""Cross-service intelligence service for generating prompts from code and documents."""

import re
from typing import Dict, Any, List, Optional
from ...shared.clients import ServiceClients
from ...shared.utilities import generate_id, utc_now


class IntelligenceService:
    """Service for cross-service intelligence and prompt generation."""

    def __init__(self):
        self.clients = ServiceClients()

    async def generate_prompts_from_code(self, code_content: str, language: str = "python") -> Dict[str, Any]:
        """Generate prompts based on code analysis."""
        try:
            # Use code analyzer service (scaffolding exists)
            analysis_response = await self.clients.analyze_code(code_content, language)

            if not analysis_response.get("success"):
                return {"error": "Code analysis failed"}

            analysis_data = analysis_response.get("data", {})

            # Extract insights and generate prompts
            generated_prompts = []

            # Generate function documentation prompts
            functions = analysis_data.get("functions", [])
            for func in functions[:5]:  # Limit to top functions
                prompt = self._create_function_doc_prompt(func, language)
                generated_prompts.append(prompt)

            # Generate class documentation prompts
            classes = analysis_data.get("classes", [])
            for cls in classes[:3]:  # Limit to top classes
                prompt = self._create_class_doc_prompt(cls, language)
                generated_prompts.append(prompt)

            # Generate API endpoint prompts if applicable
            if self._is_api_code(code_content):
                api_prompt = self._create_api_doc_prompt(analysis_data)
                generated_prompts.append(api_prompt)

            return {
                "source_type": "code",
                "language": language,
                "analysis_summary": {
                    "functions_analyzed": len(functions),
                    "classes_analyzed": len(classes),
                    "complexity_score": analysis_data.get("complexity", {}).get("overall", 0)
                },
                "generated_prompts": generated_prompts,
                "total_prompts": len(generated_prompts)
            }

        except Exception as e:
            return {"error": f"Code analysis failed: {str(e)}"}

    def _create_function_doc_prompt(self, func: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Create a documentation prompt for a function."""
        func_name = func.get("name", "unknown_function")
        parameters = func.get("parameters", [])
        purpose = func.get("purpose", "performs a specific task")

        prompt_content = f"""Write comprehensive documentation for the {func_name} function in {language}.

Function signature: {func_name}({', '.join(parameters) if parameters else '...'})

Purpose: {purpose}

Documentation should include:
1. Detailed description of what the function does
2. Parameter descriptions with types and purposes
3. Return value description with type
4. Usage examples with sample code
5. Any important notes, edge cases, or constraints
6. Error handling behavior if applicable

Format the documentation clearly with sections and code examples."""

        return {
            "id": generate_id(),
            "name": f"Function Documentation: {func_name}",
            "category": "code_documentation",
            "content": prompt_content,
            "variables": [],
            "tags": ["documentation", "function", language, "auto_generated"],
            "source_type": "code_analysis",
            "source_entity": func_name,
            "confidence_score": 0.85,
            "estimated_complexity": "medium"
        }

    def _create_class_doc_prompt(self, cls: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Create a documentation prompt for a class."""
        class_name = cls.get("name", "unknown_class")
        methods = cls.get("methods", [])
        purpose = cls.get("purpose", "represents a data structure or behavior")

        prompt_content = f"""Document the {class_name} class in {language}.

Class purpose: {purpose}

Key methods: {', '.join(methods[:5]) if methods else 'various methods'}

Documentation should include:
1. Class overview and purpose
2. Key attributes/properties
3. Important methods with descriptions
4. Usage examples showing instantiation and common operations
5. Design patterns or concepts it implements (if applicable)
6. Relationships with other classes

Provide practical examples and explain when to use this class."""

        return {
            "id": generate_id(),
            "name": f"Class Documentation: {class_name}",
            "category": "code_documentation",
            "content": prompt_content,
            "variables": [],
            "tags": ["documentation", "class", language, "auto_generated"],
            "source_type": "code_analysis",
            "source_entity": class_name,
            "confidence_score": 0.8,
            "estimated_complexity": "medium"
        }

    def _create_api_doc_prompt(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an API documentation prompt."""
        functions = analysis_data.get("functions", [])
        api_endpoints = [f for f in functions if self._looks_like_api_function(f)]

        if not api_endpoints:
            return None

        prompt_content = f"""Create comprehensive API documentation for the following endpoints:

{chr(10).join([f"- {endpoint.get('name', 'unknown')}({', '.join(endpoint.get('parameters', []))})" for endpoint in api_endpoints[:10]])}

For each endpoint, document:
1. HTTP method and URL pattern
2. Purpose and functionality
3. Request parameters with types and descriptions
4. Response format and status codes
5. Authentication requirements
6. Usage examples with curl or code samples
7. Error responses and handling

Organize by resource groups and include a summary table."""

        return {
            "id": generate_id(),
            "name": "API Documentation Suite",
            "category": "api_documentation",
            "content": prompt_content,
            "variables": [],
            "tags": ["documentation", "api", "rest", "auto_generated"],
            "source_type": "code_analysis",
            "source_entity": "api_endpoints",
            "confidence_score": 0.75,
            "estimated_complexity": "high"
        }

    def _looks_like_api_function(self, func: Dict[str, Any]) -> bool:
        """Check if a function looks like an API endpoint."""
        name = func.get("name", "").lower()
        return any(keyword in name for keyword in ["get", "post", "put", "delete", "api", "endpoint", "route"])

    def _is_api_code(self, code_content: str) -> bool:
        """Check if code contains API-related patterns."""
        api_patterns = [
            r"app\.route|@app\.route|router\.|api\.|flask|fastapi|express",
            r"GET|POST|PUT|DELETE",
            r"@app\.(get|post|put|delete)",
            r"def (get|post|put|delete|create|update|delete)"
        ]

        return any(re.search(pattern, code_content, re.IGNORECASE) for pattern in api_patterns)

    async def generate_prompts_from_document(self, document_content: str, doc_type: str = "markdown") -> Dict[str, Any]:
        """Generate prompts based on document analysis."""
        try:
            # Use summarizer service (scaffolding exists)
            summary_response = await self.clients.summarize_document(document_content, format=doc_type)

            if not summary_response.get("success"):
                return {"error": "Document analysis failed"}

            summary_data = summary_response.get("data", {})

            # Extract insights and generate prompts
            generated_prompts = []

            # Generate content expansion prompts
            main_topics = summary_data.get("main_topics", [])
            for topic in main_topics[:3]:
                prompt = self._create_topic_expansion_prompt(topic, doc_type)
                generated_prompts.append(prompt)

            # Generate explanation prompts for key concepts
            key_concepts = summary_data.get("key_concepts", [])
            for concept in key_concepts[:5]:
                prompt = self._create_concept_explanation_prompt(concept)
                generated_prompts.append(prompt)

            # Generate tutorial prompts if document seems educational
            if self._is_tutorial_document(document_content):
                tutorial_prompt = self._create_tutorial_prompt(summary_data)
                generated_prompts.append(tutorial_prompt)

            return {
                "source_type": "document",
                "document_type": doc_type,
                "analysis_summary": {
                    "main_topics": len(main_topics),
                    "key_concepts": len(key_concepts),
                    "word_count": len(document_content.split()),
                    "sentiment": summary_data.get("sentiment", "neutral")
                },
                "generated_prompts": generated_prompts,
                "total_prompts": len(generated_prompts)
            }

        except Exception as e:
            return {"error": f"Document analysis failed: {str(e)}"}

    def _create_topic_expansion_prompt(self, topic: str, doc_type: str) -> Dict[str, Any]:
        """Create a content expansion prompt for a topic."""
        prompt_content = f"""Expand on the topic "{topic}" with comprehensive, well-structured content.

Create detailed content that includes:
1. Introduction and overview
2. Key concepts and definitions
3. Step-by-step explanations
4. Practical examples or use cases
5. Common pitfalls and how to avoid them
6. Best practices and recommendations
7. Summary and key takeaways

Format the content appropriately for {doc_type} format with proper headings, code blocks (if technical), and clear structure."""

        return {
            "id": generate_id(),
            "name": f"Content Expansion: {topic}",
            "category": "content_creation",
            "content": prompt_content,
            "variables": [],
            "tags": ["content", "expansion", "tutorial", "auto_generated"],
            "source_type": "document_analysis",
            "source_entity": topic,
            "confidence_score": 0.8,
            "estimated_complexity": "medium"
        }

    def _create_concept_explanation_prompt(self, concept: str) -> Dict[str, Any]:
        """Create an explanation prompt for a key concept."""
        prompt_content = f"""Explain the concept of "{concept}" in a clear, comprehensive manner.

Your explanation should:
1. Define the concept simply and accurately
2. Provide context and background information
3. Explain why it's important or useful
4. Give concrete examples or analogies
5. Show how it relates to other related concepts
6. Include common misconceptions and clarify them
7. Suggest resources for further learning

Use simple language suitable for someone new to the topic, but include technical details where appropriate."""

        return {
            "id": generate_id(),
            "name": f"Concept Explanation: {concept}",
            "category": "educational",
            "content": prompt_content,
            "variables": [],
            "tags": ["explanation", "concept", "educational", "auto_generated"],
            "source_type": "document_analysis",
            "source_entity": concept,
            "confidence_score": 0.9,
            "estimated_complexity": "low"
        }

    def _create_tutorial_prompt(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tutorial prompt based on document content."""
        topics = summary_data.get("main_topics", [])
        concepts = summary_data.get("key_concepts", [])

        prompt_content = f"""Create a comprehensive step-by-step tutorial covering:

Main Topics: {', '.join(topics[:3])}
Key Concepts: {', '.join(concepts[:5])}

Tutorial Structure:
1. Prerequisites and target audience
2. Learning objectives
3. Step-by-step instructions with examples
4. Practice exercises or challenges
5. Common mistakes and troubleshooting
6. Advanced topics and next steps
7. Additional resources and references

Make the tutorial progressive, starting with basics and building up to advanced concepts. Include code examples where relevant and provide clear explanations for each step."""

        return {
            "id": generate_id(),
            "name": "Comprehensive Tutorial",
            "category": "educational",
            "content": prompt_content,
            "variables": [],
            "tags": ["tutorial", "step-by-step", "educational", "auto_generated"],
            "source_type": "document_analysis",
            "source_entity": "tutorial_content",
            "confidence_score": 0.75,
            "estimated_complexity": "high"
        }

    def _is_tutorial_document(self, content: str) -> bool:
        """Check if document appears to be educational/tutorial content."""
        tutorial_indicators = [
            "tutorial", "guide", "how to", "step by step", "learn", "introduction to",
            "beginner", "getting started", "walkthrough", "example", "exercise"
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in tutorial_indicators)

    async def generate_service_integration_prompts(self, service_name: str, service_description: str = "") -> List[Dict[str, Any]]:
        """Generate prompts optimized for specific service integrations."""
        service_prompts = []

        # Common service integration patterns
        integration_patterns = {
            "database": [
                "CRUD operations documentation",
                "Query optimization guide",
                "Schema design patterns",
                "Migration strategies"
            ],
            "api": [
                "RESTful API design",
                "Authentication and authorization",
                "Rate limiting strategies",
                "API versioning best practices"
            ],
            "frontend": [
                "Component design patterns",
                "State management strategies",
                "UI/UX optimization",
                "Responsive design principles"
            ],
            "testing": [
                "Unit testing strategies",
                "Integration testing approaches",
                "Test-driven development",
                "Automated testing pipelines"
            ]
        }

        patterns = integration_patterns.get(service_name.lower(), ["General service integration"])

        for pattern in patterns:
            prompt = {
                "id": generate_id(),
                "name": f"{service_name.title()}: {pattern}",
                "category": "service_integration",
                "content": f"""Create comprehensive documentation for {pattern} in the context of {service_name}.

Focus on:
1. Best practices and patterns specific to {service_name}
2. Implementation examples with code samples
3. Common challenges and solutions
4. Performance considerations
5. Security implications
6. Testing strategies
7. Deployment and maintenance considerations

Provide practical, actionable guidance that developers can immediately apply.""",
                "variables": [],
                "tags": ["service_integration", service_name.lower(), "documentation", "auto_generated"],
                "source_type": "service_analysis",
                "source_entity": service_name,
                "confidence_score": 0.7,
                "estimated_complexity": "high"
            }
            service_prompts.append(prompt)

        return service_prompts

    async def analyze_prompt_effectiveness(self, prompt_id: str, usage_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze prompt effectiveness based on usage patterns."""
        if not usage_history:
            return {"error": "No usage history available"}

        # Calculate effectiveness metrics
        total_uses = len(usage_history)
        successful_uses = len([u for u in usage_history if u.get("success", False)])

        success_rate = successful_uses / total_uses if total_uses > 0 else 0

        # Analyze response times
        response_times = [u.get("response_time_ms", 0) for u in usage_history if u.get("response_time_ms")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Analyze user satisfaction (if available)
        satisfaction_scores = [u.get("user_rating", 0) for u in usage_history if u.get("user_rating")]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

        # Generate recommendations
        recommendations = []

        if success_rate < 0.7:
            recommendations.append("Consider revising prompt for clarity and specificity")
        if avg_response_time > 10000:
            recommendations.append("Prompt may be too complex, consider simplifying")
        if avg_satisfaction < 3.5 and avg_satisfaction > 0:
            recommendations.append("Low user satisfaction suggests prompt needs improvement")

        return {
            "prompt_id": prompt_id,
            "metrics": {
                "total_uses": total_uses,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "avg_user_satisfaction": avg_satisfaction,
                "usage_trend": "stable"  # Would analyze trends
            },
            "recommendations": recommendations,
            "effectiveness_score": (success_rate * 0.4 + (avg_satisfaction / 5) * 0.4 + (1 - min(avg_response_time / 30000, 1)) * 0.2)
        }
