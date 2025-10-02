#!/usr/bin/env python3
"""
Automated Container Restart and Self-Healing System
Intelligent service recovery based on failure patterns and health monitoring
"""

import json
import time
import subprocess
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
# import psutil  # Optional dependency for advanced resource monitoring

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FailurePattern(Enum):
    """Types of service failure patterns"""
    HEALTH_CHECK_FAILURE = "health_check_failure"
    EXIT_CODE_NONZERO = "exit_code_nonzero"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_FAILURE = "network_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    CONFIGURATION_ERROR = "configuration_error"

class RecoveryStrategy(Enum):
    """Recovery strategy types"""
    IMMEDIATE_RESTART = "immediate_restart"
    DELAYED_RESTART = "delayed_restart"
    GRACEFUL_RESTART = "graceful_restart"
    RESOURCE_SCALE_UP = "resource_scale_up"
    CONFIGURATION_ROLLBACK = "configuration_rollback"
    DEPENDENCY_RECOVERY = "dependency_recovery"

@dataclass
class ServiceHealth:
    """Service health information"""
    service_name: str
    container_id: str = ""
    status: str = "unknown"
    health_status: str = "unknown"
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    consecutive_failures: int = 0
    total_failures: int = 0
    last_failure_time: Optional[datetime] = None
    failure_pattern: Optional[FailurePattern] = None
    recovery_attempts: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class HealingAction:
    """Self-healing action record"""
    timestamp: datetime
    service_name: str
    action_type: RecoveryStrategy
    reason: str
    success: bool = False
    details: str = ""
    duration_seconds: float = 0

