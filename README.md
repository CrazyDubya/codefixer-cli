# CodeFixer CLI

A local-only command-line utility for automated code fixing with local LLM. CodeFixer analyzes a git repository, detects programming languages, runs linters in isolated environments, uses a local LLM (≤7B parameters) to generate fixes for lint issues, applies those fixes to a new git branch, pushes the branch, and creates a pull request for human review.

## Features

- **Local-Only**: Runs entirely on your machine with no cloud APIs or external calls beyond git remotes
- **Privacy-First**: All code analysis and LLM inference happens locally
- **Multi-Language Support**: Detects and lints Python, JavaScript, TypeScript, and more
- **Isolated Environments**: Creates temporary environments for each language's linters
- **Local LLM Integration**: Works with llama.cpp, Ollama, and other local LLM runners
- **Git Integration**: Automatically creates branches, commits fixes, and creates PRs
- **Human-in-the-Loop**: Always creates pull requests for human review, never auto-merges

## Prerequisites

- Python 3.8+
- Git
- npm (for JavaScript/TypeScript linting)
- A local LLM runner (llama.cpp, Ollama, etc.)
- GitHub CLI (`gh`) or GitLab CLI (`glab`) for PR/MR creation

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/example/codefixer-cli.git
cd codefixer-cli

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Install Local LLM Runner

#### Option 1: llama.cpp

```bash
# Clone and build llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make

# Download a model (example: Llama-3-8B)
# You'll need to download the model files separately
```

#### Option 2: Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2:8b
```

## Usage

### Basic Usage

```bash
# Analyze and fix a repository
codefixer --repo /path/to/your/repo

# Specify a custom branch name
codefixer --repo /path/to/your/repo --branch my-fixes

# Use a specific LLM model
codefixer --repo /path/to/your/repo --model llama-3.2:8b --runner ollama
```

### Advanced Options

```bash
# Dry run (show what would be done without applying changes)
codefixer --repo /path/to/your/repo --dry-run

# Skip pushing and PR creation
codefixer --repo /path/to/your/repo --no-push

# Verbose logging
codefixer --repo /path/to/your/repo --verbose

# JSON output for scripting
codefixer --repo /path/to/your/repo --output json
```

### Command Line Options

- `--repo`: Path to the git repository (required)
- `--branch`: Branch name for fixes (default: `codefixer-fixes`)
- `--model`: Local LLM model to use (default: `llama-7b`)
- `--runner`: LLM runner (default: `llama.cpp`, options: `llama.cpp`, `ollama`)
- `--no-push`: Skip pushing branch and creating PR
- `--dry-run`: Show what would be done without applying changes
- `--output`: Output format (default: `text`, options: `text`, `json`)
- `--verbose`: Verbose logging

## Supported Languages

CodeFixer currently supports:

- **Python**: flake8, black
- **JavaScript/TypeScript**: ESLint, Prettier
- **Java**: (planned)
- **Go**: (planned)
- **Rust**: (planned)
- **PHP**: (planned)
- **Ruby**: (planned)

## How It Works

1. **Language Detection**: Scans the repository to identify programming languages based on file extensions
2. **Linting**: For each detected language, creates a temporary environment and runs appropriate linters
3. **LLM Fixing**: Uses a local LLM to generate fixes for detected lint issues
4. **Git Operations**: Creates a new branch, applies fixes, commits changes
5. **PR Creation**: Pushes the branch and creates a pull request for human review

## Configuration

### Custom Prompt Templates

You can customize the LLM prompt by creating `templates/fix_prompt.txt`:

```
You are a programming assistant. Below is a source code snippet and its lint errors:

SOURCE CODE:
{code}

LINT ISSUES:
{issues}

Please provide the corrected code with all lint issues fixed. Return only the corrected code without any explanations or markdown formatting.

CORRECTED CODE:
```

### Linter Configuration

Linters are configured automatically in temporary environments, but you can customize them by modifying the linter modules in `linters/`.

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 .
black .
mypy .
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
│   ├── python_linter.py
│   └── js_linter.py
├── templates/         # LLM prompt templates
│   └── fix_prompt.txt
├── pyproject.toml     # Project configuration
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Security

- CodeFixer runs entirely locally and never sends your code to external services
- All LLM inference happens on your machine
- Temporary environments are created for each language to isolate dependencies
- File backups are created before applying fixes

## Troubleshooting

### Common Issues

1. **LLM not found**: Ensure your local LLM runner is installed and accessible
2. **Linter failures**: Check that required tools (npm, python3) are installed
3. **Git issues**: Ensure the repository is clean and you have push access
4. **PR creation fails**: Install GitHub CLI (`gh`) or GitLab CLI (`glab`)

### Getting Help

- Check the logs for detailed error messages
- Use `--verbose` flag for more detailed output
- Use `--dry-run` to see what would be done without making changes

## Roadmap

- [ ] Support for more programming languages
- [ ] Incremental linting (only changed files)
- [ ] Custom linter configurations
- [ ] Batch processing of multiple repositories
- [ ] Integration with more LLM runners
- [ ] Web interface for review and approval 