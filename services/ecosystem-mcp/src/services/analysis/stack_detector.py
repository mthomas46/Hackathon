"""
Technology Stack Detector

Detects languages, frameworks, databases, and tools used in a repository.
"""

import logging
import re
from typing import List, Dict, Set, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TechnologyStack:
    """Complete technology stack for a repository."""
    languages: Dict[str, int]  # language -> file count
    frameworks: Dict[str, List[str]]  # framework -> files where detected
    databases: List[str]
    tools: List[str]
    deployment: List[str]
    testing: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class TechnologyStackDetector:
    """
    Detects all technologies used in a repository.
    
    Features:
    - Language detection (from extensions and content)
    - Framework detection (pattern-based)
    - Database detection (connection strings, imports)
    - Tool detection (config files)
    - Deployment platform detection (Docker, K8s, etc.)
    """
    
    def __init__(self):
        # Framework detection patterns by language
        self.framework_patterns = {
            'python': {
                'fastapi': [r'from fastapi', r'import fastapi', r'FastAPI\('],
                'flask': [r'from flask', r'import flask', r'Flask\('],
                'django': [r'django\.conf', r'INSTALLED_APPS', r'from django'],
                'sqlalchemy': [r'from sqlalchemy', r'create_engine', r'declarative_base'],
                'pydantic': [r'from pydantic', r'BaseModel'],
                'pytest': [r'import pytest', r'def test_'],
                'celery': [r'from celery', r'import celery'],
                'asyncio': [r'import asyncio', r'async def'],
                'pandas': [r'import pandas', r'pd\.DataFrame'],
                'numpy': [r'import numpy', r'np\.array'],
                'tensorflow': [r'import tensorflow', r'tf\.'],
                'pytorch': [r'import torch', r'nn\.Module'],
                'streamlit': [r'import streamlit', r'st\.'],
            },
            'javascript': {
                'react': [r'import React', r'from ["\']react["\']', r'useState', r'useEffect'],
                'vue': [r'import Vue', r'new Vue\(', r'createApp'],
                'angular': [r'@angular/', r'@Component', r'@Injectable'],
                'express': [r'require\(["\']express["\']\)', r'from ["\']express["\']'],
                'nextjs': [r'next/router', r'getServerSideProps', r'getStaticProps'],
                'nestjs': [r'@nestjs/', r'@Module\(', r'@Controller\('],
                'jest': [r'describe\(', r'it\(', r'expect\('],
                'webpack': [r'webpack\.config', r'module\.exports'],
            },
            'typescript': {
                'react': [r'import React', r'from ["\']react["\']', r'FC<', r'React\.FC'],
                'angular': [r'@angular/', r'@Component', r'@Injectable'],
                'nestjs': [r'@nestjs/', r'@Module\(', r'@Controller\('],
                'express': [r'from ["\']express["\']'],
            },
            'go': {
                'gin': [r'"github\.com/gin-gonic/gin"'],
                'echo': [r'"github\.com/labstack/echo"'],
                'fiber': [r'"github\.com/gofiber/fiber"'],
                'gorm': [r'"gorm\.io/gorm"'],
            },
            'java': {
                'spring': [r'@SpringBootApplication', r'@RestController', r'springframework'],
                'hibernate': [r'@Entity', r'@Table', r'hibernate'],
            },
            'rust': {
                'actix': [r'actix_web', r'HttpServer'],
                'rocket': [r'use rocket', r'#\[get\('],
            }
        }
        
        # Database patterns
        self.database_patterns = {
            'postgresql': [
                r'postgres://', r'postgresql://', r'psycopg2', r'asyncpg',
                r'DATABASE_URL.*postgres', r'pg\.Pool'
            ],
            'mysql': [
                r'mysql://', r'pymysql', r'mysql\.connector',
                r'DATABASE_URL.*mysql'
            ],
            'mongodb': [
                r'mongodb://', r'pymongo', r'mongoose', r'MongoClient'
            ],
            'redis': [
                r'redis://', r'import redis', r'RedisClient', r'ioredis'
            ],
            'sqlite': [
                r'sqlite://', r'sqlite3', r'\.db$', r'\.sqlite$'
            ],
            'elasticsearch': [
                r'elasticsearch', r'elastic\.co', r'ElasticsearchClient'
            ],
            'dynamodb': [
                r'dynamodb', r'boto3.*dynamodb', r'AWS\.DynamoDB'
            ],
        }
        
        # Tool patterns (from config files)
        self.tool_files = {
            'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'kubernetes': ['deployment.yaml', 'service.yaml', 'ingress.yaml', 'k8s/'],
            'terraform': ['.tf', 'terraform.tfvars'],
            'ansible': ['playbook.yml', 'ansible.cfg'],
            'git': ['.git/', '.gitignore', '.gitattributes'],
            'npm': ['package.json', 'package-lock.json'],
            'yarn': ['yarn.lock'],
            'pip': ['requirements.txt', 'Pipfile', 'setup.py'],
            'poetry': ['pyproject.toml', 'poetry.lock'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle'],
            'cargo': ['Cargo.toml'],
            'make': ['Makefile'],
            'cmake': ['CMakeLists.txt'],
        }
        
        # Deployment platform patterns
        self.deployment_patterns = {
            'aws': [r'aws-sdk', r'boto3', r'amazonaws\.com', r'AWS::'],
            'gcp': [r'google-cloud', r'googleapis\.com', r'gcloud'],
            'azure': [r'azure-', r'microsoft\.azure', r'azurewebsites'],
            'heroku': [r'heroku', r'Procfile'],
            'vercel': [r'vercel\.json', r'@vercel/'],
            'netlify': [r'netlify\.toml', r'_redirects'],
            'railway': [r'railway\.json', r'railway\.toml'],
        }
        
        logger.info("TechnologyStackDetector initialized")
    
    async def detect_stack(self, files: List[Dict], repo_path: str) -> TechnologyStack:
        """
        Detect complete technology stack.
        
        Args:
            files: List of file information dictionaries
            repo_path: Repository root path
        
        Returns:
            TechnologyStack with all detected technologies
        """
        logger.info(f"🔍 Detecting technology stack for {len(files)} files...")
        
        languages = defaultdict(int)
        frameworks = defaultdict(list)
        databases = set()
        tools = set()
        deployment = set()
        testing = set()
        
        # Detect from files
        for file_info in files:
            # Language detection
            language = file_info.get('language', '').lower()
            if language and language != 'unknown':
                languages[language] += 1
            
            # Skip non-code files for framework detection
            if not file_info.get('is_code', False):
                continue
            
            file_path = file_info.get('path') or file_info.get('relative_path', '')
            if not file_path:
                continue
            
            try:
                full_path = Path(repo_path) / file_path
                if not full_path.exists() or full_path.stat().st_size > 1_000_000:
                    continue
                
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                # Detect frameworks
                if language in self.framework_patterns:
                    for framework, patterns in self.framework_patterns[language].items():
                        for pattern in patterns:
                            if re.search(pattern, content):
                                frameworks[framework].append(file_path)
                                break
                
                # Detect databases
                for db, patterns in self.database_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            databases.add(db)
                            break
                
                # Detect deployment platforms
                for platform, patterns in self.deployment_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            deployment.add(platform)
                            break
                
            except Exception as e:
                logger.debug(f"Error analyzing {file_path}: {e}")
        
        # Detect tools from file names
        for file_info in files:
            file_path = file_info.get('path') or file_info.get('relative_path', '')
            
            for tool, patterns in self.tool_files.items():
                for pattern in patterns:
                    if pattern in file_path or file_path.endswith(pattern):
                        tools.add(tool)
                        break
        
        # Detect testing frameworks
        test_tools = self._detect_testing_frameworks(frameworks, tools)
        testing.update(test_tools)
        
        stack = TechnologyStack(
            languages=dict(languages),
            frameworks={k: list(set(v[:5])) for k, v in frameworks.items()},  # Limit to 5 examples
            databases=sorted(list(databases)),
            tools=sorted(list(tools)),
            deployment=sorted(list(deployment)),
            testing=sorted(list(testing))
        )
        
        logger.info(
            f"✅ Stack detection complete: {len(languages)} languages, "
            f"{len(frameworks)} frameworks, {len(databases)} databases"
        )
        
        return stack
    
    def _detect_testing_frameworks(
        self,
        frameworks: Dict[str, List[str]],
        tools: Set[str]
    ) -> Set[str]:
        """
        Detect testing frameworks.
        
        Args:
            frameworks: Detected frameworks
            tools: Detected tools
        
        Returns:
            Set of testing framework names
        """
        testing = set()
        
        # From frameworks
        test_frameworks = {'pytest', 'jest', 'mocha', 'jasmine', 'junit'}
        for fw in test_frameworks:
            if fw in frameworks:
                testing.add(fw)
        
        # From tools
        if 'npm' in tools:
            testing.add('jest')  # Common default
        
        return testing
    
    async def get_primary_language(self, stack: TechnologyStack) -> Optional[str]:
        """
        Get the primary language (most files).
        
        Args:
            stack: Technology stack
        
        Returns:
            Primary language name or None
        """
        if not stack.languages:
            return None
        
        return max(stack.languages.items(), key=lambda x: x[1])[0]
    
    async def get_framework_summary(self, stack: TechnologyStack) -> Dict[str, int]:
        """
        Get framework summary with counts.
        
        Args:
            stack: Technology stack
        
        Returns:
            Dictionary of framework -> usage count
        """
        return {fw: len(files) for fw, files in stack.frameworks.items()}
    
    async def is_polyglot(self, stack: TechnologyStack, threshold: int = 3) -> bool:
        """
        Check if repository is polyglot (multiple languages).
        
        Args:
            stack: Technology stack
            threshold: Minimum languages to be considered polyglot
        
        Returns:
            True if polyglot
        """
        return len(stack.languages) >= threshold
    
    async def get_architecture_hints(self, stack: TechnologyStack) -> List[str]:
        """
        Get architecture hints from stack.
        
        Args:
            stack: Technology stack
        
        Returns:
            List of architecture hints
        """
        hints = []
        
        # Microservices indicators
        if 'docker' in stack.tools and 'kubernetes' in stack.tools:
            hints.append('microservices')
        
        # API indicators
        api_frameworks = {'fastapi', 'flask', 'express', 'gin', 'actix'}
        if any(fw in stack.frameworks for fw in api_frameworks):
            hints.append('api-driven')
        
        # Frontend indicators
        frontend_frameworks = {'react', 'vue', 'angular'}
        if any(fw in stack.frameworks for fw in frontend_frameworks):
            hints.append('spa-frontend')
        
        # Monolith indicators
        if 'django' in stack.frameworks or 'spring' in stack.frameworks:
            hints.append('monolithic')
        
        # Data-intensive indicators
        if len(stack.databases) > 2:
            hints.append('data-intensive')
        
        # Cloud-native indicators
        if stack.deployment:
            hints.append('cloud-native')
        
        return hints


# Singleton
_stack_detector_instance = None

def get_stack_detector() -> TechnologyStackDetector:
    """Get singleton technology stack detector instance."""
    global _stack_detector_instance
    if _stack_detector_instance is None:
        _stack_detector_instance = TechnologyStackDetector()
    return _stack_detector_instance

