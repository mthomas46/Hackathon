"""
Mock data generators for testing Workflow F.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random


class MockDataGenerator:
    """Generate realistic mock data for testing."""
    
    FIRST_NAMES = [
        "Sarah", "Marcus", "Priya", "Emily", "David", "Alex", 
        "Jordan", "Casey", "Riley", "Quinn", "Taylor", "Morgan"
    ]
    
    LAST_NAMES = [
        "Chen", "Johnson", "Patel", "Wu", "Kim", "Rivera", 
        "Lee", "Martin", "Davis", "Cooper", "Wilson", "Brown"
    ]
    
    TECH_STACKS = [
        ["Python", "FastAPI", "PostgreSQL"],
        ["JavaScript", "React", "Node.js"],
        ["TypeScript", "Angular", "MongoDB"],
        ["Go", "gRPC", "Redis"],
        ["Java", "Spring", "MySQL"],
        ["Rust", "Actix", "Cassandra"]
    ]
    
    TOPICS = [
        "Backend Development", "Frontend Development", "Database Design",
        "API Development", "Microservices", "Authentication", "Security",
        "Performance Optimization", "Testing", "DevOps", "CI/CD"
    ]
    
    SERVICES = [
        "user-service", "auth-service", "payment-service", "notification-service",
        "analytics-service", "search-service", "api-gateway", "data-pipeline"
    ]
    
    @classmethod
    def generate_username(cls, first_name: str, last_name: str) -> str:
        """Generate username from name."""
        return f"{first_name.lower()}.{last_name.lower()}"
    
    @classmethod
    def generate_github_pr(cls, pr_number: int, **overrides) -> Dict[str, Any]:
        """Generate a realistic GitHub PR."""
        author_first = random.choice(cls.FIRST_NAMES)
        author_last = random.choice(cls.LAST_NAMES)
        tech_stack = random.choice(cls.TECH_STACKS)
        
        # Generate some reviewers
        reviewers = []
        for _ in range(random.randint(0, 3)):
            reviewer_first = random.choice(cls.FIRST_NAMES)
            reviewer_last = random.choice(cls.LAST_NAMES)
            reviewers.append(f"@{cls.generate_username(reviewer_first, reviewer_last)}")
        
        description = f"Implements {random.choice(cls.TOPICS).lower()} feature using {', '.join(tech_stack[:2])}."
        if reviewers:
            description += f" {' '.join(reviewers)} please review."
        
        pr = {
            "pr_number": f"PR-{pr_number}",
            "title": f"Add {random.choice(cls.TOPICS)} to {random.choice(cls.SERVICES)}",
            "description": description,
            "author": cls.generate_username(author_first, author_last),
            "tech_stack": tech_stack,
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
        }
        
        pr.update(overrides)
        return pr
    
    @classmethod
    def generate_jira_ticket(cls, ticket_number: int, **overrides) -> Dict[str, Any]:
        """Generate a realistic Jira ticket."""
        assignee_first = random.choice(cls.FIRST_NAMES)
        assignee_last = random.choice(cls.LAST_NAMES)
        tech_stack = random.choice(cls.TECH_STACKS)
        
        # Generate some mentions
        mentions = []
        for _ in range(random.randint(0, 2)):
            mention_first = random.choice(cls.FIRST_NAMES)
            mention_last = random.choice(cls.LAST_NAMES)
            mentions.append(f"@{cls.generate_username(mention_first, mention_last)}")
        
        description = f"Need to implement {random.choice(cls.TOPICS).lower()}."
        if mentions:
            description += f" {' '.join(mentions)} can help with this."
        
        ticket = {
            "key": f"PROJ-{ticket_number}",
            "summary": f"{random.choice(['Implement', 'Fix', 'Update'])} {random.choice(cls.TOPICS)}",
            "description": description,
            "assignee": cls.generate_username(assignee_first, assignee_last),
            "tech_stack": tech_stack,
            "priority": random.choice(["High", "Medium", "Low"]),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat()
        }
        
        ticket.update(overrides)
        return ticket
    
    @classmethod
    def generate_confluence_doc(cls, doc_number: int, **overrides) -> Dict[str, Any]:
        """Generate a realistic Confluence document."""
        author_first = random.choice(cls.FIRST_NAMES)
        author_last = random.choice(cls.LAST_NAMES)
        tags = random.sample(cls.TOPICS, k=random.randint(2, 4))
        
        # Generate some contributors
        contributors = []
        for _ in range(random.randint(0, 3)):
            contrib_first = random.choice(cls.FIRST_NAMES)
            contrib_last = random.choice(cls.LAST_NAMES)
            contributors.append(f"@{cls.generate_username(contrib_first, contrib_last)}")
        
        content = f"This document covers {random.choice(cls.TOPICS).lower()}."
        if contributors:
            content += f" Contributors: {', '.join(contributors)}."
        
        doc = {
            "doc_id": f"CONF-{doc_number}",
            "title": f"{random.choice(cls.TOPICS)} Guide",
            "content": {"text": content},
            "author": cls.generate_username(author_first, author_last),
            "tags": tags,
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat()
        }
        
        doc.update(overrides)
        return doc
    
    @classmethod
    def generate_document_batch(cls, count: int) -> List[Dict[str, Any]]:
        """Generate a batch of mixed documents."""
        documents = []
        
        for i in range(count):
            doc_type = random.choice(["github_pr", "jira", "confluence"])
            
            if doc_type == "github_pr":
                documents.append({
                    "type": "github_pr",
                    "data": cls.generate_github_pr(i + 100)
                })
            elif doc_type == "jira":
                documents.append({
                    "type": "jira",
                    "data": cls.generate_jira_ticket(i + 100)
                })
            else:
                documents.append({
                    "type": "confluence",
                    "data": cls.generate_confluence_doc(i + 100)
                })
        
        return documents


# Export convenience functions
generate_github_pr = MockDataGenerator.generate_github_pr
generate_jira_ticket = MockDataGenerator.generate_jira_ticket
generate_confluence_doc = MockDataGenerator.generate_confluence_doc
generate_document_batch = MockDataGenerator.generate_document_batch

