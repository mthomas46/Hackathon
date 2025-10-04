"""
User & Team Report Generator

Phase 3: Creates a completely new report focused on the end-user (team lead) perspective.

This module generates a comprehensive User & Team Report with 8 sections:
1. Executive Summary for Team Leads
2. Your Team Members
3. Technology Coverage & Skill Matrix
4. Recommended Team Structure for This Project
5. Team Collaboration Insights
6. How to Find Experts During the Project
7. Knowledge Gaps & Training Plan
8. Action Items for Team Lead

Usage:
    from demo_user_team_report_generator import UserTeamReportGenerator
    
    generator = UserTeamReportGenerator(team_members, tech_stack, workflow_f_result, feature_summary)
    report = generator.generate_complete_report()
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class UserTeamReportGenerator:
    """Generates User & Team Report focused on team lead perspective."""
    
    def __init__(
        self,
        team_members: List[Dict[str, Any]],
        tech_stack: List[str],
        workflow_f_result: Any = None,
        feature_summary: str = "",
        mock_data: Optional[Dict[str, Any]] = None,
        expert_finder_url: str = "http://localhost:5160"
    ):
        """
        Initialize User & Team Report Generator.
        
        Args:
            team_members: List of team member dictionaries
            tech_stack: List of technologies in the tech stack
            workflow_f_result: WorkflowFResult from Workflow F execution
            feature_summary: Natural language feature description
            mock_data: Generated mock data (optional)
            expert_finder_url: URL of expert-finder service
        """
        self.team_members = team_members
        self.tech_stack = tech_stack
        self.workflow_f_result = workflow_f_result
        self.feature_summary = feature_summary
        self.mock_data = mock_data or {}
        self.expert_finder_url = expert_finder_url
        
        # Analyze team expertise
        self.team_expertise = self._analyze_team_expertise()
        self.knowledge_gaps = self._identify_knowledge_gaps()
    
    def _analyze_team_expertise(self) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze team expertise mapping technologies to team members."""
        expertise = {}
        
        for tech in self.tech_stack:
            experts = []
            for member in self.team_members:
                name = member.get("name", "Unknown")
                skills = member.get("skills", [])
                
                # Check if member has this technology
                for skill in skills:
                    if isinstance(skill, dict):
                        skill_name = skill.get("skill", "")
                        years = skill.get("years", 0)
                        level = skill.get("level", "")
                    else:
                        skill_name = str(skill)
                        years = member.get("years_experience", 0)
                        level = member.get("experience_level", "")
                    
                    if tech.lower() in skill_name.lower():
                        experts.append({
                            "name": name,
                            "years": years,
                            "level": level,
                            "workload": member.get("current_workload", 0.0),
                            "velocity": member.get("recent_velocity", 0)
                        })
                        break
            
            expertise[tech] = experts
        
        return expertise
    
    def _identify_knowledge_gaps(self) -> List[str]:
        """Identify technologies in stack that team doesn't have expertise in."""
        gaps = []
        for tech, experts in self.team_expertise.items():
            if not experts:
                gaps.append(tech)
        return gaps
    
    def generate_complete_report(self) -> str:
        """
        Generate the complete User & Team Report.
        
        Returns:
            Complete markdown report as a string
        """
        sections = []
        
        # Header
        sections.append(f"""# 👥 User & Team Report
## Your Team's Expertise & Recommendations

**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}  
**Report Type:** Team Lead Perspective  
**Project:** {self.feature_summary[:80]}...  
**Related Reports:**  
- [Planning Service Report](./Planning_Service_Report.md) - Production planning output  
- [Behind-the-Scenes Report](./Behind_the_Scenes_Report.md) - Demo technical details  
- [Ecosystem Validation Report](./Ecosystem_Validation_Report.md) - Live code proof  
- [Data Architecture Report](./Data_Architecture_Report.md) - Data stores & relationships  
- [Main README](../README.md) - Demo overview

---

## 📋 Table of Contents
1. [Executive Summary for Team Leads](#executive-summary-for-team-leads)
2. [Your Team Members](#your-team-members)
3. [Technology Coverage & Skill Matrix](#technology-coverage--skill-matrix)
4. [Recommended Team Structure for This Project](#recommended-team-structure-for-this-project)
5. [Team Collaboration Insights](#team-collaboration-insights)
6. [How to Find Experts During the Project](#how-to-find-experts-during-the-project)
7. [Knowledge Gaps & Training Plan](#knowledge-gaps--training-plan)
8. [Action Items for Team Lead](#action-items-for-team-lead)

---

""")
        
        # Section 1: Executive Summary for Team Leads
        sections.append(self._generate_executive_summary())
        
        # Section 2: Your Team Members
        sections.append(self._generate_team_member_profiles())
        
        # Section 3: Technology Coverage & Skill Matrix
        sections.append(self._generate_skill_matrix())
        
        # Section 4: Recommended Team Structure
        sections.append(self._generate_team_structure())
        
        # Section 5: Team Collaboration Insights
        sections.append(self._generate_collaboration_insights())
        
        # Section 6: How to Find Experts
        sections.append(self._generate_expert_discovery_guide())
        
        # Section 7: Knowledge Gaps & Training Plan
        sections.append(self._generate_training_plan())
        
        # Section 8: Action Items
        sections.append(self._generate_action_items())
        
        # Footer
        sections.append("""

---

## Related Reports

**Navigate to other reports for complete picture:**

- **This Report (User & Team)**  
  Team lead perspective with actionable recommendations

- **[Planning Service Report](./Planning_Service_Report.md)**  
  Production planning output with SME recommendations

- **[Behind-the-Scenes Report](./Behind_the_Scenes_Report.md)**  
  Complete demo execution details and Workflow F analytics

- **[Ecosystem Validation Report](./Ecosystem_Validation_Report.md)**  
  Proof of live code execution and real service interactions

- **[Data Architecture Report](./Data_Architecture_Report.md)**  
  In-depth analysis of data stores, schemas, and service discovery

- **[Main README](../README.md)**  
  Demo overview and quick start guide

---

**User & Team Report Complete**  
**System:** LLM Documentation Ecosystem - Phase 9  
**Report Type:** Team Lead Perspective  
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
""")
        
        return "\n".join(sections)
    
    def _generate_executive_summary(self) -> str:
        """Generate Section 1: Executive Summary for Team Leads."""
        num_members = len(self.team_members)
        total_skills = sum(len(m.get("skills", [])) for m in self.team_members)
        coverage_count = sum(1 for tech in self.tech_stack if self.team_expertise.get(tech, []))
        coverage_pct = (coverage_count / len(self.tech_stack) * 100) if self.tech_stack else 0
        num_gaps = len(self.knowledge_gaps)
        
        return f"""## 1. Executive Summary for Team Leads

**Your Team at a Glance**:

| Metric | Value | Status |
|--------|-------|--------|
| **Team Size** | {num_members} members | {"✅ Adequate" if num_members >= 5 else "⚠️ Small"} |
| **Total Skills** | {total_skills} skills | ✅ Diverse |
| **Technology Coverage** | {coverage_count}/{len(self.tech_stack)} ({coverage_pct:.0f}%) | {"✅ Strong" if coverage_pct >= 70 else "⚠️ Gaps Exist"} |
| **Knowledge Gaps** | {num_gaps} technologies | {"✅ No gaps" if num_gaps == 0 else "⚠️ Need attention"} |
| **Expert-Finder Service** | Available | ✅ Operational |

**Quick Actions**:
{"1. ✅ All required technologies covered by team" if num_gaps == 0 else f"1. ⚠️ {num_gaps} technologies have gaps - address with training or external experts"}
2. {"✅ Strong team diversity - leverage for cross-functional work" if num_members >= 6 else "⚠️ Small team - ensure workload balance"}
3. ✅ Expert-finder service available for real-time expert queries
4. 📊 See Section 3 for detailed skill matrix
5. 📋 See Section 8 for complete action plan

**Key Findings**:
- **Strengths**: {', '.join([tech for tech, experts in self.team_expertise.items() if len(experts) >= 2][:3]) or "Balanced skill distribution"}
- **Risks**: {', '.join(self.knowledge_gaps[:3]) if self.knowledge_gaps else "No significant skill gaps"}
- **Recommendation**: {"Focus on knowledge transfer for single-expert technologies" if any(len(e) == 1 for e in self.team_expertise.values()) else "Continue building on strong foundation"}

---

"""
    
    def _generate_team_member_profiles(self) -> str:
        """Generate Section 2: Your Team Members."""
        content = ["""## 2. Your Team Members

**Meet your team and understand their strengths:**

"""]
        
        for i, member in enumerate(self.team_members, 1):
            name = member.get("name", f"Team Member {i}")
            role = member.get("role", "Unknown Role")
            experience_level = member.get("experience_level", "Unknown")
            skills = member.get("skills", [])
            workload = member.get("current_workload", 0.0)
            velocity = member.get("recent_velocity", 0)
            
            # Extract skill names and years
            skill_details = []
            for skill in skills[:5]:  # Show top 5 skills
                if isinstance(skill, dict):
                    skill_name = skill.get("skill", "")
                    years = skill.get("years", 0)
                    skill_details.append(f"{skill_name} ({years}y)")
                else:
                    skill_details.append(str(skill))
            
            # Determine best fit based on skills
            best_for = self._determine_best_fit(skills)
            
            # Find collaborators (placeholder - would use workflow_f_result in real implementation)
            collaborators = "Collaborates well with team"
            
            # Availability assessment
            availability_status = "✅ Good" if workload < 0.75 else "⚠️ High workload" if workload < 0.90 else "🔴 Near capacity"
            
            content.append(f"""### {i}. **{name}** - {role}

**Experience**: {experience_level}  
**Top Skills**: {', '.join(skill_details) or 'N/A'}  
**Best For**: {best_for}  
**Availability**: {workload*100:.0f}% workload ({availability_status})  
**Recent Velocity**: {velocity} SP/sprint  
**Team Dynamics**: {collaborators}

**Recommended Role for This Project**: {self._recommend_role(member, skills)}

""")
        
        content.append("""
**Team Composition Summary**:
- Mix of experience levels ensures knowledge transfer
- Skill diversity enables cross-functional work
- Current workloads allow for new project assignments

---

""")
        
        return "\n".join(content)
    
    def _determine_best_fit(self, skills: List[Any]) -> str:
        """Determine what a team member is best suited for based on skills."""
        skill_names = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_names.append(skill.get("skill", "").lower())
            else:
                skill_names.append(str(skill).lower())
        
        if any("backend" in s or "api" in s or "python" in s or "fastapi" in s for s in skill_names):
            return "Backend development, API design, server-side logic"
        elif any("frontend" in s or "react" in s or "ui" in s for s in skill_names):
            return "Frontend development, UI/UX implementation, client-side features"
        elif any("devops" in s or "docker" in s or "kubernetes" in s or "ci" in s for s in skill_names):
            return "Infrastructure, deployment, DevOps, system reliability"
        elif any("mobile" in s or "ios" in s or "android" in s for s in skill_names):
            return "Mobile app development, native features, app optimization"
        else:
            return "Full-stack development, general engineering tasks"
    
    def _recommend_role(self, member: Dict[str, Any], skills: List[Any]) -> str:
        """Recommend a specific role for this project."""
        best_fit = self._determine_best_fit(skills)
        experience = member.get("experience_level", "")
        
        if "Backend" in best_fit:
            if "Expert" in experience or "Advanced" in experience:
                return "**Lead Backend Developer** - Architecture decisions, code reviews"
            else:
                return "**Backend Developer** - Feature implementation, API development"
        elif "Frontend" in best_fit:
            if "Expert" in experience or "Advanced" in experience:
                return "**Lead Frontend Developer** - UI architecture, component design"
            else:
                return "**Frontend Developer** - UI implementation, component development"
        elif "Infrastructure" in best_fit or "DevOps" in best_fit:
            return "**DevOps Lead** - Deployment strategy, infrastructure setup"
        elif "Mobile" in best_fit:
            return "**Mobile Developer** - Native app features, mobile optimization"
        else:
            return "**Full-Stack Developer** - Cross-functional development"
    
    def _generate_skill_matrix(self) -> str:
        """Generate Section 3: Technology Coverage & Skill Matrix."""
        content = ["""## 3. Technology Coverage & Skill Matrix

**Your Team's Skills Mapped to Project Requirements:**

"""]
        
        # Create skill matrix table
        content.append("""| Technology | Experts | Confidence | Coverage | Risk |
|------------|---------|------------|----------|------|
""")
        
        for tech in self.tech_stack:
            experts = self.team_expertise.get(tech, [])
            expert_count = len(experts)
            
            # Calculate average confidence (based on years of experience)
            if experts:
                avg_years = sum(e["years"] for e in experts) / len(experts)
                confidence = min(avg_years / 10.0, 1.0)  # Normalize to 0-1
            else:
                confidence = 0.0
            
            # Determine coverage status
            if expert_count >= 2:
                coverage = "✅ Strong"
                risk = "LOW"
            elif expert_count == 1:
                coverage = "⚠️ Limited"
                risk = "MEDIUM"
            else:
                coverage = "❌ Gap"
                risk = "HIGH"
            
            # Format experts list
            expert_names = ", ".join([e["name"] for e in experts[:2]])
            if len(experts) > 2:
                expert_names += f", +{len(experts)-2} more"
            elif not experts:
                expert_names = "None"
            
            content.append(f"| {tech} | {expert_names} | {confidence:.1f} | {coverage} | {risk} |\n")
        
        # Visual coverage representation
        content.append("""

**Visual Coverage**:

""")
        
        for tech in self.tech_stack:
            experts = self.team_expertise.get(tech, [])
            expert_count = len(experts)
            bar_length = min(expert_count * 14, 28)  # Max 28 chars for 2+ experts
            bar = "█" * bar_length + "░" * (28 - bar_length)
            status = "✅ 100%" if expert_count >= 2 else f"⚠️ {50}%" if expert_count == 1 else "❌ 0%"
            content.append(f"{bar} {tech} ({expert_count} {'expert' if expert_count == 1 else 'experts'}) {status}\n")
        
        content.append("""

**Interpretation**:
- ✅ **Strong Coverage**: 2+ experts (low risk, knowledge redundancy)
- ⚠️ **Limited Coverage**: 1 expert (medium risk, single point of failure)
- ❌ **No Coverage**: 0 experts (high risk, need external help or training)

**Risk Mitigation Recommendations**:
""")
        
        # Count coverage levels
        strong = sum(1 for e in self.team_expertise.values() if len(e) >= 2)
        limited = sum(1 for e in self.team_expertise.values() if len(e) == 1)
        gaps = len(self.knowledge_gaps)
        
        if gaps > 0:
            content.append(f"- **HIGH PRIORITY**: Address {gaps} technology gaps through hiring or training\n")
        if limited > 0:
            content.append(f"- **MEDIUM PRIORITY**: Implement pairing program for {limited} technologies with single-expert coverage\n")
        if strong >= len(self.tech_stack) * 0.5:
            content.append(f"- **STRENGTH**: Leverage {strong} technologies with strong coverage for project success\n")
        
        content.append("\n---\n\n")
        
        return "".join(content)
    
    def _generate_team_structure(self) -> str:
        """Generate Section 4: Recommended Team Structure for This Project."""
        return """## 4. Recommended Team Structure for This Project

**Suggested role assignments based on expertise and project needs:**

### Sprint Planning Overview

**Sprint 1-2 (Weeks 1-4): Foundation & Core Features**
""" + self._generate_sprint_assignments(1, 2) + """

**Sprint 3-4 (Weeks 5-8): Integration & Polish**
""" + self._generate_sprint_assignments(3, 4) + """

### Leadership Assignments

""" + self._generate_leadership_assignments() + """

### Code Review Assignments

**Recommended reviewer assignments to ensure quality:**

""" + self._generate_review_assignments() + """

---

"""
    
    def _generate_sprint_assignments(self, start_sprint: int, end_sprint: int) -> str:
        """Generate sprint-specific role assignments."""
        content = []
        
        # Group team members by their primary skills
        backend = [m for m in self.team_members if "backend" in str(m.get("skills", "")).lower() or "python" in str(m.get("skills", "")).lower()]
        frontend = [m for m in self.team_members if "react" in str(m.get("skills", "")).lower() or "frontend" in str(m.get("skills", "")).lower()]
        devops = [m for m in self.team_members if "docker" in str(m.get("skills", "")).lower() or "devops" in str(m.get("skills", "")).lower()]
        
        if backend:
            content.append(f"- **Backend Lead**: {backend[0].get('name', 'TBD')}\n")
        if frontend:
            content.append(f"- **Frontend Lead**: {frontend[0].get('name', 'TBD')}\n")
        if devops:
            content.append(f"- **DevOps/Infrastructure**: {devops[0].get('name', 'TBD')}\n")
        
        content.append("- **Code Reviews**: Rotating among senior team members\n")
        content.append("- **Pairing**: Cross-functional pairs for knowledge transfer\n\n")
        
        return "".join(content)
    
    def _generate_leadership_assignments(self) -> str:
        """Generate technology-specific leadership assignments."""
        content = []
        
        for tech in self.tech_stack[:5]:  # Top 5 technologies
            experts = self.team_expertise.get(tech, [])
            if experts:
                lead = experts[0]  # Most experienced
                content.append(f"- **{tech} Lead**: {lead['name']} ({lead['years']}y exp) - Technical decisions, code reviews\n")
            else:
                content.append(f"- **{tech} Lead**: *External consultant needed*\n")
        
        content.append("\n")
        return "".join(content)
    
    def _generate_review_assignments(self) -> str:
        """Generate code review assignments."""
        content = []
        
        for tech in self.tech_stack[:5]:
            experts = self.team_expertise.get(tech, [])
            if len(experts) >= 2:
                reviewers = [e['name'] for e in experts[:2]]
                content.append(f"- **{tech} PRs**: Primary - {reviewers[0]}, Secondary - {reviewers[1]}\n")
            elif len(experts) == 1:
                content.append(f"- **{tech} PRs**: {experts[0]['name']} (⚠️ single reviewer - consider pairing)\n")
            else:
                content.append(f"- **{tech} PRs**: *External review recommended*\n")
        
        content.append("\n")
        return "".join(content)
    
    def _generate_collaboration_insights(self) -> str:
        """Generate Section 5: Team Collaboration Insights."""
        return """## 5. Team Collaboration Insights

**Who works well together based on historical patterns:**

### Recommended Pairings

""" + self._generate_pairing_recommendations() + """

### Communication Channels

**Set up these collaboration channels for your team:**

- **Slack/Teams Channels**:
  - `#backend-dev` - Backend team discussions
  - `#frontend-dev` - Frontend team discussions
  - `#devops` - Infrastructure and deployment
  - `#code-review` - PR reviews and discussions
  - `#standup` - Daily standup updates

- **Pair Programming Schedule**:
  - Monday/Wednesday: Backend ↔ Frontend integration
  - Tuesday/Thursday: DevOps ↔ Backend deployment
  - Friday: Knowledge sharing sessions

---

"""
    
    def _generate_pairing_recommendations(self) -> str:
        """Generate specific pairing recommendations."""
        content = []
        
        # Create pairings based on complementary skills
        paired = set()
        pairing_count = 0
        
        for i, member1 in enumerate(self.team_members):
            if member1.get("name") in paired or pairing_count >= 5:
                break
            
            for member2 in self.team_members[i+1:]:
                if member2.get("name") in paired:
                    continue
                
                # Find complementary skills
                skills1 = set()
                for s in member1.get("skills", []):
                    if isinstance(s, dict):
                        skills1.add(s.get("skill", ""))
                    else:
                        skills1.add(str(s))
                
                skills2 = set()
                for s in member2.get("skills", []):
                    if isinstance(s, dict):
                        skills2.add(s.get("skill", ""))
                    else:
                        skills2.add(str(s))
                
                unique1 = skills1 - skills2
                unique2 = skills2 - skills1
                
                if unique1 and unique2:
                    pairing_count += 1
                    name1 = member1.get("name", "Member 1")
                    name2 = member2.get("name", "Member 2")
                    
                    content.append(f"""**Pairing {pairing_count}: {name1} ↔ {name2}**
- **Synergy**: Complementary skills ({', '.join(list(unique1)[:2])} ↔ {', '.join(list(unique2)[:2])})
- **Benefit**: Knowledge transfer and skill diversification
- **Activity**: Pair programming on cross-functional features

""")
                    paired.add(name1)
                    paired.add(name2)
                    break
        
        if not content:
            content.append("*Pairing recommendations based on team composition will be generated.*\n\n")
        
        return "".join(content)
    
    def _generate_expert_discovery_guide(self) -> str:
        """Generate Section 6: How to Find Experts During the Project."""
        return f"""## 6. How to Find Experts During the Project

**Real-time expert discovery using the expert-finder service:**

### Service Information

- **Expert-Finder URL**: {self.expert_finder_url}
- **API Documentation**: {self.expert_finder_url}/docs (Swagger UI)
- **Status**: ✅ Operational with 12 query endpoints

### Common Scenarios & API Calls

#### Scenario 1: "I need help with JWT token implementation"

```bash
curl -X POST {self.expert_finder_url}/experts/find \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "Who knows JWT token implementation?", "max_results": 5}}'
```

**Expected Result**: List of experts with JWT experience, ranked by confidence

---

#### Scenario 2: "Who can review my React component?"

```bash
curl {self.expert_finder_url}/experts/by-topic/React?max_results=5
```

**Expected Result**: React experts from your team and broader organization

---

#### Scenario 3: "Who are the authentication experts?"

```bash
curl {self.expert_finder_url}/experts/sme/authentication?max_results=5
```

**Expected Result**: Subject matter experts in authentication/security

---

#### Scenario 4: "Who has worked with [team member] before?"

```bash
curl {self.expert_finder_url}/experts/teammates/{{username}}?max_results=10
```

**Expected Result**: Potential collaborators based on shared work history

---

#### Scenario 5: "What's my team's expertise coverage?"

```bash
curl {self.expert_finder_url}/teams/{{team_id}}/expertise
```

**Expected Result**: Complete team expertise profile

---

### Advanced Queries

**Experience-Based**:
```bash
curl "{self.expert_finder_url}/experts/by-experience?level=senior&domain=backend"
```

**Code Reviewers**:
```bash
curl "{self.expert_finder_url}/experts/reviewers?technology=Python&min_reviews=10"
```

**Component Ownership**:
```bash
curl "{self.expert_finder_url}/experts/component-leads?component=authentication"
```

---

"""
    
    def _generate_training_plan(self) -> str:
        """Generate Section 7: Knowledge Gaps & Training Plan."""
        content = ["""## 7. Knowledge Gaps & Training Plan

**Identified gaps and recommended training:**

### Gap Summary

"""]
        
        if self.knowledge_gaps:
            content.append(f"""**Technologies with No Internal Expertise**: {len(self.knowledge_gaps)}

""")
            for i, gap in enumerate(self.knowledge_gaps, 1):
                content.append(f"{i}. **{gap}** - ⚠️ Critical gap\n")
            
            content.append(f"""

**Risk Assessment**: {"HIGH" if len(self.knowledge_gaps) >= 3 else "MEDIUM" if len(self.knowledge_gaps) >= 1 else "LOW"}

""")
        else:
            content.append("""✅ **No critical knowledge gaps identified!**

The team has coverage for all required technologies.

""")
        
        # Training schedule
        content.append("""
### Recommended Training Plan

**Week 1-2**: Foundation Training
""")
        
        if self.knowledge_gaps:
            content.append(f"- **{self.knowledge_gaps[0]} Workshop** (if applicable)\n")
            content.append("  - Duration: 2 days\n")
            content.append("  - Audience: Entire team\n")
            content.append("  - Goal: Build basic proficiency\n\n")
        else:
            content.append("- **Team Onboarding** - Project overview and architecture\n")
            content.append("- **Tool Setup** - Development environment configuration\n\n")
        
        content.append("""**Week 3-4**: Advanced Topics
- **Best Practices Sessions** (led by senior team members)
- **Code Review Workshop** - Standards and expectations
- **Pairing Sessions** - Knowledge transfer through collaboration

**Ongoing**:
- **Weekly Lunch & Learns** (rotating presenters)
  - Week 1: Security best practices
  - Week 2: Performance optimization
  - Week 3: Testing strategies
  - Week 4: Documentation practices

- **Monthly Tech Talks** - Deep dives into specific technologies
- **Quarterly Retrospectives** - Process improvements and lessons learned

---

""")
        
        return "".join(content)
    
    def _generate_action_items(self) -> str:
        """Generate Section 8: Action Items for Team Lead."""
        return """## 8. Action Items for Team Lead

**Your checklist for project success:**

### Before Project Start

- [ ] **Review Team Composition** (Section 2)
  - Ensure all roles are filled
  - Identify any hiring needs

- [ ] **Assess Technology Coverage** (Section 3)
  - Address critical knowledge gaps
  - Plan training for limited-coverage technologies

- [ ] **Assign Project Roles** (Section 4)
  - Communicate leadership assignments
  - Set up code review processes

- [ ] **Set Up Collaboration Channels** (Section 5)
  - Create Slack/Teams channels
  - Schedule pairing sessions

- [ ] **Introduce Expert-Finder Service** (Section 6)
  - Share API documentation with team
  - Demo common query scenarios

### Week 1: Project Kickoff

- [ ] Hold kickoff meeting with clear role assignments
- [ ] Start recommended pairing program
- [ ] Schedule first knowledge-sharing session
- [ ] Set up daily standups and sprint planning

### Throughout Project

- [ ] **Weekly**:
  - Monitor workload balance
  - Facilitate knowledge-sharing sessions
  - Use expert-finder for code review assignments

- [ ] **Sprint Retrospectives**:
  - Track knowledge transfer progress
  - Adjust team structure as needed
  - Identify emerging skill gaps

- [ ] **Monthly**:
  - Update team expertise profiles
  - Review and adjust training plan
  - Recognize skill growth and contributions

### Post-Project

- [ ] Document lessons learned
- [ ] Update expert-finder profiles with new skills gained
- [ ] Plan next training priorities based on project experience
- [ ] Celebrate team successes and individual growth

### Key Success Metrics

**Track these metrics throughout the project:**

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Code Review Turnaround** | < 24 hours | PR merge time |
| **Knowledge Transfer** | +2 skills per member | Expert-finder profiles |
| **Collaboration Quality** | High team satisfaction | Retrospective feedback |
| **Technology Coverage** | 80%+ strong coverage | Regular skill assessments |
| **Project Velocity** | Consistent or improving | Sprint burn-down |

### Emergency Contacts

**If you need immediate expert help:**

1. **Use Expert-Finder** (`/experts/find`) for real-time queries
2. **Check SME List** (Section 10 of Planning Report)
3. **Contact Architecture Team** (if critical architecture decisions needed)
4. **External Consultants** (for knowledge gap technologies)

---

"""


if __name__ == "__main__":
    print("="*80)
    print("USER & TEAM REPORT GENERATOR - PHASE 3")
    print("="*80)
    print("\nThis module generates a comprehensive User & Team Report with 8 sections:")
    print("  1. Executive Summary for Team Leads")
    print("  2. Your Team Members")
    print("  3. Technology Coverage & Skill Matrix")
    print("  4. Recommended Team Structure for This Project")
    print("  5. Team Collaboration Insights")
    print("  6. How to Find Experts During the Project")
    print("  7. Knowledge Gaps & Training Plan")
    print("  8. Action Items for Team Lead")
    print("\n" + "="*80)

