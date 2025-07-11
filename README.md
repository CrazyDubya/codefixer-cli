# CodeFixer CLI

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**CodeFixer** is a privacy-first, local-only CLI tool that automatically analyzes your git repositories, detects programming languages, runs industry-standard linters in isolated environments, and uses a local LLM (≤7B params) to generate safe, human-reviewable code fixes. It applies fixes to a new git branch and can create a pull request for your review. **No code or data ever leaves your machine.**

## 🚀 Features

- **🔍 Language Detection:** Auto-detects Python, JavaScript/TypeScript, HTML, and CSS files in your repo
- **⚙️ Opinionated Linter Configs:** Generates safe, best-practice configs for flake8, pytest, ESLint, Prettier, htmlhint, and stylelint
- **🔒 Isolated Linting:** Runs each linter in a temp venv/npm environment for reproducibility and safety
- **🤖 Local LLM Fixes:** Uses a local LLM (via llama.cpp or Ollama) to generate code fixes for lint issues
- **🔄 GitOps:** Applies fixes to a new branch, pushes, and creates a pull request for human review
- **👥 Human-in-the-Loop:** All changes are proposed via PR—no auto-merging
- **📊 Digestible Output:** Console and optional JSON output for easy review or CI integration
- **🛡️ Privacy & Security:** No cloud, no telemetry, no code leaves your machine—ever
- **🧹 Smart Environment Management:** Automatic cleanup of temp environments with manual override

## 📋 Prerequisites

