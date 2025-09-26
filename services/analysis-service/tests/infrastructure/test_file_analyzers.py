"""Tests for file analyzers."""

import pytest
from infrastructure.analysis_services.file_analyzers import (
    analyze_js_file,
    analyze_java_file,
    _extract_function_name_js,
    _is_js_function_definition,
    _check_js_complexity,
    _extract_method_name_java,
    _is_java_method_definition,
    _check_java_complexity,
)


class TestJavaScriptAnalyzer:
    """Test JavaScript file analysis functions."""

    def test_extract_function_name_js_function(self):
        """Test extracting function name from function declaration."""
        line = "function myFunction(param1, param2) {"
        result = _extract_function_name_js(line, 10)
        assert result == "myFunction"

    def test_extract_function_name_js_arrow(self):
        """Test extracting function name from arrow function."""
        line = "const myArrow = (param) => {"
        result = _extract_function_name_js(line, 10)
        assert result == "anonymous_function_10"

    def test_is_js_function_definition_function(self):
        """Test detecting function definition."""
        assert _is_js_function_definition("function test() {")
        assert _is_js_function_definition("const arrow = () => {")
        assert not _is_js_function_definition("let x = 5;")

    def test_check_js_complexity_simple(self):
        """Test simple JavaScript complexity check."""
        issues = {"complex_functions": []}
        _check_js_complexity("let x = 5;", "testFunc", 10, issues)
        assert len(issues["complex_functions"]) == 0

    def test_check_js_complexity_complex(self):
        """Test complex JavaScript complexity check."""
        issues = {"complex_functions": []}
        line = "if (condition && other && third && fourth && fifth) {"
        _check_js_complexity(line, "testFunc", 10, issues)
        assert len(issues["complex_functions"]) == 1
        assert "testFunc (line 11)" in issues["complex_functions"][0]

    def test_analyze_js_file_simple(self):
        """Test analyzing simple JavaScript file."""
        lines = [
            "function simpleFunc() {",
            "    return true;",
            "}",
        ]
        result = analyze_js_file(lines)
        assert "complex_functions" in result
        assert "long_methods" in result
        assert len(result["long_methods"]) == 0  # Function is short

    def test_analyze_js_file_complex(self):
        """Test analyzing complex JavaScript file."""
        lines = [
            "function complexFunc() {",
            "    if (a && b && c && d && e) {",
            "        console.log('complex');",
            "    }",
        ]
        # Add enough lines to make it a long method (>40 lines)
        for i in range(38):  # 3 lines above + 38 = 41 lines
            lines.append("    console.log('line');")
        lines.append("}")

        result = analyze_js_file(lines)
        assert len(result["complex_functions"]) > 0
        assert len(result["long_methods"]) > 0


class TestJavaAnalyzer:
    """Test Java file analysis functions."""

    def test_extract_method_name_java_public(self):
        """Test extracting method name from public method."""
        line = "public void myMethod(String param) {"
        result = _extract_method_name_java(line, 10)
        assert result == "myMethod"

    def test_extract_method_name_java_private(self):
        """Test extracting method name from private method."""
        line = "private int calculate(String input) {"
        result = _extract_method_name_java(line, 10)
        assert result == "calculate"

    def test_extract_method_name_java_no_match(self):
        """Test method name extraction with no match."""
        line = "public class MyClass {"
        result = _extract_method_name_java(line, 10)
        assert result == "method_10"

    def test_is_java_method_definition_public(self):
        """Test detecting public method definition."""
        assert _is_java_method_definition("public void test(String s) {")
        assert _is_java_method_definition("private int calculate() {")
        assert _is_java_method_definition("protected boolean validate() {")
        assert not _is_java_method_definition("public class Test {")

    def test_check_java_complexity_simple(self):
        """Test simple Java complexity check."""
        issues = {"complex_functions": []}
        _check_java_complexity("int x = 5;", "testMethod", 10, issues)
        assert len(issues["complex_functions"]) == 0

    def test_check_java_complexity_complex(self):
        """Test complex Java complexity check."""
        issues = {"complex_functions": []}
        line = "if (condition && other && third && fourth) {"
        _check_java_complexity(line, "testMethod", 10, issues)
        assert len(issues["complex_functions"]) == 1
        assert "testMethod (line 11)" in issues["complex_functions"][0]

    def test_analyze_java_file_simple(self):
        """Test analyzing simple Java file."""
        lines = [
            "public class Test {",
            "    public void simpleMethod() {",
            "        System.out.println(\"Hello\");",
            "    }",
            "}",
        ]
        result = analyze_java_file(lines)
        assert "complex_functions" in result
        assert "long_methods" in result

    def test_analyze_java_file_complex(self):
        """Test analyzing complex Java file."""
        lines = [
            "public class Complex {",
            "    public void complexMethod() {",
            "        if (a && b && c && d && e) {",
            "            System.out.println(\"complex\");",
            "        }",
        ]
        # Add enough lines to make it a long method (>50 lines)
        for i in range(48):  # 4 lines above + 48 = 52 lines
            lines.append("        System.out.println(\"line\");")
        lines.append("    }")
        lines.append("}")

        result = analyze_java_file(lines)
        assert len(result["complex_functions"]) > 0
        assert len(result["long_methods"]) > 0


class TestFileAnalyzerIntegration:
    """Integration tests for file analyzers."""

    def test_js_analyzer_empty_file(self):
        """Test JavaScript analyzer with empty file."""
        result = analyze_js_file([])
        assert result == {"complex_functions": [], "long_methods": []}

    def test_java_analyzer_empty_file(self):
        """Test Java analyzer with empty file."""
        result = analyze_java_file([])
        assert result == {"complex_functions": [], "long_methods": []}

    def test_js_analyzer_no_functions(self):
        """Test JavaScript analyzer with no functions."""
        lines = [
            "let x = 5;",
            "console.log('hello');",
            "const y = x * 2;",
        ]
        result = analyze_js_file(lines)
        assert result == {"complex_functions": [], "long_methods": []}

    def test_java_analyzer_no_methods(self):
        """Test Java analyzer with no methods."""
        lines = [
            "public class Test {",
            "    private int field;",
            "    public Test() {",
            "        this.field = 0;",
            "    }",
            "}",
        ]
        result = analyze_java_file(lines)
        assert result == {"complex_functions": [], "long_methods": []}
