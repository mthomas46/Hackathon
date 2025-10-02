#!/usr/bin/env python3
"""
Ecosystem Audit Runner

Comprehensive audit testing tool for the entire LLM Documentation Ecosystem.
Runs all audit tests against the complete ecosystem and provides detailed analysis,
reporting, and recommendations.

Usage:
    # Run full ecosystem audit
    python scripts/test/ecosystem_audit_runner.py

    # Run with specific focus areas
    python scripts/test/ecosystem_audit_runner.py --focus docker infrastructure

    # Generate comprehensive report
    python scripts/test/ecosystem_audit_runner.py --report ecosystem_audit_2024.json

    # Run against staging environment
    python scripts/test/ecosystem_audit_runner.py --env staging

    # Continuous monitoring mode
    python scripts/test/ecosystem_audit_runner.py --continuous --interval 300

    # CI/CD mode (non-interactive)
    python scripts/test/ecosystem_audit_runner.py --ci
"""

import argparse
import asyncio
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import requests
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
import logging
import schedule

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class EcosystemAuditResult:
    """Complete ecosystem audit results"""
    timestamp: str
    environment: str
    duration: float

    # Infrastructure metrics
    infrastructure_health: Dict[str, Any] = field(default_factory=dict)

    # Service metrics
    services_tested: int = 0
    services_healthy: int = 0
    services_degraded: int = 0
    services_failed: int = 0

    # Audit results
    docker_compose_audit: Dict[str, Any] = field(default_factory=dict)
    config_drift_audit: Dict[str, Any] = field(default_factory=dict)
    production_readiness_audit: Dict[str, Any] = field(default_factory=dict)
    config_standardization_audit: Dict[str, Any] = field(default_factory=dict)
    docker_standardization_audit: Dict[str, Any] = field(default_factory=dict)

    # Individual service results
    service_results: List[Dict[str, Any]] = field(default_factory=list)

    # Overall assessment
    overall_score: float = 0.0
    readiness_level: str = "unknown"
    critical_issues: int = 0
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


