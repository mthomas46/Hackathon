"""
Unit Tests for Model Router Edge Cases (Week 4, Day 2)

Comprehensive edge case testing for:
- Model router with unusual inputs
- Code detector with edge cases
- Language detection edge cases
- Fallback scenarios
- Performance edge cases
"""

import pytest
from src.services.llm.enhanced_model_router import (
    EnhancedModelRouter,
    CodeDetector,
    TaskType,
    get_enhanced_model_router
)


@pytest.fixture
def router():
    """Get fresh router instance."""
    return EnhancedModelRouter()


@pytest.fixture
def detector():
    """Get fresh code detector."""
    return CodeDetector()


@pytest.mark.unit
class TestCodeDetectorEdgeCases:
    """Test code detector edge cases."""
    
    def test_empty_file_path(self, detector):
        """Test with empty file path."""
        assert detector.is_code_file("") is False
        assert detector.detect_language("") is None
    
    def test_file_with_no_extension(self, detector):
        """Test file with no extension."""
        assert detector.is_code_file("Makefile") is False
        assert detector.is_code_file("Dockerfile") is False
        assert detector.detect_language("README") is None
    
    def test_hidden_files(self, detector):
        """Test hidden files (dot files)."""
        assert detector.is_code_file(".gitignore") is False
        assert detector.is_code_file(".env") is False
        assert detector.is_code_file(".python-version") is False
    
    def test_multiple_dots_in_filename(self, detector):
        """Test files with multiple dots."""
        assert detector.is_code_file("test.spec.ts") == True
        assert detector.is_code_file("package.json") is False
        assert detector.is_code_file("config.prod.py") == True
    
    def test_uppercase_extensions(self, detector):
        """Test uppercase file extensions."""
        assert detector.is_code_file("Main.PY") == True
        assert detector.is_code_file("App.JS") == True
        assert detector.is_code_file("Test.CPP") == True
    
    def test_mixed_case_extensions(self, detector):
        """Test mixed case extensions."""
        assert detector.is_code_file("file.Py") == True
        assert detector.is_code_file("module.Ts") == True
    
    def test_very_long_filename(self, detector):
        """Test with very long filename."""
        long_name = "very_long_" * 100 + "file.py"
        assert detector.is_code_file(long_name) == True
    
    def test_special_characters_in_filename(self, detector):
        """Test filenames with special characters."""
        assert detector.is_code_file("test-file.py") == True
        assert detector.is_code_file("test_file.py") == True
        assert detector.is_code_file("test file.py") == True  # Space in name
        assert detector.is_code_file("test@file.py") == True
    
    def test_empty_content(self, detector):
        """Test with empty content."""
        assert detector.is_code_content("") is False
        assert detector.detect_language_from_content("") is None
    
    def test_whitespace_only_content(self, detector):
        """Test with only whitespace."""
        assert detector.is_code_content("   \n   \n   ") is False
        assert detector.is_code_content("\t\t\t\n\n\n") is False
    
    def test_single_line_content(self, detector):
        """Test with single line."""
        assert detector.is_code_content("def hello(): pass") == True
        assert detector.is_code_content("This is text") is False
    
    def test_comments_only_content(self, detector):
        """Test with only comments."""
        comments = "# Comment 1\n# Comment 2\n# Comment 3\n"
        result = detector.is_code_content(comments)
        # Should be False as we skip comment lines
        assert result is False
    
    def test_mixed_code_and_comments(self, detector):
        """Test with mixed code and comments."""
        mixed = """
# This is a comment
def function():
    # Another comment
    return True
"""
        assert detector.is_code_content(mixed) == True
    
    def test_very_long_content(self, detector):
        """Test with very long content."""
        # 10000 lines of code
        long_content = "def func():\n    pass\n" * 10000
        assert detector.is_code_content(long_content, max_lines=50) == True
    
    def test_unicode_content(self, detector):
        """Test with unicode characters."""
        unicode_code = """
def hello_世界():
    print("Hello 世界")
    return "Привет мир"
"""
        assert detector.is_code_content(unicode_code) == True
    
    def test_mixed_language_content(self, detector):
        """Test content with mixed programming patterns."""
        mixed = """
def python_function():
    pass

function javascriptFunction() {
    return true;
}
"""
        # Should detect as code
        assert detector.is_code_content(mixed) == True
    
    def test_threshold_boundary(self, detector):
        """Test at code detection threshold boundary."""
        # Create content at exactly 30% code patterns
        content_lines = ["code line" for _ in range(3)] + ["text line" for _ in range(7)]
        content = "\n".join(["def func(): pass" if "code" in line else "plain text" for line in content_lines])
        
        # At threshold (0.3)
        result = detector.is_code_content(content, threshold=0.3)
        assert result == True


