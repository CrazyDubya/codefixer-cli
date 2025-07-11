# Changelog

All notable changes to CodeFixer CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-07-11

### Added
- **Initial release** of CodeFixer CLI
- **Language Detection**: Auto-detects Python, JavaScript/TypeScript, HTML, and CSS files
- **Multi-language Linting**: Support for flake8/black (Python), ESLint/Prettier (JS/TS), htmlhint (HTML), stylelint (CSS)
- **Local LLM Integration**: Works with Ollama and llama.cpp for local code fixing
- **GitOps Workflow**: Creates branches, applies fixes, commits changes, and creates pull requests
- **Smart Environment Management**: Automatic cleanup of temporary linter environments
- **Privacy-First Design**: All processing happens locally, no code leaves your machine
- **Comprehensive CLI**: Rich command-line interface with multiple output formats
- **JSON Output**: Machine-readable output for LLM and script integration
- **Dry-run Mode**: Preview changes before applying them
- **Issue and Diff Display**: Show detailed lint issues and code diffs
- **Environment Cleanup**: Manual and automatic cleanup of temporary environments

### Features
- **One-click automation**: Run `codefixer --repo <repo>` for fully automated fixing
- **Review workflow**: Use `--dry-run --show-issues --show-diff` to review before applying
- **LLM-friendly output**: JSON format with full issue lists and diffs
- **Flexible deployment**: Skip PR creation with `--no-push` for local-only fixes
- **Model selection**: Choose from various local LLM models and runners
- **Verbose logging**: Detailed output for debugging and understanding the process

### Technical Details
- **Python 3.8+** compatibility
- **Cross-platform** support (Windows, macOS, Linux)
- **Isolated environments** for each language's linters
- **Opinionated but safe** linter configurations
- **Automatic dependency management** for linters
- **Robust error handling** and graceful degradation
- **Comprehensive logging** with configurable levels

### Documentation
- **Comprehensive README** with installation, usage, and troubleshooting
- **Detailed CLI help** with prose explanations and examples
- **Contributing guidelines** for open source development
- **MIT License** for open source use

### Supported Languages & Linters
- **Python**: flake8, black, pytest
- **JavaScript**: ESLint, Prettier
- **TypeScript**: ESLint, Prettier
- **HTML**: htmlhint
- **CSS**: stylelint

### LLM Integration
- **Ollama**: Easy setup with recommended models (smollm2:135m, phi3:3b, gemma:2b)
- **llama.cpp**: Advanced configuration for custom models
- **Model recommendations**: Optimized for ≤7B parameter models for speed and quality

---

## [Unreleased]

### Planned Features
- Support for additional languages (Rust, Go, Java, etc.)
- Configurable linter rules and custom configurations
- CI/CD integration helpers
- Web interface for review and approval
- Batch processing of multiple repositories
- Interactive fix selection and approval
- Integration with more LLM runners
- Performance optimizations and caching improvements

### Known Issues
- None at this time

---

## Version History

- **0.1.0**: Initial release with core functionality 