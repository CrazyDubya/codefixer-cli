"""
Linter configuration generator for CodeFixer.
Provides opinionated but safe default configurations for all supported linters.
"""

import json
from pathlib import Path
from typing import Dict, Any

# Python linter configs
PYTHON_FLAKE8_CONFIG = """[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = .git,__pycache__,build,dist,.venv,venv,node_modules
per-file-ignores =
    __init__.py:F401
    tests/*:S101,S105,S106,S107
"""

PYTHON_BLACK_CONFIG = """[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'
extend-exclude = '''
/(
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''
"""

PYTHON_PYTEST_CONFIG = """[pytest]
addopts = --strict-markers --tb=short --disable-warnings
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
"""

# JavaScript/TypeScript linter configs
JS_ESLINT_CONFIG = {
    "env": {
        "browser": True,
        "es2021": True,
        "node": True
    },
    "extends": [
        "eslint:recommended"
    ],
    "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module"
    },
    "rules": {
        "indent": ["error", 2],
        "linebreak-style": ["error", "unix"],
        "quotes": ["error", "single"],
        "semi": ["error", "always"],
        "no-unused-vars": ["warn"],
        "no-console": ["warn"],
        "prefer-const": ["error"]
    }
}

JS_PRETTIER_CONFIG = {
    "semi": True,
    "trailingComma": "es5",
    "singleQuote": True,
    "printWidth": 88,
    "tabWidth": 2,
    "useTabs": False
}

# HTML linter config
HTML_HTMLHINT_CONFIG = {
    "tagname-lowercase": True,
    "attr-lowercase": True,
    "doctype-first": True,
    "id-unique": True,
    "src-not-empty": True,
    "attr-value-double-quotes": True,
    "attr-no-duplication": True,
    "title-require": True
}

# CSS linter config
CSS_STYLELINT_CONFIG = {
    "extends": "stylelint-config-standard",
    "rules": {
        "indentation": 2,
        "string-quotes": "double",
        "color-hex-case": "lower",
        "color-hex-length": "short",
        "declaration-block-trailing-semicolon": "always",
        "declaration-colon-space-after": "always",
        "declaration-colon-space-before": "never"
    }
}

def generate_python_configs(temp_dir: Path) -> Dict[str, Path]:
    """Generate Python linter configuration files."""
    configs = {}
    
    # Generate .flake8
    flake8_path = temp_dir / ".flake8"
    with open(flake8_path, "w") as f:
        f.write(PYTHON_FLAKE8_CONFIG)
    configs["flake8"] = flake8_path
    
    # Generate pyproject.toml for black
    pyproject_path = temp_dir / "pyproject.toml"
    with open(pyproject_path, "w") as f:
        f.write(PYTHON_BLACK_CONFIG)
    configs["black"] = pyproject_path
    
    # Generate pytest.ini
    pytest_path = temp_dir / "pytest.ini"
    with open(pytest_path, "w") as f:
        f.write(PYTHON_PYTEST_CONFIG)
    configs["pytest"] = pytest_path
    
    return configs

def generate_js_configs(temp_dir: Path) -> Dict[str, Path]:
    """Generate JavaScript/TypeScript linter configuration files."""
    configs = {}
    
    # Generate .eslintrc.json
    eslint_path = temp_dir / ".eslintrc.json"
    with open(eslint_path, "w") as f:
        json.dump(JS_ESLINT_CONFIG, f, indent=2)
    configs["eslint"] = eslint_path
    
    # Generate .prettierrc
    prettier_path = temp_dir / ".prettierrc"
    with open(prettier_path, "w") as f:
        json.dump(JS_PRETTIER_CONFIG, f, indent=2)
    configs["prettier"] = prettier_path
    
    return configs

def generate_html_configs(temp_dir: Path) -> Dict[str, Path]:
    """Generate HTML linter configuration files."""
    configs = {}
    
    # Generate .htmlhintrc
    htmlhint_path = temp_dir / ".htmlhintrc"
    with open(htmlhint_path, "w") as f:
        json.dump(HTML_HTMLHINT_CONFIG, f, indent=2)
    configs["htmlhint"] = htmlhint_path
    
    return configs

def generate_css_configs(temp_dir: Path) -> Dict[str, Path]:
    """Generate CSS linter configuration files."""
    configs = {}
    
    # Generate .stylelintrc.json
    stylelint_path = temp_dir / ".stylelintrc.json"
    with open(stylelint_path, "w") as f:
        json.dump(CSS_STYLELINT_CONFIG, f, indent=2)
    configs["stylelint"] = stylelint_path
    
    return configs

def generate_all_configs(temp_dir: Path, languages: list) -> Dict[str, Dict[str, Path]]:
    """Generate all linter configuration files for detected languages."""
    all_configs = {}
    
    if "python" in languages:
        all_configs["python"] = generate_python_configs(temp_dir)
    
    if "javascript" in languages or "typescript" in languages:
        all_configs["javascript"] = generate_js_configs(temp_dir)
    
    if "html" in languages:
        all_configs["html"] = generate_html_configs(temp_dir)
    
    if "css" in languages:
        all_configs["css"] = generate_css_configs(temp_dir)
    
    return all_configs 