#!/usr/bin/env python3
"""
Docker Compose Generator with Centralized Port Management

This script generates Docker Compose configurations from the centralized
service port registry, ensuring consistency and preventing port conflicts.
"""

import yaml
import os
import sys
from pathlib import Path

class DockerComposeGenerator:
    def __init__(self, config_path="config/service-ports.yaml"):
        self.config_path = Path(config_path)
        self.load_port_config()
        
    def load_port_config(self):
        """Load the centralized port configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Port config not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def get_service_ports(self, service_name):
        """Get port mapping for a service"""
        for category in ['core_services', 'ai_services', 'agent_services', 
                        'analysis_services', 'utility_services', 'web_services']:
            services = self.config.get(category, {})
            if service_name in services:
                service_config = services[service_name]
                return {
                    'internal': service_config['internal_port'],
                    'external': service_config['external_port'],
                    'description': service_config['description']
                }
        return None
        
    def generate_service_block(self, service_name, dockerfile_path, dependencies=None, profiles=None):
        """Generate a Docker Compose service block with standardized configuration"""
        port_config = self.get_service_ports(service_name)
        if not port_config:
            raise ValueError(f"No port configuration found for service: {service_name}")
            
        service_block = {
            'build': {
                'context': '.',
                'dockerfile': dockerfile_path
            },
            'environment': [
                'PYTHONPATH=/app',
                f'SERVICE_PORT={port_config["internal"]}',
                'ENVIRONMENT=development'
            ],
            'ports': [
                f'{port_config["external"]}:{port_config["internal"]}'
            ],
            'healthcheck': {
                'test': [
                    'CMD', 'curl', '-f', 
                    f'http://localhost:{port_config["internal"]}/health'
                ],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        }
        
        # Add dependencies if specified
        if dependencies:
            service_block['depends_on'] = {}
            for dep in dependencies:
                service_block['depends_on'][dep] = {'condition': 'service_healthy'}
                
        # Add profiles if specified
        if profiles:
            service_block['profiles'] = profiles
            
        return service_block
    
    def generate_port_validation_script(self):
        """Generate a script to validate port configurations"""
        validation_script = '''#!/bin/bash
# Port Configuration Validation Script
# Automatically generated from service-ports.yaml

echo "🔍 Validating Service Port Configurations..."

ERRORS=0

# Check for port conflicts
declare -A EXTERNAL_PORTS
declare -A INTERNAL_PORTS

'''
        
        # Add port conflict checking
        for category in ['core_services', 'ai_services', 'agent_services', 
                        'analysis_services', 'utility_services', 'web_services']:
            services = self.config.get(category, {})
            for service_name, config in services.items():
                external_port = config['external_port']
                internal_port = config['internal_port']
                
                validation_script += f'''
# {service_name} - {config['description']}
if [[ -n "${{EXTERNAL_PORTS[{external_port}]}}" ]]; then
    echo "❌ ERROR: External port {external_port} conflict between {service_name} and ${{EXTERNAL_PORTS[{external_port}]}}"
    ERRORS=$((ERRORS + 1))
else
    EXTERNAL_PORTS[{external_port}]="{service_name}"
fi

if [[ -n "${{INTERNAL_PORTS[{internal_port}]}}" ]]; then
    echo "⚠️  WARNING: Internal port {internal_port} conflict between {service_name} and ${{INTERNAL_PORTS[{internal_port}]}}"
fi
INTERNAL_PORTS[{internal_port}]="{service_name}"
'''

        validation_script += '''
if [ $ERRORS -eq 0 ]; then
    echo "✅ All port configurations are valid!"
    exit 0
else
    echo "❌ Found $ERRORS port configuration errors!"
    exit 1
fi
'''
        
        return validation_script
    
    def generate_environment_template(self):
        """Generate environment variable template"""
        env_template = "# Environment Variables Template\n"
        env_template += "# Generated from centralized service configuration\n\n"
        
        # Add standard environment variables
        standards = self.config.get('environment_standards', {})
        env_template += "# Standard Environment Variables\n"
        for var_name, var_desc in standards.items():
            env_template += f"# {var_name.upper()}={var_desc}\n"
            
        env_template += "\n# Service-Specific Variables\n"
        
        # Add service-specific environment variables
        for category in ['core_services', 'ai_services', 'agent_services', 
                        'analysis_services', 'utility_services', 'web_services']:
            services = self.config.get(category, {})
            env_template += f"\n# {category.replace('_', ' ').title()}\n"
            
            for service_name, config in services.items():
                service_upper = service_name.upper().replace('-', '_')
                env_template += f"{service_upper}_PORT={config['external_port']}\n"
                env_template += f"{service_upper}_INTERNAL_PORT={config['internal_port']}\n"
                
        return env_template
    
    def generate_makefile_targets(self):
        """Generate Makefile targets for service management"""
        makefile = """# Makefile targets for service management
# Generated from centralized service configuration

.PHONY: validate-ports start-core start-ai start-analysis start-all

validate-ports:
	@echo "🔍 Validating port configurations..."
	@chmod +x scripts/docker/validate-ports.sh
	@scripts/docker/validate-ports.sh

"""
        
        # Add service category targets
        categories = {
            'core': 'core_services',
            'ai': 'ai_services', 
            'analysis': 'analysis_services',
            'agents': 'agent_services',
            'utility': 'utility_services'
        }
        
        for target, category in categories.items():
            services = self.config.get(category, {})
            service_names = ' '.join(services.keys())
            
            makefile += f"""start-{target}:
	@echo "🚀 Starting {target} services..."
	@docker-compose -f docker-compose.dev.yml up -d {service_names}

stop-{target}:
	@echo "🛑 Stopping {target} services..."
	@docker-compose -f docker-compose.dev.yml stop {service_names}

restart-{target}: stop-{target} start-{target}

"""
        
        return makefile

def main():
    """Main function to generate all configuration files"""
    generator = DockerComposeGenerator()
    
    # Create output directory
    output_dir = Path("scripts/docker")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate port validation script
    validation_script = generator.generate_port_validation_script()
    with open(output_dir / "validate-ports.sh", 'w') as f:
        f.write(validation_script)
    os.chmod(output_dir / "validate-ports.sh", 0o755)
    
    # Generate environment template
    env_template = generator.generate_environment_template()
    with open("config/service-ports.env.template", 'w') as f:
        f.write(env_template)
    
    # Generate Makefile targets
    makefile_targets = generator.generate_makefile_targets()
    with open("scripts/docker/service-targets.mk", 'w') as f:
        f.write(makefile_targets)
    
    print("✅ Generated standardized Docker configuration files:")
    print("   - scripts/docker/validate-ports.sh")
    print("   - config/service-ports.env.template") 
    print("   - scripts/docker/service-targets.mk")
    print("")
    print("🔧 To use these configurations:")
    print("   1. Run: make validate-ports")
    print("   2. Include service-targets.mk in your main Makefile")
    print("   3. Use the port config in your docker-compose files")

if __name__ == "__main__":
    main()
