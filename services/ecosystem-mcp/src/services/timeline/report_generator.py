"""
Report Generator (Phase 5)

Generates comprehensive reports with source citations:
- Progression reports (work over time)
- Gap reports (what's missing)
- Drift reports (what changed)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Report types."""
    PROGRESSION = "progression"
    GAP = "gap"
    DRIFT = "drift"


class ReportFormat(Enum):
    """Report output formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class ReportGenerator:
    """
    Generates comprehensive reports with source citations.
    
    Features:
    - Timeline-based progression analysis
    - Gap identification with recommendations
    - Drift detection with severity
    - Source citations for all findings
    """
    
    def __init__(self):
        logger.info("ReportGenerator initialized")
    
    async def generate_progression_report(
        self,
        timeline_id: str,
        service_name: Optional[str] = None,
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> Dict:
        """
        Generate progression report showing documentation evolution over time.
        
        Args:
            timeline_id: Timeline to analyze
            service_name: Optional service filter
            format: Output format
        
        Returns:
            Report dictionary with content and metadata
        """
        logger.info(f"Generating progression report for timeline {timeline_id}")
        
        try:
            # Fetch timeline data
            timeline_data = await self._fetch_timeline_data(timeline_id)
            
            if not timeline_data:
                return self._generate_empty_report("progression", "Timeline not found")
            
            # Analyze progression
            progression_analysis = await self._analyze_progression(
                timeline_data, service_name
            )
            
            # Generate report content
            content = await self._format_progression_report(
                timeline_data, progression_analysis, format
            )
            
            return {
                'type': 'progression',
                'timeline_id': timeline_id,
                'service_name': service_name,
                'format': format.value,
                'content': content,
                'generated_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'timeline_name': timeline_data.get('timeline_name'),
                    'period_count': len(timeline_data.get('periods', [])),
                    'period_strategy': timeline_data.get('period_strategy'),
                    'total_documents': progression_analysis.get('total_documents', 0)
                }
            }
        except Exception as e:
            logger.error(f"Error generating progression report: {e}")
            raise
    
    async def generate_gap_report(
        self,
        service_name: str,
        include_root_cause: bool = False,
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> Dict:
        """
        Generate gap report identifying missing documentation.
        
        Args:
            service_name: Service to analyze
            include_root_cause: Include root cause analysis
            format: Output format
        
        Returns:
            Report dictionary with content and metadata
        """
        logger.info(f"Generating gap report for service {service_name}")
        
        try:
            # Import gap analyzer
            from .gap_analyzer import GapAnalyzer
            
            analyzer = GapAnalyzer()
            
            # Analyze gaps
            gaps_result = await analyzer.analyze_gaps(
                service_name=service_name,
                include_root_cause=include_root_cause
            )
            
            # Generate report content
            content = await self._format_gap_report(
                service_name, gaps_result, format
            )
            
            return {
                'type': 'gap',
                'service_name': service_name,
                'format': format.value,
                'content': content,
                'generated_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'total_gaps': gaps_result.get('total_gaps', 0),
                    'critical_gaps': len([g for g in gaps_result.get('gaps', []) 
                                         if g.get('severity') == 'CRITICAL']),
                    'high_gaps': len([g for g in gaps_result.get('gaps', []) 
                                     if g.get('severity') == 'HIGH']),
                    'include_root_cause': include_root_cause
                }
            }
        except Exception as e:
            logger.error(f"Error generating gap report: {e}")
            raise
    
    async def generate_drift_report(
        self,
        service_name: str,
        detection_mode: str = "hybrid",
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> Dict:
        """
        Generate drift report showing code-documentation divergence.
        
        Args:
            service_name: Service to analyze
            detection_mode: Detection mode (hybrid/git/content)
            format: Output format
        
        Returns:
            Report dictionary with content and metadata
        """
        logger.info(f"Generating drift report for service {service_name}")
        
        try:
            # Import drift detector
            from .drift_detector import DriftDetector
            
            detector = DriftDetector()
            
            # Detect drift
            drift_result = await detector.detect_drift(
                service_name=service_name,
                detection_mode=detection_mode
            )
            
            # Generate report content
            content = await self._format_drift_report(
                service_name, drift_result, format
            )
            
            return {
                'type': 'drift',
                'service_name': service_name,
                'format': format.value,
                'content': content,
                'generated_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'total_drifts': drift_result.get('total_drifts', 0),
                    'critical_drifts': len([d for d in drift_result.get('drifts', []) 
                                          if d.get('severity') == 'CRITICAL']),
                    'high_drifts': len([d for d in drift_result.get('drifts', []) 
                                      if d.get('severity') == 'HIGH']),
                    'detection_mode': detection_mode,
                    'confidence': drift_result.get('confidence')
                }
            }
        except Exception as e:
            logger.error(f"Error generating drift report: {e}")
            raise
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    async def _fetch_timeline_data(self, timeline_id: str) -> Optional[Dict]:
        """Fetch timeline data from repository."""
        try:
            from ...storage.repositories import TimelineRepository, TimePeriodRepository
            from ...storage import get_database
            from uuid import UUID
            
            db = get_database()
            async with db.session() as session:
                timeline_repo = TimelineRepository(session)
                period_repo = TimePeriodRepository(session)
                
                timeline = await timeline_repo.get_by_id(UUID(timeline_id) if isinstance(timeline_id, str) else timeline_id)
                
                if not timeline:
                    return None
                
                # Get periods
                periods = await period_repo.get_by_timeline(timeline.id)
                
                # Build timeline data
                return {
                    'timeline_id': str(timeline.id),
                    'timeline_name': timeline.name,
                    'service_name': timeline.service_name,
                    'start_date': timeline.start_date,
                    'end_date': timeline.end_date,
                    'period_strategy': timeline.period_strategy,
                    'periods': [
                        {
                            'id': str(p.id),
                            'name': p.name,
                            'start_date': p.start_date,
                            'end_date': p.end_date,
                            'document_count': p.document_count
                        }
                        for p in periods
                    ]
                }
        except Exception as e:
            logger.error(f"Error fetching timeline data: {e}")
            return None
    
    async def _analyze_progression(
        self,
        timeline_data: Dict,
        service_name: Optional[str]
    ) -> Dict:
        """Analyze documentation progression over time."""
        periods = timeline_data.get('periods', [])
        
        # Calculate metrics
        total_documents = sum(p['document_count'] for p in periods)
        avg_documents_per_period = total_documents / len(periods) if periods else 0
        
        # Identify growth periods
        growth_periods = []
        for i, period in enumerate(periods):
            if i > 0:
                prev_count = periods[i-1]['document_count']
                curr_count = period['document_count']
                growth = curr_count - prev_count
                if growth > 0:
                    growth_periods.append({
                        'period': period['name'],
                        'growth': growth,
                        'percentage': (growth / prev_count * 100) if prev_count > 0 else 0
                    })
        
        return {
            'total_documents': total_documents,
            'avg_documents_per_period': avg_documents_per_period,
            'growth_periods': growth_periods,
            'period_count': len(periods)
        }
    
    async def _format_progression_report(
        self,
        timeline_data: Dict,
        analysis: Dict,
        format: ReportFormat
    ) -> str:
        """Format progression report."""
        if format == ReportFormat.MARKDOWN:
            return self._format_progression_markdown(timeline_data, analysis)
        elif format == ReportFormat.JSON:
            return self._format_progression_json(timeline_data, analysis)
        else:  # HTML
            return self._format_progression_html(timeline_data, analysis)
    
    def _format_progression_markdown(
        self,
        timeline_data: Dict,
        analysis: Dict
    ) -> str:
        """Format progression report as Markdown."""
        timeline_name = timeline_data.get('timeline_name', 'Unknown')
        confidence = timeline_data.get('confidence', 'UNKNOWN')
        periods = timeline_data.get('periods', [])
        
        # Build period table
        period_rows = []
        for period in periods:
            period_rows.append(
                f"| {period['name']} | {period['start_date']} | "
                f"{period['end_date']} | {period['document_count']} |"
            )
        
        period_table = '\n'.join(period_rows) if period_rows else "*No periods available*"
        
        # Build growth section
        growth_periods = analysis.get('growth_periods', [])
        growth_text = []
        for gp in growth_periods:
            growth_text.append(
                f"- **{gp['period']}**: +{gp['growth']} documents "
                f"({gp['percentage']:.1f}% growth)"
            )
        
        growth_section = '\n'.join(growth_text) if growth_text else "*No significant growth detected*"
        
        content = f"""# Documentation Progression Report

