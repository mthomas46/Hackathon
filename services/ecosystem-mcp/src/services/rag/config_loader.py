"""
Optional RAG configuration loader.

All configs are optional - system works perfectly without them.
"""

import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class GlossaryTerm(BaseModel):
    """Glossary term configuration."""
    term: str
    description: str
    synonyms: list[str] = []
    boost_weight: float = Field(default=1.3, ge=1.0, le=3.0)
    examples: list[str] = []


class ExclusionRule(BaseModel):
    """Document exclusion rule."""
    pattern: str  # Regex pattern
    reason: str
    applies_to_queries: list[str] = ["*"]  # Query types or "*" for all


class QueryTemplate(BaseModel):
    """Pre-optimized query template."""
    description: str = ""  # Human-readable description
    patterns: list[str]  # Regex patterns that match this template
    optimized_sections: list[str]  # Pre-defined sections for multi-pass
    boost_paths: list[str] = []  # File patterns to prioritize
    boost_keywords: list[str] = []  # Keywords to boost
    documents_needed: int = 20  # Override default n_results
    prefer_recent: bool = True  # Whether to boost recent documents


class RAGConfig(BaseModel):
    """
    Complete RAG configuration.
    
    ALL fields are optional with sensible defaults.
    """
    # Feature flags (can disable features)
    features_enabled: Dict[str, bool] = {
        'glossary': False,
        'exclusions': False,
        'templates': False,
        'priorities': False,
        'feedback': False
    }
    
    # Glossary terms
    glossary: Dict[str, GlossaryTerm] = {}
    
    # Exclusion rules
    exclusions: list[ExclusionRule] = []
    
    # Query templates
    templates: Dict[str, QueryTemplate] = {}
    
    # Signal weights (must sum to 1.0)
    signal_weights: Dict[str, float] = {
        'semantic': 0.40,
        'glossary': 0.15,
        'priority': 0.15,
        'content_quality': 0.15,
        'recency': 0.15
    }
    
    @validator('signal_weights')
    def weights_sum_to_one(cls, v):
        """Ensure weights sum to 1.0."""
        total = sum(v.values())
        if not 0.95 <= total <= 1.05:  # Allow small float errors
            raise ValueError(f"Signal weights must sum to 1.0, got {total}")
        return v


