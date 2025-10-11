#!/usr/bin/env python3
"""
Comprehensive Deployment Manager for Ecosystem MCP.

Handles startup, rebuild, redeploy, teardown with graceful handling,
health monitoring, and rollback capabilities.
"""

import sys
import subprocess
import signal
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum
import logging


class DeploymentState(Enum):
    """Deployment states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    REBUILDING = "rebuilding"


class DeploymentManager:
    """Manages deployment lifecycle with graceful operations."""
    
    def __init__(self, service_root: Path):
        """Initialize deployment manager."""
        self.service_root = service_root
        self.state_file = service_root / ".deployment_state.json"
        self.pid_file = service_root / "server.pid"
        self.backup_dir = service_root / ".deployment_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def print_banner(self, text: str, style: str = "="):
        """Print a styled banner."""
        width = 80
        print(f"\n{style * width}")
        print(f"  {text}")
        print(f"{style * width}\n")
    
    def print_section(self, text: str):
        """Print a section header."""
        print(f"\n{'─' * 80}")
        print(f"  {text}")
        print(f"{'─' * 80}\n")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"✅ {text}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"❌ {text}")
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"⚠️  {text}")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"ℹ️  {text}")
    
    def print_step(self, step: int, total: int, text: str):
        """Print step progress."""
        print(f"\n[{step}/{total}] {text}")
    
    def save_state(self, state: DeploymentState, metadata: Optional[Dict] = None):
        """Save deployment state."""
        data = {
            "state": state.value,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.state_file.write_text(json.dumps(data, indent=2))
    
    def load_state(self) -> Optional[Dict]:
        """Load deployment state."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}")
        return None
    
    def get_server_pid(self) -> Optional[int]:
        """Get server PID if running."""
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                # Check if process is actually running
                result = subprocess.run(
                    ["ps", "-p", str(pid)],
                    capture_output=True,
                    timeout=5
                )
                # Only return PID if process actually exists
                if result.returncode == 0:
                    return pid
                else:
                    # Process not running, clean up stale PID file
                    self.pid_file.unlink()
                    return None
            except Exception:
                return None
        return None
    
    def is_service_running(self) -> bool:
        """Check if service is running."""
        return self.get_server_pid() is not None
    
    def check_service_health(self, timeout: int = 10) -> bool:
        """Check if service is healthy."""
        import httpx
        
        for i in range(timeout):
            try:
                response = httpx.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1)
        
        return False
    
    def stop_service(self, graceful: bool = True) -> bool:
        """Stop the service gracefully or forcefully."""
        self.print_section("🛑 Stopping Service")
        
        pid = self.get_server_pid()
        if not pid:
            self.print_info("Service is not running")
            return True
        
        self.save_state(DeploymentState.STOPPING)
        
        try:
            if graceful:
                self.print_info(f"Sending SIGTERM to PID {pid}...")
                subprocess.run(["kill", "-TERM", str(pid)], timeout=5)
                
                # Wait for graceful shutdown
                for i in range(10):
                    if not self.is_service_running():
                        self.print_success("Service stopped gracefully")
                        self.pid_file.unlink(missing_ok=True)
                        self.save_state(DeploymentState.STOPPED)
                        return True
                    time.sleep(1)
                
                self.print_warning("Graceful shutdown timeout, forcing...")
            
            # Force kill
            self.print_info(f"Sending SIGKILL to PID {pid}...")
            subprocess.run(["kill", "-9", str(pid)], timeout=5)
            time.sleep(2)
            
            if not self.is_service_running():
                self.print_success("Service stopped (forced)")
                self.pid_file.unlink(missing_ok=True)
                self.save_state(DeploymentState.STOPPED)
                return True
            else:
                self.print_error("Failed to stop service")
                return False
                
        except Exception as e:
            self.print_error(f"Error stopping service: {e}")
            return False
    
    def start_docker_services(self) -> bool:
        """Start Docker services."""
        self.print_section("🐳 Starting Docker Services")
        
        try:
            # Check if services are already running
            result = subprocess.run(
                ["docker-compose", "ps", "--services", "--filter", "status=running"],
                cwd=self.service_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            running = result.stdout.strip().split("\n")
            required = ["postgres", "redis", "ollama"]
            
            missing = [svc for svc in required if svc not in running]
            
            if not missing:
                self.print_success("All Docker services already running")
                return True
            
            self.print_info(f"Starting services: {', '.join(missing)}")
            
            # Start services
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.service_root,
                check=True,
                timeout=120
            )
            
            self.print_success("Docker services started")
            self.print_info("Waiting 10 seconds for services to be ready...")
            time.sleep(10)
            
            return True
            
        except Exception as e:
            self.print_error(f"Failed to start Docker services: {e}")
            return False
    
    def run_validation(self) -> bool:
        """Run system validation."""
        self.print_section("🔍 Running System Validation")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "src.utils.system_validator"],
                cwd=self.service_root,
                timeout=300
            )
            
            if result.returncode == 0:
                self.print_success("Validation passed")
                return True
            else:
                self.print_error("Validation failed")
                return False
                
        except Exception as e:
            self.print_error(f"Validation error: {e}")
            return False
    
    def start_service(self, background: bool = True) -> bool:
        """Start the MCP service."""
        self.print_section("🚀 Starting MCP Service")
        
        if self.is_service_running():
            self.print_warning("Service is already running")
            return True
        
        self.save_state(DeploymentState.STARTING)
        
        venv_python = self.service_root / "venv" / "bin" / "python"
        if not venv_python.exists():
            self.print_error("Virtual environment not found")
            return False
        
        try:
            if background:
                # Start in background
                log_file = self.service_root / "server.log"
                with open(log_file, "w") as f:
                    process = subprocess.Popen(
                        [
                            str(venv_python), "-m", "uvicorn",
                            "src.api.app:create_app", "--factory",
                            "--host", "0.0.0.0", "--port", "8000",
                            "--log-level", "info"
                        ],
                        cwd=self.service_root,
                        stdout=f,
                        stderr=subprocess.STDOUT,
                        start_new_session=True
                    )
                    
                    self.pid_file.write_text(str(process.pid))
                    self.print_success(f"Service started (PID: {process.pid})")
                
                # Wait for health check
                self.print_info("Waiting for service to be healthy...")
                if self.check_service_health(timeout=30):
                    self.print_success("Service is healthy ✨")
                    self.save_state(DeploymentState.RUNNING, {
                        "pid": process.pid,
                        "started_at": time.time()
                    })
                    return True
                else:
                    self.print_error("Service health check failed")
                    self.print_info("Check server.log for details")
                    self.save_state(DeploymentState.FAILED)
                    return False
            else:
                # Start in foreground
                subprocess.run(
                    [
                        str(venv_python), "-m", "uvicorn",
                        "src.api.app:create_app", "--factory",
                        "--host", "0.0.0.0", "--port", "8000",
                        "--log-level", "info"
                    ],
                    cwd=self.service_root
                )
                return True
                
        except Exception as e:
            self.print_error(f"Failed to start service: {e}")
            self.save_state(DeploymentState.FAILED)
            return False
    
    def deploy(self, skip_validation: bool = False) -> bool:
        """Full deployment process."""
        self.print_banner("🚀 ECOSYSTEM MCP - DEPLOYMENT", "=")
        
        steps = [
            ("System Validation", lambda: skip_validation or self.run_validation()),
            ("Docker Services", self.start_docker_services),
            ("Start Service", lambda: self.start_service(background=True))
        ]
        
        total = len(steps)
        for i, (name, func) in enumerate(steps, 1):
            self.print_step(i, total, name)
            if not func():
                self.print_banner("❌ DEPLOYMENT FAILED", "=")
                return False
        
        self.print_banner("✅ DEPLOYMENT SUCCESSFUL", "=")
        self.print_info("Service URL: http://localhost:8000")
        self.print_info("API Docs: http://localhost:8000/docs")
        self.print_info("Health Check: http://localhost:8000/health")
        
        return True
    
    def teardown(self, remove_data: bool = False) -> bool:
        """Graceful teardown."""
        self.print_banner("🛑 ECOSYSTEM MCP - TEARDOWN", "=")
        
        # Stop service
        if not self.stop_service(graceful=True):
            self.print_warning("Service stop had issues, continuing...")
        
        # Stop Docker services
        self.print_section("🐳 Stopping Docker Services")
        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=self.service_root,
                check=True,
                timeout=60
            )
            self.print_success("Docker services stopped")
        except Exception as e:
            self.print_error(f"Failed to stop Docker services: {e}")
        
        # Optionally remove data
        if remove_data:
            self.print_section("🗑️  Removing Data")
            self.print_warning("This will delete all data!")
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() == "yes":
                data_dirs = ["data", "logs"]
                for dir_name in data_dirs:
                    dir_path = self.service_root / dir_name
                    if dir_path.exists():
                        import shutil
                        shutil.rmtree(dir_path)
                        self.print_success(f"Removed {dir_name}/")
            else:
                self.print_info("Data removal cancelled")
        
        self.print_banner("✅ TEARDOWN COMPLETE", "=")
        return True
    
    def rebuild(self, clean: bool = False) -> bool:
        """Rebuild and redeploy."""
        self.print_banner("🔄 ECOSYSTEM MCP - REBUILD", "=")
        
        self.save_state(DeploymentState.REBUILDING)
        
        # Stop service
        if not self.stop_service(graceful=True):
            return False
        
        # Clean if requested
        if clean:
            self.print_section("🧹 Cleaning Build Artifacts")
            patterns = ["__pycache__", "*.pyc", "*.pyo", ".pytest_cache"]
            for pattern in patterns:
                try:
                    if "*" in pattern:
                        import glob
                        files = glob.glob(f"**/{pattern}", recursive=True)
                        for f in files:
                            Path(f).unlink(missing_ok=True)
                    else:
                        for p in self.service_root.rglob(pattern):
                            if p.is_dir():
                                import shutil
                                shutil.rmtree(p)
                            else:
                                p.unlink()
                except Exception as e:
                    self.print_warning(f"Cleaning {pattern}: {e}")
            
            self.print_success("Build artifacts cleaned")
        
        # Redeploy
        return self.deploy(skip_validation=False)
    
    def status(self) -> Dict:
        """Get deployment status."""
        self.print_banner("📊 ECOSYSTEM MCP - STATUS", "=")
        
        # Check service
        is_running = self.is_service_running()
        pid = self.get_server_pid()
        is_healthy = self.check_service_health(timeout=3) if is_running else False
        
        # Check Docker
        docker_status = {}
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                cwd=self.service_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        service = json.loads(line)
                        docker_status[service["Service"]] = service["State"]
                    except:
                        pass
        except Exception:
            docker_status = {"error": "Could not check Docker services"}
        
        # Load state
        state_data = self.load_state()
        
        # Print status
        print("Service Status:")
        print(f"  Running: {'✅ Yes' if is_running else '❌ No'}")
        if pid:
            print(f"  PID: {pid}")
        print(f"  Healthy: {'✅ Yes' if is_healthy else '❌ No'}")
        
        print("\nDocker Services:")
        for service, state in docker_status.items():
            icon = "✅" if state == "running" else "❌"
            print(f"  {icon} {service}: {state}")
        
        if state_data:
            print("\nLast State:")
            print(f"  State: {state_data.get('state')}")
            print(f"  Timestamp: {time.ctime(state_data.get('timestamp', 0))}")
        
        print()
        
        return {
            "service_running": is_running,
            "service_healthy": is_healthy,
            "pid": pid,
            "docker_services": docker_status,
            "last_state": state_data
        }


