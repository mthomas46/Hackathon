"""Visual Enhancements for Demo Reports

Utility functions to generate ASCII art diagrams, charts, and visual elements
for improving report comprehension and presentation.
"""

def generate_service_architecture_diagram(services_count: int, team_size: int) -> str:
    """Generate ASCII art service architecture diagram"""
    return f"""
```
┌────────────────────────────────────────────────────────────────────────┐
│                    ECOSYSTEM SERVICE ARCHITECTURE                       │
│                     ({services_count} Services Discovered)              │
└────────────────────────────────────────────────────────────────────────┘

                        ┌──────────────┐
                        │  LLM Gateway │
                        │   (Port 8100)│
                        └───────┬──────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │ Doc Store    │ │  Prompt   │ │   Memory    │
        │ (Port 5087)  │ │   Store   │ │   Agent     │
        │              │ │(Port 5110)│ │ (Port 5090) │
        └──────────────┘ └───────────┘ └─────────────┘
                │               │               │
                └───────────────┼───────────────┘
                                │
                        ┌───────▼──────┐
                        │  Project     │
                        │  Planning    │
                        │  Service     │
                        └──────────────┘
                                │
                        ┌───────▼──────┐
                        │ Your Project │
                        │ ({team_size} team members) │
                        └──────────────┘

Legend:
  ┌──┐
  │  │  = Service/Component
  └──┘
   │   = Data flow
   ▼   = Direction
```
"""

def generate_workflow_sequence_diagram(workflows: list) -> str:
    """Generate workflow execution sequence diagram"""
    workflow_lines = []
    for i, wf in enumerate(workflows, 1):
        workflow_lines.append(f"    {i}. {wf}")
    
    workflows_text = "\n".join(workflow_lines)
    
    return f"""
```
WORKFLOW EXECUTION SEQUENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start → {workflows_text}
                              ↓
                        Final Report
                              ↓
                          Complete ✓

Parallel Execution:
  • Workflows A-C: Document analysis (simultaneous)
  • Workflow D: Planning generation (uses A-C results)
  • Workflows E-F: Enhancements (parallel with D)

Timeline: ~2-15 minutes depending on data volume
```
"""

