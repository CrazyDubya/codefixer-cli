# Contributing to CodeFixer CLI

Thank you for your interest in contributing to CodeFixer CLI! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to see if your problem has already been reported
2. **Check the documentation** to see if your question is answered there
3. **Use the issue templates** when available

When reporting an issue, please include:

- **Description**: Clear description of the problem
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, Node.js version, LLM runner version
- **Logs**: Relevant error messages or logs (use `--verbose` flag)

### Suggesting Features

We welcome feature suggestions! When suggesting a feature:

1. **Describe the problem** you're trying to solve
2. **Explain your proposed solution**
3. **Consider alternatives** you've explored
4. **Provide examples** of how the feature would work

### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the coding standards below
4. **Test your changes** thoroughly
5. **Update documentation** if needed
6. **Commit your changes** with clear commit messages
7. **Push to your fork** and submit a pull request

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Git
- Node.js and npm (for testing HTML/CSS linters)
- A local LLM runner (Ollama or llama.cpp)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your/codefixer-cli.git
cd codefixer-cli

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_linters.py

# Run tests with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black .

# Check code style with flake8
flake8 .

# Type checking with mypy
mypy .

# Run all quality checks
make lint  # if you have a Makefile
```

## 📝 Coding Standards

### Python Code

- **Style**: Follow PEP 8 with black formatting
- **Type hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions
- **Imports**: Group imports (standard library, third-party, local) with blank lines

### JavaScript/TypeScript Code

- **Style**: Follow ESLint and Prettier configurations
- **Type hints**: Use TypeScript for type safety
- **Comments**: Use JSDoc comments for functions

### Git Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(linters): add support for Rust linter

fix(cli): handle missing git repository gracefully

docs(readme): update installation instructions
```

## 🧪 Testing

### Writing Tests

- **Test coverage**: Aim for at least 80% test coverage
- **Test structure**: Use descriptive test names and organize tests logically
- **Mocking**: Mock external dependencies (file system, network calls, etc.)
- **Fixtures**: Use pytest fixtures for common test data

### Test Files

- **Naming**: Test files should be named `test_*.py`
- **Location**: Place tests in a `tests/` directory
- **Organization**: Mirror the structure of the main code

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=. --cov-report=html

# Run tests in parallel
pytest -n auto

# Run tests and stop on first failure
pytest -x
```

## 📚 Documentation

### Code Documentation

- **Docstrings**: All public functions should have docstrings
- **Comments**: Add comments for complex logic
- **Type hints**: Use type hints to improve code clarity

### User Documentation

- **README.md**: Keep the main README up to date
- **CLI help**: Ensure all CLI options have clear help text
- **Examples**: Provide practical examples for common use cases

## 🔧 Adding New Linters

To add support for a new language/linter:

1. **Create linter module**: Add `linters/new_language_linter.py`
2. **Add language detection**: Update `languages.py` with new extensions
3. **Add configuration**: Update `linters/configs.py` with linter configs
4. **Update CLI**: Add the new linter to the main CLI logic
5. **Add tests**: Create comprehensive tests for the new linter
6. **Update documentation**: Update README and help text

### Linter Module Structure

```python
"""
New Language linter module for CodeFixer.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

from .env_manager import env_manager

def get_new_language_temp_dir(repo_path: Path) -> Path:
    """Get temporary environment directory for New Language linters."""
    return env_manager.get_language_env("new_language", repo_path)

def setup_new_language_env(temp_dir: Path) -> bool:
    """Set up New Language linting environment."""
    # Implementation here
    pass

def run_new_language_linter(files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Run New Language linters on a list of files."""
    # Implementation here
    pass
```

## 🚀 Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

### Release Checklist

Before releasing:

1. **Update version**: Update version in `setup.py` and `pyproject.toml`
2. **Update changelog**: Document all changes in `CHANGELOG.md`
3. **Run tests**: Ensure all tests pass
4. **Check documentation**: Update README and help text
5. **Create release**: Create a GitHub release with release notes

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/your/codefixer-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your/codefixer-cli/discussions)
- **Documentation**: [Wiki](https://github.com/your/codefixer-cli/wiki)

## 🙏 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and considerate of others.

## 📄 License

By contributing to CodeFixer CLI, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to CodeFixer CLI! 🎉 