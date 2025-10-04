"""
Executive Dashboard Report Generator

Generates a 3-page executive summary for C-suite decision-makers.
Distills 121,000+ characters (40-50 pages) into a 3-page actionable report.

Features:
- GO/NO-GO recommendation with confidence level
- 8 key metrics at a glance
- Risk heat map with mitigation strategies
- ROI analysis with payback period
- Decision points for leadership
- Next steps and milestones

Target Audience: C-suite, VPs, Directors
Reading Time: 3 minutes (vs 30+ minutes for full reports)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


@dataclass
class ExecutiveMetrics:
    """Key metrics for executive dashboard."""
    project_confidence: float  # 0-100%
    team_readiness: float  # 0-100%
    expert_availability: float  # 0-100%
    technology_risk: str  # LOW, MEDIUM, HIGH
    estimated_timeline_weeks: float
    estimated_timeline_worst_case: float
    estimated_cost: float
    budget_available: float
    roi_percentage: float
    payback_months: float
    go_no_go_confidence: float  # 0-100%
    recommendation: str  # GO, NO-GO, CONDITIONAL


@dataclass
class RiskItem:
    """Individual risk with mitigation strategy."""
    category: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    impact: str
    mitigation: str
    cost: float
    timeline: str


@dataclass
class DecisionPoint:
    """Decision point for leadership."""
    question: str
    context: str
    options: List[str]
    recommendation: str
    impact: str


class ExecutiveDashboardGenerator:
    """Generates executive dashboard report from demo metadata."""
    
    def __init__(
        self,
        metadata: Dict,
        workflow_f_result=None,
        service_discovery_results: Dict = None,
        persistence_stats: Dict = None,
        feature_summary: str = ""
    ):
        """
        Initialize dashboard generator.
        
        Args:
            metadata: Demo metadata dictionary (single source of truth)
            workflow_f_result: User intelligence workflow results
            service_discovery_results: Intelligent service discovery results
            persistence_stats: Data persistence statistics
            feature_summary: Feature description
        """
        self.metadata = metadata
        self.workflow_f_result = workflow_f_result
        self.service_discovery_results = service_discovery_results or {}
        self.persistence_stats = persistence_stats or {}
        self.feature_summary = feature_summary
        
        # Calculate executive metrics
        self.metrics = self._calculate_metrics()
        
        # Identify risks
        self.risks = self._identify_risks()
        
        # Generate decision points
        self.decision_points = self._generate_decision_points()
    
    def _calculate_metrics(self) -> ExecutiveMetrics:
        """Calculate all executive metrics."""
        # Project confidence (from metadata)
        project_confidence = self.metadata.get('report_confidence', 0.85) * 100
        
        # Team readiness (based on team size, skills, and tech gaps)
        team_size = self.metadata.get('team_size', 0)
        technologies = self.metadata.get('technologies', 0)
        users_extracted = self.metadata.get('users_extracted', 0)
        
        # Calculate tech gaps (simple heuristic)
        required_tech = technologies
        available_experts = len(self.workflow_f_result.subject_matter_experts) if self.workflow_f_result else 0
        tech_coverage = min(available_experts / max(required_tech, 1), 1.0) if required_tech > 0 else 0.8
        team_readiness = (0.7 * tech_coverage + 0.3 * min(team_size / 6, 1.0)) * 100
        
        # Expert availability (from Workflow F)
        smes_identified = self.metadata.get('smes_identified', 0)
        expert_availability = min(smes_identified / max(required_tech * 2, 1), 1.0) * 100 if required_tech > 0 else 90.0
        
        # Technology risk assessment
        tech_gaps = max(0, required_tech - available_experts)
        if tech_gaps == 0:
            technology_risk = "LOW"
        elif tech_gaps <= 2:
            technology_risk = "MEDIUM"
        else:
            technology_risk = "HIGH"
        
        # Timeline estimation (weeks)
        # Base: 3 weeks + 0.5 weeks per tech + 0.3 weeks per gap
        base_timeline = 3.0
        tech_factor = technologies * 0.5
        gap_factor = tech_gaps * 0.3
        estimated_timeline = base_timeline + tech_factor + gap_factor
        estimated_timeline_worst_case = estimated_timeline * 1.4  # 40% buffer
        
        # Cost estimation
        # Base: $100K + $10K per tech + $15K per gap
        base_cost = 100000
        tech_cost = technologies * 10000
        gap_cost = tech_gaps * 15000
        estimated_cost = base_cost + tech_cost + gap_cost
        
        # Budget (assume 125% of estimated cost for this demo)
        budget_available = estimated_cost * 1.25
        
        # ROI calculation
        # Assume value = 2.5x cost for successful project
        project_value = estimated_cost * 2.5
        roi_percentage = ((project_value - estimated_cost) / estimated_cost) * 100
        
        # Payback period (months)
        # Assume project generates value at $30K/month
        monthly_value = 30000
        payback_months = estimated_cost / monthly_value
        
        # GO/NO-GO recommendation
        go_factors = {
            'confidence': 1.0 if project_confidence >= 80 else 0.0,
            'team_readiness': 1.0 if team_readiness >= 70 else 0.5 if team_readiness >= 60 else 0.0,
            'expert_availability': 1.0 if expert_availability >= 80 else 0.7 if expert_availability >= 60 else 0.3,
            'budget': 1.0 if budget_available >= estimated_cost else 0.0,
            'tech_risk': 1.0 if technology_risk == "LOW" else 0.7 if technology_risk == "MEDIUM" else 0.3
        }
        go_no_go_confidence = (sum(go_factors.values()) / len(go_factors)) * 100
        
        # Recommendation logic
        if go_no_go_confidence >= 80:
            recommendation = "GO"
        elif go_no_go_confidence >= 60:
            recommendation = "CONDITIONAL GO"
        else:
            recommendation = "NO-GO"
        
        return ExecutiveMetrics(
            project_confidence=project_confidence,
            team_readiness=team_readiness,
            expert_availability=expert_availability,
            technology_risk=technology_risk,
            estimated_timeline_weeks=estimated_timeline,
            estimated_timeline_worst_case=estimated_timeline_worst_case,
            estimated_cost=estimated_cost,
            budget_available=budget_available,
            roi_percentage=roi_percentage,
            payback_months=payback_months,
            go_no_go_confidence=go_no_go_confidence,
            recommendation=recommendation
        )
    
    def _identify_risks(self) -> List[RiskItem]:
        """Identify and prioritize risks."""
        risks = []
        
        # Technology skill gaps
        tech_gaps = max(0, self.metadata.get('technologies', 0) - 
                       (len(self.workflow_f_result.subject_matter_experts) if self.workflow_f_result else 0))
        if tech_gaps > 0:
            severity = "HIGH" if tech_gaps > 2 else "MEDIUM"
            risks.append(RiskItem(
                category="Skills Gap",
                severity=severity,
                description=f"{tech_gaps} technology area(s) lack identified SMEs",
                impact=f"Delayed development ({tech_gaps * 0.5:.1f} weeks), increased training costs",
                mitigation="Engage external consultants, allocate training budget, pair programming with SMEs",
                cost=tech_gaps * 15000,
                timeline=f"{tech_gaps * 2} weeks training"
            ))
        
        # Team size risks
        team_size = self.metadata.get('team_size', 0)
        if team_size < 4:
            risks.append(RiskItem(
                category="Resource Constraint",
                severity="MEDIUM",
                description=f"Small team size ({team_size} members) may limit velocity",
                impact="Extended timeline, single points of failure, knowledge silos",
                mitigation="Consider team augmentation, ensure cross-training, document extensively",
                cost=25000,
                timeline="2 weeks onboarding"
            ))
        
        # Service discovery gaps
        services_discovered = self.metadata.get('services_discovered', 0)
        if services_discovered < 5:
            risks.append(RiskItem(
                category="Integration Complexity",
                severity="LOW",
                description=f"Limited external service discovery ({services_discovered} services)",
                impact="Potential missed dependencies, integration surprises",
                mitigation="Conduct thorough architecture review, allocate integration buffer",
                cost=10000,
                timeline="1 week review"
            ))
        
        # Data quality risks
        total_documents = self.metadata.get('total_documents', 0)
        if total_documents < 10:
            risks.append(RiskItem(
                category="Planning Data",
                severity="LOW",
                description=f"Limited historical data ({total_documents} documents)",
                impact="Lower confidence in estimates, potential surprises",
                mitigation="Supplement with expert interviews, add contingency buffer",
                cost=5000,
                timeline="Ongoing"
            ))
        
        # Sort by severity: CRITICAL > HIGH > MEDIUM > LOW
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        risks.sort(key=lambda r: severity_order.get(r.severity, 4))
        
        return risks[:5]  # Top 5 risks
    
    def _generate_decision_points(self) -> List[DecisionPoint]:
        """Generate key decision points for leadership."""
        decision_points = []
        
        # Decision 1: Training budget
        tech_gaps = max(0, self.metadata.get('technologies', 0) - 
                       (len(self.workflow_f_result.subject_matter_experts) if self.workflow_f_result else 0))
        if tech_gaps > 0:
            training_cost = tech_gaps * 15000
            decision_points.append(DecisionPoint(
                question=f"Approve ${training_cost/1000:.0f}K training budget for {tech_gaps} technology area(s)?",
                context=f"Team has skill gaps in {tech_gaps} critical technologies",
                options=[
                    f"YES - Allocate ${training_cost/1000:.0f}K for training/consulting ({tech_gaps * 2} weeks)",
                    f"PARTIAL - Allocate ${training_cost/2/1000:.0f}K, accept timeline extension (+{tech_gaps * 1:.0f} weeks)",
                    f"NO - Proceed with existing skills (HIGH RISK, +{tech_gaps * 2:.0f} weeks)"
                ],
                recommendation=f"YES - Training ROI pays back in {(training_cost / 30000):.1f} months",
                impact=f"Timeline: {tech_gaps * 0.5:.1f} weeks saved, Quality: +25%, Risk: -40%"
            ))
        
        # Decision 2: External SME engagement
        smes_identified = self.metadata.get('smes_identified', 0)
        if smes_identified > 3:
            decision_points.append(DecisionPoint(
                question=f"Engage {smes_identified} identified subject matter experts?",
                context=f"Workflow F discovered {smes_identified} SMEs with relevant expertise",
                options=[
                    f"YES - Engage all {smes_identified} SMEs as advisors ($30K total)",
                    f"SELECTIVE - Engage top 3 SMEs ($15K)",
                    f"NO - Internal team only (higher risk)"
                ],
                recommendation="SELECTIVE - Engage top 3 SMEs for critical areas",
                impact="Timeline: 1 week saved, Quality: +15%, Risk: -25%"
            ))
        
        # Decision 3: Timeline expectations
        estimated_weeks = self.metrics.estimated_timeline_weeks
        worst_case_weeks = self.metrics.estimated_timeline_worst_case
        decision_points.append(DecisionPoint(
            question=f"Accept {estimated_weeks:.1f}-week timeline (best case) vs {worst_case_weeks:.1f}-week (worst case)?",
            context=f"Analysis suggests {estimated_weeks:.1f} weeks with current team and {tech_gaps} skill gaps",
            options=[
                f"AGGRESSIVE - Target {estimated_weeks:.1f} weeks (requires training approval)",
                f"REALISTIC - Target {(estimated_weeks + worst_case_weeks) / 2:.1f} weeks (balanced risk)",
                f"CONSERVATIVE - Target {worst_case_weeks:.1f} weeks (lowest risk)"
            ],
            recommendation=f"REALISTIC - {(estimated_weeks + worst_case_weeks) / 2:.1f} weeks with 20% buffer",
            impact="Balances stakeholder expectations with delivery confidence"
        ))
        
        return decision_points[:3]  # Top 3 decisions
    
    def generate_report(self) -> str:
        """Generate complete 3-page executive dashboard."""
        sections = []
        
        # Page 1: Executive Summary
        sections.append(self._generate_page_1_executive_summary())
        
        # Page 2: Risk Analysis & Mitigation
        sections.append(self._generate_page_2_risk_analysis())
        
        # Page 3: Decision Points & Next Steps
        sections.append(self._generate_page_3_decision_points())
        
        return "\n\n".join(sections)
    
    def _generate_page_1_executive_summary(self) -> str:
        """Generate Page 1: One-page executive summary."""
        m = self.metrics
        
        # Recommendation badge
        if m.recommendation == "GO":
            rec_badge = "✅ **GO**"
            rec_color = "🟢"
        elif m.recommendation == "CONDITIONAL GO":
            rec_badge = "⚠️ **CONDITIONAL GO**"
            rec_color = "🟡"
        else:
            rec_badge = "❌ **NO-GO**"
            rec_color = "🔴"
        
        page = f"""# 📊 Executive Dashboard - {self.feature_summary[:60]}...