def generate_technology_coverage_heatmap(tech_stack: list, coverage: dict) -> str:
    """Generate technology coverage heatmap"""
    lines = ["```", "TECHNOLOGY COVERAGE HEATMAP", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
    
    for tech in tech_stack:
        cov = coverage.get(tech, 0)
        bar_full = int(cov * 20)  # 20 character width
        bar_empty = 20 - bar_full
        
        bar = "█" * bar_full + "░" * bar_empty
        
        if cov >= 0.8:
            status = "✅ EXCELLENT"
        elif cov >= 0.5:
            status = "⚠️  ADEQUATE"
        else:
            status = "❌ WEAK"
        
        lines.append(f"{tech:15} {bar} {cov*100:5.1f}% {status}")
    
    lines.append("")
    lines.append("Legend: █ = Covered  ░ = Gap  Threshold: 80% for ✅")
    lines.append("```")
    
    return "\n".join(lines)

def generate_risk_heatmap(risks: list) -> str:
    """Generate risk assessment heatmap"""
    risk_matrix = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }
    
    lines = ["```", "RISK ASSESSMENT HEATMAP", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
    lines.append("Impact →     LOW          MEDIUM        HIGH          CRITICAL")
    lines.append("           ┌─────────────┬─────────────┬─────────────┬─────────────┐")
    
    # Create 4x4 matrix
    likelihood_levels = ['HIGH', 'MEDIUM', 'LOW', 'MINIMAL']
    for likelihood in likelihood_levels:
        line_parts = [f"{likelihood:8} │"]
        for impact in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            # Find risks matching this cell
            matching = [r for r in risks if r.get('likelihood') == likelihood and r.get('impact') == impact]
            if matching:
                line_parts.append(f"  {risk_matrix.get(matching[0].get('severity', 'LOW'), '⚪')}  ({len(matching)})   │")
            else:
                line_parts.append("            │")
        lines.append("".join(line_parts))
    
    lines.append("           └─────────────┴─────────────┴─────────────┴─────────────┘")
    lines.append("")
    lines.append("Risk Count: 🔴 Critical  🟠 High  🟡 Medium  🟢 Low")
    lines.append("```")
    
    return "\n".join(lines)

def generate_skill_matrix_table(team_members: list, technologies: list) -> str:
    """Generate skill matrix visualization"""
    lines = ["```", "TEAM SKILL MATRIX", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
    
    # Header
    header = "Team Member          │ " + " │ ".join([f"{tech:10}" for tech in technologies])
    lines.append(header)
    lines.append("─" * len(header))
    
    # Skills legend
    skill_legend = {
        'expert': '●●●●●',
        'advanced': '●●●●○',
        'intermediate': '●●●○○',
        'beginner': '●●○○○',
        'none': '○○○○○'
    }
    
    for member in team_members:
        name = member.get('name', 'Unknown')[:20].ljust(20)
        skills_row = []
        
        for tech in technologies:
            # Simplified skill level (would come from member data)
            skills_row.append(f"{'●●●○○':10}")
        
        line = f"{name} │ " + " │ ".join(skills_row)
        lines.append(line)
    
    lines.append("")
    lines.append("Legend: ●●●●● Expert  ●●●●○ Advanced  ●●●○○ Intermediate  ●●○○○ Beginner  ○○○○○ None")
    lines.append("```")
    
    return "\n".join(lines)

def generate_timeline_gantt(phases: list) -> str:
    """Generate simplified Gantt chart timeline"""
    lines = ["```", "PROJECT TIMELINE (GANTT CHART)", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
    lines.append("Phase                Week 1    Week 2    Week 3    Week 4    Week 5    Week 6")
    lines.append("                     ────────────────────────────────────────────────────────")
    
    for phase in phases:
        name = phase.get('name', 'Unknown')[:20].ljust(20)
        start = phase.get('start_week', 1)
        duration = phase.get('duration_weeks', 1)
        
        # Create visual bar
        bar_parts = []
        for week in range(1, 7):
            if start <= week < start + duration:
                bar_parts.append("████████")
            elif week == start + duration:
                bar_parts.append("████░░░░")
            else:
                bar_parts.append("░░░░░░░░")
        
        lines.append(f"{name} {'  '.join(bar_parts)}")
    
    lines.append("")
    lines.append("Legend: ████ Active  ░░░░ Idle  Duration in weeks")
    lines.append("```")
    
    return "\n".join(lines)

def generate_data_flow_diagram() -> str:
    """Generate data flow diagram for ecosystem"""
    return """
```
DATA FLOW THROUGH ECOSYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input Sources                Datastores              Output
─────────────                ──────────              ──────

┌─────────────┐             ┌──────────┐
│ GitHub PRs  │────────────▶│Doc Store │
└─────────────┘             └────┬─────┘
                                 │
┌─────────────┐             ┌────▼─────┐            ┌──────────────┐
│ Jira Tickets│────────────▶│ Prompt   │───────────▶│   Planning   │
└─────────────┘             │  Store   │            │   Report     │
                            └────┬─────┘            └──────────────┘
┌─────────────┐             ┌────▼─────┐
│ Confluence  │────────────▶│ Memory   │            ┌──────────────┐
│    Docs     │             │  Agent   │───────────▶│  Validation  │
└─────────────┘             └────┬─────┘            │   Report     │
                                 │                  └──────────────┘
┌─────────────┐             ┌────▼─────┐
│   Service   │────────────▶│ External │            ┌──────────────┐
│    Docs     │             │ Service  │───────────▶│Architecture  │
└─────────────┘             │  Store   │            │   Report     │
                            └──────────┘            └──────────────┘

Flow: Ingest → Store → Analyze → Synthesize → Report
```
"""

def generate_collaboration_network(relationships: list) -> str:
    """Generate collaboration network diagram"""
    if not relationships:
        return "```\nNo collaboration relationships found\n```"
    
    lines = ["```", "COLLABORATION NETWORK", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
    
    # Show top relationships
    for rel in relationships[:10]:
        user1 = rel.get('user1', 'User A')[:15]
        user2 = rel.get('user2', 'User B')[:15]
        strength = rel.get('strength', 0)
        
        # Visual strength indicator
        if strength >= 5:
            connector = "═══════"
            label = "STRONG"
        elif strength >= 3:
            connector = "───────"
            label = "MEDIUM"
        else:
            connector = "┈┈┈┈┈┈┈"
            label = "WEAK"
        
        lines.append(f"{user1:15} {connector} {user2:15} ({strength} docs, {label})")
    
    lines.append("")
    lines.append("Legend: ═══ Strong (5+ docs)  ─── Medium (3-4 docs)  ┈┈┈ Weak (1-2 docs)")
    lines.append("```")
    
    return "\n".join(lines)

def generate_effort_distribution_chart(phases: list) -> str:
    """Generate effort distribution visualization"""
    total_effort = sum(p.get('effort_hours', 0) for p in phases)
    
    lines = ["```", "EFFORT DISTRIBUTION BY PHASE", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
    
    for phase in phases:
        name = phase.get('name', 'Unknown')[:20].ljust(20)
        effort = phase.get('effort_hours', 0)
        percentage = (effort / total_effort * 100) if total_effort > 0 else 0
        
        # Create bar (40 chars wide)
        bar_length = int(percentage * 0.4)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        
        lines.append(f"{name} {bar} {percentage:5.1f}% ({effort}h)")
    
    lines.append("")
    lines.append(f"Total Effort: {total_effort} hours")
    lines.append("```")
    
    return "\n".join(lines)

def generate_dependency_matrix(services: list) -> str:
    """Generate service dependency matrix"""
    if len(services) > 10:
        services = services[:10]  # Limit for readability
    
    lines = ["```", "SERVICE DEPENDENCY MATRIX", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", ""]
    
    # Header
    header = "Service          │ " + " ".join([f"{s.get('name', 'S')[:3]:3}" for s in services])
    lines.append(header)
    lines.append("─" * len(header))
    
    # Matrix rows
    for service in services:
        name = service.get('name', 'Unknown')[:16].ljust(16)
        deps = []
        for other in services:
            # Simplified - would check actual dependencies
            deps.append(" ● " if other != service else " - ")
        
        lines.append(f"{name} │ " + "".join(deps))
    
    lines.append("")
    lines.append("Legend: ● = Depends on  - = Self  (Read row → column)")
    lines.append("```")
    
    return "\n".join(lines)