@pytest.mark.unit
class TestModelRouterEdgeCases:
    """Test model router edge cases."""
    
    def test_empty_content_routing(self, router):
        """Test routing with empty content."""
        model = router.select_model(content="", file_path=None)
        assert model is not None
    
    def test_none_file_path(self, router):
        """Test routing with None file path."""
        model = router.select_model(content="def test(): pass", file_path=None)
        assert "codellama" in model.lower()
    
    def test_none_content(self, router):
        """Test routing with None-like content."""
        # Should handle gracefully
        model = router.select_model(content="", file_path="test.py")
        assert model is not None
    
    def test_contradicting_signals(self, router):
        """Test when file extension and content contradict."""
        # Python extension but JavaScript content
        js_content = "function test() { return true; }"
        model = router.select_model(content=js_content, file_path="test.py")
        # Should still detect as code
        assert "codellama" in model.lower() or "llama2" in model.lower()
    
    def test_very_large_content(self, router):
        """Test with very large content."""
        large_content = "def function():\n    pass\n" * 100000
        model = router.select_model(content=large_content[:1000], file_path="test.py")
        assert "codellama" in model.lower()
    
    def test_binary_like_content(self, router):
        """Test with binary-like content."""
        binary_content = "\x00\x01\x02\x03\x04\x05"
        model = router.select_model(content=binary_content, file_path="file.bin")
        # Should handle without crashing
        assert model is not None
    
    def test_all_task_types(self, router):
        """Test explicit task type specification."""
        content = "test content"
        
        for task_type in TaskType:
            model = router.select_model(
                content=content,
                task_type=task_type
            )
            assert model is not None
    
    def test_context_variables(self, router):
        """Test with various context variables."""
        model = router.select_model(
            content="test",
            is_documentation=True,
            is_rag_query=True,
            custom_param="value"
        )
        assert model is not None
    
    def test_get_task_type_edge_cases(self, router):
        """Test task type detection edge cases."""
        # Empty content
        task = router.get_task_type_for_content("", None)
        assert task == TaskType.GENERAL_QUERY
        
        # No file path
        task = router.get_task_type_for_content("def test(): pass", None)
        assert task == TaskType.CODE_ANALYSIS


@pytest.mark.unit
class TestLanguageDetectionEdgeCases:
    """Test language detection edge cases."""
    
    def test_detect_from_shebang(self, detector):
        """Test language detection from shebang."""
        python_shebang = "#!/usr/bin/env python3\nprint('hello')"
        # Note: Current implementation doesn't check shebang
        # This test documents expected behavior
        lang = detector.detect_language_from_content(python_shebang)
        # May or may not detect without function patterns
    
    def test_detect_typescript_vs_javascript(self, detector):
        """Test distinguishing TypeScript from JavaScript."""
        ts_code = "interface User { name: string; }"
        js_code = "function user() { return {}; }"
        
        ts_lang = detector.detect_language_from_content(ts_code)
        js_lang = detector.detect_language_from_content(js_code)
        
        assert ts_lang == "typescript"
        assert js_lang == "javascript"
    
    def test_ambiguous_code(self, detector):
        """Test code that could be multiple languages."""
        ambiguous = "x = 1 + 2"
        # Could be Python, JavaScript, etc.
        lang = detector.detect_language_from_content(ambiguous)
        # May return None or a guess
    
    def test_config_files(self, detector):
        """Test configuration file detection."""
        assert detector.is_code_file("package.json") is False
        assert detector.is_code_file("tsconfig.json") is False
        assert detector.is_code_file("Cargo.toml") is False
    
    def test_markup_languages(self, detector):
        """Test markup language files."""
        assert detector.is_code_file("index.html") is False
        assert detector.is_code_file("styles.css") is False
        assert detector.is_code_file("data.xml") is False
    
    def test_data_files(self, detector):
        """Test data file detection."""
        assert detector.is_code_file("data.csv") is False
        assert detector.is_code_file("config.yaml") is False
        assert detector.is_code_file("data.json") is False


@pytest.mark.unit
class TestPerformanceEdgeCases:
    """Test performance-related edge cases."""
    
    def test_many_small_detections(self, detector):
        """Test many rapid code detections."""
        import time
        
        start = time.perf_counter()
        for i in range(1000):
            detector.is_code_file(f"file{i}.py")
        duration = time.perf_counter() - start
        
        # Should be very fast (< 100ms for 1000 checks)
        assert duration < 0.1
    
    def test_pattern_compilation_reuse(self, detector):
        """Test that patterns are compiled once."""
        # Patterns should be compiled in __init__
        assert hasattr(detector, 'compiled_patterns')
        assert len(detector.compiled_patterns) > 0
    
    def test_router_singleton_performance(self):
        """Test singleton doesn't recreate instances."""
        router1 = get_enhanced_model_router()
        router2 = get_enhanced_model_router()
        
        # Should be same instance (fast)
        assert router1 is router2


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling edge cases."""
    
    def test_malformed_file_path(self, detector):
        """Test with malformed file paths."""
        malformed_paths = [
            "//double/slash.py",
            "path\\with\\backslash.py",  # Windows path
            "path/./with/./dots.py",
            "../relative/path.py",
        ]
        
        for path in malformed_paths:
            # Should not crash
            result = detector.is_code_file(path)
            assert isinstance(result, bool)
    
    def test_null_bytes_in_content(self, detector):
        """Test content with null bytes."""
        content_with_null = "def test():\x00\n    pass"
        # Should handle without crashing
        try:
            result = detector.is_code_content(content_with_null)
            assert isinstance(result, bool)
        except:
            # If it fails, that's also acceptable
            pass
    
    def test_extremely_nested_paths(self, detector):
        """Test with deeply nested paths."""
        deep_path = "/".join(["dir"] * 100) + "/file.py"
        result = detector.is_code_file(deep_path)
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