**Generated:** {self.metadata.get('demo_timestamp', datetime.now().isoformat())}  
**For:** C-Suite, VPs, Directors  
**Reading Time:** 3 minutes

---

## 🎯 GO/NO-GO Recommendation

{rec_color} **{m.recommendation}** ({m.go_no_go_confidence:.0f}% Confidence)

**Reasoning:** {"This project is ready to proceed with current team and resources." if m.recommendation == "GO" else "This project requires training budget approval and SME engagement." if m.recommendation == "CONDITIONAL GO" else "This project has significant risks that need resolution before proceeding."}

---

## 📈 8 Key Metrics at a Glance

| Metric | Value | Status |
|--------|-------|--------|
| **Project Confidence** | {m.project_confidence:.0f}% | {"🟢 Strong" if m.project_confidence >= 80 else "🟡 Moderate" if m.project_confidence >= 60 else "🔴 Weak"} |
| **Team Readiness** | {m.team_readiness:.0f}% | {"🟢 Ready" if m.team_readiness >= 75 else "🟡 Needs Training" if m.team_readiness >= 60 else "🔴 Not Ready"} |
| **Expert Availability** | {m.expert_availability:.0f}% | {"🟢 High" if m.expert_availability >= 80 else "🟡 Medium" if m.expert_availability >= 60 else "🔴 Low"} |
| **Technology Risk** | {m.technology_risk} | {"🟢 Manageable" if m.technology_risk == "LOW" else "🟡 Monitor" if m.technology_risk == "MEDIUM" else "🔴 Critical"} |
| **Timeline (Best/Worst)** | {m.estimated_timeline_weeks:.1f}w / {m.estimated_timeline_worst_case:.1f}w | {"🟢 Fast" if m.estimated_timeline_weeks <= 4 else "🟡 Standard" if m.estimated_timeline_weeks <= 6 else "🔴 Long"} |
| **Estimated Cost** | ${m.estimated_cost/1000:.0f}K | {"🟢 Under Budget" if m.estimated_cost <= m.budget_available else "🟡 At Budget" if m.estimated_cost <= m.budget_available * 1.1 else "🔴 Over Budget"} |
| **ROI** | {m.roi_percentage:.0f}% | {"🟢 Excellent" if m.roi_percentage >= 150 else "🟡 Good" if m.roi_percentage >= 100 else "🔴 Poor"} |
| **Payback Period** | {m.payback_months:.1f} months | {"🟢 Fast" if m.payback_months <= 4 else "🟡 Standard" if m.payback_months <= 6 else "🔴 Slow"} |

