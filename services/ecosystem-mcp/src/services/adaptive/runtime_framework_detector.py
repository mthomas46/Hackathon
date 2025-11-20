"""
Runtime Framework Detector

Detects frameworks and languages from documents when repository context is missing.
This is a fallback for when ingestion didn't create repository_contexts.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class RuntimeFrameworkDetector:
    """
    Detect frameworks and languages by analyzing document file paths.
    
    This is used when repository_contexts is empty or incomplete.
    """
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "Play Framework": [
            r"app/controllers/.*\.scala",
            r"conf/routes",
            r"conf/application\.conf",
            r"build\.sbt",
            r"app/views/.*\.scala\.html"
        ],
        "Spring Boot": [
            r"src/main/java/.*Application\.java",
            r"application\.properties",
            r"application\.yml",
            r"pom\.xml.*spring-boot"
        ],
        "Django": [
            r"manage\.py",
            r".*/settings\.py",
            r".*/urls\.py",
            r"requirements\.txt.*django"
        ],
        "Express.js": [
            r"package\.json.*express",
            r"app\.js",
            r"server\.js",
            r"routes/.*\.js"
        ],
        "Flask": [
            r"app\.py",
            r"wsgi\.py",
            r"requirements\.txt.*flask"
        ],
        "FastAPI": [
            r"main\.py.*fastapi",
            r"requirements\.txt.*fastapi",
            r"app/.*router"
        ]
    }
    
    # Language detection from file extensions
    LANGUAGE_PATTERNS = {
        "Scala": [".scala"],
        "Java": [".java"],
        "Python": [".py"],
        "JavaScript": [".js", ".jsx"],
        "TypeScript": [".ts", ".tsx"],
        "Go": [".go"],
        "Ruby": [".rb"],
        "PHP": [".php"],
        "C#": [".cs"],
        "Kotlin": [".kt"]
    }
    
    def __init__(self):
        """Initialize runtime framework detector."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.compiled_framework_patterns = {}
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            self.compiled_framework_patterns[framework] = [
                re.compile(pattern) for pattern in patterns
            ]
    
    async def detect_from_file_paths(
        self,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Detect frameworks and languages from file paths.
        
        Args:
            file_paths: List of file paths from documents
        
        Returns:
            Dictionary with detected frameworks, languages, and confidence
        """
        if not file_paths:
            logger.warning("No file paths provided for framework detection")
            return {
                "frameworks": [],
                "languages": {},
                "confidence": 0.0,
                "file_count": 0
            }
        
        # Detect frameworks
        framework_scores = {}
        for framework, patterns in self.compiled_framework_patterns.items():
            score = 0
            for pattern in patterns:
                matches = sum(1 for path in file_paths if pattern.search(path))
                score += matches
            if score > 0:
                framework_scores[framework] = score
        
        # Detect languages
        language_counts = Counter()
        for file_path in file_paths:
            for language, extensions in self.LANGUAGE_PATTERNS.items():
                if any(file_path.endswith(ext) for ext in extensions):
                    language_counts[language] += 1
                    break
        
        # Calculate confidence
        total_files = len(file_paths)
        confidence = sum(framework_scores.values()) / max(total_files, 1)
        
        # Get top frameworks
        top_frameworks = sorted(
            framework_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        detected_frameworks = [fw for fw, _ in top_frameworks if _ >= 3]  # At least 3 matches
        
        # Get language percentages
        languages_dict = {
            lang: {
                "count": count,
                "percentage": round(count / total_files * 100, 2)
            }
            for lang, count in language_counts.most_common(10)
        }
        
        result = {
            "frameworks": detected_frameworks,
            "languages": languages_dict,
            "confidence": min(confidence, 1.0),
            "file_count": total_files,
            "primary_language": language_counts.most_common(1)[0][0] if language_counts else "Unknown"
        }
        
        logger.info(
            f"🔍 Runtime framework detection: "
            f"frameworks={detected_frameworks}, "
            f"primary_language={result['primary_language']}, "
            f"confidence={result['confidence']:.2f}"
        )
        
        return result
    
    def get_framework_guidance(self, frameworks: List[str]) -> Dict[str, Any]:
        """
        Get framework-specific guidance for documentation generation.
        
        Args:
            frameworks: List of detected frameworks
        
        Returns:
            Framework-specific patterns and terminology
        """
        if not frameworks:
            return {"guidance": "generic"}
        
        primary_framework = frameworks[0]
        
        guidance_map = {
            "Play Framework": {
                "patterns_to_find": [
                    "controllers",
                    "actions",
                    "routes",
                    "models",
                    "services",
                    "dependency injection"
                ],
                "terminology": {
                    "endpoints": "actions in controllers",
                    "middleware": "filters and action composition",
                    "config": "application.conf",
                    "routing": "routes file"
                },
                "common_patterns": [
                    "Action builders",
                    "Form validation",
                    "Async actions",
                    "WebSockets",
                    "JSON serialization"
                ]
            },
            "Spring Boot": {
                "patterns_to_find": [
                    "@RestController",
                    "@Service",
                    "@Repository",
                    "@Component",
                    "application.properties"
                ],
                "terminology": {
                    "endpoints": "@RequestMapping methods",
                    "config": "application.properties or application.yml"
                }
            },
            "Django": {
                "patterns_to_find": [
                    "views",
                    "models",
                    "urls",
                    "serializers",
                    "settings"
                ],
                "terminology": {
                    "endpoints": "views mapped in urls.py",
                    "config": "settings.py"
                }
            },
            "Express.js": {
                "patterns_to_find": [
                    "routes",
                    "middleware",
                    "controllers",
                    "models"
                ],
                "terminology": {
                    "endpoints": "route handlers",
                    "config": "environment variables"
                }
            }
        }
        
        return guidance_map.get(primary_framework, {"guidance": "generic"})


# Singleton instance
_runtime_detector: Optional[RuntimeFrameworkDetector] = None


def get_runtime_detector() -> RuntimeFrameworkDetector:
    """Get or create singleton runtime detector."""
    global _runtime_detector
    if _runtime_detector is None:
        _runtime_detector = RuntimeFrameworkDetector()
    return _runtime_detector

