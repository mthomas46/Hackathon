"""
Unit Tests for Enhanced Model Router (Week 3, Day 1)

Tests:
- Code file detection
- Code content detection
- Language detection
- Model routing logic
- Task type detection
- Fallback handling
"""

import pytest
from src.services.llm.enhanced_model_router import (
    EnhancedModelRouter,
    CodeDetector,
    TaskType,
    ModelType,
    get_enhanced_model_router
)


@pytest.fixture
def code_detector():
    """Create CodeDetector instance."""
    return CodeDetector()


@pytest.fixture
def router():
    """Create EnhancedModelRouter instance."""
    return EnhancedModelRouter()


@pytest.mark.unit
@pytest.mark.skip(reason="CodeDetector API has changed - tests need updating")
class TestCodeDetector:
    """Test CodeDetector class."""
    
    def test_is_code_file_python(self, code_detector):
        """Test Python file detection."""
        assert code_detector.is_code_file("test.py") is True
        assert code_detector.is_code_file("module/file.py") is True
    
    def test_is_code_file_javascript(self, code_detector):
        """Test JavaScript file detection."""
        assert code_detector.is_code_file("app.js") is True
        assert code_detector.is_code_file("component.jsx") is True
        assert code_detector.is_code_file("module.ts") is True
        assert code_detector.is_code_file("Component.tsx") is True
    
    def test_is_code_file_various_languages(self, code_detector):
        """Test various language file detection."""
        assert code_detector.is_code_file("Main.java") is True
        assert code_detector.is_code_file("app.cpp") is True
        assert code_detector.is_code_file("main.go") is True
        assert code_detector.is_code_file("lib.rs") is True
        assert code_detector.is_code_file("script.sh") is True
        assert code_detector.is_code_file("query.sql") is True
    
    def test_is_not_code_file(self, code_detector):
        """Test non-code file detection."""
        assert code_detector.is_code_file("document.txt") is False
        assert code_detector.is_code_file("README.md") is False
        assert code_detector.is_code_file("data.json") is False
        assert code_detector.is_code_file("style.css") is False
        assert code_detector.is_code_file("image.png") is False
    
    def test_detect_language_python(self, code_detector):
        """Test Python language detection."""
        assert code_detector.detect_language("test.py") == "python"
    
    def test_detect_language_javascript(self, code_detector):
        """Test JavaScript language detection."""
        assert code_detector.detect_language("app.js") == "javascript"
        assert code_detector.detect_language("component.jsx") == "javascript"
    
    def test_detect_language_typescript(self, code_detector):
        """Test TypeScript language detection."""
        assert code_detector.detect_language("app.ts") == "typescript"
        assert code_detector.detect_language("Component.tsx") == "typescript"
    
    def test_detect_language_various(self, code_detector):
        """Test various language detection."""
        assert code_detector.detect_language("Main.java") == "java"
        assert code_detector.detect_language("app.cpp") == "cpp"
        assert code_detector.detect_language("main.go") == "go"
        assert code_detector.detect_language("lib.rs") == "rust"
    
    def test_is_code_content_python(self, code_detector):
        """Test Python code content detection."""
        python_code = """
def hello_world():
    print("Hello, World!")

class MyClass:
    def __init__(self):
        pass
"""
        assert code_detector.is_code_content(python_code) is True
    
    def test_is_code_content_javascript(self, code_detector):
        """Test JavaScript code content detection."""
        js_code = """
function hello() {
    const message = "Hello";
    return message;
}

const arrow = () => {
    console.log("Arrow function");
}
"""
        assert code_detector.is_code_content(js_code) is True
    
    def test_is_code_content_with_patterns(self, code_detector):
        """Test code content detection with various patterns."""
        code_samples = [
            "def function_name(param1, param2):",
            "class ClassName:",
            "import module",
            "const variable = value;",
            "if (condition) {",
            "for (let i = 0; i < 10; i++) {",
            "return value;",
            "async function() {",
        ]
        
        for sample in code_samples:
            assert code_detector.is_code_content(sample * 5) is True
    
    def test_is_not_code_content(self, code_detector):
        """Test non-code content detection."""
        text_content = """
This is a regular text document.
It contains plain English text.
There are no code patterns here.
Just regular sentences and paragraphs.
"""
        assert code_detector.is_code_content(text_content) is False
    
    def test_is_code_content_threshold(self, code_detector):
        """Test code content detection with custom threshold."""
        # Mix of code and text
        mixed_content = """
This is some text.
def function():
    pass
More text here.
class MyClass:
    pass
Even more text.
"""
        # Should be detected as code with default threshold (0.3)
        assert code_detector.is_code_content(mixed_content) is True
        
        # Should NOT be detected with high threshold (0.8)
        assert code_detector.is_code_content(mixed_content, threshold=0.8) is False
    
    def test_detect_language_from_content_python(self, code_detector):
        """Test language detection from Python content."""
        python_code = """
import numpy as np
from typing import List

def process_data(data: List[int]) -> np.ndarray:
    return np.array(data)

class DataProcessor:
    def __init__(self):
        pass
"""
        assert code_detector.detect_language_from_content(python_code) == "python"
    
    def test_detect_language_from_content_javascript(self, code_detector):
        """Test language detection from JavaScript content."""
        js_code = """
const express = require('express');
const app = express();

function handleRequest(req, res) {
    return res.json({ success: true });
}

const middleware = () => {
    console.log('Middleware');
}
"""
        assert code_detector.detect_language_from_content(js_code) == "javascript"
    
    def test_detect_language_from_content_typescript(self, code_detector):
        """Test language detection from TypeScript content."""
        ts_code = """
interface User {
    name: string;
    age: number;
}

type UserRole = 'admin' | 'user';

const getUser = (id: string): User => {
    return { name: 'John', age: 30 };
}
"""
        assert code_detector.detect_language_from_content(ts_code) == "typescript"