class EcosystemAuditRunner:
    """
    Comprehensive ecosystem audit runner.

    Features:
    - Full ecosystem testing
    - Infrastructure validation
    - Service health assessment
    - Continuous monitoring
    - Detailed reporting
    - CI/CD integration
    """

    def __init__(self, base_url: str = "http://localhost:8080", environment: str = "development"):
        self.base_url = base_url
        self.environment = environment
        self.session = requests.Session()
        self.session.timeout = 30

        # Define ecosystem components
        self.core_services = {
            'orchestrator', 'doc_store', 'analysis-service', 'source-agent',
            'frontend', 'memory-agent', 'discovery-agent', 'prompt_store',
            'interpreter', 'cli', 'user-store'
        }

        self.infrastructure = {
            'redis', 'log-collector'
        }

        self.integrations = {
            'llm-gateway', 'summarizer-hub', 'github-mcp', 'bedrock-proxy',
            'secure-analyzer', 'code-analyzer', 'architecture-digitizer',
            'project-simulation', 'mock-data-generator', 'simulation-dashboard',
            'unified-api-dashboard'
        }

        self.all_services = self.core_services | self.infrastructure | self.integrations

    def run_full_audit(self, focus_areas: Optional[List[str]] = None) -> EcosystemAuditResult:
        """
        Run comprehensive ecosystem audit.

        Args:
            focus_areas: Optional list of areas to focus on

        Returns:
            Complete audit results
        """
        start_time = time.time()
        result = EcosystemAuditResult(
            timestamp=datetime.now().isoformat(),
            environment=self.environment,
            duration=0
        )

        logger.info(f"🔍 Starting full ecosystem audit for {self.environment} environment")

        try:
            # Infrastructure health check
            if not focus_areas or 'infrastructure' in focus_areas:
                result.infrastructure_health = self._check_infrastructure_health()
                logger.info("✅ Infrastructure health check completed")

            # Run audit tests
            if not focus_areas or 'docker' in focus_areas:
                result.docker_compose_audit = self._run_docker_compose_audit()
                logger.info("✅ Docker Compose audit completed")

            if not focus_areas or 'config' in focus_areas:
                result.config_drift_audit = self._run_config_drift_audit()
                result.config_standardization_audit = self._run_config_standardization_audit()
                logger.info("✅ Configuration audits completed")

            if not focus_areas or 'readiness' in focus_areas:
                result.production_readiness_audit = self._run_production_readiness_audit()
                logger.info("✅ Production readiness audit completed")

            if not focus_areas or 'docker' in focus_areas:
                result.docker_standardization_audit = self._run_docker_standardization_audit()
                logger.info("✅ Docker standardization audit completed")

            # Individual service testing
            result.service_results = self._run_service_tests()
            result.services_tested = len(result.service_results)

            # Calculate service health metrics
            self._calculate_service_health_metrics(result)

            # Overall assessment
            self._calculate_overall_assessment(result)

            # Generate recommendations
            result.recommendations, result.next_steps = self._generate_recommendations(result)

        except Exception as e:
            logger.error(f"❌ Ecosystem audit failed: {e}")
            result.critical_issues += 1
            result.recommendations.append(f"Critical audit failure: {str(e)}")

        result.duration = time.time() - start_time
        return result

    def run_continuous_monitoring(self, interval_minutes: int = 60):
        """Run continuous ecosystem monitoring"""
        logger.info(f"🔄 Starting continuous ecosystem monitoring (interval: {interval_minutes} minutes)")

        def run_monitoring_cycle():
            try:
                result = self.run_full_audit()
                self._log_monitoring_results(result)

                # Alert on critical issues
                if result.critical_issues > 0:
                    self._send_alert(f"Critical issues detected: {result.critical_issues}")

                # Save periodic report
                report_file = f"monitoring_report_{int(time.time())}.json"
                self.save_report(result, report_file)

            except Exception as e:
                logger.error(f"Monitoring cycle failed: {e}")
                self._send_alert(f"Monitoring cycle failed: {str(e)}")

        # Schedule monitoring
        schedule.every(interval_minutes).minutes.do(run_monitoring_cycle)

        # Run initial cycle
        run_monitoring_cycle()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("🛑 Continuous monitoring stopped by user")

    def _check_infrastructure_health(self) -> Dict[str, Any]:
        """Check infrastructure health"""
        health_status = {
            'docker_daemon': False,
            'containers_running': 0,
            'containers_healthy': 0,
            'networks': 0,
            'volumes': 0
        }

        try:
            # Check Docker daemon
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
            health_status['docker_daemon'] = result.returncode == 0

            # Get container status
            result = subprocess.run(['docker', 'ps', '--format', 'json'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line.strip()]
                health_status['containers_running'] = len(containers)

                # Check health status (simplified)
                health_status['containers_healthy'] = len([c for c in containers if c.get('State') == 'running'])

            # Get network info
            result = subprocess.run(['docker', 'network', 'ls', '--format', 'json'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                networks = [json.loads(line) for line in result.stdout.strip().split('\n') if line.strip()]
                health_status['networks'] = len(networks)

            # Get volume info
            result = subprocess.run(['docker', 'volume', 'ls', '--format', 'json'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                volumes = [json.loads(line) for line in result.stdout.strip().split('\n') if line.strip()]
                health_status['volumes'] = len(volumes)

        except Exception as e:
            logger.warning(f"Infrastructure health check failed: {e}")

        return health_status

    def _run_docker_compose_audit(self) -> Dict[str, Any]:
        """Run Docker Compose audit"""
        try:
            url = f"{self.base_url}/api/v1/audit/docker-compose/validate"
            response = self.session.post(url)

            if response.status_code == 200:
                return response.json().get('docker_compose_validation', {})
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_config_drift_audit(self) -> Dict[str, Any]:
        """Run configuration drift audit"""
        try:
            url = f"{self.base_url}/api/v1/audit/config/drift-detect"
            response = self.session.post(url, params={'dev_only': 'false'})

            if response.status_code == 200:
                return response.json().get('configuration_drift', {})
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_production_readiness_audit(self) -> Dict[str, Any]:
        """Run production readiness audit"""
        try:
            url = f"{self.base_url}/api/v1/audit/production-readiness/validate"
            response = self.session.post(url, params={'target_level': 'production_ready'})

            if response.status_code == 200:
                return response.json().get('production_readiness', {})
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_config_standardization_audit(self) -> Dict[str, Any]:
        """Run configuration standardization audit"""
        try:
            url = f"{self.base_url}/api/v1/audit/config/standardize/all"
            response = self.session.post(url)

            if response.status_code == 200:
                return response.json().get('config_standardization', {})
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_docker_standardization_audit(self) -> Dict[str, Any]:
        """Run Docker standardization audit"""
        try:
            url = f"{self.base_url}/api/v1/audit/docker/standardize"
            response = self.session.post(url)

            if response.status_code == 200:
                return response.json().get('docker_standardization', {})
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _run_service_tests(self, max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """Run tests against individual services"""
        service_results = []

        # Test core services first (they're most critical)
        test_order = list(self.core_services) + list(self.infrastructure) + list(self.integrations)

        for service_name in test_order[:10]:  # Limit to first 10 for performance
            try:
                # Test service-specific config standardization
                url = f"{self.base_url}/api/v1/audit/config/standardize/service/{service_name}"
                response = self.session.post(url, timeout=15)

                if response.status_code == 200:
                    result = response.json().get('config_standardization', {})
                    result['service_name'] = service_name
                    service_results.append(result)
                else:
                    service_results.append({
                        'service_name': service_name,
                        'success': False,
                        'error': f'HTTP {response.status_code}'
                    })

            except Exception as e:
                service_results.append({
                    'service_name': service_name,
                    'success': False,
                    'error': str(e)
                })

        return service_results

    def _calculate_service_health_metrics(self, result: EcosystemAuditResult):
        """Calculate service health metrics"""
        healthy_services = []
        degraded_services = []
        failed_services = []

        for service_result in result.service_results:
            service_name = service_result.get('service_name', 'unknown')
            success = service_result.get('success', False)

            if success:
                # Check for warnings/issues
                issues = service_result.get('issues', [])
                if any(issue.get('severity') in ['high', 'error'] for issue in issues):
                    degraded_services.append(service_name)
                else:
                    healthy_services.append(service_name)
            else:
                failed_services.append(service_name)

        result.services_healthy = len(healthy_services)
        result.services_degraded = len(degraded_services)
        result.services_failed = len(failed_services)

    def _calculate_overall_assessment(self, result: EcosystemAuditResult):
        """Calculate overall ecosystem assessment"""
        # Calculate overall score based on various factors
        scores = []

        # Infrastructure health (40% weight)
        infra_score = 0
        if result.infrastructure_health:
            infra_metrics = result.infrastructure_health
            if infra_metrics.get('docker_daemon'):
                infra_score += 0.3
            if infra_metrics.get('containers_running', 0) > 0:
                infra_score += 0.4
            if infra_metrics.get('containers_healthy', 0) > 0:
                infra_score += 0.3
        scores.append(infra_score * 0.4)

        # Audit success rates (60% weight)
        audit_scores = []
        for audit_result in [result.docker_compose_audit, result.config_drift_audit,
                           result.production_readiness_audit, result.config_standardization_audit,
                           result.docker_standardization_audit]:
            if audit_result and audit_result.get('success'):
                audit_scores.append(1.0)
            else:
                audit_scores.append(0.0)

        if audit_scores:
            audit_avg = sum(audit_scores) / len(audit_scores)
            scores.append(audit_avg * 0.6)

        result.overall_score = sum(scores) / len(scores) if scores else 0

        # Determine readiness level
        if result.overall_score >= 0.9 and result.critical_issues == 0:
            result.readiness_level = "production_ready"
        elif result.overall_score >= 0.7:
            result.readiness_level = "development_ready"
        elif result.overall_score >= 0.5:
            result.readiness_level = "testing_ready"
        else:
            result.readiness_level = "not_ready"

        # Count critical issues
        result.critical_issues = (
            result.services_failed +
            (1 if not result.infrastructure_health.get('docker_daemon', False) else 0) +
            sum(1 for audit in [result.docker_compose_audit, result.production_readiness_audit]
                if not audit.get('success', False))
        )

    def _generate_recommendations(self, result: EcosystemAuditResult) -> Tuple[List[str], List[str]]:
        """Generate recommendations and next steps"""
        recommendations = []
        next_steps = []

        # Infrastructure recommendations
        if not result.infrastructure_health.get('docker_daemon', False):
            recommendations.append("Ensure Docker daemon is running and accessible")
            next_steps.append("Start Docker service and verify connectivity")

        if result.services_failed > 0:
            recommendations.append(f"Address {result.services_failed} failed services")
            next_steps.append("Check service logs and restart failed services")

        # Audit-specific recommendations
        if not result.docker_compose_audit.get('success', False):
            recommendations.append("Fix Docker Compose configuration issues")
            next_steps.append("Review docker-compose.yml for validation errors")

        if result.config_drift_audit.get('total_issues', 0) > 0:
            recommendations.append(f"Resolve {result.config_drift_audit.get('total_issues')} configuration drift issues")
            next_steps.append("Sync configurations between files and runtime")

        if result.readiness_level != "production_ready":
            recommendations.append(f"Improve readiness level from {result.readiness_level}")
            next_steps.append("Address critical issues and improve scores")

        # Default recommendations if everything looks good
        if not recommendations:
            recommendations.append("Ecosystem is in good health")
            next_steps.append("Continue regular monitoring and maintenance")

        return recommendations, next_steps

    def _log_monitoring_results(self, result: EcosystemAuditResult):
        """Log monitoring cycle results"""
        status_icon = "✅" if result.overall_score >= 0.8 else "⚠️" if result.overall_score >= 0.5 else "❌"

        logger.info(f"{status_icon} Ecosystem Health Check: {result.overall_score:.2f} ({result.readiness_level})")
        logger.info(f"   Services: {result.services_healthy} healthy, {result.services_degraded} degraded, {result.services_failed} failed")
        logger.info(f"   Critical Issues: {result.critical_issues}")

    def _send_alert(self, message: str):
        """Send alert notification (placeholder for actual alerting system)"""
        logger.warning(f"🚨 ALERT: {message}")
        # In a real system, this would integrate with Slack, email, PagerDuty, etc.

    def print_audit_results(self, result: EcosystemAuditResult, verbose: bool = False):
        """Print comprehensive audit results"""
        print("\n" + "="*80)
        print("🌐 ECOSYSTEM AUDIT RESULTS")
        print("="*80)

        print(f"📊 Summary:")
        print(f"   Environment: {result.environment}")
        print(f"   Timestamp: {result.timestamp}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Overall Score: {result.overall_score:.2f}")
        print(f"   Readiness Level: {result.readiness_level}")
        print(f"   Critical Issues: {result.critical_issues}")

        print(f"\n🏥 Infrastructure Health:")
        infra = result.infrastructure_health
        docker_status = "✅ Running" if infra.get('docker_daemon') else "❌ Not running"
        print(f"   Docker Daemon: {docker_status}")
        print(f"   Containers: {infra.get('containers_running', 0)} running, {infra.get('containers_healthy', 0)} healthy")
        print(f"   Networks: {infra.get('networks', 0)}")
        print(f"   Volumes: {infra.get('volumes', 0)}")

        print(f"\n🔧 Service Health:")
        print(f"   Services Tested: {result.services_tested}")
        print(f"   Healthy: {result.services_healthy}")
        print(f"   Degraded: {result.services_degraded}")
        print(f"   Failed: {result.services_failed}")

        print(f"\n📋 Audit Results:")
        audits = [
            ("Docker Compose", result.docker_compose_audit),
            ("Config Drift", result.config_drift_audit),
            ("Production Readiness", result.production_readiness_audit),
            ("Config Standardization", result.config_standardization_audit),
            ("Docker Standardization", result.docker_standardization_audit)
        ]

        for name, audit_result in audits:
            if audit_result:
                success = audit_result.get('success', False)
                status_icon = "✅" if success else "❌"
                details = self._get_audit_details(audit_result)
                print(f"   {status_icon} {name}: {details}")
            else:
                print(f"   ⚪ {name}: Not run")

        if verbose and result.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"   • {rec}")

        if verbose and result.next_steps:
            print(f"\n🎯 Next Steps:")
            for step in result.next_steps:
                print(f"   • {step}")

        print("\n" + "="*80)

    def _get_audit_details(self, audit_result: Dict[str, Any]) -> str:
        """Get human-readable audit result details"""
        if not audit_result.get('success', False):
            return "Failed"

        details = []

        # Docker Compose
        if 'services_count' in audit_result:
            services = audit_result['services_count']
            issues = len(audit_result.get('issues', []))
            conflicts = audit_result.get('port_conflicts', 0)
            details.append(f"{services} services, {issues} issues, {conflicts} conflicts")

        # Config Drift
        if 'total_issues' in audit_result:
            issues = audit_result['total_issues']
            files = audit_result.get('scanned_files', 0)
            details.append(f"{issues} issues, {files} files scanned")

        # Production Readiness
        if 'overall_readiness' in audit_result:
            readiness = audit_result['overall_readiness']
            score = audit_result.get('overall_score', 0)
            details.append(f"{readiness} ({score:.2f})")

        # Config Standardization
        if 'services_processed' in audit_result:
            processed = audit_result['services_processed']
            standardized = audit_result.get('services_standardized', 0)
            details.append(f"{processed} processed, {standardized} standardized")

        # Docker Standardization
        if 'files_processed' in audit_result:
            processed = audit_result['files_processed']
            modified = audit_result.get('files_modified', 0)
            details.append(f"{processed} files, {modified} modified")

        return ", ".join(details) if details else "Completed"

    def save_report(self, result: EcosystemAuditResult, output_file: str):
        """Save comprehensive audit report"""
        # Convert dataclass to dict
        report_data = asdict(result)

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"📄 Comprehensive audit report saved to: {output_file}")


def check_service_availability(base_url: str) -> bool:
    """Check if the meta-orchestrator service is available"""
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        return response.status_code == 200
    except:
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Ecosystem Audit Runner")
    parser.add_argument('--focus', nargs='*',
                       choices=['infrastructure', 'docker', 'config', 'readiness'],
                       help='Focus on specific audit areas')
    parser.add_argument('--env', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--report', '-r', help='Save comprehensive JSON report')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in minutes')
    parser.add_argument('--ci', action='store_true', help='CI/CD mode (exit codes based on results)')
    parser.add_argument('--url', default='http://localhost:8080', help='Meta-orchestrator base URL')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Check service availability
    if not check_service_availability(args.url):
        print(f"❌ Meta-orchestrator service not available at {args.url}")
        print("   Make sure the service is running with: docker-compose up meta-orchestrator")
        sys.exit(1)

    # Create audit runner
    runner = EcosystemAuditRunner(args.url, args.env)

    if args.continuous:
        # Run continuous monitoring
        try:
            runner.run_continuous_monitoring(args.interval)
        except KeyboardInterrupt:
            print("\n🛑 Continuous monitoring stopped")
            sys.exit(0)
    else:
        # Run single audit
        print(f"🚀 Starting Ecosystem Audit")
        print(f"   Environment: {args.env}")
        print(f"   Target URL: {args.url}")
        if args.focus:
            print(f"   Focus Areas: {', '.join(args.focus)}")
        print(f"   CI Mode: {args.ci}")

        try:
            # Run the audit
            result = runner.run_full_audit(args.focus)

            # Print results
            runner.print_audit_results(result, args.verbose)

            # Save report if requested
            if args.report:
                runner.save_report(result, args.report)

            # Determine exit code for CI/CD
            if args.ci:
                if result.readiness_level == "production_ready" and result.critical_issues == 0:
                    print("✅ CI: Ecosystem audit passed - production ready")
                    sys.exit(0)
                elif result.readiness_level in ["development_ready", "testing_ready"] and result.critical_issues <= 2:
                    print("⚠️ CI: Ecosystem audit passed with warnings")
                    sys.exit(0)
                else:
                    print("❌ CI: Ecosystem audit failed - critical issues detected")
                    sys.exit(1)
            else:
                # Interactive mode - always exit 0
                sys.exit(0)

        except KeyboardInterrupt:
            print("\n⏹️ Audit interrupted by user")
            sys.exit(130)
        except Exception as e:
            print(f"\n❌ Audit execution failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
