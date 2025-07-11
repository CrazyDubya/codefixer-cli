#!/usr/bin/env python3
"""
CodeFixer CLI - A local-only command-line utility for automated code fixing.
"""

import click
import os
import sys
from pathlib import Path
import difflib

# Import our modules
from languages import detect_languages
from linters.python_linter import run_python_linter
from linters.js_linter import run_js_linter
from linters.html_linter import run_html_linter
from linters.css_linter import run_css_linter
from llm import generate_fix
from git_utils import create_branch, apply_fixes, push_and_pr
from logger import setup_logger

logger = setup_logger()

@click.command()
@click.option('--repo', help='Path to the git repository')
@click.option('--branch', default='codefixer-fixes', help='Branch name for fixes')
@click.option('--model', default='gemma3:1b', help='Local LLM model to use')
@click.option('--runner', default='ollama', help='LLM runner (llama.cpp, ollama)')
@click.option('--no-push', is_flag=True, help='Skip pushing branch and creating PR')
@click.option('--dry-run', is_flag=True, help='Show what would be done without applying changes')
@click.option('--output', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
@click.option('--cleanup', is_flag=True, help='Clean up all temporary environments')
@click.option('--show-issues', is_flag=True, help='Show all lint issues per file in dry-run mode')
@click.option('--show-diff', is_flag=True, help='Show unified diff of proposed fixes in dry-run mode')
@click.option('--config', is_flag=True, help='Show current configuration')
@click.option('--config-reset', is_flag=True, help='Reset configuration to defaults')
@click.option('--list-models', is_flag=True, help='List available LLM models')
def main(repo, branch, model, runner, no_push, dry_run, output, verbose, cleanup, show_issues, show_diff, config, config_reset, list_models):
    """CodeFixer - Automated code fixing with local LLM and best-practice linters.
    
    CodeFixer is a privacy-first, local-only CLI tool that automatically analyzes your git repositories,
    detects programming languages, runs industry-standard linters in isolated environments, and uses a
    local LLM (≤7B parameters) to generate safe, human-reviewable code fixes. It applies fixes to a
    new git branch and can create a pull request for your review. No code or data ever leaves your machine.
    
    WORKFLOW:
    1. Language Detection: Scans repository for Python, JavaScript/TypeScript, HTML, and CSS files
    2. Linting: Runs flake8/black (Python), ESLint/Prettier (JS/TS), htmlhint (HTML), stylelint (CSS)
    3. LLM Fixing: Uses local LLM to generate fixes for detected lint issues
    4. Git Operations: Creates branch, applies fixes, commits changes
    5. PR Creation: Pushes branch and creates pull request for human review
    
    USAGE EXAMPLES:
    
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
    
    # Show configuration and available models
    codefixer --config
    codefixer --list-models
    
    ENVIRONMENT MANAGEMENT:
    - Temporary linter environments are stored in your system temp directory
    - Environments older than 24 hours are automatically cleaned up
    - Use --cleanup to manually remove all temporary environments
    - Each repository gets its own cached environments for faster subsequent runs
    
    PRIVACY & SECURITY:
    - All analysis, linting, and LLM inference happens locally
    - No code, metadata, or telemetry is sent anywhere
    - All fixes are proposed in a new branch and PR for human review
    - Temporary environments are isolated and automatically cleaned up
    
    SUPPORTED LANGUAGES & LINTERS:
    - Python: flake8, black, mypy, pytest
    - JavaScript/TypeScript: ESLint, Prettier
    - HTML: htmlhint
    - CSS: stylelint
    - YAML: yamllint
    
    For more information, visit: https://github.com/CrazyDubya/codefixer-cli
    """
    
    if verbose:
        logger.setLevel('DEBUG')
    
    # Handle configuration commands
    if config:
        from config_manager import show_config
        show_config()
        return
    
    if config_reset:
        from config_manager import reset_config
        if reset_config():
            logger.info("Configuration reset to defaults")
        else:
            logger.error("Failed to reset configuration")
        return
    
    if list_models:
        list_available_models()
        return
    
    # Handle cleanup command
    if cleanup:
        from linters.env_manager import env_manager
        env_manager.cleanup_all()
        return
    
    logger.info(f"Starting CodeFixer on repository: {repo}")
    
    # Validate repository path (skip if cleanup only)
    if not repo:
        logger.error("Repository path is required (use --repo)")
        sys.exit(1)
        
    repo_path = Path(repo)
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo}")
        sys.exit(1)
    
    if not (repo_path / '.git').exists():
        logger.error(f"Not a git repository: {repo}")
        sys.exit(1)
    
    # Check if repository is clean
    from git_utils import check_repo_clean
    if not check_repo_clean(repo_path):
        logger.error(f"Repository has uncommitted changes. Please commit or stash them first.")
        sys.exit(1)
    
    try:
        # Phase 1: Detect languages
        logger.info("Detecting languages...")
        languages = detect_languages(repo_path)
        logger.info(f"Detected languages: {list(languages.keys())}")
        
        if not languages:
            logger.warning("No supported languages detected")
            return
        
        # Phase 2: Run linters
        all_issues = {}
        
        # Handle JS/TS together to avoid redundant linting
        js_files = []
        ts_files = []
        other_languages = {}
        
        for lang, files in languages.items():
            if lang == 'javascript':
                js_files.extend(files)
            elif lang == 'typescript':
                ts_files.extend(files)
            else:
                other_languages[lang] = files
        
        # Run JS/TS linter once if we have JS or TS files
        if js_files or ts_files:
            logger.info("Linting JavaScript/TypeScript files...")
            all_js_ts_files = js_files + ts_files
            issues = run_js_linter(all_js_ts_files, repo_path)
            if issues:
                all_issues.update(issues)
        
        # Run other language linters
        for lang, files in other_languages.items():
            logger.info(f"Linting {lang} files...")
            if lang == 'python':
                issues = run_python_linter(files, repo_path)
            elif lang == 'html':
                issues = run_html_linter(files, repo_path)
            elif lang == 'css':
                issues = run_css_linter(files, repo_path)
            elif lang == 'yaml':
                from linters.yaml_linter import run_yaml_linter
                issues = run_yaml_linter(files, repo_path)
            else:
                logger.warning(f"No linter configured for {lang}")
                continue
            
            if issues:
                all_issues.update(issues)
        
        if not all_issues:
            logger.info("No linting issues found")
            return
        
        # Deduplicate and prioritize issues
        from issue_deduplicator import deduplicate_issues, prioritize_issues
        all_issues = deduplicate_issues(all_issues)
        all_issues = prioritize_issues(all_issues)
        
        total_issues = sum(len(issues) for issues in all_issues.values())
        logger.info(f"Found {total_issues} issues across {len(all_issues)} files (after deduplication)")
        
        # Phase 3: Generate fixes with LLM
        logger.info("Generating fixes with LLM...")
        fixes = {}
        
        # Try to use tqdm for progress bar
        try:
            from tqdm import tqdm
            progress_bar = tqdm(all_issues.items(), desc="Generating fixes", unit="file")
        except ImportError:
            progress_bar = all_issues.items()
        
        for file_path, issues in progress_bar:
            logger.debug(f"Fixing {file_path}...")
            try:
                fix = generate_fix(file_path, issues, model, runner)
                if fix:
                    fixes[file_path] = fix
            except Exception as e:
                logger.error(f"Failed to generate fix for {file_path}: {e}")
        
        if not fixes:
            logger.warning("No fixes generated")
            return
        
        logger.info(f"Generated fixes for {len(fixes)} files")
        
        # Phase 4: Apply fixes and create PR
        if dry_run:
            logger.info("DRY RUN - Would apply the following fixes:")
            for file_path, fix in fixes.items():
                # Show issues if requested
                if show_issues:
                    logger.info(f"Issues for {file_path}:")
                    for issue in all_issues[file_path]:
                        logger.info(f"  Line {issue['row']}, Col {issue['col']}: {issue['code']} - {issue['text']}")
                # Show diff if requested
                if show_diff:
                    try:
                        with open(file_path, 'r') as f:
                            original = f.read().splitlines()
                        fixed = fix.splitlines()
                        diff = list(difflib.unified_diff(original, fixed, fromfile=f"a/{file_path}", tofile=f"b/{file_path}", lineterm=''))
                        logger.info(f"Diff for {file_path}:")
                        for line in diff:
                            # Add colors for diff output
                            if line.startswith('+'):
                                print(f"\033[32m{line}\033[0m")  # Green for additions
                            elif line.startswith('-'):
                                print(f"\033[31m{line}\033[0m")  # Red for deletions
                            elif line.startswith('@'):
                                print(f"\033[36m{line}\033[0m")  # Cyan for context
                            else:
                                print(line)
                        num_changed_lines = sum(1 for l in diff if l.startswith('+') or l.startswith('-'))
                    except Exception as e:
                        logger.warning(f"Could not show diff for {file_path}: {e}")
                        num_changed_lines = len(fix.splitlines())
                else:
                    num_changed_lines = len(fix.splitlines())
                logger.info(f"  {file_path}: {num_changed_lines} changed lines")
            if output == 'json':
                import json
                result = {
                    'languages_detected': list(languages.keys()),
                    'files_analyzed': len(all_issues),
                    'total_issues': sum(len(issues) for issues in all_issues.values()),
                    'files_with_fixes': len(fixes),
                    'dry_run': True,
                    'fixes': {file_path: {
                        'num_changed_lines': len(fix.splitlines()),
                        'issues': all_issues[file_path],
                        'diff': list(difflib.unified_diff(open(file_path).readlines(), fix.splitlines(keepends=True), fromfile=f"a/{file_path}", tofile=f"b/{file_path}")) if show_diff else None
                    } for file_path, fix in fixes.items()}
                }
                print(json.dumps(result, indent=2))
            return
        
        # Create branch and apply fixes
        logger.info(f"Creating branch: {branch}")
        create_branch(repo_path, branch)
        
        logger.info("Applying fixes...")
        apply_fixes(repo_path, fixes)
        
        if not no_push:
            logger.info("Pushing branch and creating PR...")
            pr_url = push_and_pr(repo_path, branch, all_issues, fixes)
            if pr_url:
                logger.info(f"Pull request created: {pr_url}")
            else:
                logger.warning("Failed to create pull request")
        else:
            logger.info("Skipping push (--no-push flag)")
        
        logger.info("CodeFixer completed successfully")
        
    except Exception as e:
        logger.error(f"CodeFixer failed: {e}")
        sys.exit(1)

def list_available_models():
    """List available LLM models."""
    print("Available LLM Models:")
    print("\nOllama Models (recommended):")
    print("  smollm2:135m     - Very fast, good for simple fixes")
    print("  phi3:3b          - Good balance of speed and quality")
    print("  gemma:2b         - Reliable, good code understanding")
    print("  llama3.2:3b      - Excellent code generation")
    print("  codellama:7b     - Specialized for code (larger)")
    print("  deepseek-coder:6.7b - Code-focused model")
    
    print("\nTo install a model with Ollama:")
    print("  ollama pull <model-name>")
    print("\nTo see all available models:")
    print("  ollama list")
    
    print("\nllama.cpp Models:")
    print("  Use any GGUF model file")
    print("  Download from: https://huggingface.co/models?search=gguf")
    print("  Example: llama-3.2-3b.Q4_K_M.gguf")

if __name__ == '__main__':
    main() 