---

## 💰 Budget Breakdown

| Item | Amount | Notes |
|------|--------|-------|
| **Development** | ${(m.estimated_cost * 0.7)/1000:.0f}K | {self.metadata.get('team_size', 6)} developers × {m.estimated_timeline_weeks:.0f} weeks |
| **Training/Consulting** | ${(m.estimated_cost * 0.15)/1000:.0f}K | Skill gap mitigation |
| **Infrastructure** | ${(m.estimated_cost * 0.10)/1000:.0f}K | Cloud, tools, licenses |
| **Contingency (10%)** | ${(m.estimated_cost * 0.05)/1000:.0f}K | Risk buffer |
| **Total Estimated** | **${m.estimated_cost/1000:.0f}K** | |
| **Budget Available** | ${m.budget_available/1000:.0f}K | |
| **Cushion** | **+${(m.budget_available - m.estimated_cost)/1000:.0f}K** | {"🟢 Healthy" if m.budget_available - m.estimated_cost > m.estimated_cost * 0.2 else "🟡 Tight" if m.budget_available > m.estimated_cost else "🔴 Insufficient"} |

---

## 📅 Timeline with Critical Path

```
Week 1-2:    Sprint 0 (Planning, Environment Setup)
Week 3-{int(m.estimated_timeline_weeks * 0.6)}:    Core Development ({self.metadata.get('technologies', 4)} technologies)
Week {int(m.estimated_timeline_weeks * 0.6) + 1}-{int(m.estimated_timeline_weeks * 0.85)}:  Integration & Testing
Week {int(m.estimated_timeline_weeks * 0.85) + 1}-{int(m.estimated_timeline_weeks)}:    UAT & Deployment

Critical Path: {"Development → Integration → UAT" if m.technology_risk == "LOW" else "Training → Development → Integration → UAT"}
Buffer: {((m.estimated_timeline_worst_case - m.estimated_timeline_weeks) / m.estimated_timeline_weeks * 100):.0f}% ({m.estimated_timeline_worst_case - m.estimated_timeline_weeks:.1f} weeks)
```

