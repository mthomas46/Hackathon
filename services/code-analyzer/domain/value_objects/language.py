"""Language value object."""

from enum import Enum, auto
from typing import List

from domain.exceptions import UnsupportedLanguageError


class Language(Enum):
    """Supported programming languages."""
    
    PYTHON = auto()
    JAVASCRIPT = auto()
    TYPESCRIPT = auto()
    JAVA = auto()
    GO = auto()
    RUST = auto()
    
    @property
    def extensions(self) -> List[str]:
        """Get file extensions for this language."""
        extensions_map = {
            Language.PYTHON: ['.py', '.pyw'],
            Language.JAVASCRIPT: ['.js', '.mjs'],
            Language.TYPESCRIPT: ['.ts'],
            Language.JAVA: ['.java'],
            Language.GO: ['.go'],
            Language.RUST: ['.rs']
        }
        return extensions_map.get(self, [])
    
    @classmethod
    def from_extension(cls, extension: str) -> 'Language':
        """Detect language from file extension."""
        for language in cls:
            if extension in language.extensions:
                return language
        raise UnsupportedLanguageError(f"Unsupported file extension: {extension}")