## Timeline Overview

**Timeline:** {timeline_name}  
**Confidence:** {confidence}  
**Total Periods:** {len(periods)}  
**Total Documents:** {analysis.get('total_documents', 0)}  
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Progression Metrics

- **Total Documents:** {analysis.get('total_documents', 0)}
- **Average per Period:** {analysis.get('avg_documents_per_period', 0):.2f}
- **Growth Periods:** {len(growth_periods)}

## Period Breakdown

| Period | Start Date | End Date | Documents |
|--------|------------|----------|-----------|
{period_table}

## Growth Analysis

{growth_section}

## Key Insights

### Documentation Velocity

The documentation has {"grown steadily" if len(growth_periods) > len(periods) // 2 else "shown variable growth"} across the timeline.

**Trend:** {"📈 Increasing" if growth_periods and growth_periods[-1]['growth'] > 0 else "📊 Stable"}

### Coverage Progress

- **Early Periods:** {periods[0]['document_count'] if periods else 0} documents
- **Recent Periods:** {periods[-1]['document_count'] if periods else 0} documents
- **Growth Rate:** {((periods[-1]['document_count'] / periods[0]['document_count'] - 1) * 100) if periods and periods[0]['document_count'] > 0 else 0:.1f}%

## Recommendations

{self._generate_progression_recommendations(analysis)}

---
*Generated by Ecosystem MCP - Report Generator*  
*Timeline: {timeline_name} | Confidence: {confidence}*
"""
        
        return content
    
    def _format_progression_json(
        self,
        timeline_data: Dict,
        analysis: Dict
    ) -> str:
        """Format progression report as JSON."""
        import json
        
        return json.dumps({
            'timeline': timeline_data,
            'analysis': analysis,
            'generated_at': datetime.utcnow().isoformat()
        }, indent=2)
    
    def _format_progression_html(
        self,
        timeline_data: Dict,
        analysis: Dict
    ) -> str:
        """Format progression report as HTML."""
        # Convert Markdown to HTML (simplified)
        markdown_content = self._format_progression_markdown(timeline_data, analysis)
        
        # Wrap in HTML
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Documentation Progression Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <pre>{markdown_content}</pre>
</body>
</html>"""
    
    async def _format_gap_report(
        self,
        service_name: str,
        gaps_result: Dict,
        format: ReportFormat
    ) -> str:
        """Format gap report."""
        if format == ReportFormat.MARKDOWN:
            return self._format_gap_markdown(service_name, gaps_result)
        elif format == ReportFormat.JSON:
            import json
            return json.dumps(gaps_result, indent=2)
        else:  # HTML
            return self._format_gap_html(service_name, gaps_result)
    
    def _format_gap_markdown(
        self,
        service_name: str,
        gaps_result: Dict
    ) -> str:
        """Format gap report as Markdown."""
        gaps = gaps_result.get('gaps', [])
        total_gaps = gaps_result.get('total_gaps', 0)
        
        # Group by severity
        severity_groups = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for gap in gaps:
            severity = gap.get('severity', 'LOW')
            severity_groups[severity].append(gap)
        
        # Build severity sections
        sections = []
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            gaps_list = severity_groups[severity]
            if gaps_list:
                sections.append(f"\n### {severity} Priority ({len(gaps_list)} gaps)\n")
                for gap in gaps_list:
                    sections.append(f"""
**{gap.get('type', 'Unknown')}**
- **Description:** {gap.get('description', 'N/A')}
- **Affected:** {gap.get('affected_area', 'N/A')}
- **Recommendation:** {gap.get('recommendation', 'N/A')}
""")
        
        content = f"""# Documentation Gap Report

## Service Overview

**Service:** {service_name}  
**Total Gaps:** {total_gaps}  
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Gap Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {len(severity_groups['CRITICAL'])} |
| 🟠 High | {len(severity_groups['HIGH'])} |
| 🟡 Medium | {len(severity_groups['MEDIUM'])} |
| 🟢 Low | {len(severity_groups['LOW'])} |

## Detailed Gaps

{''.join(sections) if sections else '*No gaps detected*'}

## Recommendations

{self._generate_gap_recommendations(gaps_result)}

---
*Generated by Ecosystem MCP - Report Generator*  
*Service: {service_name}*
"""
        
        return content
    
    def _format_gap_html(
        self,
        service_name: str,
        gaps_result: Dict
    ) -> str:
        """Format gap report as HTML."""
        markdown_content = self._format_gap_markdown(service_name, gaps_result)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Documentation Gap Report - {service_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .critical {{ color: #d32f2f; }}
        .high {{ color: #f57c00; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
    </style>
</head>
<body>
    <pre>{markdown_content}</pre>
</body>
</html>"""
    
    async def _format_drift_report(
        self,
        service_name: str,
        drift_result: Dict,
        format: ReportFormat
    ) -> str:
        """Format drift report."""
        if format == ReportFormat.MARKDOWN:
            return self._format_drift_markdown(service_name, drift_result)
        elif format == ReportFormat.JSON:
            import json
            return json.dumps(drift_result, indent=2)
        else:  # HTML
            return self._format_drift_html(service_name, drift_result)
    
    def _format_drift_markdown(
        self,
        service_name: str,
        drift_result: Dict
    ) -> str:
        """Format drift report as Markdown."""
        drifts = drift_result.get('drifts', [])
        total_drifts = drift_result.get('total_drifts', 0)
        confidence = drift_result.get('confidence', 'UNKNOWN')
        
        # Group by severity
        severity_groups = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for drift in drifts:
            severity = drift.get('severity', 'LOW')
            severity_groups[severity].append(drift)
        
        # Build severity sections
        sections = []
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            drifts_list = severity_groups[severity]
            if drifts_list:
                sections.append(f"\n### {severity} Priority ({len(drifts_list)} drifts)\n")
                for drift in drifts_list:
                    sections.append(f"""
**{drift.get('file_path', 'Unknown')}**
- **Description:** {drift.get('description', 'N/A')}
- **Drift Days:** {drift.get('drift_days', 0)}
- **Detection Method:** {drift.get('detection_method', 'N/A')}
- **Recommendation:** {drift.get('recommendation', 'N/A')}
""")
        
        content = f"""# Code-Documentation Drift Report

## Service Overview

**Service:** {service_name}  
**Total Drifts:** {total_drifts}  
**Confidence:** {confidence}  
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Drift Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {len(severity_groups['CRITICAL'])} |
| 🟠 High | {len(severity_groups['HIGH'])} |
| 🟡 Medium | {len(severity_groups['MEDIUM'])} |
| 🟢 Low | {len(severity_groups['LOW'])} |

## Detailed Drifts

{''.join(sections) if sections else '*No drifts detected*'}

## Recommendations

{self._generate_drift_recommendations(drift_result)}

---
*Generated by Ecosystem MCP - Report Generator*  
*Service: {service_name} | Confidence: {confidence}*
"""
        
        return content
    
    def _format_drift_html(
        self,
        service_name: str,
        drift_result: Dict
    ) -> str:
        """Format drift report as HTML."""
        markdown_content = self._format_drift_markdown(service_name, drift_result)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Drift Report - {service_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <pre>{markdown_content}</pre>
</body>
</html>"""
    
    def _generate_empty_report(self, report_type: str, reason: str) -> Dict:
        """Generate empty report."""
        return {
            'type': report_type,
            'content': f"# {report_type.title()} Report\n\n*{reason}*",
            'generated_at': datetime.utcnow().isoformat(),
            'metadata': {}
        }
    
    def _generate_progression_recommendations(self, analysis: Dict) -> str:
        """Generate recommendations for progression report."""
        total_docs = analysis.get('total_documents', 0)
        growth_periods = analysis.get('growth_periods', [])
        
        recs = []
        
        if total_docs < 10:
            recs.append("- **Low Coverage**: Increase documentation efforts")
        
        if len(growth_periods) < 2:
            recs.append("- **Stagnant Growth**: Establish regular documentation cadence")
        
        if total_docs > 50:
            recs.append("- **Good Coverage**: Maintain documentation quality")
        
        return '\n'.join(recs) if recs else "- Continue current documentation practices"
    
    def _generate_gap_recommendations(self, gaps_result: Dict) -> str:
        """Generate recommendations for gap report."""
        critical_count = len([g for g in gaps_result.get('gaps', []) 
                             if g.get('severity') == 'CRITICAL'])
        
        recs = []
        
        if critical_count > 0:
            recs.append(f"- **Urgent**: Address {critical_count} critical gaps immediately")
        
        recs.append("- Prioritize documentation by severity")
        recs.append("- Review root causes to prevent future gaps")
        
        return '\n'.join(recs)
    
    def _generate_drift_recommendations(self, drift_result: Dict) -> str:
        """Generate recommendations for drift report."""
        critical_count = len([d for d in drift_result.get('drifts', []) 
                             if d.get('severity') == 'CRITICAL'])
        
        recs = []
        
        if critical_count > 0:
            recs.append(f"- **Urgent**: Update {critical_count} critical drifted documents")
        
        recs.append("- Establish automated drift detection")
        recs.append("- Review documentation update process")
        
        return '\n'.join(recs)

