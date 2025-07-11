"""
Tests for language detection module.
"""

import pytest
from pathlib import Path
from languages import detect_languages, should_ignore, LANGUAGE_EXTENSIONS


class TestLanguageDetection:
    """Test language detection functionality."""
    
    def test_detect_python_files(self, temp_repo):
        """Test detection of Python files."""
        # Create additional Python files
        (temp_repo / "main.py").write_text("print('Hello')")
        (temp_repo / "utils.py").write_text("def helper(): pass")
        (temp_repo / "test_module.py").write_text("import os")
        
        languages = detect_languages(temp_repo)
        
        assert "python" in languages
        assert len(languages["python"]) == 5  # Including existing test files
        assert any("main.py" in str(f) for f in languages["python"])
        assert any("utils.py" in str(f) for f in languages["python"])
    
    def test_detect_javascript_files(self, temp_repo):
        """Test detection of JavaScript files."""
        # Create additional JS files
        (temp_repo / "app.js").write_text("console.log('Hello')")
        (temp_repo / "utils.js").write_text("function helper() {}")
        (temp_repo / "component.jsx").write_text("import React from 'react'")
        
        languages = detect_languages(temp_repo)
        
        assert "javascript" in languages
        assert len(languages["javascript"]) == 4  # Including existing test.js
        assert any("app.js" in str(f) for f in languages["javascript"])
        assert any("component.jsx" in str(f) for f in languages["javascript"])
    
    def test_detect_typescript_files(self, temp_repo):
        """Test detection of TypeScript files."""
        (temp_repo / "app.ts").write_text("console.log('Hello')")
        (temp_repo / "component.tsx").write_text("import React from 'react'")
        
        languages = detect_languages(temp_repo)
        
        assert "typescript" in languages
        assert len(languages["typescript"]) == 2
        assert any("app.ts" in str(f) for f in languages["typescript"])
        assert any("component.tsx" in str(f) for f in languages["typescript"])
    
    def test_detect_html_files(self, temp_repo):
        """Test detection of HTML files."""
        (temp_repo / "index.html").write_text("<html><body>Hello</body></html>")
        (temp_repo / "about.htm").write_text("<html><body>About</body></html>")
        
        languages = detect_languages(temp_repo)
        
        assert "html" in languages
        assert len(languages["html"]) == 2
        assert any("index.html" in str(f) for f in languages["html"])
        assert any("about.htm" in str(f) for f in languages["html"])
    
    def test_detect_css_files(self, temp_repo):
        """Test detection of CSS files."""
        (temp_repo / "style.css").write_text("body { color: red; }")
        (temp_repo / "main.scss").write_text("$color: red; body { color: $color; }")
        
        languages = detect_languages(temp_repo)
        
        assert "css" in languages
        assert len(languages["css"]) == 2
        assert any("style.css" in str(f) for f in languages["css"])
        assert any("main.scss" in str(f) for f in languages["css"])
    
    def test_detect_yaml_files(self, temp_repo):
        """Test detection of YAML files."""
        (temp_repo / "config.yml").write_text("name: test\nversion: 1.0")
        (temp_repo / "settings.yaml").write_text("debug: true")
        
        languages = detect_languages(temp_repo)
        
        assert "yaml" in languages
        assert len(languages["yaml"]) == 2
        assert any("config.yml" in str(f) for f in languages["yaml"])
        assert any("settings.yaml" in str(f) for f in languages["yaml"])
    
    def test_ignore_patterns(self, temp_repo):
        """Test that ignore patterns work correctly."""
        # Create files that should be ignored
        (temp_repo / "__pycache__").mkdir()
        (temp_repo / "__pycache__" / "test.pyc").write_text("")
        # .git directory already exists from fixture, just add config file
        (temp_repo / ".git" / "config").write_text("")
        (temp_repo / "node_modules").mkdir()
        (temp_repo / "node_modules" / "package.json").write_text("{}")
        
        languages = detect_languages(temp_repo)
        
        # Check that ignored files are not included
        for lang_files in languages.values():
            for file_path in lang_files:
                assert "__pycache__" not in str(file_path)
                assert ".git" not in str(file_path)
                assert "node_modules" not in str(file_path)
    
    def test_ignore_hidden_files(self, temp_repo):
        """Test that hidden files are ignored."""
        (temp_repo / ".hidden.py").write_text("print('hidden')")
        (temp_repo / ".config.js").write_text("console.log('hidden')")
        
        languages = detect_languages(temp_repo)
        
        # Check that hidden files are not included
        for lang_files in languages.values():
            for file_path in lang_files:
                assert not file_path.name.startswith(".")
    
    def test_should_ignore_function(self):
        """Test the should_ignore function directly."""
        # Test files that should be ignored
        assert should_ignore(Path("__pycache__/test.py"))
        assert should_ignore(Path(".git/config"))
        assert should_ignore(Path("node_modules/package.json"))
        assert should_ignore(Path(".hidden.py"))
        assert should_ignore(Path("build/script.py"))
        assert should_ignore(Path("dist/package.py"))
        
        # Test files that should not be ignored
        assert not should_ignore(Path("main.py"))
        assert not should_ignore(Path("src/app.js"))
        assert not should_ignore(Path("test/test_file.py"))
    
    def test_language_extensions_mapping(self):
        """Test that language extensions mapping is complete."""
        # Test that all expected languages are present
        expected_languages = [
            'python', 'javascript', 'typescript', 'html', 'css', 'yaml',
            'java', 'cpp', 'c', 'go', 'rust', 'php', 'ruby'
        ]
        
        for lang in expected_languages:
            assert lang in LANGUAGE_EXTENSIONS
            assert len(LANGUAGE_EXTENSIONS[lang]) > 0
    
    def test_empty_repository(self, temp_repo):
        """Test detection in an empty repository."""
        # Remove all test files
        for file_path in temp_repo.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        
        languages = detect_languages(temp_repo)
        assert len(languages) == 0
    
    def test_nested_directories(self, temp_repo):
        """Test detection in nested directory structure."""
        # Create nested structure
        (temp_repo / "src").mkdir()
        (temp_repo / "src" / "main.py").write_text("print('main')")
        (temp_repo / "src" / "utils.py").write_text("def helper(): pass")
        
        (temp_repo / "src" / "frontend").mkdir()
        (temp_repo / "src" / "frontend" / "app.js").write_text("console.log('app')")
        (temp_repo / "src" / "frontend" / "style.css").write_text("body { margin: 0; }")
        
        languages = detect_languages(temp_repo)
        
        assert "python" in languages
        assert "javascript" in languages
        assert "css" in languages
        
        # Check that nested files are detected
        python_files = [str(f) for f in languages["python"]]
        assert any("src/main.py" in f for f in python_files)
        assert any("src/utils.py" in f for f in python_files)
        
        js_files = [str(f) for f in languages["javascript"]]
        assert any("src/frontend/app.js" in f for f in js_files)
        
        css_files = [str(f) for f in languages["css"]]
        assert any("src/frontend/style.css" in f for f in css_files) 