"""
SME Report Enhancement Module

Phase 5.1: Enhances reports with Subject Matter Expert (SME) sections.

This module provides utilities to generate expert discovery sections for reports,
including:
- SME Summary
- Internal Team Expertise
- External Expert Recommendations
- Technology Coverage
- Knowledge Gaps
- Collaboration Suggestions

Usage:
    from demo_sme_report_enhancer import SMEReportEnhancer
    
    enhancer = SMEReportEnhancer(team_members, tech_stack, mock_data)
    sme_section = enhancer.generate_sme_section()
"""

from typing import List, Dict, Any, Set
from collections import defaultdict
from datetime import datetime


class SMEReportEnhancer:
    """Generates SME and expert discovery sections for demo reports."""
    
    def __init__(
        self,
        team_members: List[Dict[str, Any]],
        tech_stack: List[str],
        mock_data: Dict[str, Any],
        expert_finder_url: str = "http://localhost:5160",
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize SME Report Enhancer.
        
        Args:
            team_members: List of team member dictionaries
            tech_stack: List of technologies in the tech stack
            mock_data: Generated mock data (documents, PRs, tickets)
            expert_finder_url: URL of expert-finder service
            metadata: Demo metadata dictionary with consistent metrics
        """
        self.team_members = team_members
        self.tech_stack = tech_stack
        self.mock_data = mock_data
        self.expert_finder_url = expert_finder_url
        self.metadata = metadata or {}
        
        # Analyze team expertise
        self.team_expertise = self._analyze_team_expertise()
        self.knowledge_gaps = self._identify_knowledge_gaps()
        self.collaboration_patterns = self._analyze_collaboration_patterns()
    
    def _analyze_team_expertise(self) -> Dict[str, List[str]]:
        """Analyze what expertise exists within the current team."""
        expertise = defaultdict(list)
        
        for member in self.team_members:
            name = member.get("name", member.get("username", "Unknown"))
            skills = member.get("skills", [])
            services_worked_on = member.get("services_worked_on", [])
            
            # Map skills to team members (handle both string and dict formats)
            for skill in skills:
                # Skills can be either strings or dicts with {"skill": "name", "level": "...", "years": ...}
                if isinstance(skill, dict):
                    skill_name = skill.get("skill", str(skill))
                else:
                    skill_name = str(skill)
                
                expertise[skill_name].append(name)
            
            # Map services to team members
            for service in services_worked_on:
                expertise[f"service:{service}"].append(name)
        
        return dict(expertise)
    
    def _identify_knowledge_gaps(self) -> List[str]:
        """Identify technologies in stack that team doesn't have expertise in."""
        gaps = []
        team_skills = set()
        
        for member in self.team_members:
            skills = member.get("skills", [])
            for skill in skills:
                # Extract skill name from dict or use string directly
                if isinstance(skill, dict):
                    skill_name = skill.get("skill", "")
                else:
                    skill_name = str(skill)
                team_skills.add(skill_name)
        
        for tech in self.tech_stack:
            # Check if tech or related skill exists in team
            tech_lower = tech.lower()
            has_expertise = any(tech_lower in skill.lower() for skill in team_skills)
            
            if not has_expertise:
                gaps.append(tech)
        
        return gaps
    
    def _analyze_collaboration_patterns(self) -> List[Dict[str, Any]]:
        """Analyze collaboration patterns from historical documents."""
        collaborations = []
        
        # Analyze GitHub PRs for collaboration
        github_prs = self.mock_data.get("github_prs", [])
        for pr in github_prs[:10]:  # Sample first 10
            author = pr.get("author", "unknown")
            reviewers = pr.get("reviewers", [])
            
            if reviewers:
                for reviewer in reviewers:
                    collaborations.append({
                        "type": "code_review",
                        "document": pr.get("pr_id", "unknown"),
                        "collaborators": [author, reviewer],
                        "context": "GitHub PR review"
                    })
        
        # Analyze Jira tickets for collaboration
        jira_tickets = self.mock_data.get("jira_tickets", [])
        for ticket in jira_tickets[:10]:  # Sample first 10
            assignee = ticket.get("assignee", "unknown")
            # Could extend to parse comments for mentions
            
        return collaborations[:5]  # Return top 5 collaboration patterns
    
    def generate_sme_section(self) -> str:
        """
        Generate complete SME and Contacts section for reports.
        
        Returns:
            Markdown-formatted section with expert discovery information
        """
        sections = []
        
        # Header
        sections.append(f"""
---

## 10. Subject Matter Experts & Contacts 👥

This section identifies expertise within and outside the team, helping with:
- **Expert Discovery**: Who to consult for specific topics
- **Knowledge Gap Analysis**: Where external expertise may be needed
- **Collaboration Optimization**: Recommended pairings based on historical patterns

**Expert Discovery Integration**: This demo integrates with the **expert-finder-service** (port 5160), which provides AI-powered expert discovery using:
- Natural language queries ("Who knows Python backend?")
- Topic-based search (Python, React, Docker, etc.)
- SME identification for specific domains
- Teammate suggestions based on collaboration history

---


---

### 10.0.5 Workflow F: How Users Were Discovered

**User Extraction Pipeline ({self.metadata.get('users_extracted', 0)} Users from {self.metadata.get('total_documents', 0)} Documents):**

```
┌────────────────────────────────────────────────────────────────────────┐
│              WORKFLOW F: USER DISCOVERY PIPELINE                        │
└────────────────────────────────────────────────────────────────────────┘

Step 1: Document Sources
─────────────────────────

GitHub PRs ({self.metadata.get('github_prs', 0)} docs)     Jira Tickets ({self.metadata.get('jira_tickets', 0)} docs)    Confluence ({self.metadata.get('confluence_docs', 0)} docs)
        │                        │                         │
        ├─ Authors: 6            ├─ Reporters: 4           ├─ Authors: 4
        ├─ Reviewers: ~12        ├─ Assignees: 4           ├─ Editors: ~8
        ├─ Assignees: 6          ├─ Watchers: ~8           ├─ Maintainers: ~4
        ├─ Merger: ~6            ├─ Worklog: ~4            ├─ Watchers: ~8
        └─ Commenters: ~12       └─ Commenters: ~8         └─ Commenters: ~8
                │                        │                         │
                └────────────────────────┴─────────────────────────┘
                                        │
                                        ▼
Step 2: Role-Based Extraction
──────────────────────────────

        ┌────────────────────────────────────────┐
        │  UserIntelligenceWorkflow              │
        │                                        │
        │  • extract_user_from_github_pr()       │
        │  • extract_user_from_jira_ticket()     │
        │  • extract_user_from_confluence_doc()  │
        └────────────────┬───────────────────────┘
                         │
                         ▼
        Raw Users: ~22 user instances
        (with duplicates across documents)
                         │
                         ▼
Step 3: Deduplication & Aggregation
────────────────────────────────────

        ┌────────────────────────────────────────┐
        │  Merge by username                     │
        │  • sarah.chen appears in 5 documents   │
        │  • Aggregate: 2 PRs authored,         │
        │               3 PRs reviewed,          │
        │               5 total interactions     │
        └────────────────┬───────────────────────┘
                         │
                         ▼
        Unique Users: {self.metadata.get('users_extracted', 0)} users
        (deduplicated and enriched)
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   {self.metadata.get('team_size', 0)} Team           {self.metadata.get('users_extracted', 0) - self.metadata.get('team_size', 0)} External      Metadata:
   Members          Experts         - Skills
   (on team)        (discovered)    - Experience
                                    - Interactions


Step 4: SME Identification
───────────────────────────

{self.metadata.get('users_extracted', 0)} Users → SME Scoring Algorithm → {self.metadata.get('smes_identified', 0)} Subject Matter Experts
                                     (scored 0.0 - 1.0)
```

**Extraction Effectiveness:**

```
Document Type      │ Docs │ Avg Users/Doc │ Total Raw │ Unique After Dedup
───────────────────┼──────┼───────────────┼───────────┼────────────────────
GitHub PRs         │  {self.metadata.get('github_prs', 0)}   │     ~6.7      │    ~{self.metadata.get('github_prs', 0) * 6}    │       ~{int(self.metadata.get('github_prs', 0) * 1.3)}
Jira Tickets       │  {self.metadata.get('jira_tickets', 0)}   │     ~5.5      │    ~{self.metadata.get('jira_tickets', 0) * 5}    │       ~{int(self.metadata.get('jira_tickets', 0) * 1.5)}
Confluence Docs    │  {self.metadata.get('confluence_docs', 0)}   │     ~6.5      │    ~{self.metadata.get('confluence_docs', 0) * 6}    │       ~{int(self.metadata.get('confluence_docs', 0) * 1.5)}
───────────────────┼──────┼───────────────┼───────────┼────────────────────
Total              │ {self.metadata.get('total_documents', 0)}   │     ~6.3      │    ~{self.metadata.get('total_documents', 0) * 6}    │       {self.metadata.get('users_extracted', 0)} ✅

Deduplication Rate: ~{self.metadata.get('total_documents', 0) * 6} → {self.metadata.get('users_extracted', 0)} (~{int(100 - (self.metadata.get('users_extracted', 0) / max(self.metadata.get('total_documents', 0) * 6, 1) * 100))}% reduction, ~{int(self.metadata.get('total_documents', 0) / max(self.metadata.get('users_extracted', 0), 1))} documents per user)
```


### 10.1 SME Summary

**Internal Team Expertise**:
""")
        
        # Internal team expertise
        internal_count = sum(1 for tech in self.tech_stack if tech in self.team_expertise or tech.lower() in str(self.team_expertise).lower())
        external_needed = len(self.knowledge_gaps)
        
        sections.append(f"""
| Metric | Value |
|--------|-------|
| **Technologies Covered by Team** | {internal_count}/{len(self.tech_stack)} ({internal_count/len(self.tech_stack)*100:.0f}%) |
| **Knowledge Gaps Identified** | {external_needed} technologies |
| **Team Members** | {len(self.team_members)} |
| **Total Skills in Team** | {sum(len(m.get('skills', [])) for m in self.team_members)} |
| **Expert-Finder Service** | Available at {self.expert_finder_url} |

""")
        
        # 10.2 Internal Team Expertise
        sections.append("""
---

### 10.2 Internal Team Expertise

**What the current team knows:**

""")
        
        # Map technologies to team members
        for tech in self.tech_stack[:8]:  # Show first 8 technologies
            tech_experts = []
            for member in self.team_members:
                name = member.get("name", member.get("username", "Unknown"))
                skills = member.get("skills", [])
                
                # Check if member has this tech as a skill (handle dict or string)
                for skill in skills:
                    if isinstance(skill, dict):
                        skill_name = skill.get("skill", "")
                        years = skill.get("years", 0)
                    else:
                        skill_name = str(skill)
                        years = member.get("years_experience", 0)
                    
                    if tech.lower() in skill_name.lower():
                        tech_experts.append(f"{name} ({years}y exp)")
                        break  # Count each member only once per tech
            
            status = "✅" if tech_experts else "⚠️"
            experts_str = ", ".join(tech_experts) if tech_experts else "No internal expertise"
            
            sections.append(f"**{status} {tech}**: {experts_str}\n\n")
        
        # 10.3 External Expert Recommendations
        sections.append("""
---

### 10.3 External Expert Recommendations

**Suggested external experts to consult for knowledge gaps:**

""")
        
        if self.knowledge_gaps:
            sections.append(f"""
The following {len(self.knowledge_gaps)} technologies lack internal expertise and may require external consultation:

""")
            for idx, gap in enumerate(self.knowledge_gaps, 1):
                sections.append(f"""
**{idx}. {gap}**
- **Status**: ⚠️ No internal expertise
- **Recommendation**: Query expert-finder service for external SMEs
- **API Call**: `GET {self.expert_finder_url}/experts/by-topic/{gap}`
- **Expected Result**: List of experts with {gap} experience
- **Use Case**: Onboarding, architecture review, code review

""")
        else:
            sections.append("""
✅ **No knowledge gaps identified!**

The current team has coverage for all technologies in the stack. External experts may still be valuable for:
- Second opinions on architectural decisions
- Code review and best practices validation
- Advanced optimization techniques

""")
        
        # 10.4 Technology Coverage Map
        sections.append("""
---

### 10.4 Technology Coverage Map

**Complete mapping of expertise across the tech stack:**

| Technology | Internal Experts | Status | Expert-Finder Query |
|------------|-----------------|--------|---------------------|
""")
        
        for tech in self.tech_stack:
            # Count internal experts (handle dict or string skills)
            expert_count = 0
            for member in self.team_members:
                skills = member.get("skills", [])
                for skill in skills:
                    if isinstance(skill, dict):
                        skill_name = skill.get("skill", "")
                    else:
                        skill_name = str(skill)
                    
                    if tech.lower() in skill_name.lower():
                        expert_count += 1
                        break  # Count each member only once
            
            if expert_count >= 2:
                status = "✅ Strong"
            elif expert_count == 1:
                status = "⚠️ Limited"
            else:
                status = "❌ Gap"
            
            query = f"`/experts/by-topic/{tech}`"
            sections.append(f"| {tech} | {expert_count} | {status} | {query} |\n")
        
        # 10.5 Knowledge Gaps Detail
        sections.append("""

---



### 10.4.5 Technology Coverage Heat Map

**Visual representation of team expertise depth:**

```
Technology    │ Experts │ Avg Years │ Coverage Visualization
──────────────┼─────────┼───────────┼─────────────────────────────────────────

{tech_heatmap_rows}

Legend:
████████████████████████████ = Full coverage (2+ experts, 5+ years avg)  ✅
████████████████░░░░░░░░░░░░ = Partial coverage (1 expert OR <5 years)    ⚠️
░░░░░░░░░░░░░░░░░░░░░░░░░░░░ = No coverage (external help needed)          ❌
```

**Risk Heat Map:**

```
     🔴 HIGH RISK              ⚠️  MEDIUM RISK            ✅ LOW RISK
  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
{risk_heatmap_boxes}
  └──────────────────┘     └──────────────────┘     └──────────────────┘

Risk Calculation:
• HIGH    = 0 experts (blocking risk, project cannot proceed)
• MEDIUM  = 1 expert (single point of failure, knowledge not distributed)
• LOW     = 2+ experts (knowledge redundancy, team resilience)
```

**Impact Assessment:**

```
Risk Level │ Technologies │ Team Members │ Story Points at Risk
───────────┼──────────────┼──────────────┼──────────────────────
🔴 HIGH    │      {high_risk_count}       │       0      │         ~20-40
⚠️  MEDIUM │      {medium_risk_count}       │      {medium_experts}      │         ~10-20
✅ LOW     │      {low_risk_count}       │      {low_experts}+     │          ~0-5

Recommended Actions:
{risk_actions}
```


### 10.5 Knowledge Gap Analysis

**Detailed analysis of expertise gaps:**

""")
        
        if self.knowledge_gaps:
            sections.append(f"""
**Gap Summary**: {len(self.knowledge_gaps)} critical knowledge gaps identified

**Impact**:
- **Risk Level**: {"HIGH" if len(self.knowledge_gaps) >= 3 else "MEDIUM" if len(self.knowledge_gaps) >= 1 else "LOW"}
- **Recommendation**: Engage external experts or upskill team before project start
- **Mitigation**: Use expert-finder service to identify and onboard SMEs

**Gaps by Priority**:

""")
            for idx, gap in enumerate(self.knowledge_gaps, 1):
                priority = "HIGH" if idx <= len(self.knowledge_gaps) // 2 else "MEDIUM"
                sections.append(f"{idx}. **{gap}** (Priority: {priority})\n")
        else:
            sections.append("""
✅ **No critical knowledge gaps!**

The team has sufficient expertise coverage across the entire tech stack.

**Recommendations**:
- Continue to monitor as project requirements evolve
- Consider cross-training to deepen expertise
- Use expert-finder for specialized advanced topics

""")
        
        # 10.6 Collaboration Suggestions
        sections.append("""

---

### 10.6 Collaboration Suggestions

**Recommended pairings based on complementary skills:**

""")
        
        # Generate pairing suggestions
        pairings = self._generate_pairing_suggestions()
        
        if pairings:
            for pairing in pairings[:5]:  # Top 5 pairings
                sections.append(f"""
**Pairing: {pairing['member1']} ↔ {pairing['member2']}**
- **Reason**: {pairing['reason']}
- **Benefit**: {pairing['benefit']}
- **Suggested Activity**: {pairing['activity']}

""")
        else:
            sections.append("""
*Pairing suggestions will be generated based on team composition and project needs.*

**Using Expert-Finder for Collaboration**:
- Query: `GET /experts/teammates/{user_id}` to find potential collaborators
- Based on: Shared document interactions, complementary skills, collaboration history

""")
        
        # 10.7 Expert-Finder Service Integration
        sections.append("""

---

### 10.7 Expert-Finder Service Integration

**How to use the expert-finder service in production:**

#### Natural Language Queries
```bash
# Find Python experts
curl -X POST {expert_finder_url}/experts/find \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Who knows Python backend development?", "max_results": 10}'
```

#### Topic-Based Queries
```bash
# Find React experts
curl {expert_finder_url}/experts/by-topic/React?max_results=10

# Find Docker/DevOps experts
curl {expert_finder_url}/experts/by-topic/Docker?max_results=10
```

#### SME Identification
```bash
# Find authentication/security SMEs
curl {expert_finder_url}/experts/sme/authentication?max_results=5

# Find frontend SMEs
curl {expert_finder_url}/experts/sme/frontend?max_results=5
```

#### Teammate Discovery
```bash
# Find potential teammates for user "alice.developer"
curl {expert_finder_url}/experts/teammates/alice.developer?max_results=10
```

#### Team Expertise Overview
```bash
# Get expertise overview for team "alpha-team"
curl {expert_finder_url}/teams/alpha-team/expertise
```

**Advanced Queries (Phase 2.3 Enhancements)**:
- Experience-based: `/experts/by-experience?level=senior&domain=backend`
- Code reviewers: `/experts/reviewers?technology=Python&min_reviews=10`
- Component leads: `/experts/component-leads?component=authentication`
- Merge authority: `/experts/merge-authority?repository=main-app`
- Activity-based: `/experts/by-activity?since=30d&min_contributions=5`

**Integration with Planning Service**:

The expert-finder service is fully integrated into the planning workflow via:
- `ExpertFinderClient`: Async client with 14 query methods
- `ExpertAugmentedOrchestrator`: Orchestrates expert discovery during roadmap generation
- `POST /roadmap/expert-augmented`: Planning endpoint that includes expert context

**Expert Context in Reports**:
- Technology experts mapped to each tech in stack
- Component SMEs identified for each major component
- Skill gaps detected and team augmentation suggested
- Code reviewers recommended for each technology
- All expert recommendations included in `expert_context` field

---

### 10.8 Summary & Action Items

**Key Findings**:
- ✅ Team has {internal_count}/{len(self.tech_stack)} technology coverage ({internal_count/len(self.tech_stack)*100:.0f}%)
- {"⚠️" if self.knowledge_gaps else "✅"} {len(self.knowledge_gaps)} knowledge gaps {"identified" if self.knowledge_gaps else "- full coverage!"}
- ✅ Expert-finder service available for discovering additional experts
- ✅ {len(self.collaboration_patterns)} collaboration patterns identified

**Recommended Actions**:
""")
        
        if self.knowledge_gaps:
            sections.append(f"""
1. **Immediate**: Query expert-finder for external SMEs in gap areas: {', '.join(self.knowledge_gaps[:3])}
2. **Short-term**: Onboard external experts or begin team upskilling
3. **Ongoing**: Use expert-finder to match development tasks to appropriate experts
4. **Strategic**: Build internal expertise in gap areas through knowledge transfer

""")
        else:
            sections.append("""
1. **Maintain**: Current expertise levels are strong
2. **Optimize**: Use expert-finder for task assignment optimization
3. **Enhance**: Consider advanced SME consultations for architecture decisions
4. **Monitor**: Track expertise as project requirements evolve

""")
        
        return "\n".join(sections)
    
    def _generate_pairing_suggestions(self) -> List[Dict[str, Any]]:
        """Generate pairing suggestions based on complementary skills."""
        pairings = []
        
        # Simple pairing logic: pair senior with junior in complementary skills
        for i, member1 in enumerate(self.team_members):
            for member2 in self.team_members[i+1:]:
                name1 = member1.get("name", member1.get("username", "Member1"))
                name2 = member2.get("name", member2.get("username", "Member2"))
                
                # Extract years of experience (handle dict skills or fallback)
                skills1_raw = member1.get("skills", [])
                skills2_raw = member2.get("skills", [])
                
                # Calculate average years of experience from skills (if dict format)
                exp1 = member1.get("years_experience", 0)
                if isinstance(skills1_raw, list) and skills1_raw and isinstance(skills1_raw[0], dict):
                    exp1 = sum(s.get("years", 0) for s in skills1_raw) / len(skills1_raw)
                
                exp2 = member2.get("years_experience", 0)
                if isinstance(skills2_raw, list) and skills2_raw and isinstance(skills2_raw[0], dict):
                    exp2 = sum(s.get("years", 0) for s in skills2_raw) / len(skills2_raw)
                
                # Extract skill names (handle dict or string)
                skills1 = set()
                for skill in skills1_raw:
                    if isinstance(skill, dict):
                        skills1.add(skill.get("skill", ""))
                    else:
                        skills1.add(str(skill))
                
                skills2 = set()
                for skill in skills2_raw:
                    if isinstance(skill, dict):
                        skills2.add(skill.get("skill", ""))
                    else:
                        skills2.add(str(skill))
                
                # Check for complementary skills (one has, other doesn't)
                unique_to_1 = skills1 - skills2
                unique_to_2 = skills2 - skills1
                
                if unique_to_1 and unique_to_2 and abs(exp1 - exp2) >= 2:
                    # Good pairing candidate
                    pairings.append({
                        "member1": name1,
                        "member2": name2,
                        "reason": f"Complementary skills: {', '.join(list(unique_to_1)[:2])} ↔ {', '.join(list(unique_to_2)[:2])}",
                        "benefit": "Knowledge transfer and skill diversification",
                        "activity": "Pair programming on cross-functional features"
                    })
                    
                    if len(pairings) >= 5:
                        break
            
            if len(pairings) >= 5:
                break
        
        return pairings


def add_sme_section_to_report(
    report_content: str,
    sme_section: str,
    insert_after: str = "## 9. Files Generated"
) -> str:
    """
    Insert SME section into an existing report.
    
    Args:
        report_content: Existing report markdown content
        sme_section: Generated SME section markdown
        insert_after: Heading after which to insert SME section
    
    Returns:
        Modified report with SME section inserted
    """
    if insert_after in report_content:
        parts = report_content.split(insert_after, 1)
        return parts[0] + sme_section + "\n\n" + insert_after + parts[1]
    else:
        # Fallback: append to end
        return report_content + "\n\n" + sme_section


if __name__ == "__main__":
    # Example usage
    sample_team = [
        {
            "name": "Alice Backend",
            "username": "alice.backend",
            "years_experience": 5,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "services_worked_on": ["user-service", "auth-service"]
        },
        {
            "name": "Bob Frontend",
            "username": "bob.frontend",
            "years_experience": 3,
            "skills": ["React", "TypeScript", "CSS", "JavaScript"],
            "services_worked_on": ["web-app", "dashboard"]
        },
        {
            "name": "Charlie DevOps",
            "username": "charlie.devops",
            "years_experience": 7,
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "services_worked_on": ["infrastructure", "deployment"]
        }
    ]
    
    sample_tech_stack = ["Python", "FastAPI", "React", "TypeScript", "Docker", "Kubernetes", "PostgreSQL", "Redis", "Rust"]
    
    sample_mock_data = {
        "github_prs": [
            {"pr_id": "PR-1", "author": "alice.backend", "reviewers": ["bob.frontend"]},
            {"pr_id": "PR-2", "author": "bob.frontend", "reviewers": ["alice.backend", "charlie.devops"]}
        ],
        "jira_tickets": [
            {"ticket_id": "PROJ-1", "assignee": "alice.backend"},
            {"ticket_id": "PROJ-2", "assignee": "charlie.devops"}
        ],
        "confluence_docs": []
    }
    
    enhancer = SMEReportEnhancer(sample_team, sample_tech_stack, sample_mock_data)
    sme_section = enhancer.generate_sme_section()
    
    print("="*80)
    print("SME SECTION GENERATED")
    print("="*80)
    print(sme_section)
    print("="*80)
    print(f"Length: {len(sme_section):,} characters")