def main():
    """Main CLI."""
    import argparse
    
    service_root = Path(__file__).parent
    manager = DeploymentManager(service_root)
    
    parser = argparse.ArgumentParser(description="Ecosystem MCP Deployment Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Deploy
    deploy_parser = subparsers.add_parser("deploy", help="Deploy the service")
    deploy_parser.add_argument("--skip-validation", action="store_true",
                               help="Skip system validation")
    
    # Start
    start_parser = subparsers.add_parser("start", help="Start the service")
    start_parser.add_argument("--foreground", action="store_true",
                             help="Run in foreground")
    
    # Stop
    stop_parser = subparsers.add_parser("stop", help="Stop the service")
    stop_parser.add_argument("--force", action="store_true",
                            help="Force kill")
    
    # Restart
    restart_parser = subparsers.add_parser("restart", help="Restart the service")
    
    # Rebuild
    rebuild_parser = subparsers.add_parser("rebuild", help="Rebuild and redeploy")
    rebuild_parser.add_argument("--clean", action="store_true",
                               help="Clean build artifacts")
    
    # Teardown
    teardown_parser = subparsers.add_parser("teardown", help="Teardown everything")
    teardown_parser.add_argument("--remove-data", action="store_true",
                                help="Remove all data")
    
    # Status
    status_parser = subparsers.add_parser("status", help="Show status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "deploy":
            success = manager.deploy(skip_validation=args.skip_validation)
        elif args.command == "start":
            if manager.start_docker_services():
                success = manager.start_service(background=not args.foreground)
            else:
                success = False
        elif args.command == "stop":
            success = manager.stop_service(graceful=not args.force)
        elif args.command == "restart":
            if manager.stop_service(graceful=True):
                success = manager.deploy(skip_validation=True)
            else:
                success = False
        elif args.command == "rebuild":
            success = manager.rebuild(clean=args.clean)
        elif args.command == "teardown":
            success = manager.teardown(remove_data=args.remove_data)
        elif args.command == "status":
            manager.status()
            success = True
        else:
            parser.print_help()
            success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

