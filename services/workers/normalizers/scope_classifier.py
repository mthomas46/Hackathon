"""Scope Classifier Worker - Classify documents into MCP tiers."""

import logging
import re
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseNormalizer, Document, WorkerResult

logger = logging.getLogger(__name__)


class ScopeClassifier(BaseNormalizer):
    """Classify documents into hierarchical MCP tiers."""
    
    # Tier priority (higher = more specific)
    TIER_PRIORITY = {
        "ecosystem": 0,
        "company": 1,
        "team": 2,
        "project": 3,
        "client": 4,
    }
    
    def __init__(self):
        super().__init__("scope_classifier")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def normalize(self, documents: List[Document]) -> List[Document]:
        """
        Classify documents into MCP tiers.
        
        Tiers (least to most specific):
        - ecosystem: Cross-company knowledge
        - company: Company-wide knowledge
        - team: Team-specific knowledge
        - project: Project-specific knowledge
        - client: Client-specific knowledge
        """
        classified_docs = []
        
        for doc in documents:
            try:
                tier = await self._classify_document(doc)
                doc.tier = tier
                doc.metadata["tier"] = tier
                doc.metadata["classified"] = True
                classified_docs.append(doc)
                
            except Exception as e:
                self.logger.error(f"Error classifying {doc.doc_id}: {e}")
                # Default to project tier on error
                doc.tier = "project"
                doc.metadata["tier"] = "project"
                classified_docs.append(doc)
        
        return classified_docs
    
    async def _classify_document(self, doc: Document) -> str:
        """Classify a single document into tier."""
        # Start with most specific and work down
        tier_scores = {
            "client": self._score_client(doc),
            "project": self._score_project(doc),
            "team": self._score_team(doc),
            "company": self._score_company(doc),
            "ecosystem": self._score_ecosystem(doc),
        }
        
        # Get highest scoring tier
        best_tier = max(tier_scores.items(), key=lambda x: x[1])
        
        # If no strong signals, default to project
        if best_tier[1] < 0.3:
            return "project"
        
        return best_tier[0]
    
    def _score_client(self, doc: Document) -> float:
        """Score for client-specific content."""
        score = 0.0
        
        # Check metadata
        if "client" in doc.metadata:
            score += 0.5
        
        # Check for client indicators
        client_keywords = [
            r'\bclient[- ]specific\b',
            r'\bcustom(?:er|ization)\b',
            r'\bdeployment\b',
            r'\bclient[- ]portal\b',
            r'\b(?:dedicated|private)\b',
        ]
        
        content_lower = (doc.title + " " + doc.content).lower()
        
        for pattern in client_keywords:
            if re.search(pattern, content_lower):
                score += 0.15
        
        # Check tags
        client_tags = ["client", "custom", "deployment", "private"]
        score += 0.1 * len([t for t in doc.tags if t.lower() in client_tags])
        
        return min(score, 1.0)
    
    def _score_project(self, doc: Document) -> float:
        """Score for project-specific content."""
        score = 0.0
        
        # Check metadata
        if "project" in doc.metadata or "project_key" in doc.metadata:
            score += 0.5
        
        # Source type indicators
        if doc.source == "jira":
            score += 0.3  # Jira issues are usually project-specific
        elif doc.source == "github" and doc.source_type in ["issue", "pull_request"]:
            score += 0.3
        
        # Check for project indicators
        project_keywords = [
            r'\bproject\b',
            r'\bfeature[- ]branch\b',
            r'\bsprint\b',
            r'\bepic\b',
            r'\bmilestone\b',
            r'\bbacklog\b',
        ]
        
        content_lower = (doc.title + " " + doc.content).lower()
        
        for pattern in project_keywords:
            if re.search(pattern, content_lower):
                score += 0.1
        
        # Check tags
        project_tags = ["project", "feature", "epic", "sprint"]
        score += 0.1 * len([t for t in doc.tags if t.lower() in project_tags])
        
        return min(score, 1.0)
    
    def _score_team(self, doc: Document) -> float:
        """Score for team-specific content."""
        score = 0.0
        
        # Check metadata
        if "team" in doc.metadata:
            score += 0.5
        
        # Check for team indicators
        team_keywords = [
            r'\bteam\b',
            r'\bsquad\b',
            r'\bpractices?\b',
            r'\bstandards?\b',
            r'\bguidelines?\b',
            r'\bconventions?\b',
            r'\bonboarding\b',
        ]
        
        content_lower = (doc.title + " " + doc.content).lower()
        
        for pattern in team_keywords:
            if re.search(pattern, content_lower):
                score += 0.12
        
        # Confluence pages are often team documentation
        if doc.source == "confluence":
            score += 0.2
        
        # Check tags
        team_tags = ["team", "standards", "guidelines", "practices"]
        score += 0.1 * len([t for t in doc.tags if t.lower() in team_tags])
        
        return min(score, 1.0)
    
    def _score_company(self, doc: Document) -> float:
        """Score for company-wide content."""
        score = 0.0
        
        # Check for company indicators
        company_keywords = [
            r'\bcompany[- ]wide\b',
            r'\borganization(?:al)?\b',
            r'\bpolicies\b',
            r'\bhr\b',
            r'\bbenefits\b',
            r'\ball[- ]hands\b',
            r'\bcompany[- ]values\b',
            r'\bmission\b',
        ]
        
        content_lower = (doc.title + " " + doc.content).lower()
        
        for pattern in company_keywords:
            if re.search(pattern, content_lower):
                score += 0.15
        
        # Check tags
        company_tags = ["company", "organization", "policy", "all-hands"]
        score += 0.15 * len([t for t in doc.tags if t.lower() in company_tags])
        
        return min(score, 1.0)
    
    def _score_ecosystem(self, doc: Document) -> float:
        """Score for ecosystem-wide content."""
        score = 0.0
        
        # Check for ecosystem indicators
        ecosystem_keywords = [
            r'\becosystem\b',
            r'\barchitecture\b',
            r'\binfrastructure\b',
            r'\bplatform\b',
            r'\bapi[- ]gateway\b',
            r'\bservice[- ]mesh\b',
            r'\bmicroservices?\b',
        ]
        
        content_lower = (doc.title + " " + doc.content).lower()
        
        for pattern in ecosystem_keywords:
            if re.search(pattern, content_lower):
                score += 0.15
        
        # README files are often ecosystem-level
        if doc.source_type == "readme":
            score += 0.3
        
        # Check tags
        ecosystem_tags = ["architecture", "infrastructure", "platform", "ecosystem"]
        score += 0.1 * len([t for t in doc.tags if t.lower() in ecosystem_tags])
        
        return min(score, 1.0)


# Celery task
@app.task(name="classify_scope", bind=True)
def classify_scope_task(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Celery task for scope classification."""
    import asyncio
    
    # Convert dicts back to Document objects
    from services.workers.shared.base_worker import Document
    from datetime import datetime
    
    doc_objects = []
    for d in documents:
        doc = Document(
            doc_id=d["doc_id"],
            source=d["source"],
            source_type=d["source_type"],
            title=d["title"],
            content=d["content"],
            raw_content=d.get("raw_content", ""),
            metadata=d.get("metadata", {}),
            tags=d.get("tags", []),
        )
        if d.get("tier"):
            doc.tier = d["tier"]
        doc_objects.append(doc)
    
    classifier = ScopeClassifier()
    
    # Run async classification
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(classifier.process({"documents": doc_objects}))
    
    return result.dict()