class AutoHealer:
    """Intelligent auto-healing system for container services"""

    def __init__(self, docker_compose_file: str = "docker-compose.dev.yml",
                 max_restart_attempts: int = 5, monitoring_interval: int = 30):
        self.docker_compose_file = docker_compose_file
        self.max_restart_attempts = max_restart_attempts
        self.monitoring_interval = monitoring_interval
        self.services_health: Dict[str, ServiceHealth] = {}
        self.healing_history: List[HealingAction] = []
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Recovery strategies based on failure patterns
        self.recovery_strategies = {
            FailurePattern.HEALTH_CHECK_FAILURE: [RecoveryStrategy.IMMEDIATE_RESTART, RecoveryStrategy.DELAYED_RESTART],
            FailurePattern.EXIT_CODE_NONZERO: [RecoveryStrategy.DELAYED_RESTART, RecoveryStrategy.GRACEFUL_RESTART],
            FailurePattern.RESOURCE_EXHAUSTION: [RecoveryStrategy.RESOURCE_SCALE_UP, RecoveryStrategy.DELAYED_RESTART],
            FailurePattern.NETWORK_FAILURE: [RecoveryStrategy.DELAYED_RESTART, RecoveryStrategy.DEPENDENCY_RECOVERY],
            FailurePattern.DEPENDENCY_FAILURE: [RecoveryStrategy.DEPENDENCY_RECOVERY, RecoveryStrategy.DELAYED_RESTART],
            FailurePattern.CONFIGURATION_ERROR: [RecoveryStrategy.CONFIGURATION_ROLLBACK, RecoveryStrategy.DELAYED_RESTART]
        }

    def start_monitoring(self):
        """Start continuous monitoring and healing"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Auto-healing monitoring started")

    def stop_monitoring(self):
        """Stop monitoring and healing"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Auto-healing monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._check_service_health()
                self._perform_healing_actions()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitoring_interval)

    def _check_service_health(self):
        """Check health of all services"""
        try:
            # Get container status using docker ps
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}},{{.Status}},{{.Ports}}', '--filter', 'name=hackathon'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                current_services = set()

                for line in lines:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 2:
                            service_name = parts[0].replace('hackathon-', '')
                            status = parts[1].lower()
                            current_services.add(service_name)

                            # Update or create service health record
                            if service_name not in self.services_health:
                                self.services_health[service_name] = ServiceHealth(service_name=service_name)

                            service_health = self.services_health[service_name]
                            service_health.status = status

                            # Check for health status in the status string
                            if 'healthy' in status:
                                service_health.health_status = 'healthy'
                                service_health.consecutive_failures = 0
                            elif 'unhealthy' in status:
                                service_health.health_status = 'unhealthy'
                                service_health.consecutive_failures += 1
                                service_health.last_failure_time = datetime.now()
                                self._analyze_failure_pattern(service_health)
                            elif 'exited' in status or 'dead' in status:
                                service_health.health_status = 'failed'
                                service_health.consecutive_failures += 1
                                service_health.last_failure_time = datetime.now()
                                self._analyze_failure_pattern(service_health)

                # Check for missing services
                all_expected_services = self._get_expected_services()
                for service_name in all_expected_services:
                    if service_name not in current_services and service_name not in self.services_health:
                        self.services_health[service_name] = ServiceHealth(
                            service_name=service_name,
                            status='missing',
                            health_status='failed',
                            consecutive_failures=1,
                            last_failure_time=datetime.now()
                        )

        except Exception as e:
            logger.error(f"Failed to check service health: {e}")

    def _analyze_failure_pattern(self, service_health: ServiceHealth):
        """Analyze the pattern of service failure"""
        if service_health.health_status == 'unhealthy':
            service_health.failure_pattern = FailurePattern.HEALTH_CHECK_FAILURE
        elif 'exited' in service_health.status or 'dead' in service_health.status:
            # Try to get exit code from docker logs
            try:
                result = subprocess.run(
                    ['docker', 'inspect', f'hackathon-{service_health.service_name}',
                     '--format', '{{.State.ExitCode}}'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    exit_code = int(result.stdout.strip())
                    if exit_code != 0:
                        service_health.failure_pattern = FailurePattern.EXIT_CODE_NONZERO
            except:
                service_health.failure_pattern = FailurePattern.EXIT_CODE_NONZERO

        # Analyze resource usage for resource exhaustion
        if self._check_resource_exhaustion(service_health.service_name):
            service_health.failure_pattern = FailurePattern.RESOURCE_EXHAUSTION

    def _check_resource_exhaustion(self, service_name: str) -> bool:
        """Check if service failed due to resource exhaustion"""
        try:
            # Get container stats
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', '{{.CPUPerc}},{{.MemPerc}}',
                 f'hackathon-{service_name}'],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                cpu_perc, mem_perc = result.stdout.strip().split(',')
                cpu_usage = float(cpu_perc.strip('%'))
                mem_usage = float(mem_perc.strip('%'))

                # Consider high resource usage as potential exhaustion
                if cpu_usage > 90 or mem_usage > 90:
                    return True

        except Exception as e:
            logger.debug(f"Failed to check resource usage for {service_name}: {e}")

        return False

    def _perform_healing_actions(self):
        """Perform healing actions for unhealthy services"""
        for service_name, service_health in self.services_health.items():
            if self._needs_healing(service_health):
                self._heal_service(service_health)

    def _needs_healing(self, service_health: ServiceHealth) -> bool:
        """Determine if a service needs healing"""
        # Don't heal if too many restart attempts recently
        if service_health.restart_count >= self.max_restart_attempts:
            if service_health.last_restart:
                time_since_last_restart = datetime.now() - service_health.last_restart
                if time_since_last_restart < timedelta(minutes=30):
                    return False

        # Check various failure conditions
        unhealthy_conditions = [
            service_health.health_status in ['unhealthy', 'failed'],
            service_health.consecutive_failures >= 2,
            service_health.status in ['exited', 'dead', 'missing']
        ]

        return any(unhealthy_conditions)

    def _heal_service(self, service_health: ServiceHealth):
        """Attempt to heal a service using appropriate strategy"""
        if not service_health.failure_pattern:
            service_health.failure_pattern = FailurePattern.HEALTH_CHECK_FAILURE

        # Get recovery strategies for this failure pattern
        strategies = self.recovery_strategies.get(service_health.failure_pattern, [RecoveryStrategy.DELAYED_RESTART])

        for strategy in strategies:
            if self._attempt_recovery(service_health, strategy):
                logger.info(f"Successfully healed {service_health.service_name} using {strategy.value}")
                return

        logger.warning(f"Failed to heal {service_health.service_name} with any strategy")

    def _attempt_recovery(self, service_health: ServiceHealth, strategy: RecoveryStrategy) -> bool:
        """Attempt a specific recovery strategy"""
        start_time = time.time()
        action = HealingAction(
            timestamp=datetime.now(),
            service_name=service_health.service_name,
            action_type=strategy,
            reason=f"{service_health.failure_pattern.value} - {service_health.consecutive_failures} consecutive failures"
        )

        try:
            if strategy == RecoveryStrategy.IMMEDIATE_RESTART:
                success = self._restart_container(service_health.service_name)

            elif strategy == RecoveryStrategy.DELAYED_RESTART:
                time.sleep(5)  # Wait before restart
                success = self._restart_container(service_health.service_name)

            elif strategy == RecoveryStrategy.GRACEFUL_RESTART:
                success = self._graceful_restart(service_health.service_name)

            elif strategy == RecoveryStrategy.RESOURCE_SCALE_UP:
                success = self._scale_up_resources(service_health.service_name)

            elif strategy == RecoveryStrategy.CONFIGURATION_ROLLBACK:
                success = self._rollback_configuration(service_health.service_name)

            elif strategy == RecoveryStrategy.DEPENDENCY_RECOVERY:
                success = self._recover_dependencies(service_health.service_name)

            else:
                success = False

            action.success = success
            action.duration_seconds = time.time() - start_time
            action.details = f"Recovery {'succeeded' if success else 'failed'}"

            if success:
                service_health.restart_count += 1
                service_health.last_restart = datetime.now()
                service_health.consecutive_failures = 0
                service_health.health_status = 'recovering'

        except Exception as e:
            action.success = False
            action.details = f"Exception: {e}"
            logger.error(f"Recovery failed for {service_health.service_name}: {e}")

        self.healing_history.append(action)
        return action.success

    def _restart_container(self, service_name: str) -> bool:
        """Restart a container"""
        try:
            logger.info(f"Restarting container: {service_name}")

            # First try docker-compose restart
            result = subprocess.run(
                ['docker-compose', '-f', self.docker_compose_file, 'restart', service_name],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Successfully restarted {service_name}")
                return True
            else:
                logger.warning(f"Docker-compose restart failed for {service_name}: {result.stderr}")

                # Fallback to manual container restart
                result = subprocess.run(
                    ['docker', 'restart', f'hackathon-{service_name}'],
                    capture_output=True, text=True, timeout=30
                )

                return result.returncode == 0

        except Exception as e:
            logger.error(f"Failed to restart {service_name}: {e}")
            return False

    def _graceful_restart(self, service_name: str) -> bool:
        """Perform a graceful restart with proper shutdown"""
        try:
            logger.info(f"Performing graceful restart for: {service_name}")

            # Send SIGTERM first
            container_name = f'hackathon-{service_name}'
            subprocess.run(['docker', 'kill', '--signal=SIGTERM', container_name],
                         capture_output=True, timeout=10)

            # Wait for graceful shutdown
            time.sleep(10)

            # Then restart
            return self._restart_container(service_name)

        except Exception as e:
            logger.error(f"Graceful restart failed for {service_name}: {e}")
            return False

    def _scale_up_resources(self, service_name: str) -> bool:
        """Attempt to scale up resources for a service"""
        try:
            logger.info(f"Attempting resource scale-up for: {service_name}")

            # This would integrate with Docker resource limits
            # For now, just restart with potentially more resources
            return self._restart_container(service_name)

        except Exception as e:
            logger.error(f"Resource scale-up failed for {service_name}: {e}")
            return False

    def _rollback_configuration(self, service_name: str) -> bool:
        """Rollback to previous configuration"""
        try:
            logger.info(f"Attempting configuration rollback for: {service_name}")

            # This would integrate with configuration management
            # For now, just restart
            return self._restart_container(service_name)

        except Exception as e:
            logger.error(f"Configuration rollback failed for {service_name}: {e}")
            return False

    def _recover_dependencies(self, service_name: str) -> bool:
        """Attempt to recover service dependencies"""
        try:
            logger.info(f"Attempting dependency recovery for: {service_name}")

            # Get service dependencies and try to restart them
            # This would integrate with dependency analysis
            return self._restart_container(service_name)

        except Exception as e:
            logger.error(f"Dependency recovery failed for {service_name}: {e}")
            return False

    def _get_expected_services(self) -> List[str]:
        """Get list of expected services from docker-compose"""
        try:
            with open(self.docker_compose_file, 'r') as f:
                config = json.load(f) if self.docker_compose_file.suffix == '.json' else yaml.safe_load(f)

            if 'services' in config:
                return list(config['services'].keys())

        except Exception as e:
            logger.error(f"Failed to get expected services: {e}")

        return []

    def get_healing_report(self) -> Dict[str, Any]:
        """Generate healing activity report"""
        total_actions = len(self.healing_history)
        successful_actions = sum(1 for action in self.healing_history if action.success)
        failed_actions = total_actions - successful_actions

        # Group by service
        service_actions = {}
        for action in self.healing_history:
            if action.service_name not in service_actions:
                service_actions[action.service_name] = []
            service_actions[action.service_name].append(action)

        # Calculate success rates
        success_rates = {}
        for service, actions in service_actions.items():
            success_count = sum(1 for action in actions if action.success)
            success_rates[service] = success_count / len(actions) if actions else 0

        return {
            'summary': {
                'total_actions': total_actions,
                'successful_actions': successful_actions,
                'failed_actions': failed_actions,
                'success_rate': successful_actions / total_actions if total_actions > 0 else 0
            },
            'by_service': {
                service: {
                    'total_actions': len(actions),
                    'successful': sum(1 for a in actions if a.success),
                    'failed': sum(1 for a in actions if not a.success),
                    'success_rate': success_rates[service]
                }
                for service, actions in service_actions.items()
            },
            'recent_actions': [
                {
                    'timestamp': action.timestamp.isoformat(),
                    'service': action.service_name,
                    'action': action.action_type.value,
                    'success': action.success,
                    'reason': action.reason,
                    'duration': action.duration_seconds
                }
                for action in self.healing_history[-10:]  # Last 10 actions
            ]
        }

    def export_healing_report(self, output_file: str = "healing_report.json"):
        """Export healing report to file"""
        report = self.get_healing_report()
        report['export_timestamp'] = datetime.now().isoformat()

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Healing report exported to: {output_file}")

    def print_healing_status(self):
        """Print current healing status"""
        print("\n" + "="*80)
        print("🔧 AUTO-HEALING SYSTEM STATUS")
        print("="*80)

        report = self.get_healing_report()
        summary = report['summary']

        print(f"\n📊 SUMMARY")
        print(f"  Monitoring Active: {'✅' if self.monitoring_active else '❌'}")
        print(f"  Total Healing Actions: {summary['total_actions']}")
        print(f"  Successful: {summary['successful_actions']}")
        print(f"  Failed: {summary['failed_actions']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")

        print(f"\n🏥 SERVICE HEALTH STATUS")
        for service_name, health in self.services_health.items():
            status_icon = "🟢" if health.health_status == 'healthy' else "🔴" if health.health_status == 'failed' else "🟡"
            print(f"  {status_icon} {service_name}: {health.health_status} (restarts: {health.restart_count})")

        if report['recent_actions']:
            print(f"\n📝 RECENT HEALING ACTIONS")
            for action in report['recent_actions'][-5:]:  # Show last 5
                success_icon = "✅" if action['success'] else "❌"
                print(f"  {success_icon} {action['timestamp'][:19]} {action['service']}: {action['action']}")

        print("\n" + "="*80)


def main():
    """Main entry point for auto-healing system"""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-healing system for container services")
    parser.add_argument("--start", action="store_true", help="Start monitoring and healing")
    parser.add_argument("--stop", action="store_true", help="Stop monitoring and healing")
    parser.add_argument("--status", action="store_true", help="Show healing status")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    parser.add_argument("--max-attempts", type=int, default=5, help="Maximum restart attempts")

    args = parser.parse_args()

    healer = AutoHealer(monitoring_interval=args.interval, max_restart_attempts=args.max_attempts)

    if args.start:
        print("🚀 Starting auto-healing system...")
        healer.start_monitoring()
        print("✅ Auto-healing system started. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(5)
                healer.print_healing_status()
        except KeyboardInterrupt:
            print("\n🛑 Stopping auto-healing system...")
            healer.stop_monitoring()

    elif args.stop:
        print("🛑 Stopping auto-healing system...")
        healer.stop_monitoring()

    elif args.status:
        healer.print_healing_status()

    else:
        print("🤖 Auto-healing system")
        print("Usage:")
        print("  python auto_healer.py --start          # Start monitoring")
        print("  python auto_healer.py --stop           # Stop monitoring")
        print("  python auto_healer.py --status         # Show status")
        print("  python auto_healer.py --start --interval 60  # Start with 60s interval")


if __name__ == "__main__":
    main()