- **Python 3.8+**
- **Git**
- **Node.js and npm** (for HTML/CSS linters)
- **A local LLM runner:**
  - [Ollama](https://ollama.com/) (recommended for ease of use)
  - [llama.cpp](https://github.com/ggerganov/llama.cpp) (for advanced users)

## 🛠️ Installation

### Quick Install

```bash
# Install from PyPI (when available)
pip install codefixer-cli

# Or install from source
git clone https://github.com/your/codefixer-cli.git
cd codefixer-cli
pip install -e .
```

### Setup Local LLM

#### Option 1: Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a small, fast model
ollama pull smollm2:135m

# Start Ollama service
ollama serve
```

#### Option 2: llama.cpp
```bash
# Clone and build llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make

# Download a model (you'll need to download model files separately)
```

## 🎯 Usage

### Basic Commands

```bash
# One-click automated fixing (creates PR)
codefixer --repo ~/projects/myrepo

# Preview what would be fixed (dry run)
codefixer --repo ~/projects/myrepo --dry-run

# See all issues and diffs before applying
codefixer --repo ~/projects/myrepo --dry-run --show-issues --show-diff

# Machine-readable output for LLMs/scripts
codefixer --repo ~/projects/myrepo --dry-run --output json --show-issues --show-diff

# Use specific LLM model
codefixer --repo ~/projects/myrepo --model smollm2:135m --runner ollama

# Skip PR creation (just apply fixes locally)
codefixer --repo ~/projects/myrepo --no-push

# Clean up temporary environments
codefixer --cleanup
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--repo` | Path to the git repository | Required |
| `--branch` | Branch name for fixes | `codefixer-fixes` |
| `--model` | Local LLM model to use | `gemma3:1b` |
| `--runner` | LLM runner (ollama, llama.cpp) | `ollama` |
| `--dry-run` | Show what would be done without applying changes | False |
| `--no-push` | Don't push branch or create PR | False |
| `--output` | Output format (text, json) | `text` |
| `--verbose` | Enable debug logging | False |
| `--cleanup` | Clean up all temporary environments | False |
| `--show-issues` | Show all lint issues per file in dry-run mode | False |
| `--show-diff` | Show unified diff of proposed fixes in dry-run mode | False |

## 🔧 Supported Languages & Linters

| Language | Linter(s) | Config File |
|----------|-----------|-------------|
| Python | flake8, black | .flake8, pyproject.toml |
| JavaScript | ESLint, Prettier | .eslintrc.json, .prettierrc |
| TypeScript | ESLint, Prettier | .eslintrc.json, .prettierrc |
| HTML | htmlhint | .htmlhintrc |
| CSS | stylelint | .stylelintrc.json |

## 🏗️ How It Works

### 1. Language Detection
Scans the repository to identify programming languages based on file extensions and creates a mapping of languages to file paths.

### 2. Linting
For each detected language:
- Creates a temporary environment (venv for Python, npm for JS/HTML/CSS)
- Installs appropriate linters with opinionated configurations
- Runs linters on all files of that language
- Collects and parses linting issues

### 3. LLM Fixing
For each file with lint issues:
- Reads the original file content
- Builds a prompt with the code and lint issues
- Sends to local LLM for fix generation
- Extracts and validates the proposed fix

### 4. Git Operations
- Creates a new branch from the current HEAD
- Applies all generated fixes to the working directory
- Commits changes with descriptive messages
- Optionally pushes the branch and creates a pull request

## 🧹 Environment Management

CodeFixer automatically manages temporary linter environments:

- **Location**: Stored in your system's temp directory (e.g., `/tmp/codefixer/` on Unix)
- **Naming**: Each repo+language gets a unique environment (e.g., `python_<repo_hash>`)
- **Automatic cleanup**: Environments older than 24 hours are automatically removed
- **Manual cleanup**: Run `codefixer --cleanup` to remove all temporary environments
- **Caching**: Active repos reuse their environments for faster subsequent runs

## 🔒 Privacy & Security

- **Local-only**: All analysis, linting, and LLM inference happens on your machine
- **No telemetry**: No usage data, metrics, or analytics are collected
- **No code transmission**: Your source code never leaves your machine
- **Isolated environments**: Each linter runs in its own temporary environment
- **Human review**: All changes are proposed via pull requests for manual review

## 🤖 LLM Integration

### Supported Runners
- **Ollama**: Easy setup, good model selection, recommended for most users
- **llama.cpp**: Advanced users, custom models, more configuration options

### Recommended Models
For best performance, use models ≤7B parameters:
- `smollm2:135m` - Very fast, good for simple fixes
- `phi3:3b` - Good balance of speed and quality
- `gemma:2b` - Reliable, good code understanding
- `llama3.2:3b` - Excellent code generation

### Model Setup
```bash
# With Ollama
ollama pull smollm2:135m
ollama serve

# Use with CodeFixer
codefixer --repo ~/projects/myrepo --model smollm2:135m --runner ollama
```

## 📊 Output Formats

### Console Output
Default human-readable output with progress indicators and summaries.

### JSON Output
Machine-readable output for integration with other tools or LLMs:
```bash
codefixer --repo ~/projects/myrepo --dry-run --output json --show-issues --show-diff
```

Example JSON structure:
```json
{
  "languages_detected": ["python", "javascript"],
  "files_analyzed": 5,
  "total_issues": 12,
  "files_with_fixes": 3,
  "dry_run": true,
  "fixes": {
    "src/main.py": {
      "num_changed_lines": 8,
      "issues": [...],
      "diff": [...]
    }
  }
}
```

## 🧪 Examples

### Python Project
```bash
# Fix a Python project with formatting and linting issues
codefixer --repo ~/projects/my-python-app --model smollm2:135m
```

### JavaScript/TypeScript Project
```bash
# Preview fixes for a JS/TS project
codefixer --repo ~/projects/my-react-app --dry-run --show-issues --show-diff
```

### Mixed Language Project
```bash
# Fix a full-stack project with Python backend and JS frontend
codefixer --repo ~/projects/fullstack-app --model phi3:3b
```

## 🐛 Troubleshooting

### Common Issues

**LLM not found:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve
```

**Linter failures:**
```bash
# Check Node.js and npm installation
node --version
npm --version

# Clean up and retry
codefixer --cleanup
codefixer --repo ~/projects/myrepo --verbose
```

**Git issues:**
```bash
# Ensure repository is clean
git status

# Check remote access
git remote -v
```

### Getting Help

- Use `--verbose` for detailed logging
- Use `--dry-run` to preview changes without applying them
- Check the logs for specific error messages
- Run `codefixer --cleanup` if environments seem corrupted

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your/codefixer-cli.git
cd codefixer-cli

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 .
black .
```

### Project Structure

```
codefixer-cli/
├── cli.py              # Main CLI entry point
├── languages.py        # Language detection
├── llm.py             # LLM integration
├── git_utils.py       # Git operations
├── logger.py          # Logging setup
├── linters/           # Language-specific linters
│   ├── __init__.py
│   ├── env_manager.py # Environment management
│   ├── configs.py     # Linter configurations
│   ├── python_linter.py
│   ├── js_linter.py
│   ├── html_linter.py
│   └── css_linter.py
├── templates/         # LLM prompt templates
│   └── fix_prompt.txt
├── setup.py          # Package configuration
├── pyproject.toml    # Project configuration
└── README.md
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Ollama](https://ollama.com/) and [llama.cpp](https://github.com/ggerganov/llama.cpp) for local LLM inference
- [flake8](https://flake8.pycqa.org/), [ESLint](https://eslint.org/), [htmlhint](https://htmlhint.com/), [stylelint](https://stylelint.io/) for linting
- [smollm2](https://huggingface.co/unsloth/smollm2), [phi3](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct), [gemma](https://ai.google.dev/gemma) for local models

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your/codefixer-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your/codefixer-cli/discussions)
- **Documentation**: [Wiki](https://github.com/your/codefixer-cli/wiki)

---

**Made with ❤️ for privacy-conscious developers who want to write better code.** 