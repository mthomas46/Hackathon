"""Summarizer Hub Service - Simplified Version.

Advanced document summarization and categorization service for the LLM Documentation Ecosystem.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict, Any, List, Optional
import time
import os
import httpx
import uuid
import json
import base64
import re
from datetime import datetime, timedelta

# Service configuration
SERVICE_NAME = "summarizer-hub"
SERVICE_TITLE = "Summarizer Hub"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5160

# Environment configuration
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Jira configuration
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_DEFAULT_PROJECT = os.getenv("JIRA_DEFAULT_PROJECT", "DOC")

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Advanced document summarization, categorization, and AI-assisted peer review service"
)

class SummarizeRequest(BaseModel):
    """Request model for document summarization."""
    content: str
    format: str = "markdown"
    max_length: int = 500
    style: Optional[str] = "professional"

class SummarizeResponse(BaseModel):
    """Response model for document summarization."""
    success: bool
    data: Dict[str, Any] = {}
    error: str = ""

class CategorizeRequest(BaseModel):
    """Request model for document categorization."""
    document: Dict[str, Any]
    candidate_categories: Optional[List[str]] = None
    use_zero_shot: bool = True

    @field_validator('document')
    @classmethod
    def validate_document(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Document must be a dictionary')
        if 'content' not in v:
            raise ValueError('Document must contain content field')
        return v

class CategorizeResponse(BaseModel):
    """Response model for document categorization."""
    success: bool
    document_id: str
    category: str
    confidence: float
    explanation: str
    metadata: Dict[str, Any] = {}

class PeerReviewRequest(BaseModel):
    """Request model for peer review."""
    content: str
    review_type: str = "general"
    focus_areas: Optional[List[str]] = None

class PeerReviewResponse(BaseModel):
    """Response model for peer review."""
    success: bool
    review_id: str
    suggestions: List[Dict[str, Any]]
    overall_score: float
    metadata: Dict[str, Any] = {}

class RecommendationType(str):
    """Enumeration of recommendation types."""
    CONSOLIDATION = "consolidation"
    DUPLICATE = "duplicate"
    OUTDATED = "outdated"
    QUALITY = "quality"


class JiraIssueType(str):
    """Enumeration of Jira issue types."""
    TASK = "Task"
    BUG = "Bug"
    STORY = "Story"
    EPIC = "Epic"


class JiraPriority(str):
    """Enumeration of Jira priority levels."""
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"


class JiraTicketRequest(BaseModel):
    """Request model for creating Jira tickets from recommendations."""
    recommendations: List[Dict[str, Any]]
    project_key: str
    issue_type: str = JiraIssueType.TASK
    assignee: Optional[str] = None
    labels: List[str] = []
    components: List[str] = []
    custom_fields: Dict[str, Any] = {}

class JiraTicketResponse(BaseModel):
    """Response model for Jira ticket creation."""
    success: bool
    tickets_created: List[Dict[str, Any]] = []
    tickets_failed: List[Dict[str, Any]] = []
    total_created: int
    total_failed: int
    jira_project: str

class RecommendationRequest(BaseModel):
    """Request model for document recommendations."""
    documents: List[Dict[str, Any]]
    recommendation_types: Optional[List[str]] = None  # consolidation, duplicate, outdated, quality
    confidence_threshold: float = 0.4
    include_jira_suggestions: bool = False
    create_jira_tickets: bool = False
    jira_project_key: Optional[str] = None
    timeline: Optional[Dict[str, Any]] = None

    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError('At least one document is required')
        for doc in v:
            if not isinstance(doc, dict):
                raise ValueError('Each document must be a dictionary')
            if 'id' not in doc or 'content' not in doc:
                raise ValueError('Each document must have id and content fields')
        return v

class RecommendationResponse(BaseModel):
    """Response model for document recommendations."""
    success: bool
    recommendations: List[Dict[str, Any]] = []
    total_documents: int
    recommendations_count: int
    processing_time: float
    metadata: Dict[str, Any] = {}
    error: str = ""
    suggested_jira_tickets: List[Dict[str, Any]] = []
    jira_ticket_creation: Dict[str, Any] = {}
    drift_analysis: Dict[str, Any] = {}
    alignment_analysis: Dict[str, Any] = {}
    inconclusive_analysis: Dict[str, Any] = {}
    timeline_analysis: Dict[str, Any] = {}

class SimpleSummarizer:
    """Core summarization logic."""
    
    def __init__(self):
        self.categories = [
            "Technical Documentation",
            "API Documentation", 
            "User Guide",
            "Architecture Documentation",
            "Process Documentation",
            "Meeting Notes",
            "Requirements",
            "Code Documentation"
        ]
    
    async def summarize_with_llm(self, content: str, max_length: int = 500, style: str = "professional") -> str:
        """Summarize content using LLM Gateway."""
        try:
            prompt = f"Summarize the following content in a {style} style, keeping it under {max_length} words:\n\n{content}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_GATEWAY_URL}/query",
                    json={
                        "prompt": prompt,
                        "provider": "ollama",
                        "model": "llama2",
                        "max_tokens": max_length
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("data", {}).get("response", "")
                else:
                    return self.fallback_summarize(content, max_length)
                    
        except Exception as e:
            print(f"LLM summarization failed: {e}")
            return self.fallback_summarize(content, max_length)
    
    def fallback_summarize(self, content: str, max_length: int = 500) -> str:
        """Fallback summarization without LLM."""
        words = content.split()
        if len(words) <= max_length:
            return content
        
        # Simple truncation with sentence awareness
        truncated = " ".join(words[:max_length])
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.7:  # If we can find a sentence ending in the last 30%
            return truncated[:last_period + 1]
        return truncated + "..."
    
    async def categorize_with_llm(self, content: str, candidate_categories: List[str] = None) -> Dict[str, Any]:
        """Categorize content using LLM Gateway."""
        categories = candidate_categories or self.categories
        try:
            prompt = f"Categorize the following content into one of these categories: {', '.join(categories)}. Provide the category name and a confidence score (0-1):\n\n{content[:1000]}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_GATEWAY_URL}/query",
                    json={
                        "prompt": prompt,
                        "provider": "ollama",
                        "model": "llama2",
                        "max_tokens": 200
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("data", {}).get("response", "")
                    return self.parse_categorization_response(llm_response, categories)
                else:
                    return self.fallback_categorize(content, categories)
                    
        except Exception as e:
            print(f"LLM categorization failed: {e}")
            return self.fallback_categorize(content, categories)
    
    def parse_categorization_response(self, response: str, categories: List[str]) -> Dict[str, Any]:
        """Parse LLM categorization response."""
        response_lower = response.lower()
        
        # Find the category mentioned in the response
        for category in categories:
            if category.lower() in response_lower:
                # Try to extract confidence if mentioned
                confidence = 0.8  # Default confidence
                if "confidence" in response_lower:
                    import re
                    conf_match = re.search(r'(\d+\.?\d*)%?', response)
                    if conf_match:
                        conf_val = float(conf_match.group(1))
                        confidence = conf_val / 100 if conf_val > 1 else conf_val
                
                return {
                    "category": category,
                    "confidence": confidence,
                    "explanation": response.strip()
                }
        
        # Fallback to first category
        return {
            "category": categories[0],
            "confidence": 0.5,
            "explanation": "Category assigned by fallback logic"
        }
    
    def fallback_categorize(self, content: str, categories: List[str]) -> Dict[str, Any]:
        """Fallback categorization without LLM."""
        content_lower = content.lower()
        
        # Simple keyword matching
        if any(word in content_lower for word in ["api", "endpoint", "request", "response"]):
            return {"category": "API Documentation", "confidence": 0.7, "explanation": "Contains API-related keywords"}
        elif any(word in content_lower for word in ["architecture", "system", "design"]):
            return {"category": "Architecture Documentation", "confidence": 0.7, "explanation": "Contains architecture-related keywords"}
        elif any(word in content_lower for word in ["user", "guide", "tutorial", "how to"]):
            return {"category": "User Guide", "confidence": 0.7, "explanation": "Contains user guide keywords"}
        elif any(word in content_lower for word in ["meeting", "notes", "discussion"]):
            return {"category": "Meeting Notes", "confidence": 0.7, "explanation": "Contains meeting-related keywords"}
        else:
            return {"category": "Technical Documentation", "confidence": 0.5, "explanation": "Default categorization"}
    
    async def peer_review_with_llm(self, content: str, review_type: str = "general", focus_areas: List[str] = None) -> Dict[str, Any]:
        """Perform peer review using LLM Gateway."""
        focus = focus_areas or ["clarity", "completeness", "accuracy"]
        try:
            prompt = f"Perform a {review_type} peer review of the following content, focusing on {', '.join(focus)}. Provide specific suggestions and an overall score (0-10):\n\n{content}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LLM_GATEWAY_URL}/query",
                    json={
                        "prompt": prompt,
                        "provider": "ollama",
                        "model": "llama2",
                        "max_tokens": 800
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("data", {}).get("response", "")
                    return self.parse_review_response(llm_response, focus)
                else:
                    return self.fallback_review(content, focus)
                    
        except Exception as e:
            print(f"LLM peer review failed: {e}")
            return self.fallback_review(content, focus)
    
    def parse_review_response(self, response: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Parse LLM review response."""
        suggestions = []
        
        # Extract suggestions (simple heuristic)
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 'suggest' in line.lower()):
                suggestions.append({
                    "type": "improvement",
                    "suggestion": line,
                    "priority": "medium"
                })
        
        # Extract score
        import re
        score_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/\s*10|out of 10)', response)
        score = float(score_match.group(1)) if score_match else 7.5
        
        if not suggestions:
            suggestions = [{"type": "general", "suggestion": "Overall content is well-structured", "priority": "low"}]
        
        return {
            "suggestions": suggestions,
            "overall_score": score,
            "review_text": response
        }
    
    def fallback_review(self, content: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Fallback review without LLM."""
        suggestions = [
            {"type": "clarity", "suggestion": "Consider adding more examples to improve clarity", "priority": "medium"},
            {"type": "structure", "suggestion": "Content structure is adequate", "priority": "low"}
        ]

        # Simple scoring based on content length and structure
        word_count = len(content.split())
        score = min(8.0, 5.0 + (word_count / 200))  # Basic scoring

        return {
            "suggestions": suggestions,
            "overall_score": score,
            "review_text": "Automated review completed with basic analysis"
        }

    async def generate_recommendations(self, documents: List[Dict[str, Any]], recommendation_types: List[str] = None, confidence_threshold: float = 0.4, include_jira_suggestions: bool = False, create_jira_tickets: bool = False, jira_project_key: str = None, timeline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive document recommendations."""
        start_time = time.time()

        # Default recommendation types if none specified
        if not recommendation_types:
            recommendation_types = ["consolidation", "duplicate", "outdated", "quality"]

        all_recommendations = []

        # Generate recommendations for each type
        if "consolidation" in recommendation_types:
            consolidation_recs = await self._generate_consolidation_recommendations(documents, confidence_threshold)
            all_recommendations.extend(consolidation_recs)

        if "duplicate" in recommendation_types:
            duplicate_recs = await self._generate_duplicate_recommendations(documents, confidence_threshold)
            all_recommendations.extend(duplicate_recs)

        if "outdated" in recommendation_types:
            outdated_recs = await self._generate_outdated_recommendations(documents, confidence_threshold)
            all_recommendations.extend(outdated_recs)

        if "quality" in recommendation_types:
            quality_recs = await self._generate_quality_recommendations(documents, confidence_threshold)
            all_recommendations.extend(quality_recs)

        # Sort by priority and confidence
        all_recommendations.sort(key=lambda r: (
            ["critical", "high", "medium", "low"].index(r.get("priority", "low")),
            -r.get("confidence_score", 0)
        ))

        processing_time = time.time() - start_time

        result = {
            "recommendations": all_recommendations,
            "total_documents": len(documents),
            "recommendations_count": len(all_recommendations),
            "processing_time": processing_time,
            "recommendation_types": recommendation_types,
            "confidence_threshold": confidence_threshold
        }

        # Generate Jira ticket suggestions if requested
        jira_ticket_creation = {}
        if include_jira_suggestions and all_recommendations:
            jira_suggestions = self._generate_jira_ticket_suggestions(all_recommendations, documents)
            result["suggested_jira_tickets"] = jira_suggestions

            # Create actual Jira tickets if requested
            if create_jira_tickets:
                ticket_creation_result = await jira_client.create_jira_tickets_from_suggestions(
                    jira_suggestions, jira_project_key
                )
                jira_ticket_creation = ticket_creation_result

        result["jira_ticket_creation"] = jira_ticket_creation

        # Add drift detection and alerts
        drift_analysis = self._detect_drift_and_alerts(documents, all_recommendations)
        result["drift_analysis"] = drift_analysis

        # Add documentation alignment analysis
        alignment_analysis = self._check_documentation_alignment(documents)
        result["alignment_analysis"] = alignment_analysis

        # Add inconclusive recommendation handling
        inconclusive_handling = self._handle_inconclusive_recommendations(documents, all_recommendations, confidence_threshold)
        result["inconclusive_analysis"] = inconclusive_handling

        # Add timeline analysis if timeline is provided
        if timeline:
            timeline_analysis = self._analyze_timeline_and_documents(documents, timeline)
            result["timeline_analysis"] = timeline_analysis

        return result

    async def _generate_consolidation_recommendations(self, documents: List[Dict[str, Any]], confidence_threshold: float) -> List[Dict[str, Any]]:
        """Generate consolidation recommendations."""
        recommendations = []

        if len(documents) < 2:
            return recommendations

        # Group documents by type
        type_groups = {}
        for doc in documents:
            doc_type = doc.get("type", "unknown")
            if doc_type not in type_groups:
                type_groups[doc_type] = []
            type_groups[doc_type].append(doc)

        for doc_type, docs_in_type in type_groups.items():
            if len(docs_in_type) >= 3:
                # Calculate similarity within the group
                avg_similarity = self._calculate_group_similarity(docs_in_type)
                type_confidence = self._calculate_type_consolidation_confidence(docs_in_type, avg_similarity)

                if type_confidence >= confidence_threshold:
                    recommendations.append({
                        "id": str(uuid.uuid4()),
                        "type": "consolidation",
                        "description": f"Consolidate {len(docs_in_type)} {doc_type} documents into a comprehensive guide",
                        "affected_documents": [doc["id"] for doc in docs_in_type],
                        "confidence_score": type_confidence,
                        "priority": "high" if type_confidence > 0.8 or len(docs_in_type) > 5 else "medium",
                        "rationale": f"{len(docs_in_type)} {doc_type} documents with {avg_similarity:.1%} average similarity",
                        "expected_impact": f"Reduce maintenance overhead by {max(20, len(docs_in_type) * 15)}%",
                        "effort_level": "medium" if len(docs_in_type) <= 5 else "high",
                        "tags": ["consolidation", doc_type],
                        "metadata": {
                            "document_type": doc_type,
                            "document_count": len(docs_in_type),
                            "average_similarity": avg_similarity,
                            "consolidation_strategy": "merge_into_comprehensive_guide"
                        }
                    })

        return recommendations

    async def _generate_duplicate_recommendations(self, documents: List[Dict[str, Any]], confidence_threshold: float) -> List[Dict[str, Any]]:
        """Generate duplicate detection recommendations."""
        recommendations = []

        if len(documents) < 2:
            return recommendations

        processed_pairs = set()

        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents):
                if i >= j:
                    continue

                pair_key = f"{min(doc1['id'], doc2['id'])}_{max(doc1['id'], doc2['id'])}"
                if pair_key in processed_pairs:
                    continue

                processed_pairs.add(pair_key)
                similarity_score = self._calculate_simple_similarity(doc1, doc2)

                if similarity_score >= 0.6 and similarity_score >= confidence_threshold:
                    recommendations.append({
                        "id": str(uuid.uuid4()),
                        "type": "duplicate",
                        "description": f"Documents '{doc1.get('title', 'Unknown')}' and '{doc2.get('title', 'Unknown')}' appear to be duplicates",
                        "affected_documents": [doc1["id"], doc2["id"]],
                        "confidence_score": min(similarity_score, 0.95),
                        "priority": "medium",
                        "rationale": f"Content similarity score: {similarity_score:.2f}",
                        "expected_impact": "Eliminate redundancy and reduce maintenance burden",
                        "effort_level": "low",
                        "tags": ["duplicate", "redundancy"],
                        "metadata": {"similarity_score": similarity_score}
                    })

        return recommendations

    async def _generate_outdated_recommendations(self, documents: List[Dict[str, Any]], confidence_threshold: float) -> List[Dict[str, Any]]:
        """Generate outdated document recommendations."""
        recommendations = []
        current_time = datetime.now()

        for doc in documents:
            created_date = self._parse_date(doc.get("dateCreated"))
            updated_date = self._parse_date(doc.get("dateUpdated"))

            if not created_date and not updated_date:
                continue

            reference_date = updated_date or created_date
            age_days = (current_time - reference_date).days

            if age_days > 365:
                confidence = min(age_days / (365 * 2), 0.9)  # Reduced denominator for higher confidence
                if confidence >= confidence_threshold:
                    priority = "high" if age_days > (365 * 2) else "medium"

                    recommendations.append({
                        "id": str(uuid.uuid4()),
                        "type": "outdated",
                        "description": f"Document '{doc.get('title', 'Unknown')}' is {age_days} days old and may be outdated",
                        "affected_documents": [doc["id"]],
                        "confidence_score": confidence,
                        "priority": priority,
                        "rationale": f"Document last updated {age_days} days ago",
                        "expected_impact": "Ensure users have access to current information",
                        "effort_level": "medium",
                        "tags": ["outdated", "maintenance"],
                        "age_days": age_days,
                        "metadata": {"last_updated": reference_date.isoformat() if reference_date else None}
                    })

        return recommendations

    async def _generate_quality_recommendations(self, documents: List[Dict[str, Any]], confidence_threshold: float) -> List[Dict[str, Any]]:
        """Generate comprehensive quality improvement recommendations."""
        recommendations = []

        for doc in documents:
            quality_analysis = await self._analyze_document_quality_comprehensive(doc)
            issues = quality_analysis["issues"]
            metrics = quality_analysis["metrics"]

            if issues:
                confidence = min(len(issues) / 4.0, 0.9)  # More reasonable confidence scaling
                if confidence >= confidence_threshold:
                    priority = self._determine_quality_priority(issues, metrics)

                    recommendations.append({
                        "id": str(uuid.uuid4()),
                        "type": "quality",
                        "description": self._build_quality_description(doc, issues),
                        "affected_documents": [doc["id"]],
                        "confidence_score": confidence,
                        "priority": priority,
                        "rationale": f"Comprehensive quality analysis identified {len(issues)} issues with {metrics['overall_score']:.1f} quality score",
                        "expected_impact": self._calculate_quality_impact(issues, metrics),
                        "effort_level": self._estimate_quality_effort(issues, metrics),
                        "tags": ["quality", "improvement"] + [issue["type"] for issue in issues[:3]],
                        "metadata": {
                            "issues": issues,
                            "metrics": metrics,
                            "quality_score": metrics["overall_score"],
                            "severity_breakdown": self._categorize_issue_severity(issues)
                        }
                    })

        return recommendations

    async def _analyze_document_quality_comprehensive(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive quality analysis on a document."""
        content = document.get("content", "")
        title = document.get("title", "")

        issues = []
        metrics = {
            "word_count": len(content.split()) if content else 0,
            "sentence_count": 0,
            "avg_sentence_length": 0,
            "readability_score": 0,
            "technical_accuracy": 0,
            "structure_score": 0,
            "consistency_score": 0,
            "completeness_score": 0,
            "overall_score": 0
        }

        if not content:
            issues.append({
                "type": "missing_content",
                "severity": "critical",
                "description": "Document has no content",
                "suggestion": "Add comprehensive content to the document"
            })
            return {"issues": issues, "metrics": metrics}

        # 1. Content Length Analysis
        length_issues = self._analyze_content_length(content, metrics)
        issues.extend(length_issues)

        # 2. Clarity and Readability Analysis
        clarity_issues = self._analyze_clarity_and_readability(content, metrics)
        issues.extend(clarity_issues)

        # 3. Technical Accuracy Analysis
        accuracy_issues = self._analyze_technical_accuracy(content, document, metrics)
        issues.extend(accuracy_issues)

        # 4. Structure and Organization Analysis
        structure_issues = self._analyze_structure_and_organization(content, title, metrics)
        issues.extend(structure_issues)

        # 5. Consistency Analysis
        consistency_issues = self._analyze_consistency(content, metrics)
        issues.extend(consistency_issues)

        # 6. Completeness Analysis
        completeness_issues = self._analyze_completeness(content, document, metrics)
        issues.extend(completeness_issues)

        # Calculate overall quality score
        metrics["overall_score"] = self._calculate_overall_quality_score(metrics, issues)

        return {"issues": issues, "metrics": metrics}

    def _analyze_content_length(self, content: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze content length for quality issues."""
        issues = []
        word_count = metrics["word_count"]

        if word_count < 50:
            issues.append({
                "type": "too_short",
                "severity": "high",
                "description": f"Content is too short ({word_count} words)",
                "suggestion": "Expand content with more detailed explanations and examples"
            })
        elif word_count > 3000:
            issues.append({
                "type": "too_verbose",
                "severity": "medium",
                "description": f"Content may be too verbose ({word_count} words)",
                "suggestion": "Consider breaking into multiple documents or condensing information"
            })

        return issues

    def _analyze_clarity_and_readability(self, content: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze clarity and readability issues."""
        issues = []
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        metrics["sentence_count"] = len(sentences)

        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            metrics["avg_sentence_length"] = avg_length

            # Check for overly complex sentences
            complex_sentences = [s for s in sentences if len(s.split()) > 40]
            if complex_sentences:
                issues.append({
                    "type": "complex_sentences",
                    "severity": "medium",
                    "description": f"Found {len(complex_sentences)} overly complex sentences (avg {avg_length:.1f} words)",
                    "suggestion": "Break down complex sentences into simpler, clearer statements"
                })

        # Check for passive voice (simplified)
        passive_indicators = ["is", "are", "was", "were", "be", "been", "being"]
        passive_count = sum(1 for word in content.lower().split() if word in passive_indicators)
        passive_ratio = passive_count / max(1, len(content.split()))

        if passive_ratio > 0.15:  # More than 15% passive voice
            issues.append({
                "type": "passive_voice",
                "severity": "low",
                "description": f"High use of passive voice ({passive_ratio:.1%})",
                "suggestion": "Use active voice for better clarity and engagement"
            })

        # Check for unclear language
        unclear_terms = ["thing", "stuff", "something", "anything", "etc."]
        unclear_count = sum(1 for term in unclear_terms if term in content.lower())

        if unclear_count > 0:
            issues.append({
                "type": "unclear_language",
                "severity": "medium",
                "description": f"Found {unclear_count} unclear terms that reduce specificity",
                "suggestion": "Replace vague terms with specific, clear language"
            })

        return issues

    def _analyze_technical_accuracy(self, content: str, document: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze technical accuracy issues."""
        issues = []
        content_lower = content.lower()

        # Check for code-like content without proper formatting
        if any(keyword in content_lower for keyword in ["function", "class", "import", "def ", "return "]):
            if "```" not in content or content.count("```") < 2:
                issues.append({
                    "type": "unformatted_code",
                    "severity": "high",
                    "description": "Contains code-like content without proper formatting",
                    "suggestion": "Format code blocks using markdown code fences (```)"
                })

        # Check for API references without proper documentation
        if "api" in content_lower:
            api_references = content_lower.count("api")
            if api_references > 3 and not any(term in content_lower for term in ["endpoint", "method", "request", "response"]):
                issues.append({
                    "type": "incomplete_api_docs",
                    "severity": "high",
                    "description": "Mentions APIs but lacks proper API documentation",
                    "suggestion": "Add detailed API documentation with endpoints, methods, and examples"
                })

        # Check for outdated technology references (simplified)
        outdated_terms = ["jquery", "angularjs", "old version"]
        outdated_found = [term for term in outdated_terms if term in content_lower]

        if outdated_found:
            issues.append({
                "type": "outdated_technology",
                "severity": "high",
                "description": f"References potentially outdated technologies: {', '.join(outdated_found)}",
                "suggestion": "Update references to current technology versions"
            })

        metrics["technical_accuracy"] = 1.0 - (len(issues) * 0.2)  # Reduce score for each issue

        return issues

    def _analyze_structure_and_organization(self, content: str, title: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze document structure and organization."""
        issues = []

        # Check for proper heading structure
        lines = content.split('\n')
        headings = [line for line in lines if line.strip().startswith('#')]

        if len(headings) < 2 and len(content.split()) > 200:
            issues.append({
                "type": "poor_structure",
                "severity": "high",
                "description": "Long document lacks proper heading structure",
                "suggestion": "Add headings (# ## ###) to organize content into logical sections"
            })

        # Check heading hierarchy
        if headings:
            heading_levels = []
            for heading in headings:
                level = len(heading) - len(heading.lstrip('#'))
                heading_levels.append(level)

            # Check for proper hierarchy (no skipping levels)
            for i in range(1, len(heading_levels)):
                if heading_levels[i] > heading_levels[i-1] + 1:
                    issues.append({
                        "type": "heading_hierarchy",
                        "severity": "medium",
                        "description": "Heading hierarchy skips levels (e.g., # directly to ###)",
                        "suggestion": "Use proper heading hierarchy without skipping levels"
                    })
                    break

        # Check for logical flow
        transition_words = ["however", "therefore", "additionally", "furthermore", "consequently"]
        transition_count = sum(1 for word in transition_words if word in content.lower())

        if len(content.split()) > 300 and transition_count < 2:
            issues.append({
                "type": "poor_flow",
                "severity": "medium",
                "description": "Document lacks transition words for logical flow",
                "suggestion": "Add transition words to improve content flow and readability"
            })

        metrics["structure_score"] = 1.0 - (len(issues) * 0.15)

        return issues

    def _analyze_consistency(self, content: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze consistency issues in the document."""
        issues = []

        # Check for inconsistent terminology
        content_lower = content.lower()

        # Common inconsistent term pairs
        term_pairs = [
            (["web site", "website"], "website"),
            (["e-mail", "email"], "email"),
            (["user name", "username"], "username"),
            (["log in", "login"], "login")
        ]

        for variants, preferred in term_pairs:
            found_variants = [v for v in variants if v in content_lower]
            if len(found_variants) > 1:
                issues.append({
                    "type": "inconsistent_terminology",
                    "severity": "low",
                    "description": f"Uses multiple variants of '{preferred}': {', '.join(found_variants)}",
                    "suggestion": f"Use consistent terminology: prefer '{preferred}'"
                })

        # Check for formatting consistency
        lines = content.split('\n')
        bullet_points = [line for line in lines if line.strip().startswith(('- ', '* ', '+ '))]

        if len(bullet_points) > 5:
            bullet_styles = set(line.strip()[0] for line in bullet_points)
            if len(bullet_styles) > 1:
                issues.append({
                    "type": "inconsistent_formatting",
                    "severity": "low",
                    "description": f"Mixed bullet point styles: {', '.join(bullet_styles)}",
                    "suggestion": "Use consistent bullet point style throughout"
                })

        metrics["consistency_score"] = 1.0 - (len(issues) * 0.1)

        return issues

    def _analyze_completeness(self, content: str, document: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze completeness issues."""
        issues = []
        content_lower = content.lower()

        # Check for tutorial-like content missing key sections
        if any(word in content_lower for word in ["tutorial", "guide", "how to", "learn"]):
            required_sections = ["prerequisites", "requirements", "example", "conclusion"]
            missing_sections = []

            for section in required_sections:
                if section not in content_lower:
                    missing_sections.append(section)

            if missing_sections:
                issues.append({
                    "type": "missing_sections",
                    "severity": "medium",
                    "description": f"Tutorial missing key sections: {', '.join(missing_sections)}",
                    "suggestion": f"Add missing sections: {', '.join(missing_sections)}"
                })

        # Check for API documentation completeness
        if "api" in content_lower:
            api_elements = ["endpoint", "method", "parameter", "response", "example"]
            missing_elements = [elem for elem in api_elements if elem not in content_lower]

            if len(missing_elements) > 2:
                issues.append({
                    "type": "incomplete_api_docs",
                    "severity": "high",
                    "description": f"API documentation missing key elements: {', '.join(missing_elements[:3])}",
                    "suggestion": "Add comprehensive API documentation with all required elements"
                })

        # Check for contact/support information
        if not any(term in content_lower for term in ["contact", "support", "help", "email", "github"]):
            issues.append({
                "type": "missing_support_info",
                "severity": "low",
                "description": "Document lacks contact or support information",
                "suggestion": "Add contact information or support resources"
            })

        metrics["completeness_score"] = 1.0 - (len(issues) * 0.15)

        return issues

    def _calculate_overall_quality_score(self, metrics: Dict[str, Any], issues: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score based on metrics and issues."""
        # Base score from individual metrics
        base_score = (
            metrics.get("technical_accuracy", 0.8) * 0.25 +
            metrics.get("structure_score", 0.8) * 0.20 +
            metrics.get("consistency_score", 0.8) * 0.15 +
            metrics.get("completeness_score", 0.8) * 0.25 +
            (1.0 if metrics.get("word_count", 0) > 100 else 0.5) * 0.15
        )

        # Reduce score based on issue severity
        severity_penalty = {
            "critical": 0.3,
            "high": 0.2,
            "medium": 0.1,
            "low": 0.05
        }

        total_penalty = sum(severity_penalty.get(issue.get("severity", "low"), 0.05) for issue in issues)

        return max(0.0, min(1.0, base_score - total_penalty))

    def _determine_quality_priority(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        """Determine priority for quality recommendations."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in issues:
            severity_counts[issue.get("severity", "low")] += 1

        if severity_counts["critical"] > 0 or severity_counts["high"] > 2:
            return "high"
        elif severity_counts["high"] > 0 or severity_counts["medium"] > 3:
            return "medium"
        else:
            return "low"

    def _build_quality_description(self, document: Dict[str, Any], issues: List[Dict[str, Any]]) -> str:
        """Build human-readable quality description."""
        title = document.get("title", "Unknown Document")
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]

        if critical_issues:
            return f"Critical quality issues in '{title}' - immediate attention required"
        elif high_issues:
            return f"Multiple quality issues in '{title}' - {len(issues)} issues identified"
        else:
            return f"Quality improvements needed for '{title}' - {len(issues)} issues to address"

    def _calculate_quality_impact(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        """Calculate expected impact of quality improvements."""
        quality_score = metrics.get("overall_score", 0.5)
        issue_count = len(issues)

        if quality_score < 0.3:
            return "Major improvement in user experience and comprehension"
        elif issue_count > 5:
            return "Significant enhancement of document clarity and usefulness"
        else:
            return "Moderate improvement in document quality and readability"

    def _estimate_quality_effort(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        """Estimate effort level for quality improvements."""
        issue_count = len(issues)
        word_count = metrics.get("word_count", 0)

        if issue_count > 8 or word_count > 2000:
            return "high"
        elif issue_count > 4 or word_count > 1000:
            return "medium"
        else:
            return "low"

    def _categorize_issue_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize issues by severity."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in issues:
            severity = issue.get("severity", "low")
            severity_counts[severity] += 1

        return severity_counts

    def _calculate_group_similarity(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate average similarity within a group of documents."""
        if len(documents) < 2:
            return 0.0

        total_similarity = 0.0
        pair_count = 0

        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents):
                if i < j:
                    similarity = self._calculate_simple_similarity(doc1, doc2)
                    total_similarity += similarity
                    pair_count += 1

        return total_similarity / pair_count if pair_count > 0 else 0.0

    def _calculate_type_consolidation_confidence(self, documents: List[Dict[str, Any]], avg_similarity: float) -> float:
        """Calculate confidence for type-based consolidation."""
        doc_count = len(documents)
        count_factor = min(doc_count / 5.0, 0.6)
        similarity_factor = avg_similarity * 0.4
        return min(count_factor + similarity_factor, 0.95)

    def _calculate_simple_similarity(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> float:
        """Calculate simple similarity score between two documents."""
        title1 = doc1.get("title", "").lower()
        title2 = doc2.get("title", "").lower()
        content1 = doc1.get("content", "").lower()
        content2 = doc2.get("content", "").lower()

        title_words1 = set(title1.split())
        title_words2 = set(title2.split())
        title_similarity = len(title_words1 & title_words2) / len(title_words1 | title_words2) if (title_words1 | title_words2) else 0

        content_words1 = set(content1.split())
        content_words2 = set(content2.split())
        content_similarity = len(content_words1 & content_words2) / len(content_words1 | content_words2) if (content_words1 | content_words2) else 0

        return (title_similarity * 0.6) + (content_similarity * 0.4)

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string into datetime object."""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            except:
                pass

        return None

class JiraClient:
    """Jira API client for creating and managing tickets."""

    def __init__(self, base_url: str = None, username: str = None, api_token: str = None):
        self.base_url = base_url or JIRA_BASE_URL
        self.username = username or JIRA_USERNAME
        self.api_token = api_token or JIRA_API_TOKEN
        self.auth_header = self._create_auth_header()

    def _create_auth_header(self) -> str:
        """Create Basic Auth header for Jira API."""
        if not self.username or not self.api_token:
            return ""

        credentials = f"{self.username}:{self.api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

    def is_configured(self) -> bool:
        """Check if Jira client is properly configured."""
        return bool(self.base_url and self.username and self.api_token and self.auth_header)

    async def create_issue(self, project_key: str, summary: str, description: str,
                          issue_type: str = JiraIssueType.TASK,
                          priority: str = JiraPriority.MEDIUM,
                          assignee: str = None,
                          labels: List[str] = None,
                          components: List[str] = None,
                          custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a Jira issue."""
        if not self.is_configured():
            raise HTTPException(status_code=500, detail="Jira client not properly configured")

        url = f"{self.base_url}/rest/api/2/issue"

        # Build issue payload
        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority}
            }
        }

        # Add optional fields
        if assignee:
            issue_data["fields"]["assignee"] = {"name": assignee}

        if labels:
            issue_data["fields"]["labels"] = labels

        if components:
            issue_data["fields"]["components"] = [{"name": comp} for comp in components]

        if custom_fields:
            issue_data["fields"].update(custom_fields)

        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=issue_data, headers=headers)

                if response.status_code == 201:
                    issue_data = response.json()
                    return {
                        "success": True,
                        "issue_key": issue_data["key"],
                        "issue_id": issue_data["id"],
                        "self": issue_data["self"]
                    }
                else:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("errors", {}).get("summary", [error_detail])[0]
                    except:
                        pass

                    return {
                        "success": False,
                        "error": f"Jira API error: {error_detail}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create Jira issue: {str(e)}"
            }

    async def get_project(self, project_key: str) -> Dict[str, Any]:
        """Get Jira project details."""
        if not self.is_configured():
            return {"success": False, "error": "Jira client not configured"}

        url = f"{self.base_url}/rest/api/2/project/{project_key}"
        headers = {"Authorization": self.auth_header}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    project_data = response.json()
                    return {
                        "success": True,
                        "project": {
                            "key": project_data["key"],
                            "name": project_data["name"],
                            "id": project_data["id"]
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Project not found: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get project: {str(e)}"
            }

    def map_recommendation_to_jira(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Map a recommendation to Jira ticket parameters."""
        rec_type = recommendation.get("type", "general")
        priority = recommendation.get("priority", "medium")

        # Map recommendation type to issue type
        issue_type_map = {
            "consolidation": JiraIssueType.TASK,
            "duplicate": JiraIssueType.TASK,
            "outdated": JiraIssueType.TASK,
            "quality": JiraIssueType.BUG
        }

        # Map priority
        priority_map = {
            "critical": JiraPriority.HIGHEST,
            "high": JiraPriority.HIGH,
            "medium": JiraPriority.MEDIUM,
            "low": JiraPriority.LOW
        }

        # Create summary based on recommendation type
        summary_map = {
            "consolidation": "📋 Consolidate Similar Documentation",
            "duplicate": "🔄 Remove Duplicate Documentation",
            "outdated": "⏰ Update Outdated Documentation",
            "quality": "✨ Improve Documentation Quality"
        }

        return {
            "issue_type": issue_type_map.get(rec_type, JiraIssueType.TASK),
            "priority": priority_map.get(priority, JiraPriority.MEDIUM),
            "summary_prefix": summary_map.get(rec_type, "📝 Documentation Task"),
            "labels": ["documentation", rec_type, f"priority-{priority}"]
        }

    def _generate_jira_ticket_suggestions(self, recommendations: List[Dict[str, Any]], documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate suggested Jira tickets based on recommendations."""
        suggested_tickets = []

        # Analyze recommendations to determine what types of tickets to suggest
        rec_types = {}
        priorities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        total_recommendations = len(recommendations)

        for rec in recommendations:
            rec_type = rec.get("type", "general")
            priority = rec.get("priority", "medium")

            rec_types[rec_type] = rec_types.get(rec_type, 0) + 1
            priorities[priority] += 1

        # High-priority ticket for critical issues
        if priorities["critical"] > 0 or priorities["high"] > 0:
            suggested_tickets.append({
                "priority": "Critical" if priorities["critical"] > 0 else "High",
                "issue_type": "Task",
                "summary": f"🔴 CRITICAL: Address Documentation Issues ({total_recommendations} recommendations)",
                "description": f"""**Urgent Documentation Issues Identified**

**Analysis Summary:**
- Total Recommendations: {total_recommendations}
- Critical Issues: {priorities['critical']}
- High Priority Issues: {priorities['high']}
- Documents Analyzed: {len(documents)}

**Key Issues:**
{chr(10).join([f"- {count} {rec_type} recommendations" for rec_type, count in rec_types.items()])}

**Immediate Actions Required:**
1. Review all critical and high-priority recommendations
2. Assess impact on user experience and system functionality
3. Prioritize fixes based on business impact
4. Schedule stakeholder review and approval
5. Allocate resources for urgent documentation improvements

**Success Criteria:**
- All critical issues resolved within 48 hours
- High-priority issues addressed within 1 week
- Documentation quality improved by minimum 20%
- Stakeholder sign-off obtained

**Labels:** documentation, critical, urgent, quality-improvement
**Components:** Technical Writing, Documentation
**Assignee:** Senior Technical Writer
**Epic:** Documentation Quality Initiative""",
                "story_points": 13,
                "epic_link": "Documentation Quality Initiative"
            })

        # Documentation consolidation ticket
        consolidation_count = rec_types.get("consolidation", 0)
        duplicate_count = rec_types.get("duplicate", 0)
        if consolidation_count > 2 or duplicate_count > 2:
            suggested_tickets.append({
                "priority": "High",
                "issue_type": "Task",
                "summary": "📋 Documentation Consolidation & Cleanup Initiative",
                "description": f"""**Documentation Consolidation Required**

**Consolidation Analysis:**
- Consolidation Opportunities: {consolidation_count}
- Duplicate Content Issues: {duplicate_count}
- Total Documents: {len(documents)}

**Objectives:**
1. **Identify Redundancy:** Locate duplicate and overlapping content across documents
2. **Content Consolidation:** Merge similar information into comprehensive guides
3. **Navigation Improvement:** Enhance cross-references and linking between documents
4. **Content Audit:** Remove outdated or redundant information

**Implementation Plan:**
- Phase 1: Content analysis and duplicate identification (1-2 weeks)
- Phase 2: Consolidation planning and stakeholder alignment (1 week)
- Phase 3: Content consolidation and updates (3-4 weeks)
- Phase 4: Navigation improvements and validation (1-2 weeks)

**Success Metrics:**
- Reduce documentation redundancy by 30%
- Improve user navigation efficiency by 40%
- Consolidate at least {min(consolidation_count + duplicate_count, 5)} document sections
- Maintain or improve content freshness scores

**Related Recommendations:**
{chr(10).join([f"- {rec.get('description', '')[:100]}..." for rec in recommendations if rec.get('type') in ['consolidation', 'duplicate']][:3])}

**Labels:** documentation, consolidation, cleanup, maintenance
**Components:** Technical Writing, Information Architecture
**Assignee:** Documentation Architect
**Epic:** Documentation Quality Initiative""",
                "story_points": 21,
                "epic_link": "Documentation Quality Initiative"
            })

        # Quality improvement ticket
        quality_count = rec_types.get("quality", 0)
        if quality_count > 3 or priorities["medium"] > 5:
            suggested_tickets.append({
                "priority": "Medium",
                "issue_type": "Task",
                "summary": "✨ Documentation Quality Enhancement Program",
                "description": f"""**Documentation Quality Improvement Initiative**

**Quality Analysis Results:**
- Quality Recommendations: {quality_count}
- Medium Priority Issues: {priorities['medium']}
- Documents Requiring Attention: {len([r for r in recommendations if r.get('priority') in ['medium', 'high']])}

**Quality Dimensions to Address:**
1. **Content Clarity:** Improve readability and comprehension
2. **Technical Accuracy:** Ensure all technical information is correct and current
3. **Structure & Organization:** Enhance document navigation and flow
4. **Completeness:** Fill identified content gaps
5. **Consistency:** Standardize formatting, terminology, and style

**Implementation Strategy:**
- **Week 1-2:** Quality assessment and priority matrix creation
- **Week 3-6:** High-impact improvements (clarity, structure, consistency)
- **Week 7-10:** Technical accuracy validation and updates
- **Week 11-12:** Completeness review and gap filling

**Quality Gates:**
- Achieve 80% quality score across all documents
- Reduce readability issues by 60%
- Improve technical accuracy by 25%
- Standardize formatting across 100% of documents

**Training & Support:**
- Technical writing best practices workshop
- Quality assessment tools training
- Style guide development and adoption
- Peer review process implementation

**Success Metrics:**
- Average documentation quality score > 0.8
- User satisfaction with documentation > 4.2/5
- Reduction in support tickets related to documentation by 30%
- Time to find information reduced by 40%

**Related Quality Issues:**
{chr(10).join([f"- {rec.get('description', '')[:100]}..." for rec in recommendations if rec.get('type') == 'quality'][:3])}

**Labels:** documentation, quality, enhancement, training
**Components:** Technical Writing, Quality Assurance
**Assignee:** Quality Assurance Lead
**Epic:** Documentation Quality Initiative""",
                "story_points": 34,
                "epic_link": "Documentation Quality Initiative"
            })

        # Outdated content management ticket
        outdated_count = rec_types.get("outdated", 0)
        if outdated_count > 2:
            suggested_tickets.append({
                "priority": "Medium",
                "issue_type": "Task",
                "summary": "⏰ Outdated Documentation Review & Update Program",
                "description": f"""**Outdated Documentation Management Initiative**

**Outdated Content Analysis:**
- Outdated Documents Identified: {outdated_count}
- Documents Requiring Updates: {len([r for r in recommendations if r.get('type') == 'outdated'])}
- Total Document Inventory: {len(documents)}

**Objectives:**
1. **Freshness Assessment:** Evaluate all documents for currency and relevance
2. **Update Planning:** Prioritize updates based on business impact and usage
3. **Content Refresh:** Update technical information, examples, and references
4. **Maintenance Process:** Establish ongoing freshness monitoring

**Implementation Approach:**
- **Phase 1:** Content freshness audit and impact assessment (2 weeks)
- **Phase 2:** Priority matrix creation and update planning (1 week)
- **Phase 3:** Content updates and technical validation (4-6 weeks)
- **Phase 4:** Review process and stakeholder approval (2 weeks)

**Update Categories:**
- **Critical Updates:** Security, API changes, breaking changes
- **Important Updates:** Feature changes, best practices, examples
- **Minor Updates:** Formatting, links, references, style

**Success Criteria:**
- All documents updated within acceptable freshness windows
- Technical accuracy maintained at 95%+
- User feedback on documentation freshness > 4.0/5
- Automated freshness monitoring implemented

**Maintenance Strategy:**
- Quarterly freshness reviews for high-traffic documents
- Monthly reviews for medium-traffic content
- Automated alerts for documents approaching freshness thresholds
- Integration with product release cycle

**Related Outdated Content:**
{chr(10).join([f"- {rec.get('description', '')[:100]}..." for rec in recommendations if rec.get('type') == 'outdated'][:3])}

**Labels:** documentation, outdated, maintenance, updates
**Components:** Technical Writing, Product Management
**Assignee:** Content Maintenance Lead
**Epic:** Documentation Quality Initiative""",
                "story_points": 21,
                "epic_link": "Documentation Quality Initiative"
            })

        # Sort tickets by priority
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        suggested_tickets.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return suggested_tickets

    def _detect_drift_and_alerts(self, documents: List[Dict[str, Any]], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect documentation and API drift and generate alerts."""
        drift_alerts = []
        api_drift_issues = []
        documentation_drift_issues = []

        # Analyze documents for drift indicators
        for doc in documents:
            content = doc.get("content", "")
            title = doc.get("title", "")
            last_updated = doc.get("last_updated", doc.get("dateUpdated"))

            # API drift detection
            if content:
                # Check for outdated API references
                api_patterns = [
                    r"api/v\d+",  # API version patterns
                    r"endpoint.*deprecated",  # Deprecated endpoint mentions
                    r"breaking.*change",  # Breaking change references
                    r"migration.*required",  # Migration requirements
                ]

                for pattern in api_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        api_drift_issues.append({
                            "document_id": doc.get("id", title),
                            "document_title": title,
                            "drift_type": "api_reference",
                            "pattern": pattern,
                            "severity": "medium",
                            "recommendation": "Review API references for currency and update if necessary"
                        })

                # Check for version mismatches
                version_refs = re.findall(r"v\d+\.\d+", content)
                if len(set(version_refs)) > 2:  # Multiple different versions
                    api_drift_issues.append({
                        "document_id": doc.get("id", title),
                        "document_title": title,
                        "drift_type": "version_conflict",
                        "versions_found": list(set(version_refs)),
                        "severity": "high",
                        "recommendation": "Consolidate version references to ensure consistency"
                    })

            # Documentation drift detection
            if last_updated:
                try:
                    # Parse last updated date
                    if isinstance(last_updated, str):
                        if "T" in last_updated:
                            last_updated_date = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                        else:
                            last_updated_date = datetime.strptime(last_updated, "%Y-%m-%d")
                    else:
                        last_updated_date = last_updated

                    days_since_update = (datetime.now() - last_updated_date.replace(tzinfo=None)).days

                    if days_since_update > 365:  # Over a year old
                        documentation_drift_issues.append({
                            "document_id": doc.get("id", title),
                            "document_title": title,
                            "drift_type": "outdated_content",
                            "days_since_update": days_since_update,
                            "severity": "high" if days_since_update > 730 else "medium",
                            "recommendation": "Review and update documentation content for currency"
                        })
                    elif days_since_update > 180:  # Over 6 months old
                        documentation_drift_issues.append({
                            "document_id": doc.get("id", title),
                            "document_title": title,
                            "drift_type": "aging_content",
                            "days_since_update": days_since_update,
                            "severity": "low",
                            "recommendation": "Consider updating documentation for best practices and current standards"
                        })

                except (ValueError, AttributeError) as e:
                    documentation_drift_issues.append({
                        "document_id": doc.get("id", title),
                        "document_title": title,
                        "drift_type": "date_parsing_error",
                        "error": str(e),
                        "severity": "low",
                        "recommendation": "Fix date format in document metadata"
                    })

        # Combine all drift alerts
        drift_alerts.extend(api_drift_issues)
        drift_alerts.extend(documentation_drift_issues)

        # Generate summary statistics
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        drift_types = {}

        for alert in drift_alerts:
            severity = alert.get("severity", "low")
            severity_counts[severity] += 1
            drift_type = alert.get("drift_type", "unknown")
            drift_types[drift_type] = drift_types.get(drift_type, 0) + 1

        return {
            "drift_alerts": drift_alerts,
            "summary": {
                "total_alerts": len(drift_alerts),
                "severity_breakdown": severity_counts,
                "drift_type_breakdown": drift_types,
                "api_drift_count": len(api_drift_issues),
                "documentation_drift_count": len(documentation_drift_issues)
            },
            "critical_alerts": [alert for alert in drift_alerts if alert.get("severity") == "high"]
        }

    def _check_documentation_alignment(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check documentation alignment across the document set."""
        alignment_issues = []
        alignment_score = 1.0
        penalty_factors = []

        if len(documents) < 2:
            return {
                "alignment_score": 1.0,
                "issues": [],
                "recommendations": ["Need multiple documents to assess alignment"]
            }

        # Check for consistency in terminology
        all_terms = []
        term_frequency = {}

        for doc in documents:
            content = doc.get("content", "").lower()
            # Extract potential technical terms (capitalized words, API endpoints, etc.)
            terms = re.findall(r'\b[A-Z][a-zA-Z]*\b|\bapi/[a-zA-Z_]+\b|\b[A-Z_][A-Z_]+\b', content)
            all_terms.extend(terms)

        # Count term frequencies
        for term in all_terms:
            term_frequency[term] = term_frequency.get(term, 0) + 1

        # Check for inconsistent terminology usage
        inconsistent_terms = []
        for term, count in term_frequency.items():
            if count == 1 and len(term) > 3:  # Terms used only once might indicate inconsistency
                inconsistent_terms.append(term)

        if inconsistent_terms:
            alignment_issues.append({
                "type": "terminology_inconsistency",
                "severity": "medium",
                "description": f"Found {len(inconsistent_terms)} terms used only once across documents",
                "examples": inconsistent_terms[:5],
                "recommendation": "Standardize terminology usage across documentation"
            })
            penalty_factors.append(0.1)

        # Check for structural alignment
        structure_patterns = []
        for doc in documents:
            content = doc.get("content", "")
            # Look for common structural elements
            has_intro = bool(re.search(r'\b(intro|overview|summary)\b', content, re.IGNORECASE))
            has_examples = bool(re.search(r'\b(example|sample|code)\b', content, re.IGNORECASE))
            has_prerequisites = bool(re.search(r'\b(prereq|requirement|before|needed)\b', content, re.IGNORECASE))

            structure_patterns.append({
                "document": doc.get("title", "Unknown"),
                "has_intro": has_intro,
                "has_examples": has_examples,
                "has_prerequisites": has_prerequisites
            })

        # Check consistency in structure
        intro_consistency = len([p for p in structure_patterns if p["has_intro"]]) / len(structure_patterns)
        if intro_consistency < 0.7:
            alignment_issues.append({
                "type": "structural_inconsistency",
                "severity": "medium",
                "description": f"Only {intro_consistency:.1%} of documents have introduction sections",
                "recommendation": "Ensure consistent document structure across all documentation"
            })
            penalty_factors.append(0.15)

        # Check for cross-references
        cross_ref_count = 0
        for doc in documents:
            content = doc.get("content", "")
            # Look for see also, refer to, etc.
            cross_refs = re.findall(r'\b(see also|refer to|see|reference|link)\b', content, re.IGNORECASE)
            cross_ref_count += len(cross_refs)

        if cross_ref_count < len(documents) * 0.5:  # Less than 0.5 cross-refs per document
            alignment_issues.append({
                "type": "poor_cross_referencing",
                "severity": "low",
                "description": f"Low cross-referencing between documents ({cross_ref_count} total references)",
                "recommendation": "Add cross-references to improve document navigation and coherence"
            })
            penalty_factors.append(0.05)

        # Calculate alignment score
        for penalty in penalty_factors:
            alignment_score -= penalty
        alignment_score = max(0.0, alignment_score)

        return {
            "alignment_score": alignment_score,
            "issues": alignment_issues,
            "structure_analysis": structure_patterns,
            "terminology_consistency": 1.0 - (len(inconsistent_terms) / max(len(term_frequency), 1)),
            "cross_reference_density": cross_ref_count / len(documents),
            "recommendations": [issue["recommendation"] for issue in alignment_issues]
        }

    def _handle_inconclusive_recommendations(self, documents: List[Dict[str, Any]], recommendations: List[Dict[str, Any]], confidence_threshold: float) -> Dict[str, Any]:
        """Handle cases where information is insufficient for confident recommendations."""
        inconclusive_handling = {
            "insufficient_data_warnings": [],
            "data_quality_assessment": {},
            "confidence_analysis": {},
            "suggested_improvements": []
        }

        # Analyze data sufficiency for each recommendation type
        rec_types = ["consolidation", "duplicate", "outdated", "quality"]
        data_sufficiency = {}

        for rec_type in rec_types:
            type_recs = [r for r in recommendations if r.get("type") == rec_type]
            confidence_scores = [r.get("confidence_score", 0) for r in type_recs]

            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                low_confidence_count = len([c for c in confidence_scores if c < confidence_threshold])

                data_sufficiency[rec_type] = {
                    "recommendations_count": len(type_recs),
                    "average_confidence": avg_confidence,
                    "low_confidence_count": low_confidence_count,
                    "data_sufficient": avg_confidence >= confidence_threshold * 0.8
                }

                if not data_sufficiency[rec_type]["data_sufficient"]:
                    inconclusive_handling["insufficient_data_warnings"].append({
                        "recommendation_type": rec_type,
                        "issue": "Low confidence in recommendations",
                        "average_confidence": avg_confidence,
                        "low_confidence_recommendations": low_confidence_count,
                        "reason": "Insufficient data or inconsistent document patterns"
                    })

        # Assess overall data quality
        total_docs = len(documents)
        avg_doc_length = sum(len(doc.get("content", "")) for doc in documents) / max(total_docs, 1)
        docs_with_dates = len([d for d in documents if d.get("last_updated") or d.get("dateUpdated")])

        inconclusive_handling["data_quality_assessment"] = {
            "total_documents": total_docs,
            "average_document_length": avg_doc_length,
            "documents_with_dates": docs_with_dates,
            "date_coverage": docs_with_dates / max(total_docs, 1),
            "data_quality_score": min(1.0, (avg_doc_length / 1000) * (docs_with_dates / max(total_docs, 1)))
        }

        # Generate confidence analysis
        inconclusive_handling["confidence_analysis"] = {
            "overall_confidence_threshold": confidence_threshold,
            "recommendation_types_analysis": data_sufficiency,
            "confidence_distribution": {
                "high": len([r for r in recommendations if r.get("confidence_score", 0) >= 0.8]),
                "medium": len([r for r in recommendations if 0.5 <= r.get("confidence_score", 0) < 0.8]),
                "low": len([r for r in recommendations if r.get("confidence_score", 0) < 0.5])
            }
        }

        # Generate suggested improvements for inconclusive cases
        if inconclusive_handling["insufficient_data_warnings"]:
            for warning in inconclusive_handling["insufficient_data_warnings"]:
                rec_type = warning["recommendation_type"]

                if rec_type == "consolidation":
                    inconclusive_handling["suggested_improvements"].append({
                        "type": "data_collection",
                        "recommendation_type": rec_type,
                        "improvement": "Add more documents or improve document categorization",
                        "expected_impact": "Better consolidation recommendations with higher confidence"
                    })
                elif rec_type == "duplicate":
                    inconclusive_handling["suggested_improvements"].append({
                        "type": "content_analysis",
                        "recommendation_type": rec_type,
                        "improvement": "Enhance content similarity analysis with better text processing",
                        "expected_impact": "More accurate duplicate detection with improved confidence"
                    })
                elif rec_type == "outdated":
                    inconclusive_handling["suggested_improvements"].append({
                        "type": "metadata_enhancement",
                        "recommendation_type": rec_type,
                        "improvement": "Ensure all documents have proper dateCreated/dateUpdated metadata",
                        "expected_impact": "More reliable outdated content detection"
                    })
                elif rec_type == "quality":
                    inconclusive_handling["suggested_improvements"].append({
                        "type": "quality_metrics",
                        "recommendation_type": rec_type,
                        "improvement": "Expand quality assessment criteria and improve scoring algorithms",
                        "expected_impact": "More comprehensive and confident quality recommendations"
                    })

        return inconclusive_handling

    def _analyze_timeline_and_documents(self, documents: List[Dict[str, Any]], timeline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze timeline and document placement for coherence and completeness."""
        timeline_analysis = {
            "timeline_structure": {},
            "document_placement": {},
            "timeline_recommendations": [],
            "placement_score": 0.0,
            "gaps_identified": []
        }

        if not timeline:
            timeline_analysis["timeline_structure"]["status"] = "No timeline provided"
            return timeline_analysis

        # Extract timeline phases
        timeline_phases = timeline.get("phases", [])
        if not timeline_phases:
            timeline_analysis["timeline_structure"]["status"] = "No phases defined"
            return timeline_analysis

        # Analyze timeline structure
        total_duration = sum(phase.get("duration_weeks", 0) for phase in timeline_phases)
        timeline_analysis["timeline_structure"] = {
            "phase_count": len(timeline_phases),
            "total_duration_weeks": total_duration,
            "phases": timeline_phases,
            "structure_assessment": "good" if total_duration >= 4 else "too_short"
        }

        # Analyze document placement on timeline
        document_placements = self._analyze_document_timeline_placement(documents, timeline_phases)
        timeline_analysis["document_placement"] = document_placements

        # Calculate placement score
        total_docs = len(documents)
        placed_docs = len([p for p in document_placements if p.get("placement_reason") != "unplaced"])
        placement_score = placed_docs / total_docs if total_docs > 0 else 0.0
        timeline_analysis["placement_score"] = placement_score

        # Generate timeline recommendations
        timeline_analysis["timeline_recommendations"] = self._generate_timeline_recommendations(
            document_placements, timeline_phases, placement_score
        )

        # Identify gaps
        timeline_analysis["gaps_identified"] = self._identify_timeline_gaps(
            document_placements, timeline_phases
        )

        return timeline_analysis

    def _analyze_document_timeline_placement(self, documents: List[Dict[str, Any]], timeline_phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze how documents fit into the timeline."""
        placements = []

        for doc in documents:
            placement = {
                "document_id": doc.get("id", "unknown"),
                "document_title": doc.get("title", "Unknown"),
                "placement_phase": None,
                "placement_reason": "unplaced",
                "relevance_score": 0.0,
                "timeline_context": {}
            }

            # Try to determine placement based on timestamps
            last_updated = doc.get("last_updated") or doc.get("dateUpdated")
            if last_updated:
                try:
                    if isinstance(last_updated, str):
                        if "T" in last_updated:
                            doc_date = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                        else:
                            doc_date = datetime.strptime(last_updated, "%Y-%m-%d")
                    else:
                        doc_date = last_updated

                    # Find the most relevant phase for this document
                    relevant_phase = self._find_relevant_timeline_phase(doc_date, timeline_phases)
                    if relevant_phase:
                        placement["placement_phase"] = relevant_phase["name"]
                        placement["placement_reason"] = "timestamp_match"
                        placement["relevance_score"] = self._calculate_timeline_relevance(doc_date, relevant_phase)
                        placement["timeline_context"] = {
                            "phase_start": relevant_phase.get("start_week", 0),
                            "phase_duration": relevant_phase.get("duration_weeks", 0),
                            "document_date": doc_date.isoformat()
                        }
                except (ValueError, AttributeError):
                    placement["placement_reason"] = "date_parse_error"

            # If no timestamp match, try content-based placement
            if placement["placement_reason"] == "unplaced":
                content_placement = self._analyze_content_based_placement(doc, timeline_phases)
                if content_placement:
                    placement.update(content_placement)

            placements.append(placement)

        return placements

    def _find_relevant_timeline_phase(self, doc_date: datetime, timeline_phases: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the most relevant timeline phase for a document based on date."""
        # This is a simplified version - in practice you'd need to know the project start date
        # For now, we'll assume phases are in chronological order
        for phase in timeline_phases:
            # This is a placeholder - you'd need actual date mapping logic
            if phase.get("start_week", 0) >= 0:  # Basic check
                return phase
        return None

    def _calculate_timeline_relevance(self, doc_date: datetime, phase: Dict[str, Any]) -> float:
        """Calculate how relevant a document is to a timeline phase."""
        # Placeholder relevance calculation
        # In practice, this would consider phase duration, document recency, etc.
        return 0.8  # High relevance for matched documents

    def _analyze_content_based_placement(self, document: Dict[str, Any], timeline_phases: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze document content to determine timeline placement."""
        content = document.get("content", "").lower()

        # Simple keyword-based phase detection
        phase_keywords = {
            "planning": ["plan", "design", "architecture", "requirements"],
            "development": ["implement", "code", "build", "develop"],
            "testing": ["test", "qa", "quality", "validate"],
            "deployment": ["deploy", "release", "production", "launch"]
        }

        for phase in timeline_phases:
            phase_name = phase.get("name", "").lower()
            for keyword_phase, keywords in phase_keywords.items():
                if keyword_phase in phase_name:
                    if any(keyword in content for keyword in keywords):
                        return {
                            "placement_phase": phase["name"],
                            "placement_reason": "content_match",
                            "relevance_score": 0.6,
                            "timeline_context": {"matched_keywords": keywords}
                        }

        return None

    def _generate_timeline_recommendations(self, placements: List[Dict[str, Any]], timeline_phases: List[Dict[str, Any]], placement_score: float) -> List[str]:
        """Generate recommendations based on timeline analysis."""
        recommendations = []

        if placement_score < 0.5:
            recommendations.append("Low document-timeline alignment detected. Consider adding more phase-specific documentation.")

        if placement_score > 0.8:
            recommendations.append("Excellent document-timeline alignment. Documentation appears well-structured.")

        # Check for phase coverage
        phase_coverage = {}
        for placement in placements:
            phase = placement.get("placement_phase")
            if phase:
                phase_coverage[phase] = phase_coverage.get(phase, 0) + 1

        for phase in timeline_phases:
            phase_name = phase.get("name", "")
            doc_count = phase_coverage.get(phase_name, 0)
            if doc_count == 0:
                recommendations.append(f"No documents found for phase '{phase_name}'. Consider adding documentation.")

        return recommendations

    def _identify_timeline_gaps(self, placements: List[Dict[str, Any]], timeline_phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify gaps in timeline coverage."""
        gaps = []

        phase_coverage = {}
        for placement in placements:
            phase = placement.get("placement_phase")
            if phase:
                if phase not in phase_coverage:
                    phase_coverage[phase] = []
                phase_coverage[phase].append(placement)

        for phase in timeline_phases:
            phase_name = phase.get("name", "")
            if phase_name not in phase_coverage:
                gaps.append({
                    "gap_type": "no_documents",
                    "phase": phase_name,
                    "severity": "high",
                    "description": f"No documents found for phase '{phase_name}'"
                })
            elif len(phase_coverage[phase_name]) < 2:
                gaps.append({
                    "gap_type": "insufficient_coverage",
                    "phase": phase_name,
                    "severity": "medium",
                    "description": f"Limited documentation coverage for phase '{phase_name}'"
                })

        return gaps

    async def create_jira_tickets_from_suggestions(self, suggested_tickets: List[Dict[str, Any]], project_key: str = None) -> Dict[str, Any]:
        """Create actual Jira tickets from suggested tickets."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Jira client not configured",
                "tickets_created": 0,
                "tickets_failed": len(suggested_tickets),
                "results": []
            }

        # Use default project if none specified
        if not project_key:
            project_key = JIRA_DEFAULT_PROJECT or "DOC"

        results = []
        created_count = 0
        failed_count = 0

        for ticket in suggested_tickets:
            try:
                # Create the Jira issue
                create_result = await self.create_issue(
                    project_key=project_key,
                    summary=ticket["summary"],
                    description=ticket["description"],
                    issue_type=ticket["issue_type"],
                    priority=ticket["priority"],
                    labels=ticket.get("labels", []),
                    components=ticket.get("components", []),
                    custom_fields={
                        "customfield_10010": ticket.get("epic_link", "Documentation Quality Initiative")  # Epic Link
                    }
                )

                if create_result["success"]:
                    created_count += 1
                    results.append({
                        "suggestion": ticket,
                        "creation_result": create_result,
                        "status": "created"
                    })
                else:
                    failed_count += 1
                    results.append({
                        "suggestion": ticket,
                        "creation_result": create_result,
                        "status": "failed"
                    })

            except Exception as e:
                failed_count += 1
                results.append({
                    "suggestion": ticket,
                    "error": str(e),
                    "status": "error"
                })

        return {
            "success": created_count > 0,
            "tickets_created": created_count,
            "tickets_failed": failed_count,
            "total_suggestions": len(suggested_tickets),
            "project_key": project_key,
            "results": results
        }

    async def create_jira_tickets_for_recommendations(self, recommendations: List[Dict[str, Any]], documents: List[Dict[str, Any]] = None, project_key: str = None) -> Dict[str, Any]:
        """Create Jira tickets directly from recommendations."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Jira client not configured",
                "tickets_created": 0,
                "tickets_failed": len(recommendations)
            }

        if documents is None:
            documents = []

        # Generate suggestions first
        suggestions = self._generate_jira_ticket_suggestions(recommendations, documents)

        # Then create the tickets
        return await self.create_jira_tickets_from_suggestions(suggestions, project_key)


# Initialize clients
summarizer = SimpleSummarizer()
jira_client = JiraClient()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": time.time(),
        "environment": ENVIRONMENT,
        "llm_gateway_url": LLM_GATEWAY_URL
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": SERVICE_NAME,
        "title": SERVICE_TITLE,
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "summarize": "/summarize",
            "categorize": "/categorize",
            "peer_review": "/peer-review",
            "recommendations": "/recommendations",
            "capabilities": "/capabilities"
        },
        "features": {
            "llm_integration": True,
            "fallback_processing": True,
            "batch_processing": True,
            "peer_review": True,
            "recommendations": True
        }
    }

@app.get("/capabilities")
async def get_capabilities():
    """Get service capabilities."""
    return {
        "summarization": {
            "formats": ["markdown", "plain", "structured"],
            "styles": ["professional", "casual", "technical", "executive"],
            "max_length": 2000
        },
        "categorization": {
            "default_categories": summarizer.categories,
            "custom_categories": True,
            "confidence_scoring": True
        },
        "peer_review": {
            "review_types": ["general", "technical", "editorial", "compliance"],
            "focus_areas": ["clarity", "completeness", "accuracy", "style", "structure"],
            "scoring": "0-10 scale"
        },
        "recommendations": {
            "types": ["consolidation", "duplicate", "outdated", "quality"],
            "confidence_threshold": "0.4-0.9",
            "max_documents": 100,
            "batch_processing": True,
            "priority_levels": ["critical", "high", "medium", "low"]
        }
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_document(request: SummarizeRequest):
    """Summarize a document."""
    try:
        summary = await summarizer.summarize_with_llm(
            request.content, 
            request.max_length,
            getattr(request, 'style', 'professional')
        )
        
        return SummarizeResponse(
            success=True,
            data={
                "summary": summary,
                "original_length": len(request.content.split()),
                "summary_length": len(summary.split()),
                "compression_ratio": len(summary) / len(request.content) if request.content else 0,
                "format": request.format
            }
        )
        
    except Exception as e:
        return SummarizeResponse(
            success=False,
            error=str(e)
        )

@app.post("/categorize", response_model=CategorizeResponse)
async def categorize_document(request: CategorizeRequest):
    """Categorize a document."""
    try:
        content = request.document.get("content", "")
        result = await summarizer.categorize_with_llm(content, request.candidate_categories)
        
        return CategorizeResponse(
            success=True,
            document_id=request.document.get("id", str(uuid.uuid4())),
            category=result["category"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            metadata={
                "use_zero_shot": request.use_zero_shot,
                "candidate_categories": request.candidate_categories or summarizer.categories,
                "content_length": len(content)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/peer-review", response_model=PeerReviewResponse)
async def peer_review_document(request: PeerReviewRequest):
    """Perform peer review on a document."""
    try:
        result = await summarizer.peer_review_with_llm(
            request.content,
            request.review_type,
            request.focus_areas
        )

        return PeerReviewResponse(
            success=True,
            review_id=str(uuid.uuid4()),
            suggestions=result["suggestions"],
            overall_score=result["overall_score"],
            metadata={
                "review_type": request.review_type,
                "focus_areas": request.focus_areas or ["clarity", "completeness", "accuracy"],
                "content_length": len(request.content),
                "review_timestamp": time.time()
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations", response_model=RecommendationResponse)
async def generate_recommendations(request: RecommendationRequest):
    """Generate document recommendations."""
    try:
        result = await summarizer.generate_recommendations(
            request.documents,
            request.recommendation_types,
            request.confidence_threshold,
            request.include_jira_suggestions,
            request.create_jira_tickets,
            request.jira_project_key,
            request.timeline
        )

        return RecommendationResponse(
            success=True,
            recommendations=result["recommendations"],
            total_documents=result["total_documents"],
            recommendations_count=result["recommendations_count"],
            processing_time=result["processing_time"],
            metadata={
                "recommendation_types": result["recommendation_types"],
                "confidence_threshold": result["confidence_threshold"],
                "timestamp": time.time()
            },
            suggested_jira_tickets=result.get("suggested_jira_tickets", []),
            jira_ticket_creation=result.get("jira_ticket_creation", {}),
            drift_analysis=result.get("drift_analysis", {}),
            alignment_analysis=result.get("alignment_analysis", {}),
            inconclusive_analysis=result.get("inconclusive_analysis", {}),
            timeline_analysis=result.get("timeline_analysis", {})
        )

    except Exception as e:
        return RecommendationResponse(
            success=False,
            total_documents=len(request.documents),
            recommendations_count=0,
            processing_time=0.0,
            error=f"Recommendation generation failed: {str(e)}",
            suggested_jira_tickets=[],
            jira_ticket_creation={},
            drift_analysis={},
            alignment_analysis={},
            inconclusive_analysis={},
            timeline_analysis={}
        )

@app.post("/api/v1/recommendations")
async def recommendations_v1(request: RecommendationRequest):
    """Generate document recommendations using standardized API v1 interface."""
    try:
        result = await summarizer.generate_recommendations(
            request.documents,
            request.recommendation_types,
            request.confidence_threshold,
            request.include_jira_suggestions,
            request.create_jira_tickets,
            request.jira_project_key,
            request.timeline
        )

        return {
            "success": True,
            "recommendations": result["recommendations"],
            "total_documents": result["total_documents"],
            "recommendations_count": result["recommendations_count"],
            "processing_time": result["processing_time"],
            "suggested_jira_tickets": result.get("suggested_jira_tickets", []),
            "jira_ticket_creation": result.get("jira_ticket_creation", {}),
            "drift_analysis": result.get("drift_analysis", {}),
            "alignment_analysis": result.get("alignment_analysis", {}),
            "inconclusive_analysis": result.get("inconclusive_analysis", {}),
            "timeline_analysis": result.get("timeline_analysis", {}),
            "metadata": {
                "recommendation_types": result["recommendation_types"],
                "confidence_threshold": result["confidence_threshold"],
                "timestamp": time.time(),
                "version": SERVICE_VERSION
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Recommendation generation failed: {str(e)}",
            "total_documents": len(request.documents),
            "recommendations_count": 0,
            "processing_time": 0.0,
            "suggested_jira_tickets": [],
            "jira_ticket_creation": {},
            "drift_analysis": {},
            "alignment_analysis": {},
            "inconclusive_analysis": {},
            "timeline_analysis": {}
        }

@app.post("/jira/create-tickets", response_model=JiraTicketResponse)
async def create_jira_tickets(request: JiraTicketRequest):
    """Create Jira tickets from suggestions."""
    try:
        if not jira_client.is_configured():
            raise HTTPException(
                status_code=500,
                detail="Jira client not configured. Please set JIRA_BASE_URL, JIRA_USERNAME, and JIRA_API_TOKEN environment variables."
            )

        result = await jira_client.create_jira_tickets_from_suggestions(
            request.suggested_tickets,
            request.project_key
        )

        return JiraTicketResponse(
            success=result["success"],
            tickets_created=result["tickets_created"],
            tickets_failed=result["tickets_failed"],
            total_requested=len(request.suggested_tickets),
            jira_project=request.project_key or JIRA_DEFAULT_PROJECT,
            ticket_details=result["results"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Jira ticket creation failed: {str(e)}")


@app.post("/batch/summarize")
async def batch_summarize(requests: List[SummarizeRequest]):
    """Batch summarize multiple documents."""
    results = []
    
    for request in requests:
        try:
            result = await summarize_document(request)
            results.append(result)
        except Exception as e:
            results.append(SummarizeResponse(success=False, error=str(e)))
    
    return {
        "batch_results": results,
        "total_processed": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success)
    }

@app.post("/api/v1/summarize")
async def summarize_v1(request: SummarizeRequest):
    """Summarize text content using standardized API v1 interface."""
    try:
        summarizer = SimpleSummarizer()

        # Generate summary
        summary_text = await summarizer.summarize_with_llm(
            request.content,
            max_length=request.max_length,
            style=request.style or "professional"
        )

        # Get content analysis
        analysis = summarizer.analyze_content(request.content)

        # Categorize content
        category_result = await summarizer.categorize_with_llm(request.content)

        response_data = {
            "summary_id": str(uuid.uuid4()),
            "original_length": len(request.content),
            "summary_length": len(summary_text),
            "compression_ratio": len(summary_text) / len(request.content) if request.content else 0,
            "summary": summary_text,
            "format": request.format,
            "style": request.style,
            "category": category_result.get("category", "Unknown"),
            "confidence": category_result.get("confidence", 0.0),
            "content_analysis": analysis,
            "processing_time": 0.5,  # Mock processing time
            "timestamp": time.time(),
            "metadata": {
                "llm_model": "llama2",
                "provider": "ollama",
                "version": SERVICE_VERSION
            }
        }

        return SummarizeResponse(
            success=True,
            data=response_data
        )

    except Exception as e:
        return SummarizeResponse(
            success=False,
            error=f"Summarization failed: {str(e)}"
        )

@app.get("/test/llm-connection")
async def test_llm_connection():
    """Test connection to LLM Gateway."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LLM_GATEWAY_URL}/health")
            if response.status_code == 200:
                return {
                    "llm_gateway_status": "connected",
                    "response": response.json()
                }
            else:
                return {
                    "llm_gateway_status": "error",
                    "status_code": response.status_code
                }
    except Exception as e:
        return {
            "llm_gateway_status": "unreachable",
            "error": str(e)
        }

if __name__ == "__main__":
    """Run the Summarizer Hub service directly."""
    import uvicorn
    print(f"🚀 Starting {SERVICE_TITLE} Service...")
    print(f"🔗 LLM Gateway: {LLM_GATEWAY_URL}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
