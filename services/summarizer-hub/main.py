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
from datetime import datetime, timedelta

# Service configuration
SERVICE_NAME = "summarizer-hub"
SERVICE_TITLE = "Summarizer Hub"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5160

# Environment configuration
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

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

class RecommendationRequest(BaseModel):
    """Request model for document recommendations."""
    documents: List[Dict[str, Any]]
    recommendation_types: Optional[List[str]] = None  # consolidation, duplicate, outdated, quality
    confidence_threshold: float = 0.4

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

    async def generate_recommendations(self, documents: List[Dict[str, Any]], recommendation_types: List[str] = None, confidence_threshold: float = 0.4) -> Dict[str, Any]:
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

        return {
            "recommendations": all_recommendations,
            "total_documents": len(documents),
            "recommendations_count": len(all_recommendations),
            "processing_time": processing_time,
            "recommendation_types": recommendation_types,
            "confidence_threshold": confidence_threshold
        }

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

# Initialize summarizer
summarizer = SimpleSummarizer()

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
            request.confidence_threshold
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
            }
        )

    except Exception as e:
        return RecommendationResponse(
            success=False,
            total_documents=len(request.documents),
            recommendations_count=0,
            processing_time=0.0,
            error=f"Recommendation generation failed: {str(e)}"
        )

@app.post("/api/v1/recommendations")
async def recommendations_v1(request: RecommendationRequest):
    """Generate document recommendations using standardized API v1 interface."""
    try:
        result = await summarizer.generate_recommendations(
            request.documents,
            request.recommendation_types,
            request.confidence_threshold
        )

        return {
            "success": True,
            "recommendations": result["recommendations"],
            "total_documents": result["total_documents"],
            "recommendations_count": result["recommendations_count"],
            "processing_time": result["processing_time"],
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
            "processing_time": 0.0
        }

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
