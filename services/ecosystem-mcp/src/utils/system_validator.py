#!/usr/bin/env python3
"""
Comprehensive System Validator for Ecosystem MCP.

Validates all system requirements, dependencies, and configurations
before service startup. Provides automatic fixes where possible.
"""

import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import importlib.util


class SystemValidator:
    """Validates system requirements and provides auto-fixes."""
    
    def __init__(self, service_root: Path):
        """Initialize validator."""
        self.service_root = service_root
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.fixes_applied: List[str] = []
        
    def print_banner(self, text: str, char: str = "="):
        """Print a banner."""
        print(f"\n{char * 80}")
        print(f"  {text}")
        print(f"{char * 80}\n")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"✅ {text}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"❌ {text}")
        self.issues.append(text)
    
    def print_warning(self, text: str):
        """Print warning message."""
        print(f"⚠️  {text}")
        self.warnings.append(text)
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"ℹ️  {text}")
    
    def print_fix(self, text: str):
        """Print fix applied message."""
        print(f"🔧 {text}")
        self.fixes_applied.append(text)
    
    def check_python_version(self) -> bool:
        """Check Python version."""
        print("\n📋 Checking Python Version...")
        version = sys.version_info
        
        if version.major == 3 and version.minor >= 10:
            self.print_success(f"Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.print_error(f"Python 3.10+ required, found {version.major}.{version.minor}.{version.micro}")
            return False
    
    def check_docker(self) -> bool:
        """Check if Docker is running."""
        print("\n🐳 Checking Docker...")
        
        if not shutil.which("docker"):
            self.print_error("Docker not installed")
            return False
        
        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.print_success("Docker is running")
                return True
            else:
                self.print_error("Docker is installed but not running")
                self.print_info("Start Docker Desktop: open -a Docker")
                return False
        except Exception as e:
            self.print_error(f"Docker check failed: {e}")
            return False
    
    def check_virtual_environment(self) -> bool:
        """Check if virtual environment exists and is activated."""
        print("\n🐍 Checking Virtual Environment...")
        
        venv_path = self.service_root / "venv"
        
        if not venv_path.exists():
            self.print_warning("Virtual environment not found")
            self.print_info("Creating virtual environment...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    check=True,
                    capture_output=True
                )
                self.print_fix("Created virtual environment at venv/")
                return True
            except Exception as e:
                self.print_error(f"Failed to create virtual environment: {e}")
                return False
        else:
            self.print_success("Virtual environment exists")
            return True
    
    def get_pip_executable(self) -> str:
        """Get pip executable path."""
        venv_pip = self.service_root / "venv" / "bin" / "pip"
        if venv_pip.exists():
            return str(venv_pip)
        return "pip3"
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        print("\n📦 Checking Dependencies...")
        
        required_packages = {
            "fastapi": "FastAPI web framework",
            "uvicorn": "ASGI server",
            "pydantic": "Data validation",
            "pydantic_settings": "Settings management",
            "sqlalchemy": "Database ORM",
            "asyncpg": "Async PostgreSQL driver",
            "redis": "Redis client",
            "chromadb": "Vector database",
            "structlog": "Structured logging",
            "rich": "Terminal formatting",
            "httpx": "HTTP client",
            "psycopg": "PostgreSQL driver",
        }
        
        missing = []
        installed = []
        
        for package, description in required_packages.items():
            # Handle package name variations
            import_name = package.replace("-", "_")
            if package == "pydantic_settings":
                import_name = "pydantic_settings"
            elif package == "chromadb":
                import_name = "chromadb"
            
            spec = importlib.util.find_spec(import_name)
            if spec is None:
                missing.append((package, description))
                self.print_warning(f"Missing: {package} ({description})")
            else:
                installed.append(package)
        
        if installed:
            self.print_success(f"Found {len(installed)}/{len(required_packages)} packages")
        
        if missing:
            self.print_info(f"\n🔧 Installing {len(missing)} missing packages...")
            return self.install_dependencies(missing)
        
        return True
    
    def install_dependencies(self, missing: List[Tuple[str, str]]) -> bool:
        """Install missing dependencies."""
        pip = self.get_pip_executable()
        
        # Special handling for packages with extras
        packages_to_install = []
        for package, _ in missing:
            if package == "psycopg":
                packages_to_install.append("psycopg[binary]")
            else:
                packages_to_install.append(package)
        
        try:
            self.print_info(f"Running: {pip} install {' '.join(packages_to_install)}")
            result = subprocess.run(
                [pip, "install", "-q"] + packages_to_install,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.print_fix(f"Installed {len(packages_to_install)} packages")
                return True
            else:
                self.print_error(f"Failed to install packages: {result.stderr}")
                return False
        except Exception as e:
            self.print_error(f"Installation failed: {e}")
            return False
    
    def check_configuration(self) -> bool:
        """Check configuration files."""
        print("\n⚙️  Checking Configuration...")
        
        env_file = self.service_root / ".env"
        env_template = self.service_root / "env.template"
        
        if not env_file.exists():
            if env_template.exists():
                self.print_warning(".env file not found")
                self.print_info("Creating .env from template...")
                try:
                    # Create basic .env
                    env_content = """# Ecosystem MCP Configuration

# Service
SERVICE_NAME=ecosystem-mcp
LOG_LEVEL=INFO

# PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecosystem_mcp

# Redis
REDIS_URL=redis://localhost:6379/0

# ChromaDB
CHROMA_PATH=./data/chroma_db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_SMALL=llama3.1:8b-instruct-q8_0
OLLAMA_MODEL_MEDIUM=mistral:7b-instruct-q8_0
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# Model Strategy
MODEL_STRATEGY=ollama-only

# Git Repository
GIT_REPO_PATH=../../..

# Ingestion
MAX_WORKERS=8
BATCH_SIZE=100
"""
                    env_file.write_text(env_content)
                    self.print_fix("Created .env file with defaults")
                    return True
                except Exception as e:
                    self.print_error(f"Failed to create .env: {e}")
                    return False
            else:
                self.print_error(".env and env.template not found")
                return False
        else:
            self.print_success(".env file exists")
            return True
    
    def check_directories(self) -> bool:
        """Check and create required directories."""
        print("\n📁 Checking Directories...")
        
        required_dirs = [
            "data",
            "data/chroma_db",
            "logs",
        ]
        
        created = []
        for dir_name in required_dirs:
            dir_path = self.service_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(dir_name)
        
        if created:
            self.print_fix(f"Created directories: {', '.join(created)}")
        
        self.print_success("All required directories exist")
        return True
    
    def check_docker_services(self) -> Dict[str, bool]:
        """Check Docker services status."""
        print("\n🐳 Checking Docker Services...")
        
        services = {
            "postgres": False,
            "redis": False,
            "ollama": False
        }
        
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--services", "--filter", "status=running"],
                cwd=self.service_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            running_services = result.stdout.strip().split("\n")
            
            for service in services.keys():
                if f"ecosystem-mcp-{service}" in result.stdout or service in running_services:
                    services[service] = True
                    self.print_success(f"{service.capitalize()}: Running")
                else:
                    self.print_warning(f"{service.capitalize()}: Not running")
        except Exception as e:
            self.print_warning(f"Could not check Docker services: {e}")
        
        return services
    
    def fix_sqlalchemy_models(self) -> bool:
        """Fix SQLAlchemy model issues."""
        print("\n🔧 Checking SQLAlchemy Models...")
        
        db_models_file = self.service_root / "src" / "storage" / "db_models.py"
        
        if not db_models_file.exists():
            self.print_info("db_models.py not found, skipping")
            return True
        
        try:
            content = db_models_file.read_text()
            
            # Check for reserved 'metadata' attribute (but exclude renamed versions)
            # Look for exact pattern: metadata = Column (without prefix like doc_, extra_, etc.)
            import re
            pattern = r'^\s+metadata\s*=\s*Column'
            if re.search(pattern, content, re.MULTILINE):
                self.print_warning("Found reserved 'metadata' attribute in SQLAlchemy model")
                self.print_info("This should be renamed to avoid conflicts")
                self.print_info("Suggestion: Rename 'metadata' to 'doc_metadata'")
                return False
            else:
                self.print_success("SQLAlchemy models look good")
                return True
        except Exception as e:
            self.print_warning(f"Could not check models: {e}")
            return True
    
    def run_full_validation(self) -> bool:
        """Run full system validation."""
        self.print_banner("🔍 ECOSYSTEM MCP - SYSTEM VALIDATION", "=")
        
        checks = [
            ("Python Version", self.check_python_version()),
            ("Docker", self.check_docker()),
            ("Virtual Environment", self.check_virtual_environment()),
            ("Dependencies", self.check_dependencies()),
            ("Configuration", self.check_configuration()),
            ("Directories", self.check_directories()),
            ("SQLAlchemy Models", self.fix_sqlalchemy_models()),
        ]
        
        # Check Docker services (optional)
        services = self.check_docker_services()
        
        # Print summary
        self.print_banner("📊 VALIDATION SUMMARY", "=")
        
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        print(f"\n✅ Passed: {passed}/{total} checks")
        
        if self.fixes_applied:
            print(f"\n🔧 Fixes Applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"  • {fix}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings[:5]:
                print(f"  • {warning}")
        
        if self.issues:
            print(f"\n❌ Issues: {len(self.issues)}")
            for issue in self.issues:
                print(f"  • {issue}")
        
        success = passed == total and len(self.issues) == 0
        
        if success:
            self.print_banner("✅ ALL CHECKS PASSED - READY TO START", "=")
        else:
            self.print_banner("⚠️  SOME ISSUES FOUND - REVIEW ABOVE", "=")
        
        return success


def main():
    """Run system validation."""
    service_root = Path(__file__).parent.parent.parent
    validator = SystemValidator(service_root)
    
    success = validator.run_full_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

