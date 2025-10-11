#!/usr/bin/env python3
"""
Configuration Validator for Ecosystem MCP.

Validates that .env file matches docker-compose.yml to prevent configuration drift.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml


class ConfigValidator:
    """Validates configuration consistency between .env and docker-compose.yml."""
    
    def __init__(self, service_root: Path):
        """Initialize validator."""
        self.service_root = service_root
        self.env_file = service_root / ".env"
        self.docker_compose_file = service_root / "docker-compose.yml"
        self.issues: List[str] = []
        self.warnings: List[str] = []
    
    def parse_env_file(self) -> Dict[str, str]:
        """Parse .env file into key-value pairs."""
        env_vars = {}
        
        if not self.env_file.exists():
            return env_vars
        
        for line in self.env_file.read_text().split('\n'):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def parse_docker_compose(self) -> Dict[str, Dict[str, str]]:
        """Parse docker-compose.yml to extract environment variables."""
        if not self.docker_compose_file.exists():
            return {}
        
        try:
            with open(self.docker_compose_file) as f:
                compose_config = yaml.safe_load(f)
            
            services_env = {}
            
            if 'services' in compose_config:
                for service_name, service_config in compose_config['services'].items():
                    if 'environment' in service_config:
                        services_env[service_name] = {}
                        env = service_config['environment']
                        
                        # Handle both dict and list formats
                        if isinstance(env, dict):
                            services_env[service_name] = env
                        elif isinstance(env, list):
                            for item in env:
                                if '=' in item:
                                    key, value = item.split('=', 1)
                                    services_env[service_name][key] = value
            
            return services_env
        except Exception as e:
            self.issues.append(f"Failed to parse docker-compose.yml: {e}")
            return {}
    
    def extract_db_credentials_from_url(self, database_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract username, password, database from DATABASE_URL."""
        # postgresql://user:password@host:port/database
        pattern = r'postgresql://([^:]+):([^@]+)@[^/]+/(.+)'
        match = re.match(pattern, database_url)
        
        if match:
            return match.group(1), match.group(2), match.group(3)
        return None, None, None
    
    def validate_postgresql_config(self, env_vars: Dict[str, str], docker_env: Dict[str, Dict[str, str]]) -> bool:
        """Validate PostgreSQL configuration consistency."""
        if 'postgres' not in docker_env:
            self.warnings.append("No postgres service found in docker-compose.yml")
            return True
        
        postgres_env = docker_env['postgres']
        
        # Get expected values from docker-compose
        expected_user = postgres_env.get('POSTGRES_USER')
        expected_password = postgres_env.get('POSTGRES_PASSWORD')
        expected_db = postgres_env.get('POSTGRES_DB')
        
        # Get actual values from .env
        database_url = env_vars.get('DATABASE_URL', '')
        actual_user, actual_password, actual_db = self.extract_db_credentials_from_url(database_url)
        
        issues_found = False
        
        if expected_user and actual_user != expected_user:
            self.issues.append(
                f"PostgreSQL user mismatch: "
                f"docker-compose.yml has '{expected_user}', "
                f".env has '{actual_user}'"
            )
            issues_found = True
        
        if expected_password and actual_password != expected_password:
            self.issues.append(
                f"PostgreSQL password mismatch: "
                f"docker-compose.yml has '{expected_password}', "
                f".env has '{actual_password}'"
            )
            issues_found = True
        
        if expected_db and actual_db != expected_db:
            self.issues.append(
                f"PostgreSQL database mismatch: "
                f"docker-compose.yml has '{expected_db}', "
                f".env has '{actual_db}'"
            )
            issues_found = True
        
        return not issues_found
    
    def validate_redis_config(self, env_vars: Dict[str, str], docker_env: Dict[str, Dict[str, str]]) -> bool:
        """Validate Redis configuration consistency."""
        # Redis is simpler - just check it exists
        if 'redis' not in docker_env:
            self.warnings.append("No redis service found in docker-compose.yml")
        
        redis_url = env_vars.get('REDIS_URL', '')
        if not redis_url:
            self.warnings.append("No REDIS_URL in .env file")
            return False
        
        # Basic validation - should be redis://
        if not redis_url.startswith('redis://'):
            self.issues.append(f"Invalid REDIS_URL format: {redis_url}")
            return False
        
        return True
    
    def validate_ollama_config(self, env_vars: Dict[str, str], docker_env: Dict[str, Dict[str, str]]) -> bool:
        """Validate Ollama configuration."""
        if 'ollama' not in docker_env:
            self.warnings.append("No ollama service found in docker-compose.yml")
        
        ollama_url = env_vars.get('OLLAMA_BASE_URL', '')
        if not ollama_url:
            self.warnings.append("No OLLAMA_BASE_URL in .env file")
            return False
        
        return True
    
    def validate(self) -> bool:
        """
        Validate configuration consistency.
        
        Returns:
            True if validation passed, False otherwise
        """
        print("🔍 Validating Configuration Consistency...")
        print("─" * 80)
        
        # Check files exist
        if not self.env_file.exists():
            print("❌ .env file not found")
            return False
        
        if not self.docker_compose_file.exists():
            print("❌ docker-compose.yml file not found")
            return False
        
        # Parse configurations
        env_vars = self.parse_env_file()
        docker_env = self.parse_docker_compose()
        
        if not env_vars:
            print("⚠️  .env file is empty or could not be parsed")
            return False
        
        if not docker_env:
            print("⚠️  docker-compose.yml has no service environments")
            return False
        
        # Validate each service
        validations = [
            ("PostgreSQL", self.validate_postgresql_config(env_vars, docker_env)),
            ("Redis", self.validate_redis_config(env_vars, docker_env)),
            ("Ollama", self.validate_ollama_config(env_vars, docker_env)),
        ]
        
        # Print results
        print()
        for service, passed in validations:
            if passed:
                print(f"✅ {service}: Configuration consistent")
            else:
                print(f"❌ {service}: Configuration mismatch")
        
        # Print issues
        if self.issues:
            print(f"\n❌ Found {len(self.issues)} configuration issues:")
            for issue in self.issues:
                print(f"  • {issue}")
            
            print("\n💡 To fix:")
            print("  1. Update .env to match docker-compose.yml, OR")
            print("  2. Update docker-compose.yml to match .env")
            print("  3. Then run: docker-compose down -v && docker-compose up -d")
        
        # Print warnings
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print("─" * 80)
        
        success = len(self.issues) == 0
        if success:
            print("✅ Configuration validation passed!")
        else:
            print("❌ Configuration validation failed!")
        
        return success


def main():
    """Main entry point for standalone validation."""
    import sys
    
    service_root = Path(__file__).parent.parent.parent
    validator = ConfigValidator(service_root)
    
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

