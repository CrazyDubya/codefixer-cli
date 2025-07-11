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

PYTHON_FLAKE8_TEST_CONFIG = """[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501, S101,S105,S106,S107
exclude = .git,__pycache__,build,dist,.venv,venv,node_modules
per-file-ignores =
    __init__.py:F401
    test_*.py:S101,S105,S106,S107
    *_test.py:S101,S105,S106,S107
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

PYTHON_MYPY_CONFIG = """[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy.plugins.numpy.*]
ignore_missing_imports = True

[mypy-pandas.*]
ignore_missing_imports = True
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

# TypeScript linter config
TS_TSLINT_CONFIG = {
    "defaultSeverity": "error",
    "extends": [
        "tslint:recommended"
    ],
    "rules": {
        "indent": [true, "spaces", 2],
        "quotemark": [true, "single"],
        "semicolon": [true, "always"],
        "no-unused-variable": true,
        "no-console": [true, "log", "warn", "error"],
        "prefer-const": true,
        "no-var-keyword": true,
        "arrow-parens": [true, "always"],
        "trailing-comma": [true, {"multiline": "always", "singleline": "never"}],
        "object-literal-sort-keys": false,
        "interface-name": [true, "never-prefix"],
        "member-access": [true, "no-public"],
        "no-empty": [true, "allow-empty-catch"],
        "no-consecutive-blank-lines": [true, 1],
        "max-line-length": [true, 88]
    }
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

# YAML linter config
YAML_YAMLLINT_CONFIG = """extends: default

rules:
  line-length:
    max: 88
    level: warning
  indentation:
    spaces: 2
    indent-sequences: true
  trailing-spaces: enable
  truthy:
    check-keys: false
  comments-indentation: enable
  document-start: disable
  empty-lines:
    max: 1
    max-end: 1
"""

def generate_python_configs(temp_dir: Path) -> None:
    """Generate Python linter configuration files."""
    # Flake8 config
    with open(temp_dir / "flake8.ini", "w") as f:
        f.write(PYTHON_FLAKE8_CONFIG)
    
    # Flake8 test config
    with open(temp_dir / "flake8_test.ini", "w") as f:
        f.write(PYTHON_FLAKE8_TEST_CONFIG)
    
    # Black config
    with open(temp_dir / "pyproject.toml", "w") as f:
        f.write(PYTHON_BLACK_CONFIG)
    
    # pytest config
    with open(temp_dir / "pytest.ini", "w") as f:
        f.write(PYTHON_PYTEST_CONFIG)
    
    # mypy config
    with open(temp_dir / "mypy.ini", "w") as f:
        f.write(PYTHON_MYPY_CONFIG)

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
    
    # Generate tslint.json for TypeScript
    tslint_path = temp_dir / "tslint.json"
    with open(tslint_path, "w") as f:
        json.dump(TS_TSLINT_CONFIG, f, indent=2)
    configs["tslint"] = tslint_path
    
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

def generate_yaml_configs(temp_dir: Path) -> Dict[str, Path]:
    """Generate YAML linter configuration files."""
    configs = {}
    
    # Generate .yamllint
    yamllint_path = temp_dir / ".yamllint"
    with open(yamllint_path, "w") as f:
        f.write(YAML_YAMLLINT_CONFIG)
    configs["yamllint"] = yamllint_path
    
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
    
    if "yaml" in languages:
        all_configs["yaml"] = generate_yaml_configs(temp_dir)
    
    return all_configs 