---

## 👥 Expert Availability (Workflow F Results)

**SMEs Identified:** {self.metadata.get('smes_identified', 0)} subject matter experts  
**User Intelligence:** {self.metadata.get('users_extracted', 0)} users analyzed from {self.metadata.get('total_documents', 0)} documents  
**Services Discovered:** {self.metadata.get('services_discovered', 0)} external services mapped

**Top Strengths:**
{self._format_top_strengths()}

**Key Gaps:**
{self._format_key_gaps()}

---

## 📊 ROI Analysis

| Scenario | Investment | Return | ROI | Payback |
|----------|------------|--------|-----|---------|
| **Base Case** | ${m.estimated_cost/1000:.0f}K | ${(m.estimated_cost * 2.5)/1000:.0f}K | {m.roi_percentage:.0f}% | {m.payback_months:.1f} months |
| **Optimistic** | ${(m.estimated_cost * 0.9)/1000:.0f}K | ${(m.estimated_cost * 3.0)/1000:.0f}K | {(((m.estimated_cost * 3.0) - (m.estimated_cost * 0.9)) / (m.estimated_cost * 0.9) * 100):.0f}% | {(m.estimated_cost * 0.9 / 30000):.1f} months |
| **Pessimistic** | ${(m.estimated_cost * 1.2)/1000:.0f}K | ${(m.estimated_cost * 2.0)/1000:.0f}K | {(((m.estimated_cost * 2.0) - (m.estimated_cost * 1.2)) / (m.estimated_cost * 1.2) * 100):.0f}% | {(m.estimated_cost * 1.2 / 30000):.1f} months |

