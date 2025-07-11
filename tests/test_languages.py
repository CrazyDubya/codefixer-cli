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
        # Note: build/script.py is no longer ignored as it's too broad
        # Only /build/ directories are ignored, not files with 'build' in the name
    
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

    def test_detect_go_files(self, temp_repo):
        """Test detection of Go files."""
        # Create test Go files
        go_file = temp_repo / "main.go"
        go_file.write_text("package main\n\nfunc main() {\n\tprintln(\"Hello, World!\")\n}")
        
        languages = detect_languages(temp_repo)
        
        assert 'go' in languages
        assert 'main.go' in [f.name for f in languages['go']]
    
    def test_detect_rust_files(self, temp_repo):
        """Test detection of Rust files."""
        # Create test Rust files
        rust_file = temp_repo / "main.rs"
        rust_file.write_text("fn main() {\n    println!(\"Hello, World!\");\n}")
        
        languages = detect_languages(temp_repo)
        
        assert 'rust' in languages
        assert 'main.rs' in [f.name for f in languages['rust']]
    
    def test_detect_java_files(self, temp_repo):
        """Test detection of Java files."""
        # Create test Java files
        java_file = temp_repo / "Main.java"
        java_file.write_text("public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}")
        
        languages = detect_languages(temp_repo)
        
        assert 'java' in languages
        assert 'Main.java' in [f.name for f in languages['java']]
    
    def test_detect_c_cpp_files(self, temp_repo):
        """Test detection of C and C++ files."""
        # Create test C and C++ files
        c_file = temp_repo / "main.c"
        c_file.write_text("#include <stdio.h>\n\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}")
        
        cpp_file = temp_repo / "main.cpp"
        cpp_file.write_text("#include <iostream>\n\nint main() {\n    std::cout << \"Hello, World!\" << std::endl;\n    return 0;\n}")
        
        languages = detect_languages(temp_repo)
        
        assert 'c' in languages
        assert 'cpp' in languages
        assert 'main.c' in [f.name for f in languages['c']]
        assert 'main.cpp' in [f.name for f in languages['cpp']]
    
    def test_detect_php_files(self, temp_repo):
        """Test detection of PHP files."""
        # Create test PHP files
        php_file = temp_repo / "index.php"
        php_file.write_text("<?php\necho \"Hello, World!\";\n?>")
        
        languages = detect_languages(temp_repo)
        
        assert 'php' in languages
        assert 'index.php' in [f.name for f in languages['php']]
    
    def test_detect_ruby_files(self, temp_repo):
        """Test detection of Ruby files."""
        # Create test Ruby files
        ruby_file = temp_repo / "main.rb"
        ruby_file.write_text("puts \"Hello, World!\"")
        
        languages = detect_languages(temp_repo)
        
        assert 'ruby' in languages
        assert 'main.rb' in [f.name for f in languages['ruby']]
    
    def test_detect_shell_files(self, temp_repo):
        """Test detection of shell script files."""
        # Create test shell files
        shell_file = temp_repo / "script.sh"
        shell_file.write_text("#!/bin/bash\necho \"Hello, World!\"")
        
        languages = detect_languages(temp_repo)
        
        assert 'shell' in languages
        assert 'script.sh' in [f.name for f in languages['shell']]
    
    def test_detect_markdown_files(self, temp_repo):
        """Test detection of Markdown files."""
        # Create test Markdown files
        md_file = temp_repo / "README.md"
        md_file.write_text("# Hello World\n\nThis is a test markdown file.")
        
        languages = detect_languages(temp_repo)
        
        assert 'markdown' in languages
        assert 'README.md' in [f.name for f in languages['markdown']]
    
    def test_detect_json_files(self, temp_repo):
        """Test detection of JSON files."""
        # Create test JSON files
        json_file = temp_repo / "config.json"
        json_file.write_text('{"name": "test", "version": "1.0.0"}')
        
        languages = detect_languages(temp_repo)
        
        assert 'json' in languages
        assert 'config.json' in [f.name for f in languages['json']]
    
    def test_detect_xml_files(self, temp_repo):
        """Test detection of XML files."""
        # Create test XML files
        xml_file = temp_repo / "config.xml"
        xml_file.write_text('<?xml version="1.0"?>\n<config><name>test</name></config>')
        
        languages = detect_languages(temp_repo)
        
        assert 'xml' in languages
        assert 'config.xml' in [f.name for f in languages['xml']]
    
    def test_detect_sql_files(self, temp_repo):
        """Test detection of SQL files."""
        # Create test SQL files
        sql_file = temp_repo / "schema.sql"
        sql_file.write_text("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255));")
        
        languages = detect_languages(temp_repo)
        
        assert 'sql' in languages
        assert 'schema.sql' in [f.name for f in languages['sql']]
    
    def test_detect_dockerfile(self, temp_repo):
        """Test detection of Dockerfile."""
        # Create test Dockerfile
        dockerfile = temp_repo / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY . .\nCMD [\"python\", \"app.py\"]")
        
        languages = detect_languages(temp_repo)
        
        assert 'dockerfile' in languages
        assert 'Dockerfile' in [f.name for f in languages['dockerfile']]
    
    def test_detect_makefile(self, temp_repo):
        """Test detection of Makefile."""
        # Create test Makefile
        makefile = temp_repo / "Makefile"
        makefile.write_text("all:\n\techo \"Hello, World!\"")
        
        languages = detect_languages(temp_repo)
        
        assert 'makefile' in languages
        assert 'Makefile' in [f.name for f in languages['makefile']]
    
    def test_detect_toml_files(self, temp_repo):
        """Test detection of TOML files."""
        # Create test TOML files
        toml_file = temp_repo / "pyproject.toml"
        toml_file.write_text("[project]\nname = \"test\"\nversion = \"1.0.0\"")
        
        languages = detect_languages(temp_repo)
        
        # pyproject.toml is detected as 'requirements', not 'toml'
        assert 'requirements' in languages
        assert 'pyproject.toml' in [f.name for f in languages['requirements']]
    
    def test_detect_ini_files(self, temp_repo):
        """Test detection of INI files."""
        # Create test INI files
        ini_file = temp_repo / "config.ini"
        ini_file.write_text("[section]\nkey = value")
        
        languages = detect_languages(temp_repo)
        
        assert 'ini' in languages
        assert 'config.ini' in [f.name for f in languages['ini']]
    
    def test_detect_properties_files(self, temp_repo):
        """Test detection of properties files."""
        # Create test properties files
        props_file = temp_repo / "application.properties"
        props_file.write_text("server.port=8080\napp.name=test")
        
        languages = detect_languages(temp_repo)
        
        assert 'properties' in languages
        assert 'application.properties' in [f.name for f in languages['properties']]
    
    def test_detect_gradle_files(self, temp_repo):
        """Test detection of Gradle files."""
        # Create test Gradle files
        gradle_file = temp_repo / "build.gradle"
        gradle_file.write_text("plugins {\n    id 'java'\n}\n\ndependencies {\n    testImplementation 'junit:junit:4.13'\n}")
        
        languages = detect_languages(temp_repo)
        
        assert 'gradle' in languages
        assert 'build.gradle' in [f.name for f in languages['gradle']]
    
    def test_detect_maven_files(self, temp_repo):
        """Test detection of Maven files."""
        # Create test Maven files
        pom_file = temp_repo / "pom.xml"
        pom_file.write_text('<?xml version="1.0"?>\n<project>\n    <groupId>com.example</groupId>\n    <artifactId>test</artifactId>\n    <version>1.0.0</version>\n</project>')
        
        languages = detect_languages(temp_repo)
        
        assert 'maven' in languages
        assert 'pom.xml' in [f.name for f in languages['maven']]
    
    def test_detect_npm_files(self, temp_repo):
        """Test detection of npm files."""
        # Create test npm files
        package_file = temp_repo / "package.json"
        package_file.write_text('{"name": "test", "version": "1.0.0", "scripts": {"test": "echo \\"test\\""}}')
        
        languages = detect_languages(temp_repo)
        
        assert 'npm' in languages
        assert 'package.json' in [f.name for f in languages['npm']]
    
    def test_detect_cargo_files(self, temp_repo):
        """Test detection of Cargo files."""
        # Create test Cargo files
        cargo_file = temp_repo / "Cargo.toml"
        cargo_file.write_text('[package]\nname = "test"\nversion = "1.0.0"\n[dependencies]')
        
        languages = detect_languages(temp_repo)
        
        assert 'cargo' in languages
        assert 'Cargo.toml' in [f.name for f in languages['cargo']]
    
    def test_detect_go_mod_files(self, temp_repo):
        """Test detection of Go module files."""
        # Create test Go module files
        go_mod_file = temp_repo / "go.mod"
        go_mod_file.write_text("module test\n\ngo 1.21\n")
        
        languages = detect_languages(temp_repo)
        
        assert 'go_mod' in languages
        assert 'go.mod' in [f.name for f in languages['go_mod']]
    
    def test_detect_requirements_files(self, temp_repo):
        """Test detection of requirements files."""
        # Create test requirements files
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("requests==2.31.0\npytest==7.4.0")
        
        languages = detect_languages(temp_repo)
        
        assert 'requirements' in languages
        assert 'requirements.txt' in [f.name for f in languages['requirements']]
    
    def test_detect_gemfile_files(self, temp_repo):
        """Test detection of Gemfile files."""
        # Create test Gemfile files
        gemfile = temp_repo / "Gemfile"
        gemfile.write_text("source 'https://rubygems.org'\n\ngem 'rails', '~> 7.0'")
        
        languages = detect_languages(temp_repo)
        
        assert 'gemfile' in languages
        assert 'Gemfile' in [f.name for f in languages['gemfile']]
    
    def test_detect_composer_files(self, temp_repo):
        """Test detection of Composer files."""
        # Create test Composer files
        composer_file = temp_repo / "composer.json"
        composer_file.write_text('{"name": "test/app", "require": {"php": ">=7.4"}}')
        
        languages = detect_languages(temp_repo)
        
        assert 'composer' in languages
        assert 'composer.json' in [f.name for f in languages['composer']]
    
    def test_detect_pubspec_files(self, temp_repo):
        """Test detection of pubspec files."""
        # Create test pubspec files
        pubspec_file = temp_repo / "pubspec.yaml"
        pubspec_file.write_text("name: test\nversion: 1.0.0\n\ndependencies:\n  flutter:\n    sdk: flutter")
        
        languages = detect_languages(temp_repo)
        
        assert 'pubspec' in languages
        assert 'pubspec.yaml' in [f.name for f in languages['pubspec']] 