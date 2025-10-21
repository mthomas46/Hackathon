"""
Enhanced Model Router with Code Detection (Week 3, Day 1)

Features:
- Automatic code file detection
- Smart routing to CodeLlama for code files
- Fallback to general-purpose models
- Language-specific optimization
- Performance tracking
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Available model types."""
    GENERAL = "general"  # llama2, mistral
    CODE = "code"  # codellama
    EMBEDDING = "embedding"  # nomic-embed-text


class TaskType(Enum):
    """Types of tasks."""
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    RAG_QUERY = "rag_query"
    GENERAL_QUERY = "general_query"


class CodeDetector:
    """
    Detect code files and content.
    
    Uses multiple strategies:
    1. File extension matching
    2. Content pattern detection
    3. Language-specific syntax detection
    """
    
    # Programming language extensions
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.h', '.hpp',
        '.go', '.rs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.cs', '.sh', '.sql',
        '.r', '.m', '.lua', '.pl', '.dart',
        '.vue', '.elm', '.ex', '.exs', '.clj',
        '.jl', '.nim', '.zig', '.v', '.vhdl'
    }
    
    # Common code patterns
    CODE_PATTERNS = [
        r'\bdef\s+\w+\s*\(',  # Python function
        r'\bclass\s+\w+',  # Class definition
        r'\bfunction\s+\w+\s*\(',  # JS function
        r'\b(import|from)\s+\w+',  # Import statement
        r'\b(const|let|var)\s+\w+\s*=',  # JS variable
        r'\b(public|private|protected)\s+',  # Access modifiers
        r'\basync\s+(def|function)',  # Async function
        r'=>\s*\{',  # Arrow function
        r'\bif\s*\(',  # If statement
        r'\bfor\s*\(',  # For loop
        r'\bwhile\s*\(',  # While loop
        r'\breturn\s+',  # Return statement
        r'\bawait\s+',  # Await keyword
        r'\btry\s*\{',  # Try block
        r'^\s*#include\s+[<"]',  # C/C++ include
        r'^\s*package\s+\w+',  # Java/Go package
        r'^\s*namespace\s+\w+',  # C# namespace
    ]
    
    # Language-specific patterns
    LANGUAGE_PATTERNS = {
        'python': [r'\bdef\s+', r'\bclass\s+', r'\bimport\s+', r'\bfrom\s+\w+\s+import'],
        'javascript': [r'\bfunction\s+', r'\bconst\s+', r'\blet\s+', r'=>', r'require\('],
        'typescript': [r'\binterface\s+', r'\btype\s+', r':\s*\w+', r'\bas\s+\w+'],
        'java': [r'\bpublic\s+class', r'\bprivate\s+', r'\bpackage\s+', r'@\w+'],
        'cpp': [r'#include\s+', r'std::', r'\btemplate\s*<', r'\bnamespace\s+'],
        'go': [r'\bpackage\s+', r'\bfunc\s+', r'\btype\s+\w+\s+struct', r'\bgo\s+func'],
        'rust': [r'\bfn\s+', r'\blet\s+mut', r'\bimpl\s+', r'\buse\s+'],
    }
    
    def __init__(self):
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(p) for p in self.CODE_PATTERNS]
        self.compiled_language_patterns = {
            lang: [re.compile(p) for p in patterns]
            for lang, patterns in self.LANGUAGE_PATTERNS.items()
        }
    
    def is_code_file(self, file_path: str) -> bool:
        """
        Check if file is a code file by extension.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file is a code file
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.CODE_EXTENSIONS
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to file
        
        Returns:
            Language name or None
        """
        ext = Path(file_path).suffix.lower()
        
        # Extension to language mapping
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.cs': 'csharp',
            '.sh': 'shell',
            '.sql': 'sql',
        }
        
        return ext_map.get(ext)
    
    def is_code_content(
        self,
        content: str,
        threshold: float = 0.3,
        max_lines: int = 50
    ) -> bool:
        """
        Check if content appears to be code.
        
        Uses pattern matching to detect code-like syntax.
        
        Args:
            content: Content to check
            threshold: Minimum ratio of code patterns (0-1)
            max_lines: Maximum lines to check
        
        Returns:
            True if content appears to be code
        """
        if not content:
            return False
        
        # Split into lines
        lines = content.split('\n')[:max_lines]
        
        if not lines:
            return False
        
        # Count lines with code patterns
        code_line_count = 0
        
        for line in lines:
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue
            
            # Check for code patterns
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    code_line_count += 1
                    break
        
        # Calculate ratio
        non_empty_lines = sum(1 for line in lines if line.strip())
        ratio = code_line_count / non_empty_lines if non_empty_lines > 0 else 0
        
        return ratio >= threshold
    
    def detect_language_from_content(
        self,
        content: str,
        max_lines: int = 50
    ) -> Optional[str]:
        """
        Detect programming language from content.
        
        Args:
            content: Content to analyze
            max_lines: Maximum lines to check
        
        Returns:
            Detected language or None
        """
        lines = content.split('\n')[:max_lines]
        
        # Count pattern matches for each language
        language_scores = {}
        
        for lang, patterns in self.compiled_language_patterns.items():
            score = 0
            for line in lines:
                for pattern in patterns:
                    if pattern.search(line):
                        score += 1
            if score > 0:
                language_scores[lang] = score
        
        # Return language with highest score
        if language_scores:
            return max(language_scores, key=language_scores.get)
        
        return None


