"""
Mock Data Generator for Project Simulations.
Following TDD principles with clean, testable code.
"""

from typing import List, Dict, Any
from datetime import datetime
import random


class MockDataGenerator:
    """Generator for mock data used in project simulations."""

    def __init__(self):
        """Initialize the mock data generator."""
        self.common_keywords = [
            "api", "database", "frontend", "backend", "authentication", "security",
            "microservices", "deployment", "testing", "documentation", "analytics"
        ]

        self.tech_mapping = {
            "api": ["REST", "GraphQL", "Swagger", "OpenAPI", "FastAPI"],
            "database": ["PostgreSQL", "Redis", "MongoDB", "MySQL", "SQLite"],
            "frontend": ["React", "Vue.js", "Angular", "Next.js", "JavaScript", "TypeScript"],
            "backend": ["Node.js", "Express", "Django", "Flask", "Spring Boot", "FastAPI"],
            "react": ["React", "Redux", "React Router", "Next.js"],
            "node": ["Node.js", "Express", "npm", "yarn"],
            "postgres": ["PostgreSQL", "PostGIS", "pgAdmin", "Database"],
            "authentication": ["JWT", "OAuth2", "Auth0", "Firebase Auth"],
            "deployment": ["Docker", "Kubernetes", "AWS", "Heroku", "CI/CD"],
            "testing": ["pytest", "Jest", "Selenium", "Cypress", "unittest"]
        }

    def extract_keywords_from_query(self, query: str) -> List[str]:
        """Extract relevant keywords from natural language queries."""
        if not query or not query.strip():
            return ["general", "application"]

        query_lower = query.lower()
        keywords = []

        # Add predefined keywords that appear in query
        for keyword in self.common_keywords:
            if keyword in query_lower:
                keywords.append(keyword)

        # Extract technology names from query (e.g., "React", "Node.js", "PostgreSQL")
        tech_indicators = ["react", "vue", "angular", "node", "python", "java", "postgres", "mysql", "mongodb"]
        for tech in tech_indicators:
            if tech in query_lower:
                keywords.append(tech)

        # Add query-specific keywords
        words = query.split()
        for word in words:
            word_clean = word.lower().strip(".,!?")
            if len(word_clean) > 3 and word_clean not in keywords:
                keywords.append(word_clean)

        # Ensure we have at least some keywords
        if not keywords:
            keywords = ["application", "development"]

        return keywords[:10]  # Limit to 10 keywords

    def generate_mock_team_members(self, keywords: List[str], team_size: int) -> List[Dict[str, Any]]:
        """Generate mock team members based on keywords."""
        roles = ["developer", "qa_engineer", "product_owner", "designer", "architect"]
        team_members = []

        # Ensure we don't exceed available roles
        actual_team_size = min(team_size, len(roles))

        for i in range(actual_team_size):
            role = roles[i]
            # Use keywords as skills, limited to 3 per member
            skills = keywords[:3] if len(keywords) >= 3 else keywords + ["general"] * (3 - len(keywords))

            team_members.append({
                "id": f"member_{i+1}",
                "name": f"Mock {role.title().replace('_', ' ')} {i+1}",
                "role": role,
                "skills": skills,
                "experience_years": 3 + i,  # 3, 4, 5, 6, 7 years
                "productivity_factor": round(0.8 + (i * 0.1), 1)  # 0.8, 0.9, 1.0, 1.1, 1.2
            })

        return team_members

    def generate_mock_documents(self, keywords: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock documents based on keywords and context."""
        doc_types = ["api_documentation", "architecture_diagram", "requirements_spec", "user_manual"]
        documents = []

        for i, doc_type in enumerate(doc_types):
            documents.append({
                "id": f"doc_{i+1}",
                "type": doc_type,
                "title": f"Mock {doc_type.title().replace('_', ' ')}",
                "content": f"Mock content for {doc_type} related to {', '.join(keywords[:3])}",
                "keywords": keywords[:5],
                "created_at": datetime.now().isoformat()
            })

        return documents

    def infer_technologies_from_query(self, query: str, keywords: List[str]) -> List[str]:
        """Infer technology stack from query and keywords."""
        base_technologies = ["Python", "FastAPI"]
        inferred_tech = []

        # Add technologies based on keywords
        for keyword in keywords:
            if keyword in self.tech_mapping:
                inferred_tech.extend(self.tech_mapping[keyword])

        # Remove duplicates and limit to 5 additional technologies
        all_tech = base_technologies + list(set(inferred_tech))
        return all_tech[:7]  # Base + 5 inferred

    def generate_mock_timeline(self, duration_weeks: int, keywords: List[str]) -> List[Dict[str, Any]]:
        """Generate mock project timeline."""
        phases = ["Planning", "Development", "Testing", "Deployment", "Maintenance"]
        timeline = []

        for i, phase in enumerate(phases):
            start_week = i * 2
            phase_duration = min(2, duration_weeks - start_week)

            if phase_duration > 0:
                timeline.append({
                    "phase": phase,
                    "start_week": start_week,
                    "duration_weeks": phase_duration,
                    "milestones": [f"Complete {phase.lower()} phase"],
                    "deliverables": [f"{phase} documentation and artifacts"]
                })

        return timeline

    def generate_comprehensive_mock_data(self, query: str, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive mock data for simulation."""
        try:
            # Extract keywords from query
            keywords = self.extract_keywords_from_query(query)

            # Generate team members
            team_size = config.get("team_size", 5)
            team_members = self.generate_mock_team_members(keywords, team_size)

            # Generate documents
            documents = self.generate_mock_documents(keywords, context)

            # Infer technologies
            technologies = self.infer_technologies_from_query(query, keywords)

            # Generate timeline
            duration_weeks = config.get("duration_weeks", 8)
            timeline = self.generate_mock_timeline(duration_weeks, keywords)

            return {
                "team_members": team_members,
                "documents": documents,
                "technologies": technologies,
                "timeline": timeline,
                "keywords_extracted": keywords,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            # Return minimal fallback data
            return {
                "team_members": [],
                "documents": [],
                "technologies": ["Python", "FastAPI"],
                "timeline": [],
                "keywords_extracted": ["error"],
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