class OptionalConfigLoader:
    """
    Loads RAG configs with graceful degradation and smart caching.
    
    Philosophy:
    - No config found? Return None, system uses defaults
    - Invalid config? Log warning, return None
    - Partial config? Use what's valid, ignore invalid parts
    
    Smart Caching:
    - Checks file modification time (mtime) before using cache
    - Reloads immediately if file changed
    - Falls back to 5-minute TTL if file unchanged
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            config_dir: Directory containing .rag-config/ folder
                       If None, uses current working directory
        """
        if config_dir is None:
            # Default: look in repo root
            config_dir = Path.cwd()
        
        self.config_dir = config_dir / ".rag-config"
        self._config_cache: Optional[RAGConfig] = None
        self._cache_timestamp: Optional[float] = None
        self._config_file_mtime: Optional[float] = None
    
    def load_config(self) -> Optional[RAGConfig]:
        """
        Load RAG configuration with smart cache invalidation.
        
        Cache is invalidated if:
        1. Config file modified (check mtime)
        2. TTL expired (5 minutes)
        3. Manual invalidation requested
        
        Returns:
            RAGConfig if found and valid, None otherwise
        """
        config_file = self.config_dir / "config.yaml"
        
        # Check if config directory exists
        if not self.config_dir.exists():
            logger.debug(f"No config directory found: {self.config_dir}")
            return None
        
        if not config_file.exists():
            logger.debug(f"No config file found: {config_file}")
            return None
        
        # Check file modification time
        current_mtime = config_file.stat().st_mtime
        
        # Cache hit conditions:
        # 1. Cache exists
        # 2. File hasn't been modified
        # 3. TTL not expired
        if (
            self._config_cache is not None and
            self._config_file_mtime == current_mtime and
            self._is_cache_valid()
        ):
            logger.debug("Using cached config")
            return self._config_cache
        
        # Cache miss or invalidated - reload
        logger.info("Reloading config (cache invalidated or expired)")
        
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                logger.debug("Config file is empty")
                return None
            
            # Load additional config files if referenced
            if 'glossary_file' in config_data:
                glossary = self._load_glossary_file(
                    self.config_dir / config_data['glossary_file']
                )
                config_data['glossary'] = glossary
            
            if 'exclusions_file' in config_data:
                exclusions = self._load_exclusions_file(
                    self.config_dir / config_data['exclusions_file']
                )
                config_data['exclusions'] = exclusions
            
            if 'templates_file' in config_data:
                templates = self._load_templates_file(
                    self.config_dir / config_data['templates_file']
                )
                config_data['templates'] = templates
            
            # Validate and create config
            config = RAGConfig(**config_data)
            
            # Update cache
            self._config_cache = config
            self._cache_timestamp = time.time()
            self._config_file_mtime = current_mtime
            
            logger.info(
                f"✅ Loaded RAG config: "
                f"glossary={len(config.glossary)} terms, "
                f"exclusions={len(config.exclusions)} rules, "
                f"templates={len(config.templates)}"
            )
            
            return config
        
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to load RAG config: {e}. "
                f"Continuing with default behavior."
            )
            # Keep old cache if reload fails
            return self._config_cache
    
    def _is_cache_valid(self) -> bool:
        """Check if cache TTL is still valid."""
        if self._cache_timestamp is None:
            return False
        
        ttl = 300  # 5 minutes
        age = time.time() - self._cache_timestamp
        return age < ttl
    
    def _load_glossary_file(self, path: Path) -> Dict[str, GlossaryTerm]:
        """Load glossary from separate file."""
        if not path.exists():
            return {}
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            glossary = {}
            for term_name, term_data in data.get('glossary', {}).items():
                try:
                    glossary[term_name] = GlossaryTerm(
                        term=term_name,
                        **term_data
                    )
                except Exception as e:
                    logger.warning(f"Invalid glossary term '{term_name}': {e}")
            
            return glossary
        
        except Exception as e:
            logger.warning(f"Failed to load glossary file {path}: {e}")
            return {}
    
    def _load_exclusions_file(self, path: Path) -> list[ExclusionRule]:
        """Load exclusions from separate file."""
        if not path.exists():
            return []
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            exclusions = []
            for rule_data in data.get('exclusions', []):
                try:
                    exclusions.append(ExclusionRule(**rule_data))
                except Exception as e:
                    logger.warning(f"Invalid exclusion rule: {e}")
            
            return exclusions
        
        except Exception as e:
            logger.warning(f"Failed to load exclusions file {path}: {e}")
            return []
    
    def _load_templates_file(self, path: Path) -> Dict[str, QueryTemplate]:
        """Load query templates from separate file."""
        if not path.exists():
            return {}
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            templates = {}
            for template_name, template_data in data.get('templates', {}).items():
                try:
                    templates[template_name] = QueryTemplate(**template_data)
                except Exception as e:
                    logger.warning(f"Invalid template '{template_name}': {e}")
            
            logger.info(f"✅ Loaded {len(templates)} query templates")
            return templates
        
        except Exception as e:
            logger.warning(f"Failed to load templates file {path}: {e}")
            return {}
    
    def invalidate_cache(self):
        """Manually invalidate cache."""
        logger.info("Cache manually invalidated")
        self._config_cache = None
        self._cache_timestamp = None
        self._config_file_mtime = None
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Feature name (e.g., 'glossary')
        
        Returns:
            True if feature is explicitly enabled, False otherwise
        """
        config = self.load_config()
        if config is None:
            return False
        
        return config.features_enabled.get(feature_name, False)


# Global config loader instance
_config_loader: Optional[OptionalConfigLoader] = None


def get_config_loader() -> OptionalConfigLoader:
    """Get global config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = OptionalConfigLoader()
    return _config_loader


def get_rag_config() -> Optional[RAGConfig]:
    """
    Get RAG configuration (cached).
    
    Returns None if no config exists - this is NORMAL and EXPECTED.
    """
    loader = get_config_loader()
    return loader.load_config()


def invalidate_config_cache():
    """
    Manually invalidate config cache.
    
    Call this when config is updated through API.
    """
    global _config_loader
    if _config_loader:
        _config_loader.invalidate_cache()