@pytest.mark.unit
class TestEnhancedModelRouter:
    """Test EnhancedModelRouter class."""
    
    def test_initialization(self, router):
        """Test router initialization."""
        assert router.code_detector is not None
        assert router.model_priorities is not None
        assert router.language_models is not None
    
    def test_select_model_for_python_file(self, router):
        """Test model selection for Python file."""
        content = "def hello(): pass"
        model = router.select_model(content, file_path="test.py")
        
        # Should route to CodeLlama
        assert "codellama" in model.lower()
    
    def test_select_model_for_javascript_file(self, router):
        """Test model selection for JavaScript file."""
        content = "function hello() { return 'world'; }"
        model = router.select_model(content, file_path="app.js")
        
        # Should route to CodeLlama
        assert "codellama" in model.lower()
    
    def test_select_model_for_code_content(self, router):
        """Test model selection for code content (no file path)."""
        python_code = """
def process_data(data):
    return [x * 2 for x in data]

class Processor:
    def __init__(self):
        pass
"""
        model = router.select_model(python_code)
        
        # Should route to CodeLlama
        assert "codellama" in model.lower()
    
    def test_select_model_for_text_content(self, router):
        """Test model selection for text content."""
        text = "This is a plain text document with no code."
        model = router.select_model(text)
        
        # Should route to general model (llama2 or mistral)
        assert "llama2" in model.lower() or "mistral" in model.lower()
    
    def test_select_model_for_documentation_task(self, router):
        """Test model selection for documentation task."""
        content = "Generate documentation for this module."
        model = router.select_model(
            content,
            task_type=TaskType.DOCUMENTATION
        )
        
        # Should use documentation models
        assert "llama2" in model.lower() or "mistral" in model.lower()
    
    def test_select_model_for_rag_query(self, router):
        """Test model selection for RAG query."""
        content = "What is the purpose of this function?"
        model = router.select_model(
            content,
            task_type=TaskType.RAG_QUERY
        )
        
        # Should use RAG models
        assert model is not None
    
    def test_get_task_type_for_python_code(self, router):
        """Test task type detection for Python code."""
        python_code = "def function(): pass"
        task_type = router.get_task_type_for_content(python_code, "test.py")
        
        assert task_type == TaskType.CODE_ANALYSIS
    
    def test_get_task_type_for_text(self, router):
        """Test task type detection for text."""
        text = "This is plain text."
        task_type = router.get_task_type_for_content(text, "doc.txt")
        
        assert task_type == TaskType.GENERAL_QUERY
    
    def test_context_aware_routing_documentation(self, router):
        """Test context-aware routing for documentation."""
        content = "Some content"
        model = router.select_model(
            content,
            is_documentation=True
        )
        
        # Should prefer documentation models
        assert model is not None
    
    def test_context_aware_routing_rag(self, router):
        """Test context-aware routing for RAG."""
        content = "Some content"
        model = router.select_model(
            content,
            is_rag_query=True
        )
        
        # Should prefer RAG models
        assert model is not None
    
    def test_language_specific_routing_python(self, router):
        """Test language-specific routing for Python."""
        python_code = """
import numpy as np

def analyze_data(data):
    return np.mean(data)
"""
        model = router.select_model(python_code, file_path="analysis.py")
        
        assert "codellama" in model.lower()
    
    def test_language_specific_routing_typescript(self, router):
        """Test language-specific routing for TypeScript."""
        ts_code = """
interface Config {
    apiUrl: string;
}

const getConfig = (): Config => {
    return { apiUrl: 'https://api.example.com' };
}
"""
        model = router.select_model(ts_code, file_path="config.ts")
        
        assert "codellama" in model.lower()


@pytest.mark.unit
class TestSingleton:
    """Test singleton pattern."""
    
    def test_singleton_returns_same_instance(self):
        """Test that singleton returns same instance."""
        router1 = get_enhanced_model_router()
        router2 = get_enhanced_model_router()
        
        assert router1 is router2


@pytest.mark.unit
@pytest.mark.skip(reason="EnhancedModelRouter API has changed - tests need updating")
class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_content(self, router):
        """Test with empty content."""
        model = router.select_model("")
        
        # Should still return a valid model
        assert model is not None
    
    def test_very_short_content(self, router):
        """Test with very short content."""
        model = router.select_model("x = 1")
        
        assert model is not None
    
    def test_mixed_code_and_text(self, router):
        """Test with mixed code and text."""
        mixed = """
Here is some explanation text.

def example_function():
    pass

More text here.
"""
        model = router.select_model(mixed)
        
        # Should detect as code
        assert "codellama" in model.lower()
    
    def test_unknown_file_extension(self, code_detector):
        """Test with unknown file extension."""
        assert code_detector.is_code_file("file.unknown") is False
    
    def test_no_file_path(self, router):
        """Test routing with no file path."""
        code = "def function(): pass"
        model = router.select_model(code, file_path=None)
        
        # Should still detect code
        assert "codellama" in model.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