class EnhancedModelRouter:
    """
    Enhanced model router with intelligent task routing.
    
    Routes tasks to optimal models based on:
    - Content type (code vs text)
    - Programming language
    - Task complexity
    - Model availability
    - Performance requirements
    """
    
    def __init__(self):
        self.code_detector = CodeDetector()
        self.model_priorities = self._init_priorities()
        self.language_models = self._init_language_models()
        logger.info("EnhancedModelRouter initialized")
    
    def _init_priorities(self) -> Dict[TaskType, List[str]]:
        """Initialize model priorities for each task type."""
        return {
            TaskType.CODE_ANALYSIS: [
                "codellama:13b",
                "codellama:7b",
                "llama2:13b"  # Fallback
            ],
            TaskType.DOCUMENTATION: [
                "llama2:13b",
                "mistral:7b",
                "llama2:7b"
            ],
            TaskType.RAG_QUERY: [
                "llama2:13b",
                "mistral:7b"
            ],
            TaskType.GENERAL_QUERY: [
                "llama2:13b",
                "mistral:7b",
                "llama2:7b"
            ]
        }
    
    def _init_language_models(self) -> Dict[str, List[str]]:
        """Initialize language-specific model preferences."""
        return {
            'python': ['codellama:13b', 'codellama:7b'],
            'javascript': ['codellama:13b', 'codellama:7b'],
            'typescript': ['codellama:13b', 'codellama:7b'],
            'java': ['codellama:13b', 'codellama:7b'],
            'cpp': ['codellama:13b', 'codellama:7b'],
            'go': ['codellama:13b', 'codellama:7b'],
            'rust': ['codellama:13b', 'codellama:7b'],
        }
    
    def select_model(
        self,
        content: str,
        file_path: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        **context
    ) -> str:
        """
        Select optimal model for task.
        
        Args:
            content: Content to process
            file_path: Optional file path for detection
            task_type: Optional explicit task type
            **context: Additional context
        
        Returns:
            Model name to use
        """
        # Detect task type if not provided
        if task_type is None:
            task_type = self._detect_task_type(content, file_path, context)
        
        logger.info(f"🎯 Task type detected: {task_type.value}")
        
        # For code analysis, try to use language-specific preferences
        if task_type == TaskType.CODE_ANALYSIS:
            model = self._select_code_model(content, file_path)
        else:
            # Get model priorities
            priorities = self.model_priorities.get(
                task_type,
                self.model_priorities[TaskType.GENERAL_QUERY]
            )
            model = self._select_available_model(priorities)
        
        logger.info(f"✅ Selected model: {model} for {task_type.value}")
        
        return model
    
    def _detect_task_type(
        self,
        content: str,
        file_path: Optional[str],
        context: Dict[str, Any]
    ) -> TaskType:
        """Detect task type from content and context."""
        
        # Check if it's code
        if file_path and self.code_detector.is_code_file(file_path):
            return TaskType.CODE_ANALYSIS
        
        if self.code_detector.is_code_content(content):
            return TaskType.CODE_ANALYSIS
        
        # Check context for task hints
        if context.get("is_documentation"):
            return TaskType.DOCUMENTATION
        
        if context.get("is_rag_query"):
            return TaskType.RAG_QUERY
        
        return TaskType.GENERAL_QUERY
    
    def _select_code_model(
        self,
        content: str,
        file_path: Optional[str]
    ) -> str:
        """Select model for code analysis."""
        
        # Detect language
        language = None
        
        if file_path:
            language = self.code_detector.detect_language(file_path)
        
        if not language:
            language = self.code_detector.detect_language_from_content(content)
        
        # Get language-specific models
        if language and language in self.language_models:
            priorities = self.language_models[language]
            logger.info(f"📝 Detected language: {language}")
        else:
            priorities = self.model_priorities[TaskType.CODE_ANALYSIS]
        
        return self._select_available_model(priorities)
    
    def _select_available_model(self, priorities: List[str]) -> str:
        """
        Select first available model from priorities.
        
        In production, would check actual model availability.
        For now, returns first priority.
        """
        # TODO: Check Ollama for model availability
        # For now, return first priority
        return priorities[0]
    
    def get_task_type_for_content(
        self,
        content: str,
        file_path: Optional[str] = None
    ) -> TaskType:
        """
        Get task type for content (public API).
        
        Useful for testing and debugging.
        """
        return self._detect_task_type(content, file_path, {})


# Singleton
_router_instance: Optional[EnhancedModelRouter] = None


def get_enhanced_model_router() -> EnhancedModelRouter:
    """Get singleton router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = EnhancedModelRouter()
    return _router_instance