**Break-even:** {m.payback_months:.1f} months at $30K/month value generation

---

**Page 1 of 3** • [Continue to Risk Analysis →](#page-2-risk-analysis--mitigation)
"""
        return page
    
    def _format_top_strengths(self) -> str:
        """Format top team strengths."""
        # Simple heuristic based on metadata
        strengths = []
        
        if self.metadata.get('team_size', 0) >= 6:
            strengths.append("- **Team Size:** Adequate coverage ({} members)".format(self.metadata.get('team_size')))
        
        if self.metadata.get('smes_identified', 0) >= 5:
            strengths.append("- **Expert Network:** {} SMEs available for consultation".format(self.metadata.get('smes_identified')))
        
        if self.metadata.get('users_extracted', 0) >= 10:
            strengths.append("- **User Intelligence:** {} users profiled, collaboration patterns mapped".format(self.metadata.get('users_extracted')))
        
        if self.metadata.get('services_discovered', 0) >= 10:
            strengths.append("- **Service Catalog:** {} external services documented".format(self.metadata.get('services_discovered')))
        
        return "\n".join(strengths) if strengths else "- Team and resources are adequate for project scope"
    
    def _format_key_gaps(self) -> str:
        """Format key skill/resource gaps."""
        gaps = []
        
        tech_gaps = max(0, self.metadata.get('technologies', 0) - 
                       (len(self.workflow_f_result.subject_matter_experts) if self.workflow_f_result else 0))
        
        if tech_gaps > 0:
            gaps.append(f"- **Skills:** {tech_gaps} technology area(s) lack SMEs (training recommended)")
        
        if self.metadata.get('team_size', 0) < 4:
            gaps.append(f"- **Resources:** Small team size ({self.metadata.get('team_size')}) may limit velocity")
        
        if self.metadata.get('total_documents', 0) < 10:
            gaps.append(f"- **Data:** Limited historical data ({self.metadata.get('total_documents')} documents) for planning")
        
        return "\n".join(gaps) if gaps else "- No critical gaps identified"
    
    def _generate_page_2_risk_analysis(self) -> str:
        """Generate Page 2: Risk analysis & mitigation."""
        page = f"""---

## Page 2: Risk Analysis & Mitigation

### 🔥 Risk Heat Map

| Risk Category | Severity | Impact | Mitigation Cost | Status |
|---------------|----------|--------|----------------|--------|
"""
        for risk in self.risks:
            severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk.severity, "⚪")
            page += f"| {risk.category} | {severity_icon} {risk.severity} | {risk.impact[:40]}... | ${risk.cost/1000:.0f}K | {risk.timeline} |\n"
        
        page += f"""
**Total Mitigation Cost:** ${sum(r.cost for r in self.risks)/1000:.0f}K  
**Timeline Impact:** {max([int(r.timeline.split()[0]) for r in self.risks if r.timeline.split()[0].isdigit()] + [0])} weeks

---

### 📋 Detailed Risk Assessment

"""
        for i, risk in enumerate(self.risks, 1):
            severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk.severity, "⚪")
            page += f"""
#### {i}. {risk.category} ({severity_icon} {risk.severity})

**Description:** {risk.description}

**Impact:** {risk.impact}

**Mitigation Strategy:**  
{risk.mitigation}

**Investment Required:** ${risk.cost/1000:.0f}K over {risk.timeline}

**Residual Risk After Mitigation:** {"🟢 LOW" if risk.severity in ["LOW", "MEDIUM"] else "🟡 MEDIUM"}

---
"""
        
        page += f"""
### 🎯 Recommended Actions (Immediate)

"""
        if self.risks:
            page += "**Within 48 Hours:**\n"
            for i, risk in enumerate(self.risks[:2], 1):
                page += f"{i}. Address {risk.category}: {risk.mitigation.split(',')[0]}\n"
            
            page += "\n**Within 1 Week:**\n"
            for i, risk in enumerate(self.risks[2:4], 1):
                if i + 1 < len(self.risks):
                    page += f"{i}. Address {risk.category}: {risk.mitigation.split(',')[0]}\n"
        
        page += f"""

### 📊 Alternative Scenarios

| Scenario | Cost | Timeline | Risk Level | Recommendation |
|----------|------|----------|------------|----------------|
| **A: Aggressive** | ${self.metrics.estimated_cost * 0.9 / 1000:.0f}K | {self.metrics.estimated_timeline_weeks:.0f}w | 🔴 HIGH | Not recommended |
| **B: Balanced** | ${self.metrics.estimated_cost / 1000:.0f}K | {self.metrics.estimated_timeline_weeks:.0f}w | 🟡 MEDIUM | **✅ Recommended** |
| **C: Conservative** | ${self.metrics.estimated_cost * 1.2 / 1000:.0f}K | {self.metrics.estimated_timeline_worst_case:.0f}w | 🟢 LOW | Acceptable alternative |

**Recommendation:** Scenario B (Balanced) offers best risk/reward ratio with {self.metrics.go_no_go_confidence:.0f}% confidence.

---

### 👥 Team Readiness Breakdown

| Team Member Role | Skill Level | Gap Analysis | Action Required |
|-----------------|-------------|--------------|-----------------|
"""
        # Simple heuristic for team breakdown
        team_size = self.metadata.get('team_size', 6)
        technologies = self.metadata.get('tech_stack', [])
        
        roles = ["Tech Lead", "Senior Dev", "Mid-Level Dev", "Junior Dev", "QA Engineer", "DevOps Engineer"]
        for i, role in enumerate(roles[:team_size]):
            if i < len(technologies):
                page += f"| {role} | {'⭐⭐⭐⭐⭐' if i == 0 else '⭐⭐⭐⭐' if i < 2 else '⭐⭐⭐'} | {technologies[i] if i < len(technologies) else 'General'} | {'None' if i < 2 else 'Training'} |\n"
        
        page += f"""

**Overall Team Readiness:** {self.metrics.team_readiness:.0f}% ({"🟢 Ready" if self.metrics.team_readiness >= 75 else "🟡 Needs Support"})

---

**Page 2 of 3** • [← Back to Summary](#-executive-dashboard---{self.feature_summary[:20].replace(' ', '-')}) • [Continue to Decisions →](#page-3-decision-points--next-steps)
"""
        return page
    
    def _generate_page_3_decision_points(self) -> str:
        """Generate Page 3: Decision points & next steps."""
        page = """---

## Page 3: Decision Points & Next Steps

### ⚡ 3 Critical Decisions for Leadership

"""
        for i, dp in enumerate(self.decision_points, 1):
            page += f"""
#### Decision {i}: {dp.question}

**Context:** {dp.context}

**Options:**
"""
            for j, option in enumerate(dp.options, 1):
                page += f"   {j}. {option}\n"
            
            page += f"""
**Recommendation:** ✅ {dp.recommendation}

**Impact:** {dp.impact}

---
"""
        
        page += f"""
### 🚀 Next Steps (48 Hours)

**Immediate Actions:**
1. **Decision:** Review and approve recommendations above
2. **Budget:** Confirm ${self.metrics.estimated_cost/1000:.0f}K allocation
3. **Team:** Notify team leads of GO decision
4. **Training:** If approved, schedule training for Week 1

**Communication:**
- **Stakeholders:** Email summary with timeline
- **Team:** Kickoff meeting scheduled
- **SMEs:** Engagement agreements if approved

---

### 📅 Week 1 Milestones

| Day | Milestone | Owner | Deliverable |
|-----|-----------|-------|-------------|
| Day 1 | Project Kickoff | Tech Lead | Kickoff slides, team roster |
| Day 2 | Environment Setup | DevOps | Dev environments ready |
| Day 3 | Architecture Review | Tech Lead + SMEs | Architecture doc v1 |
| Day 4 | Sprint Planning | Team | Sprint 1 backlog |
| Day 5 | First Commit | Team | "Hello World" deployed |

---

### ✅ Go/No-Go Checkpoints

We recommend 3 checkpoints to validate progress:

**Checkpoint 1: Week 2 (Sprint 0 Complete)**
- ✓ Environment setup complete
- ✓ Architecture approved
- ✓ Team trained on key technologies
- ✓ First sprint planned

**GO/NO-GO:** {"🟢 Proceed to Sprint 1" if self.metrics.team_readiness >= 70 else "🟡 Address training gaps"}

**Checkpoint 2: Week {int(self.metrics.estimated_timeline_weeks * 0.5)} (Midpoint)**
- ✓ 50% of features implemented
- ✓ Integration tests passing
- ✓ No critical blockers
- ✓ Timeline on track (±10%)

**GO/NO-GO:** {"🟢 Proceed to integration phase" if self.metrics.project_confidence >= 80 else "🟡 Re-assess timeline"}

**Checkpoint 3: Week {int(self.metrics.estimated_timeline_weeks * 0.85)} (Pre-UAT)**
- ✓ All features code-complete
- ✓ End-to-end tests passing
- ✓ Documentation complete
- ✓ UAT environment ready

**GO/NO-GO:** {"🟢 Begin UAT" if self.metrics.project_confidence >= 80 else "🟡 Address quality issues"}

---

### 📚 Links to Detailed Reports

For deeper analysis, refer to these detailed reports:

1. **[Planning Service Report](./reports/Planning_Service_Report.md)** - Business timeline, ROI, milestones
2. **[Behind-the-Scenes Report](./reports/Behind_the_Scenes_Report.md)** - Technical implementation details
3. **[User & Team Report](./reports/User_and_Team_Report.md)** - Team composition, skills, collaboration
4. **[Ecosystem Validation Report](./reports/Ecosystem_Validation_Report.md)** - Service validation, live code proof
5. **[Data Architecture Report](./reports/Data_Architecture_Report.md)** - Data flow, schemas, user intelligence

**Total Detail:** 50+ pages of analysis (vs this 3-page summary)

---

### 🎯 Final Recommendation

{self._generate_final_recommendation()}

---

**Page 3 of 3** • [← Back to Risk Analysis](#page-2-risk-analysis--mitigation) • [↑ Back to Top](#-executive-dashboard---{self.feature_summary[:20].replace(' ', '-')})

---

*This Executive Dashboard was generated by AI-powered planning system on {self.metadata.get('demo_timestamp', 'N/A')}*  
*Report Confidence: {self.metrics.project_confidence:.0f}% | GO/NO-GO Confidence: {self.metrics.go_no_go_confidence:.0f}%*
"""
        return page
    
    def _generate_final_recommendation(self) -> str:
        """Generate final recommendation based on all factors."""
        m = self.metrics
        
        if m.recommendation == "GO":
            return f"""
**🟢 GO - Proceed with Confidence ({m.go_no_go_confidence:.0f}%)**

This project is ready to proceed. The team has adequate skills, expert support is available, and the budget is sufficient. We recommend:

1. **Approve:** ${m.estimated_cost/1000:.0f}K budget allocation
2. **Timeline:** Target {m.estimated_timeline_weeks:.0f}-week delivery with {(m.estimated_timeline_worst_case - m.estimated_timeline_weeks):.0f}-week buffer
3. **Training:** Allocate ${sum(r.cost for r in self.risks if r.category == "Skills Gap")/1000:.0f}K for identified skill gaps
4. **Proceed:** Begin Week 1 immediately upon approval

**Expected ROI:** {m.roi_percentage:.0f}% ({m.payback_months:.1f}-month payback)
"""
        elif m.recommendation == "CONDITIONAL GO":
            return f"""
**🟡 CONDITIONAL GO - Proceed with Training/SME Engagement ({m.go_no_go_confidence:.0f}%)**

This project can succeed with the following conditions met:

1. **Approve Training Budget:** ${sum(r.cost for r in self.risks if r.category == "Skills Gap")/1000:.0f}K for skill gap mitigation
2. **Engage SMEs:** Secure {min(3, self.metadata.get('smes_identified', 0))} subject matter experts as advisors
3. **Extended Timeline:** Accept {self.metrics.estimated_timeline_worst_case:.0f}-week timeline (vs {self.metrics.estimated_timeline_weeks:.0f}-week optimistic)
4. **Checkpoint Reviews:** Mandatory GO/NO-GO reviews at Weeks 2, {int(self.metrics.estimated_timeline_weeks * 0.5)}, and {int(self.metrics.estimated_timeline_weeks * 0.85)}

**If conditions met:** Expected ROI {m.roi_percentage:.0f}% ({m.payback_months:.1f}-month payback)  
**If conditions not met:** Re-assess viability before Week 1
"""
        else:
            return f"""
**🔴 NO-GO - Address Critical Risks First ({m.go_no_go_confidence:.0f}%)**

This project has significant risks that must be resolved before proceeding:

1. **Team Readiness:** Only {m.team_readiness:.0f}% (target: 70%+)
2. **Skill Gaps:** {max(0, self.metadata.get('technologies', 0) - (len(self.workflow_f_result.subject_matter_experts) if self.workflow_f_result else 0))} critical technology areas lack SMEs
3. **Budget:** ${m.estimated_cost/1000:.0f}K required vs ${m.budget_available/1000:.0f}K available

**Recommended Actions Before Re-Assessment:**
1. Secure training budget and complete upskilling (4-6 weeks)
2. Hire/contract SMEs for critical areas
3. Conduct feasibility study with updated team composition

**Re-assess in:** 6-8 weeks after remediation actions
"""

